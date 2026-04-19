# 🍳 智能厨房助手

基于智谱AI大模型的智能厨房助手，提供食材识别、食谱推荐、营养分析和中文语音交互等功能。

## 🚀 一键部署

[![Deploy to GitHub Pages](https://img.shields.io/badge/Deploy-GitHub%20Pages-blue?style=for-the-badge&logo=github)](https://github.com/zcz10086-dot/kitchen-assistant/deployments)
[![Streamlit Cloud](https://img.shields.io/badge/Deploy-Streamlit%20Cloud-orange?style=for-the-badge&logo=streamlit)](https://share.streamlit.io/zcz10086-dot/kitchen-assistant)

### 🌐 在线访问地址
- **GitHub Pages**: https://zcz10086-dot.github.io/kitchen-assistant
- **Streamlit Cloud**: https://share.streamlit.io/zcz10086-dot/kitchen-assistant

## ✨ 核心功能特性

### 🤖 AI智能功能（100%云端部署支持）
- **📷 AI食材识别**: 使用GLM-4V模型智能识别图片中的食材
- **🍽️ AI推荐菜品**: 基于可用食材和用户偏好使用GLM-4进行智能推荐
- **📊 AI营养分析**: 使用GLM-4分析食材营养成分和热量
- **🎤 云端语音助手**: 支持TTS语音合成和文件上传语音识别
- **👨‍🍳 AI实时指导**: 烹饪步骤实时指导
- **📦 AI库存管理**: 智能食材库存分析
- **🛒 智能购物清单**: 基于库存的购物建议

### ✅ 云端部署优势
- **🌐 完全云端兼容**: 无需本地环境，100%云端运行
- **🔊 完整中文语音支持**: 4种中文语音类型 + 6种英文语音类型
- **🎤 智能语音设置**: 语言分类选择 + 语音类型显示
- **🚀 自动部署**: GitHub Actions自动构建和部署
- **💯 稳定可靠**: GitHub基础设施保障

## 📁 项目结构（精简版）

```
kitchen_assistant_zhipu/
├── .github/workflows/        # GitHub Actions工作流
│   └── deploy.yml            # 自动部署配置
├── .streamlit/               # Streamlit配置
│   └── config.toml           # 应用配置文件
├── modules/                  # AI功能模块（核心）
│   ├── zhipu_client.py       # 智谱AI统一客户端
│   ├── image_recognition.py  # 食材识别模块（GLM-4V）
│   ├── recommendation.py     # 推荐系统模块（GLM-4）
│   ├── nutrition.py          # 营养分析模块（GLM-4）
│   ├── voice_assistant.py    # 本地语音助手模块
│   └── voice_assistant_cloud_enhanced.py # 云端语音助手（增强版）
├── app.py                    # Streamlit主界面（云端优化版）
├── requirements.txt          # 依赖包列表（部署优化）
├── index.html                # GitHub Pages静态页面
├── .env.example              # 环境变量配置示例
└── README.md                 # 项目说明文档
```

## 🚀 快速部署指南

### 方法一：GitHub Actions自动部署（推荐）

1. **Fork或克隆仓库**
   ```bash
   git clone https://github.com/zcz10086-dot/kitchen-assistant.git
   cd kitchen-assistant
   ```

2. **设置环境变量**（在GitHub仓库Settings → Secrets）
   - `ZHIPU_API_KEY`: 您的智谱AI API密钥

3. **推送到GitHub**
   ```bash
   git add .
   git commit -m "初始化项目"
   git push origin main
   ```

4. **自动部署**
   - GitHub Actions会自动构建和部署
   - 访问：https://yourusername.github.io/kitchen-assistant

### 方法二：Streamlit Cloud部署

1. **访问Streamlit Cloud**: https://share.streamlit.io
2. **连接GitHub仓库**
3. **选择分支和文件**: 选择main分支和app.py
4. **设置环境变量**: 添加ZHIPU_API_KEY
5. **部署完成**: 自动生成访问链接

### 方法三：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/zcz10086-dot/kitchen-assistant.git
cd kitchen-assistant

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置环境变量
cp .env.example .env
# 编辑.env文件，添加您的智谱AI API密钥

# 4. 运行应用
streamlit run app.py
```

## 🔧 环境配置

### 1. 获取智谱AI API密钥
1. 访问智谱AI开放平台：https://open.bigmodel.cn/
2. 注册账号并创建API密钥
3. 复制您的API密钥

### 2. 依赖包说明（最新优化版）

**核心AI功能依赖**:
- `streamlit>=1.28.0` - Web应用框架
- `zhipuai>=2.0.0` - 智谱AI SDK
- `Pillow>=10.0.0` - 图像处理
- `python-dotenv>=1.0.0` - 环境变量管理

**云端兼容音频处理**:
- `wave>=0.0.2` - WAV文件处理（Python标准库）
- `audioop>=1.0.0` - 音频操作（Python标准库）

**已移除不兼容依赖**:
- `librosa` - 云端可能不兼容
- `audioread` - 云端可能不兼容
- `sounddevice` - 需要系统音频驱动
- `soundfile` - 依赖libsndfile
- `pydub` - 依赖ffmpeg
- `pygame` - 需要图形界面和音频

### 3. 设置环境变量

**本地运行**：创建`.env`文件
```bash
ZHIPU_API_KEY=your_zhipuai_api_key_here
```

**云端部署**：在部署平台设置环境变量
- GitHub Pages: 仓库Settings → Secrets
- Streamlit Cloud: 应用设置 → Secrets

## 🎯 功能使用说明

### 1. 食材识别（GLM-4V）
- 上传食材图片
- AI自动识别食材种类和数量
- 提供新鲜度评估和烹饪建议

### 2. 智能推荐（GLM-4）
- 基于可用食材推荐菜品
- 考虑用户饮食偏好和忌口
- 提供详细烹饪步骤和营养信息

### 3. 营养分析（GLM-4）
- 分析食材营养成分
- 计算总卡路里和营养比例
- 提供健康饮食建议

### 4. 云端语音助手（最新增强版）
- **🎤 智能语音设置**: 支持中文/英文语言选择
- **🗣️ 中文语音类型**: 晓晓、云希、晓伊、云扬等4种中文语音
- **🔊 TTS语音合成**: 文本转语音，实时显示语音类型
- **📁 文件上传语音识别**: 上传音频文件进行识别
- **🎯 中文命令识别**: 支持"下一步"、"暂停"、"加时间"等命令
- **⚙️ 语音设置保存**: 用户偏好保存在session_state中

## 🔧 技术架构

### 前端技术栈
- **Streamlit**: Web应用框架
- **HTML5/CSS**: 用户界面
- **JavaScript**: 前端交互

### 后端技术栈
- **Python 3.10+**: 主要编程语言
- **智谱AI API**: GLM-4系列模型
- **GitHub Actions**: CI/CD自动化

### 部署平台
- **GitHub Pages**: 静态网站托管
- **Streamlit Cloud**: 应用托管服务

## 🐛 故障排除

### 常见问题

**Q: 部署失败怎么办？**
A: 检查requirements.txt是否包含不兼容的依赖包，已移除librosa、audioread等不兼容库

**Q: AI功能无法使用？**
A: 确保已正确设置ZHIPU_API_KEY环境变量，检查GitHub Actions测试日志

**Q: 音频功能不可用？**
A: 云端环境使用文件上传方式替代实时录音，已优化为Python标准库音频处理

**Q: 中文语音类型不可选？**
A: 确保使用最新版本，支持4种中文语音类型和6种英文语音类型

**Q: 如何更新应用？**
A: 推送代码到GitHub，GitHub Actions会自动重新部署，包含完整的模块导入测试

### 最新优化特性

✅ **依赖优化**: 移除不兼容库，使用Python标准库替代
✅ **中文语音增强**: 完整的中文语音类型支持
✅ **云端兼容性**: 100%云端环境兼容
✅ **自动测试**: GitHub Actions包含完整的模块导入测试
✅ **部署稳定性**: 经过全面测试的部署配置

### 调试技巧
1. 查看GitHub Actions日志，检查模块导入测试结果
2. 检查环境变量设置，确保ZHIPU_API_KEY正确
3. 验证API密钥有效性，访问智谱AI平台测试
4. 查看浏览器控制台错误信息，检查网络连接
5. 测试语音设置功能，确保中文语音类型可选

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- **智谱AI**: 提供强大的AI模型支持
- **Streamlit**: 优秀的Web应用框架
- **GitHub**: 免费的代码托管和部署服务

---

**🍳 智能厨房助手** - 让AI助力您的烹饪体验！