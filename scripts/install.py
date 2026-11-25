#!/usr/bin/env python3
"""Safe whitelist installer for Herdr Line plugin.

Never modifies Claude/Antigravity/Codex/Devin CLI settings or read-only shipped Herdr layouts.
Optionally wires a user's personal cloned layout (--activate-layout <name>) with atomic backup.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

PROJECT = Path(__file__).resolve().parents[1]

MOD_FILES = (
    "main.js",
    "layout.js",
    "collector.py",
    "mod.json",
    "jsconfig.json",
    "icons/model.svg",
    "icons/claude.svg",
    "icons/gemini.svg",
    "icons/openai.svg",
    "icons/devin.svg",
    "icons/grok.svg",
    "icons/folder.svg",
    "icons/git.svg",
    "icons/context.svg",
    "icons/cache.svg",
    "icons/quota.svg",
    "icons/cost.svg",
    "icons/bolt.svg",
    "icons/clock.svg",
    "icons/sliders.svg",
    "icons/terminal.svg",
)

SHIPPED_LAYOUTS = frozenset({"main", "terminals", "win98"})


def safe_path(path):
    """Refuse symbolic links anywhere in source or destination chain."""
    path = Path(path)
    for current in (path, *path.parents):
        if current.is_symlink():
            raise ValueError(f"Refusing symbolic link: {current}")
    return path


def atomic_write(path, data, mode):
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(prefix=".ccline-install-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        safe_path(path)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def build_plan(app_home, pi_agent_dir):
    files = [
        (PROJECT / "mods/ccline" / rel, app_home / "mods/ccline" / rel)
        for rel in MOD_FILES
    ]
    files.append(
        (
            PROJECT / "extensions/herdr-ccline.ts",
            pi_agent_dir / "extensions/herdr-ccline.ts",
        )
    )
    return files


def preflight(files, allow_replace=False):
    changes = []
    for source, target in files:
        safe_path(source)
        safe_path(target)
        data = source.read_bytes()
        if target.exists():
            if not target.is_file():
                raise ValueError(f"Destination is not a regular file: {target}")
            if target.read_bytes() == data:
                continue
            if not allow_replace:
                raise ValueError(f"Existing file differs (pass --replace to back up and overwrite): {target}")
        changes.append((source, target, data))
    return changes


def patch_status_node(node, height=48):
    if not isinstance(node, dict):
        return False
    if node.get("id") == "status" and node.get("type") == "block":
        node["content"] = {"mod": "ccline"}
        node["size"] = {"px": height}
        return True
    for child in node.get("children") or ():
        if patch_status_node(child, height=height):
            return True
    return False


def prepare_layout_update(app_home, layout_name, height=48):
    if layout_name in SHIPPED_LAYOUTS:
        raise ValueError(
            f"Refusing to edit shipped Herdr layout '{layout_name}'. "
            f"Clone it first with: herdr-app do layout.clone '{{\"name\":\"{layout_name}\",\"as\":\"my-{layout_name}\"}}'"
        )
    layout_path = app_home / "layouts" / f"{layout_name}.json"
    safe_path(layout_path)
    if not layout_path.is_file():
        raise ValueError(f"Layout file does not exist: {layout_path}")
    tree = json.loads(layout_path.read_text(encoding="utf-8"))
    if not patch_status_node(tree, height=height):
        raise ValueError(f"Layout '{layout_name}' has no block with id='status'")
    rendered = (json.dumps(tree, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return layout_path, rendered


def main(argv=None):
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Install validated whitelist files")
    mode.add_argument("--dry-run", action="store_true", help="Preview operations without writing (default)")
    parser.add_argument("--replace", action="store_true", help="Back up and overwrite differing plugin files")
    parser.add_argument("--home", type=Path, help="Target user home directory")
    parser.add_argument("--app-home", type=Path, help="Custom Herdr app config folder")
    parser.add_argument("--pi-agent-dir", type=Path, help="Custom Pi agent config folder")
    parser.add_argument(
        "--activate-layout",
        metavar="NAME",
        help="Wire bottom status block to 'ccline' in a cloned personal layout (e.g. main-timers)",
    )
    args = parser.parse_args(argv)

    home = (args.home or Path.home()).expanduser().resolve()
    app_home = (
        args.app_home
        or (Path(os.environ["HERDR_APP_HOME"]) if not args.home and os.environ.get("HERDR_APP_HOME") else home / ".config/herdr-app")
    ).expanduser().absolute()
    pi_agent_dir = (args.pi_agent_dir or home / ".pi/agent").expanduser().absolute()

    try:
        files = build_plan(app_home, pi_agent_dir)
        changes = preflight(files, allow_replace=args.replace or not args.apply)
        layout_plan = None
        if args.activate_layout:
            layout_path, layout_bytes = prepare_layout_update(app_home, args.activate_layout)
            if layout_path.read_bytes() != layout_bytes:
                layout_plan = (layout_path, layout_bytes)

        for _src, target, _data in changes:
            verb = "replace" if target.exists() else "install"
            prefix = verb.capitalize() if args.apply else f"Would {verb}"
            print(f"{prefix}: {target}")
        if layout_plan:
            prefix = "Update layout" if args.apply else "Would update layout"
            print(f"{prefix}: {layout_plan[0]}")

        if not args.apply:
            print("Dry run complete. Re-run with --apply to write files.")
            return 0

        backup_root = home / ".config/herdr-ccline/backups" / f"install-{uuid.uuid4().hex[:12]}"
        backed_up = False
        for src, target, _data in changes:
            if target.exists():
                atomic_write(backup_root / src.relative_to(PROJECT), target.read_bytes(), 0o600)
                backed_up = True
        if layout_plan:
            atomic_write(backup_root / "layouts" / layout_plan[0].name, layout_plan[0].read_bytes(), 0o600)
            backed_up = True

        for src, target, data in changes:
            mode_bits = 0o755 if src.name.endswith(".py") else 0o644
            atomic_write(target, data, mode_bits)
        if layout_plan:
            atomic_write(layout_plan[0], layout_plan[1], 0o644)

        print(f"Installed {len(changes)} plugin files." + (" Updated personal layout." if layout_plan else ""))
        if backed_up:
            print(f"Private backup saved to: {backup_root}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Herdr Line installation refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
