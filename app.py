import streamlit as st
import base64
import io
import json
import tempfile
import time
import threading
from PIL import Image

# 基础导入（确保应用能启动）
zhipu_client = None
image_recognizer = None
recipe_recommender = None
nutrition_analyzer = None

# 尝试导入AI模块（如果可用）
try:
    from modules.zhipu_client import ZhipuClient
    zhipu_client = ZhipuClient()
    print("✅ zhipuai库可用")
    
    from modules.image_recognition import ImageRecognition
    from modules.recommendation import RecipeRecommender
    from modules.nutrition import NutritionAnalyzer
    
    image_recognizer = ImageRecognition()
    recipe_recommender = RecipeRecommender()
    nutrition_analyzer = NutritionAnalyzer()
    
    print("✅ 所有AI模块初始化成功")
    AI_ENABLED = True
except ImportError as e:
    print(f"⚠️ AI功能受限: {e}")
    print("💡 应用将以基础模式运行")
    AI_ENABLED = False

# 音频功能依赖检查
try:
    from modules.voice_assistant import VoiceAssistant
    from modules.tts_assistant import TTSEngine
    voice_assistant = VoiceAssistant()
    tts_engine = TTSEngine()
    AUDIO_ENABLED = True
except ImportError as e:
    print(f"完整音频功能不可用：{e}")
    # 使用云端环境专用的语音助手
    try:
        from modules.voice_assistant_cloud import VoiceAssistantCloud
        voice_assistant = VoiceAssistantCloud()
        tts_engine = None
        AUDIO_ENABLED = False
        print("使用云端环境专用的语音助手")
    except ImportError:
        print("云端语音助手也不可用")
        AUDIO_ENABLED = False
        voice_assistant = None
        tts_engine = None

# 页面配置
st.set_page_config(
    page_title="智能厨房助手",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS样式
st.markdown("""
<style>
.main-header {
    font-size: 2.5em;
    font-weight: bold;
    text-align: center;
    color: #FF6B6B;
    margin-bottom: 1em;
}
.timer-display {
    font-size: 3em;
    font-weight: bold;
    text-align: center;
    color: #4ECDC4;
    margin: 0.5em 0;
}
</style>
""", unsafe_allow_html=True)

# 初始化session state
def init_session_state():
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'diet_preferences': [],
            'allergies': [],
            'spicy_level': '中等',
            'cooking_skill': '中级'
        }
    
    if 'current_recipe' not in st.session_state:
        st.session_state.current_recipe = None
    
    if 'timer_active' not in st.session_state:
        st.session_state.timer_active = False
    
    if 'timer_seconds' not in st.session_state:
        st.session_state.timer_seconds = 0
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    
    if 'recognized_ingredients' not in st.session_state:
        st.session_state.recognized_ingredients = []
    
    if 'recommended_recipes' not in st.session_state:
        st.session_state.recommended_recipes = []
    
    # 新增功能的状态管理
    if 'ingredient_inventory' not in st.session_state:
        st.session_state.ingredient_inventory = []
    
    if 'shopping_list' not in st.session_state:
        st.session_state.shopping_list = []
    
    if 'favorite_recipes' not in st.session_state:
        st.session_state.favorite_recipes = []
    
    if 'nutrition_goals' not in st.session_state:
        st.session_state.nutrition_goals = {
            'daily_calories': 2000,
            'protein_goal': 50,
            'carb_goal': 250,
            'fat_goal': 70
        }
    
    if 'meal_plan' not in st.session_state:
        st.session_state.meal_plan = {}
    
    if 'cooking_history' not in st.session_state:
        st.session_state.cooking_history = []

# 侧边栏 - 用户偏好设置
def render_sidebar():
    with st.sidebar:
        st.header("👤 用户偏好设置")
        
        # 饮食偏好
        diet_options = ["素食", "低脂", "低糖", "高蛋白", "低碳水", "无麸质"]
        selected_diets = st.multiselect(
            "饮食偏好",
            diet_options,
            default=st.session_state.user_preferences['diet_preferences']
        )
        st.session_state.user_preferences['diet_preferences'] = selected_diets
        
        # 忌口/过敏
        allergy_options = ["海鲜", "坚果", "乳制品", "鸡蛋", "大豆", "小麦"]
        selected_allergies = st.multiselect(
            "忌口/过敏",
            allergy_options,
            default=st.session_state.user_preferences['allergies']
        )
        st.session_state.user_preferences['allergies'] = selected_allergies
        
        # 辣度偏好
        spicy_level = st.select_slider(
            "辣度偏好",
            options=["不辣", "微辣", "中等", "重辣", "特辣"],
            value=st.session_state.user_preferences['spicy_level']
        )
        st.session_state.user_preferences['spicy_level'] = spicy_level
        
        # 烹饪技能
        cooking_skill = st.selectbox(
            "烹饪技能",
            ["新手", "初级", "中级", "高级", "专业"],
            index=["新手", "初级", "中级", "高级", "专业"].index(st.session_state.user_preferences['cooking_skill'])
        )
        st.session_state.user_preferences['cooking_skill'] = cooking_skill
        
        st.divider()
        
        # 语音设置
        st.header("🎤 语音设置")
        enable_voice = st.checkbox("启用语音功能", value=True)
        if enable_voice and tts_engine:
            voice_type = st.selectbox("语音类型", tts_engine.get_available_voices())

