#!/bin/sh
AUTH_CGI="/usr/syno/synoman/webman/modules/authenticate.cgi"
SELF_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)"

printf 'Content-Type: text/html; charset=UTF-8\r\n'
printf 'Cache-Control: no-store\r\n\r\n'

if [ -x "$AUTH_CGI" ]; then
    AUTH_USER="$($AUTH_CGI 2>/dev/null | tr -d '\r\n')"
    if [ -z "$AUTH_USER" ]; then
        printf '%s\n' '<!doctype html><meta charset="utf-8"><title>FRP Client</title><p>DSM 登录状态无效，请重新登录。</p>'
        exit 0
    fi
fi

if [ -r "$SELF_DIR/index.html" ]; then
    cat "$SELF_DIR/index.html"
else
    printf '%s\n' '<!doctype html><meta charset="utf-8"><title>FRP Client</title><p>管理界面文件缺失，请重新安装套件。</p>'
fi
