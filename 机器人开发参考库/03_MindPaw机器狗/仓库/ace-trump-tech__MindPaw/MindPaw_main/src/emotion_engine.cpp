//----------------------------------------------
// PAD 情感状态机实现
//
// 核心方程:
//   Δ = α · (target - current) · (1 + β · personality)
//   current(t+1) = λ · current(t) + (1-λ) · baseline  (衰减)
//
// 特征情感 PAD 坐标 (参考 Mehrabian 基本情感 PAD 值):
//   快乐:   P=+0.81, A=+0.65, D=+0.57
//   悲伤:   P=-0.63, A=+0.06, D=-0.28
//   生气:   P=-0.51, A=+0.59, D=+0.25
//   惊讶:   P=+0.40, A=+0.67, D=-0.13
//   喜爱:   P=+0.85, A=+0.42, D=+0.35
//   中性:   P= 0.00, A= 0.30, D= 0.50
//----------------------------------------------
#include "emotion_engine.h"

// ==================== 构造函数 ====================
EmotionEngine::EmotionEngine() {
    // 默认基线: 中性
    _baseline = {0.0f, 0.3f, 0.5f};
    _current = _baseline;

    // 默认人格: 友好型 (高宜人 + 高外倾)
    _extraversion = 0.7f;
    _agreeableness = 0.8f;
    _conscientiousness = 0.6f;
    _neuroticism = 0.3f;
    _openness = 0.7f;

    // 默认衰减 (每帧 ~2-5% 回归基线)
    _decayP = 0.97f;
    _decayA = 0.98f;
    _decayD = 0.99f;

    _lastUpdateMs = 0;
    _firstInteraction = true;
    _debug = false;
}

// ==================== 指数移动平均更新 ====================
void EmotionEngine::_emaUpdate(float& current, float target, float rate, float personalityMod) {
    // Δ = rate · (target - current) · (1 + personalityMod)
    // personalityMod 根据人格调整变化速率
    float delta = rate * (target - current) * (1.0f + personalityMod);
    current += delta;
}

// ==================== 约束范围 ====================
void EmotionEngine::_clamp(PADState& s) const {
    if (s.pleasure < -1.0f) s.pleasure = -1.0f;
    if (s.pleasure > 1.0f) s.pleasure = 1.0f;
    if (s.arousal < 0.0f) s.arousal = 0.0f;
    if (s.arousal > 1.0f) s.arousal = 1.0f;
    if (s.dominance < 0.0f) s.dominance = 0.0f;
    if (s.dominance > 1.0f) s.dominance = 1.0f;
}

// ==================== PAD → 离散情感 ====================
DiscreteEmotion EmotionEngine::_padToDiscrete(const PADState& s) const {
    // 基于 PAD 空间的最近邻分类到基本情感
    // 参考 Mehrabian 基本情感 PAD 原型
    struct Proto { float p, a, d; DiscreteEmotion e; };
    static const Proto protos[] = {
        { 0.81f, 0.65f, 0.57f, DE_HAPPY},
        {-0.63f, 0.06f, 0.28f, DE_SAD},
        {-0.51f, 0.59f, 0.25f, DE_ANGRY},
        { 0.40f, 0.67f, 0.13f, DE_SURPRISE},
        { 0.85f, 0.42f, 0.35f, DE_LOVE},
        { 0.00f, 0.30f, 0.50f, DE_NEUTRAL},
    };
    const uint8_t N = 6;

    // 欧氏距离找最近原型
    float minDist = 999.0f;
    DiscreteEmotion best = DE_NEUTRAL;
    for (uint8_t i = 0; i < N; i++) {
        float dp = s.pleasure - protos[i].p;
        float da = s.arousal - protos[i].a;
        float dd = s.dominance - protos[i].d;
        float dist = dp*dp + da*da + dd*dd;
        if (dist < minDist) {
            minDist = dist;
            best = protos[i].e;
        }
    }
    return best;
}

