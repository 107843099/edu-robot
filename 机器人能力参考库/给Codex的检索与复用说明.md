# 给Codex的检索与复用说明

当用户提出“眨眼”“点头”“语音控制”“做一个四足步态”等需求时，先进入本目录，定位已经归档的实现，再确定新增开发范围。

1. 读`需求查找表.md`或解析`能力索引.json`的`capabilities`数组。按tags、project_ids、dependencies筛选，先匹配目标主控、显示/执行器和语言。不同平台同名API不能互换。
2. 打开候选的`document`，检查reuse_status、hardware、invocation和limitations。`reference_only`不含完整可调用实现；`portable_component`仍需要显示/舵机/网络适配。
3. 读取`sources[].path`的完整函数及调用链。line_start/line_end只定位符号附近；上游URL固定提交。git_blob标识旧快照原字节，sha256_utf8标识解码后的UTF-8文本；GBK文件不能拿这两个哈希混比。
4. 从`库与依赖清单.json`核对原声明与新增参考版本。`new_reference_snapshot`不证明原机器人使用相同版本。软件、动画、CAD和模型的许可分开核对，保持原LICENSE/NOTICE。
5. 从`表情动作预设清单.json`选择真实枚举或注册名，确认大小写、单位、持续时间、调度、中断和完成方式。特别看I07：stop、回中、保持、释放PWM、制动不是同一动作。
6. 选择最小提取范围：完整独立组件优先；原工程函数需带状态/配置/资源；跨硬件先替换驱动。不要修改研究快照，独立开发工程中记录来源和改动。
7. 使用`调用示例与移植路线.md`作为接入片段参考。示例不是通用SDK，Needle示例schema中的机器人函数需要真实dispatcher；ElectronPlayer.SetPose是空实现，不可选择。
8. 验证目标工程编译、主机算法/协议或实体行为，并把实际范围写回文档；静态来源/符号校验不能升级成“真机可用”。需要新增行为时更新卡片、JSON、依赖、预设和项目对照。

## 机器读取示例

```python
import json
from pathlib import Path

catalog = json.loads(Path("机器人能力参考库/能力索引.json").read_text())
candidates = [c for c in catalog["capabilities"]
              if c["reuse_status"] != "reference_only"
              and any("眨眼" in tag for tag in c["tags"])]
for c in candidates:
    print(c["id"], c["hardware"], c["document"])
```

运行位置为仓库根目录。它只检索JSON，不运行上游代码、烧录或驱动机器人。全文查找可以用`rg`，随后只读取候选源码，避免在大规模vendor/模型目录里无目的搜索。

## 当前明确的复用边界

|需求|已有基础|需要新增的部分|
|---|---|---|
|纸壳OLED表情|RoboEyes/Tiny独立组件/GFX驱动|目标I2C、尺寸、事件选择|
|纸壳点头摇头|ESP32Servo、MindPaw振荡、Tiny平滑结构|两通道映射、校准、软限位、停止|
|给芝麻加对话|同作者电脑语音桥与HTTP固件|目标设备配置；新传输需要适配|
|自然语言找动作|Needle schema/complete|有限dispatcher、真实固件接口和结果回报|
|四足/六足运动|姿势表、振荡器、IK/队列、策略契约|目标机械几何/标定；策略可能要重训|
|作者BIN换表情|外部材料与版本说明|完整可维护固件源码尚未提供|

原19项目主仓和配套阅读资料仍以`机器人开发参考库/`为入口。本库覆盖精选可复用实现，不宣称枚举了75仓全部功能或逆向恢复所有二进制。
