// Herdr-native Herdr Line plugin:
//   1. Workspace bottom status bar (auto-tracks any active Agent across tabs/panes)
//   2. Full interactive Configurator & Live Preview dialog (`mod.open { name: "ccline" }`)
import { View, div, svg, image } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import {
  spaces,
  agents as liveAgents,
  panes,
  terminals,
  focused,
  theme,
  window as appWindow,
  settings,
  keys,
  layout,
  shared,
  setShared,
  props,
  run,
  openOverlay,
  closeOverlay,
  exec,
  home,
  appHome,
  checking,
} from "herdr";
import {
  PRESETS,
  SKINS,
  BAR_STYLES,
  PALETTE_DEFS,
  SEGMENT_META,
  normalizeConfig,
  applyPreset,
  withAlpha,
  buildStatusModel,
} from "./layout.js";

// Legacy persisted keys and mod ID are retained for existing installations.
const CONFIG_KEY = "ccline.config";
const SNAPSHOT_KEY = "ccline.snapshot";

function findNode(node, id) {
  if (!node) return null;
  if (node.id === id) return node;
  for (const child of node.children ?? []) {
    const found = findNode(child, id);
    if (found) return found;
  }
  return null;
}

function programIcon(prog, size, fallbackColor) {
  if (!prog?.icon) return null;
  return prog.tint
    ? svg(prog.icon).size(size).flex_none().text_color(fallbackColor)
    : image(prog.icon).w(size).h(size).flex_none();
}

function looksLikeAgent(paneOrTerm) {
  if (!paneOrTerm) return false;
  if (paneOrTerm.program?.agent || paneOrTerm.status || paneOrTerm.app) return true;
  if (paneOrTerm.program?.shell) return false;
  const s = `${paneOrTerm.program?.key ?? ""} ${paneOrTerm.program?.name ?? ""}`.toLowerCase();
  return /(claude|codex|devin|antigravity|\bagy\b|\bpi\b|\bomp\b|grok|cursor|opencode|kiro|aider)/.test(s);
}

export default class HerdrLine extends View {
  init(_props, cx) {
    this.widthPx = 1120;
    this.busy = false;
    this.pinnedTerminal = null;
    this.collected = {};
    this.lastSyncedHeight = null;
    this.configTab = "presets";
    if (checking()) return;

    const isOverlay = Boolean(props()?.overlay);
    if (!isOverlay) {
      this.poll(cx);
      cx.timer.every(2000, (cx) => {
        if (appWindow()?.visible === false) return;
        this.poll(cx);
      });
      cx.timer.every(1000, (cx) => {
        if (appWindow()?.visible === false) return;
        if (this.needsLiveTick()) cx.notify();
      });
    }
  }

  config() {
    return normalizeConfig(shared(CONFIG_KEY));
  }

  saveConfig(next, cx) {
    const normalized = normalizeConfig(next);
    setShared(CONFIG_KEY, normalized);
    this.syncBarHeight(normalized);
    cx.notify();
  }

  syncBarHeight(cfg) {
    if (checking() || !cfg.autoSyncHeight) return;
    const statusNode = findNode(layout(), "status");
    if (!statusNode || statusNode.content?.mod !== "ccline") return;
    const currentPx = statusNode.size?.px;
    if (currentPx !== cfg.height && this.lastSyncedHeight !== cfg.height) {
      this.lastSyncedHeight = cfg.height;
      try {
        run("layout.resize", { id: "status", px: cfg.height });
      } catch {}
    }
  }

  needsLiveTick() {
    const space = spaces().find((s) => s.active);
    const activeTab = space?.tabs?.find((t) => t.active);
    if (Number.isFinite(activeTab?.working_since)) return true;
    const nowSec = Date.now() / 1000;
    for (const item of Object.values(this.collected)) {
      const exp = item?.cache?.expiresAt;
      if (typeof exp === "number" && exp > nowSec) return true;
    }
    return false;
  }

