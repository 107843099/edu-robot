//----------------------------------------------
// 多模态情感融合层实现
//----------------------------------------------
#include "multimodal_fusion.h"

// ==================== 构造函数 ====================
MultimodalFusion::MultimodalFusion() {
    _emotion = nullptr;
    _debug = false;
    _lastCtx.modality = MOD_TEXT;
    _lastCtx.gestureClass = -1;
    _lastCtx.gestureConfidence = 0.0f;
    _lastCtx.voiceCmd = -1;
}

// ==================== 模态标签 ====================
const char* MultimodalFusion::_modalityLabel(InputModality mod) {
    switch (mod) {
        case MOD_TEXT:    return "文本";
        case MOD_VOICE:   return "语音";
        case MOD_GESTURE: return "手势";
        default:          return "未知";
    }
}

// ==================== 语音命令 → 文本 ====================
String MultimodalFusion::_voiceCmdToText(int8_t cmd) {
    switch (cmd) {
        case 1:  return "前进";
        case 2:  return "后退";
        case 3:  return "左转";
        case 4:  return "右转";
        case 5:  return "停止";
        case 6:  return "坐下";
        case 7:  return "趴下";
        case 8:  return "开心";
        case 9:  return "生气";
        case 10: return "难过";
        case 11: return "好奇";
        case 12: return "喜欢";
        case 13: return "睡觉";
        case 14: return "自由模式";
        case 15: return "抬左手";
        case 16: return "抬右手";
        case 17: return "时间";
        case 18: return "天气";
        case 20: return "你好";
        case 21: return "再见";
        default:
            if (cmd >= 30) return "AI对话";  // 扩展命令
            return "未知指令";
    }
}

// ==================== 手势 → 文本 ====================
String MultimodalFusion::_gestureToText(int8_t gestureClass) {
    switch (gestureClass) {
        case 1: return "挥手";
        case 2: return "伸掌";
        case 3: return "握拳";
        case 4: return "指点";
        default: return "";
    }
}

// ==================== 处理文本输入 ====================
MultimodalContext MultimodalFusion::processText(const String& text) {
    MultimodalContext ctx;
    ctx.modality = MOD_TEXT;
    ctx.userText = text;
    ctx.gestureClass = -1;
    ctx.gestureConfidence = 0.0f;
    ctx.voiceCmd = -1;

    // 更新情感引擎
    if (_emotion) {
        _emotion->updateFromUserInput(text, -1, -1);
        ctx.emotionDescription = _emotion->getStateDescription();
    }

    _lastCtx = ctx;

    if (_debug) {
        Serial.printf("FUSION: [文本] \"%s\" | %s\n", text.c_str(), ctx.emotionDescription.c_str());
    }

    return ctx;
}

// ==================== 处理语音输入 ====================
MultimodalContext MultimodalFusion::processVoice(int8_t voiceCmd) {
    String voiceText = _voiceCmdToText(voiceCmd);

    MultimodalContext ctx;
    ctx.modality = MOD_VOICE;
    ctx.userText = voiceText;
    ctx.gestureClass = -1;
    ctx.gestureConfidence = 0.0f;
    ctx.voiceCmd = voiceCmd;

    // 更新情感引擎
    if (_emotion) {
        _emotion->updateFromUserInput(voiceText, -1, voiceCmd);
        _emotion->updateFromVoice(voiceCmd);
        ctx.emotionDescription = _emotion->getStateDescription();
    }

    _lastCtx = ctx;

    if (_debug) {
        Serial.printf("FUSION: [语音] cmd=%d \"%s\" | %s\n",
                     voiceCmd, voiceText.c_str(), ctx.emotionDescription.c_str());
    }

    return ctx;
}

// ==================== 处理手势输入 ====================
MultimodalContext MultimodalFusion::processGesture(int8_t gestureClass, float confidence) {
    String gestureText = _gestureToText(gestureClass);

    MultimodalContext ctx;
    ctx.modality = MOD_GESTURE;
    ctx.userText = gestureText;
    ctx.gestureClass = gestureClass;
    ctx.gestureConfidence = confidence;
    ctx.voiceCmd = -1;

    // 更新情感引擎
    if (_emotion) {
        _emotion->updateFromUserInput(gestureText, gestureClass, -1);
        _emotion->updateFromGesture(gestureClass, confidence);
        ctx.emotionDescription = _emotion->getStateDescription();
    }

    _lastCtx = ctx;

    if (_debug) {
        Serial.printf("FUSION: [手势] class=%d \"%s\" (conf=%.2f) | %s\n",
                     gestureClass, gestureText.c_str(), confidence, ctx.emotionDescription.c_str());
    }

    return ctx;
}

// ==================== 构建情感增强 Prompt ====================
String MultimodalFusion::buildAffectivePrompt(const MultimodalContext& ctx) {
    String prompt;

    // 情感上下文前缀
    if (_emotion) {
        prompt += "[情感状态:";
        prompt += _emotion->getEmotionLabel();
        prompt += "|P=";
        prompt += String(_emotion->getState().pleasure, 2);
        prompt += "|A=";
        prompt += String(_emotion->getState().arousal, 2);
        prompt += "|D=";
        prompt += String(_emotion->getState().dominance, 2);
        prompt += "]";
    }

    // 模态标签
    prompt += "[模态:";
    prompt += _modalityLabel(ctx.modality);
    prompt += "]";

    // 手势补充信息
    if (ctx.gestureClass > 0) {
        prompt += "[手势:";
        prompt += _gestureToText(ctx.gestureClass);
        prompt += "]";
    }

    // 用户消息
    prompt += " 用户说: \"";
    prompt += ctx.userText;
    prompt += "\"";

    return prompt;
}
