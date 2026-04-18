import os
import tempfile
import numpy as np
from typing import Optional, Tuple, Dict, Any
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

class VoiceAssistant:
    """语音识别模块（基于GLM-ASR-2512）"""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.client = ZhipuClient()
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_data = []
    
    def record_audio(self, duration: float = 5.0) -> Optional[str]:
        """录制音频"""
        try:
            print(f"开始录音，时长：{duration}秒...")
            
            # 录制音频
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32'
            )
            sd.wait()
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, self.sample_rate)
                return temp_file.name
                
        except Exception as e:
            print(f"录音失败：{str(e)}")
            return None
    
    def preprocess_audio(self, audio_path: str) -> str:
        """预处理音频文件"""
        try:
            # 加载音频
            audio = AudioSegment.from_file(audio_path)
            
            # 标准化音量
            audio = normalize(audio)
            
            # 转换为单声道
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # 转换为16kHz采样率
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
            
            # 保存处理后的音频
            processed_path = audio_path.replace('.wav', '_processed.wav')
            audio.export(processed_path, format='wav')
            
            return processed_path
            
        except Exception as e:
            print(f"音频预处理失败：{str(e)}")
            return audio_path
    
    def speech_to_text(self, audio_path: str) -> Optional[str]:
        """语音转文字"""
        try:
            # 预处理音频
            processed_path = self.preprocess_audio(audio_path)
            
            # 调用智谱AI语音识别
            result = self.client.speech_to_text(processed_path)
            
            # 清理临时文件
            try:
                if processed_path != audio_path:
                    os.unlink(processed_path)
                os.unlink(audio_path)
            except:
                pass
            
            if result["success"]:
                return result["data"]
            else:
                print(f"语音识别失败：{result['error']}")
                return None
            
        except Exception as e:
            print(f"语音识别失败：{str(e)}")
            
            # 清理临时文件
            try:
                os.unlink(audio_path)
            except:
                pass
            
            return None
    
    def process_kitchen_command(self, command_text: str) -> Dict[str, Any]:
        """处理厨房相关语音命令"""
        try:
            prompt = f"""
            用户说了以下厨房相关命令："{command_text}"
            
            请分析命令意图并按照以下JSON格式返回：
            {{
                "intent": "命令意图（如：食材识别、食谱推荐、营养分析等）",
                "ingredients": ["提到的食材"],
                "action": "需要执行的动作",
                "parameters": {{"参数键": "参数值"}},
                "response": "给用户的语音回复"
            }}
            """
            
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.7
            )
            
            import json
            if result["success"]:
                try:
                    return json.loads(result["data"])
                except:
                    return {
                        "intent": "unknown",
                        "ingredients": [],
                        "action": "unknown",
                        "parameters": {},
                        "response": result["data"]
                    }
            else:
                raise Exception(f"Command processing failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Command processing failed: {str(e)}")
    
    def start_continuous_listening(self, callback) -> bool:
        """开始持续监听"""
        try:
            self.is_recording = True
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"音频状态：{status}")
                
                # 检测语音活动
                if np.max(np.abs(indata)) > 0.01:  # 音量阈值
                    self.audio_data.append(indata.copy())
                
                # 每2秒处理一次音频
                if len(self.audio_data) >= 2:
                    self._process_audio_chunk(callback)
            
            # 开始流式录音
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=audio_callback,
                blocksize=int(self.sample_rate * 1)  # 1秒块
            ):
                while self.is_recording:
                    sd.sleep(100)
            
            return True
            
        except Exception as e:
            print(f"持续监听失败：{str(e)}")
            return False
    
    def _process_audio_chunk(self, callback):
        """处理音频块"""
        try:
            if not self.audio_data:
                return
            
            # 合并音频数据
            audio_chunk = np.concatenate(self.audio_data)
            self.audio_data = []
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, audio_chunk, self.sample_rate)
                
                # 语音识别
                text = self.speech_to_text(temp_file.name)
                if text:
                    # 处理命令
                    command_result = self.process_kitchen_command(text)
                    callback(command_result)
            
        except Exception as e:
            print(f"音频块处理失败：{str(e)}")
    
    def stop_listening(self):
        """停止监听"""
        self.is_recording = False

# 单例模式
voice_assistant = VoiceAssistant()