"""
备用的智谱AI客户端
当zhipuai库安装失败时使用，通过requests直接调用API
"""

import json
import time
import requests
import base64
from typing import Dict, List, Any, Optional
from PIL import Image
import io


class ZhipuClientFallback:
    """备用的智谱AI客户端（不依赖zhipuai库）"""
    
    def __init__(self):
        """初始化备用客户端"""
        import os
        self.api_key = os.getenv('ZHIPU_API_KEY')
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY环境变量未设置")
    
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """发送API请求"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API请求失败: {str(e)}"}
    
    def chat(self, messages: List[Dict], model: str = "glm-4", temperature: float = 0.6) -> Dict:
        """通用对话调用"""
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        return self._make_request("/chat/completions", data)
    
    def chat_with_image(self, image_url: str, prompt: str) -> Dict:
        """多模态图像理解"""
        # 下载图像并转换为base64
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = base64.b64encode(response.content).decode('utf-8')
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }
            ]
            
            return self.chat(messages, model="glm-4v")
        except Exception as e:
            return {"error": f"图像处理失败: {str(e)}"}
    
    def get_embedding(self, text: str) -> Dict:
        """文本向量化"""
        data = {
            "model": "embedding-2",
            "input": text
        }
        return self._make_request("/embeddings", data)
    
    def speech_to_text(self, audio_file: str) -> Dict:
        """语音转文字（云端环境返回提示）"""
        return {
            "success": False,
            "error": "云端环境：语音转文字功能受限",
            "data": "请使用文本输入"
        }
    
    def text_to_speech(self, text: str) -> Dict:
        """文字转语音（云端环境返回提示）"""
        return {
            "success": False,
            "error": "云端环境：文字转语音功能受限",
            "data": "请使用文本显示"
        }


# 创建备用客户端实例
zhipu_client_fallback = ZhipuClientFallback()