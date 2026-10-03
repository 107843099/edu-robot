# VerdureLab 外壳与结构资源 详细资料

这是一组适配不同开源硬件的外壳与装饰资源，适合为后续产品和课程建立造型参考库。应按具体目录找到对应的电路和固件。

[返回项目总览](<../00_%E9%A1%B9%E7%9B%AE%E6%80%BB%E8%A7%88.md>) · [配套生态与代码导读](<%E9%85%8D%E5%A5%97%E7%94%9F%E6%80%81%E4%B8%8E%E4%BB%A3%E7%A0%81%E5%AF%BC%E8%AF%BB.md>) · [逐仓阅读记录](<%E4%BB%93%E5%BA%93%E9%98%85%E8%AF%BB%E8%AE%B0%E5%BD%95.md>) · [来源与固定版本](<%E6%9D%A5%E6%BA%90%E4%B8%8E%E7%89%88%E6%9C%AC.json>)

## 已核对的硬件与能力

提供 STL、多份 Fusion 360 f3z 原始模型及局部装配资料，包含 EMO、鸭子和移动底盘外壳等。EMO V2 说明兼容 OttoRobot 主板，并有按钮、耳部和脚间距调整。

对话和控制配套现状：外壳仓对应多个设备与对话仓库，需要按造型选择一条技术链。

VerdureLab 提供造型；VerdiBot 通过 Assistant API 对话；BuddyRover 用小智语音板经 UART 指挥 C3 底盘。

## 外观参考

![VerdureLab EMO V2 实物示例  来源为该子目录说明](<%E5%9B%BE%E7%89%87/%E5%8F%82%E8%80%83%E5%9B%BE.jpg>)

VerdureLab EMO V2 实物示例  来源为该子目录说明。原图出处见下方来源，图片作为研究资料留档，不能从代码许可推定照片与角色的独立授权。

## 外观代码与产品思路借鉴

以下为面向后续自研与课程的分析建议。

- 外观：让面罩、耳部、配色和按键造型可替换，形成多个角色；保留原创造型与自己的视觉语言。
- 结构：利用原始 CAD 学习分件、安装柱、屏幕保护和 USB 接口位置，比只观察成品照片更有开发价值。
- 课程：让学生在固定内部尺寸下改变一个结构或交互细节，形成有约束的设计任务。

## 本地资料组成

| 仓库入口 | 配套角色 | 分支 | 固定提交 |
|---|---|---|---|
| [GreenShadeZhang/xiaozhi-sharp](<%E4%BB%93%E5%BA%93/GreenShadeZhang__xiaozhi-sharp>) | Verdure Assistant 引用的 CSharp 小智客户端 | `main` | `051fe36c62d6` |
| [maker-community/PiWiFiAP](<%E4%BB%93%E5%BA%93/maker-community__PiWiFiAP>) | 树莓派配网配套 | `master` | `64b820f72d52` |
| [maker-community/VerdiBot](<%E4%BB%93%E5%BA%93/maker-community__VerdiBot>) | 同组织树莓派桌面机器人 | `main` | `b85e25099cd8` |
| [maker-community/Verdure.Assistant](<%E4%BB%93%E5%BA%93/maker-community__Verdure.Assistant>) | VerdiBot 对话软件 | `master` | `98a8bcbc927b` |
| [maker-community/VerdureBuddyRover](<%E4%BB%93%E5%BA%93/maker-community__VerdureBuddyRover>) | 同组织移动底盘 | `main` | `cf1c772dcc85` |
| [maker-community/VerdureLab](<%E4%BB%93%E5%BA%93/maker-community__VerdureLab>) | 主项目结构资源 | `main` | `bcc1859dd35e` |
| [maker-community/taishanpi-3m-rk3576-dotnet-iot](<%E4%BB%93%E5%BA%93/maker-community__taishanpi-3m-rk3576-dotnet-iot>) | VerdureLab 关联的泰山派设备控制 | `main` | `2b434fcfbddd` |
| [maker-community/xiaozhi-esp32](<%E4%BB%93%E5%BA%93/maker-community__xiaozhi-esp32>) | 移动底盘配套语音固件的正确分支 | `verdure-buddy-rover` | `caf40bbba420` |

## 开发试验建议

选一个与现有硬件接近的模型，先测屏幕和主板安装尺寸，再做自己的外壳修改与一轮试装。

桌面版可先评估 VerdiBot 加 Assistant；移动版选 Rover 两板链路。统一行为接口与角色资产，再在原创外壳上调整显示、线束、散热与维护口。

## 已知限制和待补资料

壳体变化会影响重心、关节活动、音频开孔和检修。可打印不代表与新主板兼容；整个仓库也不对应同一主控或一套运动固件。

源码存在、说明中的功能、作者的测试和本次真机验证是不同状态。本次完成资料核查和静态阅读，未编译固件、训练模型或测试实物。

## 许可记录

根目录 MIT；README 明确模型商用须注明作者出处。保留许可、版权与署名，并分别判断第三方角色与标识的使用范围。

每个配套仓库单独保留许可证，具体文件、模型、音色和素材声明优先。各仓库阅读记录提供原许可文件入口。

## 原始来源

- [项目](https://github.com/maker-community/VerdureLab)
- [EMO V2 与图片来源](https://github.com/maker-community/VerdureLab/blob/main/verdure-emo-v2/README.md)
- [许可](https://github.com/maker-community/VerdureLab/blob/main/LICENSE)

整理日期为 2026-10-02 香港时间。源码版本以本夹来源与版本记录为准，作者历史成本不是当前香港交付预算。

## 可复用能力索引

表情、动作、库与真实调用入口已另存能力库；原环境和移植要求分别记录。

- [M15 VerdureBuddyRover 双电机差速与 LED情绪](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/02_%E5%8A%A8%E4%BD%9C%E4%B8%8E%E8%BF%90%E5%8A%A8/M15_VerdureBuddyRover%20%E5%8F%8C%E7%94%B5%E6%9C%BA%E5%B7%AE%E9%80%9F%E4%B8%8E%20LED%E6%83%85%E7%BB%AA.md>)
- [C07 Rover UART 命令、ACK 与异步状态](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/04_%E9%80%9A%E4%BF%A1%E4%B8%8E%E5%B7%A5%E5%85%B7%E8%B0%83%E7%94%A8/C07_Rover%20UART%20%E5%91%BD%E4%BB%A4%E3%80%81ACK%20%E4%B8%8E%E5%BC%82%E6%AD%A5%E7%8A%B6%E6%80%81.md>)
- [A04 Verdure 外壳与能力来源分层](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/05_%E5%AA%92%E4%BD%93%E4%B8%8E%E8%B5%84%E6%BA%90/A04_Verdure%20%E5%A4%96%E5%A3%B3%E4%B8%8E%E8%83%BD%E5%8A%9B%E6%9D%A5%E6%BA%90%E5%88%86%E5%B1%82.md>)

[库与版本](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E5%BA%93%E4%B8%8E%E4%BE%9D%E8%B5%96%E6%B8%85%E5%8D%95.md>) · [调用示例与移植路线](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
