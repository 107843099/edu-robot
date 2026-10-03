# M17 XGO-Duck 61维观测与14维策略动作

复用等级：**需要移植或配套运行环境**。硬件：Linux主机＋XGO-Duck MCU/IMU/15电机。语言：Python。

关联项目：[13 XGO-Duck赛博鸭子](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/13_XGO-Duck%E8%B5%9B%E5%8D%9A%E9%B8%AD%E5%AD%90/README.md>)。

检索词：策略模型、ONNX、四足、头部、嘴巴、关节映射。依赖：NumPy、onnxruntime、rl_core、wire协议。

## 怎么实现

build_obs 将角速度、重力、关节偏移/速度、上一动作、移动指令和头部参数组成61维。Policy 用 ONNX 推理14维并过滤，action_to_deg 按 home 和关节 ID 映射回15电机；嘴巴是额外电机，不由14维策略直接生成。

## 如何调用

Policy.load(本地onnx) 检查模型维度；infer(...) 后 action_to_deg(action)。必须保持 MOTOR_IDS 与 POLICY_IDS 的实际次序，关节偏移/速度涉及度→弧度换算。嘴巴限制0..30°是原机器设定。

## 移植与提取范围

对未来策略机器人可借观测契约、状态过滤和控制来源分离。更换机械形态需要重训/适配策略，不是拿 ONNX 配一个新舵机列表就可走路。

## 限制与核对点

软件、模型、硬件许可分别记录，模型上游可能含非商业限制。50Hz策略/100Hz MCU 是设计配置，不是本次实测；不能把部署推理称为已训练可适配任何机器人。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [rl_core.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/13_XGO-Duck%E8%B5%9B%E5%8D%9A%E9%B8%AD%E5%AD%90/%E4%BB%93%E5%BA%93/LuwuDynamics__xgoduck_runtime_arduino/python/rl_core.py>)：`def build_obs`，L142–L165。 [上游固定提交](https://github.com/LuwuDynamics/xgoduck_runtime_arduino/blob/8cdbbd84710d856581982c9eaf0d5e2970666232/python/rl_core.py#L142-L165)；提交 `8cdbbd84710d856581982c9eaf0d5e2970666232`。
- [rl_core.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/13_XGO-Duck%E8%B5%9B%E5%8D%9A%E9%B8%AD%E5%AD%90/%E4%BB%93%E5%BA%93/LuwuDynamics__xgoduck_runtime_arduino/python/rl_core.py>)：`def action_to_deg`，L159–L165。 [上游固定提交](https://github.com/LuwuDynamics/xgoduck_runtime_arduino/blob/8cdbbd84710d856581982c9eaf0d5e2970666232/python/rl_core.py#L159-L165)；提交 `8cdbbd84710d856581982c9eaf0d5e2970666232`。
- [policy.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/13_XGO-Duck%E8%B5%9B%E5%8D%9A%E9%B8%AD%E5%AD%90/%E4%BB%93%E5%BA%93/LuwuDynamics__xgoduck_runtime_arduino/python/policy.py>)：`def infer`，L88–L118。 [上游固定提交](https://github.com/LuwuDynamics/xgoduck_runtime_arduino/blob/8cdbbd84710d856581982c9eaf0d5e2970666232/python/policy.py#L88-L118)；提交 `8cdbbd84710d856581982c9eaf0d5e2970666232`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
