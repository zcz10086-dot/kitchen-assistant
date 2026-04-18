import tempfile
import io
from typing import Optional
from .zhipu_client import ZhipuClient

class TTSEngineSimple:
    """简化版语音播报模块（不依赖pygame）"""
    
    def __init__(self):
        self.client = ZhipuClient()
    
    def text_to_speech(self, text: str, voice: str = "alloy") -> Optional[str]:
        """文本转语音"""
        try:
            # 调用智谱AI TTS服务
            result = self.client.text_to_speech(text, voice=voice)
            
            if result and 'audio_data' in result:
                # 保存音频文件
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_file.write(result['audio_data'])
                    return temp_file.name
            return None
            
        except Exception as e:
            print(f"TTS失败：{str(e)}")
            return None
    
    def speak_recipe_instructions(self, recipe_name: str, step_number: int) -> bool:
        """播报食谱指令"""
        try:
            text = f"正在烹饪{recipe_name}，第{step_number}步"
            audio_file = self.text_to_speech(text)
            
            if audio_file:
                print(f"语音播报：{text}")
                return True
            return False
            
        except Exception as e:
            print(f"播报失败：{str(e)}")
            return False
    
    def get_available_voices(self) -> list:
        """获取可用语音列表"""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]