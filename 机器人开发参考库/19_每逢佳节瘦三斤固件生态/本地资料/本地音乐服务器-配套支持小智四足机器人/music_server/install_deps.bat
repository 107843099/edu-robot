@echo off
chcp 65001 >nul
title 安装依赖

echo 正在安装本地音乐服务器所需依赖...
echo.
pip install -r "%~dp0requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/

if %errorlevel% equ 0 (
    echo.
    echo 依赖安装成功！
    echo 现在可以双击 start_server.bat 启动服务器了
) else (
    echo.
    echo 安装失败，请检查网络后重试
)

pause