# 食材识别Tab
def render_ingredient_recognition():
    st.header("📷 食材识别")
    
    if not AI_ENABLED:
        st.warning("⚠️ AI功能当前不可用")
        st.info("💡 请手动输入食材清单")
        
        # 手动输入替代方案
        manual_ingredients = st.text_area("手动输入食材清单（用逗号分隔）", 
                                         placeholder="例如：西红柿,鸡蛋,洋葱,土豆")
        
        if st.button("分析食材", use_container_width=True):
            if manual_ingredients.strip():
                ingredients_list = [ing.strip() for ing in manual_ingredients.split(",") if ing.strip()]
                
                st.success(f"✅ 识别到 {len(ingredients_list)} 种食材")
                
                # 显示食材清单
                st.subheader("📋 食材清单")
                for i, ingredient in enumerate(ingredients_list, 1):
                    st.write(f"{i}. {ingredient}")
                
                # 提供基础建议
                st.subheader("💡 烹饪建议")
                st.write("基于您输入的食材，建议尝试以下菜品：")
                st.write("- 炒菜类：简单快炒")
                st.write("- 汤类：营养汤品")
                st.write("- 凉拌类：清爽凉菜")
            else:
                st.error("❌ 请输入食材清单")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "上传食材图片", 
            type=['png', 'jpg', 'jpeg'],
            help="支持PNG、JPG、JPEG格式"
        )
        
        if uploaded_file is not None:
            # 显示图片
            image = Image.open(uploaded_file)
            st.image(image, caption="上传的食材图片", use_column_width=True)
            
            # 识别按钮
            if st.button("🔍 识别食材", use_container_width=True):
                with st.spinner("正在识别食材..."):
                    try:
                        # 读取图片数据
                        image_data = uploaded_file.getvalue()
                        
                        # 调用AI识别
                        result = image_recognizer.recognize_ingredients(image_data)
                        
                        # 加强API调用结果检查
                        if 'ingredients' in result and result['ingredients']:
                            st.session_state.recognized_ingredients = result['ingredients']
                            st.success(f"✅ 识别到 {len(result['ingredients'])} 种食材")
                        elif 'raw_result' in result:
                            # 如果只有原始结果，说明API调用成功但解析失败
                            st.warning("⚠️ AI识别成功但解析失败，显示原始结果")
                            st.info(f"AI回复: {result['raw_result'][:200]}...")
                            st.session_state.recognized_ingredients = []
                        else:
                            st.error("❌ 识别失败，请检查网络连接或重试")
                            
                    except Exception as e:
                        st.error(f"❌ 识别失败: {str(e)}")
    
    with col2:
        st.subheader("📋 识别结果")
        
        if st.session_state.recognized_ingredients:
            for ingredient in st.session_state.recognized_ingredients:
                st.write(f"🍎 **{ingredient.get('name', '未知')}**")
                st.write(f"  数量: {ingredient.get('quantity', '未知')}")
                st.write(f"  新鲜度: {ingredient.get('freshness', '未知')}")
                st.divider()
        else:
            st.info("👆 请上传图片识别食材")

