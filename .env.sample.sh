#!/bin/sh
# macOS / Linux 一条龙开发环境变量样例
# 用法: cp .env.sample.sh .env  然后  uv run --env-file .env ...
export PYTHONPATH="$(pwd)/src"
export ZZZ_OD_TEST="$(pwd)/zzz-od-test"