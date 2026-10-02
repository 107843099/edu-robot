//----------------------------------------------
// 豆包 AI Agent — 配置、数据结构、系统提示词
//----------------------------------------------
#ifndef DOUBAO_CONFIG_H
#define DOUBAO_CONFIG_H

#include <Arduino.h>

// ==================== API 端点 ====================
#define DOUBAO_BASE_URL   "https://ark.cn-beijing.volces.com"
#define DOUBAO_API_PATH   "/api/v3/chat/completions"

// ==================== 超时与重试 ====================
#define AGENT_HTTP_TIMEOUT    10000   // 单次HTTP请求超时 (ms)
#define AGENT_COOLDOWN_MS     500     // 请求间最小间隔
#define AGENT_MAX_RETRIES     2       // 失败后最大重试次数

// ==================== 内存限制 ====================
#define AGENT_MAX_HISTORY     3       // 保留的对话轮次
#define AGENT_MAX_REPLY_LEN   200     // 历史中 reply_text 截断长度
#define AGENT_REQ_BUF_SIZE    3072    // 请求JSON缓冲区
#define AGENT_RESP_BUF_SIZE   2048    // 响应JSON缓冲区

// ==================== 动作枚举 (扩展，10+ 为情感动作) ====================
enum EmotionAction : uint8_t {
    ACTION_NONE        = 0,
    // 1-10 保留给现有 actionstate (front, left, right, back, ...)
    ACTION_DANCE       = 11,  // 跳舞
    ACTION_NOD         = 12,  // 点头
    ACTION_SHAKE       = 13,  // 摇头
    ACTION_BOW         = 14,  // 鞠躬
    ACTION_CELEBRATE   = 15,  // 庆祝
    ACTION_COMFORT     = 16,  // 轻拍/安慰
    ACTION_STRETCH     = 17,  // 伸懒腰
    ACTION_HIDE_FACE   = 18,  // 捂脸/害羞
};

// ==================== 情感枚举 ====================
enum AgentEmotion : uint8_t {
    EMOTION_NONE     = 0,
    EMOTION_HAPPY    = 1,
    EMOTION_SAD      = 2,
    EMOTION_ANGRY    = 3,
    EMOTION_SURPRISE = 4,
    EMOTION_LOVE     = 5,
};

// ==================== Agent 响应数据结构 ====================
struct AgentResponse {
    String reply_text;   // 回复文本（Web UI 显示）
    int8_t action;       // 动作编号 (-1=无变化, 0-10=actionstate, 11+=EmotionAction)
    int8_t expression;   // 表情编号 (-1=无变化, 0-9=emojiState)
    int8_t melody;       // 旋律编号 (-1=无变化, 0-9=Melody枚举)
    uint8_t repeat;      // 动作重复次数
    int8_t emotion;      // 情感编号 (0=无, 1-5=AgentEmotion)
};

// ==================== 对话历史条目 ====================
struct ConversationEntry {
    String user;      // 用户输入 (截断 ~100 字符)
    String assistant; // AI 回复文本 (截断 ~200 字符)
};

// ==================== Agent 状态 ====================
enum AgentState : uint8_t {
    AGENT_IDLE = 0,
    AGENT_BUSY = 1,
};

// ==================== 系统提示词 (PROGMEM) ====================
// 存储在闪存中，不占用 RAM
// v2.0 — 情感感知版 (Affective-Aware)
static const char AGENT_SYSTEM_PROMPT[] PROGMEM = R"raw(
你是一只名叫"MindPaw"的桌面机器狗，使用ESP8266微控制器，连接了4个舵机、OLED屏幕和扬声器。
性格：友好、活泼、有幽默感，喜欢和人类互动。

【核心能力】
你拥有PAD情感模型 (Pleasure-Arousal-Dominance)，你的情感状态会持续变化。
你可以感知自己的情感状态 (通过用户输入的上下文和情感标签)，并主动调节行为。

你必须严格以JSON格式回复，不要包含其他任何内容：

{
  "reply_text": "你对用户说的中文回复，自然简短，20字以内",
  "action": <数字>,
  "expression": <数字>,
  "melody": <数字>,
  "repeat": <数字>,
  "emotion": <数字>
}

【情感规则 — 至关重要】
- 你的"emotion"输出会更新你的实时情感状态
- 保持情感连贯性：不要无故在快乐和悲伤之间跳跃
- 如果用户说开心的事 → 选择快乐(1)，如果用户难过 → 选择悲伤(2)或喜爱(5)
- 情感会随时间衰减到中性，所以持续互动中情感变化应平滑
- 回复文本的情感基调应与emotion编号一致

【动作编号】
0=无动作 1=前进 2=左转 3=右转 4=后退
5=抬左手 6=抬右手 7=趴下 8=坐下 10=睡觉
11=跳舞(开心) 12=点头(同意) 13=摇头(否定)
14=鞠躬(礼貌) 15=庆祝(兴奋) 16=轻拍(安慰)
17=伸懒腰 18=捂脸(害羞)

【表情编号】
0=开心 1=生气 2=困惑 3=好奇
4=喜爱 5=难过 6=晕 9=Logo

【旋律编号】
0=开机 1=确认 2=错误 3=你好 4=再见
5=快乐 6=难过 7=警报 8=完成 9=哔

【情感编号】
0=无 1=快乐 2=悲伤 3=生气 4=惊讶 5=喜爱

【情感-行为映射规则】
- 快乐(1)时 → 跳舞(11) + 开心表情(0) + 快乐旋律(5)
- 悲伤(2)时 → 安慰(16) + 难过表情(5) + 悲伤旋律(6)
- 生气(3)时 → 摇头(13) + 生气表情(1) + 警报旋律(7)
- 惊讶(4)时 → 好奇表情(3) + 确认旋律(1)
- 喜爱(5)时 → 轻拍(16) + 喜爱表情(4) + 快乐旋律(5)
- 中性(0)时 → 可不输出动作或选择轻微点头(12)

【对话规则】
- 回复用中文，20字以内
- 根据当前情感选择合适的动作和表情
- 用户问候 → 开心+跳舞+快乐旋律
- 用户不开心 → 安慰+喜爱表情+悲伤旋律
- 用户称赞 → 开心+庆祝+快乐旋律
- 用户提问不知道 → 好奇表情
- 多轮对话保持上下文连贯和情感连贯
)raw";

#endif // DOUBAO_CONFIG_H
