#!/usr/bin/env python3
"""Zero-intrusion multi-agent status collector and SWR Git cache for Herdr Line."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote

TERMINAL_RE = re.compile(r"^t[0-9a-zA-Z_-]+$")
UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
CLAUDE_FAMILY_RE = re.compile(
    r"(?i)(?:(?P<pre_maj>\d{1,2})(?:[.-](?P<pre_min>\d{1,2}))?-(?P<pre_kw>opus|sonnet|haiku|fable|mythos)"
    r"|(?P<post_kw>opus|sonnet|haiku|fable|mythos)-(?P<post_maj>\d{1,2})(?:[.-](?P<post_min>\d{1,2}))?)"
    r"(?:-\d{3,}|-[a-z]|\[|@|:|$)"
)
EFFORT_SUFFIX_RE = re.compile(r"(?i)(?:\s*\((low|medium|med|high|xhigh|max)\)|-(low|medium|high|xhigh|max))$")
DCC_QUOTA_RE = re.compile(
    r"配额使用率\s*([0-9]+(?:\.[0-9]+)?)%\s*(?:\(([^)]+)\))?"
)

BUILTIN_MODELS = (
    ("swe-2-1-max", "SWE-2.1 Max", 262144, "devin", 6.0),
    ("swe-2.1-max", "SWE-2.1 Max", 262144, "devin", 6.0),
    ("swe-2-1", "SWE-2.1", 262144, "devin", 4.0),
    ("swe-2.1", "SWE-2.1", 262144, "devin", 4.0),
    ("swe-2-flash", "SWE-2 Flash", 262144, "devin", 1.0),
    ("swe-2", "SWE-2", 262144, "devin", 4.0),
    ("gemini-4-neon", "Gemini 4 Neon", 1000000, "gemini", 3.5),
    ("gemini-4-hydrogen", "Gemini 4 Hydrogen", 1000000, "gemini", 2.5),
    ("gemini-4-carbon", "Gemini 4 Carbon", 1000000, "gemini", 2.5),
    ("gemini-4-argon", "Gemini 4 Argon", 1000000, "gemini", 1.0),
    ("gemini-3.1-pro", "Gemini 3.1 Pro", 1000000, "gemini", 2.0),
    ("gemini-3.8-flash", "Gemini 3.8 Flash", 1000000, "gemini", 0.5),
    ("gemini-3.7-flash", "Gemini 3.7 Flash", 1000000, "gemini", 0.5),
    ("gemini-3.6-flash", "Gemini 3.6 Flash", 1000000, "gemini", 0.4),
    ("gemini-3.5-flash-lite", "Gemini 3.5 Flash Lite", 1000000, "gemini", 0.2),
    ("gemini-2.5-pro", "Gemini 2.5 Pro", 1048576, "gemini", 1.25),
    ("gemini-2.5-flash", "Gemini 2.5 Flash", 1048576, "gemini", 0.3),
    ("gpt-6.1-sol", "GPT-6.1 Sol", 400000, "openai", 5.0),
    ("gpt-6-astra", "GPT-6 Astra", 400000, "openai", 5.0),
    ("gpt-5.6-luna", "GPT-5.6 Luna", 400000, "openai", 3.0),
    ("gpt-5.4", "GPT-5.4", 400000, "openai", 2.5),
    ("gpt-5.3-codex", "GPT-5.3 Codex", 400000, "openai", 2.5),
    ("gpt-5.2-codex", "GPT-5.2 Codex", 400000, "openai", 2.0),
    ("gpt-5", "GPT-5", 400000, "openai", 2.0),
    ("codex-mini", "Codex Mini", 200000, "openai", 1.5),
    ("o3-pro", "o3 Pro", 200000, "openai", 20.0),
    ("o3", "o3", 200000, "openai", 2.0),
    ("o4-mini", "o4-mini", 200000, "openai", 1.1),
    ("grok-4.7", "Grok 4.7", 256000, "grok", 3.0),
    ("grok-4", "Grok 4", 256000, "grok", 3.0),
    ("grok-3", "Grok 3", 131072, "grok", 3.0),
    ("deepseek-v4.1-flash", "DeepSeek V4.1 Flash", 128000, "generic", 0.3),
    ("deepseek-v4", "DeepSeek V4", 128000, "generic", 0.6),
    ("deepseek-r1", "DeepSeek R1", 128000, "generic", 0.55),
    ("deepseek-v3", "DeepSeek V3", 128000, "generic", 0.27),
    ("glm-5.4", "GLM-5.4", 200000, "generic", 1.0),
    ("glm-5.3-flash", "GLM-5.3 Flash", 200000, "generic", 0.3),
    ("glm-5.3", "GLM-5.3", 200000, "generic", 0.8),
    ("glm-4.5", "GLM-4.5", 128000, "generic", 0.6),
    ("kimi-k2-turbo", "Kimi K2 Turbo", 256000, "generic", 1.0),
    ("kimi-k2", "Kimi K2", 256000, "generic", 0.8),
    ("qwen3-coder", "Qwen3 Coder", 256000, "generic", 0.6),
)


def num(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def first_num(*values):
    for v in values:
        n = num(v)
        if n is not None:
            return n
    return None


def parse_iso_ts(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) / 1000.0 if value > 1e11 else float(value)
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def compact_json(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def runtime_root(home):
    override = os.environ.get("HERDR_CCLINE_HOME")
    if override:
        return Path(override).expanduser()
    return home / ".config/herdr-ccline"


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def read_tail_lines(path, max_bytes=131072):
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > max_bytes:
                handle.seek(size - max_bytes)
                raw = handle.read()
                nl = raw.find(b"\n")
                if nl != -1:
                    raw = raw[nl + 1:]
            else:
                raw = handle.read()
        return raw.decode("utf-8", errors="replace").splitlines()
    except OSError:
        return []


def read_head_lines(path, count=12, max_bytes=32768):
    lines = []
    try:
        with path.open("rb") as handle:
            raw = handle.read(max_bytes).decode("utf-8", errors="replace")
        for line in raw.splitlines():
            lines.append(line)
            if len(lines) >= count:
                break
    except OSError:
        pass
    return lines


def claude_display_and_price(model_id):
    match = CLAUDE_FAMILY_RE.search(model_id or "")
    if not match:
        return None, None
    fam = (match.group("post_kw") or match.group("pre_kw") or "").lower()
    maj = int(match.group("post_maj") or match.group("pre_maj") or 0)
    minor_raw = match.group("post_min") or match.group("pre_min")
    minor = int(minor_raw) if minor_raw is not None else None
    title = fam.capitalize() + (f" {maj}.{minor}" if minor is not None else f" {maj}")
    ver = (maj, minor or 0)
    if fam == "opus":
        price = 5.0 if ver >= (4, 5) else 15.0
    elif fam == "sonnet":
        price = 3.0
    elif fam == "haiku":
        price = 1.0 if ver >= (4, 0) else (0.8 if ver >= (3, 5) else 0.25)
    elif fam == "fable":
        price = 10.0
    else:
        price = 5.0
    return title, price


def resolve_model(raw_id, raw_name=None, effort=None, custom_rules=None, devin_catalog=None, default_window=None):
    source = str(raw_name or raw_id or "").strip()
    ident = str(raw_id or raw_name or "").strip()
    if not source and not ident:
        return {}

    is_1m = "[1m]" in ident.lower() or "(1m" in source.lower()
    clean_id = re.sub(r"(?i)\[1m\]", "", ident).strip()
    clean_source = re.sub(r"(?i)\[1m\]", "", source).strip()

    # Extract trailing effort when embedded in model id or display name
    eff_match = EFFORT_SUFFIX_RE.search(clean_source) or EFFORT_SUFFIX_RE.search(clean_id)
    extracted_effort = (eff_match.group(1) or eff_match.group(2)).lower() if eff_match else None
    final_effort = str(effort or extracted_effort or "").strip() or None

    # Strip provider routing prefixes like auto/, ai-studio/, magpie/auto/
    short_id = clean_id.split("/")[-1] if "/" in clean_id else clean_id
    low = clean_id.lower()

    # 1. User custom rules
    for rule in custom_rules or ():
        pat = str(rule.get("pattern") or "").lower()
        if pat and pat in low:
            win = int(rule["window"]) if num(rule.get("window")) else (1000000 if is_1m else default_window)
            return {
                "id": clean_id,
                "displayName": (rule.get("displayName") or short_id) + (" 1M" if is_1m and "1M" not in str(rule.get("displayName")) else ""),
                "effort": final_effort,
                "family": rule.get("family") or infer_family(low),
                "window": win,
                "inputPrice": num(rule.get("inputPrice")),
            }

    # 2. Devin catalog if exact match
    if devin_catalog and clean_id in devin_catalog:
        cat_item = devin_catalog[clean_id]
        disp = cat_item.get("displayName") or short_id
        # Avoid duplicating "Max" if displayName already ends with Max
        if disp.lower().endswith(" max") and final_effort and final_effort.lower() == "max":
            final_effort = None
        return {
            "id": clean_id,
            "displayName": disp,
            "effort": final_effort,
            "family": infer_family(low),
            "window": 1000000 if is_1m else (cat_item.get("window") or default_window or 262144),
            "inputPrice": 4.0,
        }

    # 3. Claude family parser
    c_name, c_price = claude_display_and_price(short_id)
    if c_name:
        return {
            "id": clean_id,
            "displayName": c_name + (" 1M" if is_1m else ""),
            "effort": final_effort,
            "family": "claude",
            "window": 1000000 if is_1m else (default_window or 200000),
            "inputPrice": c_price,
        }

    # 4. Built-in table
    for pattern, name, window, family, price in BUILTIN_MODELS:
        if pattern in low:
            if name.lower().endswith(" max") and final_effort and final_effort.lower() == "max":
                final_effort = None
            return {
                "id": clean_id,
                "displayName": name + (" 1M" if is_1m and window < 1000000 else ""),
                "effort": final_effort,
                "family": family,
                "window": 1000000 if is_1m else (default_window or window),
                "inputPrice": price,
            }

    # 5. Clean fallback
    cleaned_display = EFFORT_SUFFIX_RE.sub("", raw_name or short_id).strip() or short_id
    return {
        "id": clean_id,
        "displayName": cleaned_display + (" 1M" if is_1m and "1m" not in cleaned_display.lower() else ""),
        "effort": final_effort,
        "family": infer_family(low),
        "window": 1000000 if is_1m else default_window,
        "inputPrice": None,
    }


def infer_family(low):
    if any(k in low for k in ("claude", "opus", "sonnet", "haiku", "fable", "anthropic")):
        return "claude"
    if "gemini" in low:
        return "gemini"
    if any(k in low for k in ("gpt-", "openai", "codex", "o1", "o3", "o4")):
        return "openai"
    if any(k in low for k in ("swe-", "devin")):
        return "devin"
    if "grok" in low:
        return "grok"
    return "generic"


def estimate_cost_usd(input_tokens, cache_read, cache_write, output_tokens, input_price_per_m):
    if not input_price_per_m:
        return None
    inp = float(input_tokens or 0)
    cr = float(cache_read or 0)
    cw = float(cache_write or 0)
    out = float(output_tokens or 0)
    # Anthropic/standard ratios: cache_read = 0.1x, cache_write = 1.25x, output = 5x
    usd = (inp * 1.0 + cr * 0.1 + cw * 1.25 + out * 5.0) * float(input_price_per_m) / 1_000_000.0
    return round(usd, 4) if usd > 0 else None


class ProcessIndex:
    """Single-pass process table snapshot for mapping terminal PIDs to running agents."""

    def __init__(self, rows=None):
        self.parents = {}
        self.children = {}
        self.commands = {}
        if rows is None:
            rows = self._capture()
        for pid, ppid, cmd in rows:
            self.parents[pid] = ppid
            self.commands[pid] = cmd
            self.children.setdefault(ppid, []).append(pid)

    @staticmethod
    def _capture():
        out = []
        try:
            proc = subprocess.run(
                ["ps", "-axo", "pid=,ppid=,command="],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            for line in proc.stdout.splitlines():
                parts = line.strip().split(None, 2)
                if len(parts) >= 2:
                    try:
                        pid = int(parts[0])
                        ppid = int(parts[1])
                        cmd = parts[2] if len(parts) > 2 else ""
                        out.append((pid, ppid, cmd))
                    except ValueError:
                        continue
        except (OSError, subprocess.TimeoutExpired):
            pass
        return out

    def family_pids(self, seed_pid):
        """Return ordered candidate PIDs: seed, descendants (BFS), and bounded shell ancestors."""
        if not seed_pid or seed_pid <= 1:
            return []
        result = []
        seen = set()
        queue = [seed_pid]
        while queue and len(result) < 64:
            cur = queue.pop(0)
            if cur in seen or cur <= 1:
                continue
            seen.add(cur)
            result.append(cur)
            for child in self.children.get(cur, ()):
                if child not in seen:
                    queue.append(child)
        # Walk up ancestors until hitting herdr-core / launchd / init
        cur = self.parents.get(seed_pid, 0)
        steps = 0
        while cur > 1 and cur not in seen and steps < 12:
            cmd = (self.commands.get(cur) or "").lower()
            if "herdr-core" in cmd or "herdr-app" in cmd or "launchd" in cmd:
                break
            seen.add(cur)
            result.append(cur)
            cur = self.parents.get(cur, 0)
            steps += 1
        return result

    def connected(self, pid_a, pid_b):
        if not pid_a or not pid_b:
            return False
        if pid_a == pid_b:
            return True
        fam_a = set(self.family_pids(pid_a))
        if pid_b in fam_a:
            return True
        # Check if pid_b walks up into fam_a
        cur = pid_b
        seen = set()
        for _ in range(20):
            if cur in fam_a:
                return True
            if cur <= 1 or cur in seen:
                break
            seen.add(cur)
            cur = self.parents.get(cur, 0)
        return False


def find_git_root(cwd):
    if not cwd:
        return None, None, False
    try:
        cur = Path(cwd).expanduser().resolve()
    except OSError:
        return None, None, False
    for candidate in (cur, *cur.parents):
        dot_git = candidate / ".git"
        try:
            if dot_git.is_dir():
                return candidate, dot_git, False
            if dot_git.is_file():
                text = dot_git.read_text(encoding="utf-8", errors="ignore").strip()
                if text.startswith("gitdir:"):
                    raw_gitdir = text.split(":", 1)[1].strip()
                    gitdir = (candidate / raw_gitdir).resolve()
                    return candidate, gitdir, True
        except OSError:
            continue
    return None, None, False


def read_git_head_fast(git_dir):
    if not git_dir:
        return None
    head_file = git_dir / "HEAD"
    try:
        head = head_file.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return None
    if head.startswith("ref: refs/heads/"):
        return head[len("ref: refs/heads/"):]
    if head.startswith("ref: "):
        return head.split("/")[-1]
    return head[:7] if head else None


def collect_git_swr(cwd, root_dir, ttl_sec=5.0):
    repo_root, git_dir, is_worktree = find_git_root(cwd)
    if not repo_root:
        return {}
    fast_branch = read_git_head_fast(git_dir)
    cache_path = root_dir / "cache" / "git.json"
    cache = {}
    try:
        if cache_path.is_file():
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}

    key = str(repo_root)
    now = time.time()
    cached = cache.get(key)
    if isinstance(cached, dict) and now - float(cached.get("updated") or 0) < ttl_sec:
        data = dict(cached.get("vcs") or {})
        if fast_branch:
            data["branch"] = fast_branch
        data["worktree"] = is_worktree
        return data

    vcs = {
        "branch": fast_branch,
        "repo": repo_root.name,
        "worktree": is_worktree,
        "dirty": False,
        "staged": 0,
        "unstaged": 0,
        "untracked": 0,
        "ahead": 0,
        "behind": 0,
        "added": 0,
        "removed": 0,
    }
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        st = subprocess.run(
            ["git", "-C", key, "status", "--porcelain=v2", "--branch"],
            capture_output=True,
            text=True,
            env=env,
            timeout=1.2,
        )
        if st.returncode == 0:
            for line in st.stdout.splitlines():
                if line.startswith("# branch.head ") and not fast_branch:
                    b = line[14:].strip()
                    if b != "(detached)":
                        vcs["branch"] = b
                elif line.startswith("# branch.ab "):
                    for tok in line[12:].split():
                        if tok.startswith("+"):
                            vcs["ahead"] = int(tok[1:] or 0)
                        elif tok.startswith("-"):
                            vcs["behind"] = int(tok[1:] or 0)
                elif line.startswith(("1 ", "2 ")):
                    xy = line.split(" ", 2)[1]
                    if len(xy) >= 2:
                        if xy[0] != ".":
                            vcs["staged"] += 1
                        if xy[1] != ".":
                            vcs["unstaged"] += 1
                elif line.startswith("u "):
                    vcs["unstaged"] += 1
                elif line.startswith("? "):
                    vcs["untracked"] += 1
            vcs["dirty"] = bool(vcs["staged"] or vcs["unstaged"] or vcs["untracked"])
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass

    if vcs["dirty"]:
        try:
            df = subprocess.run(
                ["git", "-C", key, "diff", "--shortstat", "HEAD"],
                capture_output=True,
                text=True,
                env=env,
                timeout=0.8,
            )
            if df.returncode == 0 and df.stdout:
                ins = re.search(r"(\d+)\s+insertion", df.stdout)
                dels = re.search(r"(\d+)\s+deletion", df.stdout)
                if ins:
                    vcs["added"] = int(ins.group(1))
                if dels:
                    vcs["removed"] = int(dels.group(1))
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass

    # Prune old entries to keep cache tiny
    if len(cache) > 48:
        oldest = sorted(cache.items(), key=lambda kv: float((kv[1] or {}).get("updated") or 0))[:16]
        for k, _ in oldest:
            cache.pop(k, None)
    cache[key] = {"updated": now, "vcs": vcs}
    try:
        atomic_write(cache_path, compact_json(cache))
    except OSError:
        pass
    return vcs


def load_devin_catalog(root_dir):
    cache_path = root_dir / "cache" / "devin-models.json"
    try:
        if cache_path.is_file():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if time.time() - float(cached.get("updated") or 0) < 7 * 86400:
                return cached.get("models") or {}
    except (OSError, ValueError):
        pass
    if not shutil.which("devin"):
        return {}
    models = {}
    try:
        proc = subprocess.run(["devin", "models"], capture_output=True, text=True, timeout=6.0)
        if proc.returncode == 0:
            pat = re.compile(r"^\s*(\S+)\s{2,}(.+?)\s*\[([0-9.]+)(K|M) context")
            for line in proc.stdout.splitlines():
                m = pat.match(line)
                if m:
                    mid, name, size, unit = m.groups()
                    if unit == "K" and abs(float(size) - 262.0) < 0.01:
                        window = 262144
                    else:
                        scale = 1024 if unit == "K" else 1000000
                        window = int(float(size) * scale)
                    models[mid] = {"displayName": name.strip(), "window": window}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    if models:
        try:
            atomic_write(cache_path, compact_json({"updated": time.time(), "models": models}))
        except OSError:
            pass
    return models


def load_dcc_quota(root_dir):
    cache_path = root_dir / "cache" / "dcc-quota.json"
    now = time.time()
    try:
        if cache_path.is_file():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if now - float(cached.get("updated") or 0) < 30.0:
                return cached.get("quota") or {}
    except (OSError, ValueError):
        pass
    if not shutil.which("dcc"):
        return {}
    quota = {}
    try:
        proc = subprocess.run(["dcc", "quota", "render"], input="{}", capture_output=True, text=True, timeout=1.5)
        if proc.returncode == 0 and proc.stdout:
            clean = re.sub(r"\x1b\[[0-9;]*m", "", proc.stdout).strip()
            m = DCC_QUOTA_RE.search(clean)
            if m:
                pct = float(m.group(1))
                detail = m.group(2) or ""
                quota["spend"] = {"percent": pct, "detail": detail}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    try:
        atomic_write(cache_path, compact_json({"updated": now, "quota": quota}))
    except OSError:
        pass
    return quota


def detect_adapter(target, proc_index):
    explicit = " ".join(
        str(target.get(k) or "") for k in ("app", "programKey", "programName")
    ).lower()
    for token, adapter in (
        ("devin", "devin"),
        ("claude", "claude-code"),
        ("codex", "codex"),
        ("antigravity", "antigravity"),
        ("agy", "antigravity"),
        ("omp", "omp"),
        ("grok", "grok"),
        ("cursor", "cursor"),
    ):
        if token in explicit:
            return adapter
    if re.search(r"(^|\W)pi(\W|$)", explicit):
        return "pi"

    # Inspect live process family commands when wrapper / shell hides the program name
    pid = int(target.get("pid") or 0)
    for cand in proc_index.family_pids(pid):
        cmd = (proc_index.commands.get(cand) or "").lower()
        if "/devin" in cmd or cmd.startswith("devin "):
            return "devin"
        if "/claude" in cmd or cmd.startswith("claude ") or cmd == "claude":
            return "claude-code"
        if "/codex" in cmd or cmd.startswith("codex ") or "codex.app" in cmd:
            return "codex"
        if "/agy" in cmd or "antigravity-cli" in cmd or cmd.startswith("agy "):
            return "antigravity"
        if "/omp" in cmd or cmd.startswith("omp "):
            return "omp"
        if "/.grok/" in cmd or cmd.startswith("grok "):
            return "grok"
        if "/.pi/" in cmd or cmd.startswith("pi ") or cmd == "pi":
            return "pi"

    if target.get("isShell") and not target.get("isAgent"):
        return "shell"
    return "generic"


def read_push_cache(root_dir, terminal):
    if not terminal or not TERMINAL_RE.fullmatch(terminal):
        return None
    path = root_dir / "agents" / f"{terminal}.json"
    try:
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(data.get("updated") or 0) > 86400:
            return None
        return data
    except (OSError, ValueError):
        return None


def collect_devin_passive(home, root_dir, target, proc_index, custom_rules, catalog):
    base = home / ".local/share/devin/cli"
    db_path = base / "sessions.db"
    if not db_path.is_file():
        return None

    pid = int(target.get("pid") or 0)
    session_id = None
    locks_dir = base / "session_locks"
    if pid and locks_dir.is_dir():
        for lock in locks_dir.glob("*.lock"):
            try:
                lock_pid = int(lock.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                continue
            if proc_index.connected(pid, lock_pid):
                session_id = lock.stem
                break

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=1.0)
    try:
        if session_id:
            row = con.execute(
                "SELECT id, working_directory, model, agent_mode, title, metadata FROM sessions WHERE id=?",
                (session_id,),
            ).fetchone()
        else:
            cwd = target.get("cwd") or ""
            row = con.execute(
                "SELECT id, working_directory, model, agent_mode, title, metadata "
                "FROM sessions WHERE working_directory=? AND hidden=0 ORDER BY last_activity_at DESC LIMIT 1",
                (cwd,),
            ).fetchone()
        if not row:
            return None
        sid, cwd, cfg_model, agent_mode, title, meta_raw = row
        latest_meta, latest_metrics, latest_ts = {}, {}, None
        for (chat_raw, created_at) in con.execute(
            "SELECT chat_message, created_at FROM message_nodes WHERE session_id=? ORDER BY node_id DESC LIMIT 100",
            (sid,),
        ):
            try:
                msg = json.loads(chat_raw)
            except ValueError:
                continue
            m_meta = msg.get("metadata") or {}
            metrics = m_meta.get("metrics") or {}
            if metrics.get("context_input_tokens") is not None:
                latest_meta = m_meta
                latest_metrics = metrics
                latest_ts = parse_iso_ts(created_at)
                break

        model_id = latest_meta.get("generation_model") or cfg_model
        model_info = resolve_model(model_id, custom_rules=custom_rules, devin_catalog=catalog, default_window=262144)
        tokens = int(latest_metrics["context_input_tokens"]) if num(latest_metrics.get("context_input_tokens")) is not None else None
        window = model_info.get("window")
        pct = (tokens * 100.0 / window) if (tokens is not None and window) else None
        cache_read = int(latest_metrics.get("cache_read_tokens") or 0)
        cache_write = int(latest_metrics.get("cache_creation_tokens") or 0)
        hit_ratio = (cache_read * 100.0 / tokens) if (tokens and cache_read > 0) else None
        expires_at = (latest_ts + 300.0) if (latest_ts and hit_ratio is not None and latest_ts + 300.0 > time.time()) else None

        try:
            s_meta = json.loads(meta_raw or "{}")
        except ValueError:
            s_meta = {}
        mode_map = {"dangerous": "bypass", "accept-edits": "accept-edits", "smart": "smart", "auto": "auto"}
        clean_mode = mode_map.get(str(agent_mode or "").lower(), agent_mode or None)
        return {
            "adapter": "devin",
            "source": "devin-db",
            "sessionId": sid,
            "sessionTitle": title,
            "cwd": cwd or target.get("cwd"),
            "model": model_info,
            "context": {
                "tokens": tokens,
                "window": window,
                "percent": pct,
                "inputTokens": latest_metrics.get("input_tokens"),
                "outputTokens": latest_metrics.get("output_tokens"),
                "cacheReadTokens": cache_read or None,
                "cacheWriteTokens": cache_write or None,
            },
            "cache": {
                "hitRatio": hit_ratio,
                "warm": expires_at is not None,
                "expiresAt": expires_at,
            },
            "cost": {
                "acu": num(s_meta.get("total_acu_cost")),
                "credits": num(s_meta.get("total_credit_cost")),
            },
            "timing": {
                "ttftMs": num(latest_metrics.get("ttft_ms")),
                "tokensPerSec": num(latest_metrics.get("tokens_per_sec")),
            },
            "mode": clean_mode,
        }
    finally:
        con.close()


def claude_settings_defaults(home):
    path = home / ".claude/settings.json"
    try:
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def collect_claude_passive(home, root_dir, target, proc_index, custom_rules):
    claude_dir = home / ".claude"
    if not claude_dir.is_dir():
        return None
    pid = int(target.get("pid") or 0)
    cwd = target.get("cwd") or ""
    session_id = None
    session_name = None
    sessions_dir = claude_dir / "sessions"

    # 1. Exact PID lookup via ~/.claude/sessions/<pid>.json
    for cand in proc_index.family_pids(pid):
        sfile = sessions_dir / f"{cand}.json"
        if sfile.is_file():
            try:
                sdata = json.loads(sfile.read_text(encoding="utf-8"))
                session_id = sdata.get("sessionId")
                session_name = sdata.get("name")
                cwd = sdata.get("cwd") or cwd
                break
            except (OSError, ValueError):
                continue
        cmd = proc_index.commands.get(cand) or ""
        if "--resume" in cmd or "--session-id" in cmd:
            m = UUID_RE.search(cmd)
            if m:
                session_id = m.group(0)
                break

    projects_dir = claude_dir / "projects"
    jsonl_path = None
    if projects_dir.is_dir():
        if session_id:
            if cwd:
                slug = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
                direct = projects_dir / slug / f"{session_id}.jsonl"
                if direct.is_file():
                    jsonl_path = direct
            if not jsonl_path:
                matches = list(projects_dir.glob(f"*/{session_id}.jsonl"))
                if matches:
                    jsonl_path = matches[0]
        elif cwd:
            slug = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
            proj = projects_dir / slug
            if proj.is_dir():
                files = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
                if files:
                    jsonl_path = files[0]

    settings = claude_settings_defaults(home)
    env_cfg = settings.get("env") or {}
    default_window = int(env_cfg["CLAUDE_CODE_MAX_CONTEXT_TOKENS"]) if str(env_cfg.get("CLAUDE_CODE_MAX_CONTEXT_TOKENS", "")).isdigit() else None
    cfg_model = settings.get("model")
    alias_map = {
        "sonnet": env_cfg.get("ANTHROPIC_DEFAULT_SONNET_MODEL") or "claude-sonnet-4-5",
        "opus": env_cfg.get("ANTHROPIC_DEFAULT_OPUS_MODEL") or "claude-opus-4-8",
        "haiku": env_cfg.get("ANTHROPIC_DEFAULT_HAIKU_MODEL") or "claude-haiku-4-5",
    }

    latest_usage = None
    latest_model = None
    latest_ts = None
    sum_inp = sum_cr = sum_cw = sum_out = 0
    ttl_sec = 300.0

    if jsonl_path and jsonl_path.is_file():
        for line in read_tail_lines(jsonl_path, max_bytes=196608):
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            session_id = entry.get("sessionId") or session_id
            msg = entry.get("message")
            if isinstance(msg, dict):
                usage = msg.get("usage")
                if isinstance(usage, dict) and (usage.get("input_tokens") is not None or usage.get("cache_read_input_tokens") is not None):
                    latest_usage = usage
                    latest_model = msg.get("model") or latest_model
                    latest_ts = parse_iso_ts(entry.get("timestamp")) or latest_ts
                    sum_inp += int(usage.get("input_tokens") or 0)
                    sum_cr += int(usage.get("cache_read_input_tokens") or 0)
                    sum_cw += int(usage.get("cache_creation_input_tokens") or 0)
                    sum_out += int(usage.get("output_tokens") or 0)
                    cc = usage.get("cache_creation") or {}
                    if int(cc.get("ephemeral_1h_input_tokens") or 0) > 0:
                        ttl_sec = 3600.0

    resolved_raw_model = latest_model or alias_map.get(str(cfg_model or "").lower(), cfg_model)
    model_settings = settings.get("modelSettings") or {}
    effort = None
    if resolved_raw_model:
        short_key = str(resolved_raw_model).split("/")[-1].split("[")[0]
        effort = (model_settings.get(resolved_raw_model) or model_settings.get(short_key) or {}).get("effortLevel")

    model_info = resolve_model(resolved_raw_model, effort=effort, custom_rules=custom_rules, default_window=default_window)
    window = model_info.get("window") or default_window or 200000

    inp = int((latest_usage or {}).get("input_tokens") or 0)
    cr = int((latest_usage or {}).get("cache_read_input_tokens") or 0)
    cw = int((latest_usage or {}).get("cache_creation_input_tokens") or 0)
    out = int((latest_usage or {}).get("output_tokens") or 0)
    tokens = (inp + cr + cw) if latest_usage is not None else 0
    pct = (tokens * 100.0 / window) if (window and latest_usage is not None) else (0.0 if model_info else None)
    hit_ratio = (cr * 100.0 / tokens) if (tokens > 0 and cr > 0) else None
    expires_at = (latest_ts + ttl_sec) if (latest_ts and (cr > 0 or cw > 0) and latest_ts + ttl_sec > time.time()) else None
    est_usd = estimate_cost_usd(sum_inp, sum_cr, sum_cw, sum_out, model_info.get("inputPrice"))
    quota = load_dcc_quota(root_dir)

    return {
        "adapter": "claude-code",
        "source": "claude-passive",
        "sessionId": session_id,
        "sessionTitle": session_name,
        "cwd": cwd or None,
        "model": model_info,
        "context": {
            "tokens": tokens if (latest_usage is not None or model_info) else None,
            "window": window,
            "percent": pct,
            "inputTokens": inp or None,
            "outputTokens": out or None,
            "cacheReadTokens": cr or None,
            "cacheWriteTokens": cw or None,
        },
        "cache": {
            "hitRatio": hit_ratio,
            "warm": expires_at is not None,
            "expiresAt": expires_at,
        },
        "cost": {"totalUsd": est_usd, "estimated": True} if est_usd is not None else {},
        "quota": quota,
    }


def collect_codex_passive(home, target, custom_rules):
    sessions_root = home / ".codex/sessions"
    if not sessions_root.is_dir():
        return None
    cwd = target.get("cwd") or ""
    candidates = sorted(sessions_root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:40]
    chosen = None
    chosen_meta = {}
    for fpath in candidates:
        for line in read_head_lines(fpath, count=6):
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("type") == "session_meta":
                payload = entry.get("payload") or {}
                s_cwd = payload.get("cwd") or ""
                if not cwd or s_cwd == cwd or cwd.startswith(s_cwd + "/"):
                    chosen = fpath
                    chosen_meta = payload
                    break
        if chosen:
            break
    if not chosen and candidates and not cwd:
        chosen = candidates[0]
    if not chosen:
        return None

    model_id = None
    effort = None
    mode = None
    token_info = None
    rate_limits = {}
    last_ts = None

    for line in read_tail_lines(chosen, max_bytes=196608):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        etype = entry.get("type")
        payload = entry.get("payload") or {}
        if etype == "turn_context" and isinstance(payload, dict):
            model_id = payload.get("model") or model_id
            effort = payload.get("effort") or effort
            mode = payload.get("approval_policy") or mode
        elif etype == "event_msg" and isinstance(payload, dict) and payload.get("type") == "token_count":
            token_info = payload.get("info") or token_info
            rate_limits = payload.get("rate_limits") or rate_limits
            last_ts = parse_iso_ts(entry.get("timestamp")) or last_ts

    last_usage = (token_info or {}).get("last_token_usage") or {}
    total_usage = (token_info or {}).get("total_token_usage") or {}
    window = int(token_info["model_context_window"]) if num((token_info or {}).get("model_context_window")) else None
    model_info = resolve_model(model_id or "codex", effort=effort, custom_rules=custom_rules, default_window=window or 400000)
    window = window or model_info.get("window")

    # In Codex/OpenAI usage, input_tokens ALREADY includes cached_input_tokens.
    prompt_tokens = int(last_usage["input_tokens"]) if num(last_usage.get("input_tokens")) is not None else None
    cached_tokens = int(last_usage.get("cached_input_tokens") or 0)
    uncached_tokens = max(0, (prompt_tokens or 0) - cached_tokens)
    output_tokens = int(last_usage.get("output_tokens") or 0)
    pct = (prompt_tokens * 100.0 / window) if (prompt_tokens is not None and window) else None
    hit_ratio = (cached_tokens * 100.0 / prompt_tokens) if (prompt_tokens and cached_tokens > 0) else None
    expires_at = (last_ts + 300.0) if (last_ts and hit_ratio is not None and last_ts + 300.0 > time.time()) else None

    quota = {}
    for src_key, q_label in (("primary", "5H"), ("secondary", "7D")):
        item = rate_limits.get(src_key)
        if isinstance(item, dict) and num(item.get("used_percent")) is not None:
            quota[q_label] = {
                "percent": float(item["used_percent"]),
                "resetsAt": item.get("resets_at"),
            }

    tot_in = int(total_usage.get("input_tokens") or 0)
    tot_cached = int(total_usage.get("cached_input_tokens") or 0)
    tot_out = int(total_usage.get("output_tokens") or 0)
    est_usd = estimate_cost_usd(max(0, tot_in - tot_cached), tot_cached, 0, tot_out, model_info.get("inputPrice"))

    return {
        "adapter": "codex",
        "source": "codex-jsonl",
        "sessionId": chosen_meta.get("session_id") or chosen_meta.get("id"),
        "cwd": chosen_meta.get("cwd") or cwd or None,
        "model": model_info,
        "context": {
            "tokens": prompt_tokens,
            "window": window,
            "percent": pct,
            "inputTokens": uncached_tokens or None,
            "outputTokens": output_tokens or None,
            "cacheReadTokens": cached_tokens or None,
        },
        "cache": {
            "hitRatio": hit_ratio,
            "warm": expires_at is not None,
            "expiresAt": expires_at,
        },
        "cost": {"totalUsd": est_usd, "estimated": True} if est_usd is not None else {},
        "quota": quota,
        "mode": mode,
    }


def collect_antigravity_passive(home, target, custom_rules):
    agy_root = home / ".gemini/antigravity-cli"
    cfg_model = None
    settings_path = agy_root / "settings.json"
    try:
        if settings_path.is_file():
            cfg = json.loads(settings_path.read_text(encoding="utf-8"))
            cfg_model = cfg.get("model")
    except (OSError, ValueError):
        pass

    brain_dir = agy_root / "brain"
    chosen_transcript = None
    conv_id = None
    cwd = target.get("cwd") or ""
    try:
        if brain_dir.is_dir():
            transcripts = []
            for child in brain_dir.iterdir():
                tfile = child / ".system_generated/logs/transcript.jsonl"
                if tfile.is_file():
                    transcripts.append((tfile.stat().st_mtime, child.name, tfile))
            transcripts.sort(reverse=True)
            for _mtime, cid, tfile in transcripts[:12]:
                head_blob = "\n".join(read_head_lines(tfile, count=8))
                if not cwd or cwd in head_blob or _mtime == transcripts[0][0]:
                    chosen_transcript = tfile
                    conv_id = cid
                    if cwd and cwd in head_blob:
                        break
    except OSError:
        pass

    latest_model = None
    inp = cr = out = None
    last_ts = None
    subagent_count = 0
    sum_inp = sum_cr = sum_out = 0

    if chosen_transcript:
        for line in read_tail_lines(chosen_transcript, max_bytes=262144):
            try:
                step = json.loads(line)
            except ValueError:
                continue
            if step.get("type") == "PLANNER_RESPONSE":
                if step.get("input_tokens") is not None or step.get("cache_read_tokens") is not None:
                    latest_model = step.get("model") or latest_model
                    inp = int(step.get("input_tokens") or 0)
                    cr = int(step.get("cache_read_tokens") or 0)
                    out = int(step.get("output_tokens") or 0)
                    sum_inp += inp
                    sum_cr += cr
                    sum_out += out
                    last_ts = parse_iso_ts(step.get("created_at")) or last_ts
                for tc in step.get("tool_calls") or ():
                    if isinstance(tc, dict) and tc.get("name") == "invoke_subagent":
                        subagent_count += 1

    model_info = resolve_model(latest_model or cfg_model, raw_name=cfg_model if not latest_model else None, custom_rules=custom_rules, default_window=1000000)
    window = model_info.get("window") or 1000000
    tokens = (inp + cr) if (inp is not None and cr is not None) else (0 if model_info else None)
    pct = (tokens * 100.0 / window) if (tokens is not None and window) else None
    hit_ratio = (cr * 100.0 / tokens) if (tokens and cr and cr > 0) else None
    expires_at = (last_ts + 300.0) if (last_ts and hit_ratio is not None and last_ts + 300.0 > time.time()) else None
    est_usd = estimate_cost_usd(sum_inp, sum_cr, 0, sum_out, model_info.get("inputPrice"))

    return {
        "adapter": "antigravity",
        "source": "agy-transcript",
        "sessionId": conv_id,
        "cwd": cwd or None,
        "model": model_info,
        "context": {
            "tokens": tokens,
            "window": window,
            "percent": pct,
            "inputTokens": inp,
            "outputTokens": out,
            "cacheReadTokens": cr,
        },
        "cache": {
            "hitRatio": hit_ratio,
            "warm": expires_at is not None,
            "expiresAt": expires_at,
        },
        "cost": {"totalUsd": est_usd, "estimated": True} if est_usd is not None else {},
        "activity": {"subagents": subagent_count} if subagent_count else {},
    }


def collect_pi_family_passive(home, root_dir, target, adapter, custom_rules):
    # Check live push cache from extensions/herdr-ccline.ts first
    pushed = read_push_cache(root_dir, target.get("terminal") or "")
    base_dir = home / (".omp/agent" if adapter == "omp" else ".pi/agent")
    cwd = target.get("cwd") or ""

    # Load configured model window map from models.json if available
    pi_windows = {}
    models_file = base_dir / "models.json"
    try:
        if models_file.is_file():
            mdata = json.loads(models_file.read_text(encoding="utf-8"))
            providers = mdata.get("providers") if isinstance(mdata, dict) else {}
            if isinstance(providers, dict):
                for prov in providers.values():
                    for m in (prov.get("models") if isinstance(prov, dict) else ()) or ():
                        if isinstance(m, dict) and m.get("id") and num(m.get("contextWindow")):
                            pi_windows[str(m["id"])] = int(m["contextWindow"])
    except (OSError, ValueError):
        pass

    sessions_dir = base_dir / "sessions"
    chosen = None
    if sessions_dir.is_dir():
        if cwd:
            pi_slug = "--" + cwd.strip("/").replace("/", "-") + "--"
            slug_dir = sessions_dir / pi_slug
            if slug_dir.is_dir():
                files = sorted(slug_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
                if files:
                    chosen = files[0]
        if not chosen:
            all_files = sorted(sessions_dir.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
            if all_files:
                chosen = all_files[0]

    # Prefer live extension push if newer than passive session file
    if pushed and pushed.get("adapter") in ("pi", "omp"):
        file_mtime = chosen.stat().st_mtime if chosen and chosen.is_file() else 0
        if float(pushed.get("updated") or 0) >= file_mtime - 2.0:
            raw_m = pushed.get("model") or {}
            m_info = resolve_model(raw_m.get("id"), raw_m.get("displayName"), raw_m.get("effort"), custom_rules=custom_rules, default_window=(pushed.get("context") or {}).get("window"))
            out = dict(pushed)
            out["model"] = m_info
            return out

    if not chosen or not chosen.is_file():
        return None

    session_id = None
    model_id = None
    effort = None
    latest_usage = None
    last_ts = None
    total_cost = 0.0
    has_cost = False

    for line in read_head_lines(chosen, count=4):
        try:
            h = json.loads(line)
            if h.get("type") == "session":
                session_id = h.get("id")
                cwd = h.get("cwd") or cwd
        except ValueError:
            continue

    for line in read_tail_lines(chosen, max_bytes=196608):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        etype = entry.get("type")
        if etype == "model_change":
            model_id = entry.get("modelId") or entry.get("model") or model_id
        elif etype == "thinking_level_change":
            effort = entry.get("thinkingLevel") or effort
        msg = entry.get("message")
        if isinstance(msg, dict):
            model_id = msg.get("model") or model_id
            usage = msg.get("usage")
            if isinstance(usage, dict):
                if num((usage.get("cost") or {}).get("total")) is not None:
                    total_cost += float(usage["cost"]["total"])
                    has_cost = True
                if usage.get("input") is not None or usage.get("cacheRead") is not None or usage.get("totalTokens") is not None:
                    latest_usage = usage
                    last_ts = parse_iso_ts(entry.get("timestamp")) or last_ts

    short_m = str(model_id or "").split("/")[-1]
    win_hint = pi_windows.get(str(model_id or "")) or pi_windows.get(short_m)
    model_info = resolve_model(model_id or adapter, effort=effort, custom_rules=custom_rules, default_window=win_hint or 200000)
    window = win_hint or model_info.get("window") or 200000

    inp = int((latest_usage or {}).get("input") or 0)
    cr = int((latest_usage or {}).get("cacheRead") or 0)
    cw = int((latest_usage or {}).get("cacheWrite") or 0)
    out = int((latest_usage or {}).get("output") or 0)
    prompt_total = inp + cr + cw
    tokens = int(latest_usage["totalTokens"]) if num((latest_usage or {}).get("totalTokens")) is not None else (prompt_total if latest_usage else None)
    pct = (tokens * 100.0 / window) if (tokens is not None and window) else None
    hit_ratio = (cr * 100.0 / prompt_total) if (prompt_total > 0 and cr > 0) else None
    expires_at = (last_ts + 300.0) if (last_ts and hit_ratio is not None and last_ts + 300.0 > time.time()) else None

    return {
        "adapter": adapter,
        "source": f"{adapter}-jsonl",
        "sessionId": session_id,
        "cwd": cwd or None,
        "model": model_info,
        "context": {
            "tokens": tokens,
            "window": window,
            "percent": pct,
            "inputTokens": inp or None,
            "outputTokens": out or None,
            "cacheReadTokens": cr or None,
            "cacheWriteTokens": cw or None,
        },
        "cache": {
            "hitRatio": hit_ratio,
            "warm": expires_at is not None,
            "expiresAt": expires_at,
        },
        "cost": {"totalUsd": round(total_cost, 4), "estimated": False} if has_cost else {},
    }


def collect_grok_passive(home, target, custom_rules):
    sessions_dir = home / ".grok/sessions"
    if not sessions_dir.is_dir():
        return None
    cwd = target.get("cwd") or ""
    chosen_summary = None
    if cwd:
        encoded = quote(cwd, safe="")
        sub = sessions_dir / encoded
        if sub.is_dir():
            summaries = sorted(sub.glob("*/summary.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if summaries:
                chosen_summary = summaries[0]
    if not chosen_summary:
        summaries = sorted(sessions_dir.glob("*/*/summary.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if summaries:
            chosen_summary = summaries[0]
    if not chosen_summary:
        return None
    try:
        data = json.loads(chosen_summary.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    model_id = data.get("current_model_id") or "grok-4"
    effort = data.get("reasoning_effort")
    model_info = resolve_model(model_id, effort=effort, custom_rules=custom_rules, default_window=256000)
    info = data.get("info") or {}
    return {
        "adapter": "grok",
        "source": "grok-summary",
        "sessionId": info.get("id"),
        "cwd": info.get("cwd") or cwd or None,
        "model": model_info,
        "context": {
            "tokens": None,
            "window": model_info.get("window") or 256000,
            "percent": None,
        },
        "mode": data.get("agent_name"),
    }


def collect_one(home, root_dir, target, proc_index, custom_rules, devin_catalog):
    adapter = detect_adapter(target, proc_index)
    terminal = str(target.get("terminal") or "")
    cwd = target.get("cwd") or ""
    data = None

    try:
        if adapter == "devin":
            data = collect_devin_passive(home, root_dir, target, proc_index, custom_rules, devin_catalog)
        elif adapter == "claude-code":
            data = collect_claude_passive(home, root_dir, target, proc_index, custom_rules)
        elif adapter == "codex":
            data = collect_codex_passive(home, target, custom_rules)
        elif adapter == "antigravity":
            data = collect_antigravity_passive(home, target, custom_rules)
        elif adapter in ("pi", "omp"):
            data = collect_pi_family_passive(home, root_dir, target, adapter, custom_rules)
        elif adapter == "grok":
            data = collect_grok_passive(home, target, custom_rules)
    except Exception:
        data = None

    # Merge any voluntary push cache when passive collector had no data
    pushed = read_push_cache(root_dir, terminal)
    if not data and pushed:
        data = dict(pushed)
        raw_m = data.get("model") or {}
        if isinstance(raw_m, dict) and (raw_m.get("id") or raw_m.get("displayName")):
            data["model"] = resolve_model(
                raw_m.get("id"),
                raw_m.get("displayName"),
                raw_m.get("effort"),
                custom_rules=custom_rules,
                default_window=(data.get("context") or {}).get("window"),
            )

    if not data:
        prog_name = target.get("programName") or target.get("app") or ("shell" if adapter == "shell" else adapter)
        data = {
            "adapter": adapter,
            "source": "herdr-live",
            "cwd": cwd or None,
            "model": {
                "id": adapter,
                "displayName": prog_name,
                "family": infer_family(str(prog_name).lower()),
            },
        }

    final_cwd = data.get("cwd") or cwd
    vcs = collect_git_swr(final_cwd, root_dir) if final_cwd else {}
    if vcs:
        merged_vcs = dict(vcs)
        if isinstance(data.get("vcs"), dict):
            merged_vcs.update({k: v for k, v in data["vcs"].items() if v is not None})
        data["vcs"] = merged_vcs

    data["terminal"] = terminal
    data["updated"] = time.time()
    return {k: v for k, v in data.items() if v not in (None, {}, [])}


def normalize_ingested_payload(payload, adapter, custom_rules):
    model = payload.get("model") or {}
    cw = payload.get("context_window") or {}
    usage = cw.get("current_usage") or {}
    inp = first_num(usage.get("input_tokens"), 0) or 0
    cr = first_num(usage.get("cache_read_input_tokens"), 0) or 0
    cw_tok = first_num(usage.get("cache_creation_input_tokens"), 0) or 0
    out = first_num(usage.get("output_tokens"), 0) or 0
    used = first_num(
        (inp + cr + cw_tok) if usage else None,
        cw.get("total_tokens"),
        cw.get("total_input_tokens"),
    )
    window = first_num(cw.get("context_window_size"))
    pct = first_num(cw.get("used_percentage"))
    if used is None and pct is not None and window:
        used = round(float(pct) * float(window) / 100.0)
    if pct is None and used is not None and window:
        pct = float(used) * 100.0 / float(window)

    denom = inp + cr + cw_tok
    hit_ratio = (cr * 100.0 / denom) if denom > 0 and cr > 0 else None
    prompt_cache = payload.get("prompt_cache") or {}
    if hit_ratio is None and num(prompt_cache.get("hit_ratio")) is not None:
        r = float(prompt_cache["hit_ratio"])
        hit_ratio = r * 100.0 if r <= 1.0 else r

    effort = model.get("effort") or ((payload.get("effort") or {}).get("level") if isinstance(payload.get("effort"), dict) else None)
    m_info = resolve_model(model.get("id"), model.get("display_name") or model.get("displayName"), effort, custom_rules=custom_rules, default_window=int(window) if window else None)
    cost_obj = payload.get("cost") or {}
    usd = first_num(cost_obj.get("total_usd"), cost_obj.get("total_cost_usd"))

    return {
        "version": 1,
        "adapter": adapter,
        "source": "statusline-ingest",
        "terminal": os.environ.get("HC_TERMINAL_ID", ""),
        "sessionId": payload.get("session_id") or payload.get("conversation_id"),
        "updated": time.time(),
        "cwd": ((payload.get("workspace") or {}).get("current_dir") if isinstance(payload.get("workspace"), dict) else None) or payload.get("cwd"),
        "model": m_info,
        "context": {
            "tokens": int(used) if used is not None else None,
            "window": int(window) if window is not None else m_info.get("window"),
            "percent": pct,
            "inputTokens": int(inp) if inp else None,
            "outputTokens": int(out) if out else None,
            "cacheReadTokens": int(cr) if cr else None,
            "cacheWriteTokens": int(cw_tok) if cw_tok else None,
        },
        "cache": {
            "hitRatio": hit_ratio,
            "warm": prompt_cache.get("warm"),
            "expiresAt": prompt_cache.get("expires_at"),
        },
        "cost": {"totalUsd": usd, "estimated": cost_obj.get("estimated")} if usd is not None else {},
        "mode": payload.get("cycle_mode") or payload.get("permission_mode"),
    }


def cmd_collect(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", default="[]", help="JSON array of terminal descriptors")
    parser.add_argument("--config", default="{}", help="Optional user config JSON")
    parser.add_argument("--home", type=Path, help="Override user home directory (for testing)")
    args = parser.parse_args(argv)

    home = (args.home or Path.home()).expanduser().resolve()
    root_dir = runtime_root(home)
    try:
        targets = json.loads(args.targets or "[]")
    except ValueError:
        targets = []
    try:
        cfg = json.loads(args.config or "{}")
    except ValueError:
        cfg = {}

    custom_rules = cfg.get("models") if isinstance(cfg, dict) and isinstance(cfg.get("models"), list) else []
    proc_index = ProcessIndex()
    needs_devin = any("devin" in str(t.get("app") or "") or "devin" in str(t.get("programKey") or "") for t in targets if isinstance(t, dict))
    devin_catalog = load_devin_catalog(root_dir) if needs_devin else {}

    agents_out = {}
    for target in targets:
        if not isinstance(target, dict):
            continue
        term = str(target.get("terminal") or "")
        if not term:
            continue
        agents_out[term] = collect_one(home, root_dir, target, proc_index, custom_rules, devin_catalog)

    sys.stdout.write(compact_json({"ok": True, "updated": time.time(), "agents": agents_out}))
    return 0


def cmd_ingest(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", default="generic")
    parser.add_argument("--home", type=Path)
    parser.add_argument("--passthrough", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    home = (args.home or Path.home()).expanduser().resolve()
    root_dir = runtime_root(home)
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except ValueError:
        payload = {}
    status = normalize_ingested_payload(payload, args.adapter, [])
    term = status.get("terminal") or ""
    if TERMINAL_RE.fullmatch(term):
        try:
            atomic_write(root_dir / "agents" / f"{term}.json", compact_json(status))
        except OSError:
            pass
    if args.passthrough:
        try:
            proc = subprocess.run(args.passthrough, input=raw, capture_output=True, text=True, timeout=5.0)
            if proc.returncode == 0 and proc.stdout:
                sys.stdout.write(proc.stdout)
        except (OSError, subprocess.TimeoutExpired):
            pass
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    sub = argv[0] if argv else "collect"
    if sub == "collect":
        return cmd_collect(argv[1:])
    if sub == "ingest":
        return cmd_ingest(argv[1:])
    return cmd_collect(argv)


if __name__ == "__main__":
    sys.exit(main())
