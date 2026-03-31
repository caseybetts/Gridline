from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROLES = ("Planner", "Designer", "Coder", "Tester")
DEFAULT_TERMINAL_MODE = "tabs"


def ps_single_quote(value: str) -> str:
    return value.replace("'", "''")


def build_codex_prompt(role: str, prompt_path: Path) -> str:
    return (
        f"Your terminal title is {role}. "
        f"Read the prompt file at '{prompt_path}' immediately and follow it for this session. "
        f"Use that file as your role instructions."
    )


def build_powershell_command(role: str, workspace: Path, prompt_path: Path) -> str:
    role_ps = ps_single_quote(role)
    workspace_ps = ps_single_quote(str(workspace))
    prompt_ps = ps_single_quote(str(prompt_path))
    codex_prompt_ps = ps_single_quote(build_codex_prompt(role, prompt_path))

    return (
        f"$Host.UI.RawUI.WindowTitle = '{role_ps}'; "
        f"[Console]::Title = '{role_ps}'; "
        f"Set-Location '{workspace_ps}'; "
        f"if (-not (Test-Path '{prompt_ps}')) {{ "
        f"Write-Error 'Missing prompt file: {prompt_ps}'; "
        f"return "
        f"}}; "
        f"codex --cd '{workspace_ps}' '{codex_prompt_ps}'"
    )


def get_prompt_path(role: str, workspace: Path) -> Path:
    prompt_path = workspace / f"{role}_Prompt.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found for role '{role}': {prompt_path}")

    return prompt_path


def build_console_command(role: str, workspace: Path) -> list[str]:
    prompt_path = get_prompt_path(role, workspace)
    ps_command = build_powershell_command(role, workspace, prompt_path)
    return ["powershell.exe", "-NoExit", "-Command", ps_command]


def build_wt_tab_command(role: str, workspace: Path) -> list[str]:
    prompt_path = get_prompt_path(role, workspace)
    ps_command = build_powershell_command(role, workspace, prompt_path)
    return [
        "new-tab",
        "--title",
        role,
        "--suppressApplicationTitle",
        "-d",
        str(workspace),
        "powershell.exe",
        "-NoExit",
        "-Command",
        ps_command,
    ]


def launch_console_windows(workspace: Path, dry_run: bool) -> None:
    for role in ROLES:
        command = build_console_command(role, workspace)

        if dry_run:
            print(f"[dry-run] {role}: {' '.join(command)}")
            continue

        subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)


def launch_windows_terminal_tabs(workspace: Path, dry_run: bool, window_target: str) -> None:
    if not shutil.which("wt"):
        raise RuntimeError("Windows Terminal CLI 'wt' was not found on PATH.")

    command: list[str] = ["wt", "-w", window_target]

    for index, role in enumerate(ROLES):
        if index > 0:
            command.append(";")
        command.extend(build_wt_tab_command(role, workspace))

    if dry_run:
        print(f"[dry-run] {' '.join(command)}")
        return

    subprocess.Popen(command)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open Codex terminals for Planner, Designer, Coder, and Tester roles."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Workspace directory to open in each terminal. Defaults to this script's directory.",
    )
    parser.add_argument(
        "--mode",
        choices=("tabs", "windows"),
        default=DEFAULT_TERMINAL_MODE,
        help="Use Windows Terminal tabs in one window or separate console windows.",
    )
    parser.add_argument(
        "--window-target",
        default="new",
        help="Windows Terminal target window. Use 'new' for a fresh window or '0' to reuse the current WT window.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the terminal launch commands without opening any windows.",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()

    if not workspace.exists():
        print(f"Workspace does not exist: {workspace}", file=sys.stderr)
        return 1

    if not workspace.is_dir():
        print(f"Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1

    try:
        if args.mode == "tabs":
            launch_windows_terminal_tabs(workspace, dry_run=args.dry_run, window_target=args.window_target)
        else:
            launch_console_windows(workspace, dry_run=args.dry_run)
    except (FileNotFoundError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
