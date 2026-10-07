import crypto from "node:crypto";
import { execFileSync } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";

const EXPECTED_COMMIT = "2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d";
const repositoryRoot = path.resolve(
  process.argv[2] || "F:/YoloongPPT-Research/P01",
);
const productRoot = path.resolve("research/P01");
const upstreamRoot = path.join(repositoryRoot, "skills/ppt-master");
const templateRoot = path.join(upstreamRoot, "templates");
const sourceHead = execFileSync(
  "git",
  ["-C", repositoryRoot, "rev-parse", "HEAD"],
  { encoding: "utf8" },
).trim();

if (sourceHead !== EXPECTED_COMMIT) {
  throw new Error(
    "Pinned source mismatch: expected " + EXPECTED_COMMIT + ", got " + sourceHead,
  );
}

const bytes = async (file) => fs.readFile(file);
const text = async (file) => (await bytes(file)).toString("utf8");
const hash = (value) =>
  crypto.createHash("sha256").update(value).digest("hex");
const relativeSource = (file) =>
  path.relative(upstreamRoot, file).split(path.sep).join("/");
const lineNumber = (source, offset) =>
  source.slice(0, Math.max(0, offset)).split(/\r?\n/).length;
const attributes = (tag) =>
  Object.fromEntries(
    [...tag.matchAll(/([\w:-]+)="([^"]*)"/g)].map((match) => [
      match[1],
      match[2],
    ]),
  );
const walk = async (directory) => {
  const found = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) found.push(...(await walk(fullPath)));
    else found.push(fullPath);
  }
  return found;
};
const indexFor = async (kind) => {
  const file = path.join(templateRoot, kind, kind + "_index.json");
  const raw = await bytes(file);
  return {
    path: relativeSource(file),
    sha256: hash(raw),
    entries: JSON.parse(raw.toString("utf8")),
  };
};
const frontmatter = (source) => {
  const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) throw new Error("Missing Design Spec frontmatter");
  const body = match[1];
  const value = (key) =>
    body.match(new RegExp("^" + key + ":\\s*(.*)$", "m"))?.[1]?.trim() ??
    null;
  const number = (key) => {
    const candidate = Number(value(key));
    return Number.isFinite(candidate) ? candidate : null;
  };
  const tokensByPage = {};
  let inPlaceholders = false;
  for (const line of body.split(/\r?\n/)) {
    if (/^placeholders:\s*$/.test(line)) {
      inPlaceholders = true;
      continue;
    }
    if (inPlaceholders && !/^\s{2}/.test(line)) break;
    if (!inPlaceholders) continue;
    const item = line.match(/^\s{2}([^:]+):\s*(.*)$/);
    if (!item) continue;
    tokensByPage[item[1].trim()] = {
      tokens: [...item[2].matchAll(/\{\{([^}]+)\}\}/g)].map((part) =>
        part[1].trim(),
      ),
      line: lineNumber(source, source.indexOf(line)),
    };
  }
  return {
    endOffset: match[0].length,
    tokensByPage,
    values: {
      layout_id: value("layout_id"),
      kind: value("kind"),
      category: value("category"),
      summary: value("summary"),
      canvas_format: value("canvas_format"),
      canvas_width: number("canvas_width"),
      canvas_height: number("canvas_height"),
      canvas_viewbox: value("canvas_viewbox")?.replace(/^"|"$/g, "") ?? null,
      source_canvas_width: number("source_canvas_width"),
      source_canvas_height: number("source_canvas_height"),
      source_viewbox: value("source_viewbox")?.replace(/^"|"$/g, "") ?? null,
      replication_mode: value("replication_mode"),
      native_structure_mode: value("native_structure_mode"),
      page_count: number("page_count"),
    },
  };
};

const kinds = [
  "brands",
  "styles",
  "layouts",
  "decks",
  "charts",
  "tables",
];
const indexes = Object.fromEntries(
  await Promise.all(kinds.map(async (kind) => [kind, await indexFor(kind)])),
);
const layoutEntries = indexes.layouts.entries;
const layoutMaps = [];

