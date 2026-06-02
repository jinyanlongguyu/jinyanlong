#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金艳龙AI税务助手 - Web 界面（支持真实 DeepSeek AI）
运行：streamlit run tax_web_app.py

API Key 配置优先级：
  1. 侧边栏手动输入（最高）
  2. .streamlit/secrets.toml 或 Streamlit Cloud secrets
  3. .env 文件中的 DEEPSEEK_API_KEY
  4. 未配置则使用模拟模式
"""

import sys
import os
import json
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 启动时加载 .env 文件
load_dotenv()

# 导入计算参数
from tax_calculator import (
    SOCIAL_INSURANCE_ACTUAL,
    SOCIAL_INSURANCE_COMPANY,
    BASIC_DEDUCTION,
    calc_corporate_income_tax_quarterly,
    format_corporate_tax_report,
)

# ===============================================
#  DeepSeek AI 配置
# ===============================================

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# 从 .env 读取默认 Key
ENV_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


def get_api_key():
    """获取当前生效的 API Key（手动输入 > st.secrets > .env）"""
    # 1. 侧边栏手动输入（最高优先级）
    manual_key = st.session_state.get("deepseek_api_key_manual", "")
    if manual_key:
        return manual_key, "manual"
    # 2. Streamlit Cloud secrets
    try:
        if "DEEPSEEK_API_KEY" in st.secrets:
            return st.secrets["DEEPSEEK_API_KEY"], "secrets"
    except Exception:
        pass
    # 3. .env 文件
    if ENV_API_KEY:
        return ENV_API_KEY, "env"
    return "", "none"


def ask_deepseek(prompt: str, system_prompt: str = None) -> str:
    """调用 DeepSeek API"""
    api_key, _ = get_api_key()
    if not api_key:
        return "[未配置 API Key，跳过 AI 生成]"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[AI 调用失败: {e}]"


# ===============================================
#  核心计算函数
# ===============================================

def calc_one_employee(
    name, gross_salary, si_base, si_personal,
    special_total, child_edu, infant_care, elderly_care,
    housing_fund_personal=0.0,
) -> dict:
    """计算单名员工"""
    taxable_income = (
        gross_salary
        - si_personal
        - housing_fund_personal
        - BASIC_DEDUCTION
        - special_total
    )

    if taxable_income <= 0:
        tax = 0.0
        taxable_income = 0.0
    else:
        if taxable_income <= 3000:
            rate, deduction = 0.03, 0
        elif taxable_income <= 12000:
            rate, deduction = 0.10, 210
        elif taxable_income <= 25000:
            rate, deduction = 0.20, 1410
        elif taxable_income <= 35000:
            rate, deduction = 0.25, 2660
        elif taxable_income <= 55000:
            rate, deduction = 0.30, 4410
        elif taxable_income <= 80000:
            rate, deduction = 0.35, 7160
        else:
            rate, deduction = 0.45, 15160

        tax = taxable_income * rate - deduction

    net_salary = gross_salary - si_personal - housing_fund_personal - round(tax, 2)

    si_company = (
        si_base * SOCIAL_INSURANCE_COMPANY["pension"]
        + si_base * SOCIAL_INSURANCE_COMPANY["medical"]
        + si_base * SOCIAL_INSURANCE_COMPANY["unemployment"]
        + si_base * SOCIAL_INSURANCE_COMPANY["injury"]
    )
    total_cost = gross_salary + si_company

    return {
        "姓名": name,
        "税前工资": gross_salary,
        "个人社保": si_personal,
        "专项附加扣除": special_total,
        "子女教育": child_edu,
        "婴幼儿照护": infant_care,
        "赡养老人": elderly_care,
        "应税收入": round(taxable_income, 2),
        "应纳税额": round(tax, 2),
        "实发工资": round(net_salary, 2),
        "公司社保承担": round(si_company, 2),
        "公司用人总成本": round(total_cost, 2),
    }


# ===============================================
#  AI 申报说明生成
# ===============================================

def generate_tax_report_ai(results: list) -> str:
    """生成个税申报说明（真实 AI 或模拟）"""
    now = datetime.now()
    api_key, _ = get_api_key()
    use_ai = bool(api_key)

    if use_ai:
        rows_text = ""
        for r in results:
            rows_text += (
                f"员工 {r['姓名']}：税前工资 {r['税前工资']} 元，"
                f"个人社保 {r['个人社保']} 元，"
                f"专项附加扣除 {r['专项附加扣除']} 元"
                f"（子女教育 {r['子女教育']} 元，婴幼儿照护 {r['婴幼儿照护']} 元，"
                f"赡养老人 {r['赡养老人']} 元），"
                f"应税收入 {r['应税收入']} 元，应纳税额 {r['应纳税额']} 元，"
                f"实发工资 {r['实发工资']} 元。\n"
            )

        company_si_total = sum(r["公司社保承担"] for r in results)
        total_tax = sum(r["应纳税额"] for r in results)
        total_cost = sum(r["公司用人总成本"] for r in results)

        prompt = f"""你是一位专业的税务顾问，请为以下企业{now.year}年{now.month}月的个税及社保申报撰写一份专业的申报说明。