# 推荐菜品Tab - 适配AI功能状态
def render_recipe_recommendation():
    st.header("🍽️ 推荐菜品")
    
    if not AI_ENABLED:
        st.warning("⚠️ AI功能当前不可用")
        st.info("💡 使用基础菜品推荐")
        
        # 手动输入食材
        manual_ingredients = st.text_area("输入可用食材（用逗号分隔）", 
                                         placeholder="例如：西红柿,鸡蛋,洋葱,土豆")
        
        if st.button("🔍 基础推荐菜品", use_container_width=True):
            if manual_ingredients.strip():
                ingredients_list = [ing.strip() for ing in manual_ingredients.split(",") if ing.strip()]
                
                # 基础推荐逻辑
                basic_recipes = [
                    {
                        "name": "家常炒菜",
                        "difficulty": "简单",
                        "cooking_time": "15分钟",
                        "flavor": "咸鲜",
                        "calories": "约200大卡",
                        "description": "简单快炒，保留食材原味",
                        "cooking_steps": ["热锅凉油", "爆香调料", "下入食材翻炒", "调味出锅"],
                        "tips": ["火候要足", "快速翻炒"]
                    },
                    {
                        "name": "营养汤品", 
                        "difficulty": "中等",
                        "cooking_time": "30分钟",
                        "flavor": "鲜美",
                        "calories": "约150大卡",
                        "description": "营养丰富的汤品",
                        "cooking_steps": ["准备食材", "炖煮汤底", "加入主料", "调味出锅"],
                        "tips": ["小火慢炖", "注意火候"]
                    },
                    {
                        "name": "清爽凉拌",
                        "difficulty": "简单", 
                        "cooking_time": "10分钟",
                        "flavor": "清爽",
                        "calories": "约100大卡",
                        "description": "夏日清爽凉菜",
                        "cooking_steps": ["食材处理", "调制酱汁", "拌匀装盘"],
                        "tips": ["酱汁要均匀", "冷藏后更佳"]
                    }
                ]
                
                st.session_state.recommended_recipes = basic_recipes
                st.success(f"✅ 为您推荐了 {len(basic_recipes)} 道基础菜品")
            else:
                st.error("❌ 请输入食材清单")
        
        # 显示推荐结果
        if st.session_state.recommended_recipes:
            st.subheader("📋 基础菜品推荐")
            for i, recipe in enumerate(st.session_state.recommended_recipes, 1):
                with st.expander(f"{i}. {recipe.get('name', '未知菜品')}", expanded=i==1):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**难度:** {recipe.get('difficulty', '未知')}")
                        st.write(f"**时间:** {recipe.get('cooking_time', '未知')}")
                    
                    with col2:
                        st.write(f"**口味:** {recipe.get('flavor', '未知')}")
                        st.write(f"**热量:** {recipe.get('calories', '未知')}")
                    
                    # 菜品描述
                    if recipe.get('description'):
                        st.write(f"**描述:** {recipe['description']}")
                    
                    # 烹饪步骤
                    if recipe.get('cooking_steps'):
                        st.write("**烹饪步骤:**")
                        for j, step in enumerate(recipe['cooking_steps'], 1):
                            st.write(f"{j}. {step}")
                    
                    # 烹饪技巧
                    if 'tips' in recipe and recipe['tips']:
                        st.write("**烹饪技巧:**")
                        for tip in recipe['tips']:
                            st.write(f"💡 {tip}")
        return
    
    # AI功能可用时的完整逻辑
    # 获取识别的食材
    ingredient_names = [ing.get('name', '') for ing in st.session_state.recognized_ingredients]
    
    if not ingredient_names:
        st.info("👆 请先在'食材识别'页面识别食材")
        return
    
    st.write(f"**可用食材:** {', '.join(ingredient_names)}")
    
    # 推荐设置
    col1, col2 = st.columns(2)
    
    with col1:
        max_recipes = st.slider("推荐数量", 1, 10, 5)
    
    with col2:
        if st.button("🔄 重新推荐"):
            st.session_state.recommended_recipes = []
    
    # AI推荐按钮
    if st.button("🔍 AI智能推荐菜品", use_container_width=True):
        with st.spinner("正在使用AI为您推荐合适的菜品..."):
            try:
                # 获取AI推荐
                recommendations = recipe_recommender.recommend_recipes(
                    ingredient_names, 
                    st.session_state.user_preferences,
                    max_recipes
                )
                
                st.session_state.recommended_recipes = recommendations
                
                # 加强API调用结果检查
                if recommendations:
                    # 检查是否是错误信息
                    if len(recommendations) == 1 and 'AI推荐解析失败' in str(recommendations[0].get('name', '')):
                        st.error("❌ AI推荐解析失败，请重试")
                        st.info(f"错误信息: {recommendations[0].get('description', '未知错误')}")
                    else:
                        st.success(f"✅ AI为您推荐了 {len(recommendations)} 道菜品")
                else:
                    st.warning("⚠️ AI未找到合适的菜品推荐")
                    
            except Exception as e:
                st.error(f"❌ AI推荐失败: {str(e)}")
    
    # 显示AI推荐结果
    if st.session_state.recommended_recipes:
        st.subheader("🤖 AI推荐菜品")
        
        for i, recipe in enumerate(st.session_state.recommended_recipes, 1):
            with st.expander(f"{i}. {recipe.get('name', '未知菜品')}", expanded=i==1):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**难度:** {recipe.get('difficulty', '未知')}")
                    st.write(f"**时间:** {recipe.get('cooking_time', '未知')}")
                
                with col2:
                    st.write(f"**热量:** {recipe.get('calories', '未知')} 卡路里")
                    st.write(f"**蛋白质:** {recipe.get('protein', '未知')}g")
                
                with col3:
                    if st.button(f"👨‍🍳 选择此菜品", key=f"select_{i}"):
                        st.session_state.current_recipe = recipe
                        st.success(f"✅ 已选择: {recipe.get('name', '未知菜品')}")
                
                # 食材清单
                st.write("**食材清单:**")
                for ingredient in recipe.get('ingredients', []):
                    if ingredient in ingredient_names:
                        st.write(f"✅ {ingredient}")
                    else:
                        st.write(f"❌ {ingredient}")
                
                # 菜品描述
                if 'description' in recipe:
                    st.write(f"**描述:** {recipe['description']}")
                
                # 烹饪技巧
                if 'tips' in recipe and recipe['tips']:
                    st.write("**烹饪技巧:**")
                    for tip in recipe['tips']:
                        st.write(f"💡 {tip}")

