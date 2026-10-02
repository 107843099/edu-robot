@echo off
chcp 65001 >nul
title 刷新曲库

echo ===============================================
echo       正在刷新曲库...
echo ===============================================
echo.

:: 发送POST请求触发重新扫描
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8888/api/rescan' -Method POST -UseBasicParsing; Write-Host $r.Content } catch { Write-Host '连接失败，请确保服务器已启动' }"

echo.
echo ===============================================
echo  完成后可访问 http://localhost:8888/api/list 查看
echo ===============================================
echo.
pause