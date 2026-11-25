import test from "node:test";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import {
  PRESETS,
  normalizeConfig,
  applyPreset,
  fmtTokens,
  renderTextBar,
  buildStatusModel,
} from "../mods/ccline/layout.js";

test("presets and config normalization cover all Herdr Line modes", () => {
  assert.ok(PRESETS.length >= 6);
  const def = normalizeConfig(null);
  assert.equal(def.preset, "cometix-pro");
  assert.equal(def.lines, 2);
  assert.equal(def.height, 48);

  const agy = applyPreset(def, "agyline");
  assert.equal(agy.lines, 1);
  assert.equal(agy.height, 30);
  assert.equal(agy.palette, "tokyo-night");

  const dash = applyPreset(def, "dashboard");
  assert.equal(dash.skin, "pill");
  assert.equal(dash.lines, 2);
});

test("token formatting and text bars match Herdr Line style", () => {
  assert.equal(fmtTokens(1000000), "1M");
  assert.equal(fmtTokens(142800), "142.8k");
  assert.equal(fmtTokens(512), "512");

  const bar = renderTextBar(40, 10, "blocks");
  assert.equal(bar.filled.length, 4);
  assert.equal(bar.empty.length, 6);
});

test("buildStatusModel renders 2-line and shrinks gracefully on narrow widths", () => {
  const sampleAgent = { name: "Devin", terminal: "t59", status: "working", isAgent: true };
  const sampleCollected = {
    adapter: "devin",
    source: "devin-db",
    sessionId: "session-demo-01",
    cwd: "/example-home/herdr-line",
    model: { id: "swe-2-1-max", displayName: "SWE-2.1 Max", family: "devin", window: 262144 },
    context: { tokens: 104857, window: 262144, percent: 40, cacheReadTokens: 100000 },
    cache: { hitRatio: 95.4, warm: true, expiresAt: Date.now() / 1000 + 200 },
    timing: { ttftMs: 3200, tokensPerSec: 152 },
    cost: { acu: 1.4 },
    vcs: { branch: "main", dirty: true, ahead: 1, added: 40, removed: 5 },
    mode: "bypass",
  };
  const ws = {
    homeDir: "/example-home",
    machine: "This computer",
    spaceAgents: [sampleAgent],
    activeAgentIndex: 0,
    workingSince: Date.now() - 45000,
    totalAgents: 3,
    blockedCount: 1,
    paletteHint: "⌘⇧P commands",
  };

  const wide = buildStatusModel({
    agent: sampleAgent,
    collected: sampleCollected,
    workspace: ws,
    config: normalizeConfig({ preset: "cometix-pro" }),
    herdrTheme: {},
    widthPx: 1400,
  });
  assert.equal(wide.rows.length, 2);
  assert.ok(wide.rows[0].left.some((i) => i.id === "model"));
  assert.ok(wide.rows[0].left.some((i) => i.id === "git"));
  assert.ok(wide.rows[1].left.some((i) => i.id === "context-bar"));
  assert.ok(wide.rows[1].right.some((i) => i.id === "needs-you"));

  const narrow = buildStatusModel({
    agent: sampleAgent,
    collected: sampleCollected,
    workspace: ws,
    config: normalizeConfig({ preset: "cometix", lines: 1 }),
    herdrTheme: {},
    widthPx: 420,
  });
  assert.equal(narrow.rows.length, 1);
  // High-priority items (agent/model/context/open-config) survive narrow width shrink
  assert.ok(narrow.rows[0].left.length >= 1);
});

test("Herdr Line branding retains legacy installation and preset interfaces", () => {
  const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url)));
  const meta = JSON.parse(readFileSync(new URL("../mods/ccline/mod.json", import.meta.url)));
  const keys = JSON.parse(readFileSync(new URL("../keys.json", import.meta.url)));
  assert.equal(pkg.name, "herdr-line");
  assert.equal(meta.palette[0].title, "Herdr Line: Configure Status Bar");
  assert.equal(meta.palette[0].args.name, "ccline");
  assert.equal(keys.global["cmd-alt-l"].args.name, "ccline");
  assert.equal(PRESETS.find(p => p.id === "cometix-pro").name, "Line Pro");
  assert.equal(PRESETS.find(p => p.id === "cometix").name, "Line Classic");
  assert.equal(normalizeConfig({ preset: "cometix" }).preset, "cometix");
});