# 语音助手Tab - 适配云环境的AI语音助手
def render_voice_assistant():
    st.header("🎤 AI语音助手（中文支持）")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗣️ 中文语音/文本控制")
        
        if not AUDIO_ENABLED:
            st.warning("⚠️ 云端环境：音频功能受限，使用文本输入替代")
            
            # 文本输入替代语音输入
            text_input = st.text_area("📝 输入中文语音命令（云端环境使用）", 
                                    placeholder="例如：下一步、暂停、查看步骤等",
                                    height=100)
            
            if st.button("🚀 执行命令", use_container_width=True):
                if text_input.strip():
                    st.success(f"✅ 输入命令: {text_input}")
                    
                    # 使用AI识别命令（即使没有音频功能，命令识别逻辑仍然可用）
                    if voice_assistant:
                        command_result = voice_assistant.recognize_chinese_commands(text_input)
                    else:
                        # 简单的命令识别逻辑（备用方案）
                        command_result = recognize_commands_fallback(text_input)
                    
                    if command_result["command"] != "unknown":
                        st.info(f"🎯 识别命令: {command_result['command']}")
                        process_voice_command(text_input)
                    else:
                        st.warning("⚠️ 未识别到有效命令，请尝试以下标准命令")
                else:
                    st.error("❌ 请输入命令文本")
        else:
            # 本地环境的语音功能
            st.subheader("🗣️ 中文语音控制")
            duration = st.slider("录音时长(秒)", 1, 10, 5)
            enable_feedback = st.checkbox("启用语音反馈", value=True)
            
            if st.button("🎙️ 开始录音（中文）", use_container_width=True):
                with st.spinner(f"录音中... ({duration}秒)"):
                    try:
                        recognized_text = voice_assistant.record_and_recognize(duration, language="zh-CN")
                        
                        if recognized_text:
                            if "语音识别失败" in recognized_text or "语音识别异常" in recognized_text:
                                st.error("❌ 语音识别失败")
                                st.info(f"错误信息: {recognized_text}")
                            else:
                                st.success(f"✅ 识别结果: {recognized_text}")
                                command_result = voice_assistant.recognize_chinese_commands(recognized_text)
                                
                                if command_result["command"] != "unknown":
                                    st.info(f"🎯 识别命令: {command_result['command']} (置信度: {command_result['confidence']:.1f})")
                                    if enable_feedback:
                                        voice_assistant.provide_chinese_feedback(command_result)
                                
                                process_voice_command(recognized_text)
                        else:
                            st.error("❌ 识别失败，请检查麦克风权限或网络连接")
                            
                    except Exception as e:
                        st.error(f"❌ 语音处理失败: {str(e)}")
        
        # 中文语音命令列表
        st.subheader("🗣️ 支持的中文命令")
        chinese_commands = [
            "下一步", "暂停", "继续", "重新开始",
            "加时间", "减时间", "查看步骤", "查看营养",
            "帮助", "退出"
        ]
        for cmd in chinese_commands:
            st.write(f"🎯 {cmd}")
    
    with col2:
        st.subheader("⏱️ 烹饪计时器")
        
        # 计时器显示
        if st.session_state.timer_active:
            minutes = st.session_state.timer_seconds // 60
            seconds = st.session_state.timer_seconds % 60
            st.markdown(f"<div class='timer-display'>{minutes:02d}:{seconds:02d}</div>", unsafe_allow_html=True)
        else:
            st.info("⏰ 计时器未启动")
        
        # 计时器控制
        col_time1, col_time2, col_time3 = st.columns(3)
        
        with col_time1:
            if st.button("▶️ 开始", disabled=st.session_state.timer_active):
                start_timer()
        
        with col_time2:
            if st.button("⏸️ 暂停", disabled=not st.session_state.timer_active):
                pause_timer()
        
        with col_time3:
            if st.button("⏹️ 重置"):
                reset_timer()
        
        # 快速时间设置
        st.subheader("⏰ 快速设置")
        time_options = ["5分钟", "10分钟", "15分钟", "30分钟", "1小时"]
        for time_opt in time_options:
            if st.button(time_opt):
                set_timer(time_opt)

