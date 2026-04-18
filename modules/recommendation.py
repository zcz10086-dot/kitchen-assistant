import json
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from .zhipu_client import ZhipuClient

class RecipeRecommender:
    """食谱推荐系统（GLM-4 + AI智能推荐）"""
    
    def __init__(self):
        self.client = ZhipuClient()
        # 示例食谱数据库（作为备用）
        self.recipe_database = [
            {
                "name": "番茄炒蛋",
                "ingredients": ["番茄", "鸡蛋", "盐", "油"],
                "difficulty": "简单",
                "cooking_time": "10分钟",
                "calories": 200,
                "category": "家常菜"
            },
            {
                "name": "红烧肉", 
                "ingredients": ["猪肉", "酱油", "糖", "姜", "葱"],
                "difficulty": "中等",
                "cooking_time": "60分钟",
                "calories": 450,
                "category": "肉类"
            }
        ]
        
    def recommend_recipes(self, available_ingredients: List[str], 
                         user_preferences: Dict[str, Any] = None,
                         max_recipes: int = 5) -> List[Dict[str, Any]]:
        """基于食材和用户偏好使用AI推荐食谱"""
        try:
            # 构建AI提示词
            diet_prefs = user_preferences.get('diet_preferences', []) if user_preferences else []
            allergies = user_preferences.get('allergies', []) if user_preferences else []
            spicy_level = user_preferences.get('spicy_level', '中等') if user_preferences else '中等'
            cooking_skill = user_preferences.get('cooking_skill', '中级') if user_preferences else '中级'
            
            prompt = f"""
            请基于以下信息推荐合适的菜品：
            
            **可用食材**: {', '.join(available_ingredients)}
            **饮食偏好**: {', '.join(diet_prefs) if diet_prefs else '无特殊偏好'}
            **忌口/过敏**: {', '.join(allergies) if allergies else '无'}
            **辣度偏好**: {spicy_level}
            **烹饪技能**: {cooking_skill}
            
            请推荐{max_recipes}道菜品，并按照以下JSON格式返回：
            {{
                "recommendations": [
                    {{
                        "name": "菜品名称",
                        "ingredients": ["主要食材1", "主要食材2"],
                        "cooking_steps": ["步骤1", "步骤2", "步骤3"],
                        "cooking_time": "预计烹饪时间",
                        "difficulty": "难度级别",
                        "calories": 估算热量,
                        "protein": "蛋白质含量",
                        "carbs": "碳水化合物含量", 
                        "fat": "脂肪含量",
                        "description": "菜品描述",
                        "tips": ["烹饪技巧1", "烹饪技巧2"]
                    }}
                ]
            }}
            """
            
            # 调用AI进行推荐
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.7
            )
            
            if result["success"]:
                try:
                    ai_response = json.loads(result["data"])
                    recommendations = ai_response.get("recommendations", [])
                    
                    # 添加缺失食材信息
                    for recipe in recommendations:
                        recipe['missing_ingredients'] = [
                            ing for ing in recipe.get('ingredients', [])
                            if ing not in available_ingredients
                        ]
                    
                    return recommendations
                except Exception as json_error:
                    print(f"JSON解析错误: {json_error}")
                    # 返回友好的错误信息而不是静默失败
                    return [{
                        "name": "AI推荐解析失败",
                        "ingredients": available_ingredients,
                        "cooking_steps": ["抱歉，AI推荐解析出现问题，请重试"],
                        "cooking_time": "未知",
                        "difficulty": "未知",
                        "calories": 0,
                        "description": f"JSON解析错误: {json_error}",
                        "tips": ["请检查网络连接或稍后重试"]
                    }]
            else:
                # AI调用失败时返回示例数据
                return self.recipe_database[:max_recipes]
                
        except Exception as e:
            print(f"AI recipe recommendation error: {e}")
            # 出错时返回示例数据
            return self.recipe_database[:max_recipes]

# 单例模式（注释掉，避免循环导入）
# recipe_recommender = RecipeRecommender()