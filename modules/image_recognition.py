import base64
import io
from typing import List, Dict, Any
from PIL import Image

try:
    from .zhipu_client import ZhipuClient
    CLIENT_AVAILABLE = True
except ImportError:
    try:
        from .zhipu_client_fallback import ZhipuClientFallback
        CLIENT_AVAILABLE = True
    except ImportError:
        CLIENT_AVAILABLE = False

class ImageRecognition:
    """食材识别模块（基于GLM-4V）"""
    
    def __init__(self):
        if CLIENT_AVAILABLE:
            try:
                self.client = ZhipuClient()
            except:
                self.client = ZhipuClientFallback()
        else:
            self.client = None
    
    def recognize_ingredients(self, image_data: bytes) -> Dict[str, Any]:
        """识别图片中的食材"""
        if not self.client:
            return {
                "success": False,
                "error": "AI客户端不可用",
                "ingredients": []
            }
            
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
            
            # 调用GLM-4V进行图像识别
            result = self.client.chat_with_image(image_url, prompt)
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "ingredients": []
                }
            
            # 解析AI返回的结果
            response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 尝试解析JSON
            try:
                import json
                # 从响应文本中提取JSON部分
                if "{" in response_text and "}" in response_text:
                    json_start = response_text.index("{")
                    json_end = response_text.rindex("}") + 1
                    json_str = response_text[json_start:json_end]
                    parsed_result = json.loads(json_str)
                    
                    return {
                        "success": True,
                        "ingredients": parsed_result.get("ingredients", []),
                        "total_count": parsed_result.get("total_count", 0),
                        "cooking_suggestions": parsed_result.get("cooking_suggestions", [])
                    }
                else:
                    # 如果无法解析JSON，返回原始文本
                    return {
                        "success": True,
                        "ingredients": [{"name": "无法解析AI响应", "quantity": "", "freshness": "", "confidence": 0.0}],
                        "total_count": 0,
                        "cooking_suggestions": ["请重试或手动输入食材"]
                    }
                    
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "JSON解析失败",
                    "ingredients": []
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"识别失败: {str(e)}",
                "ingredients": []
            }
    
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