import streamlit as st
import base64
import io
import json
import tempfile
import time
import threading
from PIL import Image

# 修复后的导入方式
from modules.zhipu_client import ZhipuClient
from modules.image_recognition import ImageRecognition
from modules.recommendation import RecipeRecommender
from modules.nutrition import NutritionAnalyzer

# 初始化模块实例
zhipu_client = ZhipuClient()
image_recognizer = ImageRecognition()
recipe_recommender = RecipeRecommender()
nutrition_analyzer = NutritionAnalyzer()

# 音频功能依赖检查
try:
    from modules.voice_assistant import VoiceAssistant
    from modules.tts_assistant import TTSEngine
    voice_assistant = VoiceAssistant()
    tts_engine = TTSEngine()
    AUDIO_ENABLED = True
except ImportError as e:
    print(f"完整音频功能不可用：{e}")
    # 尝试使用简化版
    try:
        from modules.voice_assistant_simple import VoiceAssistantSimple
        from modules.tts_assistant_simple import TTSEngineSimple
        voice_assistant = VoiceAssistantSimple()
        tts_engine = TTSEngineSimple()
        AUDIO_ENABLED = True
        print("使用简化版音频功能")
    except ImportError:
        print("音频功能完全不可用")
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

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #FF6B35;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .step-card {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .timer-display {
        font-size: 1.5rem;
        font-weight: bold;
        color: #e74c3c;
        text-align: center;
        margin: 10px 0;
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
        
        # API设置
        st.header("🔧 API设置")
        api_key = st.text_input("智谱AI API密钥", type="password")
        if api_key:
            st.success("✅ API密钥已设置")
        
        # 语音设置
        st.header("🎤 语音设置")
        enable_voice = st.checkbox("启用语音功能", value=True)
        if enable_voice:
            voice_type = st.selectbox("语音类型", tts_engine.get_available_voices())

# 食材识别Tab
def render_ingredient_recognition():
    st.header("📷 食材识别")
    
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
            if st.button("🔍 开始识别食材", use_container_width=True):
                with st.spinner("正在识别食材..."):
                    try:
                        # 转换图片为bytes
                        img_bytes = uploaded_file.getvalue()
                        
                        # 识别食材
                        result = image_recognizer.recognize_ingredients(img_bytes)
                        
                        # 存储识别结果
                        st.session_state.recognized_ingredients = result.get('ingredients', [])
                        
                        # 显示结果
                        if st.session_state.recognized_ingredients:
                            st.success(f"✅ 识别到 {len(st.session_state.recognized_ingredients)} 种食材")
                            
                            # 显示食材列表
                            for i, ingredient in enumerate(st.session_state.recognized_ingredients, 1):
                                with st.expander(f"{i}. {ingredient.get('name', '未知食材')}"):
                                    st.write(f"**数量:** {ingredient.get('quantity', '未知')}")
                                    st.write(f"**新鲜度:** {ingredient.get('freshness', '未知')}")
                                    st.write(f"**置信度:** {ingredient.get('confidence', '未知')}")
                            
                            # 烹饪建议
                            if 'cooking_suggestions' in result:
                                st.subheader("🍳 烹饪建议")
                                for suggestion in result['cooking_suggestions']:
                                    st.write(f"💡 {suggestion}")
                        else:
                            st.warning("⚠️ 未识别到食材，请尝试更清晰的图片")
                            
                    except Exception as e:
                        st.error(f"❌ 识别失败: {str(e)}")
        
        # 手动输入食材
        st.subheader("📝 手动添加食材")
        manual_ingredients = st.text_input("输入食材名称（用逗号分隔）")
        if st.button("➕ 添加食材") and manual_ingredients:
            ingredients_list = [ing.strip() for ing in manual_ingredients.split(',') if ing.strip()]
            for ingredient in ingredients_list:
                st.session_state.recognized_ingredients.append({
                    'name': ingredient,
                    'quantity': '适量',
                    'freshness': '未知',
                    'confidence': 0.8
                })
            st.success(f"✅ 添加了 {len(ingredients_list)} 种食材")
    
    with col2:
        st.subheader("📋 当前食材清单")
        if st.session_state.recognized_ingredients:
            for ingredient in st.session_state.recognized_ingredients:
                st.write(f"🍎 {ingredient.get('name', '未知食材')}")
            
            # 清空按钮
            if st.button("🗑️ 清空食材清单", type="secondary"):
                st.session_state.recognized_ingredients = []
                st.rerun()
        else:
            st.info("👆 请先上传图片或手动添加食材")

