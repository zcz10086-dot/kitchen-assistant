"""
云端环境专用的语音助手模块
避免导入音频相关依赖，适配Streamlit Cloud环境
"""

import json
import time
from typing import Dict, Any, Optional


class VoiceAssistantCloud:
    """云端环境专用的语音助手（无音频功能）"""
    
    def __init__(self, client=None):
        """初始化云端语音助手"""
        self.client = client
        self.sample_rate = 16000
        
    def record_and_recognize(self, duration: int = 5, language: str = "zh-CN") -> Optional[str]:
        """云端环境：返回提示信息（无录音功能）"""
        return "云端环境：语音功能受限，请使用文本输入"
    
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
        for chinese_cmd, english_cmd in commands.items():
            if any(word in recognized_text for word in chinese_cmd):
                return {
                    "command": english_cmd,
                    "original_text": recognized_text,
                    "confidence": 0.7
                }
        
        return {"command": "unknown", "original_text": recognized_text, "confidence": 0.0}
    
    def provide_chinese_feedback(self, command_result: Dict[str, Any]):
        """提供中文反馈（云端环境：文本反馈）"""
        command = command_result["command"]
        feedback_messages = {
            "next_step": "好的，下一步",
            "pause": "已暂停",
            "continue": "继续烹饪",
            "restart": "重新开始",
            "add_time": "增加5分钟",
            "reduce_time": "减少5分钟",
            "view_steps": "显示烹饪步骤",
            "view_nutrition": "显示营养信息",
            "help": "帮助信息",
            "exit": "退出语音助手"
        }
        
        feedback = feedback_messages.get(command, "命令已执行")
        print(f"语音反馈: {feedback}")
        
    def _post_process_chinese_text(self, text: str) -> str:
        """中文文本后处理"""
        if not text:
            return ""
        
        # 简单的文本清理
        text = text.strip()
        
        # 移除常见的语音识别错误
        common_errors = {
            "呃": "",
            "嗯": "",
            "啊": "",
            "那个": ""
        }
        
        for error, replacement in common_errors.items():
            text = text.replace(error, replacement)
        
        return text.strip()
    
    def get_available_voices(self):
        """获取可用语音（云端环境返回空列表）"""
        return []
    
    def set_voice(self, voice_name: str):
        """设置语音（云端环境无操作）"""
        pass


# 创建云端环境专用的语音助手实例
voice_assistant_cloud = VoiceAssistantCloud()