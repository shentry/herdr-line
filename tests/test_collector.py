import unittest
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "mods/ccline"))
sys.path.insert(0, str(REPO / "scripts"))

import collector  # noqa: E402
import install as installer  # noqa: E402


class CollectorTests(unittest.TestCase):
    def test_resolve_model_across_families_and_modifiers(self):
        c = collector.resolve_model("auto/claude-opus-5-5[1m]", effort="xHigh")
        self.assertEqual(c["displayName"], "Opus 5.5 1M")
        self.assertEqual(c["window"], 1000000)
        self.assertEqual(c["family"], "claude")
        self.assertEqual(c["effort"], "xHigh")

        g = collector.resolve_model("gemini-4-carbon-high")
        self.assertEqual(g["displayName"], "Gemini 4 Carbon")
        self.assertEqual(g["effort"], "high")
        self.assertEqual(g["window"], 1000000)
        self.assertEqual(g["family"], "gemini")

        d = collector.resolve_model("swe-2-1-max")
        self.assertEqual(d["displayName"], "SWE-2.1 Max")
        self.assertIsNone(d["effort"])
        self.assertEqual(d["window"], 262144)
        self.assertEqual(d["family"], "devin")

        custom = collector.resolve_model(
            "my-router/kimi-k2-preview",
            custom_rules=[{"pattern": "kimi-k2", "displayName": "Kimi K2 Custom", "window": 256000}],
        )
        self.assertEqual(custom["displayName"], "Kimi K2 Custom")
        self.assertEqual(custom["window"], 256000)

    def test_claude_passive_with_pid_session_and_unicode_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cwd = str(home / "知识库")
            os.makedirs(cwd, exist_ok=True)
            sdir = home / ".claude/sessions"
            sdir.mkdir(parents=True)
            sid = "00000000-0000-4000-8000-000000000001"  # Synthetic UUID fixture.
            (sdir / "42424.json").write_text(
                json.dumps({"pid": 42424, "sessionId": sid, "cwd": cwd, "name": "kb-work"}),
                encoding="utf-8",
            )
            slug = collector.re.sub(r"[^a-zA-Z0-9]", "-", cwd)
            pdir = home / ".claude/projects" / slug
            pdir.mkdir(parents=True)
            now_iso = "2099-01-01T00:00:00Z"
            (pdir / f"{sid}.jsonl").write_text(
                json.dumps(
                    {
                        "type": "assistant",
                        "sessionId": sid,
                        "cwd": cwd,
                        "timestamp": now_iso,
                        "message": {
                            "model": "claude-opus-5-5[1m]",
                            "usage": {
                                "input_tokens": 5000,
                                "cache_read_input_tokens": 95000,
                                "cache_creation_input_tokens": 0,
                                "output_tokens": 800,
                            },
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            proc_index = collector.ProcessIndex([(42424, 100, "claude")])
            res = collector.collect_one(
                home,
                home / ".config/herdr-ccline",
                {"terminal": "t1", "pid": 42424, "cwd": cwd, "app": "claude-code"},
                proc_index,
                [],
                {},
            )
            self.assertEqual(res["adapter"], "claude-code")
            self.assertEqual(res["model"]["displayName"], "Opus 5.5 1M")
            self.assertEqual(res["context"]["tokens"], 100000)
            self.assertAlmostEqual(res["context"]["percent"], 10.0)
            self.assertAlmostEqual(res["cache"]["hitRatio"], 95.0)
            self.assertTrue(res["cache"]["warm"])

    def test_codex_passive_without_double_counting_cached_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cwd = str(home / "repo")
            os.makedirs(cwd, exist_ok=True)
            rdir = home / ".codex/sessions/2026/11/25"
            rdir.mkdir(parents=True)
            rollout = rdir / "rollout-1.jsonl"
            rollout.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "session_meta", "payload": {"id": "cx-1", "cwd": cwd}}),
                        json.dumps(
                            {
                                "type": "turn_context",
                                "payload": {"cwd": cwd, "model": "gpt-6.1-sol", "effort": "high", "approval_policy": "on-request"},
                            }
                        ),
                        json.dumps(
                            {
                                "timestamp": "2099-01-01T00:00:00Z",
                                "type": "event_msg",
                                "payload": {
                                    "type": "token_count",
                                    "info": {
                                        "model_context_window": 400000,
                                        "last_token_usage": {
                                            "input_tokens": 160000,
                                            "cached_input_tokens": 144000,
                                            "output_tokens": 500,
                                            "total_tokens": 160500,
                                        },
                                        "total_token_usage": {
                                            "input_tokens": 320000,
                                            "cached_input_tokens": 280000,
                                            "output_tokens": 1200,
                                        },
                                    },
                                    "rate_limits": {
                                        "primary": {"used_percent": 22.5, "resets_at": 4102444800},
                                        "secondary": {"used_percent": 61.0, "resets_at": 4102531200},
                                    },
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            res = collector.collect_codex_passive(home, {"cwd": cwd}, [])
            self.assertEqual(res["model"]["displayName"], "GPT-6.1 Sol")
            self.assertEqual(res["context"]["tokens"], 160000)
            self.assertAlmostEqual(res["context"]["percent"], 40.0)
            self.assertAlmostEqual(res["cache"]["hitRatio"], 90.0)
            self.assertEqual(res["quota"]["5H"]["percent"], 22.5)
            self.assertEqual(res["quota"]["7D"]["percent"], 61.0)

    def test_devin_antigravity_pi_and_grok_adapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cwd = str(home / "work")
            os.makedirs(cwd, exist_ok=True)

            # 1. Devin SQLite + session lock
            devin_dir = home / ".local/share/devin/cli"
            (devin_dir / "session_locks").mkdir(parents=True)
            (devin_dir / "session_locks/calm-otter.lock").write_text("51515\n", encoding="utf-8")
            con = sqlite3.connect(str(devin_dir / "sessions.db"))
            con.execute(
                "CREATE TABLE sessions (id TEXT, working_directory TEXT, model TEXT, agent_mode TEXT, last_activity_at INT, title TEXT, hidden INT, metadata TEXT)"
            )
            con.execute(
                "CREATE TABLE message_nodes (node_id INT, session_id TEXT, chat_message TEXT, created_at TEXT)"
            )
            con.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                ("calm-otter", cwd, "swe-2-1-max", "dangerous", int(time.time()), "Build ccline", json.dumps({"total_acu_cost": 1.75})),
            )
            con.execute(
                "INSERT INTO message_nodes VALUES (1, 'calm-otter', ?, '2099-01-01T00:00:00Z')",
                (
                    json.dumps(
                        {
                            "metadata": {
                                "generation_model": "swe-2-1-max",
                                "metrics": {
                                    "context_input_tokens": 65536,
                                    "cache_read_tokens": 60000,
                                    "output_tokens": 420,
                                    "ttft_ms": 1800,
                                    "tokens_per_sec": 145,
                                },
                            }
                        }
                    ),
                ),
            )
            con.commit()
            con.close()

            # Child tool process 51520 under devin 51515 under shell 51500
            proc = collector.ProcessIndex([(51500, 1, "zsh"), (51515, 51500, "devin"), (51520, 51515, "bash -c ls")])
            d_res = collector.collect_devin_passive(home, home / ".config/herdr-ccline", {"pid": 51520, "cwd": cwd}, proc, [], {})
            self.assertEqual(d_res["sessionId"], "calm-otter")
            self.assertEqual(d_res["mode"], "bypass")
            self.assertAlmostEqual(d_res["context"]["percent"], 25.0)
            self.assertEqual(d_res["cost"]["acu"], 1.75)

            # 2. Antigravity transcript
            agy_logs = home / ".gemini/antigravity-cli/brain/conv-123/.system_generated/logs"
            agy_logs.mkdir(parents=True)
            (agy_logs / "transcript.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"step_index": 0, "type": "USER_INPUT", "content": f"Working in {cwd}"}),
                        json.dumps(
                            {
                                "step_index": 1,
                                "type": "PLANNER_RESPONSE",
                                "created_at": "2099-01-01T00:00:00Z",
                                "model": "gemini-4-carbon-high",
                                "input_tokens": 10000,
                                "cache_read_tokens": 40000,
                                "output_tokens": 600,
                                "tool_calls": [{"name": "invoke_subagent"}],
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            a_res = collector.collect_antigravity_passive(home, {"cwd": cwd}, [])
            self.assertEqual(a_res["context"]["tokens"], 50000)
            self.assertAlmostEqual(a_res["cache"]["hitRatio"], 80.0)
            self.assertEqual(a_res["activity"]["subagents"], 1)

            # 3. Pi JSONL passive
            pi_slug = "--" + cwd.strip("/").replace("/", "-") + "--"
            pi_dir = home / ".pi/agent/sessions" / pi_slug
            pi_dir.mkdir(parents=True)
            (pi_dir / "s1.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"type": "session", "id": "pi-s1", "cwd": cwd}),
                        json.dumps({"type": "thinking_level_change", "thinkingLevel": "high"}),
                        json.dumps(
                            {
                                "type": "message",
                                "timestamp": "2099-01-01T00:00:00Z",
                                "message": {
                                    "model": "claude-sonnet-4-5",
                                    "usage": {
                                        "input": 2000,
                                        "cacheRead": 18000,
                                        "cacheWrite": 0,
                                        "output": 300,
                                        "totalTokens": 20300,
                                        "cost": {"total": 0.125},
                                    },
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            p_res = collector.collect_pi_family_passive(home, home / ".config/herdr-ccline", {"terminal": "t9", "cwd": cwd}, "pi", [])
            self.assertEqual(p_res["model"]["displayName"], "Sonnet 4.5")
            self.assertEqual(p_res["model"]["effort"], "high")
            self.assertEqual(p_res["cost"]["totalUsd"], 0.125)

            # 4. Grok summary
            g_dir = home / ".grok/sessions" / quote(cwd, safe="") / "g-1"
            g_dir.mkdir(parents=True)
            (g_dir / "summary.json").write_text(
                json.dumps({"info": {"id": "g-1", "cwd": cwd}, "current_model_id": "grok-4.7", "reasoning_effort": "high", "agent_name": "plan"}),
                encoding="utf-8",
            )
            g_res = collector.collect_grok_passive(home, {"cwd": cwd}, [])
            self.assertEqual(g_res["model"]["displayName"], "Grok 4.7")
            self.assertEqual(g_res["mode"], "plan")

    def test_git_swr_and_safe_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            repo = home / "sample-repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-b", "feat/ccline", str(repo)], check=True, capture_output=True)
            (repo / "hello.txt").write_text("hello\n", encoding="utf-8")
            vcs = collector.collect_git_swr(str(repo), home / ".config/herdr-ccline")
            self.assertEqual(vcs["branch"], "feat/ccline")
            self.assertTrue(vcs["dirty"])
            self.assertEqual(vcs["untracked"], 1)

            # Installer dry-run writes nothing
            app_home = home / ".config/herdr-app"
            (app_home / "layouts").mkdir(parents=True)
            (app_home / "layouts/my-main.json").write_text(
                json.dumps(
                    {
                        "id": "root",
                        "type": "column",
                        "children": [{"id": "status", "type": "block", "content": {"mod": "workspace-status"}, "size": {"px": 28}}],
                    }
                ),
                encoding="utf-8",
            )
            rc = installer.main(["--dry-run", "--home", str(home), "--activate-layout", "my-main"])
            self.assertEqual(rc, 0)
            self.assertFalse((app_home / "mods/ccline/main.js").exists())

            # Refuses shipped layout 'main'
            rc_shipped = installer.main(["--apply", "--home", str(home), "--activate-layout", "main"])
            self.assertEqual(rc_shipped, 1)

            # Apply succeeds and updates cloned layout
            rc_apply = installer.main(["--apply", "--home", str(home), "--activate-layout", "my-main"])
            self.assertEqual(rc_apply, 0)
            self.assertTrue((app_home / "mods/ccline/main.js").is_file())
            self.assertTrue((home / ".pi/agent/extensions/herdr-ccline.ts").is_file())
            updated_layout = json.loads((app_home / "layouts/my-main.json").read_text(encoding="utf-8"))
            self.assertEqual(updated_layout["children"][0]["content"]["mod"], "ccline")
            self.assertEqual(updated_layout["children"][0]["size"]["px"], 48)


if __name__ == "__main__":
    unittest.main()