## 员工数据
{rows_text}
## 汇总数据
- 公司承担社保总额：{company_si_total} 元
- 全体员工应纳税额合计：{total_tax} 元
- 公司用人总成本：{total_cost} 元

## 要求
1. 以"武汉金艳龙科技有限公司 {now.year}年{now.month}月 税务申报说明"为标题
2. 分四个部分：一、申报概况；二、员工个税明细；三、社保缴纳说明；四、申报注意事项
3. 语气专业、简洁，适合财务提交给税务局或留存备案
4. 提醒用户核对专项附加扣除信息是否已及时更新（个税APP）
5. 说明社保基数如有调整请以社保局核定为准
6. 总字数控制在 500-800 字
7. 用中文输出，不要输出英文
"""

        ai_result = ask_deepseek(
            prompt,
            system_prompt="你是一位专业的税务顾问，擅长撰写企业税务申报说明。"
        )
        if not ai_result.startswith("["):
            return ai_result

    # 模拟模式
    has_tax = any(r["应纳税额"] > 0 for r in results)
    lines = [f"【{now.year}年{now.month}月个税申报说明】", ""]
    lines.append(f"本月公司共有 {len(results)} 名员工需进行个税申报。")
    if has_tax:
        total_tax = sum(r["应纳税额"] for r in results)
        lines.append(f"本月应纳个税合计 {total_tax:.2f} 元，请及时在自然人电子税务局（扣缴端）完成申报缴税。")
    else:
        lines.append("经计算，本月所有员工应税收入均为 0 元，无需缴纳个税。请在自然人电子税务局进行零申报操作。")
    lines.append("")
    lines.append("【扣除项说明】")
    for r in results:
        lines.append(
            f"  {r['姓名']}：社保扣除 {r['个人社保']} 元，"
            f"专项附加扣除 {r['专项附加扣除']} 元"
            f"（子女教育{r['子女教育']}+婴幼儿{r['婴幼儿照护']}+赡养老人{r['赡养老人']}）。"
        )
    lines.append("")
    lines.append("【注意事项】")
    lines.append("  1. 请核实员工专项附加扣除信息是否最新；")
    lines.append("  2. 社保基数如有调整，请及时更新系统参数；")
    lines.append("  3. 零申报也需按时提交，避免产生逾期记录。")
    lines.append("")
    lines.append("—— 由 金艳龙AI税务助手 自动生成")
    return "\n".join(lines)


def generate_social_report_ai(results: list) -> str:
    """生成社保申报说明（真实 AI 或模拟）"""
    now = datetime.now()
    api_key, _ = get_api_key()
    use_ai = bool(api_key)

    if use_ai:
        rows_text = ""
        for r in results:
            rows_text += (
                f"  员工{r['姓名']}：缴费基数 5000 元，"
                f"公司社保承担 {r['公司社保承担']} 元，"
                f"个人社保 {r['个人社保']} 元。\n"
            )
        total_si = sum(r["公司社保承担"] for r in results)

        prompt = f"""请为武汉金艳龙科技有限公司生成 {now.year}年{now.month}月 的社保申报操作说明。

社保数据：
{rows_text}
汇总：公司承担社保合计 {total_si} 元。

