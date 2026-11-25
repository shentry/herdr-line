// Pure CCometixLine layout, preset, palette, skin, and responsive fit engine.
// Zero host-module imports so this module runs identically inside Herdr (gpui-kit) and Node tests.

export const PRESETS = [
  {
    id: "cometix-pro",
    name: "Cometix Pro",
    lines: 2,
    height: 48,
    skin: "plain",
    palette: "herdr",
    barStyle: "blocks",
    summary: "双行完整形态：模型/目录/Git/上下文/缓存 + 速率/计量条/配额/工作区汇总",
  },
  {
    id: "cometix",
    name: "Cometix Classic",
    lines: 1,
    height: 30,
    skin: "plain",
    palette: "herdr",
    barStyle: "blocks",
    summary: "经典单行：左模型·目录·Git·上下文·缓存，右配额·花费·工作区控制",
  },
  {
    id: "agyline",
    name: "Agyline",
    lines: 1,
    height: 30,
    skin: "plain",
    palette: "tokyo-night",
    barStyle: "shapes",
    summary: "agyline 风格：紧凑单行，右对齐模式·子智能体·5H/7D 配额·会话花费",
  },
  {
    id: "dashboard",
    name: "Dashboard Pill",
    lines: 2,
    height: 50,
    skin: "pill",
    palette: "catppuccin-mocha",
    barStyle: "shapes",
    summary: "胶囊仪表盘：Catppuccin 圆角胶囊分段，上下双行全指标展示",
  },
  {
    id: "powerline",
    name: "Powerline",
    lines: 1,
    height: 30,
    skin: "powerline",
    palette: "tokyo-night",
    barStyle: "blocks",
    summary: "Powerline 色块：Tokyo Night 高对比实心色块拼接",
  },
  {
    id: "minimal",
    name: "Minimal",
    lines: 1,
    height: 28,
    skin: "plain",
    palette: "herdr",
    barStyle: "dots",
    summary: "极简模式：仅保留当前 Agent、模型、上下文百分比、缓存与花费",
  },
];

export const SKINS = [
  { id: "plain", name: "Plain │" },
  { id: "pill", name: "Pill 胶囊" },
  { id: "powerline", name: "Powerline 色块" },
  { id: "bracket", name: "[Bracket]" },
];

export const BAR_STYLES = [
  { id: "blocks", name: "█░ Blocks", full: "█", empty: "░" },
  { id: "shapes", name: "▰▱ Shapes", full: "▰", empty: "▱" },
  { id: "dots", name: "●○ Dots", full: "●", empty: "○" },
  { id: "braille", name: "⣿⣀ Braille", full: "⣿", empty: "⣀" },
];

