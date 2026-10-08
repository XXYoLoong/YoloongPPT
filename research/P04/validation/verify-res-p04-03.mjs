import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const workspaceRoot = process.env.P04_WORKSPACE_ROOT ?? '/work';
const sourceRoot = process.env.P04_SOURCE_ROOT ?? '/source';
const artifactRoot = path.join(workspaceRoot, 'research', 'P04');
const validationRoot = path.join(artifactRoot, 'validation');
const upstreamCommit = 'c3605ebc487fc6c7d4f4139761e46d7021cd656c';
const mapPath = path.join(artifactRoot, 'decision-map.json');
const map = JSON.parse(await readFile(mapPath, 'utf8'));
const sourceIndex = JSON.parse(await readFile(path.join(artifactRoot, 'source-index.json'), 'utf8'));
const sourceIndexById = new Map(sourceIndex.nodes.map(node => [node.id, node]));
const sourceHead = process.env.P04_SOURCE_HEAD ?? '';
const sourceCheckoutClean = process.env.P04_SOURCE_CLEAN === 'true';
assert.equal(sourceHead, upstreamCommit, 'source checkout must remain on the pinned commit');
assert.equal(sourceCheckoutClean, true, 'host must confirm the upstream research checkout is clean before the Docker run');

const expectedDecIds = Array.from({ length: 40 }, (_, i) => `DEC-${String(i + 1).padStart(3, '0')}`);
const validStatuses = new Set(['mapped', 'partial', 'not_evidenced']);
assert.equal(map.requirementId, 'RES-P04-03');
assert.equal(map.taskId, 'TASK-RES-P04-03');
assert.equal(map.verifyTaskId, 'VERIFY-RES-P04-03');
assert.equal(map.project.commit, upstreamCommit);
assert.equal(map.project.license, 'MIT');
assert.equal(map.decisionNodes.length, 17);
assert.equal(map.decCrosswalk.length, 40);
assert.deepEqual(map.decCrosswalk.map(item => item.id), expectedDecIds, 'crosswalk must cover each DEC exactly once and in order');
for (const item of map.decCrosswalk) assert.ok(validStatuses.has(item.status), `${item.id} has invalid status`);
const counts = Object.fromEntries([...validStatuses].map(status => [status, map.decCrosswalk.filter(item => item.status === status).length]));
assert.deepEqual(counts, { mapped: 3, partial: 27, not_evidenced: 10 });

const nodeById = new Map(map.decisionNodes.map(item => [item.id, item]));
assert.equal(nodeById.size, map.decisionNodes.length, 'decision node IDs must be unique');
const checkedRanges = [];
for (const item of map.decisionNodes) {
  for (const key of ['input', 'candidates', 'mechanism', 'output', 'constraints', 'fallback', 'trace', 'sources', 'runtimeEvidence']) {
    assert.ok(item[key] && (Array.isArray(item[key]) ? item[key].length > 0 : true), `${item.id} missing ${key}`);
  }
  assert.ok(item.decIds.length > 0, `${item.id} needs a global DEC mapping`);
  for (const decId of item.decIds) {
    const crosswalk = map.decCrosswalk.find(row => row.id === decId);
    assert.ok(crosswalk, `${item.id} references unknown ${decId}`);
    assert.ok(crosswalk.nodeIds.includes(item.id), `${decId} omits reverse node mapping ${item.id}`);
  }
  for (const ref of item.sources) {
    assert.ok(ref.file && Array.isArray(ref.lines) && ref.lines.length === 2, `${item.id} has malformed source reference`);
    const sourcePath = path.join(sourceRoot, ...ref.file.split('/'));
    const sourceText = await readFile(sourcePath, 'utf8');
    const lineCount = sourceText.split(/\r?\n/).length;
    assert.ok(ref.lines[0] >= 1 && ref.lines[1] >= ref.lines[0] && ref.lines[1] <= lineCount, `${item.id} source range out of bounds: ${ref.file}:${ref.lines.join('-')} (lines=${lineCount})`);
    for (const sourceId of ref.sourceIndexIds ?? []) {
      const indexed = sourceIndexById.get(sourceId);
      assert.ok(indexed, `${item.id} references unknown source-index node ${sourceId}`);
      assert.equal(indexed.kind, 'source', `${sourceId} must identify a source location`);
      assert.equal(indexed.file, ref.file, `${sourceId} file differs from direct source reference`);
    }
    checkedRanges.push({ nodeId: item.id, file: ref.file, lines: ref.lines });
  }
}
for (const row of map.decCrosswalk) {
  for (const nodeId of row.nodeIds) {
    const item = nodeById.get(nodeId);
    assert.ok(item, `${row.id} references unknown node ${nodeId}`);
    assert.ok(item.decIds.includes(row.id), `${nodeId} does not declare ${row.id}`);
  }
  if (row.status === 'not_evidenced') assert.equal(row.nodeIds.length, 0, `${row.id} not_evidenced should not claim a mapped node`);
  else assert.ok(row.nodeIds.length > 0, `${row.id} needs a source-backed node`);
}
for (const item of map.projectSpecificMechanisms) assert.ok(nodeById.has(item.nodeId), `${item.id} references unknown node`);

const readJson = async relative => JSON.parse(await readFile(path.join(workspaceRoot, ...relative.split('/')), 'utf8'));
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex').toUpperCase();
const p01 = await readJson('research/P04/validation/verify-res-p04-01.json');
const p02 = await readJson('research/P04/validation/verify-res-p04-02.json');
assert.equal(p01.upstreamCommit, upstreamCommit);
assert.equal(p02.upstreamCommit, upstreamCommit);

