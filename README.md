# codex-warp

Codex plugin that forwards Codex lifecycle hooks to a patched Warp OSS build so Warp can show Codex running/completed status in top tabs, vertical tabs, and native notifications.

This plugin is intentionally quiet outside supported Warp environments. If Warp has not injected the required notification helper environment variables, hooks exit successfully without printing anything or changing Codex behavior.

## Requirements

- Codex CLI with plugin and hook support
- A patched Warp OSS build that injects the CLI agent notification env vars
- `python3`
- Hook trust enabled for this plugin in Codex

The plugin uses Warp's injected environment variables:

- `WARP_AGENT_SOCKET`
- `WARP_REMOTE_AGENT_SOCKET`
- `WARP_TERMINAL_VIEW_ID`
- `WARP_BUNDLED_CLI_PATH`

When Codex fires a hook, `plugins/warp/scripts/warp_agent_notify.py` converts the Codex hook input into Warp's agent event schema and calls:

```sh
"$WARP_BUNDLED_CLI_PATH" warp-agent-notify --payload-json '<event-json>'
```

## Install

Install from the GitHub marketplace source:

```sh
codex plugin marketplace add eclipse1228/codex-warp
codex
/plugins
```

In the plugin browser, select the `Codex Warp` marketplace and install `warp`.

For local development from a checkout:

```sh
git clone https://github.com/eclipse1228/codex-warp.git ~/codex-warp
codex plugin marketplace add ~/codex-warp
codex
/plugins
```

After installing, start a new Codex session and open:

```text
/hooks
```

Review and trust the `warp@codex-warp` hook definitions. Codex records hook trust by hash, so after plugin updates you may need to trust the hooks again.

## Test Checklist

1. Open a new terminal tab in the patched Warp OSS build.
2. Confirm the required env vars exist:

```sh
env | rg '^WARP_(AGENT_SOCKET|REMOTE_AGENT_SOCKET|TERMINAL_VIEW_ID|BUNDLED_CLI_PATH)='
```

3. Start a new Codex session.
4. Open `/hooks` and trust the `warp@codex-warp` hook definitions.
5. Send a Codex prompt. `UserPromptSubmit` should mark the tab as running and `Stop` should mark it complete.

## SSH and tmux

If `WARP_TERMINAL_VIEW_ID`, `WARP_BUNDLED_CLI_PATH`, and either `WARP_AGENT_SOCKET` or `WARP_REMOTE_AGENT_SOCKET` are missing, the hook exits successfully without sending a notification. This keeps normal Codex sessions outside patched Warp unaffected.

For existing local tmux servers, start a fresh tmux server from a patched Warp shell or propagate the local `WARP_*` env vars into the tmux server before starting Codex. For SSH warpified tmux, use the patched Warp OSS build so it injects `WARP_REMOTE_AGENT_SOCKET` and the remote bundled helper path.

Expected env check inside an SSH + tmux session:

```sh
env | rg '^WARP_(REMOTE_AGENT_SOCKET|TERMINAL_VIEW_ID|BUNDLED_CLI_PATH|CLI_AGENT_PROTOCOL_VERSION)='
tmux -Lwarp show-environment -g | rg '^WARP_(REMOTE_AGENT_SOCKET|TERMINAL_VIEW_ID|BUNDLED_CLI_PATH|CLI_AGENT_PROTOCOL_VERSION|AGENT_SOCKET)='
```

Manual helper test:

```sh
"${WARP_BUNDLED_CLI_PATH/#\~/$HOME}" warp-agent-notify \
  --agent codex \
  --event stop \
  --summary "manual codex notify test"
```

## Hook Events

The plugin maps Codex hook events to Warp CLI agent events:

- `SessionStart` -> `session_start`
- `UserPromptSubmit` -> `prompt_submit`
- `PermissionRequest` -> `permission_request`
- `PostToolUse` -> `tool_complete`
- `Stop` -> `stop`

## Development

Run tests:

```sh
python3 plugins/warp/tests/test_warp_agent_notify.py
python3 -m py_compile plugins/warp/scripts/warp_agent_notify.py plugins/warp/tests/test_warp_agent_notify.py
```

Validate plugin metadata from the repo root:

```sh
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/warp
```

## Privacy

This plugin runs locally inside Codex hooks. It forwards Codex lifecycle metadata to Warp through the helper path exposed by the local Warp session. It does not send data to this repository owner or to any third-party service by itself.

Event payloads may include the current working directory, prompt text, assistant summary, tool name, and truncated tool input when Codex provides those fields to the hook.

## Terms

This plugin is provided as-is under the MIT license. Use it only with Warp and Codex environments where you are comfortable forwarding hook metadata to the local Warp notification pipeline.