# 推荐菜品Tab
def render_recipe_recommendation():
    st.header("🍽️ 推荐菜品")
    
    if not st.session_state.recognized_ingredients:
        st.warning("⚠️ 请先在'食材识别'页面添加食材")
        return
    
    # 获取食材名称列表
    ingredient_names = [ing.get('name', '') for ing in st.session_state.recognized_ingredients]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 推荐参数设置
        st.subheader("⚙️ 推荐参数")
        max_recipes = st.slider("最大推荐数量", 1, 10, 5)
        difficulty = st.selectbox("难度级别", ["任意", "简单", "中等", "困难"])
        cooking_time = st.selectbox("烹饪时间", ["任意", "15分钟内", "30分钟内", "1小时内", "1小时以上"])
    
    with col2:
        st.subheader("📊 当前食材")
        st.write("可用食材:")
        for name in ingredient_names:
            st.write(f"✅ {name}")
    
    # 推荐按钮
    if st.button("🔍 智能推荐菜品", use_container_width=True):
        with st.spinner("正在为您推荐合适的菜品..."):
            try:
                # 获取推荐
                recommendations = recipe_recommender.recommend_recipes(
                    ingredient_names, max_recipes
                )
                
                st.session_state.recommended_recipes = recommendations
                
                if recommendations:
                    st.success(f"✅ 为您推荐了 {len(recommendations)} 道菜品")
                else:
                    st.warning("⚠️ 未找到合适的菜品推荐")
                    
            except Exception as e:
                st.error(f"❌ 推荐失败: {str(e)}")
    
    # 显示推荐结果
    if st.session_state.recommended_recipes:
        st.subheader("📋 推荐菜品")
        
        for i, recipe in enumerate(st.session_state.recommended_recipes, 1):
            with st.expander(f"{i}. {recipe.get('name', '未知菜品')}", expanded=i==1):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**难度:** {recipe.get('difficulty', '未知')}")
                    st.write(f"**时间:** {recipe.get('cooking_time', '未知')}")
                
                with col2:
                    st.write(f"**热量:** {recipe.get('calories', '未知')} 卡路里")
                    st.write(f"**类别:** {recipe.get('category', '未知')}")
                
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
                
                # 查看详细步骤
                if st.button(f"📖 查看详细步骤", key=f"steps_{i}"):
                    with st.spinner("获取烹饪步骤..."):
                        try:
                            instructions = recipe_recommender.get_cooking_instructions(recipe.get('name', ''))
                            
                            if 'cooking_steps' in instructions:
                                st.write("**烹饪步骤:**")
                                for j, step in enumerate(instructions.get('cooking_steps', []), 1):
                                    st.write(f"{j}. {step}")
                        except Exception as e:
                            st.error(f"❌ 获取步骤失败: {str(e)}")

# 语音助手Tab
def render_voice_assistant():
    st.header("🎤 语音助手")
    
    if not AUDIO_ENABLED:
        st.warning("⚠️ 音频功能不可用，请检查音频依赖包安装")
        st.info("需要安装的包：sounddevice, soundfile, numpy, pydub, pygame")
        st.info("Windows用户可以使用：pip install pipwin && pipwin install pyaudio")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎙️ 语音控制")
        
        # 录音功能
        if st.button("🎤 开始录音", key="record_start"):
            with st.spinner("正在录音...请说话（5秒）"):
                try:
                    audio_file = voice_assistant.record_audio(duration=5)
                    
                    if audio_file:
                        text = voice_assistant.speech_to_text(audio_file)
                        
                        if text:
                            st.success("✅ 语音识别成功")
                            st.write(f"**识别结果:** {text}")
                            
                            # 处理命令
                            command_result = voice_assistant.process_kitchen_command(text)
                            
                            st.write(f"**意图:** {command_result.get('intent', '未知')}")
                            st.write(f"**动作:** {command_result.get('action', '未知')}")
                            
                            # 执行命令
                            execute_voice_command(command_result)
                                
                        else:
                            st.error("❌ 语音识别失败")
                    else:
                        st.error("❌ 录音失败")
                        
                except Exception as e:
                    st.error(f"❌ 语音处理失败: {str(e)}")
        
        # 语音命令列表
        st.subheader("🗣️ 支持的命令")
        commands = [
            "开始烹饪", "下一步", "上一步", "暂停", "继续",
            "加5分钟", "减5分钟", "重复步骤", "完成", "取消"
        ]
        for cmd in commands:
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

