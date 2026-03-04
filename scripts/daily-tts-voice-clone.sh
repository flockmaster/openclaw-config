#!/bin/bash
# 每日语音播报 - 使用用户声音克隆
# 用法：./daily-tts-voice-clone.sh "要播报的文本"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QWEN_TTS_DIR="$HOME/.agents/skills/qwen3-tts-skills"
REF_AUDIO="$HOME/.openclaw/media/inbound/金隅丽景园_3---0ab9da22-166b-4c0d-9f09-960be8535a74.m4a"
REF_TEXT="哼，继续"
OUTPUT_DIR="$HOME/Desktop/qwen3-tts-output"

# 确保输出目录存在
mkdir -p "$OUTPUT_DIR"

# 获取文本参数，如果没有则使用默认测试文本
TEXT="${1:-你好，这是用你的声音克隆生成的每日语音播报。}"

# 生成时间戳文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$OUTPUT_DIR/daily_broadcast_$TIMESTAMP.wav"

echo "正在生成语音..."
echo "文本：$TEXT"
echo "输出：$OUTPUT_FILE"

cd "$QWEN_TTS_DIR" && uv run scripts/run_qwen3_tts.py voice-clone \
  --language Chinese \
  --ref-audio "$REF_AUDIO" \
  --ref-text "$REF_TEXT" \
  --text "$TEXT" \
  --output "$OUTPUT_FILE" \
  --x-vector-only-mode

if [ $? -eq 0 ]; then
  echo "✅ 语音生成成功：$OUTPUT_FILE"
  # 自动播放（可选）
  # afplay "$OUTPUT_FILE" &
else
  echo "❌ 语音生成失败"
  exit 1
fi