要求：
1. 说明社保缴纳明细和公司承担部分
2. 提供操作指引（登录湖北政务服务网，进入单位社保申报模块）
3. 提醒申报截止时间和注意事项
4. 语气专业，200-300 字，用中文输出
"""

        ai_result = ask_deepseek(prompt)
        if not ai_result.startswith("["):
            return ai_result

    # 模拟模式
    total_si = sum(r["公司社保承担"] for r in results)
    lines = [
        f"【{now.year}年{now.month}月社保申报说明】",
        "",
        f"本月需为 {len(results)} 名员工缴纳社保，公司承担部分合计 {total_si:.2f} 元。",
        "",
        "【缴费明细】",
    ]
    for r in results:
        lines.append(
            f"  {r['姓名']}：缴费基数 5000 元，"
            f"公司承担 {r['公司社保承担']} 元，"
            f"个人承担 {r['个人社保']} 元。"
        )
    lines.append("")
    lines.append("【操作指引】")
    lines.append("  1. 登录「湖北政务服务网」或「武汉社保申报系统」；")
    lines.append("  2. 进入「单位社保申报」模块，核对人员名单；")
    lines.append("  3. 确认缴费基数无误后提交申报；")
    lines.append("  4. 缴费成功后留存缴费凭证备查。")
    lines.append("")
    lines.append("【注意事项】")
    lines.append("  社保申报截止时间为每月 25 日，请提前办理。")
    lines.append("")
    lines.append("—— 由 金艳龙AI税务助手 自动生成")
    return "\n".join(lines)


# ===============================================
#  生成上传模板（内存中）
# ===============================================

def get_template_df():
    """返回示范用的上传模板 DataFrame"""
    return pd.DataFrame([
        {
            "姓名": "员工A",
            "税前工资": 10522,
            "社保基数": 5000,
            "个人社保实缴": 522,
            "专项附加扣除": 5000,
            "子女教育": 2000,
            "婴幼儿照护": 2000,
            "赡养老人": 1000,
        },
        {
            "姓名": "员工B",
            "税前工资": 8000,
            "社保基数": 5000,
            "个人社保实缴": 522,
            "专项附加扣除": 0,
            "子女教育": 0,
            "婴幼儿照护": 0,
            "赡养老人": 0,
        },
    ])


# ===============================================
#  页面配置
# ===============================================

st.set_page_config(
    page_title="金艳龙AI税务助手",
    page_icon="💰",
    layout="wide",
)

# ===============================================
#  侧边栏
# ===============================================

with st.sidebar:
    st.title("⚙️ 配置")

    # API Key 状态显示
    st.subheader("DeepSeek AI")
    current_key, key_source = get_api_key()

    if key_source in ("secrets", "env"):
        st.success("✅ 已通过配置文件配置 API Key")
        st.caption("如需临时覆盖，可在下方输入")
    elif key_source == "manual":
        st.success("✅ 已手动配置 API Key")
    else:
        st.warning("⚠️ 未配置 API Key")
        st.caption("请在 .streamlit/secrets.toml 中添加 DEEPSEEK_API_KEY=sk-xxx，或在下方输入")

    # 手动输入（可覆盖 .env）
    api_key_manual = st.text_input(
        "手动输入 API Key（可选，覆盖配置文件）",
        value=st.session_state.get("deepseek_api_key_manual", ""),
        type="password",
        help="在 platform.deepseek.com 获取。留空则使用配置文件中的配置。",
        key="deepseek_api_key_manual_input",
    )
    # 同步到 session_state
    if api_key_manual != st.session_state.get("deepseek_api_key_manual", ""):
        st.session_state["deepseek_api_key_manual"] = api_key_manual
        st.rerun()

    # 测试连接按钮
    if st.button("🔍 测试 AI 连接", use_container_width=True):
        test_result = ask_deepseek("请用一句话介绍你自己")
        if test_result.startswith("["):
            st.error(f"连接失败：{test_result}")
        else:
            st.success("✅ AI 连接成功！")
            st.caption(test_result[:100] + "...")

    st.divider()

    # 社保参数说明
    st.caption("武汉社保参数（2026）")
    st.markdown("**个人社保**")
    st.markdown("- 养老 8%\n- 医疗 2%\n- 失业 0.5%")
    st.markdown("**公司社保**")
    st.markdown("- 养老 16%\n- 医疗 8.7%\n- 失业 0.5%\n- 工伤 0.4%")
    st.markdown(f"**个税起征点**：{BASIC_DEDUCTION} 元/月")

    st.divider()
    st.caption("金艳龙AI税务助手 v1.3")
    st.caption("仅供参考，申报前请核实")

# ===============================================
#  主界面
# ===============================================

st.title("💰 金艳龙AI税务助手")
st.caption("武汉金艳龙科技有限公司 · 个税/社保计算 + AI 申报说明生成")

tab1, tab2, tab3, tab4 = st.tabs(["💰 工资计算", "📋 批量导入", "📄 申报说明", "📊 季度申报"])

# ---- Tab1：手动录入 ----
with tab1:
    st.header("员工工资录入")

    num_emp = st.number_input(
        "员工人数", min_value=1, max_value=20, value=1, step=1
    )

    employees_data = []

    for i in range(num_emp):
        st.divider()
        st.subheader(f"员工 {i+1}")

        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(
                "姓名", value=f"员工{i+1}", key=f"name_{i}"
            )
            salary = st.number_input(
                "税前工资（元）", min_value=0.0,
                value=10522.0 if i == 0 else 8000.0,
                step=100.0, key=f"salary_{i}"
            )
            si_base = st.number_input(
                "社保缴费基数（元）", min_value=0.0,
                value=5000.0, step=100.0, key=f"si_base_{i}"
            )
        with c2:
            si_personal = st.number_input(
                "个人社保实缴（元）", min_value=0.0,
                value=float(SOCIAL_INSURANCE_ACTUAL),
                step=10.0, key=f"si_personal_{i}"
            )
            special = st.number_input(
                "专项附加扣除合计（元）", min_value=0.0,
                value=5000.0 if i == 0 else 0.0,
                step=500.0, key=f"special_{i}"
            )
            st.markdown("**专项附加扣除明细**")
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                child = st.number_input(
                    "子女教育", min_value=0.0,
                    value=2000.0 if i == 0 else 0.0,
                    step=500.0, key=f"child_{i}"
                )
            with cc2:
                infant = st.number_input(
                    "婴幼儿照护", min_value=0.0,
                    value=2000.0 if i == 0 else 0.0,
                    step=500.0, key=f"infant_{i}"
                )
            with cc3:
                elderly = st.number_input(
                    "赡养老人", min_value=0.0,
                    value=1000.0 if i == 0 else 0.0,
                    step=500.0, key=f"elderly_{i}"
                )

        employees_data.append({
            "name": name,
            "gross_salary": salary,
            "si_base": si_base,
            "si_personal_actual": si_personal,
            "special_deductions": special,
            "child_education": child,
            "infant_care": infant,
            "elderly_care": elderly,
        })

    if st.button("🚀 开始计算", use_container_width=True, type="primary"):
        results = []
        for emp in employees_data:
            r = calc_one_employee(
                emp["name"],
                emp["gross_salary"],
                emp["si_base"],
                emp["si_personal_actual"],
                emp["special_deductions"],
                emp["child_education"],
                emp["infant_care"],
                emp["elderly_care"],
            )
            results.append(r)

        st.session_state["results"] = results
        st.success("✅ 计算完成！")

        df = pd.DataFrame(results)
        st.subheader("📊 计算结果")
        # 只对数字列格式化
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
        st.dataframe(
            df.style.format("{:.2f}", subset=numeric_cols),
            use_container_width=True,
        )

        # 汇总
        st.subheader("📈 汇总")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("工资总额", f"{df['税前工资'].sum():.2f} 元")
        m2.metric("个税总额", f"{df['应纳税额'].sum():.2f} 元")
        m3.metric("实发总额", f"{df['实发工资'].sum():.2f} 元")
        m4.metric("公司总成本", f"{df['公司用人总成本'].sum():.2f} 元")

        # 下载 CSV
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 下载申报底稿（CSV）",
            data=csv_data,
            file_name=f"申报底稿_{datetime.now().strftime('%Y%m')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ---- Tab2：批量导入 ----
with tab2:
    st.header("批量导入员工工资表")

    # 上传说明 + 下载模板 并排
    col_info, col_template = st.columns([2, 1])
    with col_info:
        st.info(
            "请上传 CSV 或 Excel 文件，需包含以下列：\n"
            "姓名, 税前工资, 社保基数, 个人社保实缴, 专项附加扣除, "
            "子女教育, 婴幼儿照护, 赡养老人"
        )
    with col_template:
        # 读取本地模板文件提供下载
        template_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "申报底稿模板.csv")
        if os.path.exists(template_csv_path):
            with open(template_csv_path, "rb") as f:
                csv_bytes = f.read()
            st.download_button(
                label="📥 下载上传模板（CSV）",
                data=csv_bytes,
                file_name="申报底稿模板.csv",
                mime="text/csv",
                use_container_width=True,
            )
        # Excel 模板
        template_xlsx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "申报底稿模板.xlsx")
        if os.path.exists(template_xlsx_path):
            with open(template_xlsx_path, "rb") as f:
                xlsx_bytes = f.read()
            st.download_button(
                label="📥 下载上传模板（Excel）",
                data=xlsx_bytes,
                file_name="申报底稿模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    st.divider()

    uploaded = st.file_uploader(
        "选择文件上传", type=["csv", "xlsx", "xls"], key="uploader"
    )

    if uploaded is not None:
        try:
            # 每次上传新文件时，重新读取并缓存到 session_state
            file_id = getattr(uploaded, "file_id", id(uploaded))
            if st.session_state.get("_uploaded_file_id") != file_id:
                if uploaded.name.endswith(".csv"):
                    try:
                        df_up = pd.read_csv(uploaded, encoding="utf-8-sig")
                    except Exception:
                        uploaded.seek(0)
                        df_up = pd.read_csv(uploaded, encoding="gbk")
                else:
                    df_up = pd.read_excel(uploaded)
                st.session_state["_uploaded_df"] = df_up
                st.session_state["_uploaded_file_id"] = file_id
            else:
                df_up = st.session_state["_uploaded_df"]

            st.write("文件预览：")
            st.dataframe(df_up.head(), use_container_width=True)

            if st.button("🚀 导入并计算", key="btn_upload"):
                results = []
                for _, row in df_up.iterrows():
                    r = calc_one_employee(
                        str(row.get("姓名", "员工")),
                        float(row.get("税前工资") or 0),
                        float(row.get("社保基数") or 5000),
                        float(row.get("个人社保实缴") or SOCIAL_INSURANCE_ACTUAL),
                        float(row.get("专项附加扣除") or 0),
                        float(row.get("子女教育") or 0),
                        float(row.get("婴幼儿照护") or 0),
                        float(row.get("赡养老人") or 0),
                    )
                    results.append(r)

                st.session_state["results"] = results

                df_result = pd.DataFrame(results)
                st.success(f"✅ 计算完成！共 {len(results)} 名员工")
                numeric_cols = df_result.select_dtypes(include=["float64", "int64"]).columns
                st.dataframe(
                    df_result.style.format("{:.2f}", subset=numeric_cols),
                    use_container_width=True,
                )

                csv_data = df_result.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 下载申报底稿（CSV）",
                    data=csv_data,
                    file_name=f"申报底稿_{datetime.now().strftime('%Y%m')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        except Exception as e:
            st.error(f"文件读取失败：{e}")

# ---- Tab3：申报说明 ----
with tab3:
    st.header("AI 申报说明")

    if "results" not in st.session_state:
        st.info("请先在「工资计算」页面完成计算，再查看申报说明。")
    else:
        results = st.session_state["results"]
        now_str = datetime.now().strftime("%Y年%m月")

        # 个税说明
        st.subheader("📄 个税申报说明")
        with st.spinner("AI 正在生成个税申报说明..."):
            tax_text = generate_tax_report_ai(results)
        st.text_area("个税申报说明", tax_text, height=400, key="tax_area")

        # 社保说明
        st.subheader("📄 社保申报说明")
        with st.spinner("AI 正在生成社保申报说明..."):
            social_text = generate_social_report_ai(results)
        st.text_area("社保申报说明", social_text, height=400, key="social_area")

        # 下载
        full_text = tax_text + "\n\n" + "=" * 50 + "\n\n" + social_text
        st.download_button(
            label="📥 下载申报说明（TXT）",
            data=full_text,
            file_name=f"申报说明_{datetime.now().strftime('%Y%m')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ===============================================
#  季度申报数据持久化
# ===============================================

QUARTER_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "季度申报数据.json")


def load_quarter_data(year: int) -> dict:
    """加载某年度的季度申报数据"""
    if not os.path.exists(QUARTER_DATA_FILE):
        return {}
    try:
        with open(QUARTER_DATA_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
            return all_data.get(str(year), {})
    except Exception:
        return {}


def save_quarter_data(year: int, quarter: int, data: dict):
    """保存季度申报数据"""
    if os.path.exists(QUARTER_DATA_FILE):
        with open(QUARTER_DATA_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    else:
        all_data = {}

    if str(year) not in all_data:
        all_data[str(year)] = {}

    all_data[str(year)][str(quarter)] = data
    all_data[str(year)]["_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(QUARTER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)


def get_ytd_values(year: int, quarter: int) -> dict:
    """获取本年累计值（基于已保存的上季度数据）"""
    data = load_quarter_data(year)
    ytd_revenue = 0.0
    ytd_cost = 0.0
    ytd_profit = 0.0

    for q in range(1, quarter):
        if str(q) in data:
            q_data = data[str(q)]
            ytd_revenue += q_data.get("revenue", 0)
            ytd_cost += q_data.get("cost", 0)
            ytd_profit += q_data.get("period_profit", 0)

    return {
        "ytd_revenue": ytd_revenue,
        "ytd_cost": ytd_cost,
        "ytd_profit": ytd_profit,
    }


# ===============================================
#  Tab4：季度企业所得税申报
# ===============================================

# ---- Tab4：季度企业所得税申报 ----
with tab4:
    st.header("📊 企业所得税季度预缴申报")

    st.info(
        "小型微利企业优惠税率 5%（2024-2027年政策）。\n"
        "系统会自动加载上季度数据，计算本年累计值。"
    )

    # ========== 季度选择 ==========
    col_q, col_y = st.columns([1, 1])
    with col_q:
        quarter = st.selectbox("申报季度", [1, 2, 3, 4], index=min(datetime.now().month // 3, 3))
    with col_y:
        year = st.number_input("年度", min_value=2024, max_value=2030, value=datetime.now().year)

    # ========== 加载上季度数据 ==========
    ytd = get_ytd_values(year, quarter)
    prev_saved = load_quarter_data(year)

    if quarter > 1 and str(quarter - 1) in prev_saved:
        st.success(
            f"✅ 已加载 Q{quarter-1} 数据："
            f"累计收入 {ytd['ytd_revenue']:.2f} 元，"
            f"累计利润 {ytd['ytd_profit']:.2f} 元"
        )

    st.divider()

    # ========== 银行流水导入区域 ==========
    with st.expander("📥 导入银行流水（自动填表）", expanded=False):
        st.caption("支持民生银行、建设银行等 CSV/Excel 流水文件，自动分类并填入下方表单")

        bank_file = st.file_uploader(
            "上传银行流水文件（可多次上传不同银行）",
            type=["csv", "xlsx", "xls"],
            key="bank_uploader",
            accept_multiple_files=True,
        )

        if bank_file:
            try:
                all_txns = []
                for bf in bank_file:
                    # 读取文件
                    if bf.name.endswith(".csv"):
                        try:
                            df_bank = pd.read_csv(bf, encoding="utf-8-sig")
                        except Exception:
                            bf.seek(0)
                            df_bank = pd.read_csv(bf, encoding="gbk")
                    else:
                        df_bank = pd.read_excel(bf)

                    # 统一列名（常见银行格式兼容）
                    col_map = {}
                    for col in df_bank.columns:
                        col_lower = str(col).strip().lower()
                        if any(k in col_lower for k in ["日期", "date", "交易日期", "记账日期"]):
                            col_map[col] = "交易日期"
                        elif any(k in col_lower for k in ["摘要", "备注", "用途", "description", "摘要说明"]):
                            col_map[col] = "摘要"
                        elif any(k in col_lower for k in ["收入", "贷方", "存款", "credit", "存入"]):
                            col_map[col] = "收入金额"
                        elif any(k in col_lower for k in ["支出", "借方", "取款", "debit", "转出"]):
                            col_map[col] = "支出金额"
                        elif any(k in col_lower for k in ["金额", "发生额", "transaction"]):
                            col_map[col] = "金额"
                        elif any(k in col_lower for k in ["余额", "balance"]):
                            col_map[col] = "余额"
                        elif any(k in col_lower for k in ["借贷", "收支方向", "类型"]):
                            col_map[col] = "借贷标识"

                    df_bank = df_bank.rename(columns=col_map)

                    # 如果没有明确的收入/支出列，尝试从"金额"+"借贷标识"推断
                    if "金额" in df_bank.columns and "借贷标识" in df_bank.columns:
                        for _, row in df_bank.iterrows():
                            amount = abs(float(row.get("金额") or 0))
                            flag = str(row.get("借贷标识", "")).strip()
                            txn = {
                                "银行": bf.name,
                                "日期": row.get("交易日期", ""),
                                "摘要": row.get("摘要", ""),
                                "收入金额": amount if flag in ["贷", "收入", "存入", "CREDIT"] else 0,
                                "支出金额": amount if flag in ["借", "支出", "转出", "DEBIT"] else 0,
                            }
                            all_txns.append(txn)
                    else:
                        # 直接取收入/支出列
                        for _, row in df_bank.iterrows():
                            all_txns.append({
                                "银行": bf.name,
                                "日期": row.get("交易日期", row.get("日期", "")),
                                "摘要": row.get("摘要", ""),
                                "收入金额": float(row.get("收入金额", 0) or 0),
                                "支出金额": float(row.get("支出金额", 0) or 0),
                            })

                df_txns = pd.DataFrame(all_txns)
                st.success(f"✅ 成功读取 {len(df_txns)} 条交易记录")

                # 简单分类（根据关键词）
                def classify_txn(desc):
                    desc = str(desc).lower()
                    if any(k in desc for k in ["货款", "收入", "销售", "服务费", "咨询费", "收款"]):
                        return "营业收入"
                    elif any(k in desc for k in ["工资", "社保", "公积金", "福利"]):
                        return "管理费用-人工"
                    elif any(k in desc for k in ["水电", "物业", "房租", "租赁"]):
                        return "管理费用-办公"
                    elif any(k in desc for k in ["采购", "进货", "成本", "材料"]):
                        return "营业成本"
                    elif any(k in desc for k in ["报销", "差旅", "交通", "餐饮", "办公用品"]):
                        return "管理费用-其他"
                    elif any(k in desc for k in ["税", "费"]):
                        return "税金及附加"
                    else:
                        return "待分类"

                df_txns["自动分类"] = df_txns["摘要"].apply(classify_txn)
                st.dataframe(df_txns[["日期", "摘要", "收入金额", "支出金额", "自动分类"]].head(10), use_container_width=True)

                st.subheader("请确认交易分类（可手动修改）")
                edited_df = st.data_editor(
                    df_txns[["日期", "摘要", "收入金额", "支出金额", "自动分类"]],
                    use_container_width=True,
                    num_rows="dynamic",
                    key="txn_editor",
                )

                # 计算汇总
                revenue_total = edited_df[edited_df["自动分类"] == "营业收入"]["收入金额"].sum()
                cost_total = edited_df[edited_df["自动分类"] == "营业成本"]["支出金额"].sum()
                expense_total = edited_df[edited_df["自动分类"].str.contains("管理费用", na=False)]["支出金额"].sum()
                profit = revenue_total - cost_total - expense_total

                st.subheader("📈 自动汇总结果（本期）")
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("营业收入", f"{revenue_total:.2f}")
                col_b.metric("营业成本", f"{cost_total:.2f}")
                col_c.metric("管理费用", f"{expense_total:.2f}")
                col_d.metric("利润总额", f"{profit:.2f}")

                if st.button("✅ 确认并填入申报表", use_container_width=True, type="primary", key="btn_fill_quarter"):
                    st.session_state["auto_revenue"] = revenue_total
                    st.session_state["auto_cost"] = cost_total
                    st.session_state["auto_profit"] = profit
                    st.success("✅ 已自动填入申报表，请向下滚动确认数据！")
                    st.rerun()

            except Exception as e:
                st.error(f"银行流水解析失败：{e}")
                st.caption("请确保文件包含：日期、摘要、收入金额、支出金额 等列")

    st.divider()

    # ========== 手动输入区域 ==========
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("本期数（Q" + str(quarter) + "）")

        # 自动填入（如果银行流水导入了）
        rev_val = st.session_state.get("auto_revenue", 0.0)
        revenue = st.number_input("季度营业收入（元）", min_value=0.0, value=rev_val, step=1000.0, key="q_revenue")

        cost_val = st.session_state.get("auto_cost", 0.0)
        cost = st.number_input("季度营业成本（元）", min_value=0.0, value=cost_val, step=1000.0, key="q_cost")

    with c2:
        st.subheader("本期利润及企业信息")

        profit_val = st.session_state.get("auto_profit", 0.0)
        period_profit = st.number_input("季度利润总额（元）", value=profit_val, step=1000.0, key="q_profit")

        num_employees = st.number_input("季度平均从业人数", min_value=1, value=1, step=1)
        total_assets = st.number_input("季度平均资产总额（万元）", min_value=0.0, value=0.0, step=10.0)

    # ========== 累计数（自动计算）==========
    st.divider()
    st.subheader("📈 累计数（自动计算）")

    ytd_revenue = ytd["ytd_revenue"] + revenue
    ytd_cost = ytd["ytd_cost"] + cost
    ytd_profit = ytd["ytd_profit"] + period_profit

    col_y1, col_y2, col_y3 = st.columns(3)
    col_y1.metric("本年累计营业收入", f"{ytd_revenue:.2f} 元")
    col_y2.metric("本年累计营业成本", f"{ytd_cost:.2f} 元")
    col_y3.metric("本年累计利润总额", f"{ytd_profit:.2f} 元")

    # ========== 计算按钮 ==========
    st.divider()

    if st.button("🚀 计算季度预缴税额", use_container_width=True, type="primary"):
        result = calc_corporate_income_tax_quarterly(
            revenue, cost, period_profit, ytd_profit,
            int(num_employees), total_assets,
        )
        st.session_state["corp_tax_result"] = result

        # 保存本期数据
        save_quarter_data(year, quarter, {
            "revenue": revenue,
            "cost": cost,
            "period_profit": period_profit,
            "ytd_revenue": ytd_revenue,
            "ytd_cost": ytd_cost,
            "ytd_profit": ytd_profit,
            "num_employees": int(num_employees),
            "total_assets": total_assets,
            "tax_payable": result["本期应纳税额"],
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        st.success(f"✅ 计算完成！Q{quarter} 数据已保存，下次申报 Q{quarter+1} 时会自动加载。")

    # ========== 计算结果展示 ==========
    if "corp_tax_result" in st.session_state:
        r = st.session_state["corp_tax_result"]

        st.subheader("📈 计算结果")
        m1, m2, m3 = st.columns(3)
        m1.metric("季度利润总额", f"{r['利润总额']:.2f} 元")
        m2.metric("应纳税所得额", f"{r['应纳税所得额']:.2f} 元")
        m3.metric("本期应纳税额", f"{r['本期应纳税额']:.2f} 元")

        # 详细结果表格
        df_corp = pd.DataFrame([r])
        numeric_cols = df_corp.select_dtypes(include=["float64", "int64"]).columns
        st.dataframe(
            df_corp.style.format("{:.2f}", subset=numeric_cols),
            use_container_width=True,
        )

        # AI 申报说明
        st.subheader("📄 申报说明")
        report_text = format_corporate_tax_report(r, quarter, year)
        st.text_area("申报说明", report_text, height=350, key="corp_tax_area")

        # 下载
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 下载申报说明（TXT）",
                data=report_text,
                file_name=f"企业所得税预缴申报_{year}Q{quarter}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_dl2:
            csv_corp = df_corp.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 下载申报底稿（CSV）",
                data=csv_corp,
                file_name=f"企业所得税预缴申报_{year}Q{quarter}.csv",
                mime="text/csv",
                use_container_width=True,
            )
