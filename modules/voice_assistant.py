import os
import tempfile
import numpy as np
import base64
import io
import re
from typing import Optional, Tuple, Dict, Any, List
from .zhipu_client import ZhipuClient

# 音频依赖检查
try:
    import sounddevice as sd
    import soundfile as sf
    from pydub import AudioSegment
    from pydub.effects import normalize
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sd = None
    sf = None
    AudioSegment = None
    normalize = None

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

class VoiceAssistant:
    """语音助手（使用GLM-ASR-2512和GLM-TTS）"""
    
    def __init__(self):
        self.client = ZhipuClient()
        self.sample_rate = 44100
        
    def _record_audio(self, duration: int = 5) -> Optional[np.ndarray]:
        """录制音频"""
        if not AUDIO_AVAILABLE:
            print("音频功能不可用，请安装sounddevice和soundfile")
            return None
            
        try:
            print(f"开始录音 {duration} 秒...")
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            print("录音完成")
            return audio_data.flatten()
        except Exception as e:
            print(f"录音失败: {e}")
            return None
    
    def record_and_recognize(self, duration: int = 5, language: str = "zh-CN") -> Optional[str]:
        """录音并使用GLM-ASR-2512进行语音识别（支持中文）"""
        try:
            # 录音
            audio_data = self._record_audio(duration)
            if audio_data is None:
                return None
            
            # 保存临时音频文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            sf.write(temp_file.name, audio_data, self.sample_rate)
            
            # 调用GLM-ASR-2512进行语音识别，指定中文语言
            result = self.client.speech_to_text(temp_file.name)
            
            # 清理临时文件
            os.unlink(temp_file.name)
            
            if result["success"]:
                recognized_text = result["data"]
                # 中文语音识别后处理
                return self._post_process_chinese_text(recognized_text)
            else:
                print(f"语音识别失败: {result['error']}")
                return None
                
        except Exception as e:
            print(f"语音识别错误: {e}")
            return None
    
    def _post_process_chinese_text(self, text: str) -> str:
        """中文语音识别后处理"""
        if not text:
            return text
            
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 常见中文语音识别错误修正
        corrections = {
            "下一步": ["下步", "下不", "下一步骤", "下一步骤"],
            "暂停": ["暂停一下", "停一下", "停止", "停"],
            "继续": ["继续", "继续吧", "继续开始"],
            "重新开始": ["重新", "重新来", "重新开始", "重新来过"],
            "加时间": ["加时", "加十分钟", "加五分钟", "加时间"],
            "减时间": ["减时", "减十分钟", "减五分钟", "减时间"],
            "查看步骤": ["查看", "看步骤", "步骤", "查看步骤"],
            "查看营养": ["营养", "看营养", "营养信息", "查看营养"]
        }
        
        for correct_word, wrong_variants in corrections.items():
            for wrong in wrong_variants:
                if wrong in text:
                    text = text.replace(wrong, correct_word)
        
        return text

    def speak_text(self, text: str, language: str = "zh-CN") -> bool:
        """使用GLM-TTS进行语音合成（支持中文）"""
        try:
            # 调用GLM-TTS进行语音合成，指定中文语言
            result = self.client.text_to_speech(text)
            
            if result["success"]:
                # 播放音频
                audio_data = base64.b64decode(result["data"])
                audio_file = io.BytesIO(audio_data)
                
                if PYGAME_AVAILABLE:
                    pygame.mixer.init()
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    return True
                else:
                    print("PyGame不可用，无法播放音频")
                    return False
            else:
                print(f"语音合成失败: {result['error']}")
                return False
                
        except Exception as e:
            print(f"语音合成错误: {e}")
            return False
    
    def speak_chinese_text(self, text: str) -> bool:
        """专门的中文语音合成"""
        return self.speak_text(text, language="zh-CN")

    def get_available_voices(self) -> List[str]:
        """获取可用的语音类型"""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def recognize_chinese_commands(self, recognized_text: str) -> Dict[str, Any]:
        """识别中文语音命令"""
        if not recognized_text:
            return {"command": "unknown", "original_text": "", "confidence": 0.0}
            
        commands = {
            "下一步": "next_step",
            "暂停": "pause", 
            "继续": "continue",
            "重新开始": "restart",
            "加时间": "add_time",
            "减时间": "reduce_time",
            "查看步骤": "view_steps",
            "查看营养": "view_nutrition",
            "帮助": "help",
            "退出": "exit"
        }
        
        # 中文命令精确匹配
        for chinese_cmd, english_cmd in commands.items():
            if chinese_cmd in recognized_text:
                return {
                    "command": english_cmd,
                    "original_text": recognized_text,
                    "confidence": 0.9
                }
        
        # 模糊匹配
        for chinese_cmd, english_cmd in commands.items():
            if any(word in recognized_text for word in chinese_cmd):
                return {
                    "command": english_cmd,
                    "original_text": recognized_text,
                    "confidence": 0.7
                }
        
        return {"command": "unknown", "original_text": recognized_text, "confidence": 0.0}
    
    def provide_chinese_feedback(self, command_result: Dict[str, Any]) -> bool:
        """提供中文语音反馈"""
        feedback_messages = {
            "next_step": "好的，正在为您跳转到下一步",
            "pause": "已暂停，请说'继续'来恢复", 
            "continue": "好的，继续烹饪",
            "restart": "正在重新开始烹饪流程",
            "add_time": "已为您增加时间",
            "reduce_time": "已为您减少时间",
            "view_steps": "正在显示烹饪步骤",
            "view_nutrition": "正在显示营养信息",
            "help": "我是您的智能厨房助手，支持语音控制烹饪流程",
            "exit": "再见，祝您烹饪愉快",
            "unknown": "抱歉，我没有听懂您的指令，请再说一遍"
        }
        
        command = command_result.get("command", "unknown")
        if command in feedback_messages:
            feedback_text = feedback_messages[command]
            return self.speak_chinese_text(feedback_text)
        
        return False
    
    def get_chinese_voice_settings(self) -> Dict[str, Any]:
        """获取中文语音设置"""
        return {
            "language": "zh-CN",
            "voice": "alloy",  # 可以尝试不同的中文语音
            "speed": 1.0,      # 语速
            "pitch": 1.0,      # 音调
            "volume": 0.8      # 音量
        }
    
    def handle_chinese_voice_errors(self, error_type: str) -> bool:
        """处理中文语音错误"""
        error_messages = {
            "recognition_failed": "抱歉，语音识别失败，请重试",
            "synthesis_failed": "语音合成失败，请检查网络连接",
            "audio_device_error": "音频设备错误，请检查麦克风权限",
            "network_error": "网络连接失败，请检查网络设置"
        }
        
        if error_type in error_messages:
            error_text = error_messages[error_type]
            print(f"中文语音错误: {error_text}")
            # 可以选择是否播放错误提示
            # return self.speak_chinese_text(error_text)
        
        return False

# 单例模式（注释掉，避免循环导入）
# voice_assistant = VoiceAssistant()