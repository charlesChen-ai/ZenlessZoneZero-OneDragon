@echo off
rem 一条龙 Windows 开发环境启动脚本
rem 用途: 开发期迭代调试，等价于 debug.bat 但不申请管理员权限
uv run --env-file .env src\zzz_od\gui\app.py