#!/usr/bin/env python3
"""Forward Codex hook events to Warp's CLI agent notification helper."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any


PLUGIN_VERSION = "0.1.1"

EVENT_MAP = {
    "SessionStart": "session_start",
    "UserPromptSubmit": "prompt_submit",
    "PermissionRequest": "permission_request",
    "PostToolUse": "tool_complete",
    "Stop": "stop",
}


def main() -> int:
    raw = sys.stdin.read()
    try:
        hook_input = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0

    event = EVENT_MAP.get(as_str(hook_input.get("hook_event_name")))
    if event is None:
        return 0

    helper = expand_path(os.environ.get("WARP_BUNDLED_CLI_PATH"))
    socket = os.environ.get("WARP_AGENT_SOCKET") or os.environ.get("WARP_REMOTE_AGENT_SOCKET")
    terminal_view_id = os.environ.get("WARP_TERMINAL_VIEW_ID")
    if not helper or not socket or not terminal_view_id or not os.access(helper, os.X_OK):
        return 0

    payload = build_payload(hook_input, event)
    try:
        subprocess.run(
            [helper, "warp-agent-notify", "--payload-json", json.dumps(payload, separators=(",", ":"))],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except Exception:
        return 0

    return 0


def expand_path(value: str | None) -> str | None:
    if not value:
        return None
    return os.path.expanduser(value)


def build_payload(hook_input: dict[str, Any], event: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "v": 1,
        "agent": "codex",
        "event": event,
        "plugin_version": PLUGIN_VERSION,
    }

    copy_string(payload, hook_input, "session_id")
    copy_string(payload, hook_input, "cwd")
    copy_string(payload, hook_input, "transcript_path")
    copy_string(payload, hook_input, "tool_name")

    turn_id = as_str(hook_input.get("turn_id"))
    if turn_id:
        payload["turn_id"] = turn_id
        payload.setdefault("session_id", turn_id)

    project = project_name(as_str(hook_input.get("cwd")))
    if project:
        payload["project"] = project

    prompt = as_str(hook_input.get("prompt"))
    if prompt:
        payload["query"] = prompt

    last_assistant_message = as_str(hook_input.get("last_assistant_message"))
    if last_assistant_message:
        payload["response"] = last_assistant_message
        payload["summary"] = truncate(last_assistant_message, 240)

    tool_input = hook_input.get("tool_input")
    if isinstance(tool_input, dict):
        command = as_str(tool_input.get("command")) or as_str(tool_input.get("file_path"))
        if command:
            payload["tool_input"] = {"command": truncate(command, 240)}

        description = as_str(tool_input.get("description"))
        if description and event == "permission_request":
            payload["summary"] = truncate(description, 240)

    return payload


def copy_string(payload: dict[str, Any], source: dict[str, Any], key: str) -> None:
    value = as_str(source.get(key))
    if value:
        payload[key] = value


def as_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def project_name(cwd: str | None) -> str | None:
    if not cwd:
        return None
    name = os.path.basename(os.path.normpath(cwd))
    return name or None


def truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
