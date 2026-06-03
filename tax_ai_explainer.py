#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
閲戣壋榫橝I绋庡姟鍔╂墜 - 鍛戒护琛岀増锛堟敮鎸佺湡瀹?DeepSeek AI锛?杩愯锛歱ython tax_ai_explainer.py

閰嶇疆 API Key锛堜换閫変竴绉嶏級锛?  鏂瑰紡1锛氬湪椤圭洰鏍圭洰褰曞垱寤?.env 鏂囦欢锛屽啓鍏?DEEPSEEK_API_KEY=sk-xxx
  鏂瑰紡2锛氳缃幆澧冨彉閲?DEEPSEEK_API_KEY
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# 璇诲彇 .env 鏂囦欢
load_dotenv()

# ===============================================
#  DeepSeek AI 閰嶇疆
# ===============================================

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# 鏄惁浣跨敤鐪熷疄 AI
USE_REAL_AI = bool(DEEPSEEK_API_KEY)

if USE_REAL_AI:
    print("[OK] 妫€娴嬪埌 DeepSeek API Key锛屽皢浣跨敤鐪熷疄 AI 鐢熸垚鐢虫姤璇存槑")
else:
    print("[鎻愮ず] 鏈娴嬪埌 API Key锛屼娇鐢ㄦā鎷熸ā寮忥紙瑙勫垯鐢熸垚锛?)
    print("       濡傞渶浣跨敤鐪熷疄 AI锛岃鍦?.env 鏂囦欢涓厤缃?DEEPSEEK_API_KEY")


# ===============================================
#  绀句繚涓庝釜绋庤绠楀嚱鏁帮紙涓?tax_calculator.py 淇濇寔涓€鑷达級
# ===============================================

# 姝︽眽 2026 绀句繚姣斾緥锛堜釜浜猴級
SOCIAL_INSURANCE_RATE_PERSONAL = {
    "鍏昏€?: 0.08,
    "鍖荤枟": 0.02,
    "澶变笟": 0.003,
}
SOCIAL_INSURANCE_PERSONAL_FIXED = {
    "鍖荤枟澶х梾": 7,   # 澶ч鍖荤枟淇濋櫓鍥哄畾 7 鍏冿紙閯備汉绀惧彂銆?023銆曪級
}

# 鍏徃鎵挎媴閮ㄥ垎
SOCIAL_INSURANCE_RATE_COMPANY = {
    "鍏昏€?: 0.16,
    "鍖荤枟": 0.087,
    "澶变笟": 0.007,
    "宸ヤ激": 0.002,
}

def calc_social_insurance_personal(base):
    """璁＄畻涓汉绀句繚缂寸撼閲戦"""
    total = 0
    detail = {}
    for k, v in SOCIAL_INSURANCE_RATE_PERSONAL.items():
        amount = base * v
        detail[k] = round(amount, 2)
        total += amount
    for k, v in SOCIAL_INSURANCE_PERSONAL_FIXED.items():
        detail[k] = v
        total += v
    return round(total, 2), detail

def calc_social_insurance_company(base):
    """璁＄畻鍏徃鎵挎媴绀句繚閲戦"""
    total = 0
    detail = {}
    for k, v in SOCIAL_INSURANCE_RATE_COMPANY.items():
        amount = base * v
        detail[k] = round(amount, 2)
        total += amount
    return round(total, 2), detail

def calc_income_tax(taxable_income):
    """璁＄畻涓◣锛堢疮璁￠鎵ｆ硶锛屾澶勭畝鍖栦负鏈堝害璁＄畻锛?""
    if taxable_income <= 0:
        return 0, 0.0
    brackets = [
        (36000,    0.03, 0),
        (144000,   0.10, 2520),
        (300000,   0.20, 16920),
        (420000,   0.25, 31920),
        (660000,   0.30, 52920),
        (960000,   0.35, 85920),
        (float('inf'), 0.45, 181920),
    ]
    remaining = taxable_income
    tax = 0
    for threshold, rate, deduction in brackets:
        if remaining <= threshold:
            tax = remaining * rate - deduction
            break
        remaining = threshold
    # 娉ㄦ剰锛氫互涓婁负骞村害绱閫昏緫绠€鍖栵紝瀹為檯鏈堝害鐢虫姤鐢ㄧ疮璁￠鎵ｆ硶
    # 姝ゅ鍋氱畝鍖栨紨绀猴紝寤鸿瀵规帴涓撲笟绋庡姟璁＄畻搴?    return max(0, round(tax, 2)), 0.0

def calc_one_employee(name, gross_salary, si_base, si_personal_actual,
                     special_deduction, child_edu=0, infant_care=0, elderly_care=0):
    """璁＄畻鍗曞悕鍛樺伐绋庡姟璇︽儏"""
    # 濡傛灉鐢ㄥ疄闄呯即绾抽噾棰濓紝浠ュ疄闄呬负鍑嗭紱鍚﹀垯鎸夊熀鏁拌绠?    if si_personal_actual > 0:
        si_personal = si_personal_actual
    else:
        si_personal, _ = calc_social_insurance_personal(si_base)

    taxable = gross_salary - si_personal - 5000 - special_deduction
    tax, _ = calc_income_tax(max(0, taxable))

    net_salary = gross_salary - si_personal - tax

    company_si, company_si_detail = calc_social_insurance_company(si_base)
    total_labor_cost = gross_salary + company_si

    return {
        "濮撳悕": name,
        "绋庡墠宸ヨ祫": gross_salary,
        "涓汉绀句繚": si_personal,
        "涓撻」闄勫姞鎵ｉ櫎": special_deduction,
        "瀛愬コ鏁欒偛": child_edu,
        "濠村辜鍎跨収鎶?: infant_care,
        "璧″吇鑰佷汉": elderly_care,
        "搴旂◣鏀跺叆": max(0, round(taxable, 2)),
        "搴旂撼绋庨": tax,
        "瀹炲彂宸ヨ祫": round(net_salary, 2),
        "鍏徃绀句繚鎵挎媴": company_si,
        "鍏徃鐢ㄤ汉鎬绘垚鏈?: round(total_labor_cost, 2),
        "鍏徃绀句繚鏄庣粏": company_si_detail,
    }


# ===============================================
#  AI 鐢虫姤璇存槑鐢熸垚
# ===============================================

def generate_ai_explanation(results, year, month):
    """璋冪敤 DeepSeek API 鐢熸垚涓撲笟鐢虫姤璇存槑"""

    # 鏋勯€犳彁绀鸿瘝
    rows_text = ""
    for r in results:
        rows_text += (
            f"鍛樺伐 {r['濮撳悕']}锛氱◣鍓嶅伐璧?{r['绋庡墠宸ヨ祫']} 鍏冿紝"
            f"涓汉绀句繚 {r['涓汉绀句繚']} 鍏冿紝"
            f"涓撻」闄勫姞鎵ｉ櫎 {r['涓撻」闄勫姞鎵ｉ櫎']} 鍏?
            f"锛堝瓙濂虫暀鑲?{r['瀛愬コ鏁欒偛']} 鍏冿紝濠村辜鍎跨収鎶?{r['濠村辜鍎跨収鎶?]} 鍏冿紝璧″吇鑰佷汉 {r['璧″吇鑰佷汉']} 鍏冿級锛?
            f"搴旂◣鏀跺叆 {r['搴旂◣鏀跺叆']} 鍏冿紝搴旂撼绋庨 {r['搴旂撼绋庨']} 鍏冿紝"
            f"瀹炲彂宸ヨ祫 {r['瀹炲彂宸ヨ祫']} 鍏冦€俓n"
        )

    company_si_total = sum(r["鍏徃绀句繚鎵挎媴"] for r in results)
    total_labor_cost = sum(r["鍏徃鐢ㄤ汉鎬绘垚鏈?] for r in results)
    total_tax = sum(r["搴旂撼绋庨"] for r in results)

    prompt = f"""浣犳槸涓€浣嶄笓涓氱殑绋庡姟椤鹃棶锛岃涓轰互涓嬩紒涓歿year}骞磠month}鏈堢殑涓◣鍙婄ぞ淇濈敵鎶ユ挵鍐欎竴浠戒笓涓氱殑鐢虫姤璇存槑銆?