  paletteHint() {
    const mac = appWindow()?.platform === "macos";
    const mod = {
      cmd: mac ? "⌘" : "Ctrl+",
      ctrl: mac ? "⌃" : "Ctrl+",
      shift: mac ? "⇧" : "Shift+",
      alt: mac ? "⌥" : "Alt+",
      option: mac ? "⌥" : "Alt+",
    };
    const b = keys().find((k) => k.section === "global" && k.action === "app.palette");
    const parts = b && b.keys.endsWith("--") ? [...b.keys.slice(0, -2).split("-"), "-"] : b?.keys.split("-");
    const key = parts && parts.map((p) => mod[p.toLowerCase()] ?? p.toUpperCase()).join("");
    return key ? `${key} commands` : "commands";
  }

  spaceContext() {
    const space = spaces().find((s) => s.active) || spaces()[0] || null;
    const allAgents = liveAgents();
    const allPanes = panes();
    const allTerms = terminals();
    const termMap = new Map(allTerms.map((t) => [t.address, t]));
    const agentMap = new Map(allAgents.map((a) => [a.address, a]));

    const tabIds = new Set((space?.tabs || []).map((t) => t.id));
    const spacePanes = allPanes.filter((p) => p.terminal && tabIds.has(p.tab));
    const spaceAgents = spacePanes
      .filter((p) => looksLikeAgent(p) || agentMap.has(p.terminal))
      .map((p) => {
        const a = agentMap.get(p.terminal);
        const term = termMap.get(p.terminal);
        return {
          pane: p.pane,
          terminal: p.terminal,
          tab: p.tab,
          name: p.name || p.program?.name || a?.program?.name || p.title || "Agent",
          cwd: p.cwd || term?.cwd || space?.folder || null,
          branch: p.branch || space?.branch || null,
          status: p.status || a?.status || "idle",
          app: p.app || a?.app || null,
          program: p.program || a?.program || term?.program || null,
          focused: p.focused,
          isAgent: true,
          isShell: Boolean(p.program?.shell),
          pid: term?.foreground?.pid || term?.pid || null,
        };
      });

    const foc = focused();
    const activeTab = space?.tabs?.find((t) => t.active) || null;
    const cfg = this.config();

    let target = null;
    // 1. User manually cycled/pinned an agent still alive in this space
    if (this.pinnedTerminal) {
      target = spaceAgents.find((a) => a.terminal === this.pinnedTerminal) || null;
      if (!target) this.pinnedTerminal = null;
    }
    // 2. If focused pane itself is an agent, follow it immediately (and clear stale pin if user clicked another agent)
    const focusedAgent = spaceAgents.find((a) => a.terminal === foc?.terminal || a.pane === foc?.pane);
    if (focusedAgent) {
      this.pinnedTerminal = null;
      target = focusedAgent;
    }
    // 3. Smart follow: another agent in the active tab, then most recently active agent in space
    if (!target && cfg.followMode === "smart") {
      target =
        spaceAgents.find((a) => a.tab === activeTab?.id && a.status === "working") ||
        spaceAgents.find((a) => a.tab === activeTab?.id) ||
        spaceAgents.find((a) => a.status === "working") ||
        spaceAgents[0] ||
        null;
    }
    // 4. Fallback to focused non-agent shell pane so workspace dir & Git still display cleanly
    if (!target) {
      const shellPane =
        spacePanes.find((p) => p.pane === foc?.pane || p.terminal === foc?.terminal) ||
        spacePanes.find((p) => p.tab === activeTab?.id) ||
        spacePanes[0];
      if (shellPane) {
        const term = termMap.get(shellPane.terminal);
        target = {
          pane: shellPane.pane,
          terminal: shellPane.terminal,
          tab: shellPane.tab,
          name: shellPane.name || shellPane.program?.name || "shell",
          cwd: shellPane.cwd || space?.folder || null,
          branch: shellPane.branch || space?.branch || null,
          status: shellPane.status || "idle",
          app: shellPane.app || null,
          program: shellPane.program || null,
          focused: shellPane.focused,
          isAgent: false,
          isShell: true,
          pid: term?.foreground?.pid || term?.pid || null,
        };
      }
    }

    const activeAgentIndex = target
      ? Math.max(0, spaceAgents.findIndex((a) => a.terminal === target.terminal))
      : 0;
    const subagentCount = target?.terminal
      ? allTerms.filter((t) => t.parent === target.terminal).length
      : 0;
    const targetTab = space?.tabs?.find((t) => t.id === target?.tab) || activeTab;
    const blockedAgent = allAgents.find((a) => a.status === "blocked") || null;

    return {
      space,
      target,
      spaceAgents,
      activeAgentIndex,
      subagentCount,
      workingSince: targetTab?.working_since ?? null,
      totalAgents: allAgents.length,
      blockedCount: allAgents.filter((a) => a.status === "blocked").length,
      blockedTerminal: blockedAgent?.address || null,
    };
  }

