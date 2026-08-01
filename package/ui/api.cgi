#!/bin/sh
set -u

PKGNAME="frpc"
PKGROOT="${FRPC_PKGROOT:-/var/packages/$PKGNAME}"
VAR_DIR="$PKGROOT/var"
CONTROL_DIR="$VAR_DIR/control"
RESPONSE_DIR="$VAR_DIR/responses"
LOGFILE="$VAR_DIR/frpc.log"
STATE_FILE="$VAR_DIR/state"
MESSAGE_FILE="$VAR_DIR/state.message"
VERSION_FILE="$VAR_DIR/version"
AUTH_CGI="/usr/syno/synoman/webman/modules/authenticate.cgi"
LOGIN_CGI="/usr/syno/synoman/webman/login.cgi"
MAX_BODY=1048576

header_text() {
    printf 'Content-Type: text/plain; charset=UTF-8\r\n'
    printf 'Cache-Control: no-store\r\n\r\n'
}

fail_http() {
    code="$1"
    text="$2"
    printf 'Status: %s\r\n' "$code"
    header_text
    printf '%s\n' "$text"
    exit 0
}

url_param() {
    key="$1"
    printf '%s' "${QUERY_STRING:-}" | tr '&' '\n' | sed -n "s/^${key}=//p" | head -n 1
}

AUTH_USER=""
if [ -x "$AUTH_CGI" ]; then
    AUTH_USER="$($AUTH_CGI 2>/dev/null | tr -d '\r\n' || true)"
fi
[ -n "$AUTH_USER" ] || fail_http '403 Forbidden' 'DSM 登录状态无效。'

is_admin=0
[ "$AUTH_USER" = "admin" ] && is_admin=1
if [ "$is_admin" -eq 0 ]; then
    groups="$(id -Gn "$AUTH_USER" 2>/dev/null || true)"
    printf '%s\n' "$groups" | tr ' ' '\n' | grep -qx 'administrators' && is_admin=1
fi
if [ "$is_admin" -eq 0 ] && [ -x /usr/syno/sbin/synogroup ]; then
    /usr/syno/sbin/synogroup --get administrators 2>/dev/null | grep -F "$AUTH_USER" >/dev/null 2>&1 && is_admin=1
fi
[ "$is_admin" -eq 1 ] || fail_http '403 Forbidden' '仅 DSM 管理员可以修改 FRP 配置。'

provided_token="${HTTP_X_SYNO_TOKEN:-$(url_param SynoToken)}"
if [ -x "$LOGIN_CGI" ]; then
    login_json="$($LOGIN_CGI 2>/dev/null || true)"
    expected_token="$(printf '%s' "$login_json" | sed -n 's/.*"SynoToken"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
    if [ -n "$expected_token" ] && [ "$provided_token" != "$expected_token" ]; then
        fail_http '403 Forbidden' 'SynoToken 校验失败。'
    fi
fi

action="$(url_param action)"

submit_request() {
    req_action="$1"
    with_body="${2:-no}"
    stamp="$(date +%s)"
    id="$stamp.$$"
    req="$CONTROL_DIR/$id.req"
    data="$CONTROL_DIR/$id.data"
    resp="$RESPONSE_DIR/$id.resp"

    [ -d "$CONTROL_DIR" ] && [ -d "$RESPONSE_DIR" ] || {
        header_text
        printf 'ERROR\nFRP Client 管理进程尚未启动。\n'
        return
    }

    if [ "$with_body" = "yes" ]; then
        len="${CONTENT_LENGTH:-0}"
        case "$len" in
            ''|*[!0-9]*) len=0 ;;
        esac
        if [ "$len" -le 0 ] || [ "$len" -gt "$MAX_BODY" ]; then
            header_text
            printf 'ERROR\n配置内容为空或超过 1 MiB。\n'
            return
        fi
        umask 077
        dd bs=1 count="$len" of="$data.tmp" 2>/dev/null || {
            rm -f "$data.tmp"
            header_text
            printf 'ERROR\n读取配置内容失败。\n'
            return
        }
        mv -f "$data.tmp" "$data" || {
            rm -f "$data.tmp"
            header_text
            printf 'ERROR\n提交配置内容失败。\n'
            return
        }
    fi

    printf '%s\n' "$req_action" > "$req.tmp" || {
        rm -f "$data" "$req.tmp"
        header_text
        printf 'ERROR\n无法创建控制请求。\n'
        return
    }
    mv -f "$req.tmp" "$req"

    count=0
    while [ ! -f "$resp" ] && [ "$count" -lt 20 ]; do
        sleep 1
        count=$((count + 1))
    done
    header_text
    if [ -f "$resp" ]; then
        cat "$resp"
        rm -f "$resp"
    else
        rm -f "$req" "$data"
        printf 'ERROR\n管理进程响应超时。\n'
    fi
}

case "$action" in
    load)
        submit_request load no
        ;;
    verify)
        submit_request verify yes
        ;;
    save)
        submit_request save yes
        ;;
    save_restart)
        submit_request save_restart yes
        ;;
    start|stop|restart)
        submit_request "$action" no
        ;;
    status)
        header_text
        state="$(cat "$STATE_FILE" 2>/dev/null || echo unknown)"
        message="$(cat "$MESSAGE_FILE" 2>/dev/null || echo '无法读取运行状态。')"
        version="$(cat "$VERSION_FILE" 2>/dev/null || echo unknown)"
        printf 'state=%s\n' "$state"
        printf 'message=%s\n' "$message"
        printf 'version=%s\n' "$version"
        ;;
    log)
        header_text
        if [ -r "$LOGFILE" ]; then
            tail -n 200 "$LOGFILE" 2>/dev/null
        else
            printf '日志文件尚不存在或不可读。\n'
        fi
        ;;
    *)
        fail_http '400 Bad Request' '未知操作。'
        ;;
esac