## 鍛樺伐鏁版嵁
{rows_text}
## 姹囨€绘暟鎹?- 鍏徃鎵挎媴绀句繚鎬婚锛歿company_si_total} 鍏?- 鍏ㄤ綋鍛樺伐搴旂撼绋庨鍚堣锛歿total_tax} 鍏?- 鍏徃鐢ㄤ汉鎬绘垚鏈細{total_labor_cost} 鍏?
## 瑕佹眰
1. 浠?姝︽眽閲戣壋榫欑鎶€鏈夐檺鍏徃 {year}骞磠month}鏈?绋庡姟鐢虫姤璇存槑"涓烘爣棰?2. 鍒嗗洓涓儴鍒嗭細涓€銆佺敵鎶ユ鍐碉紱浜屻€佸憳宸ヤ釜绋庢槑缁嗭紱涓夈€佺ぞ淇濈即绾宠鏄庯紱鍥涖€佺敵鎶ユ敞鎰忎簨椤?3. 璇皵涓撲笟銆佺畝娲侊紝閫傚悎璐㈠姟鎻愪氦缁欑◣鍔″眬鎴栫暀瀛樺妗?4. 鎻愰啋鐢ㄦ埛鏍稿涓撻」闄勫姞鎵ｉ櫎淇℃伅鏄惁宸插強鏃舵洿鏂帮紙涓◣APP锛?5. 璇存槑绀句繚鍩烘暟濡傛湁璋冩暣璇蜂互绀句繚灞€鏍稿畾涓哄噯
6. 鎬诲瓧鏁版帶鍒跺湪 500-800 瀛?7. 鐢ㄤ腑鏂囪緭鍑猴紝涓嶈杈撳嚭鑻辨枃
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "浣犳槸涓€浣嶄笓涓氱殑绋庡姟椤鹃棶锛屾搮闀挎挵鍐欎紒涓氱◣鍔＄敵鎶ヨ鏄庛€?},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.3,
    }

    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            return result["choices"][0]["message"]["content"]
        else:
            print(f"[AI璋冪敤澶辫触 {resp.status_code}]锛屽垏鎹㈡ā鎷熸ā寮?)
            return generate_mock_explanation(results, year, month)
    except Exception as e:
        print(f"[AI璋冪敤寮傚父: {e}]锛屽垏鎹㈡ā鎷熸ā寮?)
        return generate_mock_explanation(results, year, month)


def generate_mock_explanation(results, year, month):
    """妯℃嫙 AI 鐢熸垚鐢虫姤璇存槑锛堟棤 API Key 鏃剁殑闄嶇骇鏂规锛?""
    lines = []
    lines.append(f"姝︽眽閲戣壋榫欑鎶€鏈夐檺鍏徃 {year}骞磠month}鏈?绋庡姟鐢虫姤璇存槑\n")
    lines.append("=" * 50)
    lines.append("\n涓€銆佺敵鎶ユ鍐礬n")
    lines.append(f"  鏈湀鐢虫姤鍛樺伐浜烘暟锛歿len(results)} 浜?)
    total_tax = sum(r["搴旂撼绋庨"] for r in results)
    company_si = sum(r["鍏徃绀句繚鎵挎媴"] for r in results)
    lines.append(f"  搴旂撼绋庨鍚堣锛歿total_tax} 鍏?)
    lines.append(f"  鍏徃鎵挎媴绀句繚鍚堣锛歿company_si} 鍏?)
    lines.append("\n浜屻€佸憳宸ヤ釜绋庢槑缁哱n")
    for r in results:
        lines.append(f"  {r['濮撳悕']}锛氬簲绋庢敹鍏?{r['搴旂◣鏀跺叆']} 鍏冿紝搴旂撼绋庨 {r['搴旂撼绋庨']} 鍏冿紝瀹炲彂 {r['瀹炲彂宸ヨ祫']} 鍏?)
    lines.append("\n涓夈€佺ぞ淇濈即绾宠鏄嶾n")
    lines.append(f"  绀句繚缂磋垂鍩烘暟锛歿results[0]['涓汉绀句繚']} 鍏冿紙浠ュ疄闄呯敵鎶ヤ负鍑嗭級")
    lines.append(f"  鍏徃鎵挎媴閮ㄥ垎鍚堣锛歿company_si} 鍏?)
    lines.append("\n鍥涖€佺敵鎶ユ敞鎰忎簨椤筡n")
    lines.append("  1. 璇锋牳瀵逛笓椤归檮鍔犳墸闄や俊鎭槸鍚﹀凡鍙婃椂鏇存柊锛堜釜绋嶢PP锛?)
    lines.append("  2. 绀句繚鍩烘暟濡傛湁璋冩暣璇蜂互绀句繚灞€鏍稿畾涓哄噯")
    lines.append("  3. 鏈簳绋跨敱 AI 杈呭姪鐢熸垚锛屾彁浜ゅ墠璇蜂汉宸ュ鏍?)
    lines.append("\n" + "=" * 50 + "\n")
    return "\n".join(lines)


def save_results(results, explanation, year, month):
    """淇濆瓨璁＄畻缁撴灉鍜岀敵鎶ヨ鏄?""
    # 淇濆瓨 CSV 搴曠
    import csv
    csv_path = f"鐢虫姤搴曠_{year}{month:02d}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"[OK] CSV搴曠宸茬敓鎴愶細{csv_path}")

    # 淇濆瓨鐢虫姤璇存槑
    txt_path = f"鐢虫姤璇存槑_{year}{month:02d}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(explanation)
    print(f"[OK] 鐢虫姤璇存槑宸茬敓鎴愶細{txt_path}")

    return csv_path, txt_path


# ===============================================
#  涓荤▼搴?# ===============================================

if __name__ == "__main__":
    now = datetime.now()
    year, month = now.year, now.month

    print(f"\n閲戣壋榫橝I绋庡姟鍔╂墜 - {year}骞磠month}鏈堢敵鎶n")
    print("-" * 50)

    # 鍛樺伐鏁版嵁锛堝彲淇敼涓?Excel 瀵煎叆锛?    employees = [
        {
            "name": "鍛樺伐A",
            "gross": 10522,
            "si_base": 5000,
            "si_actual": 522,
            "special": 5000,
            "child_edu": 2000,
            "infant": 2000,
            "elderly": 1000,
        },
    ]

    results = []
    for emp in employees:
        r = calc_one_employee(
            emp["name"], emp["gross"], emp["si_base"], emp["si_actual"],
            emp["special"], emp["child_edu"], emp["infant"], emp["elderly"]
        )
        results.append(r)
        print(f"  {r['濮撳悕']}锛氫釜绋?{r['搴旂撼绋庨']} 鍏冿紝瀹炲彂 {r['瀹炲彂宸ヨ祫']} 鍏?)

    print("\n姝ｅ湪鐢熸垚 AI 鐢虫姤璇存槑...\n")
    explanation = generate_ai_explanation(results, year, month)
    print(explanation)

    save_results(results, explanation, year, month)

    print("\n[鎻愮ず] 浣跨敤璇存槑锛?)
    print("  1. 淇敼涓婃柟 employees 鍒楄〃澧炲姞鍛樺伐")
    print("  2. 鎴栨帴鍏?Excel 瀵煎叆锛堝弬鑰?tax_web_app.py锛?)
    print("  3. 纭繚 .env 鏂囦欢宸查厤缃?DEEPSEEK_API_KEY 浠ヤ娇鐢ㄧ湡瀹?AI\n")
