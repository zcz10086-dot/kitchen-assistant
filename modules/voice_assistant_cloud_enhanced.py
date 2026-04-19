"""
云端环境增强版语音助手模块
支持云端音频功能：TTS和文件上传ASR
"""

import json
import time
import base64
import io
from typing import Dict, Any, Optional, List


class VoiceAssistantCloudEnhanced:
    """云端环境增强版语音助手（支持云端音频功能）"""
    
    def __init__(self, client=None):
        """初始化云端语音助手"""
        self.client = client
        self.sample_rate = 16000
        
    def text_to_speech(self, text: str, voice: str = None) -> Dict[str, Any]:
        """
        云端TTS功能 - 完全支持中文
        
        Args:
            text: 要合成的文本
            voice: 语音类型，默认使用中文语音
            
        Returns:
            包含音频数据和URL的字典
        """
        # 如果没有指定语音，使用默认中文语音
        if voice is None:
            voice = "zh-CN-XiaoxiaoNeural"
        """
        云端TTS功能 - 完全支持
        
        Args:
            text: 要合成的文本
            voice: 语音类型
            
        Returns:
            {
                "success": bool,
                "audio_data": base64编码的音频数据,
                "audio_url": data URL,
                "error": Optional[str]
            }
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "error": "AI客户端不可用",
                    "audio_data": None,
                    "audio_url": None
                }
            
            # 调用智谱AI TTS API
            result = self.client.text_to_speech(text)
            
            if result["success"]:
                # 返回base64编码的音频数据和data URL
                audio_data = result["data"]
                audio_url = f"data:audio/mpeg;base64,{audio_data}"
                
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "audio_url": audio_url,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "TTS合成失败"),
                    "audio_data": None,
                    "audio_url": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"TTS异常: {str(e)}",
                "audio_data": None,
                "audio_url": None
            }
    
    def speech_to_text_file(self, audio_file) -> Dict[str, Any]:
        """
        云端ASR功能 - 通过文件上传支持
        
        Args:
            audio_file: 上传的音频文件对象
            
        Returns:
            {
                "success": bool,
                "text": 识别结果,
                "error": Optional[str]
            }
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "text": "",
                    "error": "AI客户端不可用"
                }
            
            # 保存临时文件并调用ASR API
            import tempfile
            import os
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # 将上传的文件内容写入临时文件
                audio_bytes = audio_file.read()
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # 调用智谱AI ASR API
            result = self.client.speech_to_text(temp_file_path)
            
            # 清理临时文件
            os.unlink(temp_file_path)
            
            if result["success"]:
                return {
                    "success": True,
                    "text": result["data"],
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "text": "",
                    "error": result.get("error", "语音识别失败")
                }
                
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": f"ASR异常: {str(e)}"
            }
    
    def record_and_recognize(self, duration: int = 5, language: str = "zh-CN") -> Optional[str]:
        """云端环境：支持文件上传方式的语音识别"""
        return "云端环境：请上传音频文件进行语音识别（支持WAV/MP3格式）"
    
    def recognize_chinese_commands(self, recognized_text: str) -> Dict[str, Any]:
        """识别中文语音命令（云端环境可用）"""
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
        lower_text = recognized_text.lower()
        if "下一步" in lower_text or "继续" in lower_text:
            return {"command": "next_step", "original_text": recognized_text, "confidence": 0.7}
        elif "暂停" in lower_text or "停止" in lower_text:
            return {"command": "pause", "original_text": recognized_text, "confidence": 0.7}
        elif "帮助" in lower_text:
            return {"command": "help", "original_text": recognized_text, "confidence": 0.8}
        
        return {"command": "unknown", "original_text": recognized_text, "confidence": 0.0}
    
    def provide_chinese_feedback(self, command_result: Dict[str, Any]) -> str:
        """提供中文语音反馈"""
        command = command_result.get("command", "unknown")
        
        feedback_map = {
            "next_step": "好的，执行下一步",
            "pause": "已暂停",
            "continue": "继续执行",
            "restart": "重新开始",
            "add_time": "已增加时间",
            "reduce_time": "已减少时间",
            "view_steps": "显示步骤",
            "view_nutrition": "显示营养信息",
            "help": "显示帮助信息",
            "exit": "退出应用",
            "unknown": "抱歉，没有理解您的指令"
        }
        
        return feedback_map.get(command, "指令执行完成")
    
    def get_supported_audio_formats(self) -> List[str]:
        """获取支持的音频格式"""
        return ["wav", "mp3", "m4a", "ogg"]
    
    def validate_audio_file(self, audio_file) -> Dict[str, Any]:
        """验证音频文件"""
        try:
            # 检查文件大小（限制10MB）
            max_size = 10 * 1024 * 1024  # 10MB
            audio_file.seek(0, 2)  # 移动到文件末尾
            file_size = audio_file.tell()
            audio_file.seek(0)  # 回到文件开头
            
            if file_size > max_size:
                return {
                    "valid": False,
                    "error": f"文件大小超过限制（最大10MB）"
                }
            
            # 检查文件类型
            filename = getattr(audio_file, 'name', 'unknown')
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            supported_formats = self.get_supported_audio_formats()
            if file_ext not in supported_formats:
                return {
                    "valid": False,
                    "error": f"不支持的文件格式，请使用: {', '.join(supported_formats)}"
                }
            
            return {
                "valid": True,
                "file_size": file_size,
                "file_format": file_ext
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"文件验证失败: {str(e)}"
            }
    
    def play_audio(self, audio_data: str) -> Dict[str, Any]:
        """播放音频（云端环境：返回音频URL）"""
        try:
            audio_url = f"data:audio/mpeg;base64,{audio_data}"
            return {
                "success": True,
                "audio_url": audio_url,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "audio_url": None,
                "error": f"音频播放失败: {str(e)}"
            }