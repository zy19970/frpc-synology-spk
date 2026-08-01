# FRP Client DSM 6.2 SPK 构建与调试说明

本文档对应套件版本：`0.70.1-6`。

目标平台：Synology DSM 6.2，`x86_64`。

本项目**不编译 FRP 源码**。构建过程只是把 FRP 官方 `linux_amd64` 发布包中的 `frpc` 二进制、DSM 套件脚本、TOML 管理界面和配置模板封装为 `.spk`。

---

## 1. 目录结构

```text
frpc-spk-source-0.70.1-6-ui-launcher-fix-with-docs/
├─ INFO.in                         # INFO 模板，构建时写入 package.tgz 的 MD5
├─ INFO                            # 最近一次构建生成的 INFO
├─ PACKAGE_ICON.PNG                # 套件中心图标
├─ README.md
├─ BUILD_AND_DEBUG.md              # 本文档
├─ build.sh                        # 使用现有 package/bin/frpc 构建 SPK
├─ build-offline.sh                # 校验官方压缩包、提取 frpc 并构建 SPK
├─ frp_0.70.1_linux_amd64.tar.gz   # FRP 官方发布包
├─ package/
│  ├─ bin/
│  │  ├─ frpc                      # 官方 x86-64 ELF 二进制
│  │  └─ frpc-manager              # 后台管理进程
│  ├─ share/
│  │  └─ frpc.toml.example         # 首次安装使用的配置模板
│  └─ ui/
│     ├─ config                    # DSM 主菜单启动项
│     ├─ index.html                # TOML 管理页面
│     ├─ index.cgi                 # 保留的认证入口，当前主菜单不使用
│     ├─ api.cgi                   # 读取、校验、保存、启停接口
│     └─ images/                   # DSM 菜单图标
└─ scripts/
   ├─ postinst
   ├─ preuninst
   ├─ postuninst
   ├─ preupgrade
   ├─ postupgrade
   └─ start-stop-status
```

构建生成：

```text
package.tgz
INFO
frpc-x86_64-0.70.1-6-ui-launcher-fix.spk
```

---

## 2. 推荐构建环境

推荐使用以下任一环境：

- Ubuntu、Debian 或其他常见 x86-64 Linux；
- Windows 10/11 的 WSL2；
- Linux 虚拟机。

不建议直接使用 macOS 自带 BSD `tar`，因为 `build.sh` 使用了 GNU tar 参数：

```text
--owner=0 --group=0 --numeric-owner
```

macOS 可安装 GNU tar 后，把脚本中的 `tar` 替换为 `gtar`；更简单的方式是使用 WSL2。

所需命令：

```text
sh tar gzip sed awk find md5sum sha256sum dd od tr grep chmod cp mv
```

可选调试工具：

```text
file readelf shellcheck python3 jq curl unzip
```

Ubuntu / WSL2 可执行：

```sh
sudo apt update
sudo apt install -y tar gzip coreutils findutils sed gawk file binutils unzip python3 shellcheck
```

---

## 3. 最快构建方式

进入源码目录：

```sh
cd frpc-spk-source-0.70.1-6-ui-launcher-fix-with-docs
chmod +x build.sh build-offline.sh scripts/* package/bin/frpc-manager package/ui/*.cgi
```

### 3.1 使用已内置的 `frpc` 构建

```sh
./build.sh
```

输出：

```text
frpc-x86_64-0.70.1-6-ui-launcher-fix.spk
```

自定义输出文件名：

```sh
./build.sh frpc-test.spk
```

### 3.2 从 FRP 官方压缩包重新提取并构建

```sh
./build-offline.sh
```

也可以指定压缩包路径：

```sh
./build-offline.sh /path/to/frp_0.70.1_linux_amd64.tar.gz
```

`build-offline.sh` 会依次执行：

1. 校验官方压缩包 SHA-256；
2. 解压并查找 `frpc`；
3. 校验 `frpc` 二进制 SHA-256；
4. 复制到 `package/bin/frpc`；
5. 调用 `build.sh` 生成 `.spk`。

