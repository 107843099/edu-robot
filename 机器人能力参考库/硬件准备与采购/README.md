# 硬件准备与采购：A/B分类、原项目来源与适配

按用户现有材料准备纸壳第一版，同时兼顾其他19项机器人与配套技术。A类是通用开发及当前桌面首版必需，已有的无需重复买；B类是选定某项扩展后才必需。B类内部的替代方案不应全部采购。数量是单台试验起点，不是完整制造BOM。来源导航重整：2026-10-11；库存证据仍为2026-10-03用户说明。

原GitHub链接指向已归档的固定提交；本地纸壳/小坦克/作者包标注本地来源，未知GitHub不虚构。表中“原配置依据”和“本库建议”分列；厂商规格、工具与供电余量不当作机器人作者的原BOM。

[现有物料与待确认](<现有物料与待确认.json>) · [采购分类机器索引](<采购分类索引.json>) · [19项目硬件增量表](<项目硬件增量表.md>) · [表情与动作复用](<../调用示例与移植路线.md>)。


## 已有材料

用户确认：ESP32-S3 N16R8是带USB接口和排针的开发板；有面包板、四针0.96屏、HC-SR04、SG90/MG90舵机、PCA9685及五号电池盒。屏幕驱动未知，电池盒节数/电池化学体系和舵机数量待确认。TTP223、MPU6050、BMI160属于准备买，不能计为已经持有。

四针屏先核对GND/VCC/SCL/SDA丝印。I²C地址扫描可确认设备响应，但0x3C/0x3D不能独立证明是SSD1306还是SH1106；先核对型号，再选择驱动和128×64或128×32尺寸。现有S3不用为通用开发再换C3；原C3二进制不能直接用于S3。

## A类：当前必需，缺什么补什么

