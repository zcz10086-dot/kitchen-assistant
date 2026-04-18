import os
import json
import time
from typing import Dict, List, Optional, Any, Union
import requests
from zhipuai import ZhipuAI
from dotenv import load_dotenv

load_dotenv()

class ZhipuClient:
    """智谱AI统一客户端 - 包含完整的异常处理和超时控制"""
    
    def __init__(self, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            timeout: 请求超时时间（秒）
        """
        self.api_key = os.getenv('ZHIPU_API_KEY')
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not found in environment variables")
        
        self.client = ZhipuAI(api_key=self.api_key)
        self.timeout = timeout
        
    def _make_request_with_timeout(self, request_func, *args, **kwargs) -> Any:
        """
        带超时控制的请求包装器
        
        Args:
            request_func: 请求函数
            *args, **kwargs: 请求参数
            
        Returns:
            请求结果
            
        Raises:
            TimeoutError: 请求超时
            Exception: 其他错误
        """
        import threading
        
        result = {}
        exception = None
        
        def worker():
            nonlocal result, exception
            try:
                result['data'] = request_func(*args, **kwargs)
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout)
        
        if thread.is_alive():
            raise TimeoutError(f"Request timeout after {self.timeout} seconds")
        
        if exception:
            raise exception
        
        return result['data']
    
    def chat(self, messages: List[Dict], model: str = "glm-4", temperature: float = 0.6) -> Dict[str, Any]:
        """
        通用对话调用
        
        Args:
            messages: 对话消息列表
            model: 模型名称，默认glm-4
            temperature: 温度参数
            
        Returns:
            {
                "success": bool,
                "data": str,
                "error": Optional[str],
                "model": str,
                "usage": Optional[Dict]
            }
        """
        try:
            start_time = time.time()
            
            response = self._make_request_with_timeout(
                self.client.chat.completions.create,
                model=model,
                messages=messages,
                temperature=temperature
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "data": response.choices[0].message.content,
                "error": None,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None
                },
                "elapsed_time": elapsed_time
            }
            
        except TimeoutError as e:
            return {
                "success": False,
                "data": None,
                "error": f"Request timeout: {str(e)}",
                "model": model,
                "usage": None,
                "elapsed_time": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"Chat request failed: {str(e)}",
                "model": model,
                "usage": None,
                "elapsed_time": 0
            }
    
    def chat_with_image(self, image_url: str, prompt: str, model: str = "glm-4v") -> Dict[str, Any]:
        """
        多模态图像理解
        
        Args:
            image_url: 图片URL或base64数据URL
            prompt: 提示词
            model: 模型名称，默认glm-4v
            
        Returns:
            {
                "success": bool,
                "data": str,
                "error": Optional[str],
                "model": str,
                "usage": Optional[Dict]
            }
        """
        try:
            start_time = time.time()
            
            response = self._make_request_with_timeout(
                self.client.chat.completions.create,
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                temperature=0.7
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "data": response.choices[0].message.content,
                "error": None,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None
                },
                "elapsed_time": elapsed_time
            }
            
        except TimeoutError as e:
            return {
                "success": False,
                "data": None,
                "error": f"Image chat timeout: {str(e)}",
                "model": model,
                "usage": None,
                "elapsed_time": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"Image chat failed: {str(e)}",
                "model": model,
                "usage": None,
                "elapsed_time": 0
            }
    
    def get_embedding(self, text: str, model: str = "embedding-2") -> Dict[str, Any]:
        """
        文本向量化
        
        Args:
            text: 输入文本
            model: 模型名称，默认embedding-2
            
        Returns:
            {
                "success": bool,
                "data": List[float],
                "error": Optional[str],
                "model": str,
                "dimension": int
            }
        """
        try:
            start_time = time.time()
            
            response = self._make_request_with_timeout(
                self.client.embeddings.create,
                model=model,
                input=[text]
            )
            
            elapsed_time = time.time() - start_time
            embedding = response.data[0].embedding
            
            return {
                "success": True,
                "data": embedding,
                "error": None,
                "model": model,
                "dimension": len(embedding),
                "elapsed_time": elapsed_time
            }
            
        except TimeoutError as e:
            return {
                "success": False,
                "data": None,
                "error": f"Embedding timeout: {str(e)}",
                "model": model,
                "dimension": 0,
                "elapsed_time": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"Embedding failed: {str(e)}",
                "model": model,
                "dimension": 0,
                "elapsed_time": 0
            }
    
    def speech_to_text(self, audio_file: str, model: str = "glm-asr-2512") -> Dict[str, Any]:
        """
        语音转文字
        
        Args:
            audio_file: 音频文件路径
            model: 模型名称，默认glm-asr-2512
            
        Returns:
            {
                "success": bool,
                "data": str,
                "error": Optional[str],
                "model": str
            }
        """
        try:
            if not os.path.exists(audio_file):
                return {
                    "success": False,
                    "data": None,
                    "error": f"Audio file not found: {audio_file}",
                    "model": model
                }
            
            start_time = time.time()
            
            with open(audio_file, "rb") as audio:
                response = self._make_request_with_timeout(
                    self.client.asr.create,
                    model=model,
                    audio=audio
                )
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "data": response.text,
                "error": None,
                "model": model,
                "elapsed_time": elapsed_time
            }
            
        except TimeoutError as e:
            return {
                "success": False,
                "data": None,
                "error": f"Speech recognition timeout: {str(e)}",
                "model": model,
                "elapsed_time": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"Speech recognition failed: {str(e)}",
                "model": model,
                "elapsed_time": 0
            }
    
    def text_to_speech(self, text: str, voice: str = "alloy", model: str = "glm-tts") -> Dict[str, Any]:
        """
        文字转语音
        
        Args:
            text: 输入文本
            voice: 语音类型，默认alloy
            model: 模型名称，默认glm-tts
            
        Returns:
            {
                "success": bool,
                "data": bytes,
                "error": Optional[str],
                "model": str,
                "voice": str
            }
        """
        try:
            start_time = time.time()
            
            response = self._make_request_with_timeout(
                self.client.tts.create,
                model=model,
                input=text,
                voice=voice
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "data": response.audio,
                "error": None,
                "model": model,
                "voice": voice,
                "elapsed_time": elapsed_time
            }
            
        except TimeoutError as e:
            return {
                "success": False,
                "data": None,
                "error": f"Text to speech timeout: {str(e)}",
                "model": model,
                "voice": voice,
                "elapsed_time": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"Text to speech failed: {str(e)}",
                "model": model,
                "voice": voice,
                "elapsed_time": 0
            }

# 单例模式
zhipu_client = ZhipuClient()