当前固定校验值：

```text
FRP 官方压缩包：
333da23d1b9009d7c01638e9ba38cf4600f7d37d393f854e96ee1396adefa9a6

frpc 二进制：
7d0270753bd171566a5389d2709fea29d2151f8fb4066ac20947e548e1da193a
```

不要在没有确认官方文件来源的情况下直接修改或绕过校验值。

---

## 4. 构建逻辑

`build.sh` 的核心步骤如下：

```sh
tar --owner=0 --group=0 --numeric-owner -czf package.tgz -C package .
MD5="$(md5sum package.tgz | awk '{print $1}')"
sed "s/^checksum=.*/checksum=\"$MD5\"/" INFO.in > INFO
tar --owner=0 --group=0 --numeric-owner -cf output.spk \
  INFO package.tgz scripts PACKAGE_ICON.PNG
```

外层 `.spk` 是未压缩 tar 归档，内部 `package.tgz` 是 gzip 压缩 tar 归档。

`INFO` 中的 `checksum` 是 `package.tgz` 的 MD5，不是整个 `.spk` 的校验值。

同一份源码在不同时间构建时，tar 时间戳可能造成最终 SHA-256 不同。当前脚本保证结构和属主信息正确，但没有实现完全可复现构建。

---

## 5. 构建前静态检查

### 5.1 Shell 语法

```sh
for f in build.sh build-offline.sh scripts/* package/bin/frpc-manager package/ui/*.cgi; do
  sh -n "$f" || exit 1
done
```

使用 ShellCheck：

```sh
shellcheck build.sh build-offline.sh scripts/* package/bin/frpc-manager package/ui/*.cgi
```

部分 DSM BusyBox 兼容写法可能触发风格类提示，应重点处理语法、未引用变量和不可移植命令错误。

### 5.2 DSM UI JSON

```sh
python3 -m json.tool package/ui/config >/dev/null
```

当前关键配置必须保持一致：

```text
INFO.in:
  dsmappname="SYNO.SDS.FRPCClient"

package/ui/config:
  键名：SYNO.SDS.FRPCClient
  appWindow：SYNO.SDS.FRPCClient
  url：/webman/3rdparty/frpc/index.html
```

`dsmappname`、JSON 应用标识和 `appWindow` 不一致时，DSM 主菜单可能打开“页面不存在”。

### 5.3 FRPC 二进制

```sh
file package/bin/frpc
readelf -h package/bin/frpc | grep -E 'Class|Machine'
./package/bin/frpc --version
sha256sum package/bin/frpc
```

预期结果：

```text
ELF 64-bit
Machine: Advanced Micro Devices X86-64
0.70.1
```

### 5.4 权限

```sh
chmod 755 build.sh build-offline.sh
chmod 755 scripts/*
chmod 755 package/bin/frpc package/bin/frpc-manager
chmod 755 package/ui/index.cgi package/ui/api.cgi
chmod 644 package/ui/index.html package/ui/config package/share/frpc.toml.example
```

ZIP 解压工具有时不会完整恢复 Unix 可执行位。构建前重新执行上述命令最稳妥。

---

## 6. 检查生成的 SPK

### 6.1 查看外层结构

```sh
tar -tf frpc-x86_64-0.70.1-6-ui-launcher-fix.spk
```

应至少包含：

```text
INFO
package.tgz
scripts/
PACKAGE_ICON.PNG
```

### 6.2 核对 `package.tgz` MD5

```sh
TMP="$(mktemp -d)"
tar -xf frpc-x86_64-0.70.1-6-ui-launcher-fix.spk -C "$TMP"
md5sum "$TMP/package.tgz"
grep '^checksum=' "$TMP/INFO"
rm -rf "$TMP"
```

两个值必须一致。

### 6.3 查看内部结构

```sh
tar -tzf package.tgz | sort
```

重点确认：

```text
./bin/frpc
./bin/frpc-manager
./share/frpc.toml.example
./ui/config
./ui/index.html
./ui/api.cgi
```