async function verifyArtifact(reportRef, artifactPath, expected) {
  const absPath = path.join(workspaceRoot, ...artifactPath.split('/'));
  const bytes = await readFile(absPath);
  const actualHash = sha256(bytes);
  assert.equal(bytes.length, expected.bytes, `${artifactPath} byte length differs from report`);
  assert.equal(actualHash, expected.sha256.toUpperCase(), `${artifactPath} SHA-256 differs from report`);
  return { path: artifactPath, bytes: bytes.length, sha256: actualHash, matchesPriorReport: true, sourceReport: reportRef };
}
const reusedCases = [];
const htmlNormal = p01.normalCase;
assert.equal(htmlNormal.exitCode, 0);
assert.ok(htmlNormal.requiredPartsPresent.includes('ppt/slides/slide1.xml'));
reusedCases.push({ caseId:'p04-01-html-normal', category:'normal', executionReused:true, result:htmlNormal.result, artifact:await verifyArtifact('research/P04/validation/verify-res-p04-01.json', htmlNormal.artifactPath, { bytes:htmlNormal.artifactBytes, sha256:htmlNormal.artifactSha256 }) });
const htmlEdge = p01.edgeCase;
assert.equal(htmlEdge.exitCode, 0);
assert.ok(htmlEdge.requiredPartsPresent.includes('ppt/slides/slide1.xml'));
reusedCases.push({ caseId:'p04-01-nested-html-edge', category:'boundary', executionReused:true, result:htmlEdge.result, artifact:await verifyArtifact('research/P04/validation/verify-res-p04-01.json', htmlEdge.artifactPath, { bytes:htmlEdge.artifactBytes, sha256:htmlEdge.artifactSha256 }) });
assert.equal(p01.failureCase.exitCode, 1);
assert.match(p01.failureCase.stderrOrOutput, /Provide --topic, --input, --html, or --images/);
reusedCases.push({ caseId:'p04-01-missing-input-failure', category:'failure', executionReused:true, exitCode:p01.failureCase.exitCode, error:p01.failureCase.stderrOrOutput });
const topicNormal = p02.normalCase;
assert.equal(topicNormal.result, 'success');
assert.equal(topicNormal.providerCalls, 2);
reusedCases.push({ caseId:'p04-02-topic-normal', category:'normal', executionReused:true, result:topicNormal.result, providerCalls:topicNormal.providerCalls, artifact:await verifyArtifact('research/P04/validation/verify-res-p04-02.json', topicNormal.artifact.path, topicNormal.artifact) });
const fillFallback = p02.edgeCase;
assert.equal(fillFallback.result, 'success');
assert.equal(p02.contentFillOutputEffect.normalAndFallbackPptxHashesMatch, true);
reusedCases.push({ caseId:'p04-02-content-fill-fallback', category:'boundary', executionReused:true, result:fillFallback.result, providerCalls:fillFallback.providerCalls, observedBehavior:fillFallback.observedBehavior, artifact:await verifyArtifact('research/P04/validation/verify-res-p04-02.json', fillFallback.artifact.path, fillFallback.artifact) });
assert.equal(p02.failureCase.result, 'expected_failure');
assert.equal(p02.failureCase.providerCalls, 0);
reusedCases.push({ caseId:'p04-02-missing-input-failure', category:'failure', executionReused:true, result:p02.failureCase.result, providerCalls:p02.failureCase.providerCalls, error:p02.failureCase.error });

const image = process.env.P04_VALIDATION_IMAGE ?? 'node:24.14.0-bookworm-slim';
const report = {
  schemaVersion:'1.0', requirementId:'RES-P04-03', taskId:'TASK-RES-P04-03', verifyTaskId:'VERIFY-RES-P04-03',
  project:'peterfei/ai-agent-ppt', upstreamCommit,
  validationExecution:{ runner:'Docker', image, runtime:process.version, network:'none', sourceCheckout:sourceHead, sourceCheckoutClean, gitStateObservedOnHost:true, realCredentialsUsed:false, realModelOrApiCalls:false, outputDirectory:'research/P04/validation' },
  decisionMap:{ status:'passed', nodeCount:nodeById.size, checkedSourceRanges:checkedRanges.length, decIdCoverage:expectedDecIds, crosswalkStatusCounts:counts, projectSpecificMechanismCount:map.projectSpecificMechanisms.length, allSourceRangesExist:true, sourceIndexReferencesResolve:true },
  reusedRuntimeCases:reusedCases,
  casesNotExecuted:['截图 Vision 路线','真实托管模型候选/评分','无效 layout 跳过运行','上游 Vitest 全套','Office/LibreOffice 视觉渲染','QA/revision 或 YoloongPPT 产品验收'],
  acceptance:{ all17DecisionNodesHaveRequiredFields:true, all40UnifiedDecIdsCrossReferenced:true, sourceRangesVerifiedAgainstPinnedCheckout:true, existingNormalBoundaryFailureArtifactsRehashed:true, projectCapabilityStatusNotChanged:true },
  limitations:['正常/边界/失败运行结果来自 P04-01/P04-02 已完成的禁网验证；本脚本只复核其报告、产物哈希与源码映射，不重复运行上游生成命令。','Node 24.14.0 是此次隔离验证容器观测，不构成 YoloongPPT 产品运行时选择。','截图 Vision、真实模型行为、所有版式资产、视觉质量和可编辑性未由本报告验证。'],
  sourceRefs:['research/P04/decision-map.json','research/P04/decision-map.md','research/P04/source-index.json','research/P04/validation/verify-res-p04-01.json','research/P04/validation/verify-res-p04-02.json',...reusedCases.filter(item=>item.artifact).map(item=>item.artifact.path)],
};
const reportPath = path.join(validationRoot, 'verify-res-p04-03.json');
await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(report, null, 2));