| ID | 物品/条件 | 一台首版所需 | 当前处理 | 原项目/本地来源与建议边界 |
|---|---|---|---|---|
| A01 | 稳定、匹配电压的供电 | 两只微型舵机先以5V、约3A适配器作为台架试验起点；更多电机重新预算 | 只有五号电池盒，输出和负载能力未确认；优先补稳定电源，已有符合规格适配器可复用 | [Tiny供电说明](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/docs/hardware/power.md)的5V舵机/3.3V逻辑分供；[纸壳本地指南/BOM](<../../机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>)原12V进多路输出。**建议：**两微型舵机5V约3A台架起点属本库建议，不是原统一BOM；按同时负载测压降 |
| A02 | USB数据线 | 1根，与开发板和电脑接口匹配 | 有则不买；用于下载和日志 | [芝麻BOM](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/hardware/bom/README.md)和[纸壳本地指南/BOM](<../../机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>)均列数据线。**建议：**已有能传数据且接口匹配的线就不买 |
| A03 | 接线及供电分配 | 公公/公母/母母杜邦线、合适电源线、匹配端子/接头、活动轴所需舵机延长线 | 核对库存；舵机大电流优先走电源线及端子 | [芝麻BOM](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/hardware/bom/README.md)列电源线/排针；[纸壳本地指南/BOM](<../../机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>)列杜邦线。**建议：**按实物端子、线长、活动轴布置选择，不照搬任一线材数量 |
| A04 | 舵机电源开关 | 1个，额定电流覆盖实际负载 | 切断舵机供电；不同于软件停止或回中 | [芝麻BOM](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/hardware/bom/README.md)列船型开关。**建议：**按台架负载匹配开关额定电流，用于切断舵机供电 |
| A05 | 触摸输入 | TTP223 1个，按住有效、松开恢复；铜箔及可靠连接 | 为摸头回应采购；主控原生触摸也可实现，但属于另一实现路线 | [纸壳本地指南/BOM](<../../机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>)原TTP223+导电铜箔。**建议：**原摸头输入可借鉴；S3原生触摸是另一实现，不冒充原代码 |
| A06 | 两轴定位机构 | 2只位置式舵机，配套舵盘、中心螺丝、双轴连接/固定件 | 已有舵机，先确认数量、是否连续旋转款、尺寸和安装负载；支架可按纸壳自制 | [纸壳本地指南/BOM](<../../机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>)原双SG90；[Tiny引脚/五轴表](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/docs/hardware/pinout.md)原五轴中头/颈占0/1。**建议：**已有位置式舵机先盘点；提取[Tiny舵机源码](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/hardware/servo_wrapper.cpp)到两轴时改通道、范围与校准 |
| A07 | 主控和显示 | S3开发板1块、兼容屏1块 | 已有，不重复买；确认屏驱动、板型、针脚及工作电压 | [AlbertMicro源码](https://github.com/thinking0things/AlbertMicro/blob/8d0ae147e967c798469a551c1dc49da781fc5587/AlbertMicro.ino)原S3/SH1106/RoboEyes；[芝麻BOM](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/hardware/bom/README.md)原SSD1306。**建议：**现有屏先识别驱动，原项目同为0.96寸不证明兼容 |
| A08 | 绝缘与固定 | 绝缘胶带/热缩管、可拆固定、扎带或线束标签 | 核对库存；面包板先试验，洞洞板/固定接头用于后续装配 | [芝麻BOM](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/hardware/bom/README.md)列热缩等；[纸壳本地指南/BOM](<../../机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>)列纸板固定材料。**建议：**工具/可拆固定方案由实际装配决定，不是各项目统一必买 |

5V/3A是两微型舵机首版的工程建议，不是所有项目的统一额定值或已经验证的结论。电源电流能力按同时工作的负载、启动/堵转电流、线束和压降核对。[PCA9685供电与电流说明](https://learn.adafruit.com/16-channel-pwm-servo-driver/hooking-it-up)

调试接法：开发板通过电脑USB供电；外部5V接PCA9685的V+和舵机电源，PCA9685逻辑VCC用3.3V，所有GND共地。外部5V暂不并接开发板5V脚；独立运行时再按实际板卡的电源路径接线。[3.3V主控连接示例](https://learn.adafruit.com/adafruit-16-channel-servo-driver-with-raspberry-pi/hooking-it-up) · [官方DevKitC-1电源选项](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html)。官方板示例不能代替未知第三方板的原理图。

上述5V/3A台架选择、下文电阻分压组合及工具清单属于工程建议；[Tiny供电说明](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/docs/hardware/power.md)提供原项目分供原理，不能直接当作未知S3开发板的电源原理图。

建议备件/工具另列，不将它们伪装成每台机器人必装模块：万用表；470–1000µF、耐压至少10V电解电容作为舵机供电试验备件；电阻包；按钮；洞洞板和排针。电容容量须按压降测试调整，不能补偿不足的电源。选已焊排针模块可减少初期焊接；未焊模块需要焊接工具。

## 五号电池盒的实际含义

五号描述电池尺寸，不等于固定5V电源。下表按常见串联电池盒计算标称值；新电池、满充、负载和放电过程中的实际电压会变化。

| 电池组合 | 标称总电压 | 对本次准备的影响 |
|---|---:|---|
| 2节普通碱性 | 3V | 不是直接供两舵机的5V源 |
| 3节普通碱性 | 4.5V | 没有稳定5V，电池衰减/负载压降需测 |
| 4节普通碱性 | 6V | 不能当5V接开发板；舵机是否接受须按实际型号核对 |
| 4节1.2V镍氢 | 4.8V | 可考虑匹配舵机的电池试验，不能推定是稳定5V或能带任意数量舵机 |

标称值依据[碱性AA资料](https://data.energizer.com/pdfs/e91.pdf)、[镍氢AA资料](https://data.energizer.com/pdfs/nh15-2300.pdf)。最终续航不能仅由mAh计算，还受负载电流、放电曲线、转换效率和电池盒接触电阻影响。

如需电池独立运行，选B06；确认节数与电池类型后，再选择降压、升压或升降压模块，核对整个输入电压范围和实际持续/瞬态电流。先保留电池盒，不把未知规格记为“供电已齐”。

## B类：选功能后才必需

| ID/功能 | 何时必须 | 要补的材料 | 替代或限制 | 原项目/本地来源与建议边界 |
|---|---|---|---|---|
| B01 机器人自身语音输入/输出 | 要让机器人自身听与说 | 兼容I²S麦克风模块，例如INMP441；I²S功放，例如MAX98357A；匹配喇叭，例如4Ω/3W；接线 | 若语音运行在电脑、机器人只接动作/表情，则可先复用电脑音频，不一定购机器人音频模块；先匹配小智板级配置 | [小智面包板配置](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/boards/bread-compact-wifi/config.h)有I²S配置；[Tiny引脚/五轴表](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/docs/hardware/pinout.md)有MAX98357A音效；[芝麻电脑对话配套](https://github.com/dorianborian/sesame-companion-app/blob/86f82c137b9954445f55d249c966e8f9984bd87b/sesame_companion.py)用电脑音频。**建议：**INMP441+MAX98357A是候选建议，config未独立证明麦克风型号；喇叭按功放匹配，Tiny主仓无完整对话 |
| B02 倾斜、摇晃、拿起回应 | 要检测自身运动 | MPU6050或BMI160模块1块，选择有资料及驱动的一种 | 两者均含加速度计和陀螺仪，不要按“角度+角速度”拆成两种必需；姿态估计仍需算法，不能替代关节角度反馈 | [XGO硬件说明](https://github.com/LuwuDynamics/xgoduck_hardware/blob/703bfd274071cb545b1ed6f512f3c81cf91e447b/readme.md)原QMI8658A六轴IMU。**建议：**MPU6050/BMI160是本库倾斜/摇晃扩展候选，择一；不作为XGO原配或关节角度反馈 |
| B03 接近/左右输入 | 要检测外部靠近或左右遮挡 | 已有HC-SR04可先用，需Echo分压；原纸壳左右互动可用2个合适的红外避障模块；缩小结构可选ToF模块 | 单个距离值不提供左右方向或身份；寻线模块不能凭名字当作远距离避障模块。相同功能选一条方案试验 | [纸壳本地指南/BOM](<../../机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>)原两个LM393类型红外数字OUT；[Adafruit HC-SR04](https://learn.adafruit.com/distance-measurement-ultrasound-hcsr04/connect-the-sensor)为超声波接口依据。**建议：**HC/ToF为改版候选；单个距离不能代替原左右输入，寻线模块不能自动当避障 |
| B04 移动底盘 | 要做Rover、小坦克或小车 | 两个匹配减速电机、轮子/履带、底盘、双H桥模块及匹配电源；按原项目选择DRV8833或TB6612FNG | PCA9685产生控制信号，不提供直流电机所需H桥功率驱动；需要轮速反馈时增加编码器和读数程序 | [Rover电机固件](https://github.com/maker-community/VerdureBuddyRover/blob/cf1c772dcc854ae5c19699eebb3970e1c3f64f34/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino)原DRV8833；[小坦克本地BOM](<../../机器人开发参考库/18_桌面小坦克/物料与复刻路线.md>)原TB6612FNG与双3V/150比N20。**建议：**先选一种底盘；PCA不能直接驱动直流电机，电机电压/电流与接口匹配 |
| B05 更多关节/专用平台 | 要做机器狗、Otto、芝麻、六足或高级机型 | 按项目增量表补齐舵机数量、通道、专用板、关节件、负载电源和线束 | 同为舵机不代表机械/协议互换；不能先把18只SG90视为六足通用BOM | [芝麻BOM](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/hardware/bom/README.md)8轴；[NodeHexa硬件说明](https://github.com/ViolinLee/NodeHexa/blob/ba844a107de8dbb95bba51c2d5e870928d72cbd9/README.md)六足18轴；[XGO硬件说明](https://github.com/LuwuDynamics/xgoduck_hardware/blob/703bfd274071cb545b1ed6f512f3c81cf91e447b/readme.md)15串行轴。**建议：**完整复刻再按BOM补执行器/机构/驱动；不把SG90数量等同任意关节需求 |
| B06 电池独立运行 | 要脱离台架电源 | 已确认的电池组/电池盒、匹配稳压/转换和开关、必要的电压监测；可充电方案配匹配充电设备 | AA镍氢与锂电充电方案不同；完整充电+保护+转换方案按化学体系确定，不只买一个充电板 | [芝麻BOM](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/hardware/bom/README.md)按硬件版本配电池与稳压；[纸壳本地指南/BOM](<../../机器人开发参考库/15_小纸壳机器人/物料接线与机构拆解.md>)原适配器多路输出。**建议：**AA电池盒需先核对节数/类型/电压，不自动搭配锂电充电模块 |
| B07 彩屏/视觉等表现扩展 | 要采用圆屏彩色角色或相机视觉 | 彩屏及对应接口/驱动；若做视觉，选摄像头及与S3匹配的接口板/连接器 | 现有单色OLED足以验证基础表情；普通S3开发板不一定自带摄像头插座。视觉是建议扩展，不是19个项目共同标配 | [EMO-Dot配置](https://github.com/M-D-777/EMO-Dot/blob/25884f58f25d9d931ca3dbf9d5c18221d9ae237c/README.md)原1.28寸屏；[小智S3CAM说明](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/boards/bread-compact-wifi-s3cam/README.md)原OV2640/特定板卡。**建议：**彩屏与视觉分选；普通S3开发板不等于S3CAM板，接口、引脚和驱动需另适配 |

B01依据[I²S麦克风资料](https://invensense.tdk.com/wp-content/uploads/2015/02/INMP441.pdf)、[MAX98357A功放说明](https://www.adafruit.com/product/3006)。B02依据[MPU6050](https://learn.adafruit.com/mpu6050-6-dof-accelerometer-and-gyro?view=all)、[BMI160资料](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi160-ds000.pdf)。B03依据[HC-SR04电平说明](https://learn.adafruit.com/distance-measurement-ultrasound-hcsr04/connect-the-sensor)、[ToF资料](https://www.st.com/resource/datasheet/vl53l0x.pdf)；HC-SR04常见Echo为5V，需要转换后接S3，电阻分压可用Echo→2.2kΩ→GPIO节点、GPIO节点→3.3kΩ→GND，5V名义降至约3.0V。实际以模块型号和测量为准。

B04的电机驱动范围见[DRV8833资料](https://www.ti.com/product/DRV8833)及[小坦克物料](<../../机器人开发参考库/18_桌面小坦克/物料与复刻路线.md>)。驱动板实际持续电流、散热和电机堵转电流一起核对；DRV8833和TB6612不是随意互换的原固件接口。

## 当前采购顺序与Codex使用规则

先盘点A类，补稳定供电、摸头输入和缺少的接线/固定件，完成单屏和单舵机试验；然后按目标增加B01语音或B02运动输入。移动/四足/六足按一条机械路线采购，而不是把所有项目的材料相加。备用舵机按选定机型同型号补，数量不与原型必需数量混记。

Codex读取现有物料JSON，再按需求选择采购索引中的condition和项目增量；unknown/null表示待确认，不能自动当“缺少”或“已满足”。不得仅根据0.96、MG90、AA电池盒等商品泛称自动选驱动、限位、供电或充电电路。硬件建议尚未实物验收，原源码复用入口仍以能力卡为准。

## 查来源再开发

[项目来源与复用JSON](<../项目来源与复用索引.json>)记录19项及76份快照；采购JSON的source_refs指向source_registry，条目分别保存original_context和recommendation。B组project_ids包含可考虑扩展的项目，不表示它们原BOM都装有候选器件。四轴设计与通用双轴首版继续分别按各自方案验收。