  poll(cx) {
    if (this.busy || checking()) return;
    const sc = this.spaceContext();
    if (sc.space?.machine) return; // Remote SSH spaces use live Herdr metadata without local DB reads

    const candidates = sc.spaceAgents.length > 0 ? sc.spaceAgents : sc.target ? [sc.target] : [];
    if (candidates.length === 0) return;

    const targetsPayload = candidates.slice(0, 8).map((item) => ({
      terminal: String(item.terminal || "").split("/").pop(),
      pid: item.pid,
      cwd: item.cwd,
      app: item.app,
      programKey: item.program?.key,
      programName: item.program?.name,
      isAgent: item.isAgent,
      isShell: item.isShell,
    }));

    const cfg = this.config();
    const script = `${appHome()}/mods/ccline/collector.py`;
    this.busy = true;
    cx.spawn(async (cx) => {
      try {
        const res = await exec(
          "python3",
          [
            script,
            "collect",
            "--targets",
            JSON.stringify(targetsPayload),
            "--config",
            JSON.stringify({ models: cfg.models }),
          ],
          { timeout: 6000 }
        );
        if (res.code === 0 && res.stdout) {
          const parsed = JSON.parse(res.stdout);
          if (parsed?.ok && parsed.agents) {
            this.collected = { ...this.collected, ...parsed.agents };
            const activeKey = String(sc.target?.terminal || "").split("/").pop();
            if (activeKey && this.collected[activeKey]) {
              setShared(SNAPSHOT_KEY, {
                agent: sc.target,
                collected: this.collected[activeKey],
              });
            }
          }
        }
      } catch {
        // Keep previous snapshot on transient errors
      } finally {
        this.busy = false;
        cx.notify();
      }
    });
  }

  handleAction(action, sc, cx) {
    if (!action) return;
    if (action === "open-config") {
      openOverlay({ mod: "ccline", kind: "dialog", width: 780, height: 640 });
    } else if (action === "open-palette") {
      run("app.palette");
    } else if (action === "jump-blocked" && sc.blockedTerminal) {
      run("agent.focus", { terminal: sc.blockedTerminal });
    } else if (action === "focus-agent" && sc.target?.terminal) {
      run("pane.focus", { terminal: sc.target.terminal });
    } else if (action === "cycle-agent" && sc.spaceAgents.length > 1) {
      const next = sc.spaceAgents[(sc.activeAgentIndex + 1) % sc.spaceAgents.length];
      if (next) {
        this.pinnedTerminal = next.terminal;
        run("pane.focus", { terminal: next.terminal });
        cx.notify();
      }
    }
  }

  categoryColor(pal, item) {
    if (item.severity === "crit") return pal.crit;
    if (item.severity === "warn") return pal.warn;
    if (item.severity === "ok") return pal.ok;
    return pal[item.category] || pal.text;
  }