// ==================== 获取离散情感 ====================
DiscreteEmotion EmotionEngine::getDiscreteEmotion() const {
    return _padToDiscrete(_current);
}

const char* EmotionEngine::getEmotionLabel() const {
    static const char* labels[] = {"中性", "快乐", "悲伤", "生气", "惊讶", "喜爱"};
    return labels[getDiscreteEmotion()];
}

// ==================== 核心更新：情感衰减 ====================
void EmotionEngine::update() {
    unsigned long now = millis();
    if (now - _lastUpdateMs < 1000) return;  // 至少每秒更新一次
    _lastUpdateMs = now;

    // Pleasure 回归基线
    _current.pleasure = _decayP * _current.pleasure + (1.0f - _decayP) * _baseline.pleasure;
    // Arousal 回归基线 (神经质高则衰减慢)
    float neuroMod = 1.0f + 0.2f * (_neuroticism - 0.5f);
    _current.arousal = (_decayA / neuroMod) * _current.arousal + (1.0f - _decayA / neuroMod) * _baseline.arousal;
    // Dominance 回归基线
    _current.dominance = _decayD * _current.dominance + (1.0f - _decayD) * _baseline.dominance;

    _clamp(_current);

    if (_debug) {
        Serial.printf("EMOTION: Decay → P=%.2f A=%.2f D=%.2f [%s]\n",
                     _current.pleasure, _current.arousal, _current.dominance, getEmotionLabel());
    }
}

// ==================== 重置 ====================
void EmotionEngine::reset() {
    _current = _baseline;
    _firstInteraction = true;
    Serial.println("EMOTION: Reset to baseline");
}

// ==================== 从用户输入更新 ====================
void EmotionEngine::updateFromUserInput(const String& userText, int8_t gestureClass, int8_t voiceCmd) {
    // 简单启发式：根据用户输入文本长度和情感词推断
    float targetP = _baseline.pleasure;
    float targetA = _baseline.arousal;
    float targetD = _baseline.dominance;

    // 文本长度 → 激活度 (长文本 = 更多投入 = 更高激活)
    float textLenFactor = constrain(userText.length() / 50.0f, 0.0f, 1.0f);
    targetA += 0.2f * textLenFactor;

    // 外倾性调节积极情感
    if (_extraversion > 0.5f) {
        targetP += 0.1f * (_extraversion - 0.5f);
    }

    // 手势影响
    if (gestureClass >= 1 && gestureClass <= 4) {
        targetA += 0.15f;  // 有手势输入 → 激活度上升
    }

    // EMA 更新
    float pRate = 0.3f * (1.0f + 0.5f * (_extraversion - 0.5f));
    float aRate = 0.2f * (1.0f + 0.5f * (_neuroticism - 0.5f));
    float dRate = 0.1f;

    _emaUpdate(_current.pleasure, targetP, pRate, _agreeableness > 0.5f ? 0.2f : -0.1f);
    _emaUpdate(_current.arousal, targetA, aRate, 0.0f);
    _emaUpdate(_current.dominance, targetD, dRate, _conscientiousness > 0.5f ? 0.1f : -0.1f);

    _clamp(_current);

    if (_debug) {
        Serial.printf("EMOTION: UserInput → P=%.2f A=%.2f D=%.2f [%s]\n",
                     _current.pleasure, _current.arousal, _current.dominance, getEmotionLabel());
    }
}

