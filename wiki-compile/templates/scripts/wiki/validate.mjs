#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const rootDir = process.cwd();
const manifestPath = path.join(rootDir, "docs/wiki/manifest.json");
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));

const failures = [];
const warnings = [];

function readFile(relPath) {
  return fs.readFileSync(path.join(rootDir, relPath), "utf8");
}

function exists(relPath) {
  return fs.existsSync(path.join(rootDir, relPath));
}

function walk(dirPath, extensions, result = []) {
  if (!fs.existsSync(dirPath)) {
    return result;
  }

  for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, extensions, result);
      continue;
    }

    if (extensions.has(path.extname(entry.name))) {
      result.push(fullPath);
    }
  }

  return result;
}

function rel(absPath) {
  return path.relative(rootDir, absPath).split(path.sep).join("/");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function fail(message) {
  failures.push(message);
}

function warn(message) {
  warnings.push(message);
}

function parseLog(logConfig) {
  const content = readFile(logConfig.path);
  const heading = new RegExp(
    `^## (?:\\[(\\d{4}-\\d{2}-\\d{2})\\] )?(${logConfig.idPrefix}-\\d{3}): (.+)$`,
    "gm",
  );
  const entries = [];
  let match;

  while ((match = heading.exec(content))) {
    entries.push({
      date: match[1] ?? null,
      id: match[2],
      number: Number(match[2].split("-")[1]),
      title: match[3],
    });
  }

  return entries;
}

function validateLog(logConfig) {
  if (!exists(logConfig.path)) {
    fail(`Missing log file: ${logConfig.path}`);
    return { count: 0 };
  }

  const entries = parseLog(logConfig);
  const seen = new Map();

  for (const entry of entries) {
    if (seen.has(entry.id)) {
      fail(
        `${logConfig.path}: duplicate ${entry.id} (${seen.get(entry.id)} / ${entry.title})`,
      );
    } else {
      seen.set(entry.id, entry.title);
    }
  }

  let previousNumber = -1;
  for (const entry of entries) {
    if (entry.number < previousNumber) {
      warn(`${logConfig.path}: out-of-order ID detected at ${entry.id}`);
      break;
    }
    previousNumber = entry.number;
  }

  return { count: entries.length };
}

function validateMetadata(relPath) {
  const content = readFile(relPath);
  const header = content.split("\n").slice(0, 12).join("\n");
  for (const label of manifest.wiki.requiredMetadata) {
    const pattern = new RegExp(`^\\*\\*${escapeRegExp(label)}:\\*\\* .+`, "m");
    if (!pattern.test(header)) {
      fail(`${relPath}: missing metadata line "${label}"`);
    }
  }
}

function validateLinks(relPath) {
  const content = readFile(relPath);
  const linkPattern = /\[[^\]]+\]\(([^)]+\.md)\)/g;
  let match;

  while ((match = linkPattern.exec(content))) {
    const target = match[1];
    if (/^https?:\/\//.test(target)) {
      continue;
    }
    const resolved = path.normalize(path.join(path.dirname(relPath), target));
    if (!exists(resolved)) {
      fail(`${relPath}: broken markdown link -> ${target}`);
    }
  }
}

function extractMetric(content, label) {
  const regex = new RegExp(`^- ${escapeRegExp(label)}: (\\d+)$`, "m");
  const match = content.match(regex);
  return match ? Number(match[1]) : null;
}

function validateSnapshot(relPath, expectedMetrics) {
  const content = readFile(relPath);
  for (const [label, expectedValue] of Object.entries(expectedMetrics)) {
    const actualValue = extractMetric(content, label);
    if (actualValue === null) {
      fail(`${relPath}: missing snapshot metric "${label}"`);
      continue;
    }
    if (actualValue !== expectedValue) {
      fail(
        `${relPath}: snapshot metric "${label}" is ${actualValue}, expected ${expectedValue}`,
      );
    }
  }
}

function validateIndexArticleList() {
  const content = readFile(manifest.wiki.index);
  for (const article of manifest.wiki.articles) {
    if (!content.includes(`(${article})`)) {
      fail(`${manifest.wiki.index}: missing article link for ${article}`);
    }
  }
}

function countResearchDocuments() {
  let total = 0;
  for (const sourceRoot of manifest.sourceRoots) {
    const extensions = new Set(sourceRoot.extensions);
    const absRoot = path.join(rootDir, sourceRoot.path);
    total += walk(absRoot, extensions).length;
  }
  return total;
}

function validateManifestPaths() {
  for (const log of manifest.logs) {
    if (!exists(log.path)) {
      fail(`Manifest path missing: ${log.path}`);
    }
  }

  for (const sourceRoot of manifest.sourceRoots) {
    if (!exists(sourceRoot.path)) {
      fail(`Manifest source root missing: ${sourceRoot.path}`);
    }
  }

  for (const sourceFile of manifest.sourceFiles) {
    if (!exists(sourceFile)) {
      fail(`Manifest source file missing: ${sourceFile}`);
    }
  }

  for (const wikiFile of manifest.wiki.metadataFiles) {
    if (!exists(wikiFile)) {
      fail(`Manifest wiki file missing: ${wikiFile}`);
    }
  }
}

validateManifestPaths();

const counts = {
  compiledArticles: manifest.wiki.articles.length,
  researchDocuments: countResearchDocuments(),
  lessonEntries: 0,
  decisionEntries: 0,
};

for (const logConfig of manifest.logs) {
  const result = validateLog(logConfig);
  if (logConfig.idPrefix === "L") {
    counts.lessonEntries = result.count;
  }
  if (logConfig.idPrefix === "AD") {
    counts.decisionEntries = result.count;
  }
}

for (const relPath of manifest.wiki.metadataFiles) {
  validateMetadata(relPath);
}

const wikiFiles = fs
  .readdirSync(path.join(rootDir, manifest.wiki.directory))
  .filter((name) => name.endsWith(".md"))
  .map((name) => path.posix.join(manifest.wiki.directory, name));

for (const wikiFile of wikiFiles) {
  validateLinks(wikiFile);
}

const expectedSnapshot = {
  [manifest.wiki.snapshotLabels.compiledArticles]: counts.compiledArticles,
  [manifest.wiki.snapshotLabels.researchDocuments]: counts.researchDocuments,
  [manifest.wiki.snapshotLabels.lessonEntries]: counts.lessonEntries,
  [manifest.wiki.snapshotLabels.decisionEntries]: counts.decisionEntries,
};

validateSnapshot(manifest.wiki.index, expectedSnapshot);
validateSnapshot(manifest.wiki.health, expectedSnapshot);
validateIndexArticleList();

console.log("Wiki integrity summary");
console.log(`- Compiled articles: ${counts.compiledArticles}`);
console.log(`- Research documents: ${counts.researchDocuments}`);
console.log(`- Lesson entries: ${counts.lessonEntries}`);
console.log(`- Decision entries: ${counts.decisionEntries}`);

if (warnings.length > 0) {
  console.log("\nWarnings");
  for (const message of warnings) {
    console.log(`- ${message}`);
  }
}

if (failures.length > 0) {
  console.error("\nFailures");
  for (const message of failures) {
    console.error(`- ${message}`);
  }
  process.exit(1);
}

console.log("\nWiki integrity check passed.");
