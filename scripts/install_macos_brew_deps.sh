#!/usr/bin/env bash
set -e

echo "==> 安装 pygit2 所需的系统依赖 (libgit2, pkg-config)"
brew install libgit2 pkg-config

cat <<'NOTE'
==> 额外提示
若需要使用音频闪避功能，请安装虚拟音频驱动 BlackHole 2ch:
  https://github.com/ExistentialAudio/BlackHole
安装后可在 系统设置 -> 声音 -> 输出 / 输入 中将 BlackHole 2ch
设为默认或多声道聚合设备，再启动一条龙。
NOTE