### 6.4 生成发布校验值

```sh
sha256sum frpc-x86_64-0.70.1-6-ui-launcher-fix.spk
```

---

## 7. DSM 安装与升级

在 DSM 6.2 套件中心：

1. 打开“设置”；
2. 将信任级别调整为允许安装未签名或任何发行者的套件；
3. 点击“手动安装”；
4. 选择生成的 `.spk`；
5. 安装或升级后启动套件；
6. 退出 DSM 并重新登录一次，以刷新主菜单缓存；
7. 从 DSM 主菜单打开“FRP Client”。

升级现有版本时不要先卸载，否则 `postuninst` 会删除：

```text
/var/packages/frpc/etc
/var/packages/frpc/var
```

正常原位升级由 `preupgrade` 和 `postupgrade` 保存并恢复 `frpc.toml` 与停用状态。

---

## 8. DSM 运行目录

安装后主要路径：

```text
/var/packages/frpc/target/                 套件程序目录
/var/packages/frpc/target/bin/frpc         官方 frpc
/var/packages/frpc/target/bin/frpc-manager 管理进程
/var/packages/frpc/target/ui/              DSM 管理界面
/var/packages/frpc/etc/frpc.toml            实际配置
/var/packages/frpc/etc/frpc.toml.bak        上一版配置备份
/var/packages/frpc/var/frpc.log             frpc 日志
/var/packages/frpc/var/manager.log          管理进程日志
/var/packages/frpc/var/frpc.pid             frpc PID
/var/packages/frpc/var/manager.pid          管理进程 PID
/var/packages/frpc/var/state                状态码
/var/packages/frpc/var/state.message        状态说明
/var/packages/frpc/var/control/             Web CGI 请求队列
/var/packages/frpc/var/responses/           管理进程响应队列
```

DSM UI 映射通常位于：

```text
/usr/syno/synoman/webman/3rdparty/frpc
```

页面直接访问地址：

```text
http://NAS地址:5000/webman/3rdparty/frpc/index.html
```

HTTPS 或自定义 DSM 端口时，替换协议和端口即可。

---

## 9. DSM 上的服务调试

通过 SSH 登录 NAS，切换 root：

```sh
sudo -i
```

### 9.1 套件状态和启停

```sh
synopkg status frpc
synopkg start frpc
synopkg stop frpc
synopkg restart frpc
```

直接调用套件脚本：

```sh
/var/packages/frpc/scripts/start-stop-status status
echo $?
/var/packages/frpc/scripts/start-stop-status log
```

状态退出码通常为：

```text
0  管理进程正在运行
1  PID 文件存在，但进程无效
3  套件未运行或 PID 文件不存在
```

### 9.2 进程检查

```sh
cat /var/packages/frpc/var/manager.pid
cat /var/packages/frpc/var/frpc.pid 2>/dev/null
ps | grep -E '[f]rpc|[f]rpc-manager'
```

DSM 6 的 `ps` 功能较少，也可以检查：

```sh
PID="$(cat /var/packages/frpc/var/manager.pid)"
tr '\0' ' ' < "/proc/$PID/cmdline"
```

### 9.3 日志

```sh
tail -n 200 /var/packages/frpc/var/manager.log
tail -n 200 /var/packages/frpc/var/frpc.log
grep -i frpc /var/log/messages | tail -n 100
```

安装或启动失败时还可检查：

```sh
cat /tmp/frpc-postinst.log 2>/dev/null
cat /tmp/frpc-service.log 2>/dev/null
```

DSM 可能通过 `SYNOPKG_TEMP_LOGFILE` 指定其他临时日志路径，因此也应查看套件中心弹出的错误文本和 `/var/log/messages`。

### 9.4 配置校验

```sh
/var/packages/frpc/target/bin/frpc verify \
  -c /var/packages/frpc/etc/frpc.toml
```

查看权限：

```sh
ls -ld /var/packages/frpc/etc
ls -l /var/packages/frpc/etc/frpc.toml
```

