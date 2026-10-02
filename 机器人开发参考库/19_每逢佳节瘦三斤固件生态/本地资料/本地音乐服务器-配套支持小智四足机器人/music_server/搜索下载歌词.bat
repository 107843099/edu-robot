@echo off
chcp 65001 >nul
cd /d "%~dp0"
set /p keyword=请输入歌手名或歌曲关键字: 
echo.
echo ==================================================
echo  下载包含 "%keyword%" 的歌词
echo ==================================================
echo.
python download_lyrics.py --keyword "%keyword%"
pause