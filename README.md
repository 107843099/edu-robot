# edu-robot：机器人研发与教学参考库

为后续机器人开发和AI创意造物课程整理的资料库，保存外观结构、硬件、固件、表情动作、工具和作者相关项目。**这里是整理与归档仓库，原作者及GitHub来源见下方总览。**

现有19个项目及配套技术档案，包含75个不同上游GitHub仓库的76份固定提交快照；另有本地纸壳、曼波、小坦克和作者固件资料。独立能力库包含52张能力卡、12组共202个预设、24项依赖记录；另外下载7套通用库、195个文件。Needle是配套软件，VerdureLab包含结构资源，19项并不全是可直接复刻的完整实体机器人。

## 从需求进入

| 想做什么 | 阅读入口 |
|---|---|
| 查来源、外观、构型和作者配套 | 本页总览 → 各项目README → 配套生态与代码导读 |
| 做纸板机器人的第一版 | [纸壳项目](<机器人开发参考库/15_小纸壳机器人/README.md>) · [制作与验收](<机器人开发参考库/15_小纸壳机器人/第一版制作与验收清单.md>) · [原接线与机构](<机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>) |
| 找表情、动作和已有库 | [能力库README](<机器人能力参考库/README.md>) · [需求查找表](<机器人能力参考库/需求查找表.md>) · [调用示例](<机器人能力参考库/调用示例与移植路线.md>) |
| 用现有材料确定采购 | [A/B清单与逐项来源](<机器人能力参考库/硬件准备与采购/README.md>) · [19项目硬件增量](<机器人能力参考库/硬件准备与采购/项目硬件增量表.md>) |
| 判断BIN、工具与可维护源码的区别 | [纸壳逆向分析](<机器人开发参考库/15_小纸壳机器人/逆向分析与自研迁移方案.md>) · [作者固件边界](<机器人开发参考库/19_每逢佳节瘦三斤固件生态/固件版本与接线边界.md>) |
| 让Codex按需求定位原实现 | [检索说明](<机器人能力参考库/给Codex的检索与复用说明.md>) · [能力JSON](<机器人能力参考库/能力索引.json>) · [项目来源JSON](<机器人能力参考库/项目来源与复用索引.json>) |
| 课程、学生平台和规划 | [产品与教学方案](<AI创意造物课程与学生平台｜产品与教学方案.md>) · [项目思维导图](<EDUHK-SRE机器人项目.xmind>) · [综合参考Word](<开源机器人项目参考与后续开发规划.docx>) |

## 项目来源总览

GitHub链接指向原作者或组织；项目名称链接进入本仓档案。表中配套是已归档的重点入口，完整作者/社区项目及依赖见各夹阅读记录和[76份快照清单](<机器人开发参考库/仓库下载清单.json>)。同作者的独立项目有参考价值，但不能仅凭作者相同认定已接入机器人。