预期：

```text
/etc 目录：700
frpc.toml：root:root，600
```

### 9.5 状态文件

```sh
cat /var/packages/frpc/var/state
cat /var/packages/frpc/var/state.message
cat /var/packages/frpc/var/version
```

常见状态：

```text
running   frpc 正常运行
invalid   TOML 未填写完整或校验失败
disabled  用户在管理界面主动停止隧道
crashed   frpc 启动后立即退出
starting  管理进程正在启动
stopping  套件正在停止
stopped   套件已停止
```

---

## 10. Web 管理界面调试

### 10.1 主菜单点击后显示“页面不存在”

先直接访问：

```text
/webman/3rdparty/frpc/index.html
```

直接地址可访问但主菜单失败时，检查：

```sh
cat /var/packages/frpc/target/ui/config
cat /var/packages/frpc/INFO 2>/dev/null
ls -l /usr/syno/synoman/webman/3rdparty/frpc
```

必须确认：

```text
dsmuidir="ui"
dsmappname="SYNO.SDS.FRPCClient"
url="/webman/3rdparty/frpc/index.html"
appWindow="SYNO.SDS.FRPCClient"
```

升级后退出并重新登录 DSM，避免浏览器继续使用旧的桌面应用配置缓存。

### 10.2 页面能打开，但按钮无响应

浏览器按 `F12`，查看 Network 和 Console：

```text
/webman/3rdparty/frpc/api.cgi?action=status
/webman/3rdparty/frpc/api.cgi?action=load
```

然后在 NAS 检查：

```sh
synopkg status frpc
cat /var/packages/frpc/var/manager.log
ls -ld /var/packages/frpc/var/control /var/packages/frpc/var/responses
ls -l /var/packages/frpc/target/ui/api.cgi
```

预期：

```text
api.cgi 可执行
control 目录可由 DSM Web 用户写入
responses 目录可由 DSM Web 用户读取
frpc-manager 正在运行
```

安装脚本会根据 DSM 环境选择 `http` 或 `nobody` 作为 Web 用户，并以其主组设置队列权限。

### 10.3 HTTP 403

可能原因：

- DSM 登录会话已经失效；
- 当前用户不属于 `administrators`；
- `SynoToken` 不匹配；
- 通过反向代理访问时 Cookie、路径或请求头被改写。

处理：

1. 退出 DSM 后重新登录；
2. 使用管理员账号测试；
3. 先直接访问 NAS 的 DSM 端口，不经过反向代理；
4. 在浏览器 Network 中查看 `api.cgi` 的响应正文。

### 10.4 “管理进程响应超时”

CGI 已创建请求，但 `frpc-manager` 没有在 20 秒内写入响应。

检查：

```sh
ls -la /var/packages/frpc/var/control
ls -la /var/packages/frpc/var/responses
cat /var/packages/frpc/var/manager.pid
cat /var/packages/frpc/var/manager.log
```

可重启套件：

```sh
synopkg restart frpc
```

不要手工删除仍在处理的请求文件；确认管理进程已停止后，才可清理陈旧队列：

```sh
synopkg stop frpc
rm -f /var/packages/frpc/var/control/* /var/packages/frpc/var/responses/*
synopkg start frpc
```

---

## 11. 本地测试管理进程

`frpc-manager` 和 `start-stop-status` 支持两个环境变量，便于不安装 SPK 时测试：

```text
FRPC_PKGROOT       替代 /var/packages/frpc
SYNOPKG_PKGDEST    替代 /var/packages/frpc/target
```

在 Linux 构建机上：