// ==================== 从 LLM 回复更新 ====================
void EmotionEngine::updateFromLLMResponse(int8_t emotionCode) {
    // 将 LLM 的 emotion 字段反馈到 PAD 空间
    float targetP = _baseline.pleasure;
    float targetA = _baseline.arousal;
    float targetD = _baseline.dominance;

    switch (emotionCode) {
        case 1:  targetP = 0.81f; targetA = 0.65f; targetD = 0.57f; break; // 快乐
        case 2:  targetP = -0.63f; targetA = 0.06f; targetD = 0.28f; break; // 悲伤
        case 3:  targetP = -0.51f; targetA = 0.59f; targetD = 0.25f; break; // 生气
        case 4:  targetP = 0.40f; targetA = 0.67f; targetD = 0.13f; break; // 惊讶
        case 5:  targetP = 0.85f; targetA = 0.42f; targetD = 0.35f; break; // 喜爱
        default: return;  // 无变化
    }

    // 快速跟踪 LLM 情感 (速率 0.5)
    _emaUpdate(_current.pleasure, targetP, 0.5f, 0.0f);
    _emaUpdate(_current.arousal, targetA, 0.5f, 0.0f);
    _emaUpdate(_current.dominance, targetD, 0.3f, 0.0f);

    _clamp(_current);

    if (_debug) {
        Serial.printf("EMOTION: LLM feedback(%d) → P=%.2f A=%.2f D=%.2f [%s]\n",
                     emotionCode,
                     _current.pleasure, _current.arousal, _current.dominance, getEmotionLabel());
    }
}

// ==================== 从手势更新 ====================
void EmotionEngine::updateFromGesture(int8_t gestureClass, float confidence) {
    // 手势对情感的微妙影响
    // 挥手(1)=友好→积极, 推(5)=拒绝→消极, 拉(6)=欢迎→积极
    float targetP = _baseline.pleasure;
    float targetA = _baseline.arousal + 0.1f * confidence;

    switch (gestureClass) {
        case 1: targetP = 0.2f; break;  // WAVE
        case 2: targetP = 0.1f; break;  // LEFT
        case 3: targetP = 0.1f; break;  // RIGHT
        case 4: targetP = 0.3f; break;  // UP
        case 5: targetP = -0.1f; break; // DOWN (PUSH)
        case 6: targetP = 0.2f; break;  // PULL
        default: return;
    }

    // 手势影响衰减快 (浅层情感)
    _emaUpdate(_current.pleasure, targetP, 0.15f * confidence, 0.0f);
    _emaUpdate(_current.arousal, targetA, 0.1f, 0.0f);
    _clamp(_current);
}

// ==================== 从语音命令更新 ====================
void EmotionEngine::updateFromVoice(int8_t voiceCmd) {
    // 语音命令对情感的映射
    // 简单映射: 社交/积极命令 → +P, 消极 → -P
    if (voiceCmd == 8  || voiceCmd == 20) {  // HAPPY / HELLO
        _emaUpdate(_current.pleasure, 0.5f, 0.4f, 0.0f);
        _emaUpdate(_current.arousal, 0.5f, 0.3f, 0.0f);
    } else if (voiceCmd == 9  || voiceCmd == 10) { // ANGRY / SAD
        _emaUpdate(_current.pleasure, -0.4f, 0.4f, 0.0f);
        _emaUpdate(_current.arousal, 0.3f, 0.2f, 0.0f);
    }
    _clamp(_current);
}

// ==================== 2.0: 从感知层 hazard 更新 ====================
// hazard=2 (STOP) → 短期惊讶 + 高度警觉 (高 arousal, 微负 pleasure)
// hazard=1 (CAUTION) → 轻微警觉 + 中性 pleasure
// hazard=0 (SAFE)   → 不主动扰动情感，让 PAD 自然衰减
// nearestMeters 用于在 OLED 上显示具体距离（这里只更新情感状态）
void EmotionEngine::updateFromReconHazard(uint8_t hazard, float nearestMeters) {
    (void)nearestMeters;  // 情感模型暂不直接使用数值；保留参数便于扩展
    float targetP = _baseline.pleasure;
    float targetA = _baseline.arousal;
    float targetD = _baseline.dominance;

    switch (hazard) {
        case 2:  // STOP — 惊讶 + 警觉
            targetP = -0.10f;
            targetA = 0.75f;
            targetD = 0.20f;
            break;
        case 1:  // CAUTION — 轻微警觉
            targetA = 0.55f;
            break;
        case 0:  // SAFE — 不主动扰动
        default:
            return;
    }

    // hazard 触发的情感变化要快 (50ms 级反馈)，但衰减也快，避免长期干扰
    _emaUpdate(_current.pleasure, targetP, 0.6f, 0.0f);
    _emaUpdate(_current.arousal,  targetA, 0.6f, 0.0f);
    _emaUpdate(_current.dominance, targetD, 0.4f, 0.0f);
    _clamp(_current);

    if (_debug) {
        Serial.printf("EMOTION: ReconHazard(%u) nearest=%.2fm → P=%.2f A=%.2f D=%.2f [%s]\n",
                      hazard, nearestMeters,
                      _current.pleasure, _current.arousal, _current.dominance, getEmotionLabel());
    }
}