  renderSegment(pal, skin, item, sc, indexKey, previewOnly = false) {
    const v = item.activeVariant;
    if (!v) return null;
    const catColor = this.categoryColor(pal, item);
    const isFilled = skin === "powerline";
    const isPill = skin === "pill";
    const isBracket = skin === "bracket";

    const fgColor = isFilled ? pal.onFill : v.bright ? pal.text : pal.muted;
    const iconColor = isFilled ? pal.onFill : catColor;

    const row = h_flex()
      .id(`seg-${indexKey}-${item.id}`)
      .flex_none()
      .items_center()
      .gap(4)
      .when(isPill, (el) =>
        el
          .px(7)
          .h(20)
          .rounded(6)
          .bg(withAlpha(catColor, "1f"))
          .border(1)
          .border_color(withAlpha(catColor, "42"))
      )
      .when(isFilled, (el) => el.px(8).h(20).rounded(3).bg(catColor))
      .when(!isPill && !isFilled && Boolean(item.action), (el) =>
        el.px(4).h(20).rounded(4)
      )
      .when(Boolean(item.action) && !previewOnly, (el) =>
        el
          .cursor_pointer()
          .hover((s) => s.bg(isFilled ? withAlpha(catColor, "dd") : withAlpha(pal.text, "14")))
          .on_click((_e, cx) => {
            cx.stop_propagation();
            this.handleAction(item.action, sc, cx);
          })
      )
      .when(Boolean(item.tooltip), (el) => el.tooltip(item.tooltip));

    if (isBracket) {
      row.child(div().flex_none().text_color(pal.dim).child("["));
    }

    // Agent live status spinner / program icon
    if (item.id === "agent") {
      if (item.agentStatus === "working") {
        row.child(
          svg("mods/workspace-chrome/spinner.svg")
            .size(12)
            .flex_none()
            .text_color(isFilled ? pal.onFill : pal.ok)
            .spin(900)
        );
      } else {
        const pic = programIcon(item.program, 13, iconColor);
        if (pic) row.child(pic);
      }
    } else if (v.icon) {
      row.child(svg(v.icon).size(12.5).flex_none().text_color(iconColor));
    }

    if (v.bar) {
      row.child(
        h_flex()
          .flex_none()
          .items_center()
          .text_size(10.5)
          .child(div().text_color(isFilled ? pal.onFill : catColor).child(v.bar.filled))
          .child(div().text_color(isFilled ? withAlpha(pal.onFill, "55") : withAlpha(pal.dim, "88")).child(v.bar.empty))
      );
    }

    if (v.text) {
      row.child(
        div()
          .flex_none()
          .when(Boolean(v.bright || isFilled), (el) => el.font_medium())
          .text_color(fgColor)
          .child(v.text)
      );
    }

    if (v.subtext) {
      row.child(
        div()
          .flex_none()
          .text_size(11)
          .text_color(isFilled ? withAlpha(pal.onFill, "cc") : pal.dim)
          .child(v.subtext)
      );
    }

    if (isBracket) {
      row.child(div().flex_none().text_color(pal.dim).child("]"));
    }

    return row;
  }

  renderSide(pal, skin, items, sc, rowKey, previewOnly = false) {
    const children = [];
    const plain = skin === "plain";
    items.forEach((item, idx) => {
      const el = this.renderSegment(pal, skin, item, sc, `${rowKey}-${idx}`, previewOnly);
      if (!el) return;
      if (children.length > 0 && plain) {
        children.push(div().flex_none().px(2).text_color(pal.separator).child("│"));
      }
      children.push(el);
    });
    return h_flex()
      .flex_none()
      .gap(plain ? 4 : skin === "powerline" ? 3 : 5)
      .items_center()
      .children(children);
  }

  renderBarSurface(model, sc, previewOnly = false) {
    const { config: cfg, palette: pal, rows } = model;
    return v_flex()
      .size_full()
      .px(12)
      .py(cfg.lines === 2 ? 3 : 0)
      .justify_center()
      .gap(cfg.lines === 2 ? 2 : 0)
      .bg(pal.bg)
      .when(!previewOnly, (el) => el.border_t(1).border_color(pal.border))
      .when(previewOnly, (el) => el.rounded(8).border(1).border_color(pal.border).py(6))
      .text_size(11.8)
      .children(
        rows.map((r, rIdx) =>
          h_flex()
            .min_h(cfg.lines === 2 ? 19 : 24)
            .w("100%")
            .min_w(0)
            .items_center()
            .justify_between()
            .gap(10)
            .overflow_hidden()
            .child(this.renderSide(pal, cfg.skin, r.left, sc, `r${rIdx}l`, previewOnly))
            .child(this.renderSide(pal, cfg.skin, r.right, sc, `r${rIdx}r`, previewOnly))
        )
      );
  }

