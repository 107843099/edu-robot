@echo off
title 本地音乐服务器 - xiaozhi-esp32
chcp 65001 >nul

echo.
echo ===============================================
echo       正在启动本地音乐服务器...
echo ===============================================
echo.

:: 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python！
    echo 请先安装Python 3.8或更高版本: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

:: 检查并安装依赖
echo [1/3] 检查Python依赖...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 正在安装所需依赖（首次运行需要联网）...
    pip install -r "%~dp0requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/
    if %errorlevel% neq 0 (
        echo.
        echo [错误] 依赖安装失败！
        pause
        exit /b 1
    )
    echo [完成] 依赖安装完毕
) else (
    echo [完成] 依赖已就绪
)

:: 检查music目录
echo [2/3] 检查曲库目录...
if not exist "%~dp0music" (
    mkdir "%~dp0music"
    echo [信息] 已创建 music 目录
    echo [信息] 请将MP3文件放入 %~dp0music
)
echo [完成] 曲库目录已就绪

:: 启动服务器
echo [3/3] 启动服务器
echo.
echo ===============================================
echo  服务器启动后，访问以下地址测试：
echo   http://localhost:8888/health
echo ===============================================
echo.
echo  按 Ctrl+C 停止服务器
echo.

python "%~dp0server.py" --port 8888 --host 0.0.0.0

echo.
echo 服务器已停止。
pause