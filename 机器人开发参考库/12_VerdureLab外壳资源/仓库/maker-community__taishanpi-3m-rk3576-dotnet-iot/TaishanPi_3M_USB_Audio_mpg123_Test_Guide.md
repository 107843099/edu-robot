# 泰山派 3M RK3576 USB 音频与 mpg123 播放测试指南

本文档记录在 LCKFB 泰山派 3M RK3576 上使用 USB 音频板进行播放、录音、音量上限保护和 `mpg123` 播放测试的实测结果。重点是避免 USB 语音板、功放或喇叭在高音量、满幅音频、直通硬件播放时过载。

## 1. 已验证的环境

```text
Board: LCKFB TaishanPi 3M RK3576
OS: Debian GNU/Linux 12 (bookworm)
Kernel: Linux 6.1.99
Architecture: arm64 / aarch64
USB audio: Burr-Brown from TI USB audio CODEC / PCM2912A Audio Codec
Audio server: PipeWire + pipewire-pulse
Player: mpg123 1.31.2
```

当前 USB 声卡在 ALSA 中识别为：

```text
card 3: CODEC [USB audio CODEC], device 0: USB Audio [USB Audio]
```

PipeWire 默认输出节点为：

```text
PCM2912A Audio Codec Analog Stereo
```

本次最终配置后，PipeWire 默认播放和默认录音都指向 USB 声卡：

```text
Default Audio/Sink:
alsa_output.usb-Burr-Brown_from_TI_USB_audio_CODEC-00.analog-stereo

Default Audio/Source:
alsa_input.usb-Burr-Brown_from_TI_USB_audio_CODEC-00.mono-fallback
```

## 2. 包源和 DNS 修复记录

最初执行 `apt-get update` 时卡在多个源连接阶段：

```text
mirrors.tuna.tsinghua.edu.cn
security.debian.org
packages.microsoft.com
pkgs.tailscale.com
```

排查发现 IP 网络可通，但 DNS 解析超时。`/etc/resolv.conf` 被 Tailscale 接管，指向：

```text
nameserver 100.100.100.100
nameserver fd7a:115c:a1e0::53
```

处理方式：保留 Tailscale 连接，但关闭它接管系统 DNS。

```bash
sudo cp -a /etc/resolv.conf /etc/resolv.conf.bak.$(date +%Y%m%d%H%M%S)
sudo tailscale set --accept-dns=false
printf 'nameserver 223.5.5.5\nnameserver 119.29.29.29\nnameserver 8.8.8.8\n' | sudo tee /etc/resolv.conf >/dev/null
```

同时将 Debian security 源切到清华镜像，以避免 `security.debian.org` 访问慢导致完整更新卡住：

```bash
sudo cp -a /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d%H%M%S)
sudo sed -i 's#https://security.debian.org/debian-security#https://mirrors.tuna.tsinghua.edu.cn/debian-security#g' /etc/apt/sources.list
sudo apt-get update
```

当前已验证可用的主要源：

```text
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib
deb https://packages.microsoft.com/debian/12/prod bookworm main
deb https://pkgs.tailscale.com/stable/debian bookworm main
```

说明：`tailscale set --accept-dns=false` 不会关闭 Tailscale 组网，只是不再让 Tailscale 覆盖系统 DNS。MagicDNS 和 Tailnet 搜索域可能不再自动生效。

## 3. 安装 mpg123

```bash
sudo apt-get update
sudo apt-get install -y mpg123
mpg123 --version
```

实测安装结果：

```text
mpg123 1.31.2
```

安装时自动拉取的依赖包括：

```text
libaudio2
libout123-0
libportaudio2
libsyn123-0
mpg123
```

## 4. 声卡和音量检查命令

查看播放设备：

```bash
aplay -l
aplay -L
cat /proc/asound/cards
```

查看 PipeWire 状态：

```bash
wpctl status
wpctl get-volume @DEFAULT_AUDIO_SINK@
```

查看 USB 声卡硬件 mixer：

```bash
amixer -c CODEC
amixer -c CODEC get Speaker
amixer -c CODEC get Mic
```

本次 USB 声卡播放能力：

```text
Playback:
  Format: S16_LE
  Channels: 1 or 2
  Rates: 8000, 11025, 16000, 22050, 32000, 44100, 48000
```

录音能力：

```text
Capture:
  Format: S16_LE
  Channels: 1
  Rates: 8000, 11025, 16000, 22050, 32000, 44100, 48000
```

### 4.1 设置 USB 声卡为默认播放和录音设备

先查看当前 PipeWire 设备 ID：

```bash
wpctl status
```

本次实测中 USB 播放和录音节点显示为：

