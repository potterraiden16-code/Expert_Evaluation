import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="德尔菲法专家评价系统 v4.1",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式：增强科研质感
st.markdown("""
    <style>
    .stSlider {padding-bottom: 20px;}
    .section-header {color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 5px; margin-top: 5px; margin-bottom: 15px; font-weight: bold; font-size: 1.1rem;}
    .status-box {padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center; font-weight: bold; font-size: 0.9rem;}
    .pending {background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
    .completed {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .anchor-box {background-color: #f9f9f9; padding: 10px; border-radius: 5px; border-left: 4px solid #1f77b4; font-size: 0.85rem; margin-bottom: 5px;}
    </style>
    """, unsafe_allow_html=True)


# --- 2. 数据处理与状态检查 ---
@st.cache_data
def load_data():
    try:
        # 确保文件名 data_final_v3.xlsx 正确
        return pd.read_excel("data_final_v3.xlsx")
    except Exception as e:
        st.error(f"无法读取数据文件: {e}")
        return pd.DataFrame()


def get_reviewed_ids():
    results_file = "expert_evaluations.csv"
    if os.path.exists(results_file):
        try:
            # 增加对读取失败的捕获
            rdf = pd.read_csv(results_file, encoding='utf-8-sig')
            return rdf['文献ID'].unique().tolist()
        except Exception:
            return []
    return []


df = load_data()
# 这里是关键：确保每次运行都重新获取最新的已评审列表
reviewed_ids = get_reviewed_ids()
results_file = "expert_evaluations.csv"

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("👨‍🔬 评审工作台")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")
    st.divider()
    if not df.empty:
        raw_options = df['ID'].tolist()
        # 状态图标逻辑保持不变
        display_options = [f"{oid} {'✅' if oid in reviewed_ids else '⏳'}" for oid in raw_options]
        option_map = dict(zip(display_options, raw_options))
        selected_display = st.selectbox("选择文献：", options=display_options)
        current_doc_id = option_map[selected_display]
        row = df[df['ID'] == current_doc_id].iloc[0]
        st.write(f"总体进度: **{len(reviewed_ids)} / {len(raw_options)}**")

    st.divider()
    if os.path.exists(results_file):
        with open(results_file, "rb") as f:
            st.download_button("💾 下载评价汇总表", f, "delphi_results.csv", "text/csv", use_container_width=True)

# --- 4. 主界面：状态提示 ---
if current_doc_id in reviewed_ids:
    st.markdown(f'<div class="status-box completed">✅ 文献 {current_doc_id} 已评价（数据已保存）</div>',
                unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-box pending">⏳ 待处理：请阅读原始证据和AI推理结果后，对照原文结论，填写“评估量表”标签完成评分</div>',
                unsafe_allow_html=True)

# --- 5. 四标签沉浸式布局 ---
tab_evid, tab_ai, tab_author, tab_score = st.tabs(["📄 原始证据", "🧠 AI 推演", "📖 原文结论", "✍️ 评估量表"])

with tab_evid:
    st.text_area("e_c", value=row['Evidence'], height=600, disabled=True, label_visibility="collapsed")

with tab_ai:
    st.text_area("a_c", value=row['AI_Report'], height=600, disabled=True, label_visibility="collapsed")

with tab_author:
    st.markdown(row['Author_Conclusion'])

with tab_score:
    with st.form("delphi_full_form"):
        st.markdown('<div class="section-header">第一部分：具体科研能力维度的定量评分 (1-10分)</div>',
                    unsafe_allow_html=True)

        # --- 维度 1 ---
        st.write("1. **逻辑严密性与简约性