for (const [layoutId, indexEntry] of Object.entries(layoutEntries)) {
  const folder = path.join(templateRoot, "layouts", layoutId, "templates");
  const specFile = path.join(folder, "design_spec.md");
  const spec = await text(specFile);
  const fm = frontmatter(spec);
  const body = spec.slice(fm.endOffset);
  const roster = {};

  for (const line of body.split(/\r?\n/)) {
    const columns = line.split("|").slice(1, -1).map((cell) => cell.trim());
    const svgCell = columns[0]?.match(/^\x60([^\x60]+\.svg)\x60$/);
    if (!svgCell || columns.length < 4) continue;
    const hasMasterColumn = columns.length >= 5;
    const clean = (cell) => cell.replace(/^\x60|\x60$/g, "").trim();
    const layoutColumn = hasMasterColumn ? 2 : 1;
    const pickerColumn = hasMasterColumn ? 3 : 2;
    const purposeColumn = hasMasterColumn ? 4 : 3;
    roster[svgCell[1]] = {
      master: hasMasterColumn ? clean(columns[1]) : null,
      layout_key: clean(columns[layoutColumn]),
      picker_name: clean(columns[pickerColumn]),
      purpose: clean(columns[purposeColumn]),
      source_line: lineNumber(spec, spec.indexOf(line)),
    };
  }

  const files = await fs.readdir(folder);
  const svgNames = files
    .filter((name) => name.toLowerCase().endsWith(".svg"))
    .sort();
  const pages = [];

  for (const fileName of svgNames) {
    const svgFile = path.join(folder, fileName);
    const svg = await text(svgFile);
    const rootTag = svg.match(/<svg\b[\s\S]*?>/)?.[0] ?? "";
    const rootAttrs = attributes(rootTag);
    const pageType =
      rootAttrs["data-pptx-layout"] ||
      path.basename(fileName, ".svg").replace(/^\d+_/, "");
    const specKey = path.basename(fileName, ".svg");
    const slotList = [];

    for (const match of svg.matchAll(/<g\b[\s\S]*?>/g)) {
      const slotAttrs = attributes(match[0]);
      const role = slotAttrs["data-pptx-placeholder"];
      if (!role) continue;
      const rawBounds = (slotAttrs["data-pptx-bounds"] || "")
        .trim()
        .split(/\s+/)
        .map(Number);
      const validBounds =
        rawBounds.length === 4 &&
        rawBounds.every(Number.isFinite) &&
        rawBounds[2] > 0 &&
        rawBounds[3] > 0;
      const viewBox = (rootAttrs.viewBox || "").split(/\s+/).map(Number);
      const area = validBounds ? rawBounds[2] * rawBounds[3] : null;
      const canvasArea =
        viewBox.length === 4 ? viewBox[2] * viewBox[3] : null;
      slotList.push({
        group_id: slotAttrs.id || null,
        role,
        bounds_raw: slotAttrs["data-pptx-bounds"] || null,
        bounds: validBounds
          ? {
              x: rawBounds[0],
              y: rawBounds[1],
              width: rawBounds[2],
              height: rawBounds[3],
              unit: "SVG user units",
              area_user_units2: area,
              canvas_area_ratio: canvasArea
                ? Number((area / canvasArea).toFixed(6))
                : null,
            }
          : null,
        source_line: lineNumber(svg, match.index),
      });
    }

    const specTokens = fm.tokensByPage[specKey];
    const rosterEntry = roster[fileName];
    pages.push({
      file: fileName,
      path: relativeSource(svgFile),
      sha256: hash(await bytes(svgFile)),
      page_type: pageType,
      powerpoint_layout_key: rootAttrs["data-pptx-layout"] || null,
      powerpoint_master_name: rootAttrs["data-pptx-master-name"] || null,
      powerpoint_picker_name: rosterEntry?.picker_name ?? null,
      purpose: rosterEntry?.purpose ?? null,
      applicability: {
        page_job: rosterEntry?.purpose ?? null,
        canvas_format: fm.values.canvas_format,
        selection_rule:
          "Applicable when the planned page job matches this roster purpose and the deck uses this Layout family; source requires explicit selection and does not infer a family from content.",
      },
      roster_source_line: rosterEntry?.source_line ?? null,
      svg_source_line: lineNumber(svg, svg.indexOf("<svg")),
      view_box: rootAttrs.viewBox || null,
      design_spec_tokens: specTokens?.tokens ?? [],
      token_source_line: specTokens?.line ?? null,
      token_slot_mapping:
        "Design Spec tokens and SVG slot roles are recorded separately; the source does not declare a universal one-to-one mapping, so none is inferred.",
      slots: slotList,
      slot_count: slotList.length,
      capacity: {
        representation:
          "Each slot bounds rectangle is a geometric capacity zone in SVG user units.",
        maximum_characters: null,
        maximum_lines: null,
        absent_limit_reason:
          "The source contract defines bounds as capacity but does not encode a universal text or line limit.",
      },
    });
  }

  const templateFiles = [];
  for (const file of await walk(folder)) {
    const raw = await bytes(file);
    templateFiles.push({
      path: relativeSource(file),
      bytes: raw.length,
      sha256: hash(raw),
    });
  }
  const rosterMissing = svgNames.filter((fileName) => !roster[fileName]);
  const registryPageTypes = new Set(indexEntry.page_types || []);
  const pageTypesMissingFromRegistry = pages
    .filter((page) => !registryPageTypes.has(page.page_type))
    .map((page) => page.file);
  const pagesMissingTokenEntry = pages
    .filter((page) => page.token_source_line === null)
    .map((page) => page.file);
  layoutMaps.push({
    id: layoutId,
    index_entry: indexEntry,
    design_spec: {
      path: relativeSource(specFile),
      sha256: hash(await bytes(specFile)),
      source: {
        frontmatter_line: 1,
        page_roster_section: "V. Page Roster",
      },
      ...fm.values,
    },
    page_types: indexEntry.page_types || [],
    pages,
    template_files: templateFiles,
    validation: {
      declared_page_count: indexEntry.page_count,
      svg_count: svgNames.length,
      roster_missing_for_svg: rosterMissing,
      page_types_missing_from_registry: pageTypesMissingFromRegistry,
      pages_missing_design_spec_token_entry: pagesMissingTokenEntry,
      design_spec_page_count_matches_registry:
        fm.values.page_count === indexEntry.page_count,
      svg_count_matches_registry:
        svgNames.length === indexEntry.page_count &&
        svgNames.length === pages.length,
    },
  });
}