export const PALETTE_DEFS = {
  herdr: { name: "Follow Herdr Theme", dynamic: true },
  "catppuccin-mocha": {
    name: "Catppuccin Mocha",
    bg: "#181825",
    border: "#313244",
    text: "#cdd6f4",
    muted: "#a6adc8",
    dim: "#6c7086",
    separator: "#45475a",
    onFill: "#11111b",
    ok: "#a6e3a1",
    warn: "#f9e2af",
    crit: "#f38ba8",
    identity: "#89dceb",
    workspace: "#f9e2af",
    vcs: "#cba6f7",
    context: "#89b4fa",
    cache: "#74c7ec",
    quota: "#94e2d5",
    cost: "#fab387",
    timing: "#b4befe",
    activity: "#a6e3a1",
    system: "#9399b2",
  },
  "tokyo-night": {
    name: "Tokyo Night",
    bg: "#16161e",
    border: "#292e42",
    text: "#c0caf5",
    muted: "#9aa5ce",
    dim: "#565f89",
    separator: "#3b4261",
    onFill: "#15161e",
    ok: "#9ece6a",
    warn: "#e0af68",
    crit: "#f7768e",
    identity: "#7dcfff",
    workspace: "#e0af68",
    vcs: "#bb9af7",
    context: "#7aa2f7",
    cache: "#2ac3de",
    quota: "#73daca",
    cost: "#ff9e64",
    timing: "#9d7cd8",
    activity: "#9ece6a",
    system: "#787c99",
  },
  "rose-pine": {
    name: "Rosé Pine",
    bg: "#191724",
    border: "#26233a",
    text: "#e0def4",
    muted: "#908caa",
    dim: "#6e6a86",
    separator: "#403d52",
    onFill: "#191724",
    ok: "#9ccfd8",
    warn: "#f6c177",
    crit: "#eb6f92",
    identity: "#9ccfd8",
    workspace: "#f6c177",
    vcs: "#c4a7e7",
    context: "#31748f",
    cache: "#9ccfd8",
    quota: "#ebbcba",
    cost: "#f6c177",
    timing: "#c4a7e7",
    activity: "#9ccfd8",
    system: "#908caa",
  },
  dracula: {
    name: "Dracula",
    bg: "#21222c",
    border: "#44475a",
    text: "#f8f8f2",
    muted: "#bfbfbf",
    dim: "#6272a4",
    separator: "#44475a",
    onFill: "#191a21",
    ok: "#50fa7b",
    warn: "#f1fa8c",
    crit: "#ff5555",
    identity: "#8be9fd",
    workspace: "#f1fa8c",
    vcs: "#bd93f9",
    context: "#ff79c6",
    cache: "#8be9fd",
    quota: "#50fa7b",
    cost: "#ffb86c",
    timing: "#bd93f9",
    activity: "#50fa7b",
    system: "#6272a4",
  },
  nord: {
    name: "Nord",
    bg: "#2e3440",
    border: "#3b4252",
    text: "#eceff4",
    muted: "#d8dee9",
    dim: "#7b88a1",
    separator: "#4c566a",
    onFill: "#2e3440",
    ok: "#a3be8c",
    warn: "#ebcb8b",
    crit: "#bf616a",
    identity: "#88c0d0",
    workspace: "#ebcb8b",
    vcs: "#b48ead",
    context: "#81a1c1",
    cache: "#8fbcbb",
    quota: "#a3be8c",
    cost: "#d08770",
    timing: "#b48ead",
    activity: "#a3be8c",
    system: "#7b88a1",
  },
  gruvbox: {
    name: "Gruvbox Dark",
    bg: "#1d2021",
    border: "#3c3836",
    text: "#ebdbb2",
    muted: "#bdae93",
    dim: "#7c6f64",
    separator: "#504945",
    onFill: "#1d2021",
    ok: "#b8bb26",
    warn: "#fabd2f",
    crit: "#fb4934",
    identity: "#83a598",
    workspace: "#fabd2f",
    vcs: "#d3869b",
    context: "#8ec07c",
    cache: "#83a598",
    quota: "#b8bb26",
    cost: "#fe8019",
    timing: "#d3869b",
    activity: "#b8bb26",
    system: "#928374",
  },
};

export const SEGMENT_META = [
  { key: "agent", label: "Agent 切换器" },
  { key: "model", label: "模型名称" },
  { key: "effort", label: "推理档位 (Effort)" },
  { key: "dir", label: "目录名称" },
  { key: "git", label: "Git 分支与同步" },
  { key: "gitDiff", label: "Git 增删行数" },
  { key: "context", label: "上下文用量" },
  { key: "contextBar", label: "上下文进度条" },
  { key: "cache", label: "缓存倒计时与命中" },
  { key: "timing", label: "首字延迟与 tok/s" },
  { key: "quota", label: "5H / 7D / 额度配额" },
  { key: "cost", label: "会话花费 / ACU" },
  { key: "mode", label: "运行模式 (Mode)" },
  { key: "activity", label: "运行计时与子智能体" },
  { key: "session", label: "会话标识" },
  { key: "workspace", label: "工作区全局汇总" },
];

export function defaultConfig() {
  return {
    preset: "cometix-pro",
    skin: "plain",
    palette: "herdr",
    lines: 2,
    height: 48,
    barStyle: "blocks",
    barWidth: 10,
    dirStyle: "name",
    followMode: "smart",
    autoSyncHeight: true,
    segments: {
      agent: true,
      model: true,
      effort: true,
      dir: true,
      git: true,
      gitDiff: true,
      context: true,
      contextBar: true,
      cache: true,
      timing: true,
      quota: true,
      cost: true,
      mode: true,
      activity: true,
      session: true,
      workspace: true,
    },
    models: [],
  };
}

export function normalizeConfig(raw) {
  const base = defaultConfig();
  if (!raw || typeof raw !== "object") return base;
  const preset = PRESETS.find((p) => p.id === raw.preset) || PRESETS[0];
  return {
    ...base,
    ...raw,
    preset: preset.id,
    skin: SKINS.some((s) => s.id === raw.skin) ? raw.skin : preset.skin,
    palette: PALETTE_DEFS[raw.palette] ? raw.palette : preset.palette,
    lines: raw.lines === 1 || raw.lines === 2 ? raw.lines : preset.lines,
    height: Number.isFinite(raw.height) ? raw.height : preset.height,
    barStyle: BAR_STYLES.some((b) => b.id === raw.barStyle) ? raw.barStyle : preset.barStyle,
    barWidth: Number.isFinite(raw.barWidth) ? Math.max(6, Math.min(20, Math.round(raw.barWidth))) : 10,
    dirStyle: raw.dirStyle === "tilde" ? "tilde" : "name",
    followMode: raw.followMode === "focused" ? "focused" : "smart",
    autoSyncHeight: raw.autoSyncHeight !== false,
    segments: {
      ...base.segments,
      ...(raw.segments && typeof raw.segments === "object" ? raw.segments : {}),
    },
    models: Array.isArray(raw.models) ? raw.models : [],
  };
}