# AI实时指导Tab
def render_live_guidance():
    st.header("👨‍🍳 AI实时指导")
    
    if st.session_state.current_recipe:
        recipe = st.session_state.current_recipe
        
        st.subheader(f"🍳 正在烹饪: {recipe.get('name', '未知菜品')}")
        
        # 显示当前步骤
        current_step = st.session_state.current_step
        steps = recipe.get('cooking_steps', [])
        
        if steps and current_step < len(steps):
            st.subheader(f"步骤 {current_step + 1}")
            st.write(steps[current_step])
            
            # AI实时指导
            if st.button("🤔 AI需要帮助？"):
                with st.spinner("AI正在分析当前步骤..."):
                    try:
                        prompt = f"""
                        我正在烹饪{recipe['name']}的第{current_step + 1}步：
                        {steps[current_step]}
                        
                        请提供：
                        1. 详细的操作指导
                        2. 常见错误和避免方法
                        3. 时间控制建议
                        4. 下一步准备
                        
                        请用简洁明了的方式回答。
                        """
                        
                        result = zhipu_client.chat(
                            messages=[{"role": "user", "content": prompt}],
                            model="glm-4",
                            temperature=0.7
                        )
                        
                        if result["success"]:
                            st.info(f"💡 AI指导: {result['data']}")
                            
                    except Exception as e:
                        st.error(f"❌ AI指导失败: {str(e)}")
            
            # 步骤控制
            col_step1, col_step2, col_step3 = st.columns(3)
            
            with col_step1:
                if st.button("⬅️ 上一步", disabled=current_step == 0):
                    st.session_state.current_step = max(0, current_step - 1)
                    st.rerun()
            
            with col_step2:
                if st.button("⏸️ 暂停"):
                    pause_timer()
            
            with col_step3:
                if st.button("➡️ 下一步", disabled=current_step >= len(steps) - 1):
                    st.session_state.current_step = min(len(steps) - 1, current_step + 1)
                    st.rerun()
        else:
            st.success("🎉 烹饪完成！")
            if st.button("🔄 重新开始"):
                st.session_state.current_step = 0
                st.rerun()
    else:
        st.info("👆 请先在'推荐菜品'页面选择一道菜品")

# AI库存管理功能
def render_inventory_management():
    st.header("📦 AI智能库存管理")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("➕ 添加食材到库存")
        
        with st.form("add_inventory_form"):
            ingredient_name = st.text_input("食材名称")
            quantity = st.number_input("数量", min_value=0.1, step=0.1, value=1.0)
            unit = st.selectbox("单位", ["个", "克", "毫升", "包", "斤", "千克"])
            expiry_date = st.date_input("保质期")
            
            if st.form_submit_button("添加食材"):
                if ingredient_name:
                    new_item = {
                        'name': ingredient_name,
                        'quantity': quantity,
                        'unit': unit,
                        'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                        'added_date': time.strftime('%Y-%m-%d')
                    }
                    st.session_state.ingredient_inventory.append(new_item)
                    st.success(f"✅ 已添加 {ingredient_name} 到库存")
                else:
                    st.warning("⚠️ 请输入食材名称")
    
    with col2:
        st.subheader("📋 当前库存")
        
        if st.session_state.ingredient_inventory:
            for i, item in enumerate(st.session_state.ingredient_inventory):
                with st.expander(f"{item['name']} - {item['quantity']}{item['unit']}"):
                    st.write(f"**保质期:** {item['expiry_date']}")
                    st.write(f"**添加日期:** {item['added_date']}")
                    
                    if st.button("🗑️ 删除", key=f"delete_{i}"):
                        st.session_state.ingredient_inventory.pop(i)
                        st.rerun()
        else:
            st.info("📝 库存为空，请先添加食材")
        
        # AI库存分析
        if st.session_state.ingredient_inventory:
            if st.button("🔍 AI分析库存"):
                with st.spinner("AI正在分析库存..."):
                    try:
                        ingredients = [item['name'] for item in st.session_state.ingredient_inventory]
                        
                        prompt = f"""
                        请分析以下库存食材：
                        {', '.join(ingredients)}
                        
                        请提供：
                        1. 营养搭配建议
                        2. 可能的菜品组合
                        3. 保质期提醒
                        4. 采购建议
                        
                        按照以下JSON格式返回：
                        {{
                            "nutrition_analysis": "营养分析",
                            "recipe_suggestions": ["菜品建议1", "菜品建议2"],
                            "expiry_warnings": ["过期提醒1", "过期提醒2"],
                            "shopping_recommendations": ["采购建议1", "采购建议2"]
                        }}
                        """
                        
                        result = zhipu_client.chat(
                            messages=[{"role": "user", "content": prompt}],
                            model="glm-4",
                            temperature=0.7
                        )
                        
                        if result["success"]:
                            analysis = json.loads(result["data"])
                            
                            st.subheader("🤖 AI分析结果")
                            
                            if "nutrition_analysis" in analysis:
                                st.write(f"**营养分析:** {analysis['nutrition_analysis']}")
                            
                            if "recipe_suggestions" in analysis:
                                st.write("**菜品建议:**")
                                for suggestion in analysis["recipe_suggestions"]:
                                    st.write(f"• {suggestion}")
                            
                            if "expiry_warnings" in analysis:
                                st.write("**保质期提醒:**")
                                for warning in analysis["expiry_warnings"]:
                                    st.write(f"⚠️ {warning}")
                            
                            if "shopping_recommendations" in analysis:
                                st.write("**采购建议:**")
                                for recommendation in analysis["shopping_recommendations"]:
                                    st.write(f"🛒 {recommendation}")
                                    
                    except Exception as e:
                        st.error(f"❌ AI分析失败: {str(e)}")

