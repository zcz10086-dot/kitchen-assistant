import json
from typing import Dict, List, Any
from .zhipu_client import ZhipuClient

class NutritionAnalyzer:
    """营养分析模块（基于GLM-4）"""
    
    def __init__(self):
        self.client = ZhipuClient()
    
    def analyze_nutrition(self, ingredients: List[str], 
                         portion_size: str = "标准份") -> Dict[str, Any]:
        """分析食材的营养成分"""
        try:
            prompt = f"""
            请分析以下食材的营养成分（份量：{portion_size}）：
            {', '.join(ingredients)}
            
            请按照以下JSON格式返回详细分析：
            {{
                "total_calories": 总卡路里,
                "macronutrients": {{
                    "protein": "蛋白质含量",
                    "carbohydrates": "碳水化合物含量",
                    "fat": "脂肪含量",
                    "fiber": "膳食纤维含量"
                }},
                "micronutrients": {{
                    "vitamins": ["主要维生素"],
                    "minerals": ["主要矿物质"]
                }},
                "health_benefits": ["健康益处"],
                "dietary_recommendations": ["饮食建议"],
                "allergy_warnings": ["过敏警告"]
            }}
            """
            
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.7
            )
            
            if result["success"]:
                try:
                    return json.loads(result["data"])
                except:
                    return {
                        "total_calories": 0,
                        "macronutrients": {},
                        "micronutrients": {},
                        "health_benefits": [result["data"]],
                        "dietary_recommendations": [],
                        "allergy_warnings": [],
                        "raw_response": result["data"]
                    }
            else:
                print(f"营养分析失败: {result['error']}")
                return {
                    "total_calories": 0,
                    "macronutrients": {},
                    "micronutrients": {},
                    "health_benefits": [f"营养分析失败: {result['error']}"],
                    "dietary_recommendations": [],
                    "allergy_warnings": [],
                    "raw_response": f"营养分析失败: {result['error']}"
                }
                
        except Exception as e:
            print(f"营养分析异常: {str(e)}")
            return {
                "total_calories": 0,
                "macronutrients": {},
                "micronutrients": {},
                "health_benefits": [f"营养分析异常: {str(e)}"],
                "dietary_recommendations": [],
                "allergy_warnings": [],
                "raw_response": f"营养分析异常: {str(e)}"
            }
    
    def calculate_daily_intake(self, meals: List[Dict[str, Any]], 
                              user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """计算每日营养摄入量"""
        try:
            meals_info = "\n".join([
                f"{meal.get('name', '未知餐食')}: {', '.join(meal.get('ingredients', []))}"
                for meal in meals
            ])
            
            profile_info = user_profile or {
                "age": "未知",
                "gender": "未知", 
                "activity_level": "未知",
                "dietary_goals": "未知"
            }
            
            prompt = f"""
            基于以下餐食信息：
            {meals_info}
            
            和用户档案：{profile_info}
            
            请计算每日营养摄入量并给出建议：
            
            请按照以下JSON格式返回：
            {{
                "total_daily_calories": 总卡路里,
                "nutrient_breakdown": {{
                    "protein": {{"amount": "蛋白质总量", "percentage": "占比"}},
                    "carbs": {{"amount": "碳水总量", "percentage": "占比"}},
                    "fat": {{"amount": "脂肪总量", "percentage": "占比"}}
                }},
                "recommended_intake": {{
                    "calories": "推荐卡路里",
                    "protein": "推荐蛋白质",
                    "carbs": "推荐碳水",
                    "fat": "推荐脂肪"
                }},
                "deficiencies": ["缺乏的营养素"],
                "excesses": ["过量的营养素"],
                "improvement_suggestions": ["改进建议"]
            }}
            """
            
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.7
            )
            
            if result["success"]:
                try:
                    return json.loads(result["data"])
                except:
                    return {
                        "total_daily_calories": 0,
                        "nutrient_breakdown": {},
                        "recommended_intake": {},
                        "deficiencies": [],
                        "excesses": [],
                        "improvement_suggestions": [result["data"]],
                        "raw_response": result["data"]
                    }
            else:
                raise Exception(f"Daily intake calculation failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Daily intake calculation failed: {str(e)}")
    
    def get_diet_plan(self, user_goals: Dict[str, Any], 
                      available_ingredients: List[str]) -> Dict[str, Any]:
        """生成个性化饮食计划"""
        try:
            prompt = f"""
            为用户制定个性化饮食计划：
            
            用户目标：{user_goals}
            可用食材：{', '.join(available_ingredients)}
            
            请按照以下JSON格式返回7天饮食计划：
            {{
                "weekly_plan": {{
                    "monday": {{
                        "breakfast": {{"meal": "早餐", "calories": 热量}},
                        "lunch": {{"meal": "午餐", "calories": 热量}},
                        "dinner": {{"meal": "晚餐", "calories": 热量}},
                        "snacks": ["零食建议"]
                    }},
                    "tuesday": {{...}},
                    // 继续其他天...
                }},
                "total_weekly_calories": 周总热量,
                "shopping_list": ["需要采购的食材"],
                "preparation_tips": ["准备建议"]
            }}
            """
            
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.8
            )
            
            if result["success"]:
                try:
                    return json.loads(result["data"])
                except:
                    return {
                        "weekly_plan": {},
                        "total_weekly_calories": 0,
                        "shopping_list": [],
                        "preparation_tips": [result["data"]],
                        "raw_response": result["data"]
                    }
            else:
                raise Exception(f"Diet plan generation failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Diet plan generation failed: {str(e)}")
    
    def food_compatibility_check(self, food1: str, food2: str) -> Dict[str, Any]:
        """检查食物搭配兼容性"""
        try:
            prompt = f"""
            请分析"{food1}"和"{food2}"的食物搭配兼容性：
            
            请按照以下JSON格式返回：
            {{
                "compatibility_score": "兼容性评分（1-10）",
                "benefits": ["搭配益处"],
                "risks": ["搭配风险"],
                "best_combination_method": "最佳搭配方式",
                "alternative_suggestions": ["替代搭配建议"]
            }}
            """
            
            result = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4",
                temperature=0.7
            )
            
            if result["success"]:
                try:
                    return json.loads(result["data"])
                except:
                    return {
                        "compatibility_score": "未知",
                        "benefits": [],
                        "risks": [],
                        "best_combination_method": "未知",
                        "alternative_suggestions": [result["data"]],
                        "raw_response": result["data"]
                    }
            else:
                raise Exception(f"Food compatibility check failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Food compatibility check failed: {str(e)}")

# 单例模式
nutrition_analyzer = NutritionAnalyzer()