export function applyPreset(currentConfig, presetId) {
  const cfg = normalizeConfig(currentConfig);
  const preset = PRESETS.find((p) => p.id === presetId) || PRESETS[0];
  const segments = { ...defaultConfig().segments };
  if (preset.id === "minimal") {
    segments.dir = false;
    segments.git = false;
    segments.gitDiff = false;
    segments.contextBar = false;
    segments.timing = false;
    segments.quota = false;
    segments.mode = false;
    segments.session = false;
  }
  return {
    ...cfg,
    preset: preset.id,
    skin: preset.skin,
    palette: preset.palette,
    lines: preset.lines,
    height: preset.height,
    barStyle: preset.barStyle,
    segments,
  };
}

export function resolvePalette(paletteId, herdrTheme) {
  const t = herdrTheme || {};
  const def = PALETTE_DEFS[paletteId];
  if (def && !def.dynamic) return def;
  return {
    name: "Follow Herdr Theme",
    bg: t.chrome || "#16181d",
    border: t.border || "#2a2e38",
    text: t.foreground || "#e6e9ef",
    muted: t.muted || "#9ca3af",
    dim: t.dim || "#6b7280",
    separator: t.border || "#374151",
    onFill: t.background || "#111318",
    ok: t.done || t.ansi2 || "#9ece6a",
    warn: t.ansi3 || "#e0af68",
    crit: t.blocked || t.ansi1 || "#f7768e",
    identity: t.ansi6 || t.accent || "#7dcfff",
    workspace: t.ansi3 || "#e0af68",
    vcs: t.ansi5 || "#bb9af7",
    context: t.ansi4 || t.accent || "#7aa2f7",
    cache: t.ansi6 || "#2ac3de",
    quota: t.ansi2 || "#73daca",
    cost: t.ansi3 || "#ff9e64",
    timing: t.ansi5 || "#9d7cd8",
    activity: t.working || t.ansi2 || "#9ece6a",
    system: t.muted || "#9ca3af",
  };
}

export function withAlpha(hex, alphaHex) {
  if (!hex || typeof hex !== "string" || !hex.startsWith("#")) return "#88888826";
  const clean = hex.slice(1);
  if (clean.length === 3) {
    const full = clean.split("").map((c) => c + c).join("");
    return `#${full}${alphaHex}`;
  }
  if (clean.length >= 6) return `#${clean.slice(0, 6)}${alphaHex}`;
  return `#888888${alphaHex}`;
}

export function fmtTokens(n) {
  if (n == null || !Number.isFinite(Number(n))) return null;
  const v = Number(n);
  if (v >= 1_000_000) {
    const m = (v / 1_000_000).toFixed(1).replace(/\.0$/, "");
    return `${m}M`;
  }
  if (v >= 1000) {
    const k = (v / 1000).toFixed(1).replace(/\.0$/, "");
    return `${k}k`;
  }
  return String(Math.round(v));
}

