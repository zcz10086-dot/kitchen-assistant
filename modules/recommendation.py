import json
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from .zhipu_client import ZhipuClient

class RecipeRecommender:
    """食谱推荐系统（GLM-4 + Embedding）"""
    
    def __init__(self):
        self.client = ZhipuClient()
        # 示例食谱数据库
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
            },
            {
                "name": "清炒时蔬",
                "ingredients": ["青菜", "蒜", "盐", "油"],
                "difficulty": "简单", 
                "cooking_time": "5分钟",
                "calories": 80,
                "category": "素菜"
            },
            {
                "name": "酸辣汤",
                "ingredients": ["豆腐", "木耳", "鸡蛋", "醋", "辣椒"],
                "difficulty": "中等",
                "cooking_time": "20分钟",
                "calories": 120,
                "category": "汤类"
            }
        ]
        
    def get_recipe_embeddings(self) -> Dict[str, List[float]]:
        """获取食谱的嵌入向量"""
        recipe_texts = []
        for recipe in self.recipe_database:
            text = f"{recipe['name']} {', '.join(recipe['ingredients'])} {recipe['category']}"
            recipe_texts.append(text)
        
        embeddings = []
        for text in recipe_texts:
            result = self.client.get_embedding(text)
            if result["success"]:
                embeddings.append(result["data"])
            else:
                # 如果获取嵌入失败，使用零向量
                embeddings.append([0.0] * 1024)
        
        recipe_embeddings = {}
        for i, recipe in enumerate(self.recipe_database):
            recipe_embeddings[recipe['name']] = embeddings[i]
            
        return recipe_embeddings
    
    def recommend_recipes(self, available_ingredients: List[str], 
                         max_recipes: int = 5) -> List[Dict[str, Any]]:
        """基于可用食材推荐食谱"""
        try:
            # 获取食材的嵌入向量
            ingredient_embeddings = []
            for ingredient in available_ingredients:
                result = self.client.get_embedding(ingredient)
                if result["success"]:
                    ingredient_embeddings.append(result["data"])
            
            # 计算食材向量的平均值
            if ingredient_embeddings:
                avg_ingredient_embedding = np.mean(ingredient_embeddings, axis=0)
            else:
                avg_ingredient_embedding = np.zeros(1024)  # 假设嵌入维度为1024
            
            # 获取食谱嵌入向量
            recipe_embeddings = self.get_recipe_embeddings()
            
            # 计算相似度
            similarities = {}
            for recipe_name, recipe_embedding in recipe_embeddings.items():
                similarity = cosine_similarity(
                    [avg_ingredient_embedding], 
                    [recipe_embedding]
                )[0][0]
                similarities[recipe_name] = similarity
            
            # 按相似度排序
            sorted_recipes = sorted(similarities.items(), 
                                  key=lambda x: x[1], reverse=True)
            
            # 返回推荐结果
            recommendations = []
            for recipe_name, similarity in sorted_recipes[:max_recipes]:
                recipe = next((r for r in self.recipe_database 
                             if r['name'] == recipe_name), None)
                if recipe:
                    recipe['similarity_score'] = float(similarity)
                    recipe['missing_ingredients'] = [ing for ing in recipe['ingredients'] 
                                                   if ing not in available_ingredients]
                    recommendations.append(recipe)
            
            return recommendations
            
        except Exception as e:
            raise Exception(f"Recipe recommendation failed: {str(e)}")
    
    def generate_custom_recipe(self, ingredients: List[str], 
                              preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """根据食材生成定制食谱"""
        try:
            prompt = f"""
            基于以下食材：{', '.join(ingredients)}，请生成一个详细的食谱。
            
            如果提供了偏好信息：{preferences if preferences else '无特殊偏好'}，请考虑这些偏好。
            
            请按照以下JSON格式返回：
            {{
                "recipe_name": "食谱名称",
                "ingredients": ["食材列表"],
                "steps": ["烹饪步骤"],
                "cooking_time": "烹饪时间",
                "difficulty": "难度级别",
                "tips": ["烹饪小贴士"]
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
                    # 如果无法解析JSON，返回结构化数据
                    return {
                        "recipe_name": "AI生成食谱",
                        "ingredients": ingredients,
                        "steps": [result["data"]],
                        "cooking_time": "未知",
                        "difficulty": "未知",
                        "tips": ["请根据实际情况调整"],
                        "raw_response": result["data"]
                    }
            else:
                raise Exception(f"Custom recipe generation failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Custom recipe generation failed: {str(e)}")
    
    def get_cooking_instructions(self, recipe_name: str) -> Dict[str, Any]:
        """获取具体食谱的详细烹饪指导"""
        try:
            prompt = f"""
            请为"{recipe_name}"提供详细的烹饪指导。
            
            请按照以下JSON格式返回：
            {{
                "recipe_name": "{recipe_name}",
                "preparation": ["准备步骤"],
                "cooking_steps": ["烹饪步骤"],
                "key_points": ["关键要点"],
                "common_mistakes": ["常见错误"],
                "serving_suggestions": ["上菜建议"]
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
                        "recipe_name": recipe_name,
                        "preparation": [],
                        "cooking_steps": [result["data"]],
                        "key_points": [],
                        "common_mistakes": [],
                        "serving_suggestions": [],
                        "raw_response": result["data"]
                    }
            else:
                raise Exception(f"Cooking instructions failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Cooking instructions failed: {str(e)}")

# 单例模式
recipe_recommender = RecipeRecommender()