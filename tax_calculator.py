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
#  示例数据（金艳龙科技当前情况）
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
