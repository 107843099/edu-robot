@echo off
chcp 65001 >nul
title 停止音乐服务器

echo ===============================================
echo       正在停止本地音乐服务器...
echo ===============================================
echo.

:: 查找并结束占用 8888 端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8888') do (
    if not "%%a"=="" (
        taskkill /f /pid %%a >nul 2>&1
        if %errorlevel% equ 0 (
            echo [完成] 已停止端口 8888 上的进程 (PID: %%a)
        ) else (
            echo [信息] 无法自动停止进程 (PID: %%a)
        )
    )
)

:: 也尝试直接结束 python.exe（更稳妥）
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [完成] 已停止所有 Python 进程
)

echo.
echo 服务器已停止。
echo 可以重新双击 start_server.bat 启动
echo.

pause