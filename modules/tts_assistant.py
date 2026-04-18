import os
import tempfile
import io
from typing import Optional, Dict, Any, List
from .zhipu_client import ZhipuClient

# 音频依赖检查
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

class TTSEngine:
    """语音播报模块"""
    
    def __init__(self):
        self.client = ZhipuClient()
        self.is_playing = False
        
        # 初始化pygame音频系统
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except:
                pass
    
    def text_to_speech(self, text: str, voice: str = "alloy") -> Optional[str]:
        """文本转语音"""
        try:
            # 调用智谱AI TTS服务
            result = self.client.text_to_speech(text, voice=voice)
            
            if result["success"]:
                # 保存音频文件
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_file.write(result["data"])
                    return temp_file.name
            else:
                print(f"TTS失败：{result['error']}")
                return None
                    
        except Exception as e:
            print(f"TTS失败：{str(e)}")
            return None
    
    def play_audio(self, audio_path: str) -> bool:
        """播放音频文件"""
        try:
            if not os.path.exists(audio_path):
                return False
            
            self.is_playing = True
            
            # 使用pygame播放音频
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            self.is_playing = False
            
            # 清理临时文件
            try:
                os.unlink(audio_path)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"音频播放失败：{str(e)}")
            self.is_playing = False
            
            # 清理临时文件
            try:
                os.unlink(audio_path)
            except:
                pass
            
            return False
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """语音播报文本"""
        try:
            # 生成语音
            audio_path = self.text_to_speech(text)
            if not audio_path:
                return False
            
            # 播放语音
            if wait:
                return self.play_audio(audio_path)
            else:
                # 异步播放
                import threading
                thread = threading.Thread(target=self.play_audio, args=(audio_path,))
                thread.daemon = True
                thread.start()
                return True
                
        except Exception as e:
            print(f"语音播报失败：{str(e)}")
            return False
    
    def generate_kitchen_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """生成厨房相关的语音回复"""
        try:
            prompt = f"""
            用户说："{user_input}"
            
            上下文信息：{context if context else '无'}
            
            请生成一个简短、友好、有帮助的语音回复。回复应该：
            1. 直接回应用户的问题或命令
            2. 提供有用的厨房相关建议
            3. 保持简洁（最多2-3句话）
            4. 使用自然的口语化表达
            
            回复内容：
            """
            
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.8
            )
            
            if result["success"]:
                return result["data"]
            else:
                return f"抱歉，我暂时无法处理您的请求。错误：{result['error']}"
            
        except Exception as e:
            return "抱歉，我暂时无法处理您的请求。"
    
    def speak_kitchen_response(self, user_input: str, context: Dict[str, Any] = None) -> bool:
        """生成并播报厨房相关的语音回复"""
        try:
            # 生成回复文本
            response_text = self.generate_kitchen_response(user_input, context)
            
            # 播报回复
            return self.speak(response_text)
            
        except Exception as e:
            print(f"厨房回复播报失败：{str(e)}")
            return False
    
    def stop_playback(self):
        """停止当前播放"""
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            self.is_playing = False
        except:
            pass
    
    def get_available_voices(self) -> List[str]:
        """获取可用的语音类型"""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def set_voice(self, voice: str) -> bool:
        """设置语音类型"""
        available_voices = self.get_available_voices()
        if voice in available_voices:
            self.current_voice = voice
            return True
        return False
    
    def speak_ingredient_info(self, ingredient: str, info_type: str = "general") -> bool:
        """播报食材信息"""
        try:
            prompt = f"""
            请为食材"{ingredient}"生成一个简短的语音介绍。
            
            信息类型：{info_type}
            
            请包含：
            1. 基本介绍
            2. 营养价值
            3. 常见烹饪方法
            4. 储存建议
            
            保持简洁（最多3句话）：
            """
            
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.7
            )
            
            if result["success"]:
                return self.speak(result["data"])
            else:
                print(f"食材信息生成失败：{result['error']}")
                return False
            
        except Exception as e:
            print(f"食材信息播报失败：{str(e)}")
            return False
    
    def speak_recipe_instructions(self, recipe_name: str, step_number: int = None) -> bool:
        """播报食谱制作步骤"""
        try:
            if step_number:
                prompt = f"""
                请为食谱"{recipe_name}"的第{step_number}步生成语音指导。
                指导应该清晰、具体、易于操作。
                """
            else:
                prompt = f"""
                请为食谱"{recipe_name}"生成完整的语音制作指导。
                请分步骤说明，每个步骤保持简洁。
                """
            
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.7
            )
            
            if result["success"]:
                return self.speak(result["data"])
            else:
                print(f"食谱指导生成失败：{result['error']}")
                return False
            
        except Exception as e:
            print(f"食谱指导播报失败：{str(e)}")
            return False

# 单例模式
tts_engine = TTSEngine()