  renderConfigurator(cx) {
    const t = theme();
    const cfg = this.config();
    const overlayId = props()?.overlay;
    const snap = shared(SNAPSHOT_KEY) || {};

    const sampleCollected = snap.collected || {
      adapter: "claude-code",
      source: "preview",
      sessionId: "herdr-line-demo-preview",
      cwd: `${home()}/demo-project`,
      model: { id: "claude-opus-5-5[1m]", displayName: "Opus 5.5 1M", effort: "xHigh", family: "claude", window: 1000000 },
      context: { tokens: 142800, window: 1000000, percent: 14.3, inputTokens: 8200, cacheReadTokens: 134600, outputTokens: 1240 },
      cache: { hitRatio: 94.2, warm: true, expiresAt: Date.now() / 1000 + 262 },
      timing: { ttftMs: 2400, tokensPerSec: 118 },
      quota: { "5H": { percent: 24, resetsAt: Date.now() / 1000 + 9420 }, "7D": { percent: 41 } },
      cost: { totalUsd: 0.48, estimated: true },
      vcs: { branch: "main", dirty: true, ahead: 2, behind: 0, added: 86, removed: 12 },
      mode: "auto",
      activity: { subagents: 2 },
    };
    const sampleAgent = snap.agent || {
      name: "Claude Code",
      terminal: "t1",
      status: "working",
      isAgent: true,
    };
    const previewModel = buildStatusModel({
      agent: sampleAgent,
      collected: sampleCollected,
      workspace: {
        homeDir: home(),
        machine: "This computer",
        totalAgents: Math.max(1, liveAgents().length),
        blockedCount: 0,
        spaceAgents: [sampleAgent],
        activeAgentIndex: 0,
        workingSince: Date.now() - 83000,
        paletteHint: this.paletteHint(),
      },
      config: cfg,
      herdrTheme: t,
      widthPx: 720,
    });

    const pillBtn = (id, label, active, onClick) =>
      h_flex()
        .id(id)
        .h(28)
        .px(10)
        .rounded(6)
        .items_center()
        .cursor_pointer()
        .text_size(12)
        .border(1)
        .border_color(active ? t.accent : t.border)
        .bg(active ? withAlpha(t.accent, "24") : t.surface)
        .text_color(active ? t.foreground : t.muted)
        .hover((s) => s.bg(t.hover).text_color(t.foreground))
        .on_click(onClick)
        .child(label);

    const tabBtn = (id, label) =>
      pillBtn(`cfg-tab-${id}`, label, this.configTab === id, (_e, cx) => {
        this.configTab = id;
        cx.notify();
      });

    // Build rows of 2 cards for presets or segment switches
    const presetRows = [];
    for (let i = 0; i < PRESETS.length; i += 2) {
      const pair = PRESETS.slice(i, i + 2);
      presetRows.push(
        h_flex()
          .gap(8)
          .children(
            pair.map((p) => {
              const selected = cfg.preset === p.id;
              return v_flex()
                .id(`preset-${p.id}`)
                .flex_1()
                .p(10)
                .gap(4)
                .rounded(8)
                .cursor_pointer()
                .border(1)
                .border_color(selected ? t.accent : t.border)
                .bg(selected ? withAlpha(t.accent, "1c") : t.surface)
                .hover((s) => s.bg(t.hover))
                .on_click((_e, cx) => this.saveConfig(applyPreset(cfg, p.id), cx))
                .child(
                  h_flex()
                    .justify_between()
                    .items_center()
                    .child(div().text_size(12.8).font_semibold().text_color(t.foreground).child(p.name))
                    .child(
                      div()
                        .px(6)
                        .py(1)
                        .rounded(4)
                        .bg(t.raised)
                        .text_size(10.5)
                        .text_color(t.muted)
                        .child(`${p.lines}L · ${p.skin}`)
                    )
                )
                .child(div().text_size(11.2).text_color(t.muted).child(p.summary));
            })
          )
      );
    }

    const segRows = [];
    for (let i = 0; i < SEGMENT_META.length; i += 2) {
      const pair = SEGMENT_META.slice(i, i + 2);
      segRows.push(
        h_flex()
          .gap(8)
          .children(
            pair.map((s) => {
              const on = Boolean(cfg.segments[s.key]);
              return h_flex()
                .id(`seg-toggle-${s.key}`)
                .flex_1()
                .h(32)
                .px(10)
                .rounded(7)
                .items_center()
                .justify_between()
                .cursor_pointer()
                .border(1)
                .border_color(on ? withAlpha(t.accent, "88") : t.border)
                .bg(on ? withAlpha(t.accent, "16") : t.surface)
                .hover((el) => el.bg(t.hover))
                .on_click((_e, cx) =>
                  this.saveConfig(
                    {
                      ...cfg,
                      segments: { ...cfg.segments, [s.key]: !on },
                    },
                    cx
                  )
                )
                .child(div().text_size(12).text_color(on ? t.foreground : t.muted).child(s.label))
                .child(
                  div()
                    .px(6)
                    .py(1)
                    .rounded(4)
                    .bg(on ? t.accent : t.raised)
                    .text_size(10.5)
                    .font_semibold()
                    .text_color(on ? t.solid_foreground : t.dim)
                    .child(on ? "ON" : "OFF")
                );
            })
          )
      );
    }

    const paletteIds = Object.keys(PALETTE_DEFS);
    const paletteRows = [paletteIds.slice(0, 4), paletteIds.slice(4)];

    return v_flex()
      .id("herdr-line-configurator")
      .size_full()
      .bg(t.popover || t.background)
      .text_color(t.foreground)
      .child(
        // Top Header
        h_flex()
          .h(46)
          .flex_none()
          .px(16)
          .items_center()
          .justify_between()
          .border_b(1)
          .border_color(t.border)
          .child(
            h_flex()
              .gap(8)
              .items_center()
              .child(svg("mods/ccline/icons/sliders.svg").size(15).text_color(t.accent))
              .child(div().text_size(14).font_semibold().child("Herdr Line · Herdr 全局状态栏配置"))
          )
          .child(
            h_flex()
              .gap(8)
              .items_center()
              .child(
                pillBtn("cfg-reset", "恢复默认", false, (_e, cx) =>
                  this.saveConfig(applyPreset({}, "cometix-pro"), cx)
                )
              )
              .when(Boolean(overlayId), (el) =>
                el.child(
                  pillBtn("cfg-close", "完成", true, () => closeOverlay(overlayId))
                )
              )
          )
      )
      .child(
        // Live Preview Region
        v_flex()
          .flex_none()
          .px(16)
          .py(10)
          .gap(6)
          .bg(t.chrome)
          .border_b(1)
          .border_color(t.border)
          .child(
            h_flex()
              .justify_between()
              .items_center()
              .text_size(11)
              .text_color(t.dim)
              .child("实时预览 · Live Preview")
              .child(`${cfg.lines} 行布局 (${cfg.height}px) · 皮肤: ${cfg.skin} · 配色: ${PALETTE_DEFS[cfg.palette]?.name || cfg.palette}`)
          )
          .child(div().h(cfg.lines === 2 ? 54 : 34).w("100%").child(this.renderBarSurface(previewModel, {}, true)))
      )
      .child(
        // Navigation Tabs
        h_flex()
          .h(40)
          .flex_none()
          .px(16)
          .gap(8)
          .items_center()
          .border_b(1)
          .border_color(t.border)
          .child(tabBtn("presets", "预设方案 (Presets)"))
          .child(tabBtn("style", "外观与皮肤 (Style & Palette)"))
          .child(tabBtn("segments", "指标开关 (Segments)"))
      )
      .child(
        // Scrollable Body
        v_flex()
          .flex_1()
          .min_h(0)
          .p(16)
          .gap(12)
          .overflow_y_scrollbar()
          .when(this.configTab === "presets", (el) => el.children(presetRows))
          .when(this.configTab === "style", (el) =>
            el
              .child(div().text_size(12).font_semibold().text_color(t.muted).child("行数与底栏高度"))
              .child(
                h_flex()
                  .gap(8)
                  .child(
                    pillBtn("lines-1", "单行紧凑 (30px)", cfg.lines === 1, (_e, cx) =>
                      this.saveConfig({ ...cfg, lines: 1, height: 30 }, cx)
                    )
                  )
                  .child(
                    pillBtn("lines-2", "双行完整 (48px)", cfg.lines === 2, (_e, cx) =>
                      this.saveConfig({ ...cfg, lines: 2, height: 48 }, cx)
                    )
                  )
                  .child(
                    pillBtn(
                      "follow-mode",
                      cfg.followMode === "smart" ? "追踪模式: 智能跟随活跃 Agent" : "追踪模式: 仅当前聚焦窗格",
                      cfg.followMode === "smart",
                      (_e, cx) =>
                        this.saveConfig(
                          { ...cfg, followMode: cfg.followMode === "smart" ? "focused" : "smart" },
                          cx
                        )
                    )
                  )
              )
              .child(div().text_size(12).font_semibold().text_color(t.muted).child("分段皮肤 (Skin)"))
              .child(
                h_flex()
                  .gap(8)
                  .children(
                    SKINS.map((s) =>
                      pillBtn(`skin-${s.id}`, s.name, cfg.skin === s.id, (_e, cx) =>
                        this.saveConfig({ ...cfg, skin: s.id }, cx)
                      )
                    )
                  )
              )
              .child(div().text_size(12).font_semibold().text_color(t.muted).child("进度条字符集 (Bar Glyphs)"))
              .child(
                h_flex()
                  .gap(8)
                  .children(
                    BAR_STYLES.map((b) =>
                      pillBtn(`bar-${b.id}`, b.name, cfg.barStyle === b.id, (_e, cx) =>
                        this.saveConfig({ ...cfg, barStyle: b.id }, cx)
                      )
                    )
                  )
              )
              .child(div().text_size(12).font_semibold().text_color(t.muted).child("主题配色板 (Palette)"))
              .children(
                paletteRows.map((rowIds, idx) =>
                  h_flex()
                    .id(`pal-row-${idx}`)
                    .gap(8)
                    .children(
                      rowIds.map((pid) =>
                        pillBtn(`pal-${pid}`, PALETTE_DEFS[pid].name, cfg.palette === pid, (_e, cx) =>
                          this.saveConfig({ ...cfg, palette: pid }, cx)
                        )
                      )
                    )
                )
              )
          )
          .when(this.configTab === "segments", (el) => el.children(segRows))
      );
  }

