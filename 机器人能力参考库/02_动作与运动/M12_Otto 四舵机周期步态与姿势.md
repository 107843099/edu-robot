# M12 Otto 四舵机周期步态与姿势

复用等级：**可单独提取；需接入驱动**。硬件：Arduino Otto 四舵机构型。语言：C++。

关联项目：[09 Otto闪猫侠机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：两足、Otto、moonwalker、摆动、跳跃、振荡器。依赖：OttoDIYLib、Oscillator、Servo、EEPROM。

## 怎么实现

Otto 将四个舵机的振幅、中心偏移、周期和相位组织成步态。Oscillator 参数 A/O 是度，T 是毫秒，Ph 是弧度；walk/turn/moonwalker 等设置不同相位关系，并借 home 和 trim 标定支撑姿势。

## 如何调用

Otto 对象 init(YL,YR,RL,RR,load_calibration,Buzzer) 后调用 walk(steps,T,dir)、turn 等，签名见 Otto.h。matrix 嘴巴/音乐功能是额外依赖，不自动与 OLED 小智兼容。

## 移植与提取范围

复刻四舵机两足可沿原脚型/重心使用；加双臂应参考 M13 的6舵机分支。纸壳头部仅借振荡器概念，不能直接执行两足 gait。

## 限制与核对点

大量 Otto 上层动作会同步等待，必须评估语音并发。Oscillator 的源文件许可与项目/资源许可按各自声明保留；servo limiter 不代替机械限位。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [Otto.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/OttoDIY__OttoDIYLib/src/Otto.h>)：`void walk`，L55–L85。 [上游固定提交](https://github.com/OttoDIY/OttoDIYLib/blob/f384c00a641e11c8741487320c6f1d82ad72e6d5/src/Otto.h#L55-L85)；提交 `f384c00a641e11c8741487320c6f1d82ad72e6d5`。
- [Oscillator.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/OttoDIY__OttoDIYLib/src/Oscillator.h>)：`void SetPh`，L31–L61。 [上游固定提交](https://github.com/OttoDIY/OttoDIYLib/blob/f384c00a641e11c8741487320c6f1d82ad72e6d5/src/Oscillator.h#L31-L61)；提交 `f384c00a641e11c8741487320c6f1d82ad72e6d5`。
- [Otto.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/OttoDIY__OttoDIYLib/src/Otto.h>)：`void home`，L48–L78。 [上游固定提交](https://github.com/OttoDIY/OttoDIYLib/blob/f384c00a641e11c8741487320c6f1d82ad72e6d5/src/Otto.h#L48-L78)；提交 `f384c00a641e11c8741487320c6f1d82ad72e6d5`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