# 实时指导Tab
def render_live_guidance():
    st.header("👨‍🍳 实时指导")
    
    if not st.session_state.current_recipe:
        st.warning("⚠️ 请先在'推荐菜品'页面选择一道菜品")
        return
    
    recipe = st.session_state.current_recipe
    
    st.subheader(f"🍳 正在烹饪: {recipe.get('name', '未知菜品')}")
    
    # 获取烹饪步骤
    with st.spinner("获取烹饪指导..."):
        try:
            instructions = recipe_recommender.get_cooking_instructions(recipe.get('name', ''))
            
            # 显示当前步骤
            if 'cooking_steps' in instructions:
                steps = instructions['cooking_steps']
                
                if steps:
                    # 当前步骤显示
                    current_step = st.session_state.current_step
                    
                    if current_step < len(steps):
                        st.markdown(f"<div class='step-card'>**步骤 {current_step + 1}:** {steps[current_step]}</div>", unsafe_allow_html=True)
                    
                    # 步骤控制
                    col_step1, col_step2, col_step3 = st.columns(3)
                    
                    with col_step1:
                        if st.button("⬅️ 上一步", disabled=current_step == 0):
                            st.session_state.current_step = max(0, current_step - 1)
                            st.rerun()
                    
                    with col_step2:
                        if st.button("➡️ 下一步", disabled=current_step >= len(steps) - 1):
                            st.session_state.current_step = min(len(steps) - 1, current_step + 1)
                            st.rerun()
                    
                    with col_step3:
                        if st.button("🔄 重置步骤"):
                            st.session_state.current_step = 0
                            st.rerun()
                    
                    # 语音播报当前步骤
                    if st.button("🔊 语音播报当前步骤"):
                        try:
                            tts_engine.speak_recipe_instructions(
                                recipe.get('name', ''),
                                st.session_state.current_step + 1
                            )
                            st.success("✅ 语音播报完成")
                        except Exception as e:
                            st.error(f"❌ 语音播报失败: {str(e)}")
                    
                    # 显示所有步骤
                    st.subheader("📋 完整步骤")
                    for i, step in enumerate(steps):
                        if i == current_step:
                            st.markdown(f"**{i+1}. {step}** 🎯")
                        else:
                            st.write(f"{i+1}. {step}")
                
            else:
                st.warning("⚠️ 未找到烹饪步骤")
                
        except Exception as e:
            st.error(f"❌ 获取指导失败: {str(e)}")

# 语音命令执行函数
def execute_voice_command(command_result):
    intent = command_result.get('intent', '')
    action = command_result.get('action', '')
    
    if "开始" in action or "start" in intent:
        start_timer()
        st.success("✅ 开始烹饪")
    elif "下一步" in action or "next" in intent:
        st.session_state.current_step = min(
            len(st.session_state.current_recipe.get('steps', [])) - 1,
            st.session_state.current_step + 1
        )
        st.success("✅ 下一步")
    elif "暂停" in action or "pause" in intent:
        pause_timer()
        st.success("✅ 已暂停")
    elif "继续" in action or "resume" in intent:
        start_timer()
        st.success("✅ 继续烹饪")
    elif "加时间" in action or "add_time" in intent:
        st.session_state.timer_seconds += 300  # 加5分钟
        st.success("✅ 已加5分钟")
    elif "完成" in action or "finish" in intent:
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
    st.markdown('<div class="main-header">🍳 智能厨房助手</div>', unsafe_allow_html=True)
    
    # 渲染侧边栏
    render_sidebar()
    
    # 主区域 - Tab布局
    tab1, tab2, tab3, tab4 = st.tabs([
        "📷 食材识别", 
        "🍽️ 推荐菜品", 
        "🎤 语音助手", 
        "👨‍🍳 实时指导"
    ])
    
    with tab1:
        render_ingredient_recognition()
    
    with tab2:
        render_recipe_recommendation()
    
    with tab3:
        render_voice_assistant()
    
    with tab4:
        render_live_guidance()
    
    # 定时器更新（需要在主线程中运行）
    if st.session_state.timer_active:
        st.session_state.timer_seconds += 1
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()