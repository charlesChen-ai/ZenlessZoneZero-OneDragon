#!/usr/bin/env bash
set -e

uname_s="$(uname -s)"
case "$uname_s" in
    Darwin)
        echo "==> macOS 开发环境启动"
        if [ -f .env ]; then
            echo "==> 加载 .env"
            set -a
            . ./.env
            set +a
        fi
        ;;
    Linux)
        echo "==> Linux 开发环境启动"
        if [ -f .env ]; then
            echo "==> 加载 .env"
            set -a
            . ./.env
            set +a
        fi
        ;;
    *)
        echo "不支持的操作系统: $uname_s" >&2
        exit 1
        ;;
esac

exec uv run src/zzz_od/gui/app.py