#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "scripts" / "warp_agent_notify.py"


def run_hook(input_payload: dict, helper: Path, remote_socket: bool = False) -> list[str]:
    env = os.environ.copy()
    env.update(
        {
            "WARP_TERMINAL_VIEW_ID": "42",
            "WARP_BUNDLED_CLI_PATH": str(helper),
        }
    )
    if remote_socket:
        env["WARP_REMOTE_AGENT_SOCKET"] = "/tmp/fake-warp-remote.sock"
        env.pop("WARP_AGENT_SOCKET", None)
    else:
        env["WARP_AGENT_SOCKET"] = "/tmp/fake-warp-agent.sock"
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(input_payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    return json.loads(helper.with_suffix(".json").read_text())


def write_fake_helper(tmpdir: Path) -> Path:
    helper = tmpdir / "warp-oss"
    calls = helper.with_suffix(".json")
    helper.write_text(
        f"""#!/usr/bin/env python3
import json
import pathlib
import sys

path = pathlib.Path({str(calls)!r})
path.write_text(json.dumps(sys.argv[1:]))
""",
        encoding="utf-8",
    )
    helper.chmod(0o755)
    return helper


def payload_arg(args: list[str]) -> dict:
    assert args[0] == "warp-agent-notify"
    assert args[1] == "--payload-json"
    return json.loads(args[2])


def test_prompt_submit_maps_to_running_event() -> None:
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        helper = write_fake_helper(Path(raw_tmpdir))
        args = run_hook(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "session-1",
                "turn_id": "turn-1",
                "cwd": "/tmp/project-a",
                "prompt": "fix the failing test",
            },
            helper,
        )

    payload = payload_arg(args)
    assert payload["agent"] == "codex"
    assert payload["event"] == "prompt_submit"
    assert payload["session_id"] == "session-1"
    assert payload["project"] == "project-a"
    assert payload["query"] == "fix the failing test"


def test_stop_maps_to_completion_event_without_stdout() -> None:
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        helper = write_fake_helper(Path(raw_tmpdir))
        args = run_hook(
            {
                "hook_event_name": "Stop",
                "turn_id": "turn-2",
                "cwd": "/tmp/project-b",
                "last_assistant_message": "Implementation complete.",
            },
            helper,
        )

    payload = payload_arg(args)
    assert payload["agent"] == "codex"
    assert payload["event"] == "stop"
    assert payload["session_id"] == "turn-2"
    assert payload["response"] == "Implementation complete."


def test_remote_socket_env_is_accepted_without_local_socket() -> None:
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        helper = write_fake_helper(Path(raw_tmpdir))
        args = run_hook(
            {
                "hook_event_name": "Stop",
                "turn_id": "turn-remote",
                "cwd": "/tmp/project-remote",
            },
            helper,
            remote_socket=True,
        )

    payload = payload_arg(args)
    assert payload["agent"] == "codex"
    assert payload["event"] == "stop"
    assert payload["session_id"] == "turn-remote"


if __name__ == "__main__":
    test_prompt_submit_maps_to_running_event()
    test_stop_maps_to_completion_event_without_stdout()
    test_remote_socket_env_is_accepted_without_local_socket()