# 购物清单功能
def render_shopping_list():
    st.header("🛒 智能购物清单")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 购物清单")
        
        # 从推荐菜品生成购物清单
        if st.session_state.recommended_recipes and st.session_state.current_recipe:
            if st.button("🛍️ AI生成购物清单"):
                recipe = st.session_state.current_recipe
                missing_ingredients = []
                
                # 获取当前库存中的食材名称
                inventory_names = [item['name'] for item in st.session_state.ingredient_inventory]
                
                # 找出缺失的食材
                for ingredient in recipe.get('ingredients', []):
                    if ingredient not in inventory_names:
                        missing_ingredients.append(ingredient)
                
                st.session_state.shopping_list = missing_ingredients
                st.success(f"✅ AI生成了 {len(missing_ingredients)} 项购物清单")
        
        # 手动添加购物项
        st.subheader("✏️ 手动添加")
        new_item = st.text_input("添加购物项")
        if st.button("➕ 添加") and new_item:
            if new_item not in st.session_state.shopping_list:
                st.session_state.shopping_list.append(new_item)
                st.success(f"✅ 已添加: {new_item}")
        
        # 显示购物清单
        if st.session_state.shopping_list:
            st.subheader("🛍️ 待购物品")
            for i, item in enumerate(st.session_state.shopping_list):
                col_item, col_action = st.columns([4, 1])
                with col_item:
                    st.write(f"✅ {item}")
                with col_action:
                    if st.button("🗑️", key=f"remove_{i}"):
                        st.session_state.shopping_list.pop(i)
                        st.rerun()
        else:
            st.info("🛒 购物清单为空")
    
    with col2:
        st.subheader("📊 统计信息")
        st.write(f"**待购物品:** {len(st.session_state.shopping_list)} 项")
        
        if st.session_state.shopping_list:
            # 清空购物清单
            if st.button("🗑️ 清空清单"):
                st.session_state.shopping_list = []
                st.rerun()
            
            # 导出购物清单
            shopping_text = "\n".join([f"- {item}" for item in st.session_state.shopping_list])
            st.download_button("📥 导出清单", shopping_text, file_name="购物清单.txt")

