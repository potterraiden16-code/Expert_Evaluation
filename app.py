import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="表型大模型专家评价系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 优化
st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    .stTextArea textarea {font-family: 'Courier New', Courier, monospace; font-size: 14px !important;}
    .completed-text {color: #28a745; font-weight: bold;}
    .pending-text {color: #ffc107; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)


# --- 2. 数据加载与状态检查函数 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("data_final_v3.xlsx")
        return df
    except Exception as e:
        st.error(f"无法读取原始数据文件: {e}")
        return pd.DataFrame()


# 获取已评审的文献列表
def get_reviewed_ids():
    results_file = "expert_evaluations.csv"
    if os.path.exists(results_file):
        try:
            # 这里的编码必须与保存时一致
            rdf = pd.read_csv(results_file, encoding='utf-8-sig')
            return rdf['文献ID'].unique().tolist()
        except:
            return []
    return []


df = load_data()
reviewed_ids = get_reviewed_ids()

# --- 3. 侧边栏：评审工作台 ---
with st.sidebar:
    st.title("👨‍🔬 评审工作台")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")

    st.divider()

    if not df.empty:
        # 生成带有勾选标记的选项列表
        raw_options = df['ID'].tolist()
        # 如果已评审，则在显示名称后加个钩
        display_options = [f"{oid} {'✅' if oid in reviewed_ids else '⏳'}" for oid in raw_options]

        # 建立显示名称到原始ID的映射
        option_map = dict(zip(display_options, raw_options))

        selected_display = st.selectbox("选择待评审文献：", options=display_options)
        current_doc_id = option_map[selected_display]

        row = df[df['ID'] == current_doc_id].iloc[0]

        # 真实的进度统计
        total_count = len(raw_options)
        reviewed_count = len(reviewed_ids)
        st.progress(reviewed_count / total_count)
        st.write(f"总体完成情况: **{reviewed_count} / {total_count}**")

    else:
        st.stop()

    st.divider()

    # 评分数据下载逻辑
    st.markdown("### 📥 数据导出")
    results_file = "expert_evaluations.csv"
    if os.path.exists(results_file):
        with open(results_file, "rb") as f:
            st.download_button(
                label="💾 下载最新评价汇总表",
                data=f,
                file_name=f"evaluation_results_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("提交首篇评价后即可下载。")

# --- 4. 主界面布局 ---
# 状态显示
if current_doc_id in reviewed_ids:
    st.markdown(f'<p class="completed-text">已评审：该文献的评价已保存在汇总表中 ✅</p>', unsafe_allow_html=True)
else:
    st.markdown(f'<p class="pending-text">待处理：您尚未提交对此文献的评价 ⏳</p>', unsafe_allow_html=True)

st.title(f"🔍 {current_doc_id}")
st.markdown(f"**文献标题：** {row['Title']}")

tab_evid, tab_ai, tab_score = st.tabs(["📄 原始证据", "🧠 AI推演报告", "⭐ 专家评分"])

with tab_evid:
    st.text_area("内容", value=row['Evidence'], height=500, disabled=True, label_visibility="collapsed")

with tab_ai:
    st.info("大模型生成的逻辑推演报告：")
    st.text_area("内容", value=row['AI_Report'], height=400, disabled=True, label_visibility="collapsed")
    with st.expander("📖 查看原作者结论 (Benchmark)"):
        st.markdown(row['Author_Conclusion'])

with tab_score:
    st.markdown("#### ✍️ 评价指标评分")

    # 如果已经评审过，给予提示
    if current_doc_id in reviewed_ids:
        st.warning("您之前已提交过此文献的评分，再次提交将追加一条记录。")

    with st.form("score_form"):
        # 改进1：初始分设为 0
        s1 = st.slider("1. 逻辑严密性", 0, 10, 0)
        s2 = st.slider("2. 生物学合理性", 0, 10, 0)
        s3 = st.slider("3. 证据整合力", 0, 10, 0)
        s4 = st.slider("4. 转化洞察力", 0, 10, 0)

        st.divider()
        turing = st.radio("🕵️ 科学图灵测试：", ["资深科学家", "初级研究员", "AI模型"], horizontal=True)
        feedback = st.text_area("综合评语")

        submit_button = st.form_submit_button("🚀 提交本篇评估", use_container_width=True)

# --- 5. 评分保存逻辑 ---
if submit_button:
    # 逻辑检查：是否写了姓名，且是否打了分（防止误触全0提交）
    if not expert_name:
        st.error("⚠️ 请在左侧填写您的姓名。")
    elif (s1 + s2 + s3 + s4) == 0:
        st.error("⚠️ 请完成所有评分指标后再提交（分值不能全部为0）。")
    else:
        result_entry = {
            "专家": expert_name,
            "文献ID": current_doc_id,
            "提交时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "1_逻辑严密性": s1,
            "2_生物学合理性": s2,
            "3_证据整合力": s3,
            "4_转化洞察力": s4,
            "图灵测试猜想": turing,
            "评语": feedback
        }

        results_df = pd.DataFrame([result_entry])

        try:
            if not os.path.isfile(results_file):
                results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
            else:
                results_df.to_csv(results_file, mode='a', header=False, index=False, encoding='utf-8-sig')

            st.balloons()
            # 关键：清除缓存以更新已评审状态
            st.cache_data.clear()
            st.success("✅ 评价提交成功！正在更新状态...")
            st.rerun()

        except Exception as e:
            st.error(f"保存失败: {e}")

st.divider()
st.caption("表型大模型科研评价系统 v2.1 | 具备状态跟踪功能")