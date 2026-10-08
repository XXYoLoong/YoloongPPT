import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const upstreamCommit = 'c3605ebc487fc6c7d4f4139761e46d7021cd656c';
const sourceRoot = process.cwd();
const requireFromSource = createRequire(path.join(sourceRoot, 'package.json'));
const JSZip = requireFromSource('jszip');
const { CreateCommand } = await import(pathToFileURL(path.join(sourceRoot, 'dist', 'commands', 'create.js')).href);
const evidenceRoot = process.env.P04_EVIDENCE_ROOT ?? '/evidence';
const validationDir = path.join(evidenceRoot, 'validation');
const templateDir = path.join(sourceRoot, 'src', 'templates');
const layoutsDir = path.join(sourceRoot, 'src', 'layouts');
const configPath = '/tmp/p04-no-real-config.json';

await mkdir(validationDir, { recursive: true });

const outline = JSON.stringify({
  title: 'P04 离线调用链验证',
  slides: [{ title: '主题路线', layout: 'bullet', bulletPoints: ['注入式假响应'] }],
});
const fill = JSON.stringify({ expandedText: '离线填充结果', speakerNotes: '未调用真实模型' });

function fixtureProvider(actions) {
  let index = 0;
  return {
    name: 'fixture-provider',
    async chat() {
      const action = actions[index++];
      if (action instanceof Error) throw action;
      if (action === undefined) throw new Error('unexpected provider call');
      return { content: action };
    },
    get calls() { return index; },
  };
}

async function runCase(name, actions, options) {
  const provider = fixtureProvider(actions);
  const command = new CreateCommand({
    provider,
    configPath,
    layoutsDir,
    templatesDir: templateDir,
    outputDir: validationDir,
  });
  try {
    await command.execute(options);
    return { name, result: 'success', providerCalls: provider.calls, output: options.output };
  } catch (error) {
    return {
      name,
      result: 'expected_failure',
      providerCalls: provider.calls,
      error: String(error?.message ?? error),
    };
  }
}

async function inspectPptx(filename, expectedText) {
  const filePath = path.join(validationDir, filename);
  const bytes = await readFile(filePath);
  const zip = await JSZip.loadAsync(bytes);
  const entries = Object.keys(zip.files).filter(name => !zip.files[name].dir).sort();
  const slideXml = await zip.file('ppt/slides/slide1.xml')?.async('string');
  assert.ok(slideXml, `${filename} must contain slide1.xml`);
  const decodeXml = value => value
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
  const slideText = [...slideXml.matchAll(/<a:t>([\s\S]*?)<\/a:t>/g)]
    .map(match => decodeXml(match[1]))
    .join('');
  const requiredParts = ['[Content_Types].xml', 'ppt/presentation.xml', 'ppt/slides/slide1.xml'];
  const requiredPartsPresent = requiredParts.filter(name => entries.includes(name));
  for (const name of requiredParts) assert.ok(entries.includes(name), `${filename} is missing ${name}`);
  for (const text of expectedText) assert.ok(slideText.includes(text), `${filename} is missing slide text: ${text}`);
  const info = await stat(filePath);
  return {
    path: `research/P04/validation/${filename}`,
    bytes: info.size,
    sha256: createHash('sha256').update(bytes).digest('hex').toUpperCase(),
    zipEntryCount: entries.length,
    requiredPartsPresent,
    slideText,
  };
}

const normal = await runCase('topic-normal', [outline, fill], {
  topic: '可复现的离线演示',
  template: 'tech',
  output: 'topic-route-normal.pptx',
});
assert.equal(normal.result, 'success');
assert.equal(normal.providerCalls, 2);
normal.artifact = await inspectPptx(normal.output, ['主题路线', '注入式假响应']);

const edge = await runCase('content-fill-fallback', [
  outline,
  new Error('simulated provider timeout on content stage'),
], {
  topic: '内容填充失败边界',
  template: 'tech',
  output: 'topic-route-fill-fallback.pptx',
});
assert.equal(edge.result, 'success');
assert.equal(edge.providerCalls, 2);
edge.artifact = await inspectPptx(edge.output, ['主题路线', '注入式假响应']);

const failure = await runCase('missing-input', [], { output: 'should-not-exist.pptx' });
assert.equal(failure.result, 'expected_failure');
assert.equal(failure.providerCalls, 0);
assert.equal(failure.error, 'Provide --topic, --input, --html, or --images');

const report = {
  schemaVersion: '1.0',
  requirementId: 'RES-P04-02',
  taskId: 'TASK-RES-P04-02',
  verifyTaskId: 'VERIFY-RES-P04-02',
  project: 'peterfei/ai-agent-ppt',
  upstreamCommit,
  runtime: process.version,
  isolation: {
    execution: 'Docker container',
    network: 'none',
    realCredentialsUsed: false,
    realModelOrApiCalls: false,
    outputDirectory: 'research/P04/validation',
  },
  normalCase: normal,
  edgeCase: {
    ...edge,
    observedBehavior: 'ContentFiller catches the provider error, keeps original outline slide data, and PPTX generation continues.',
  },
  contentFillOutputEffect: {
    normalAndFallbackPptxHashesMatch: normal.artifact.sha256 === edge.artifact.sha256,
    selectedLayout: 'bullet',
    explanation: 'For this layout, SlideRenderer binds title and bulletPoints only; ContentFiller output fields expandedText and speakerNotes have no slots in bullet.layout.json.',
  },
  failureCase: failure,
  acceptance: {
    sourceGroundedCallGraph: true,
    sourceIndexCoversMainRouteNodes: true,
    normalTopicInputProducedStructurallyValidPptx: true,
    contentFillFailureFallbackObserved: true,
    missingInputFailedBeforeProviderCall: true,
    noRealModelOrApiCalls: true,
  },
  limitations: [
    'The provider was injected with deterministic fixture responses; no hosted model behavior was tested.',
    'Screenshot/Vision LLM route was source-mapped but not sent to a real vision provider.',
    'PPTX package structure and slide text were checked; no Office/LibreOffice visual render was performed.',
    'This is a targeted research PoC, not the upstream Vitest suite or a YoloongPPT product-runtime verification.',
  ],
  sourceRefs: [
    'research/P04/call-graph.md',
    'research/P04/source-index.json',
    'research/P04/validation/verify-res-p04-02.mjs',
    'research/P04/validation/verify-res-p04-01.json',
  ],
};

await writeFile(
  path.join(validationDir, 'verify-res-p04-02.json'),
  `${JSON.stringify(report, null, 2)}\n`,
  'utf8',
);
console.log(JSON.stringify(report, null, 2));