# 营养分析功能
def render_nutrition_analysis():
    st.header("📊 AI营养分析与健康管理")
    
    tab_nutrition, tab_goals, tab_history = st.tabs(["🍎 AI营养分析", "🎯 健康目标", "📈 历史记录"])
    
    with tab_nutrition:
        st.subheader("🍎 当前菜品AI营养分析")
        
        if st.session_state.current_recipe:
            recipe = st.session_state.current_recipe
            
            # 显示基础营养信息
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("热量", f"{recipe.get('calories', 0)} 卡路里")
            with col2:
                st.metric("蛋白质", f"{recipe.get('protein', '未知')}g")
            with col3:
                st.metric("碳水化合物", f"{recipe.get('carbs', '未知')}g")
            with col4:
                st.metric("脂肪", f"{recipe.get('fat', '未知')}g")
            
            # AI详细营养分析
            if st.button("🔍 AI详细分析"):
                with st.spinner("AI正在分析营养成分..."):
                    try:
                        ingredients = [ing.get('name', '') for ing in st.session_state.recognized_ingredients]
                        
                        if not ingredients:
                            st.warning("⚠️ 请先在'食材识别'页面上传图片识别食材")
                        else:
                            st.info(f"🔍 AI正在分析食材: {', '.join(ingredients)}")
                            analysis = nutrition_analyzer.analyze_nutrition(ingredients)
                            
                            # 加强API调用结果检查
                            if 'total_calories' in analysis and analysis['total_calories'] > 0:
                                # 显示AI分析的详细营养信息
                                st.subheader("🤖 AI营养分析结果")
                                
                                # 总卡路里
                                if 'total_calories' in analysis:
                                    st.metric("总卡路里", f"{analysis['total_calories']} 卡路里")
                                
                                # 宏量营养素
                                if 'macronutrients' in analysis:
                                    st.subheader("🍽️ 宏量营养素")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    macros = analysis['macronutrients']
                                    with col1:
                                        if 'protein' in macros:
                                            st.metric("蛋白质", macros['protein'])
                                    with col2:
                                        if 'carbohydrates' in macros:
                                            st.metric("碳水化合物", macros['carbohydrates'])
                                    with col3:
                                        if 'fat' in macros:
                                            st.metric("脂肪", macros['fat'])
                                    with col4:
                                        if 'fiber' in macros:
                                            st.metric("膳食纤维", macros['fiber'])
                            else:
                                # 显示API调用失败的错误信息
                                st.error("❌ AI营养分析失败")
                                if 'raw_response' in analysis:
                                    st.info(f"错误信息: {analysis['raw_response']}")
                                st.warning("💡 请检查网络连接或稍后重试")
                            
                            # 微量营养素
                            if 'micronutrients' in analysis:
                                st.subheader("💊 微量营养素")
                                micros = analysis['micronutrients']
                                
                                if 'vitamins' in micros:
                                    st.write(f"**主要维生素:** {', '.join(micros['vitamins'])}")
                                if 'minerals' in micros:
                                    st.write(f"**主要矿物质:** {', '.join(micros['minerals'])}")
                            
                            # 健康益处
                            if 'health_benefits' in analysis:
                                st.subheader("💚 健康益处")
                                for benefit in analysis['health_benefits']:
                                    st.write(f"✅ {benefit}")
                            
                            # 饮食建议
                            if 'dietary_recommendations' in analysis:
                                st.subheader("💡 饮食建议")
                                for recommendation in analysis['dietary_recommendations']:
                                    st.write(f"📌 {recommendation}")
                            
                            # 过敏警告
                            if 'allergy_warnings' in analysis:
                                st.subheader("⚠️ 过敏警告")
                                for warning in analysis['allergy_warnings']:
                                    st.write(f"🚫 {warning}")
                            
                            # 显示原始AI响应（调试用）
                            if 'raw_response' in analysis:
                                with st.expander("🔧 AI原始响应（调试）"):
                                    st.code(analysis['raw_response'])
                                
                    except Exception as e:
                        st.error(f"❌ AI营养分析失败: {str(e)}")
                        st.info("💡 提示：请确保API密钥正确配置，网络连接正常")
        else:
            st.info("👆 请先在'推荐菜品'页面选择一道菜品")
    
    with tab_goals:
        st.subheader("🎯 设定健康目标")
        
        # 健康目标设置
        calories = st.slider("每日热量目标(卡路里)", 1000, 3000, st.session_state.nutrition_goals['daily_calories'])
        protein = st.slider("每日蛋白质目标(g)", 30, 150, st.session_state.nutrition_goals['protein_goal'])
        carbs = st.slider("每日碳水化合物目标(g)", 100, 400, st.session_state.nutrition_goals['carb_goal'])
        fat = st.slider("每日脂肪目标(g)", 20, 100, st.session_state.nutrition_goals['fat_goal'])
        
        if st.button("💾 保存目标"):
            st.session_state.nutrition_goals = {
                'daily_calories': calories,
                'protein_goal': protein,
                'carb_goal': carbs,
                'fat_goal': fat
            }
            st.success("✅ 健康目标已保存")
        
        # 显示目标进度
        st.subheader("📊 目标进度")
        if st.session_state.current_recipe:
            recipe_calories = recipe.get('calories', 0)
            progress = min(recipe_calories / calories, 1.0) if calories > 0 else 0
            st.progress(progress)
            st.write(f"当前菜品热量: {recipe_calories} / {calories} 卡路里 ({progress*100:.1f}%)")
    
    with tab_history:
        st.subheader("📈 烹饪历史记录")
        
        # 记录当前烹饪
        if st.session_state.current_recipe and st.button("📝 记录本次烹饪"):
            cooking_record = {
                'recipe_name': st.session_state.current_recipe.get('name', '未知菜品'),
                'date': time.strftime('%Y-%m-%d %H:%M'),
                'calories': st.session_state.current_recipe.get('calories', 0),
                'rating': 0
            }
            st.session_state.cooking_history.append(cooking_record)
            st.success("✅ 烹饪记录已保存")
        
        # 显示历史记录
        if st.session_state.cooking_history:
            for record in reversed(st.session_state.cooking_history[-10:]):  # 显示最近10条
                st.write(f"**{record['date']}** - {record['recipe_name']} ({record['calories']}卡路里)")
        else:
            st.info("📝 暂无烹饪记录")

