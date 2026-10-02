//----------------------------------------------
// PAD 情感状态机 — 面向伴生机器人的情感计算引擎
//
// 基于 Mehrabian (1996) PAD 情感模型:
//   Pleasure   [-1.0, 1.0]  — 愉悦度
//   Arousal    [ 0.0, 1.0]  — 激活度
//   Dominance  [ 0.0, 1.0]  — 支配度
//
// 加上 Big Five 人格特质过滤情感变化速率。
// 参考: Mehrabian, A. "Pleasure-arousal-dominance: A general framework
//       for describing and measuring individual differences in Temperament."
//       Current Psychology, 1996.
//----------------------------------------------
#ifndef EMOTION_ENGINE_H
#define EMOTION_ENGINE_H

#include <Arduino.h>
#include "doubao_config.h"  // 复用 AgentEmotion 枚举和 EmotionAction

// ==================== PAD 情感状态 ====================
struct PADState {
    float pleasure;    // -1.0 ~ 1.0
    float arousal;     //  0.0 ~ 1.0
    float dominance;   //  0.0 ~ 1.0
};

// ==================== 离散情感映射表 ====================
// 从 PAD 空间映射到 6 种基本情感 (Ekman, 1992)
enum DiscreteEmotion : uint8_t {
    DE_NEUTRAL  = 0,
    DE_HAPPY    = 1,
    DE_SAD      = 2,
    DE_ANGRY    = 3,
    DE_SURPRISE = 4,
    DE_LOVE     = 5,
};

// ==================== 情感引擎类 ====================
class EmotionEngine {
public:
    EmotionEngine();

    // ---------- 核心控制 ----------
    // 每帧调用：情感衰减 + 基线回归
    void update();

    // 重置到基线
    void reset();

    // ---------- 外部交互更新 ----------
    // 从用户输入更新情感 (文本分析 → PAD 偏移)
    void updateFromUserInput(const String& userText, int8_t gestureClass = -1, int8_t voiceCmd = -1);

    // 从 LLM 回复更新情感 (emotion 字段反馈)
    void updateFromLLMResponse(int8_t emotionCode);

    // 2.0: 从流式 3D 重建感知层更新情感 (hazard + 最近障碍距离)
    // hazard: 0=safe, 1=caution, 2=stop
    // nearestMeters: 当前最近障碍距离 (m)
    void updateFromReconHazard(uint8_t hazard, float nearestMeters);

    // 从手势分类结果更新
    void updateFromGesture(int8_t gestureClass, float confidence);

    // 从语音命令更新
    void updateFromVoice(int8_t voiceCmd);

    // ---------- 查询 ----------
    const PADState& getState() const { return _current; }
    DiscreteEmotion getDiscreteEmotion() const;
    const char* getEmotionLabel() const;

    // PAD → 动作/表情/旋律 推荐
    int8_t recommendAction() const;
    int8_t recommendExpression() const;
    int8_t recommendMelody() const;

    // 获取情感状态描述文本 (用于 LLM prompt 注入)
    String getStateDescription() const;

    // ---------- 人格设置 ----------
    // Big Five: 各维度 [0.0, 1.0]
    void setPersonality(float extraversion, float agreeableness,
                        float conscientiousness, float neuroticism, float openness);

    // 设置情感衰减速率 [0.9, 1.0] — 越大衰减越慢
    void setDecayRate(float pDecay, float aDecay, float dDecay);

    // ---------- 调试 ----------
    void setDebug(bool debug) { _debug = debug; }

private:
    PADState _current;       // 当前情感状态
    PADState _baseline;      // 基线 (默认中性: 0.0, 0.3, 0.5)

    // Big Five 人格参数
    float _extraversion;     // 外倾性 — 影响积极情感变化速率
    float _agreeableness;    // 宜人性 — 影响愤怒/冲突反应
    float _conscientiousness;// 尽责性 — 影响情感稳定性
    float _neuroticism;      // 神经质 — 影响消极情感强度和衰减
    float _openness;         // 开放性 — 影响好奇/惊讶反应

    // 衰减参数 [0.9, 1.0) — 无交互时回归基线
    float _decayP;  // Pleasure 衰减
    float _decayA;  // Arousal 衰减
    float _decayD;  // Dominance 衰减

    // 上次更新时间 (用于衰减计算)
    unsigned long _lastUpdateMs;

    // 是否为首次交互 (用于初始化偏移)
    bool _firstInteraction;

    bool _debug;

    // ---------- 内部方法 ----------
    // 指数移动平均更新
    void _emaUpdate(float& current, float target, float rate, float personalityMod);
    // 约束到合法范围
    void _clamp(PADState& s) const;
    // PAD → 离散情感
    DiscreteEmotion _padToDiscrete(const PADState& s) const;
};

#endif // EMOTION_ENGINE_H