```sh
TEST_ROOT=/tmp/frpc-spk-test
rm -rf "$TEST_ROOT"
mkdir -p "$TEST_ROOT/etc" "$TEST_ROOT/var"
cp package/share/frpc.toml.example "$TEST_ROOT/etc/frpc.toml"
chmod 600 "$TEST_ROOT/etc/frpc.toml"

FRPC_PKGROOT="$TEST_ROOT" \
SYNOPKG_PKGDEST="$PWD/package" \
./scripts/start-stop-status start

FRPC_PKGROOT="$TEST_ROOT" \
SYNOPKG_PKGDEST="$PWD/package" \
./scripts/start-stop-status status
echo $?

cat "$TEST_ROOT/var/state"
cat "$TEST_ROOT/var/state.message"
cat "$TEST_ROOT/var/manager.log"
```

模板仍含 `REPLACE_ME_` 时，预期管理进程运行，但状态为 `invalid`，`frpc` 子进程不会启动。

停止测试：

```sh
FRPC_PKGROOT="$TEST_ROOT" \
SYNOPKG_PKGDEST="$PWD/package" \
./scripts/start-stop-status stop
```

本地 Linux 无 DSM 的 `authenticate.cgi` 和 `login.cgi`，因此只能测试管理进程、配置校验和请求队列，不能完整测试 DSM Web 身份认证。

---

## 12. 手工测试请求队列

管理进程运行后，可以绕过 CGI，直接模拟操作。

读取配置：

```sh
TEST_ROOT=/tmp/frpc-spk-test
ID="$(date +%s).$$"
printf 'load\n' > "$TEST_ROOT/var/control/$ID.req.tmp"
mv "$TEST_ROOT/var/control/$ID.req.tmp" "$TEST_ROOT/var/control/$ID.req"

for i in $(seq 1 10); do
  [ -f "$TEST_ROOT/var/responses/$ID.resp" ] && break
  sleep 1
done
cat "$TEST_ROOT/var/responses/$ID.resp"
```

校验配置：

```sh
ID="$(date +%s).$$"
cp "$TEST_ROOT/etc/frpc.toml" "$TEST_ROOT/var/control/$ID.data"
printf 'verify\n' > "$TEST_ROOT/var/control/$ID.req.tmp"
mv "$TEST_ROOT/var/control/$ID.req.tmp" "$TEST_ROOT/var/control/$ID.req"

for i in $(seq 1 10); do
  [ -f "$TEST_ROOT/var/responses/$ID.resp" ] && break
  sleep 1
done
cat "$TEST_ROOT/var/responses/$ID.resp"
```

响应第一行是：

```text
OK
```

或：

```text
ERROR
```

后续内容是配置、状态或错误说明。

---

## 13. 修改 FRP 版本

例如升级到新的 FRP 版本时，需要同时调整以下位置：

1. `INFO.in`：

```ini
version="新版本-套件修订号"
```

2. `scripts/postinst`：

```sh
EXPECTED_VERSION="新版本"
```

3. `build-offline.sh`：

```sh
VER="新版本"
EXPECTED_ARCHIVE_SHA256="新官方压缩包 SHA-256"
EXPECTED_FRPC_SHA256="新 frpc 二进制 SHA-256"
```

4. `build.sh` 默认输出文件名；
5. `build-offline.sh` 调用 `build.sh` 时的输出文件名；
6. `README.md` 和本文档中的版本说明；
7. 必要时检查新版本 TOML 语法和 `frpc verify -c` 命令是否仍兼容。

计算校验值：

```sh
sha256sum frp_新版本_linux_amd64.tar.gz
TMP="$(mktemp -d)"
tar -xzf frp_新版本_linux_amd64.tar.gz -C "$TMP"
find "$TMP" -type f -name frpc -exec sha256sum {} \;
rm -rf "$TMP"
```

更新后至少执行：

```sh
./package/bin/frpc --version
./package/bin/frpc verify -c package/share/frpc.toml.example
./build-offline.sh
```

示例模板包含占位符，因此 `verify` 可能通过语法检查，但管理进程仍会因为存在 `REPLACE_ME_` 而拒绝启动隧道，这是预期行为。

---

## 14. 修改套件版本但不修改 FRP

只修复 DSM 脚本或界面时，可保持 FRP 为 `0.70.1`，只增加 SPK 修订号，例如：

```text
0.70.1-6 → 0.70.1-7
```