  render(cx) {
    if (props()?.overlay) {
      return this.renderConfigurator(cx);
    }

    const t = theme();
    const cfg = this.config();
    this.syncBarHeight(cfg);

    const sc = this.spaceContext();
    const bareTerm = String(sc.target?.terminal || "").split("/").pop();
    const collected = (bareTerm && this.collected[bareTerm]) || {};
    const zoom = Number(settings()?.zoom) || 1;

    const model = buildStatusModel({
      agent: sc.target,
      collected,
      workspace: {
        homeDir: home(),
        folder: sc.space?.folder || null,
        branch: sc.space?.branch || null,
        machine: sc.space?.machine || "This computer",
        spaceAgents: sc.spaceAgents,
        activeAgentIndex: sc.activeAgentIndex,
        subagentCount: sc.subagentCount,
        workingSince: sc.workingSince,
        totalAgents: sc.totalAgents,
        blockedCount: sc.blockedCount,
        paletteHint: this.paletteHint(),
      },
      config: cfg,
      herdrTheme: t,
      widthPx: this.widthPx,
    });

    return div()
      .id("herdr-line-bar")
      .size_full()
      .on_size_change((size, cx) => {
        const logicalWidth = Math.round(size.width / zoom);
        if (Math.abs(logicalWidth - this.widthPx) >= 12) {
          this.widthPx = logicalWidth;
          cx.notify();
        }
      })
      .child(this.renderBarSurface(model, sc, false));
  }
}