export function fmtCountdown(ts, nowMs = Date.now()) {
  if (ts == null) return null;
  const targetMs = typeof ts === "number" ? (ts > 1e11 ? ts : ts * 1000) : Date.parse(String(ts));
  if (!Number.isFinite(targetMs)) return null;
  const diffSec = Math.max(0, Math.floor((targetMs - nowMs) / 1000));
  if (diffSec <= 0) return null;
  const mm = String(Math.floor(diffSec / 60) % 60).padStart(2, "0");
  const ss = String(diffSec % 60).padStart(2, "0");
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}:${ss}`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h${mm}m`;
  const d = new Date(targetMs);
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  return `${days[d.getDay()]} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

export function fmtElapsed(sinceMs, nowMs = Date.now()) {
  if (!Number.isFinite(sinceMs)) return null;
  const sec = Math.max(0, Math.floor((nowMs - sinceMs) / 1000));
  const m = Math.floor(sec / 60);
  const s = String(sec % 60).padStart(2, "0");
  return m < 60 ? `${m}:${s}` : `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}:${s}`;
}

export function renderTextBar(pct, width, barStyleId) {
  if (pct == null || !Number.isFinite(Number(pct))) return null;
  const style = BAR_STYLES.find((b) => b.id === barStyleId) || BAR_STYLES[0];
  const clamped = Math.max(0, Math.min(100, Number(pct)));
  const filled = Math.max(0, Math.min(width, Math.round((clamped * width) / 100)));
  return {
    filled: style.full.repeat(filled),
    empty: style.empty.repeat(Math.max(0, width - filled)),
    percent: clamped,
  };
}

export function familyIconPath(family) {
  switch (family) {
    case "claude":
      return "mods/ccline/icons/claude.svg";
    case "gemini":
      return "mods/ccline/icons/gemini.svg";
    case "openai":
      return "mods/ccline/icons/openai.svg";
    case "devin":
      return "mods/ccline/icons/devin.svg";
    case "grok":
      return "mods/ccline/icons/grok.svg";
    default:
      return "mods/ccline/icons/model.svg";
  }
}

function formatDir(cwd, homeDir, style) {
  if (!cwd) return null;
  if (style === "tilde" && homeDir) {
    if (cwd === homeDir) return "~";
    if (cwd.startsWith(homeDir + "/")) return "~" + cwd.slice(homeDir.length);
  }
  if (homeDir && cwd === homeDir) return "~";
  const parts = String(cwd).split("/").filter(Boolean);
  return parts[parts.length - 1] || cwd;
}

function itemWidth(variant, skin) {
  if (!variant) return 0;
  let cols = (variant.icon ? 2 : 0) + (variant.text ? String(variant.text).length : 0);
  if (variant.subtext) cols += 1 + String(variant.subtext).length;
  if (variant.bar) cols += 1 + variant.bar.filled.length + variant.bar.empty.length;
  if (variant.extra) cols += 1 + String(variant.extra).length;
  if (skin === "pill" || skin === "powerline" || skin === "bracket") cols += 3;
  return cols;
}

export function fitRow(spec, budgetCols, skin) {
  const slots = [
    ...(spec.left || []).map((item, idx) => ({ item, side: "left", idx, level: 0 })),
    ...(spec.right || []).map((item, idx) => ({ item, side: "right", idx, level: 0 })),
  ].map((s, order) => {
    while (s.level < 3 && !s.item.variants[s.level]) s.level++;
    return { ...s, order };
  });

  const measure = () => {
    let leftCols = 0;
    let rightCols = 0;
    let leftCount = 0;
    let rightCount = 0;
    for (const s of slots) {
      if (s.level >= 3) continue;
      const w = itemWidth(s.item.variants[s.level], skin);
      if (s.side === "left") {
        if (leftCount > 0) leftCols += 3;
        leftCols += w;
        leftCount++;
      } else {
        if (rightCount > 0) rightCols += 3;
        rightCols += w;
        rightCount++;
      }
    }
    return leftCols + (leftCount > 0 && rightCount > 0 ? 4 : 0) + rightCols;
  };

  while (budgetCols > 0 && measure() > budgetCols) {
    const active = slots.filter((s) => s.level < 3);
    if (active.length <= 1) break;
    // Drop/shrink lowest priority first; prefer shrinking right side before left on ties.
    active.sort((a, b) => {
      if (a.item.priority !== b.item.priority) return a.item.priority - b.item.priority;
      if (a.side !== b.side) return a.side === "right" ? -1 : 1;
      return b.order - a.order;
    });
    const candidate = active[0];
    candidate.level++;
    while (candidate.level < 3 && !candidate.item.variants[candidate.level]) {
      candidate.level++;
    }
  }

  const materialize = (side) =>
    slots
      .filter((s) => s.side === side && s.level < 3)
      .map((s) => ({
        ...s.item,
        activeVariant: s.item.variants[s.level],
      }));

  return {
    left: materialize("left"),
    right: materialize("right"),
  };
}

export function buildStatusModel({
  agent,
  collected,
  workspace,
  config: rawConfig,
  herdrTheme,
  widthPx = 1100,
  nowMs = Date.now(),
}) {
  const cfg = normalizeConfig(rawConfig);
  const segs = cfg.segments;
  const pal = resolvePalette(cfg.palette, herdrTheme);
  const m = collected || {};
  const ctx = m.context || {};
  const cache = m.cache || {};
  const vcs = m.vcs || {};
  const timing = m.timing || {};
  const cost = m.cost || {};
  const quota = m.quota || {};
  const model = m.model || {};
  const ws = workspace || {};

  const budgetCols = Math.max(48, Math.floor((Number(widthPx) || 1100) / 7.4));

  // 1. Agent badge (shows which agent in the space we're inspecting; click cycles/focuses)
  const agentName = agent?.name || agent?.program?.name || model.displayName || "Terminal";
  const agentStatus = agent?.status || "idle";
  const agentCount = ws.spaceAgents?.length || 0;
  const agentItem = segs.agent
    ? {
        id: "agent",
        category: "activity",
        severity: agentStatus === "blocked" ? "crit" : agentStatus === "working" ? "ok" : "normal",
        priority: 5,
        program: agent?.program || null,
        agentStatus,
        action: agentCount > 1 ? "cycle-agent" : "focus-agent",
        tooltip:
          agentCount > 1
            ? `当前追踪: ${agentName} (${agent?.terminal || ""}) · 点击在 ${agentCount} 个活跃 Agent 间切换`
            : `当前窗格: ${agentName} (${agent?.terminal || ""}) · 点击聚焦`,
        variants: [
          {
            text: agentName,
            subtext: agentCount > 1 ? `${(ws.activeAgentIndex ?? 0) + 1}/${agentCount}` : null,
            bright: true,
          },
          {
            text: agentName,
            bright: true,
          },
          {
            text: agentName.slice(0, 10),
            bright: true,
          },
        ],
      }
    : null;

  // 2. Model + Effort
  const mName = model.displayName || model.id || (agent?.isAgent ? agentName : null);
  const mEffort = segs.effort && model.effort ? String(model.effort) : null;
  const modelIcon = familyIconPath(model.family);
  const modelItem =
    segs.model && mName && m.adapter !== "shell"
      ? {
          id: "model",
          category: "identity",
          severity: "normal",
          priority: 5,
          icon: modelIcon,
          tooltip: `模型: ${model.id || mName}${mEffort ? ` · 推理档位: ${mEffort}` : ""}${ctx.window ? ` · 窗口: ${fmtTokens(ctx.window)}` : ""} (${m.source || "live"})`,
          variants: [
            { icon: modelIcon, text: mName, subtext: mEffort ? `· ${mEffort}` : null, bright: true },
            { icon: modelIcon, text: mName, bright: true },
            { icon: modelIcon, text: mName.slice(0, 14), bright: true },
          ],
        }
      : null;

  // 3. Directory
  const cwd = m.cwd || agent?.cwd || ws.folder || "";
  const dirLabel = formatDir(cwd, ws.homeDir, cfg.dirStyle);
  const dirItem =
    segs.dir && dirLabel
      ? {
          id: "dir",
          category: "workspace",
          severity: "normal",
          priority: 4,
          icon: "mods/ccline/icons/folder.svg",
          tooltip: `工作目录: ${cwd}`,
          variants: [
            { icon: "mods/ccline/icons/folder.svg", text: dirLabel },
            { icon: "mods/ccline/icons/folder.svg", text: formatDir(cwd, ws.homeDir, "name") },
            null,
          ],
        }
      : null;

  // 4. Git branch + dirty + ahead/behind + diff lines
  const branch = vcs.branch || agent?.branch || ws.branch || null;
  let gitItem = null;
  if (segs.git && branch) {
    const syncParts = [];
    if (vcs.dirty) syncParts.push("●");
    if (vcs.ahead > 0) syncParts.push(`↑${vcs.ahead}`);
    if (vcs.behind > 0) syncParts.push(`↓${vcs.behind}`);
    const diffText =
      segs.gitDiff && (vcs.added > 0 || vcs.removed > 0)
        ? `+${vcs.added || 0}/-${vcs.removed || 0}`
        : null;
    const syncStr = syncParts.join(" ");
    gitItem = {
      id: "git",
      category: "vcs",
      severity: vcs.dirty ? "warn" : "normal",
      priority: 4,
      icon: "mods/ccline/icons/git.svg",
      tooltip: `Git 分支: ${branch}${vcs.worktree ? " (worktree)" : ""}${vcs.dirty ? ` · 改动: staged ${vcs.staged || 0}, unstaged ${vcs.unstaged || 0}, untracked ${vcs.untracked || 0}` : " · 工作区干净"}${diffText ? ` · ${diffText}` : ""}`,
      variants: [
        {
          icon: "mods/ccline/icons/git.svg",
          text: `${branch}${syncStr ? ` ${syncStr}` : ""}`,
          subtext: diffText,
        },
        {
          icon: "mods/ccline/icons/git.svg",
          text: `${branch}${vcs.dirty ? " ●" : ""}`,
        },
        null,
      ],
    };
  }

  // 5. Context usage (text & bar)
  const pct = ctx.percent != null ? Number(ctx.percent) : null;
  const ctxSeverity = pct != null ? (pct >= 80 ? "crit" : pct >= 50 ? "warn" : "normal") : "normal";
  const tokStr = fmtTokens(ctx.tokens);
  const winStr = fmtTokens(ctx.window);
  const ctxTooltipParts = [];
  if (ctx.tokens != null) ctxTooltipParts.push(`上下文总计: ${ctx.tokens.toLocaleString()} tokens`);
  if (ctx.window != null) ctxTooltipParts.push(`模型窗口: ${ctx.window.toLocaleString()} tokens`);
  if (ctx.inputTokens != null) ctxTooltipParts.push(`未缓存输入: ${ctx.inputTokens.toLocaleString()}`);
  if (ctx.cacheReadTokens != null) ctxTooltipParts.push(`缓存命中读取: ${ctx.cacheReadTokens.toLocaleString()}`);
  if (ctx.outputTokens != null) ctxTooltipParts.push(`本轮输出: ${ctx.outputTokens.toLocaleString()}`);

  let contextTextItem = null;
  if (segs.context && m.adapter !== "shell") {
    const fullText =
      tokStr != null
        ? `${pct != null ? `${Math.round(pct)}% · ` : ""}${tokStr}${winStr ? `/${winStr}` : " tokens"}`
        : winStr
          ? `0% · 0/${winStr}`
          : "ready";
    const compactText =
      tokStr != null ? `${pct != null ? `${Math.round(pct)}% · ` : ""}${tokStr}` : "ready";
    const minText = pct != null ? `${Math.round(pct)}%` : tokStr || "—";
    contextTextItem = {
      id: "context",
      category: "context",
      severity: ctxSeverity,
      priority: 5,
      icon: "mods/ccline/icons/context.svg",
      tooltip: ctxTooltipParts.join(" · ") || "当前会话上下文用量",
      variants: [
        {
          icon: "mods/ccline/icons/context.svg",
          bar: cfg.lines === 1 && segs.contextBar && pct != null ? renderTextBar(pct, Math.min(8, cfg.barWidth), cfg.barStyle) : null,
          text: fullText,
          bright: true,
        },
        { icon: "mods/ccline/icons/context.svg", text: compactText, bright: true },
        { icon: "mods/ccline/icons/context.svg", text: minText, bright: true },
      ],
    };
  }

  let contextBarItem = null;
  if (cfg.lines === 2 && segs.contextBar && pct != null && m.adapter !== "shell") {
    const barObj = renderTextBar(pct, cfg.barWidth, cfg.barStyle);
    const roomLeft =
      ctx.window != null && ctx.tokens != null && ctx.window > ctx.tokens
        ? `剩 ${fmtTokens(ctx.window - ctx.tokens)}`
        : null;
    contextBarItem = {
      id: "context-bar",
      category: "context",
      severity: ctxSeverity,
      priority: 4,
      icon: "mods/ccline/icons/context.svg",
      tooltip: ctxTooltipParts.join(" · "),
      variants: [
        { icon: "mods/ccline/icons/context.svg", bar: barObj, text: `${Math.round(pct)}%`, subtext: roomLeft },
        { icon: "mods/ccline/icons/context.svg", bar: renderTextBar(pct, 8, cfg.barStyle), text: `${Math.round(pct)}%` },
        null,
      ],
    };
  }

  // 6. Prompt Cache (countdown + hit ratio)
  let cacheItem = null;
  const hit = cache.hitRatio != null ? Number(cache.hitRatio) : null;
  const cacheLeft = fmtCountdown(cache.expiresAt, nowMs);
  if (segs.cache && (hit != null || cacheLeft)) {
    const fullCache = [cacheLeft, hit != null ? `${Math.round(hit)}% hit` : null].filter(Boolean).join(" · ");
    const shortCache = hit != null ? `${Math.round(hit)}% hit` : cacheLeft;
    cacheItem = {
      id: "cache",
      category: "cache",
      severity: "normal",
      priority: 3,
      icon: "mods/ccline/icons/cache.svg",
      tooltip: `Prompt Cache${hit != null ? ` 命中率: ${ hit.toFixed(1) }%` : ""}${cacheLeft ? ` · 保温剩余: ${cacheLeft}` : ""}`,
      variants: [
        { icon: "mods/ccline/icons/cache.svg", text: fullCache },
        { icon: "mods/ccline/icons/cache.svg", text: shortCache },
        null,
      ],
    };
  }

  // 7. Timing (TTFT & tokens/sec)
  let timingItem = null;
  if (segs.timing && (timing.ttftMs != null || timing.tokensPerSec != null)) {
    const ttft = timing.ttftMs != null ? `${(Number(timing.ttftMs) / 1000).toFixed(1)}s` : null;
    const tps = timing.tokensPerSec != null ? `${Math.round(Number(timing.tokensPerSec))} tok/s` : null;
    timingItem = {
      id: "timing",
      category: "timing",
      severity: "normal",
      priority: 2,
      icon: "mods/ccline/icons/bolt.svg",
      tooltip: `响应延迟与生成速率: ${[ttft && `TTFT ${ttft}`, tps].filter(Boolean).join(" · ")}`,
      variants: [
        { icon: "mods/ccline/icons/bolt.svg", text: [ttft, tps].filter(Boolean).join(" · ") },
        tps ? { icon: "mods/ccline/icons/bolt.svg", text: tps } : null,
        null,
      ],
    };
  }

  // 8. Quota (5H / 7D / dcc spend)
  let quotaItem = null;
  if (segs.quota) {
    const qParts = [];
    let primaryPct = null;
    if (quota["5H"]?.percent != null) {
      primaryPct = Number(quota["5H"].percent);
      const r5 = fmtCountdown(quota["5H"].resetsAt, nowMs);
      qParts.push(`5H ${Math.round(primaryPct)}%${r5 ? ` (${r5})` : ""}`);
    }
    if (quota["7D"]?.percent != null) {
      const p7 = Number(quota["7D"].percent);
      if (primaryPct == null) primaryPct = p7;
      const r7 = fmtCountdown(quota["7D"].resetsAt, nowMs);
      qParts.push(`7D ${Math.round(p7)}%${r7 ? ` (${r7})` : ""}`);
    }
    if (quota.spend?.percent != null) {
      const ps = Number(quota.spend.percent);
      if (primaryPct == null) primaryPct = ps;
      qParts.push(`${ps.toFixed(1)}%${quota.spend.detail ? ` (${quota.spend.detail})` : ""}`);
    }
    if (qParts.length > 0) {
      const qSev = primaryPct >= 85 ? "crit" : primaryPct >= 65 ? "warn" : "normal";
      quotaItem = {
        id: "quota",
        category: "quota",
        severity: qSev,
        priority: 3,
        icon: "mods/ccline/icons/quota.svg",
        tooltip: `配额状态: ${qParts.join(" · ")}`,
        variants: [
          {
            icon: "mods/ccline/icons/quota.svg",
            bar: cfg.lines === 2 && primaryPct != null ? renderTextBar(primaryPct, 8, cfg.barStyle) : null,
            text: qParts.join(" · "),
          },
          { icon: "mods/ccline/icons/quota.svg", text: qParts[0] },
          null,
        ],
      };
    }
  }

  // 9. Cost / ACU
  let costItem = null;
  if (segs.cost) {
    let fullCost = null;
    let shortCost = null;
    if (cost.totalUsd != null && Number.isFinite(Number(cost.totalUsd))) {
      const prefix = cost.estimated ? "~$" : "$";
      fullCost = `${prefix}${Number(cost.totalUsd).toFixed(2)}`;
      shortCost = fullCost;
    } else if (cost.acu != null && Number(cost.acu) > 0) {
      fullCost = `${Number(cost.acu).toFixed(2)} ACU`;
      shortCost = fullCost;
    }
    if (fullCost) {
      costItem = {
        id: "cost",
        category: "cost",
        severity: "normal",
        priority: 3,
        icon: "mods/ccline/icons/cost.svg",
        tooltip: cost.estimated ? `按官方 Token 单价估算的会话成本: ${fullCost}` : `会话累计花费: ${fullCost}`,
        variants: [
          { icon: "mods/ccline/icons/cost.svg", text: fullCost },
          { icon: "mods/ccline/icons/cost.svg", text: shortCost },
          null,
        ],
      };
    }
  }

  // 10. Mode & Activity (working timer, subagents)
  let modeItem = null;
  if (segs.mode && m.mode) {
    modeItem = {
      id: "mode",
      category: "session",
      severity: String(m.mode) === "bypass" ? "warn" : "normal",
      priority: 2,
      icon: "mods/ccline/icons/terminal.svg",
      tooltip: `当前运行权限/模式: ${m.mode}`,
      variants: [
        { icon: "mods/ccline/icons/terminal.svg", text: String(m.mode) },
        { text: String(m.mode) },
        null,
      ],
    };
  }

  let activityItem = null;
  if (segs.activity) {
    const elapsed = agentStatus === "working" ? fmtElapsed(ws.workingSince, nowMs) : null;
    const subCount = (ws.subagentCount || 0) + (m.activity?.subagents || 0);
    const actParts = [];
    if (elapsed) actParts.push(`working ${elapsed}`);
    if (subCount > 0) actParts.push(`${subCount} subagents`);
    if (actParts.length > 0) {
      activityItem = {
        id: "activity",
        category: "activity",
        severity: "ok",
        priority: 3,
        icon: "mods/ccline/icons/clock.svg",
        tooltip: actParts.join(" · "),
        variants: [
          { icon: "mods/ccline/icons/clock.svg", text: actParts.join(" · ") },
          { icon: "mods/ccline/icons/clock.svg", text: actParts[0] },
          null,
        ],
      };
    }
  }

  let sessionItem = null;
  if (segs.session && (m.sessionTitle || m.sessionId)) {
    const label = m.sessionTitle
      ? String(m.sessionTitle).slice(0, 22)
      : String(m.sessionId).slice(0, 14);
    sessionItem = {
      id: "session",
      category: "system",
      severity: "normal",
      priority: 1,
      tooltip: `会话: ${m.sessionTitle || ""} (${m.sessionId || ""})`.trim(),
      variants: [
        { text: `# ${label}` },
        null,
        null,
      ],
    };
  }

  // 11. Herdr Workspace Summary items (machine, total agents / Needs you, Config, Palette)
  const workspaceItems = [];
  if (segs.workspace) {
    if (ws.blockedCount > 0) {
      workspaceItems.push({
        id: "needs-you",
        category: "system",
        severity: "crit",
        priority: 5,
        action: "jump-blocked",
        tooltip: "有 Agent 等待你的确认 · 点击立即跳转",
        variants: [
          { text: `! ${ws.blockedCount} needs you`, bright: true },
          { text: `! ${ws.blockedCount}`, bright: true },
          { text: `!${ws.blockedCount}`, bright: true },
        ],
      });
    } else if (ws.totalAgents != null) {
      workspaceItems.push({
        id: "ws-agents",
        category: "system",
        severity: "normal",
        priority: 2,
        tooltip: `${ws.machine || "This computer"} · 全局共 ${ws.totalAgents} 个运行中 Agent`,
        variants: [
          { text: `${ws.machine || "Local"} · ${ws.totalAgents} agents` },
          { text: `${ws.totalAgents} agents` },
          null,
        ],
      });
    }
  }

  const controls = [
    {
      id: "open-config",
      category: "system",
      severity: "normal",
      priority: 5,
      icon: "mods/ccline/icons/sliders.svg",
      action: "open-config",
      tooltip: "打开 CCometixLine 可视化配置器 (预设 / 皮肤 / 配色 / 指标开关)",
      variants: [
        { icon: "mods/ccline/icons/sliders.svg", text: "ccline" },
        { icon: "mods/ccline/icons/sliders.svg", text: "" },
        { icon: "mods/ccline/icons/sliders.svg", text: "" },
      ],
    },
  ];
  if (ws.paletteHint) {
    controls.push({
      id: "open-palette",
      category: "system",
      severity: "normal",
      priority: 2,
      action: "open-palette",
      tooltip: "打开 Herdr 命令面板",
      variants: [
        { text: ws.paletteHint },
        null,
        null,
      ],
    });
  }

  const compact = (arr) => arr.filter(Boolean);
  let rows;
  if (cfg.lines === 2) {
    const spec1 = {
      left: compact([agentItem, modelItem, dirItem, gitItem, contextTextItem, cacheItem]),
      right: compact([modeItem, activityItem, costItem]),
    };
    const spec2 = {
      left: compact([timingItem, contextBarItem, quotaItem, sessionItem]),
      right: compact([...workspaceItems, ...controls]),
    };
    // If line 2 left has no live meters yet (e.g. idle shell or brand-new agent), promote graceful placeholder or fold cleanly
    if (spec2.left.length === 0 && m.adapter !== "shell") {
      spec2.left.push({
        id: "idle-hint",
        category: "system",
        severity: "normal",
        priority: 1,
        variants: [
          { text: `${m.adapter || "agent"} · 等待首轮上下文统计` },
          null,
          null,
        ],
      });
    }
    rows = [fitRow(spec1, budgetCols, cfg.skin), fitRow(spec2, budgetCols, cfg.skin)];
  } else {
    const spec = {
      left: compact([agentItem, modelItem, dirItem, gitItem, contextTextItem, cacheItem]),
      right: compact([modeItem, activityItem, quotaItem, costItem, ...workspaceItems, ...controls]),
    };
    rows = [fitRow(spec, budgetCols, cfg.skin)];
  }

  return {
    config: cfg,
    palette: pal,
    rows,
  };
}