```text
Sinks:
* 77. PCM2912A Audio Codec Analog Stereo

Sources:
* 78. PCM2912A Audio Codec Mono
```

注意：`77`、`78` 这类数字 ID 会在 PipeWire / WirePlumber 重启后变化，不要写死到脚本里。更持久的是下面的节点名：

```text
alsa_output.usb-Burr-Brown_from_TI_USB_audio_CODEC-00.analog-stereo
alsa_input.usb-Burr-Brown_from_TI_USB_audio_CODEC-00.mono-fallback
```

临时或当前会话设置默认设备，可以使用当前 `wpctl status` 里看到的 ID：

```bash
wpctl set-default <USB_SINK_ID>
wpctl set-default <USB_SOURCE_ID>
```

例如本次会话中：

```bash
wpctl set-default 77
wpctl set-default 78
```

设置后用下面命令确认默认节点名已经写入：

```bash
wpctl status | sed -n '/Default Configured Node Names/,+6p'
```

期望看到：

```text
0. Audio/Sink    alsa_output.usb-Burr-Brown_from_TI_USB_audio_CODEC-00.analog-stereo
1. Audio/Source  alsa_input.usb-Burr-Brown_from_TI_USB_audio_CODEC-00.mono-fallback
```

最终确认当前活动默认设备，星号应在 USB 声卡上：

```bash
wpctl status | sed -n '/Audio/,/Video/p'
```

期望类似：

```text
Sinks:
* PCM2912A Audio Codec Analog Stereo

Sources:
* PCM2912A Audio Codec Mono
```

如果只看到 `Dummy Output`，说明 PipeWire / WirePlumber 刚重启后还没有完成 ALSA 设备枚举，可以稍等几秒再运行：

```bash
wpctl status
```

如果仍未恢复，可检查内核层 ALSA 设备和 WirePlumber 日志：

```bash
cat /proc/asound/cards
journalctl --user -u wireplumber -u pipewire -u pipewire-pulse --no-pager -n 120
```

本次遇到过重启音频栈后短暂只显示 Dummy Output 的情况，随后设备重新枚举恢复。恢复后需要确认音量保护服务仍在运行：

```bash
systemctl --user is-active audio-volume-guard.service
```

## 5. 音量上限保护服务

为了防止 UI、程序或命令把音量拉得过高，本次配置了用户级 systemd 守护服务。它会循环检查 PipeWire 默认输出和 USB 声卡 `Speaker` mixer，超过上限就自动压回。

文件路径：

```text
/home/lckfb/.local/bin/audio-volume-guard.sh
/home/lckfb/.config/systemd/user/audio-volume-guard.service
```

当前实测上限最后设置为 `90%`：

```text
Environment=CAP_PERCENT=90
PipeWire Volume: 0.74
USB Speaker: 89%
audio-volume-guard.service: active
```

注意：ALSA 硬件音量是离散档位，设置 `90%` 时显示 `89%` 属于正常取整。

修改上限示例：

```bash
sed -i 's/Environment=CAP_PERCENT=.*/Environment=CAP_PERCENT=80/' ~/.config/systemd/user/audio-volume-guard.service
systemctl --user daemon-reload
systemctl --user restart audio-volume-guard.service
wpctl set-volume @DEFAULT_AUDIO_SINK@ 80%
amixer -c CODEC set Speaker 80% unmute
alsactl store 2>/dev/null || true
```

查看服务状态：

```bash
systemctl --user status audio-volume-guard.service
systemctl --user is-enabled audio-volume-guard.service
systemctl --user is-active audio-volume-guard.service
loginctl show-user lckfb -p Linger
```

本次已启用用户 linger，使服务在用户服务中常驻：

```bash
sudo loginctl enable-linger lckfb
```

## 6. 播放测试结果

### 6.1 speaker-test

```bash
timeout 3 speaker-test -D default -t sine -f 1000 -c 2
```

结果：默认输出链路可播放 1kHz 测试音，播放后音量保护仍生效。

### 6.2 mpg123 播放 MP3

测试文件：

```text
/home/lckfb/test.mp3
```

文件信息：

```text
8.8M
MPEG layer III
320 kbps
44.1 kHz
Joint Stereo
```

短播放：

```bash
timeout 8 mpg123 -q /home/lckfb/test.mp3
```

长播放：

```bash
timeout 300 mpg123 -q /home/lckfb/test.mp3
```

实测结果：

```text
mpg123 playback: ok
60% / 70% / 80% / 90% 上限下均可播放
90% 上限下播放约 5 分钟，播放结束后音量保护仍 active
```

## 7. 录音和回放测试

### 7.1 不推荐的旧录音状态

旧命令：

```bash
arecord -D hw:3,0 -f S16_LE -r 44100 -c 1 -d 5 ./recording.wav
aplay -D hw:3,0 ./recording.wav
```

