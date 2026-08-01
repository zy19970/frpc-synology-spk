
## 0.70.1-6 launcher fix

- Uses a new DSM application identifier: `SYNO.SDS.FRPCClient`.
- Adds the DSM 6 legacy-window `appWindow` field.
- Uses the exact root-relative UI path `/webman/3rdparty/frpc/index.html`.
- Keeps the existing `frpc.toml` during an in-place upgrade.

# FRP Client for Synology DSM 6.2 — 0.70.1-6

Offline x86_64 SPK containing the official `frpc 0.70.1` binary.

This revision changes the DSM application entry from `index.cgi` to the static
`index.html`. The CGI script is used only for authenticated AJAX operations at
`/webman/3rdparty/frpc/api.cgi`. UI symlink lifecycle is left to DSM through
`dsmuidir="ui"`; the service script no longer creates or removes the DSM link.

Configuration: `/var/packages/frpc/etc/frpc.toml`
Logs: `/var/packages/frpc/var/frpc.log`

## 构建与调试

详细说明见 [`BUILD_AND_DEBUG.md`](BUILD_AND_DEBUG.md)，包括 Linux/WSL2 构建、SPK 结构检查、DSM 服务调试、Web UI 排障、版本升级和发布检查清单。