// ==================== VAD-to-Motion 映射 ====================
int8_t EmotionEngine::recommendAction() const {
    float p = _current.pleasure;
    float a = _current.arousal;

    if (p > 0.6f && a > 0.5f) return 11;   // 跳舞 (快乐+高激活)
    if (p > 0.4f && a < 0.4f) return 17;   // 伸懒腰 (满足+低激活)
    if (p < -0.3f && a > 0.6f) return 13;  // 摇头 (生气+高激活)
    if (p < -0.2f && a < 0.4f) return 16;  // 安慰动作 (悲伤+低激活)
    if (p > 0.5f && a > 0.3f) return 12;   // 点头 (积极)
    if (p < -0.1f && a > 0.4f) return 18;  // 捂脸 (尴尬+中激活)
    return 0;  // 无动作
}

int8_t EmotionEngine::recommendExpression() const {
    DiscreteEmotion de = getDiscreteEmotion();
    switch (de) {
        case DE_HAPPY:    return 0;  // 开心
        case DE_ANGRY:    return 1;  // 生气
        case DE_SAD:      return 5;  // 难过
        case DE_SURPRISE: return 3;  // 好奇
        case DE_LOVE:     return 4;  // 喜爱
        default:          return -1; // 不变
    }
}

int8_t EmotionEngine::recommendMelody() const {
    DiscreteEmotion de = getDiscreteEmotion();
    switch (de) {
        case DE_HAPPY:    return 5;  // 快乐旋律
        case DE_SAD:      return 6;  // 悲伤旋律
        case DE_ANGRY:    return 7;  // 警报
        case DE_LOVE:     return 3;  // 你好 (友好的)
        case DE_SURPRISE: return 1;  // 确认音
        default:          return -1;
    }
}

// ==================== 情感状态描述 ====================
String EmotionEngine::getStateDescription() const {
    String desc = "当前情感状态: ";
    desc += getEmotionLabel();
    desc += " (Pleasure=";
    desc += String(_current.pleasure, 2);
    desc += ", Arousal=";
    desc += String(_current.arousal, 2);
    desc += ", Dominance=";
    desc += String(_current.dominance, 2);
    desc += ")";
    return desc;
}

// ==================== 人格设置 ====================
void EmotionEngine::setPersonality(float extraversion, float agreeableness,
                                    float conscientiousness, float neuroticism, float openness) {
    _extraversion = constrain(extraversion, 0.0f, 1.0f);
    _agreeableness = constrain(agreeableness, 0.0f, 1.0f);
    _conscientiousness = constrain(conscientiousness, 0.0f, 1.0f);
    _neuroticism = constrain(neuroticism, 0.0f, 1.0f);
    _openness = constrain(openness, 0.0f, 1.0f);

    Serial.printf("EMOTION: Personality set (E=%.1f A=%.1f C=%.1f N=%.1f O=%.1f)\n",
                 _extraversion, _agreeableness, _conscientiousness, _neuroticism, _openness);
}

void EmotionEngine::setDecayRate(float pDecay, float aDecay, float dDecay) {
    _decayP = constrain(pDecay, 0.9f, 1.0f);
    _decayA = constrain(aDecay, 0.9f, 1.0f);
    _decayD = constrain(dDecay, 0.9f, 1.0f);
}
