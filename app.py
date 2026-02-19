import streamlit as st
import pandas as pd

# --- 1. 页面配置与精准 UI 隐藏 ---
st.set_page_config(
    page_title="德尔菲法专家评价系统 v4.2",
    layout="wide",
    initial_sidebar_state="expanded"  # 默认展开侧边栏
)

# 自定义 CSS：修复侧边栏消失问题，并保持科研风格
st.markdown("""
    <style>
    /* 【修复核心】隐藏右上角菜单，但保留左上角侧边栏开关 */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }
    [data-testid="stToolbar"] {
        right: 2rem !important;
    }
    #MainMenu, [data-testid="stStatusWidget"], [data-testid="stAppDeployButton"] {
        display: none !important;
    }
    
    /* 强化侧边栏展开按钮的可见性 */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
        color: #1f77b4 !important;
        border-radius: 4px !important;
        margin-left: 5px !important;
    }

    /* 隐藏底部脚注 */
    footer {visibility: hidden;}

    /* 科研UI样式 */
    .section-header {
        color: #1f77b4; 
        border-bottom: 2px solid #1f77b4; 
        padding-bottom: 5px; 
        margin-top: 10px; 
        margin-bottom: 15px; 
        font-weight: bold; 
        font-size: 1.1rem;
    }
    .status-box {
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 15px; 
        text-align: center; 
        font-weight: bold;
    }
    .pending {background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
    .completed {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .anchor-box {
        background-color: #f9f9f9; 
        padding: 10px; 
        border-radius: 5px; 
        border-left: 4px solid #1f77b4; 
        font-size: 0.85rem; 
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 模拟数据初始化 ---
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# 评价指标示例数据
indicators = [
    {"ID": "A1", "名称": "技术先进性", "定义": "评价系统在行业内的技术领先程度。"},
    {"ID": "A2", "名称": "应用成熟度", "定义": "技术在实际场景中的稳定表现与案例积累。"},
    {"ID": "A3", "名称": "成本效益比", "定义": "投入资金与产出效益的综合平衡。"}
]

# --- 3. 侧边栏：评审工作台 ---
with st.sidebar:
    st.markdown('<div class="section-header">🛠️ 评审进度控制</div>', unsafe_allow_html=True)
    
    # 状态显示
    if not st.session_state.submitted:
        st.markdown('<div class="status-box pending">⏳ 评价进行中</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-box completed">✅ 已提交结果</div>', unsafe_allow_html=True)
    
    st.info("💡 提示：您可以随时折叠此栏以获得更大的阅读空间。点击左上角的 '>' 按钮即可重新开启。")
    
    # 快捷锚点（模拟）
    st.markdown('<div class="section-header">📍 快速跳转</div>', unsafe_allow_html=True)
    for ind in indicators:
        st.markdown(f'<div class="anchor-box">{ind["ID"]} - {ind["名称"]}</div>', unsafe_allow_html=True)

    if st.button("🚀 提交最终评审结果", use_container_width=True, type="primary"):
        st.session_state.submitted = True
        st.success("提交成功！")

# --- 4. 主界面：评价内容 ---
st.title("德尔菲法专家评价系统")
st.write("请专家根据各项指标的定义，给出您的专业评分（1-10分）。")

# 动态生成评价表单
for ind in indicators:
    with st.container():
        st.markdown(f'<div class="section-header">{ind["ID"]} {ind["名称"]}</div>', unsafe_allow_html=True)
        st.caption(f"指标定义：{ind['定义']}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            score = st.slider(f"评分 ({ind['ID']})", 1, 10, 5, key=f"score_{ind['ID']}")
        with col2:
            st.write(f"当前分值: **{score}**")
        
        st.text_area("理由与改进建议", placeholder="请简要说明评分依据...", key=f"reason_{ind['ID']}")
        st.markdown("---")

# 底部展示
if st.session_state.submitted:
    st.balloons()
    st.info("数据已加密上传至服务器，感谢您的参与。")
