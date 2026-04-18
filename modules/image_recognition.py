import base64
import io
from typing import List, Dict, Any
from PIL import Image
from .zhipu_client import ZhipuClient

class ImageRecognition:
    """食材识别模块（基于GLM-4V）"""
    
    def __init__(self):
        self.client = ZhipuClient()
    
    def recognize_ingredients(self, image_data: bytes) -> Dict[str, Any]:
        """识别图片中的食材"""
        try:
            # 将图片转换为base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_b64}"
            
            prompt = """请仔细识别这张图片中的食材。
            请按照以下格式返回JSON结果：
            {
                "ingredients": [
                    {
                        "name": "食材名称",
                        "quantity": "估计数量/重量",
                        "freshness": "新鲜程度（新鲜/一般/不新鲜）",
                        "confidence": "识别置信度（0-1）"
                    }
                ],
                "total_count": 食材总数,
                "cooking_suggestions": ["基于这些食材的烹饪建议"]
            }
            """
            
            result = self.client.chat_with_image(image_url, prompt)
            
            if result["success"]:
                # 尝试解析JSON结果
                try:
                    import json
                    return json.loads(result["data"])
                except:
                    # 如果无法解析JSON，返回原始文本
                    return {
                        "ingredients": [],
                        "total_count": 0,
                        "cooking_suggestions": [result["data"]],
                        "raw_result": result["data"]
                    }
            else:
                raise Exception(f"Image recognition failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Image recognition failed: {str(e)}")
    
    def analyze_food_safety(self, image_data: bytes) -> Dict[str, Any]:
        """分析食品安全性"""
        try:
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_b64}"
            
            prompt = """请分析这张图片中食物的安全性。
            请按照以下格式返回JSON结果：
            {
                "safety_level": "安全级别（安全/警告/危险）",
                "issues": ["发现的安全问题"],
                "recommendations": ["安全建议"],
                "storage_advice": "储存建议"
            }
            """
            
            result = self.client.chat_with_image(image_url, prompt)
            
            if result["success"]:
                try:
                    import json
                    return json.loads(result["data"])
                except:
                    return {
                        "safety_level": "未知",
                        "issues": [],
                        "recommendations": [result["data"]],
                        "raw_result": result["data"]
                    }
            else:
                raise Exception(f"Food safety analysis failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Food safety analysis failed: {str(e)}")
    
    def estimate_calories(self, image_data: bytes) -> Dict[str, Any]:
        """估算食物热量"""
        try:
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_b64}"
            
            prompt = """请估算这张图片中食物的热量（卡路里）。
            请按照以下格式返回JSON结果：
            {
                "estimated_calories": 估算热量,
                "portion_size": "份量估计",
                "main_ingredients": ["主要食材"],
                "nutrition_breakdown": {
                    "protein": "蛋白质含量",
                    "carbs": "碳水化合物含量", 
                    "fat": "脂肪含量"
                }
            }
            """
            
            result = self.client.chat_with_image(image_url, prompt)
            
            if result["success"]:
                try:
                    import json
                    return json.loads(result["data"])
                except:
                    return {
                        "estimated_calories": 0,
                        "portion_size": "未知",
                        "main_ingredients": [],
                        "nutrition_breakdown": {},
                        "raw_result": result["data"]
                    }
            else:
                raise Exception(f"Calorie estimation failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Calorie estimation failed: {str(e)}")

# 单例模式
image_recognizer = ImageRecognition()