旧录音文件统计：

```text
Maximum amplitude:  0.997009
Minimum amplitude: -1.000000
RMS amplitude:      0.299226
```

这说明录音已经接近或达到满幅，可能存在削波。再用 `aplay -D hw:3,0` 直通硬件播放时，更容易给 USB 音频板、功放或喇叭带来冲击。

### 7.2 推荐的安全录音参数

先降低 USB Mic 采集增益：

```bash
amixer -c CODEC set Mic Capture 60%
amixer -c CODEC get Mic
```

实测对应：

```text
Capture 25 [60%] [13.00dB] [on]
```

推荐用 `plughw` 录音：

```bash
arecord -D plughw:3,0 -f S16_LE -r 44100 -c 1 -d 20 /home/lckfb/recording_long.wav
```

当 PipeWire 默认 Source 已经切到 USB 声卡后，也可以直接使用默认设备录音：

```bash
arecord -D default -f S16_LE -r 44100 -c 1 -d 5 /home/lckfb/default_usb_recording.wav
```

本次验证 `arecord -D default` 可成功录制，且默认 Source 已配置为：

```text
alsa_input.usb-Burr-Brown_from_TI_USB_audio_CODEC-00.mono-fallback
```

新录音统计：

```text
Length:             20 seconds
Maximum amplitude:  0.116791
Minimum amplitude: -0.096466
RMS amplitude:      0.018692
Volume adjustment:  8.562
```

这段录音没有削波，余量明显更安全。

### 7.3 推荐播放命令

优先使用默认输出，让播放经过 PipeWire 和音量保护链路：

```bash
aplay -D default /home/lckfb/recording_long.wav
```

如果必须指定 USB 声卡，使用 `plughw`：

```bash
aplay -D plughw:3,0 /home/lckfb/recording_long.wav
```

尽量避免日常测试使用：

```bash
aplay -D hw:3,0 ./recording.wav
```

原因：`hw:3,0` 是直通硬件设备，会绕过 PipeWire 的软件混音、音量、重采样和格式转换。它不是不能用，但配合满幅 WAV 或高硬件音量时风险更高。

## 8. 常用命令速查

安装播放工具：

```bash
sudo apt-get update
sudo apt-get install -y mpg123
```

播放 MP3：

```bash
mpg123 -q /home/lckfb/test.mp3
timeout 60 mpg123 -q /home/lckfb/test.mp3
```

录制 20 秒单声道 WAV：

```bash
amixer -c CODEC set Mic Capture 60%
arecord -D default -f S16_LE -r 44100 -c 1 -d 20 /home/lckfb/recording_long.wav
arecord -D plughw:3,0 -f S16_LE -r 44100 -c 1 -d 20 /home/lckfb/recording_long.wav
```

设置并确认 USB 声卡默认输入/输出：

```bash
wpctl status
wpctl set-default <USB_SINK_ID>
wpctl set-default <USB_SOURCE_ID>
wpctl status | sed -n '/Default Configured Node Names/,+6p'
wpctl status | sed -n '/Audio/,/Video/p'
```

检查 WAV 峰值：

```bash
sox /home/lckfb/recording_long.wav -n stat
```

播放 WAV：

```bash
aplay -D default /home/lckfb/recording_long.wav
aplay -D plughw:3,0 /home/lckfb/recording_long.wav
```

查看是否有残留播放进程：

```bash
pgrep -a mpg123 || true
pgrep -a aplay || true
```

查看音量：

```bash
wpctl get-volume @DEFAULT_AUDIO_SINK@
amixer -c CODEC get Speaker
```

## 9. 注意事项

- 软件音量上限可以降低风险，但不能替代硬件过流、过温、喇叭阻抗匹配和功放增益限制。
- 录音时如果 `Maximum amplitude` 接近 `1.0` 或 `Minimum amplitude` 接近 `-1.0`，说明录音过满，建议降低 `Mic Capture`。
- MP3 音源本身可能已经被压缩到接近满幅。测试高音量时建议阶梯式从 60%、70%、80%、90% 逐步上调。
- `aplay -D default` 更适合日常测试；`aplay -D plughw:3,0` 适合指定 USB 声卡；`aplay -D hw:3,0` 只建议用于明确需要硬件直通的低风险测试。
- 当前已将 PipeWire 默认播放和默认录音都切到 USB 声卡，因此使用 `aplay -D default` / `arecord -D default` 会走 USB 音频板。若重启或重新插拔 USB 声卡后异常，先用 `wpctl status` 确认星号是否仍在 `PCM2912A Audio Codec` 上。
- 如果出现破音、USB 断连、板子发热、电源掉压或播放卡死，应立刻停止播放并降低音量上限。