# 语音命令处理（中文优化）
def recognize_commands_fallback(text: str):
    """备用命令识别函数（当语音助手不可用时使用）"""
    if not text:
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
        if chinese_cmd in text:
            return {
                "command": english_cmd,
                "original_text": text,
                "confidence": 0.9
            }
    
    # 模糊匹配
    for chinese_cmd, english_cmd in commands.items():
        if any(word in text for word in chinese_cmd):
            return {
                "command": english_cmd,
                "original_text": text,
                "confidence": 0.7
            }
    
    return {"command": "unknown", "original_text": text, "confidence": 0.0}

def process_voice_command(text: str):
    """处理语音命令（支持中文）"""
    # 使用语音助手的中文命令识别功能（如果可用）
    if voice_assistant:
        command_result = voice_assistant.recognize_chinese_commands(text)
    else:
        # 使用备用识别函数
        command_result = recognize_commands_fallback(text)
    
    if command_result["command"] != "unknown":
        command = command_result["command"]
        
        if command == "next_step":
            st.session_state.current_step = min(
                len(st.session_state.current_recipe.get('cooking_steps', [])) - 1,
                st.session_state.current_step + 1
            )
            st.success("✅ 下一步")
        elif command == "pause":
            pause_timer()
            st.success("✅ 已暂停")
        elif command == "continue":
            start_timer()
            st.success("✅ 继续烹饪")
        elif command == "restart":
            reset_timer()
            st.session_state.current_step = 0
            st.success("✅ 重新开始")
        elif command == "add_time":
            st.session_state.timer_seconds += 300  # 加5分钟
            st.success("✅ 已加5分钟")
        elif command == "reduce_time":
            st.session_state.timer_seconds = max(0, st.session_state.timer_seconds - 300)  # 减5分钟
            st.success("✅ 已减5分钟")
        elif command == "view_steps":
            st.success("✅ 显示烹饪步骤")
        elif command == "view_nutrition":
            st.success("✅ 显示营养信息")
        elif command == "help":
            st.info("💡 我是您的智能厨房助手，支持以下中文语音命令：下一步、暂停、继续、重新开始、加时间、减时间、查看步骤、查看营养、帮助、退出")
        elif command == "exit":
            st.success("👋 再见，祝您烹饪愉快！")
    else:
        # 传统命令处理（兼容性）
        text_lower = text.lower()
        
        if "下一步" in text_lower or "next" in text_lower:
            st.session_state.current_step = min(
                len(st.session_state.current_recipe.get('cooking_steps', [])) - 1,
                st.session_state.current_step + 1
            )
            st.success("✅ 下一步")
        elif "暂停" in text_lower or "pause" in text_lower:
            pause_timer()
            st.success("✅ 已暂停")
        elif "继续" in text_lower or "resume" in text_lower:
            start_timer()
            st.success("✅ 继续烹饪")
        elif "加时间" in text_lower or "add time" in text_lower:
            st.session_state.timer_seconds += 300  # 加5分钟
            st.success("✅ 已加5分钟")
        elif "完成" in text_lower or "finish" in text_lower:
            reset_timer()
            st.session_state.current_step = 0
            st.success("✅ 烹饪完成！")

# 计时器相关函数
def start_timer():
    st.session_state.timer_active = True

def pause_timer():
    st.session_state.timer_active = False

def reset_timer():
    st.session_state.timer_active = False
    st.session_state.timer_seconds = 0

def set_timer(time_str):
    time_map = {
        "5分钟": 300,
        "10分钟": 600,
        "15分钟": 900,
        "30分钟": 1800,
        "1小时": 3600
    }
    st.session_state.timer_seconds = time_map.get(time_str, 0)

# 主程序
def main():
    # 初始化session state
    init_session_state()
    
    # 应用标题
    st.markdown('<div class="main-header">🍳 AI智能厨房助手</div>', unsafe_allow_html=True)
    
    # 渲染侧边栏
    render_sidebar()
    
    # 主区域 - Tab布局
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📷 AI食材识别", 
        "🍽️ AI推荐菜品", 
        "🎤 AI语音助手", 
        "👨‍🍳 AI实时指导",
        "📦 AI库存管理",
        "🛒 智能购物清单", 
        "📊 AI营养分析"
    ])
    
    with tab1:
        render_ingredient_recognition()
    
    with tab2:
        render_recipe_recommendation()
    
    with tab3:
        render_voice_assistant()
    
    with tab4:
        render_live_guidance()
    
    with tab5:
        render_inventory_management()
    
    with tab6:
        render_shopping_list()
    
    with tab7:
        render_nutrition_analysis()
    
    # 定时器更新（需要在主线程中运行）
    if st.session_state.timer_active:
        st.session_state.timer_seconds += 1
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()