import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { writeFileSync, renameSync, mkdirSync, chmodSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";

const ROOT = process.env.HERDR_CCLINE_HOME || join(homedir(), ".config/herdr-ccline");
const TERMINAL = process.env.HC_TERMINAL_ID || "";
const VALID_TERMINAL = /^t[0-9a-z]+$/.test(TERMINAL);

function atomicWrite(targetPath: string, payload: unknown): void {
  const dir = join(ROOT, "agents");
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  try {
    chmodSync(ROOT, 0o700);
    chmodSync(dir, 0o700);
  } catch {}
  const tmp = `${targetPath}.${process.pid}.tmp`;
  writeFileSync(tmp, JSON.stringify(payload), { mode: 0o600 });
  renameSync(tmp, targetPath);
}

function inspectEntries(ctx: ExtensionContext) {
  const entries = (ctx.sessionManager.getEntries() as any[]) || [];
  let latestUsage: any = null;
  let totalCost = 0;
  let hasCost = false;
  let lastTimestamp: number | null = null;
  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];
    const usage = entry?.message?.usage || entry?.usage;
    if (usage) {
      if (usage.cost?.total != null && Number.isFinite(Number(usage.cost.total))) {
        totalCost += Number(usage.cost.total);
        hasCost = true;
      }
      if (usage.input != null || usage.cacheRead != null || usage.totalTokens != null) {
        latestUsage = usage;
        if (entry?.timestamp) {
          const parsed = Date.parse(String(entry.timestamp));
          if (Number.isFinite(parsed)) lastTimestamp = parsed / 1000;
        }
      }
    }
  }
  return { latestUsage, totalCost: hasCost ? totalCost : null, lastTimestamp };
}

function publish(ctx: ExtensionContext): void {
  if (!VALID_TERMINAL) return;
  const usage = ctx.getContextUsage();
  const model: any = ctx.model || {};
  const { latestUsage, totalCost, lastTimestamp } = inspectEntries(ctx);
  const input = latestUsage?.input ?? 0;
  const cacheRead = latestUsage?.cacheRead ?? 0;
  const cacheWrite = latestUsage?.cacheWrite ?? 0;
  const output = latestUsage?.output ?? 0;
  const promptTotal = input + cacheRead + cacheWrite;
  const windowSize = usage?.contextWindow ?? model.contextWindow ?? null;
  const tokens = usage?.tokens ?? (promptTotal > 0 ? promptTotal : null);
  const percent =
    usage?.percent ??
    (tokens != null && windowSize ? (tokens * 100) / windowSize : null);
  const hitRatio = promptTotal > 0 && cacheRead > 0 ? (cacheRead * 100) / promptTotal : null;
  const nowSec = Date.now() / 1000;
  const expiresAt = lastTimestamp && hitRatio != null && lastTimestamp + 300 > nowSec
    ? lastTimestamp + 300
    : null;

  atomicWrite(join(ROOT, "agents", `${TERMINAL}.json`), {
    version: 1,
    adapter: "pi",
    source: "pi-extension",
    terminal: TERMINAL,
    pid: process.pid,
    sessionId: ctx.sessionManager.getSessionId(),
    updated: nowSec,
    cwd: ctx.cwd,
    model: {
      id: model.id || null,
      displayName: model.name || model.displayName || model.id || null,
      effort: ctx.thinkingLevel || null,
    },
    context: {
      tokens,
      window: windowSize,
      percent,
      inputTokens: input || null,
      outputTokens: output || null,
      cacheReadTokens: cacheRead || null,
      cacheWriteTokens: cacheWrite || null,
    },
    cache: {
      hitRatio,
      warm: expiresAt != null,
      expiresAt,
    },
    cost: totalCost != null ? { totalUsd: totalCost, estimated: false } : {},
  });
}

export default function herdrLineExtension(pi: ExtensionAPI): void {
  if (!VALID_TERMINAL) return;
  const emit = (_event: unknown, ctx: ExtensionContext) => {
    try {
      publish(ctx);
    } catch {}
  };
  pi.on("session_start", emit);
  pi.on("turn_start", emit);
  pi.on("tool_result", emit);
  pi.on("turn_end", emit);
  pi.on("session_compact", emit);
  pi.on("session_tree", emit);
}
