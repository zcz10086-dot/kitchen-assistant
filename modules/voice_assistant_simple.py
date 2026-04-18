import tempfile
from typing import Optional, Dict, Any
from .zhipu_client import ZhipuClient

class VoiceAssistantSimple:
    """简化版语音助手模块（不依赖复杂音频包）"""
    
    def __init__(self):
        self.client = ZhipuClient()
    
    def record_audio(self, duration: float = 5.0) -> Optional[str]:
        """模拟录音功能（返回示例音频文件路径）"""
        try:
            # 创建一个空的音频文件（模拟录音）
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # 写入WAV文件头（简单的44字节头）
                temp_file.write(b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00')
                return temp_file.name
        except Exception as e:
            print(f"模拟录音失败：{str(e)}")
            return None
    
    def speech_to_text(self, audio_file: str) -> Optional[str]:
        """语音转文字"""
        try:
            # 模拟语音识别结果
            sample_texts = [
                "开始烹饪",
                "下一步", 
                "暂停",
                "继续",
                "加五分钟",
                "完成"
            ]
            
            # 返回一个示例命令
            import random
            return random.choice(sample_texts)
            
        except Exception as e:
            print(f"语音识别失败：{str(e)}")
            return None
    
    def process_kitchen_command(self, text: str) -> Dict[str, Any]:
        """处理厨房命令"""
        commands = {
            "开始": {"intent": "start", "action": "开始烹饪"},
            "下一步": {"intent": "next", "action": "下一步"},
            "暂停": {"intent": "pause", "action": "暂停"},
            "继续": {"intent": "resume", "action": "继续"},
            "加时间": {"intent": "add_time", "action": "加5分钟"},
            "完成": {"intent": "finish", "action": "完成烹饪"}
        }
        
        for cmd, action in commands.items():
            if cmd in text:
                return action
        
        return {"intent": "unknown", "action": "未知命令"}