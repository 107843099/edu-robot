# MindPaw AI Infra：研究者路径

本目录是可选的 AI 基础设施实验场。初学者不需要启动它，直接按照 [MindPaw_main/README.md](../MindPaw_main/README.md) 复现 Demo 即可。

研究目标是探索资源受限机器人上的边缘-云 Agent 运行时：根据任务延迟、风险、电量、网络和隐私要求，在本地、Gateway 和云端之间选择执行位置。

```text
ESP8266 robot -> Edge Gateway -> local model / cloud LLM
       └──────── direct cloud mode remains available ────────┘
```

## 当前 MVP 能力

- OpenAI-compatible `POST /v1/chat/completions`
- 豆包/方舟、OpenAI-compatible、本地 Ollama 和 mock 上游
- Gateway Token 鉴权
- 上游超时和错误转换
- MindPaw 动作、表情、旋律 JSON Schema 的边界校验
- Docker 和本地 Python 启动
- **2.0 流式 3D 重建感知层** (`recon/`) —— 端到端 ~150 ms 避障延迟；详见 [recon/README.md](recon/README.md) 和 [Docs/09_Streaming_Recon.md](../Docs/09_Streaming_Recon.md)

当前 Gateway 是研究起点，不宣称已经完成完整的调度系统。后续扩展应围绕可测量的系统问题，而不是单纯增加 Provider 数量。

## 研究问题

建议围绕以下问题形成论文或实验报告：

> 在资源受限的机器人上，如何根据任务 SLO、能耗、网络、隐私和动作风险，动态选择本地、边缘或云端 Agent 执行位置？

推荐的三层执行模型：

| 层级 | 适合任务 | 目标 |
|------|---------|------|
| 设备本地 | 停止、前进、基础语音命令、简单手势 | 低延迟和安全 |
| Edge Gateway | 会话、路由、缓存、轻量模型 | 稳定和可控 |
| 云端模型 | 开放式聊天、复杂情绪理解 | 能力和泛化 |

可以将策略写成多目标优化：

```text
latency + energy + cloud_cost + privacy_exposure + action_risk
```

## 建议的实验路线

### 阶段 1：建立基线

比较以下策略：

1. ESP8266 直接访问云端。
2. 所有任务经过 Gateway。
3. 固定规则的本地/云端切换。
4. 只根据网络延迟切换。
5. 自适应策略。

记录真实的语音、手势、网页聊天和动作任务，不要只使用合成请求。

### 阶段 2：加入运行时机制

- 异步任务队列和 `request_id`。
- 设备/会话隔离。
- 网络状态和电量感知路由。
- 本地 fallback 和断网退化。
- 动作白名单与过期时间。
- 语义缓存和重复请求去重。
- 请求耗时、成本、Token 和失败率统计。

### 阶段 3：形成可复现实验

至少报告：

- P50/P95/P99 端到端延迟。
- 动作成功率和 JSON schema 失败率。
- 断网恢复时间。
- ESP8266、Gateway 和云端能耗。
- Token 消耗和单次任务成本。
- 不同丢包率、RTT、并发数下的表现。

建议保留 `experiments/` 目录，保存配置、网络轨迹、原始日志、绘图脚本和结果摘要。论文结果必须能用 Docker 和固定随机种子重新生成。

## 本地启动

```bash
cd ai-infra
cp .env.example .env
# 编辑 .env，至少设置 GATEWAY_TOKEN、AI_PROVIDER 和上游配置
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn gateway.app:app --host 0.0.0.0 --port 8000
```

没有云端 Key 时，设置 `AI_PROVIDER=mock`：

```bash
curl http://127.0.0.1:8000/healthz
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Authorization: Bearer test' \
  -H 'Content-Type: application/json' \
  -d '{"model":"mindpaw","messages":[{"role":"user","content":"你好"}]}'
```

也可以使用：

```bash
docker compose up --build -d
```

## 连接真实设备

网关主机需要和 MindPaw 的 STA 网络互通；`MindPaw` 热点只负责控制页面。

打开 `http://192.168.4.1/aiconfig.html`：

- `API Key`：填写网关的 `GATEWAY_TOKEN`。
- `推理端点 ID`：填写 `mindpaw` 或实验中的模型名。
- `AI Gateway 地址`：填写 `http://<网关IP>:8000/v1/chat/completions`。

将 Gateway 地址留空即可恢复 ESP8266 直连豆包模式。

## 代码入口

| 文件 | 作用 |
|------|------|
| `gateway/app.py` | Gateway API、鉴权、上游调用和响应校验 |
| `.env.example` | Provider、模型和安全配置模板 |
| `Dockerfile` | 可复现实验环境 |
| `docker-compose.yml` | 一键启动服务 |
| `../MindPaw_main/src/doubao_agent.*` | 设备侧请求和 fallback |
| `../MindPaw_main/src/multimodal_fusion.*` | 文本、语音、手势融合 |
| `../MindPaw_main/src/emotion_engine.*` | PAD 情绪状态机 |

## 贡献方向

- 实现真正的异步队列和 SLO 调度器。
- 增加本地小模型或 Ollama 路由。
- 添加 SQLite/PostgreSQL 会话存储。
- 增加 Prometheus metrics 和实验可视化。
- 建立机器人 Agent 的动作安全 benchmark。
- 收集不同网络和电量条件下的可复现实验数据。

提交研究型改动时，请同时附上：问题定义、baseline、指标、消融实验、硬件环境和复现实验命令。
