============================================
  本地音乐服务器 - 供 ESP32 音乐播放使用
============================================

一、部署方式
--------------------------------------------
将MP3文件放入 music 文件夹即可。
支持目录结构：
    music/
      周杰伦 - 晴天.mp3          ← 直接放
      周杰伦 - 七里香.mp3
      林俊杰/
        江南.mp3                 ← 按歌手分目录
        美人鱼.mp3
      晴天.lrc                    ← 同名的LRC歌词文件（可选）


二、启动服务器
--------------------------------------------
双击  start_server.bat 一键启动！（推荐）

或手动启动：
    python server.py --port 8888

启动后访问 http://localhost:8888/health 测试


三、下载歌曲到曲库
--------------------------------------------
方式1：双击 download_music.py，输入关键词搜索下载
方式2：把下载好的MP3直接拖入 music 文件夹
方式3：从手机/电脑其他位置复制进来

新增歌曲后执行：
    curl -X POST http://localhost:8888/api/rescan
（或重启服务器自动扫描）


四、API 接口一览
--------------------------------------------
列出所有歌曲：
  http://localhost:8888/api/list

搜索歌曲：
  http://localhost:8888/api/search?keyword=周杰伦

获取歌曲详情：
  http://localhost:8888/api/song/{歌曲ID}

播放歌曲（返回MP3流，ESP32直接连这个地址）：
  http://localhost:8888/api/play/{歌曲ID}

获取LRC歌词：
  http://localhost:8888/api/lyrics/{歌曲ID}

重新扫描曲库：
  POST http://localhost:8888/api/rescan


五、ESP32 固件配置
--------------------------------------------
修改 e:\music\main\app\app_musicplayer.h 中的：
  #define MUSIC_SERVER_HOST "192.168.x.x"
改为你电脑的局域网IP

重新编译烧录固件后，对音箱说"播放xxx"即可


六、文件说明
--------------------------------------------
server.py              - 主服务器程序（FastAPI）
start_server.bat       - 一键启动脚本【双击运行】
install_deps.bat       - 安装依赖脚本（首次使用）
download_music.py      - 下载助手（搜索并下载歌曲）
requirements.txt        - Python依赖列表
music/                  - 放MP3文件的目录