同步修改：

- `INFO.in` 的 `version`；
- `build.sh` 默认输出文件名；
- `build-offline.sh` 输出文件名；
- README 和发布文件名。

`package/bin/frpc` 及其 SHA-256 不需要改变。

---

## 15. 常见构建错误

### `Missing executable package/bin/frpc`

原因：二进制不存在或没有可执行权限。

```sh
chmod 755 package/bin/frpc
./build-offline.sh
```

### `FRP archive SHA-256 mismatch`

原因：下载文件不完整、版本不一致，或文件不是官方原始发布包。

```sh
sha256sum frp_0.70.1_linux_amd64.tar.gz
```

不要直接关闭校验。先重新下载或确认版本。

### `frpc binary SHA-256 mismatch`

压缩包内容与预期二进制不一致。确认压缩包版本、架构和来源。

### `tar: unrecognized option '--owner=0'`

当前使用的是 BSD tar 或精简 tar。改用 GNU tar、WSL2 或 Linux。

### DSM 提示 `package is not supported on the platform`

检查：

```ini
arch="x86_64"
os_min_ver="6.2-00000"
os_max_ver="6.2-99999"
```

NAS 必须是 x86-64 且 DSM 为 6.2。ARM、DSM 7 或其他架构不能直接使用当前包。

### 安装后配置未保留

必须以升级方式安装，不要先卸载。检查：

```sh
ls -l /var/packages/frpc/etc/frpc.toml
ls -l /tmp/frpc-upgrade 2>/dev/null
```

---

## 16. 安全注意事项

- 不要把实际 Token、服务器密码或私钥写入公开源码包；
- `/var/packages/frpc/etc/frpc.toml` 应保持 `root:root`、`600`；
- 管理页面只允许 DSM 管理员操作；
- 不要把 `api.cgi` 改为无需认证的接口；
- 不要让 `control` 和 `responses` 目录对所有用户开放；
- 发布前检查源码目录中是否残留真实配置：

```sh
grep -RInE 'token|password|secret|serverAddr' . \
  --exclude='frpc.toml.example' \
  --exclude='BUILD_AND_DEBUG.md'
```

人工确认搜索结果，避免误删代码中的字段名。

---

## 17. 发布前检查清单

```text
[ ] INFO.in 中的版本、架构和 DSM 范围正确
[ ] dsmappname 与 package/ui/config 完全一致
[ ] UI URL 是 /webman/3rdparty/frpc/index.html
[ ] Shell 脚本全部通过 sh -n
[ ] package/ui/config 通过 JSON 校验
[ ] frpc 是 x86-64 ELF，版本正确
[ ] 官方压缩包和 frpc SHA-256 正确
[ ] build-offline.sh 构建成功
[ ] INFO checksum 与 package.tgz MD5 一致
[ ] SPK 外层和 package.tgz 内层结构正确
[ ] DSM 原位升级后配置仍保留
[ ] DSM 主菜单可以直接打开管理界面
[ ] 读取、校验、保存、保存并重启、启动、停止均正常
[ ] frpc.toml 权限保持 600
[ ] 源码包中没有真实 Token 或服务器凭据
[ ] 为最终 SPK 和源码 ZIP 生成 SHA-256
```

---

## 18. 当前版本已验证的关键修复

`0.70.1-6` 相比早期版本，关键修复是 DSM 主菜单启动项：

```json
{
  ".url": {
    "SYNO.SDS.FRPCClient": {
      "type": "legacy",
      "title": "FRP Client",
      "icon": "images/frpc_{0}.png",
      "appWindow": "SYNO.SDS.FRPCClient",
      "allowMultiInstance": false,
      "width": 1040,
      "height": 760,
      "url": "/webman/3rdparty/frpc/index.html",
      "allUsers": false
    }
  }
}
```

直接地址可访问但主菜单点击显示“页面不存在”时，重点检查 `appWindow`、根路径 URL 和 `dsmappname` 三者，而不是重复修改 Web 页面本身。
