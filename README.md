# codex-warp

Local Codex plugin that forwards Codex lifecycle hooks to a patched Warp OSS build.

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

```sh
git clone https://github.com/eclipse1228/codex-warp.git ~/codex-warp
codex plugin marketplace add ~/codex-warp
codex plugin add warp@codex-warp
```

## Test checklist

1. Open a new terminal tab in the patched Warp OSS build.
2. Confirm the required env vars exist:

```sh
env | rg '^WARP_(AGENT_SOCKET|REMOTE_AGENT_SOCKET|TERMINAL_VIEW_ID|BUNDLED_CLI_PATH)='
```

3. Start a new Codex session.
4. Open `/hooks` and trust the `warp@codex-warp` hook definitions.
5. Send a Codex prompt. `UserPromptSubmit` should mark the tab as running and `Stop` should mark it complete.

If `WARP_TERMINAL_VIEW_ID`, `WARP_BUNDLED_CLI_PATH`, and either `WARP_AGENT_SOCKET` or `WARP_REMOTE_AGENT_SOCKET` are missing, the hook exits successfully without sending a notification. This keeps normal Codex sessions outside patched Warp unaffected.

For existing local tmux servers, start a fresh tmux server from a patched Warp shell or propagate the local `WARP_*` env vars into the tmux server before starting Codex. For SSH warpified tmux, use the patched Warp OSS build so it injects `WARP_REMOTE_AGENT_SOCKET` and the remote bundled helper path.