| 项目档案 | 原项目与重点配套来源 | 可借鉴内容 | 复用边界 |
|---|---|---|---|
| [01 芝麻机器人](<机器人开发参考库/01_芝麻机器人/README.md>) | [dorianborian/sesame-robot](https://github.com/dorianborian/sesame-robot)<br>配套：[dorianborian/sesame-companion-app](https://github.com/dorianborian/sesame-companion-app)、[lukehollis/sesame-ml](https://github.com/lukehollis/sesame-ml) | 128×64表情、8舵机姿势序列、网页控制与电脑对话桥 | 原8轴；电脑承担语音。S3/现有屏可作移植基础，PCA输出另适配。 |
| [02 曼波小狗](<机器人开发参考库/02_曼波小狗/README.md>) | [RussellCooper-DJZ/manbo-robot-dog](https://github.com/RussellCooper-DJZ/manbo-robot-dog)<br>另有[Herobrine立创版本](https://oshwhub.com/herobrine/stm32-mambo-robot-dog)及本地包 | 四舵机动作任务、OLED图案、语音指令到动作编号 | GitHub/本地4轴与Herobrine立创5轴分开；STM32改S3需移植。 |
| [03 MindPaw机器狗](<机器人开发参考库/03_MindPaw机器狗/README.md>) | [ace-trump-tech/MindPaw](https://github.com/ace-trump-tech/MindPaw) | 表情、情绪参数、正弦动作和外部Agent网关分层 | 原ESP8266、4轴；有模型占位和模拟数据，进阶AI逐项验证。 |
| [04 Stack-chan桌面机器人](<机器人开发参考库/04_Stack-chan桌面机器人/README.md>) | [stack-chan/stack-chan](https://github.com/stack-chan/stack-chan)<br>配套：[stack-chan/m5stack-avatar](https://github.com/stack-chan/m5stack-avatar)、[robo8080/AI_StackChan2](https://github.com/robo8080/AI_StackChan2) | 双轴注视/点头、Avatar脸部、MOD与音频动作分工 | M5Stack的Moddable/Arduino路线不同；普通S3/OLED需驱动适配。 |
| [05 AlbertMicro机器小狗](<机器人开发参考库/05_AlbertMicro机器小狗/README.md>) | [thinking0things/AlbertMicro](https://github.com/thinking0things/AlbertMicro)<br>配套：[thinking0things/AlbertPro](https://github.com/thinking0things/AlbertPro) | RoboEyes眼睛、4轴摆腿、插值、BLE/串口控制 | 原S3/SH1106；先确认屏驱动，Pro是独立8轴训练路线。 |
| [06 NodeHexa六足机器人](<机器人开发参考库/06_NodeHexa六足机器人/README.md>) | [ViolinLee/NodeHexa](https://github.com/ViolinLee/NodeHexa)<br>配套：[ViolinLee/PiHexa18](https://github.com/ViolinLee/PiHexa18)、[SmallpTsai/hexapod-v2-7697](https://github.com/SmallpTsai/hexapod-v2-7697) | 腿部正逆运动学、校准、动作序列与Web/UART | 六足18轴，左右驱动板地址不同；同仓四足参数不共用。 |
| [07 RookiDroid六足机器人](<机器人开发参考库/07_RookiDroid六足机器人/README.md>) | [rookidroid/hexapod](https://github.com/rookidroid/hexapod)<br>配套：[rookidroid/hexapod-link](https://github.com/rookidroid/hexapod-link)、[rookidroid/remote-arcade](https://github.com/rookidroid/remote-arcade) | 18轴路径查表、UDP姿态串流、仿真和遥控 | 原双PCA9685；三机型的舵机、尺寸和电源分别选择。 |
| [08 小智语音机器人](<机器人开发参考库/08_小智语音机器人/README.md>) | [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32)<br>配套：[78/xiaozhi-assets-generator](https://github.com/78/xiaozhi-assets-generator)、[xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) | 听/说/待机状态、网络语音、表情资源和工具调用 | 多板型工程；音频/显示/GPIO按所选board配置，服务器另配。 |
| [09 Otto闪猫侠机器人](<机器人开发参考库/09_Otto闪猫侠机器人/README.md>) | [txp666/ottodiy-docs](https://github.com/txp666/ottodiy-docs)<br>配套：[OttoDIY/OttoDIYLib](https://github.com/OttoDIY/OttoDIYLib)、[txp666/xiaozhi-esp32](https://github.com/txp666/xiaozhi-esp32) | 四轴周期步态、六轴双臂版、GIF和教学文档 | 文档、动作库、小智固件不同仓；4/6轴版本分别采购。 |
| [10 EMO-Dot小豆机器人](<机器人开发参考库/10_EMO-Dot小豆机器人/README.md>) | [M-D-777/EMO-Dot](https://github.com/M-D-777/EMO-Dot)<br>配套：[M-D-777/xiaozhi-esp32](https://github.com/M-D-777/xiaozhi-esp32)、[M-D-777/esp32_s3_lvgl9_lottie_test](https://github.com/M-D-777/esp32_s3_lvgl9_lottie_test) | 圆屏角色、语音状态、独立S3 Lottie实验 | 主仓多为BIN/说明，源码在emo-dot分支；固定支脚不含行走。 |
| [11 ElectronBot类人桌面机器人](<机器人开发参考库/11_ElectronBot类人桌面机器人/README.md>) | [peng-zhihui/ElectronBot](https://github.com/peng-zhihui/ElectronBot)<br>配套：[jinsonli/ElectronBot-Voice](https://github.com/jinsonli/ElectronBot-Voice)、[maker-community/ElectronBot-Peripheral](https://github.com/maker-community/ElectronBot-Peripheral) | 6关节反馈、USB底层SDK、圆屏帧和上位机 | 原STM32F405/改造反馈舵机，SG90不能直接替代；SetPose为空实现。 |
| [12 VerdureLab外壳与配套](<机器人开发参考库/12_VerdureLab外壳资源/README.md>) | [maker-community/VerdureLab](https://github.com/maker-community/VerdureLab)<br>配套：[maker-community/VerdureBuddyRover](https://github.com/maker-community/VerdureBuddyRover)、[maker-community/VerdiBot](https://github.com/maker-community/VerdiBot) | 桌面壳体、Rover双电机差速、主机对话模块 | 壳体仓无统一电子BOM；Rover、VerdiBot与其语音板分路线。 |
| [13 XGO-Duck赛博鸭子](<机器人开发参考库/13_XGO-Duck赛博鸭子/README.md>) | [LuwuDynamics/xgoduck_hardware](https://github.com/LuwuDynamics/xgoduck_hardware)<br>配套：[LuwuDynamics/xgoduck_runtime_arduino](https://github.com/LuwuDynamics/xgoduck_runtime_arduino)、[LuwuDynamics/xgoduck_rl](https://github.com/LuwuDynamics/xgoduck_rl) | 头颈/嘴表达、串行舵机、IMU、训练与部署分层 | 原UNO Q、15个Feetech 1910、QMI8658A；PWM微型舵机不能直接替代。 |
| [14 Jumper螃蟹机器人](<机器人开发参考库/14_Jumper螃蟹机器人/README.md>) | [KingKongRobotics/jumper](https://github.com/KingKongRobotics/jumper)<br>配套：[KingKongRobotics/jumper-design](https://github.com/KingKongRobotics/jumper-design) | 22关节仿真、任务动作、策略布局契约、Rust状态机 | 原RK3576；真机部署有缺口，mesh不等于制造BOM。 |
| [15 小纸壳机器人](<机器人开发参考库/15_小纸壳机器人/README.md>) | 用户提供的Made_by_Z指南与V0.3 ZIP；**上游GitHub未确认** | 纸板双轴结构、摸头/双红外、Web Serial模块验收 | 本地DOCX/ZIP，缺完整设备端源码；C3 BIN不能直接刷S3。 |
| [16 Tiny Engineer桌面编程机器人](<机器人开发参考库/16_TinyEngineer桌面编程机器人/README.md>) | [jamro/tiny-engineer](https://github.com/jamro/tiny-engineer)<br>配套：[jamro/yova](https://github.com/jamro/yova)、[jamro/desk-hud](https://github.com/jamro/desk-hud) | 16种独立表情、5轴PCA平滑/限位、编程事件→状态 | 原C3/128×32，有MAX98357A音效输出，无完整对话；YOVA另适配。 |
| [17 Needle端侧意图模型](<机器人开发参考库/17_Needle端侧模型/README.md>) | [cactus-compute/needle](https://github.com/cactus-compute/needle)<br>配套：[cactus-compute/needle-environments](https://github.com/cactus-compute/needle-environments)、[cactus-compute/cactus](https://github.com/cactus-compute/cactus) | 有限工具schema、结构化参数、complete与run边界 | 主机/移动/边缘软件；当前资源不是S3 N16R8可直接部署的模型。 |
| [18 桌面小坦克](<机器人开发参考库/18_桌面小坦克/README.md>) | 用户提供的桌面小坦克包；**上游GitHub未确认** | 双轮混控、WebSocket、轨迹计时、命令超时停车 | 本地源码/BOM/PCB/3MF；原双3V N20/TB6612，公开上游GitHub未确认。 |
| [19 每逢佳节瘦三斤固件生态](<机器人开发参考库/19_每逢佳节瘦三斤固件生态/README.md>) | 用户提供的作者固件及音乐等配套包；**上游GitHub未确认** | C3/S3功能取舍、控制模式、音乐服务、结构供电 | 本地多款BIN与Python配套；GitHub未确认，小智主仓不等于这些BIN来源。 |

## 当前纸壳/S3首版：具体借自哪里

以下是基于现有材料提出的路线，**尚未在你的机器人上完成集成**。原设计、其他项目代码和本库适配建议分别列出。

| 要做的部分 | 来源项目与实现位置 | 原实现及首版采用方式 |
|---|---|---|
| 纸板外形、双轴、摸头 | [Made_by_Z本地指南与V0.3接线分析](<机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>) | 原C3、双SG90、SSD1306、TTP223/双红外；S3/PCA版重新配置程序，C3 BIN不能直接移用 |
| 参数化眼睛、眨眼与注视 | [thinking0things/AlbertMicro](https://github.com/thinking0things/AlbertMicro/blob/8d0ae147e967c798469a551c1dc49da781fc5587/AlbertMicro.ino)；[FluxGarage/RoboEyes](https://github.com/FluxGarage/RoboEyes) | Albert用RoboEyes驱动SH1106 128×64；确认自己的屏驱动再接入。[E01 RoboEyes 参数化眼睛、眨眼与注视](<机器人能力参考库/01_表情显示/E01_RoboEyes 参数化眼睛、眨眼与注视.md>) |
| 另一套现成位图表情 | [jamro/tiny-engineer](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/lib/TinyEngineerExpressions/src/TinyEngineerExpressions.h) | 独立16种、128×32、30帧/种；调整现有屏的显示区域。与RoboEyes可择一做初版。[E02 TinyEngineer 独立 16 种位图表情](<机器人能力参考库/01_表情显示/E02_TinyEngineer 独立 16 种位图表情.md>) |
| PCA双轴平滑、限位 | [jamro/tiny-engineer](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/hardware/servo_wrapper.cpp) | 原5轴通过PCA、校准映射和限速；提取头/颈两轴，重配通道和范围。[M20 TinyEngineer 舵机平滑、限位与释放输出](<机器人能力参考库/02_动作与运动/M20_TinyEngineer 舵机平滑、限位与释放输出.md>) |
| 直接GPIO舵机输出的替代路线 | [madhephaestus/ESP32Servo](https://github.com/madhephaestus/ESP32Servo)；[thinking0things/AlbertMicro](https://github.com/thinking0things/AlbertMicro/blob/8d0ae147e967c798469a551c1dc49da781fc5587/AlbertMicro.ino) | 原代码输出脉宽/角度；与PCA路线择一，不为两个方案重复采购。[M01 ESP32Servo 舵机角度与脉宽驱动](<机器人能力参考库/02_动作与运动/M01_ESP32Servo 舵机角度与脉宽驱动.md>) |
| 电脑对话后触发表情/动作 | [dorianborian/sesame-companion-app](https://github.com/dorianborian/sesame-companion-app/blob/86f82c137b9954445f55d249c966e8f9984bd87b/sesame_companion.py) | 电脑ASR/LLM/TTS经HTTP控制芝麻；给自研S3命令写适配，首版可复用电脑音频。[C02 芝麻同作者语音、LLM 与机器人桥接](<机器人能力参考库/04_通信与工具调用/C02_芝麻同作者语音、LLM 与机器人桥接.md>) |
| 后续机身收音与播音 | [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/boards/bread-compact-wifi/config.h)；[78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/application.cc) | 原板级I²S/显示与听说状态；选board并加兼容音频件，动作接口另适配。[I05 小智听、说、待机与 emotion 事件调度](<机器人能力参考库/03_交互状态与调度/I05_小智听、说、待机与 emotion 事件调度.md>) |
| 等待、思考、完成、错误联动 | [jamro/tiny-engineer](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/animation/registry.cpp) | 原状态名组合表情、关节和音效；映射课程任务，现有主仓没有Codex专用钩子。[I02 TinyEngineer 表情与动作状态注册表](<机器人能力参考库/03_交互状态与调度/I02_TinyEngineer 表情与动作状态注册表.md>) |

建议首版先验收“表情 → 单舵机 → 双轴 → 摸头联动”，再选电脑对话或机身语音。IMU、彩屏、摄像头和移动底盘按功能增加。这个顺序是本库开发建议，不是任何上游的完整复刻步骤。

## A/B采购怎么判断

库存来自你的文字说明：S3 N16R8带USB/排针开发板、面包板、四针0.96寸屏、SG90/MG90、PCA9685A、HC-SR04及五号电池盒。屏幕驱动/分辨率、舵机数量、电池盒节数/类型待确认；TTP223、MPU6050和BMI160是计划购买。

| 分类 | 当前判断 | 来源口径 |
|---|---|---|
| A：通用开发及当前桌面首版所需 | 稳定匹配供电、数据线、接线/分配、舵机电源开关、双轴定位件、摸头感应区；已有件先核对 | 双轴摸头来自本地纸壳指南；PCA与分供参考Tiny；工具和电源余量属于工程建议 |
| B：选功能后必需 | 自身语音、倾斜/摇晃、距离/左右接近、轮式底盘、更多关节、电池独立运行、彩屏/视觉 | 对应小智、XGO、VerdureRover等；具体型号和原配置见A/B README，替代方案不全部列成必买 |
| 待确认 | 五号电池盒不能直接当作稳定5V电源；舵机数量和位置式型号影响缺口 | [库存证据](<机器人能力参考库/硬件准备与采购/现有物料与待确认.json>)；unknown/null不等于缺少 |

基本点头摇头不要求IMU；MPU6050/BMI160可按倾斜/摇晃扩展先选一种。XGO-Duck原配QMI8658A，不能把另两款写成它的标配。静止桌宠无需为它买寻线模块；纸壳原双红外用于左右接近/遮挡输入。[完整清单与电气依据](<机器人能力参考库/硬件准备与采购/README.md>)。

## 来源记录怎么读

| 来源类型 | 标注方式 | 能证明什么 |
|---|---|---|
| GitHub原实现 | 原仓名、固定commit、文件/符号、必要时行段/哈希 | 归档版本确有实现，不自动证明新硬件可运行 |
| 作者/社区配套 | 独立仓名和角色；未集成的独立项目明确说明 | 可继续研究和适配，不视为现成插件 |
| 本地附件 | 原文件名、来源清单、SHA256和解压路径；GitHub未知写“未确认” | 收到的资料身份；上传本仓不改变原始来源 |
| 厂商资料 | 文档/数据手册链接 | 器件电气和接口规格，不是机器人作者BOM |
| 本库建议 | 原配置与“建议、需适配、待验证”分列 | 开发判断，不写成上游已实现或真机通过 |

实现文件、符号、固定提交和哈希见[能力索引](<机器人能力参考库/能力索引.json>)；配套版本见[项目来源索引](<机器人能力参考库/项目来源与复用索引.json>)及各夹来源记录；通用库见[依赖清单](<机器人能力参考库/库与依赖清单.md>)，新增参考版本不等于原机器人精确构建版本。

## 下载、使用与验证范围

每个文件夹保留README、配套导读、逐仓记录、来源版本和原始资料。修改时在独立开发工程提取组件，保留原LICENSE/NOTICE、固定版本和改动记录。代码、图片、CAD、模型和本地固件的许可分别判断，不能以一个主仓软件许可覆盖全部配套。

较大的CAD、模型、媒体与固件使用Git LFS：

```sh
git lfs install
git clone https://github.com/107843099/edu-robot.git
cd edu-robot
git lfs pull
```

GitHub默认ZIP可能只有LFS指针；文件以`version https://git-lfs.github.com/spec/v1`开头时需获取实际对象。[GitHub归档说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-git-lfs-objects-in-archives-of-your-repository)

已完成来源阅读、静态/逆向分析及文档注明的部分主机检查。本轮重整README与来源索引，未新增烧录、制造或真机验收。Tiny主机测试、Needle离线试验、纸壳假串口复核分别保留，不合并为“全部机器人验证通过”。Word是现有综合稿，本轮更新以README和索引为准。

公开材料保留原许可与已记录的脱敏；供应商采购/报价表不在发布范围。[资料库说明](<机器人开发参考库/README.md>) · [配套缺口](<机器人开发参考库/配套链接核查与缺口.md>) · [原能力校验](<机器人能力参考库/来源与校验记录.json>) · [本轮来源重整校验](<机器人能力参考库/README来源重整校验.json>)。

README重整于2026-10-11，香港时间。上游快照仍固定原下载版本，没有替换为最新分支。