const schemaContracts = {};
for (const name of ["design_spec", "spec_lock"]) {
  const file = path.join(templateRoot, "schemas", name + ".schema.json");
  const raw = await bytes(file);
  const schema = JSON.parse(raw.toString("utf8"));
  schemaContracts[name] = {
    path: relativeSource(file),
    sha256: hash(raw),
    schema_uri: schema.$schema || null,
    title: schema.title || null,
    type: schema.type || null,
    top_level_keys: Object.keys(schema),
    declared_properties: Object.keys(schema.properties || {}),
  };
}

const readmePath = path.join(templateRoot, "README.md");
const layoutCount = layoutMaps.length;
const pages = layoutMaps.flatMap((layout) => layout.pages);
const allPageTypes = new Set(pages.map((page) => page.page_type));
const slotCount = pages.reduce((total, page) => total + page.slot_count, 0);
const tokenCount = pages.reduce(
  (total, page) => total + page.design_spec_tokens.length,
  0,
);
const map = {
  artifact: "ProjectTemplateMap",
  version: "1.0",
  generated_at_utc: new Date().toISOString(),
  requirement_id: "RES-P01-04",
  task_id: "TASK-RES-P01-04",
  source: {
    repository: "hugohe3/ppt-master",
    commit: sourceHead,
    checkout_relative_to_repository: "skills/ppt-master",
    scope: "Read-only source study; conclusions are not YoloongPPT implementation claims.",
  },
  reusable_template_kinds: {
    hierarchy:
      "Brand, Style, Layout, and Deck are independent kinds, not an inheritance chain.",
    source: {
      path: relativeSource(readmePath),
      section: "Reusable template kinds",
      lines: [3, 16],
    },
    kinds: {
      Brand: {
        owns: ["identity color", "typography", "logo", "voice", "icon style"],
        excludes: ["page structure", "SVG roster"],
      },
      Style: {
        owns: [
          "communication method",
          "visual language",
          "composition rhythm",
          "information-expression defaults",
        ],
        excludes: [
          "official identity",
          "current-project application",
          "structure",
          "SVG roster",
        ],
      },
      Layout: {
        owns: [
          "brand-neutral canvas",
          "Master/Layout graph",
          "page types",
          "slots",
          "SVG roster",
        ],
        excludes: ["identity", "recurring application"],
      },
      Deck: {
        owns: [
          "recurring presentation-family application context",
          "integrated identity",
          "structure",
        ],
        excludes: [],
      },
    },
    power_point_objects_are_compilation_targets:
      "Theme values project from resolved identity; Layout rules project to Master/Layout/Placeholder topology, semantic roles, and spatial behavior.",
  },
  catalogs: Object.fromEntries(
    Object.entries(indexes).map(([kind, item]) => [
      kind,
      {
        index_path: item.path,
        index_sha256: item.sha256,
        index_entry_count: Object.keys(item.entries).length,
        entries: item.entries,
      },
    ]),
  ),
  non_template_resource_counts: {
    charts: {
      index_group_count: Object.keys(indexes.charts.entries).length,
      declared_chart_definitions: 33,
      source: { path: relativeSource(readmePath), line: 48 },
      classification:
        "Page-local, value-driven visualization family; not a reusable template kind.",
    },
    tables: {
      index_group_count: Object.keys(indexes.tables.entries).length,
      declared_table_types: 6,
      source: { path: relativeSource(readmePath), line: 48 },
      classification:
        "Page-local, row-by-column fact grid; not a reusable template kind.",
    },
    icons: {
      vector_count: 12027,
      library_count: 5,
      source: { path: relativeSource(readmePath), line: 52 },
      classification: "Asset library; not a reusable template kind.",
    },
  },
  intermediate_representation: {
    unified_normalized_ir: false,
    representation_chain: [
      {
        artifact: "Design Spec",
        representation:
          "Markdown with YAML frontmatter and page roster/content guidance",
        schema: schemaContracts.design_spec.path,
      },
      {
        artifact: "spec_lock",
        representation:
          "Project-level executable generation/export contract",
        schema: schemaContracts.spec_lock.path,
      },
      {
        artifact: "Per-page SVG",
        representation:
          "Prototype geometry, page/layout identity, slot groups, and data-pptx metadata",
        source_contract: "references/pptx-structure-interface.md",
      },
      {
        artifact: "Native Chart/Table payload",
        representation:
          "Optional payload for requested native visualization export; not present in the listed Layout prototype directories.",
        applicability: "Only when a native data-object path is requested.",
      },
    ],
    schema_contracts: schemaContracts,
  },
  composition_and_applicability: {
    independent_axes: {
      selection_source: {
        values: ["library", "explicit"],
        meaning:
          "Discovery provenance only; index-derived root versus exact unregistered root, with no semantic effect.",
      },
      internal_creation_strategy: {
        values: ["standard", "fidelity", "mirror"],
        meaning:
          "Implementation strategy; standard/fidelity author a contract, mirror preserves validated source facts.",
      },
      template_reuse_scope: {
        values: ["style", "layout", "mirror"],
        meaning:
          "Style-only remains Slide-local; layout/mirror can reuse structured Master/Layout topology.",
      },
      template_adherence: {
        values: ["strict", "adaptive"],
        meaning:
          "Strict preserves the prototype contract; adaptive may use only an explicitly permitted Layout and does not mutate a reused key.",
      },
      pptx_structure_mode: {
        values: ["flat", "structured"],
        applicability: {
          flat: "Free-design, brand-only, or style-scope route; omit structured roster sections.",
          structured:
            "Layout/Deck with layout or mirror reuse; declare Master, Layout, page assignment, and prototype provenance.",
        },
      },
    },
    precedence_and_inheritance: {
      template_kind_inheritance: "None; the four kinds are orthogonal.",
      combination:
        "Style may coexist with Layout/Deck. Style guides expression and does not override resolved identity or the structural plan; Layout/Deck owns reusable structure.",
      power_point_shape_chain:
        "Master background/atoms -> Layout background/atoms and placeholders -> Slide-local content; explicit metadata only.",
      background_override_order: ["Master", "Layout", "Slide"],
    },
    explicitness:
      "Do not infer Layout families, cluster pages, infer placeholders, repair missing metadata, or upgrade legacy contracts in place.",
    source_refs: [
      {
        path: relativeSource(readmePath),
        lines: [5, 16, 23, 26],
      },
      {
        path: "references/pptx-structure-interface.md",
        lines: [5, 24, 28, 32, 59, 61, 63, 65, 67],
      },
      {
        path: "templates/schemas/spec_lock.schema.json",
        rule_ids: [
          "style-is-flat",
          "layout-is-structured",
          "mirror-is-strict",
        ],
      },
    ],
  },
  geometry_and_capacity: {
    geometry_source:
      "SVG root viewBox and explicit data-pptx-bounds on each data-pptx-placeholder slot group.",
    coordinate_unit: "SVG user units",
    capacity:
      "Bounds are a geometric capacity zone, not a whitespace quota. The source does not encode a universal maximum character count or line count; those fields remain null rather than guessed.",
    source: {
      path: "references/pptx-structure-interface.md",
      lines: [45, 65, 67],
    },
  },
  layout_families: layoutMaps,
  totals: {
    layout_family_count: layoutCount,
    svg_prototype_count: pages.length,
    unique_page_type_count: allPageTypes.size,
    explicit_slot_count: slotCount,
    design_spec_token_count: tokenCount,
    registry_svg_count_mismatches: layoutMaps
      .filter((layout) => !layout.validation.svg_count_matches_registry)
      .map((layout) => layout.id),
    design_spec_page_count_mismatches: layoutMaps
      .filter((layout) => !layout.validation.design_spec_page_count_matches_registry)
      .map((layout) => layout.id),
    roster_missing_for_svg: layoutMaps.flatMap((layout) =>
      layout.validation.roster_missing_for_svg.map(
        (file) => layout.id + "/" + file,
      ),
    ),
    pages_missing_viewbox: pages
      .filter((page) => !page.view_box)
      .map((page) => page.path),
    page_types_missing_from_registry: layoutMaps.flatMap((layout) =>
      layout.validation.page_types_missing_from_registry.map(
        (file) => layout.id + "/" + file,
      ),
    ),
    pages_missing_design_spec_token_entry: layoutMaps.flatMap((layout) =>
      layout.validation.pages_missing_design_spec_token_entry.map(
        (file) => layout.id + "/" + file,
      ),
    ),
    slots_missing_valid_bounds: pages.flatMap((page) =>
      page.slots
        .filter((slot) => !slot.bounds)
        .map((slot) => page.path + "/" + slot.role),
    ),
  },
};

if (layoutCount !== 7 || pages.length !== 86 || allPageTypes.size !== 53) {
  throw new Error(
    "Unexpected inventory totals: " +
      JSON.stringify({
        layoutCount,
        pageCount: pages.length,
        pageTypes: allPageTypes.size,
      }),
  );
}
if (
  map.totals.registry_svg_count_mismatches.length ||
  map.totals.design_spec_page_count_mismatches.length ||
  map.totals.roster_missing_for_svg.length ||
  map.totals.pages_missing_viewbox.length ||
  map.totals.page_types_missing_from_registry.length ||
  map.totals.pages_missing_design_spec_token_entry.length ||
  map.totals.slots_missing_valid_bounds.length
) {
  throw new Error("Unmapped layout assets: " + JSON.stringify(map.totals));
}

const output = path.join(productRoot, "project_template_map.json");
await fs.writeFile(output, JSON.stringify(map, null, 2) + "\n", "utf8");
console.log(
  JSON.stringify({
    output,
    source_commit: sourceHead,
    totals: map.totals,
    catalog_counts: Object.fromEntries(
      Object.entries(indexes).map(([kind, item]) => [
        kind,
        Object.keys(item.entries).length,
      ]),
    ),
  }),
);
