#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武汉金艳龙科技有限公司 - 个税/社保计算脚本（MVP版）
适用场景：零申报企业，有工资发放和社保缴纳
运行：python tax_calculator.py
"""

from datetime import datetime

# ========== 配置区（按实际情况修改）==========

# 社保参数（武汉，缴费基数5000）
SOCIAL_INSURANCE = {
    "pension_personal": 0.08,      # 养老个人 8%
    "medical_personal": 0.02,       # 医疗个人 2%
    "unemployment_personal": 0.005, # 失业个人 0.5%
}

# 实际个人社保总额（武汉社保局实扣，优先使用此值）
SOCIAL_INSURANCE_ACTUAL = 522  # 元/月

# 公司社保部分（武汉）
SOCIAL_INSURANCE_COMPANY = {
    "pension": 0.16,       # 养老单位 16%
    "medical": 0.087,       # 医疗单位 ~8.7%
    "unemployment": 0.005,  # 失业单位 0.5%
    "injury": 0.004,        # 工伤单位 ~0.4%
}

# 公积金（当前未缴纳）
HOUSING_FUND_PERSONAL_RATE = 0.0
HOUSING_FUND_COMPANY_RATE = 0.0

# 个税累进税率表（2024-2026年7级超额累进）
TAX_BRACKETS = [
    (0,       3000,   0.03, 0),
    (3000,    12000,  0.10, 210),
    (12000,   25000,  0.20, 1410),
    (25000,   35000,  0.25, 2660),
    (35000,   55000,  0.30, 4410),
    (55000,   80000,  0.35, 7160),
    (80000,   float('inf'), 0.45, 15160),
]

BASIC_DEDUCTION = 5000  # 基本减除费用（起征点）

# ===============================================


def calc_social_insurance_company(base=5000):
    """计算公司社保部分"""
    return (
        base * SOCIAL_INSURANCE_COMPANY["pension"]
        + base * SOCIAL_INSURANCE_COMPANY["medical"]
        + base * SOCIAL_INSURANCE_COMPANY["unemployment"]
        + base * SOCIAL_INSURANCE_COMPANY["injury"]
    )


def calc_income_tax(
    gross_salary: float,
    social_insurance_personal: float,
    housing_fund_personal: float,
    special_deductions: float,
) -> tuple[float, float]:
    """
    计算个人所得税
    返回：(应纳税额, 应税收入)
    """
    taxable_income = (
        gross_salary
        - social_insurance_personal
        - housing_fund_personal
        - BASIC_DEDUCTION
        - special_deductions
    )

    if taxable_income <= 0:
        return 0.0, 0.0

    # 查找适用税率
    tax_rate = 0.03
    quick_deduction = 0
    for lower, upper, rate, deduction in TAX_BRACKETS:
        if lower < taxable_income <= upper:
            tax_rate = rate
            quick_deduction = deduction
            break

    tax = taxable_income * tax_rate - quick_deduction
    return round(tax, 2), round(taxable_income, 2)


def format_money(val: float) -> str:
    """格式化金额显示"""
    return f"{val:,.2f}"


def process_employees(employees: list[dict]) -> list[dict]:
    """
    处理员工列表，返回计算结果
    employees 每项格式：
    {
        "name": "员工A",
        "gross_salary": 10522,
        "si_base": 5000,
        "si_personal_actual": 522,   # 个人社保实缴，不传则用 SOCIAL_INSURANCE_ACTUAL
        "special_deductions": 5000,   # 专项附加扣除合计
        "child_education": 2000,     # 明细（可选，用于底稿）
        "infant_care": 2000,
        "elderly_care": 1000,
    }
    """
    results = []

    for emp in employees:
        gross = emp["gross_salary"]
        si_base = emp.get("si_base", 5000)
        si_personal = emp.get("si_personal_actual", SOCIAL_INSURANCE_ACTUAL)
        hf_personal = emp.get("gross_salary", 0) * HOUSING_FUND_PERSONAL_RATE
        if emp.get("housing_fund_personal"):
            hf_personal = emp["housing_fund_personal"]
        special = emp.get("special_deductions", 0)

        tax, taxable_income = calc_income_tax(
            gross, si_personal, hf_personal, special
        )

        net_salary = gross - si_personal - hf_personal - tax
        si_company = calc_social_insurance_company(si_base)
        hf_company = si_base * HOUSING_FUND_COMPANY_RATE
        total_cost = gross + si_company + hf_company

        results.append({
            "姓名": emp["name"],
            "税前工资": gross,
            "个人社保": si_personal,
            "个人公积金": hf_personal,
            "专项附加扣除": special,
            "应税收入": taxable_income,
            "应纳税额": tax,
            "实发工资": round(net_salary, 2),
            "公司社保承担": round(si_company, 2),
            "公司公积金承担": round(hf_company, 2),
            "公司用人总成本": round(total_cost, 2),
            # 明细（用于底稿）
            "子女教育": emp.get("child_education", 0),
            "婴幼儿照护": emp.get("infant_care", 0),
            "赡养老人": emp.get("elderly_care", 0),
        })

    return results


def print_results(results: list[dict]):
    """打印计算结果"""
    print("\n" + "=" * 70)
    print("  个税/社保计算结果  |  武汉金艳龙科技有限公司")
    print("=" * 70)

    for r in results:
        print(f"\n【{r['姓名']}】")
        print(f"  税前工资：      {format_money(r['税前工资'])} 元")
        print(f"  个人社保扣款：  {format_money(r['个人社保'])} 元")
        print(f"  专项附加扣除：  {format_money(r['专项附加扣除'])} 元")
        print(f"    ├─ 子女教育： {format_money(r['子女教育'])} 元")
        print(f"    ├─ 婴幼儿照护：{format_money(r['婴幼儿照护'])} 元")
        print(f"    └─ 赡养老人： {format_money(r['赡养老人'])} 元")
        print(f"  应税收入：      {format_money(r['应税收入'])} 元")
        print(f"  应纳税额：      {format_money(r['应纳税额'])} 元")
        print(f"  实发工资：      {format_money(r['实发工资'])} 元")
        print(f"  公司社保承担：  {format_money(r['公司社保承担'])} 元")
        print(f"  公司用人总成本：{format_money(r['公司用人总成本'])} 元")

    print("\n" + "-" * 70)
    print("  【汇总】")
    total_gross = sum(r["税前工资"] for r in results)
    total_tax = sum(r["应纳税额"] for r in results)
    total_net = sum(r["实发工资"] for r in results)
    total_si_company = sum(r["公司社保承担"] for r in results)
    total_cost = sum(r["公司用人总成本"] for r in results)
    print(f"  工资总额：      {format_money(total_gross)} 元")
    print(f"  个税总额：      {format_money(total_tax)} 元")
    print(f"  实发工资总额：  {format_money(total_net)} 元")
    print(f"  公司社保总额：  {format_money(total_si_company)} 元")
    print(f"  公司用人总成本：{format_money(total_cost)} 元")
    print("=" * 70)


def export_csv(results: list[dict], output_path: str = None):
    """导出CSV底稿（无需pandas依赖）"""
    if output_path is None:
        month = datetime.now().strftime("%Y%m")
        output_path = f"申报底稿_{month}.csv"

    # 表头
    headers = [
        "姓名", "税前工资", "个人社保", "个人公积金",
        "专项附加扣除合计", "子女教育", "婴幼儿照护", "赡养老人",
        "应税收入", "应纳税额", "实发工资",
        "公司社保承担", "公司公积金承担", "公司用人总成本"
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(",".join(headers) + "\n")
        for r in results:
            row = [
                r["姓名"],
                str(r["税前工资"]),
                str(r["个人社保"]),
                str(r["个人公积金"]),
                str(r["专项附加扣除"]),
                str(r["子女教育"]),
                str(r["婴幼儿照护"]),
                str(r["赡养老人"]),
                str(r["应税收入"]),
                str(r["应纳税额"]),
                str(r["实发工资"]),
                str(r["公司社保承担"]),
                str(r["公司公积金承担"]),
                str(r["公司用人总成本"]),
            ]
            f.write(",".join(row) + "\n")

    print(f"\n[OK] CSV底稿已生成：{output_path}")
    return output_path


# ===============================================
#  企业所得税季度预缴（小型微利企业优惠）
# ===============================================

def calc_corporate_income_tax_quarterly(
    revenue: float,
    cost: float,
    period_profit: float,
    ytd_profit: float,
    num_employees: int,
    total_assets: float,
    tax_paid_ytd: float = 0.0,
) -> dict:
    """
    计算小型微利企业所得税季度预缴
    返回申报底稿数据字典（匹配企业所得税预缴申报表A类格式）

    参数：
      revenue:        季度营业收入（元）      申报表第1行
      cost:           季度营业成本（元）      申报表第2行
      period_profit:  季度利润总额（元）      申报表第3行
      ytd_profit:     本年累计利润总额（元）
      num_employees:  季度平均从业人数
      total_assets:   季度平均资产总额（万元）
      tax_paid_ytd:   本年累计已预缴所得税额（元） 申报表第12行

    小型微利企业标准（2026年）：
      - 年应纳税所得额 ≤ 300万元
      - 从业人数 ≤ 300人
      - 资产总额 ≤ 5000万元

    2024-2027年优惠政策：
      - 减按25%计入应纳税所得额，按20%税率，实际税负 5%
    """
    # 判断是否符合小型微利企业条件
    is_small_low_profit = (
        num_employees <= 300
        and total_assets <= 5000
    )

    # 实际利润额（申报表第8行）= 利润总额（简化：无调整项）
    actual_profit = period_profit

    # 应纳税所得额（第8行，亏损时为0）
    period_taxable = max(actual_profit, 0)

    # 标准税率 25%
    standard_rate = 0.25
    # 实际优惠税率 5%（小型微利企业）
    effective_rate = 0.05 if is_small_low_profit else 0.25

    # 第10行：应纳税额 = 应纳税所得额 × 25%
    tax_before_relief = round(period_taxable * standard_rate, 2)

    # 第11行：减免所得税额（小型微利企业优惠）
    if is_small_low_profit and period_taxable > 0:
        tax_actual = round(period_taxable * effective_rate, 2)
        relief = round(tax_before_relief - tax_actual, 2)
    else:
        tax_actual = tax_before_relief
        relief = 0.0

    # 第13行：本期应补（退）所得税额
    tax_payable = round(tax_actual - tax_paid_ytd, 2)
    if tax_payable < 0:
        tax_payable = 0.0  # 亏损或已缴足，不用补税

    return {
        "营业收入": round(revenue, 2),
        "营业成本": round(cost, 2),
        "利润总额": round(period_profit, 2),
        "实际利润额": round(actual_profit, 2),
        "应纳税所得额": period_taxable,
        "标准税率": standard_rate,
        "优惠实际税率": effective_rate,
        "应纳税额_标准": tax_before_relief,
        "减免所得税额": relief,
        "本期应纳税额": tax_actual,
        "本年累计已预缴": tax_paid_ytd,
        "本期应补(退)税额": tax_payable,
        "从业人数": num_employees,
        "资产总额_万元": total_assets,
        "是否小型微利企业": "是" if is_small_low_profit else "否",
    }


def format_corporate_tax_report(result: dict, quarter: int, year: int) -> str:
    """生成企业所得税申报说明文字（匹配A200000格式）"""
    lines = [
        f"{'='*70}",
        f"  {year}年第{quarter}季度 企业所得税预缴申报说明",
        f"  （匹配 A200000 申报表格式）",
        f"{'='*70}",
        "",
        f"一、基本信息",
        f"  纳税人名称：    武汉金艳龙科技有限公司",
        f"  所属期间：      {year}年{[1,4,7,10][quarter-1]}月01日 至 {year}年{[3,6,9,12][quarter-1]}月31日",
        f"  企业类型：     {result['是否小型微利企业']}（小型微利企业）",
        f"  从业人数：     {result['从业人数']} 人",
        f"  资产总额：     {result['资产总额_万元']:.2f} 万元",
        "",
        f"{'─'*50}",
        f"二、收入成本利润（申报表第1~3行）",
        f"{'─'*50}",
        f"  第1行 营业收入：       {result['营业收入']:>15,.2f} 元",
        f"  第2行 营业成本：       {result['营业成本']:>15,.2f} 元",
        f"  第3行 利润总额：       {result['利润总额']:>15,.2f} 元",
        "",
        f"{'─'*50}",
        f"三、应纳税所得额计算（申报表第4~8行）",
        f"{'─'*50}",
        f"  第4行 特定业务调整：    {0:>15,.2f}",
        f"  第5行 不征税收入：       {0:>15,.2f}",
        f"  第6行 固定资产折旧调整： {0:>15,.2f}",
        f"  第7行 弥补以前年度亏损： {0:>15,.2f}",
        f"  ───────────────────────────────",
        f"  第8行 实际利润额：       {result['实际利润额']:>15,.2f} 元",
        "",
        f"{'─'*50}",
        f"四、税款计算（申报表第9~13行）",
        f"{'─'*50}",
        f"  第9行 税率（25%）：       {'25%':>15s}",
        f"  第10行 应纳所得税额：     {result['应纳税额_标准']:>15,.2f} 元",
        f"  第11行 减免所得税额：     {result['减免所得税额']:>15,.2f} 元",
        f"  第12行 本年累计已预缴：   {result['本年累计已预缴']:>15,.2f} 元",
        f"  ───────────────────────────────",
        f"  第13行 本期应补(退)税额： {result['本期应补(退)税额']:>15,.2f} 元",
        "",
        f"{'─'*50}",
        f"五、计算说明",
        f"{'─'*50}",
    ]

    if result['利润总额'] <= 0:
        lines.extend([
            f"  【本期亏损】利润总额为 {result['利润总额']:,.2f} 元（负数），",
            f"             实际利润额取0或保留负数，无需缴纳企业所得税。",
            f"",
            f"  第10行应纳所得税额 = max(实际利润额, 0) × 25% = 0 元",
            f"  第11行减免所得税额 = 0 元（亏损无减免）",
            f"  第13行本期应补退税额 = 0 元",
        ])
    else:
        if result['是否小型微利企业'] == '是':
            lines.extend([
                f"  【小型微利企业优惠】2024-2027年政策：",
                f"  - 减按25%计入应纳税所得额，按20%税率征收",
                f"  - 实际税负 = 25% × 20% = 5%",
                f"",
                f"  第10行应纳所得税额 = {result['应纳税所得额']:,.2f} × 25% = {result['应纳税额_标准']:,.2f} 元",
                f"  第11行减免所得税额 = {result['应纳税额_标准']:,.2f} - {result['本期应纳税额']:,.2f} = {result['减免所得税额']:,.2f} 元",
                f"  第13行本期应补退税额 = {result['本期应纳税额']:,.2f} - {result['本年累计已预缴']:,.2f} = {result['本期应补(退)税额']:,.2f} 元",
            ])
        else:
            lines.extend([
                f"  【一般企业】适用标准税率 25%",
                f"  第10行应纳所得税额 = {result['应纳税所得额']:,.2f} × 25% = {result['应纳税额_标准']:,.2f} 元",
                f"  第11行减免所得税额 = 0 元",
                f"  第13行本期应补退税额 = {result['本期应纳税额']:,.2f} 元",
            ])

    lines.extend([
        "",
        f"{'─'*50}",
        f"六、申报提醒",
        f"{'─'*50}",
        "  1. 请核对利润总额与利润表（小企业会计准则）一致；",
        "  2. 小型微利企业优惠由系统自动判别，无需额外备案；",
        "  3. 申报截止时间为季度终了后15日内（4月、7月、10月、次年1月15日前）；",
        "  4. 请及时在国家税务总局湖北省电子税务局完成预缴申报。",
        "",
        f"{'='*70}",
        f"  —— 由 金艳龙AI税务助手 自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"{'='*70}",
    ])
    return "\n".join(lines)


# ===============================================
#  银行流水自动分类（遵循小企业会计准则）
# ===============================================

def classify_bank_transaction(desc: str) -> dict:
    """
    根据银行流水摘要，自动分类到小企业会计准则利润表项目
    返回：{"category": "营业收入", "pl_item": "营业收入", "影响利润": "收入"}
    """
    desc = str(desc).lower()
    
    # 一、营业收入（利润表第1行）
    if any(k in desc for k in ["货款", "销售收入", "服务费", "咨询费", "收款", 
                               "主营业务收入", "其他业务收入", "销售", "服务收入"]):
        return {
            "category": "营业收入",
            "pl_item": "营业收入",
            "type": "收入",
            "account": "主营业务收入"
        }
    
    # 二、营业成本（利润表第2行）
    elif any(k in desc for k in ["采购", "进货", "材料成本", "主营业务成本", 
                                 "材料", "成本", "进货成本"]):
        return {
            "category": "营业成本",
            "pl_item": "营业成本",
            "type": "支出",
            "account": "主营业务成本"
        }
    
    # 三、税金及附加（利润表第3行）
    elif any(k in desc for k in ["税金", "附加费", "城建税", "教育费附加", 
                                 "地方教育附加", "印花税", "房产税", "土地使用税"]):
        return {
            "category": "税金及附加",
            "pl_item": "税金及附加",
            "type": "支出",
            "account": "税金及附加"
        }
    
    # 四、管理费用（利润表第5行）
    elif any(k in desc for k in ["工资", "社保", "公积金", "福利费", "奖金", 
                                 "养老金", "医保", "失业保险", "工伤保险"]):
        return {
            "category": "管理费用-人工",
            "pl_item": "管理费用",
            "type": "支出",
            "account": "管理费用-工资社保"
        }
    
    elif any(k in desc for k in ["水电", "物业", "房租", "租赁", "办公用品", 
                                 "电话费", "网络费", "维修费"]):
        return {
            "category": "管理费用-办公",
            "pl_item": "管理费用",
            "type": "支出",
            "account": "管理费用-办公费"
        }
    
    elif any(k in desc for k in ["差旅", "交通", "餐饮", "招待", "会议费", 
                                 "培训费", "咨询费", "审计费"]):
        return {
            "category": "管理费用-其他",
            "pl_item": "管理费用",
            "type": "支出",
            "account": "管理费用-业务招待费"
        }
    
    # 五、财务费用（利润表第6行）
    elif any(k in desc for k in ["利息", "手续费", "银行手续费", "汇款手续费", 
                                 "贷款利息", "存款利息"]):
        return {
            "category": "财务费用",
            "pl_item": "财务费用",
            "type": "支出",
            "account": "财务费用-手续费"
        }
    
    # 六、营业外收入（利润表第10行）
    elif any(k in desc for k in ["政府补助", "补贴", "罚款收入", "违约金收入", 
                                 "捐赠收入", "盘盈"]):
        return {
            "category": "营业外收入",
            "pl_item": "营业外收入",
            "type": "收入",
            "account": "营业外收入"
        }
    
    # 七、营业外支出（利润表第11行）
    elif any(k in desc for k in ["罚款", "捐赠", "损失", "盘亏", "自然灾害损失", 
                                 "违约金支出"]):
        return {
            "category": "营业外支出",
            "pl_item": "营业外支出",
            "type": "支出",
            "account": "营业外支出"
        }
    
    # 八、投资收益（利润表第8行）
    elif any(k in desc for k in ["分红", "投资收益", "股息", "理财收益", 
                                 "投资收入"]):
        return {
            "category": "投资收益",
            "pl_item": "投资收益",
            "type": "收入",
            "account": "投资收益"
        }
    
    else:
        return {
            "category": "待分类",
            "pl_item": "待分类",
            "type": "未知",
            "account": "待确认"
        }


def generate_profit_statement(df_txns: object) -> dict:
    """
    根据银行流水DataFrame，生成小企业会计准则利润表
    df_txns 必须包含列：["摘要", "收入金额", "支出金额", "自动分类"]
    
    返回利润表各项目金额（单位：元）
    """
    # 营业收入（第1行）= 所有营业收入分类的收入金额之和
    revenue = df_txns[df_txns["自动分类"] == "营业收入"]["收入金额"].sum()
    
    # 营业成本（第2行）= 所有营业成本分类的支出金额之和
    cost = df_txns[df_txns["自动分类"] == "营业成本"]["支出金额"].sum()
    
    # 税金及附加（第3行）
    tax_expense = df_txns[df_txns["自动分类"] == "税金及附加"]["支出金额"].sum()
    
    # 管理费用（第5行）= 所有管理费用子分类的支出金额之和
    manage_expense = df_txns[
        df_txns["自动分类"].str.contains("管理费用", na=False)
    ]["支出金额"].sum()
    
    # 财务费用（第6行）
    finance_expense = df_txns[df_txns["自动分类"] == "财务费用"]["支出金额"].sum()
    
    # 投资收益（第8行）
    investment_income = df_txns[df_txns["自动分类"] == "投资收益"]["收入金额"].sum()
    
    # 营业利润（第9行）= 营业收入 - 营业成本 - 税金及附加 - 管理费用 - 财务费用 + 投资收益
    operating_profit = revenue - cost - tax_expense - manage_expense - finance_expense + investment_income
    
    # 营业外收入（第10行）
    other_income = df_txns[df_txns["自动分类"] == "营业外收入"]["收入金额"].sum()
    
    # 营业外支出（第11行）
    other_expense = df_txns[df_txns["自动分类"] == "营业外支出"]["支出金额"].sum()
    
    # 利润总额（第12行）= 营业利润 + 营业外收入 - 营业外支出
    total_profit = operating_profit + other_income - other_expense
    
    # 所得税费用（第13行）= 利润总额 × 税率（小型微利企业5%）
    # 注意：亏损时不计提所得税
    if total_profit > 0:
        tax_expense = total_profit * 0.05  # 小型微利企业实际税负5%
    else:
        tax_expense = 0.0
    
    # 净利润（第14行）= 利润总额 - 所得税费用
    net_profit = total_profit - tax_expense
    
    return {
        "营业收入": round(revenue, 2),
        "营业成本": round(cost, 2),
        "税金及附加": round(tax_expense, 2),
        "管理费用": round(manage_expense, 2),
        "财务费用": round(finance_expense, 2),
        "投资收益": round(investment_income, 2),
        "营业利润": round(operating_profit, 2),
        "营业外收入": round(other_income, 2),
        "营业外支出": round(other_expense, 2),
        "利润总额": round(total_profit, 2),
        "所得税费用": round(tax_expense, 2),
        "净利润": round(net_profit, 2),
    }


def validate_quarterly_declaration(profit_data: dict, revenue: float, cost: float, period_profit: float) -> list:
    """
    校验利润表数据与企业所得税季度申报表数据是否一致
    
    参数：
      profit_data: generate_profit_statement() 的返回值
      revenue: 申报表第1行 营业收入
      cost: 申报表第2行 营业成本
      period_profit: 申报表第3行 利润总额
    
    返回：校验结果列表，每个元素为 (是否通过, 提示信息)
    """
    results = []
    
    # 校验1：营业收入
    if abs(profit_data["营业收入"] - revenue) > 1:
        results.append((False, f"营业收入不一致：利润表{profit_data['营业收入']:.2f} vs 申报表{revenue:.2f}"))
    else:
        results.append((True, f"营业收入校验通过：{revenue:.2f} 元"))
    
    # 校验2：营业成本
    if abs(profit_data["营业成本"] - cost) > 1:
        results.append((False, f"营业成本不一致：利润表{profit_data['营业成本']:.2f} vs 申报表{cost:.2f}"))
    else:
        results.append((True, f"营业成本校验通过：{cost:.2f} 元"))
    
    # 校验3：利润总额
    if abs(profit_data["利润总额"] - period_profit) > 1:
        results.append((False, f"利润总额不一致：利润表{profit_data['利润总额']:.2f} vs 申报表{period_profit:.2f}"))
    else:
        results.append((True, f"利润总额校验通过：{period_profit:.2f} 元"))
    
    return results


# ===============================================
#  主程序（示例）
# ===============================================
if __name__ == "__main__":
    print("武汉金艳龙科技 - 个税社保计算工具 v1.0")
    print("（无需安装任何依赖，直接运行）\n")

    employees = [
        {
            "name": "员工A",
            "gross_salary": 10522,
            "si_base": 5000,
            "si_personal_actual": 522,
            "special_deductions": 5000,
            "child_education": 2000,
            "infant_care": 2000,
            "elderly_care": 1000,
        },
        # 增加员工只需复制上方字典，修改姓名和工资金额
        # {
        #     "name": "员工B",
        #     "gross_salary": 8000,
        #     ...
        # },
    ]

    results = process_employees(employees)
    print_results(results)
    export_csv(results)

    print("\n[提示] 使用提示：")
    print("  1. 修改上方 employees 列表，增加/修改员工数据")
    print("  2. 专项附加扣除如有变化，修改 special_deductions 字段")
    print("  3. 运行：python tax_calculator.py")
    print("  4. CSV底稿可直接导入Excel或发送给财务")
