@echo off
chcp 65001 >nul
title 测试服务器状态

echo ===============================================
echo       正在检测服务器状态...
echo ===============================================
echo.

:: 测试健康检查
echo [1/5] 健康检查:
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8888/health' -UseBasicParsing; $d = $r.Content | ConvertFrom-Json; Write-Host \"  ✅ 状态: $($d.status)  |  歌曲数: $($d.songs_count)\" } catch { Write-Host '  ❌ 连接失败，请先启动 start_server.bat' }"

echo.
echo [2/5] 搜索测试:
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8888/api/search?keyword=周杰伦' -UseBasicParsing; $d = $r.Content | ConvertFrom-Json; Write-Host \"  📀 搜索 '周杰伦' 结果: $($d.total) 首\" } catch { Write-Host '  ❌ 搜索失败' }"

echo.
echo [3/5] 曲库统计:
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8888/api/stats' -UseBasicParsing; $d = $r.Content | ConvertFrom-Json; Write-Host \"  📊 共 $($d.data.total) 首歌曲, $($d.data.artists) 位歌手\" } catch { $null }"

echo.
echo [4/5] 歌曲列表:
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8888/api/list?page_size=5' -UseBasicParsing; $d = $r.Content | ConvertFrom-Json; foreach($s in $d.data) { Write-Host \"  🎵 $($s.artist) - $($s.title)  [ID: $($s.id)]\" } if($d.total -gt 5) { Write-Host \"  ... 还有 $($d.total-5) 首\" } } catch { $null }"

echo.
echo [5/5] 播放测试:
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8888/api/list?page_size=1' -UseBasicParsing; $d = $r.Content | ConvertFrom-Json; if($d.data.length -gt 0) { $id = $d.data[0].id; $r2 = Invoke-WebRequest -Uri \"http://localhost:8888/api/play/$id\" -UseBasicParsing; $size = $r2.RawContentLength/1024; Write-Host \"  ✅ 播放接口正常 (文件 $size KB)\" } else { Write-Host '  ⚠️ 曲库为空，请放入MP3文件' } } catch { Write-Host '  ❌ 播放测试失败' }"

echo.
echo ===============================================
echo  测试完毕
echo  服务器地址: http://localhost:8888
echo ===============================================
echo.
pause