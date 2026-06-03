#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
姝︽眽閲戣壋榫欑鎶€鏈夐檺鍏徃 - 涓◣/绀句繚璁＄畻鑴氭湰锛圡VP鐗堬級
閫傜敤鍦烘櫙锛氶浂鐢虫姤浼佷笟锛屾湁宸ヨ祫鍙戞斁鍜岀ぞ淇濈即绾?杩愯锛歱ython tax_calculator.py
"""

from datetime import datetime
import json
import os

# ===============================================
#  鏀跨瓥鍙傛暟鍔犺浇鍣紙浠?tax_policies.json 璇诲彇锛?# ===============================================

_POLICIES_CACHE = None
_POLICIES_CACHE_TIME = None
_POLICIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tax_policies.json")


def _load_raw_policies():
    """鍔犺浇鍘熷 JSON锛堝甫缂撳瓨锛?0绉掑埛鏂帮級"""
    global _POLICIES_CACHE, _POLICIES_CACHE_TIME
    now = datetime.now()
    if _POLICIES_CACHE is not None and _POLICIES_CACHE_TIME is not None:
        if (now - _POLICIES_CACHE_TIME).seconds < 60:
            return _POLICIES_CACHE
    with open(_POLICIES_PATH, "r", encoding="utf-8") as f:
        _POLICIES_CACHE = json.load(f)
    _POLICIES_CACHE_TIME = now
    return _POLICIES_CACHE


def load_tax_policies(year: int = None):
    """
    鍔犺浇鎸囧畾骞村害鐨勭◣鏀舵斂绛栧弬鏁般€?
    鏌ユ壘閫昏緫锛?    1. 鎸?year 鍖归厤 policy_periods 涓殑鍖洪棿
    2. 濡傛灉鍖归厤鍒扮殑鍖洪棿 status="placeholder" 涓旀湁 inherit_from锛屽洖閫€鍒版簮鍖洪棿
    3. 杩斿洖涓€涓墎骞冲寲鐨勫弬鏁板瓧鍏革紝渚涘悇璁＄畻鍑芥暟浣跨敤

    鍙傛暟锛?      year: 鐢虫姤骞村害锛岄粯璁ゅ綋鍓嶅勾
    杩斿洖锛?      dict 鍖呭惈鎵€鏈夌◣绉嶅弬鏁?+ 鍏冩暟鎹?    """
    if year is None:
        year = datetime.now().year

    raw = _load_raw_policies()
    periods = raw.get("policy_periods", [])

    # 1. 鏌ユ壘鍖归厤鍖洪棿
    matched = None
    for p in periods:
        start = int(p["effective_from"][:4])
        end = int(p["effective_until"][:4])
        if start <= year <= end:
            matched = p
            break

    if matched is None:
        # 瓒呭嚭鎵€鏈夊尯闂磋寖鍥达紝浣跨敤鏈€鍚庝竴涓?        matched = periods[-1] if periods else {}

    # 2. 濡傛灉鏄崰浣嶅尯闂达紝鍥為€€鍒扮户鎵挎簮
    if matched.get("status") == "placeholder" and matched.get("inherit_from"):
        inherit_period = matched["inherit_from"]
        for p in periods:
            if p["period"] == inherit_period:
                # 娣卞害鍚堝苟锛氬崰浣嶅尯闂磋鐩栨簮鍖洪棿锛堝崰浣嶅尯闂村彲鑳芥湁閮ㄥ垎瑕嗙洊鍊硷級
                matched = _deep_merge(p.copy(), matched)
                break

    # 3. 鎻愬彇鐗规畩闄勫姞鎵ｉ櫎锛堣法绋庣鍏辩敤锛?    special_deductions = raw.get("special_deductions", {})

    return {
        "_meta": {
            "period": matched.get("period", "unknown"),
            "status": matched.get("status", "unknown"),
            "label": matched.get("label", ""),
            "summary": matched.get("summary", ""),
            "effective_from": matched.get("effective_from", ""),
            "effective_until": matched.get("effective_until", ""),
            "policy_version": raw.get("meta", {}).get("version", ""),
        },
        "personal_income_tax": matched.get("personal_income_tax", {}),
        "social_insurance": matched.get("social_insurance", {}),
        "vat": matched.get("vat", {}),
        "surcharges": matched.get("surcharges", {}),
        "corporate_income_tax": matched.get("corporate_income_tax", {}),
        "stamp_duty": matched.get("stamp_duty", {}),
        "disabled_employment_fund": matched.get("disabled_employment_fund", {}),
        "special_deductions": special_deductions,
        "auto_update": raw.get("auto_update", {}),
    }


def _deep_merge(base: dict, override: dict) -> dict:
    """娣卞害鍚堝苟锛歰verride 涓殑鍊艰鐩?base锛堜絾淇濈暀 base 涓?override 娌℃湁鐨勯敭锛?""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ===============================================
#  鍚戝悗鍏煎锛氫繚鐣欐ā鍧楃骇甯搁噺锛堜粠 JSON 榛樿鍔犺浇锛?# ===============================================

_default_pol = load_tax_policies()

SOCIAL_INSURANCE = {
    "pension_personal": _default_pol["social_insurance"]["personal_rates"]["pension"],
    "medical_personal": _default_pol["social_insurance"]["personal_rates"]["medical"],
    "unemployment_personal": _default_pol["social_insurance"]["personal_rates"]["unemployment"],
}

SOCIAL_INSURANCE_ACTUAL = _default_pol["social_insurance"]["personal_actual"]  # 522 = 鍩烘暟脳10.3%+澶х梾7鍏?
SOCIAL_INSURANCE_COMPANY = {
    "pension": _default_pol["social_insurance"]["company_rates"]["pension"],
    "medical": _default_pol["social_insurance"]["company_rates"]["medical"],
    "unemployment": _default_pol["social_insurance"]["company_rates"]["unemployment"],
    "injury": _default_pol["social_insurance"]["company_rates"]["injury"],
}

CRITICAL_ILLNESS_FIXED = _default_pol["social_insurance"].get("critical_illness_fixed", 7)

HOUSING_FUND_PERSONAL_RATE = _default_pol["social_insurance"]["housing_fund_personal"]
HOUSING_FUND_COMPANY_RATE = _default_pol["social_insurance"]["housing_fund_company"]

TAX_BRACKETS = [
    tuple(b) for b in _default_pol["personal_income_tax"]["brackets"]
]

BASIC_DEDUCTION = _default_pol["personal_income_tax"]["basic_deduction"]

# ===============================================


def calc_social_insurance_company(base=5000):
    """璁＄畻鍏徃绀句繚閮ㄥ垎锛堝ぇ鐥呭尰淇濆凡鍚湪鍖荤枟8.7%璐圭巼涓紝涓嶅彟璁★級"""
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
    璁＄畻涓汉鎵€寰楃◣
    杩斿洖锛?搴旂撼绋庨, 搴旂◣鏀跺叆)
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

    # 鏌ユ壘閫傜敤绋庣巼
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
    """鏍煎紡鍖栭噾棰濇樉绀?""
    return f"{val:,.2f}"


def process_employees(employees: list[dict]) -> list[dict]:
    """
    澶勭悊鍛樺伐鍒楄〃锛岃繑鍥炶绠楃粨鏋?    employees 姣忛」鏍煎紡锛?    {
        "name": "鍛樺伐A",
        "gross_salary": 10522,
        "si_base": 5000,
        "si_personal_actual": 522,   # 涓汉绀句繚瀹炵即 = 鍩烘暟脳(8%+2%+0.3%)+澶х梾7鍏?        "special_deductions": 5000,   # 涓撻」闄勫姞鎵ｉ櫎鍚堣
        "child_education": 2000,     # 鏄庣粏锛堝彲閫夛紝鐢ㄤ簬搴曠锛?        "infant_care": 2000,
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
            "濮撳悕": emp["name"],
            "绋庡墠宸ヨ祫": gross,
            "涓汉绀句繚": si_personal,
            "涓汉鍏Н閲?: hf_personal,
            "涓撻」闄勫姞鎵ｉ櫎": special,
            "搴旂◣鏀跺叆": taxable_income,
            "搴旂撼绋庨": tax,
            "瀹炲彂宸ヨ祫": round(net_salary, 2),
            "鍏徃绀句繚鎵挎媴": round(si_company, 2),
            "鍏徃鍏Н閲戞壙鎷?: round(hf_company, 2),
            "鍏徃鐢ㄤ汉鎬绘垚鏈?: round(total_cost, 2),
            # 鏄庣粏锛堢敤浜庡簳绋匡級
            "瀛愬コ鏁欒偛": emp.get("child_education", 0),
            "濠村辜鍎跨収鎶?: emp.get("infant_care", 0),
            "璧″吇鑰佷汉": emp.get("elderly_care", 0),
        })

    return results


def print_results(results: list[dict]):
    """鎵撳嵃璁＄畻缁撴灉"""
    print("\n" + "=" * 70)
    print("  涓◣/绀句繚璁＄畻缁撴灉  |  姝︽眽閲戣壋榫欑鎶€鏈夐檺鍏徃")
    print("=" * 70)

    for r in results:
        print(f"\n銆恵r['濮撳悕']}銆?)
        print(f"  绋庡墠宸ヨ祫锛?     {format_money(r['绋庡墠宸ヨ祫'])} 鍏?)
        print(f"  涓汉绀句繚鎵ｆ锛? {format_money(r['涓汉绀句繚'])} 鍏?)
        print(f"  涓撻」闄勫姞鎵ｉ櫎锛? {format_money(r['涓撻」闄勫姞鎵ｉ櫎'])} 鍏?)
        print(f"    鈹溾攢 瀛愬コ鏁欒偛锛?{format_money(r['瀛愬コ鏁欒偛'])} 鍏?)
        print(f"    鈹溾攢 濠村辜鍎跨収鎶わ細{format_money(r['濠村辜鍎跨収鎶?])} 鍏?)
        print(f"    鈹斺攢 璧″吇鑰佷汉锛?{format_money(r['璧″吇鑰佷汉'])} 鍏?)
        print(f"  搴旂◣鏀跺叆锛?     {format_money(r['搴旂◣鏀跺叆'])} 鍏?)
        print(f"  搴旂撼绋庨锛?     {format_money(r['搴旂撼绋庨'])} 鍏?)
        print(f"  瀹炲彂宸ヨ祫锛?     {format_money(r['瀹炲彂宸ヨ祫'])} 鍏?)
        print(f"  鍏徃绀句繚鎵挎媴锛? {format_money(r['鍏徃绀句繚鎵挎媴'])} 鍏?)
        print(f"  鍏徃鐢ㄤ汉鎬绘垚鏈細{format_money(r['鍏徃鐢ㄤ汉鎬绘垚鏈?])} 鍏?)

    print("\n" + "-" * 70)
    print("  銆愭眹鎬汇€?)
    total_gross = sum(r["绋庡墠宸ヨ祫"] for r in results)
    total_tax = sum(r["搴旂撼绋庨"] for r in results)
    total_net = sum(r["瀹炲彂宸ヨ祫"] for r in results)
    total_si_company = sum(r["鍏徃绀句繚鎵挎媴"] for r in results)
    total_cost = sum(r["鍏徃鐢ㄤ汉鎬绘垚鏈?] for r in results)
    print(f"  宸ヨ祫鎬婚锛?     {format_money(total_gross)} 鍏?)
    print(f"  涓◣鎬婚锛?     {format_money(total_tax)} 鍏?)
    print(f"  瀹炲彂宸ヨ祫鎬婚锛? {format_money(total_net)} 鍏?)
    print(f"  鍏徃绀句繚鎬婚锛? {format_money(total_si_company)} 鍏?)
    print(f"  鍏徃鐢ㄤ汉鎬绘垚鏈細{format_money(total_cost)} 鍏?)
    print("=" * 70)


def export_csv(results: list[dict], output_path: str = None):
    """瀵煎嚭CSV搴曠锛堟棤闇€pandas渚濊禆锛?""
    if output_path is None:
        month = datetime.now().strftime("%Y%m")
        output_path = f"鐢虫姤搴曠_{month}.csv"

    # 琛ㄥご
    headers = [
        "濮撳悕", "绋庡墠宸ヨ祫", "涓汉绀句繚", "涓汉鍏Н閲?,
        "涓撻」闄勫姞鎵ｉ櫎鍚堣", "瀛愬コ鏁欒偛", "濠村辜鍎跨収鎶?, "璧″吇鑰佷汉",
        "搴旂◣鏀跺叆", "搴旂撼绋庨", "瀹炲彂宸ヨ祫",
        "鍏徃绀句繚鎵挎媴", "鍏徃鍏Н閲戞壙鎷?, "鍏徃鐢ㄤ汉鎬绘垚鏈?
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(",".join(headers) + "\n")
        for r in results:
            row = [
                r["濮撳悕"],
                str(r["绋庡墠宸ヨ祫"]),
                str(r["涓汉绀句繚"]),
                str(r["涓汉鍏Н閲?]),
                str(r["涓撻」闄勫姞鎵ｉ櫎"]),
                str(r["瀛愬コ鏁欒偛"]),
                str(r["濠村辜鍎跨収鎶?]),
                str(r["璧″吇鑰佷汉"]),
                str(r["搴旂◣鏀跺叆"]),
                str(r["搴旂撼绋庨"]),
                str(r["瀹炲彂宸ヨ祫"]),
                str(r["鍏徃绀句繚鎵挎媴"]),
                str(r["鍏徃鍏Н閲戞壙鎷?]),
                str(r["鍏徃鐢ㄤ汉鎬绘垚鏈?]),
            ]
            f.write(",".join(row) + "\n")

    print(f"\n[OK] CSV搴曠宸茬敓鎴愶細{output_path}")
    return output_path


# ===============================================
#  浼佷笟鎵€寰楃◣瀛ｅ害棰勭即锛堝皬鍨嬪井鍒╀紒涓氫紭鎯狅級
# ===============================================

def calc_vat_and_surcharge(
    revenue: float,
    vat_rate: float = 0.03,
    is_small_scale: bool = True,
    is_small_low_profit: bool = True,
    vat_paid_ytd: float = 0.0,
    tax_year: int = None,
) -> dict:
    """
    璁＄畻澧炲€肩◣鍙婇檮鍔犵◣锛堝煄寤虹◣銆佹暀鑲茶垂闄勫姞銆佸湴鏂规暀鑲查檮鍔狅級

    绋庣巼鍙傛暟浠?tax_policies.json 璇诲彇锛屾寜鐢虫姤骞村害鑷姩鍖归厤瀵瑰簲鏀跨瓥鍖洪棿銆?
    鍙傛暟锛?      revenue:          瀛ｅ害鍚◣钀ヤ笟鏀跺叆锛堝厓锛?      vat_rate:         澧炲€肩◣鍚嶄箟绋庣巼锛堝皬瑙勬ā鍘?%锛屽疄闄呭噺鎸?%锛?      is_small_scale:   鏄惁灏忚妯＄撼绋庝汉
      is_small_low_profit: 鏄惁灏忓瀷寰埄浼佷笟锛堝奖鍝嶅叚绋庝袱璐瑰噺鍗婅祫鏍硷級
      vat_paid_ytd:     鏈勾宸茬即澧炲€肩◣锛堢敤浜庢牎楠岋級
      tax_year:         鐢虫姤骞村害锛堥粯璁ゅ綋鍓嶅勾锛岀敤浜庡尮閰嶆斂绛栧尯闂达級
    """
    pol = load_tax_policies(tax_year if tax_year else None)
    vat_pol = pol["vat"]
    sur_pol = pol["surcharges"]

    # ===== 灏忚妯＄撼绋庝汉锛氬惈绋庢敹鍏ユ崲绠椾笉鍚◣鏀跺叆 =====
    if is_small_scale:
        revenue_excl = round(revenue / (1 + vat_rate), 2)
    else:
        revenue_excl = revenue

    # ===== 澧炲€肩◣璁＄畻 =====
    exempt_threshold = vat_pol["quarterly_exempt_threshold"]
    effective_rate = vat_pol["small_scale_effective_rate"]
    nominal_rate = vat_pol["small_scale_nominal_rate"]
    vat_ref = vat_pol["policy_ref"]

    if is_small_scale and revenue_excl <= exempt_threshold:
        vat = 0.0
        vat_note = f"瀛ｅ害涓嶅惈绋庢敹鍏?{revenue_excl:,.2f} 鍏?鈮?{exempt_threshold//10000}涓?鈫?鍏嶅緛澧炲€肩◣"
        vat_policy = f"{vat_ref}锛氬皬瑙勬ā绾崇◣浜哄搴︹墹{exempt_threshold//10000}涓囧厤寰佸鍊肩◣"
        vat_effective_rate = 0.0
    elif is_small_scale:
        vat = round(revenue_excl * effective_rate, 2)
        vat_note = f"瀛ｅ害涓嶅惈绋庢敹鍏?{revenue_excl:,.2f} 鍏?> {exempt_threshold//10000}涓?鈫?鍑忔寜{effective_rate*100:.0f}%寰佹敹锛堝師{nominal_rate*100:.0f}%锛?
        vat_policy = f"{vat_ref}锛氬皬瑙勬ā绾崇◣浜哄噺鎸墈effective_rate*100:.0f}%寰佹敹"
        vat_effective_rate = effective_rate
    else:
        vat = round(revenue_excl * vat_rate, 2)
        vat_note = f"涓€鑸撼绋庝汉鎸墈vat_rate*100:.0f}%寰佹敹"
        vat_policy = "涓€鑸撼绋庝汉鏍囧噯绋庣巼"
        vat_effective_rate = vat_rate

    # ===== 鍏◣涓よ垂鍑忓崐鍒ゆ柇 =====
    six_two_half = sur_pol.get("six_two_half_enabled", True) and (is_small_scale or is_small_low_profit)
    half = sur_pol["half_multiplier"] if six_two_half else 1.0
    sur_ref = sur_pol["policy_ref"]

    # ===== 闄勫姞绋庯紙浠ュ疄闄呯即绾冲鍊肩◣涓哄熀纭€锛?====
    urban_nom = sur_pol["urban_construction_nominal"]
    edu_nom = sur_pol["education_nominal"]
    local_nom = sur_pol["local_education_nominal"]

    urban_tax = round(vat * urban_nom * half, 2)
    edu_surcharge = round(vat * edu_nom * half, 2)
    local_edu = round(vat * local_nom * half, 2)
    total_surcharge = round(urban_tax + edu_surcharge + local_edu, 2)

    if six_two_half:
        surcharge_policy = (
            f"銆屽叚绋庝袱璐瑰噺鍗娿€嶅煄寤簕urban_nom*100:.0f}%鈫抺urban_nom*half*100:.1f}%銆?
            f"鏁欒偛{edu_nom*100:.0f}%鈫抺edu_nom*half*100:.1f}%銆?
            f"鍦版柟鏁欒偛{local_nom*100:.0f}%鈫抺local_nom*half*100:.0f}%锛?
            f"鍚堣{(urban_nom+edu_nom+local_nom)*half*100:.0f}%"
        )
    else:
        surcharge_policy = f"鏍囧噯闄勫姞绋庣巼锛氬煄寤簕urban_nom*100:.0f}% + 鏁欒偛{edu_nom*100:.0f}% + 鍦版柟鏁欒偛{local_nom*100:.0f}%锛屽悎璁(urban_nom+edu_nom+local_nom)*100:.0f}%"

    return {
        "瀛ｅ害鍚◣鏀跺叆": round(revenue, 2),
        "瀛ｅ害涓嶅惈绋庢敹鍏?: revenue_excl,
        "澧炲€肩◣鍚嶄箟绋庣巼": vat_rate,
        "澧炲€肩◣瀹為檯绋庣巼": vat_effective_rate,
        "鏄惁灏忚妯＄撼绋庝汉": "鏄? if is_small_scale else "鍚?,
        "鏄惁灏忓瀷寰埄浼佷笟": "鏄? if is_small_low_profit else "鍚?,
        "鏄惁浜彈鍏◣涓よ垂鍑忓崐": "鏄? if six_two_half else "鍚?,
        "澧炲€肩◣搴旂即": vat,
        "澧炲€肩◣鍏嶇◣璇存槑": vat_note,
        "澧炲€肩◣浼樻儬渚濇嵁": vat_policy,
        "鍩庡缓绋庡悕涔?: round(vat * urban_nom, 2),
        "鍩庡缓绋?7%)": urban_tax,
        "鏁欒偛璐归檮鍔犲悕涔?: round(vat * edu_nom, 2),
        "鏁欒偛璐归檮鍔?3%)": edu_surcharge,
        "鍦版柟鏁欒偛闄勫姞鍚嶄箟": round(vat * local_nom, 2),
        "鍦版柟鏁欒偛闄勫姞(2%)": local_edu,
        "闄勫姞绋庡悎璁?: total_surcharge,
        "闄勫姞绋庝紭鎯犺鏄?: surcharge_policy,
        "鍏◣涓よ垂鍑忓厤閲戦": round(vat * (urban_nom + edu_nom + local_nom) * (1 - half), 2),
        "澧炲€肩◣鍙婇檮鍔犲悎璁?: round(vat + total_surcharge, 2),
        "_鏀跨瓥鍖洪棿": pol["_meta"]["period"],
    }


def calc_corporate_income_tax_quarterly(
    revenue: float,
    cost: float,
    period_profit: float,
    ytd_profit: float,
    num_employees: int,
    total_assets: float,
    tax_paid_ytd: float = 0.0,
    vat_data: dict = None,
    tax_year: int = None,
) -> dict:
    """
    璁＄畻灏忓瀷寰埄浼佷笟鎵€寰楃◣瀛ｅ害棰勭即
    杩斿洖鐢虫姤搴曠鏁版嵁瀛楀吀锛堝尮閰嶄紒涓氭墍寰楃◣棰勭即鐢虫姤琛ˋ绫绘牸寮忥級

    绋庣巼鍙傛暟浠?tax_policies.json 璇诲彇銆?
    鍙傛暟锛?      revenue:        瀛ｅ害钀ヤ笟鏀跺叆锛堝厓锛?     鐢虫姤琛ㄧ1琛?      cost:           瀛ｅ害钀ヤ笟鎴愭湰锛堝厓锛?     鐢虫姤琛ㄧ2琛?      period_profit:  瀛ｅ害鍒╂鼎鎬婚锛堝厓锛?     鐢虫姤琛ㄧ3琛?      ytd_profit:     鏈勾绱鍒╂鼎鎬婚锛堝厓锛?      num_employees:  瀛ｅ害骞冲潎浠庝笟浜烘暟
      total_assets:   瀛ｅ害骞冲潎璧勪骇鎬婚锛堜竾鍏冿級
      tax_paid_ytd:   鏈勾绱宸查缂存墍寰楃◣棰濓紙鍏冿級
      vat_data:       澧炲€肩◣鍙婇檮鍔犵◣璁＄畻缁撴灉
      tax_year:       鐢虫姤骞村害锛堢敤浜庡尮閰嶆斂绛栧尯闂达級
    """
    pol = load_tax_policies(tax_year if tax_year else None)
    cit_pol = pol["corporate_income_tax"]
    criteria = cit_pol["small_low_profit_criteria"]
    standard_rate = cit_pol["standard_rate"]
    effective_rate = cit_pol["small_low_profit_effective_rate"]
    cit_ref = cit_pol["policy_ref"]

    # 鍒ゆ柇鏄惁绗﹀悎灏忓瀷寰埄浼佷笟鏉′欢
    is_small_low_profit = (
        num_employees <= criteria["max_employees"]
        and total_assets <= criteria["max_assets_wan"]
    )

    # 瀹為檯鍒╂鼎棰濓紙鐢虫姤琛ㄧ8琛岋級
    actual_profit = period_profit
    period_taxable = max(actual_profit, 0)

    # 绗?0琛岋細搴旂撼绋庨 = 搴旂撼绋庢墍寰楅 脳 鏍囧噯绋庣巼
    tax_before_relief = round(period_taxable * standard_rate, 2)

    # 绗?1琛岋細鍑忓厤鎵€寰楃◣棰?    if is_small_low_profit and period_taxable > 0:
        tax_actual = round(period_taxable * effective_rate, 2)
        relief = round(tax_before_relief - tax_actual, 2)
    else:
        tax_actual = tax_before_relief
        relief = 0.0

    # 绗?3琛岋細鏈湡搴旇ˉ锛堥€€锛夋墍寰楃◣棰?    tax_payable = round(tax_actual - tax_paid_ytd, 2)
    if tax_payable < 0:
        tax_payable = 0.0

    result = {
        "钀ヤ笟鏀跺叆": round(revenue, 2),
        "钀ヤ笟鎴愭湰": round(cost, 2),
        "鍒╂鼎鎬婚": round(period_profit, 2),
        "瀹為檯鍒╂鼎棰?: round(actual_profit, 2),
        "搴旂撼绋庢墍寰楅": period_taxable,
        "鏍囧噯绋庣巼": standard_rate,
        "浼樻儬瀹為檯绋庣巼": effective_rate,
        "搴旂撼绋庨_鏍囧噯": tax_before_relief,
        "鍑忓厤鎵€寰楃◣棰?: relief,
        "鏈湡搴旂撼绋庨": tax_actual,
        "鏈勾绱宸查缂?: tax_paid_ytd,
        "鏈湡搴旇ˉ(閫€)绋庨": tax_payable,
        "浠庝笟浜烘暟": num_employees,
        "璧勪骇鎬婚_涓囧厓": total_assets,
        "鏄惁灏忓瀷寰埄浼佷笟": "鏄? if is_small_low_profit else "鍚?,
        "_鏀跨瓥渚濇嵁": cit_ref,
        "_鏀跨瓥鍖洪棿": pol["_meta"]["period"],
    }

    # 闄勫姞绋庢眹鎬伙紙濡傛灉鏈夛級
    if vat_data:
        result["澧炲€肩◣搴旂即"] = vat_data.get("澧炲€肩◣搴旂即", 0.0)
        result["闄勫姞绋庡悎璁?] = vat_data.get("闄勫姞绋庡悎璁?, 0.0)
        result["鏈湡绋庤垂鍚堣"] = round(
            tax_payable
            + vat_data.get("澧炲€肩◣搴旂即", 0.0)
            + vat_data.get("闄勫姞绋庡悎璁?, 0.0),
            2
        )
    else:
        result["澧炲€肩◣搴旂即"] = 0.0
        result["闄勫姞绋庡悎璁?] = 0.0
        result["鏈湡绋庤垂鍚堣"] = tax_payable

    return result


def get_tax_policy_summary(
    is_small_scale: bool = True,
    is_small_low_profit: bool = True,
    quarter_revenue: float = 0.0,
    num_employees: int = 1,
    total_assets: float = 0.0,
    quarter: int = 1,
) -> dict:
    """
    姹囨€诲綋鍓嶄紒涓氶€傜敤鐨勫叏閮ㄧ◣鏀朵紭鎯犳斂绛?
    鏀跨瓥鎻忚堪浼樺厛浠?tax_policies.json 璇诲彇銆?    """
    pol = load_tax_policies()
    vat_pol = pol["vat"]
    sur_pol = pol["surcharges"]
    cit_pol = pol["corporate_income_tax"]
    def_pol = pol["disabled_employment_fund"]
    period_label = pol["_meta"]["period"]
    effective_until = pol["_meta"]["effective_until"]

    policies = []

    # 1. 澧炲€肩◣浼樻儬
    if is_small_scale:
        threshold = vat_pol["quarterly_exempt_threshold"]
        revenue_excl = quarter_revenue / (1 + vat_pol["small_scale_nominal_rate"]) if quarter_revenue else 0
        if quarter_revenue <= 0 or revenue_excl <= threshold:
            policies.append({
                "绋庣": "澧炲€肩◣",
                "浼樻儬鍚嶇О": "灏忚妯＄撼绋庝汉瀛ｅ害鍏嶇◣",
                "浼樻儬鍐呭": f"瀛ｅ害涓嶅惈绋庢敹鍏?鈮?{threshold//10000}涓囧厓锛屽厤寰佸鍊肩◣",
                "鏀跨瓥渚濇嵁": vat_pol["policy_ref"],
                "閫傜敤鏉′欢": f"灏忚妯＄撼绋庝汉 + 瀛ｆ敹鍏モ墹{threshold//10000}涓?,
                "浼樻儬鍔涘害": "100% 鍏嶅緛",
                "鍑忓厤閲戦": 0.0,
            })
        else:
            eff = vat_pol["small_scale_effective_rate"]
            nom = vat_pol["small_scale_nominal_rate"]
            policies.append({
                "绋庣": "澧炲€肩◣",
                "浼樻儬鍚嶇О": f"灏忚妯＄撼绋庝汉鍑忔寜{eff*100:.0f}%寰佹敹",
                "浼樻儬鍐呭": f"閫傜敤{nom*100:.0f}%寰佹敹鐜囩殑搴旂◣閿€鍞敹鍏ワ紝鍑忔寜{eff*100:.0f}%寰佹敹澧炲€肩◣",
                "鏀跨瓥渚濇嵁": vat_pol["policy_ref"],
                "閫傜敤鏉′欢": f"灏忚妯＄撼绋庝汉锛屽鏀跺叆瓒厈threshold//10000}涓?,
                "浼樻儬鍔涘害": f"{nom*100:.0f}% 鈫?{eff*100:.0f}%锛堟湁鏁堥檷浣巤round((1-eff/nom)*100):.0f}%锛?,
                "鍑忓厤閲戦": 0.0,
            })

    # 2. 鍏◣涓よ垂鍑忓崐
    if sur_pol.get("six_two_half_enabled", True) and (is_small_scale or is_small_low_profit):
        policies.append({
            "绋庣": "鍩庡缓绋?,
            "浼樻儬鍚嶇О": "銆屽叚绋庝袱璐广€嶅噺鍗婂緛鏀?,
            "浼樻儬鍐呭": f"鍩庡缓绋庡噺鎸夊疄闄呯即绾冲鍊肩◣鐨?{sur_pol['urban_construction_effective']*100:.1f}%锛堝師{sur_pol['urban_construction_nominal']*100:.0f}%锛?,
            "鏀跨瓥渚濇嵁": sur_pol["policy_ref"],
            "閫傜敤鏉′欢": "灏忚妯＄撼绋庝汉 鎴?灏忓瀷寰埄浼佷笟 鉁?,
            "浼樻儬鍔涘害": "鍑忓厤 50%",
            "鍑忓厤閲戦": 0.0,
        })
        policies.append({
            "绋庣": "鏁欒偛璐归檮鍔?+ 鍦版柟鏁欒偛闄勫姞",
            "浼樻儬鍚嶇О": "銆屽叚绋庝袱璐广€嶅噺鍗婂緛鏀?,
            "浼樻儬鍐呭": f"鏁欒偛璐归檮鍔?{sur_pol['education_effective']*100:.1f}%锛堝師{sur_pol['education_nominal']*100:.0f}%锛? 鍦版柟鏁欒偛闄勫姞 {sur_pol['local_education_effective']*100:.0f}%锛堝師{sur_pol['local_education_nominal']*100:.0f}%锛?,
            "鏀跨瓥渚濇嵁": sur_pol["policy_ref"],
            "閫傜敤鏉′欢": "灏忚妯＄撼绋庝汉 鎴?灏忓瀷寰埄浼佷笟 鉁?,
            "浼樻儬鍔涘害": "鍑忓厤 50%",
            "鍑忓厤閲戦": 0.0,
        })

    # 3. 浼佷笟鎵€寰楃◣灏忓瀷寰埄
    if is_small_low_profit:
        eff = cit_pol["small_low_profit_effective_rate"]
        std = cit_pol["standard_rate"]
        criteria = cit_pol["small_low_profit_criteria"]
        policies.append({
            "绋庣": "浼佷笟鎵€寰楃◣",
            "浼樻儬鍚嶇О": "灏忓瀷寰埄浼佷笟鎵€寰楃◣浼樻儬",
            "浼樻儬鍐呭": f"鍑忔寜25%璁″叆搴旂撼绋庢墍寰楅锛屾寜20%绋庣巼缂寸撼锛屽疄闄呯◣璐?{eff*100:.0f}%",
            "鏀跨瓥渚濇嵁": cit_pol["policy_ref"],
            "閫傜敤鏉′欢": f"骞村埄娑︹墹{criteria['max_annual_taxable_income']//10000}涓?+ 鍛樺伐鈮criteria['max_employees']}浜?+ 璧勪骇鈮criteria['max_assets_wan']}涓?鉁?,
            "浼樻儬鍔涘害": f"{std*100:.0f}% 鈫?{eff*100:.0f}%锛堟湁鏁堥檷浣巤round((1-eff/std)*100):.0f}%锛?,
            "鍑忓厤閲戦": 0.0,
        })

    # 4. 娈嬩繚閲?    micro_threshold = def_pol["micro_exempt_threshold"]
    if num_employees <= micro_threshold:
        policies.append({
            "绋庣": "娈嬬柧浜哄氨涓氫繚闅滈噾",
            "浼樻儬鍚嶇О": "灏忓井浼佷笟娈嬩繚閲戝厤寰?,
            "浼樻儬鍐呭": f"鍦ㄨ亴鑱屽伐鎬绘暟 鈮?{micro_threshold}浜猴紝鍏嶅緛娈嬬柧浜哄氨涓氫繚闅滈噾",
            "鏀跨瓥渚濇嵁": def_pol["policy_ref"],
            "閫傜敤鏉′欢": f"鍛樺伐 {num_employees}浜?鈮?{micro_threshold}浜?鉁?,
            "浼樻儬鍔涘害": "100% 鍏嶅緛",
            "鍑忓厤閲戦": 0.0,
        })

    return {
        "policies": policies,
        "title": "婀栧寳鐪?姝︽眽甯?绋庢敹浼樻儬鏀跨瓥閫傜敤娓呭崟",
        "valid_until": f"浠ヤ笂鏀跨瓥鏈夋晥鏈熻嚦 {effective_until}锛堟斂绛栧尯闂达細{period_label}锛?,
        "tip": "浠ヤ笂浼樻儬鏀跨瓥鐢虫姤鏃剁郴缁熻嚜鍔ㄨ瘑鍒噺鍏嶏紝婀栧寳鐪佸凡瀹炵幇銆屽厤鐢冲嵆浜€嶏紝鏃犻渶棰濆鐢宠澶囨銆?,
    }


def calc_disabled_employment_fund(
    prev_year_employees: int,
    prev_year_disabled_employees: int = 0,
    prev_year_avg_salary: float = 0.0,
    local_avg_salary: float = 0.0,
    year: int = None,
) -> dict:
    """
    璁＄畻娈嬬柧浜哄氨涓氫繚闅滈噾锛堟畫淇濋噾锛?
    绋庣巼鍙傛暟浠?tax_policies.json 璇诲彇銆?
    鍙傛暟锛?      prev_year_employees:         涓婂勾鐢ㄤ汉鍗曚綅鍦ㄨ亴鑱屽伐浜烘暟
      prev_year_disabled_employees: 涓婂勾瀹為檯瀹夋帓鐨勬畫鐤句汉灏变笟浜烘暟
      prev_year_avg_salary:         涓婂勾鐢ㄤ汉鍗曚綅鍦ㄨ亴鑱屽伐骞村钩鍧囧伐璧勶紙鍏冿級
      local_avg_salary:             褰撳湴绀句細骞冲潎宸ヨ祫锛堝厓锛岀敤浜?鍊嶅皝椤讹級
      year:                         鐢虫姤骞翠唤
    """
    if year is None:
        year = datetime.now().year

    pol = load_tax_policies(year)
    def_pol = pol["disabled_employment_fund"]
    required_ratio = def_pol["required_ratio"]
    micro_threshold = def_pol["micro_exempt_threshold"]
    cap_mult = def_pol["salary_cap_multiplier"]
    tiers = def_pol["tier_reduction"]
    def_ref = def_pol["policy_ref"]

    # ===== 1. 灏忓井浼佷笟鍏嶅緛 =====
    if prev_year_employees <= micro_threshold:
        return {
            "鐢虫姤骞村害": year,
            "涓婂勾鑱屽伐浜烘暟": prev_year_employees,
            "涓婂勾娈嬬柧鑱屽伐浜烘暟": prev_year_disabled_employees,
            "涓婂勾鑱屽伐骞村潎宸ヨ祫": round(prev_year_avg_salary, 2),
            "娉曞畾瀹夋帓姣斾緥": f"{required_ratio*100:.1f}%",
            "搴斿畨鎺掍汉鏁?: round(prev_year_employees * required_ratio, 2),
            "宸浜烘暟": 0,
            "宸ヨ祫璁＄畻鍩烘暟": 0.0,
            "鍒嗘。寰佹敹姣斾緥": "鍏嶅緛",
            "搴旂即娈嬩繚閲戯紙鍏ㄩ锛?: 0.0,
            "鍑忓厤閲戦": 0.0,
            "鏄惁灏忓井浼佷笟鍏嶅緛": "鏄?鉁?,
            "鍏嶅緛鏉′欢": f"鍦ㄨ亴鑱屽伐 {prev_year_employees}浜?鈮?{micro_threshold}浜?,
            "搴旂即娈嬩繚閲?: 0.0,
            "鍑忓厤閲戦": 0.0,
            "浼樻儬鏀跨瓥": f"灏忓井浼佷笟鍏嶅緛锛坽def_ref}锛?,
            "鏀跨瓥渚濇嵁": def_ref,
            "鐢虫姤瑕佹眰": "浠嶉渶闆剁敵鎶ワ紙杩涘叆鐢靛瓙绋庡姟灞€濉啓鍚庣郴缁熻嚜鍔ㄨ绠椾负0锛?,
            "鐢虫姤鎴": f"閫氬父鍦?{year} 骞?7~9 鏈堬紙浠ュ綋鍦版畫鑱斿叕鍛婁负鍑嗭級",
            "璁＄畻璇存槑": f"鍛樺伐 {prev_year_employees}浜?鈮?{micro_threshold}浜?鈫?鍏ㄩ鍏嶅緛",
            "_鏀跨瓥鍖洪棿": pol["_meta"]["period"],
        }

    # ===== 2. 鍒嗘璁＄畻锛?micro_threshold浜猴級=====
    required_disabled = prev_year_employees * required_ratio
    actual_ratio = prev_year_disabled_employees / prev_year_employees if prev_year_employees > 0 else 0

    salary_cap = local_avg_salary * cap_mult if local_avg_salary > 0 else float('inf')
    calc_salary = min(prev_year_avg_salary, salary_cap)

    gap = required_disabled - prev_year_disabled_employees

    # 宸茶揪鏍?鈫?鍏ㄩ鍏嶅緛
    if gap <= 0:
        payable = 0.0
        exempted = 0.0
        reduction_rate = 1.0
        reduction_note = f"宸茶揪鏍囧畨鎺掓瘮渚嬶紙瀹為檯 {actual_ratio:.2%} 鈮?{required_ratio*100:.1f}%锛夛紝鍏嶅緛娈嬩繚閲?
        base_amount = 0.0
    else:
        base_amount = gap * calc_salary

        # 鍒嗘。鍑忓緛
        full = tiers["full_compliance"]
        partial = tiers["partial_compliance"]
        non = tiers["non_compliance"]

        if actual_ratio >= partial["min_ratio"]:
            reduction_rate = partial["rate"]
            reduction_note = partial["label"]
        else:
            reduction_rate = non["rate"]
            reduction_note = non["label"]

        payable = round(base_amount * reduction_rate, 2)
        exempted = round(base_amount - payable, 2)

    return {
        "鐢虫姤骞村害": year,
        "涓婂勾鑱屽伐浜烘暟": prev_year_employees,
        "涓婂勾娈嬬柧鑱屽伐浜烘暟": prev_year_disabled_employees,
        "涓婂勾鑱屽伐骞村潎宸ヨ祫": round(prev_year_avg_salary, 2),
        "娉曞畾瀹夋帓姣斾緥": f"{required_ratio*100:.1f}%",
        "搴斿畨鎺掍汉鏁?: round(required_disabled, 4),
        "瀹為檯瀹夋帓姣斾緥": f"{actual_ratio:.2%}",
        "宸浜烘暟": round(gap, 4),
        "宸ヨ祫璁＄畻鍩烘暟": round(calc_salary, 2),
        "宸ヨ祫灏侀《璇存槑": f"褰撳湴绀惧钩宸ヨ祫脳{cap_mult}={salary_cap:,.2f}鍏? if local_avg_salary > 0 else "鏈缃皝椤?,
        "鏄惁灏忓井浼佷笟鍏嶅緛": "鍚?,
        "搴旂即娈嬩繚閲戯紙鍏ㄩ锛?: round(base_amount, 2),
        "鍒嗘。寰佹敹姣斾緥": f"{reduction_rate:.0%}",
        "鍒嗘。璇存槑": reduction_note,
        "搴旂即娈嬩繚閲?: payable,
        "鍑忓厤閲戦": exempted,
        "浼樻儬鏀跨瓥": reduction_note,
        "鏀跨瓥渚濇嵁": def_ref,
        "鐢虫姤瑕佹眰": f"鐢虫姤骞剁即绾?{payable:,.2f} 鍏?,
        "鐢虫姤鎴": f"閫氬父鍦?{year} 骞?7~9 鏈堬紙浠ュ綋鍦版畫鑱斿叕鍛婁负鍑嗭級",
        "璁＄畻璇存槑": f"({prev_year_employees}浜?脳 {required_ratio*100:.1f}% - {prev_year_disabled_employees}浜? 脳 {calc_salary:,.2f}鍏?脳 {reduction_rate:.0%} = {payable:,.2f} 鍏?,
        "_鏀跨瓥鍖洪棿": pol["_meta"]["period"],
    }


def calc_stamp_duty(
    registered_capital: float = 0.0,
    capital_increase: float = 0.0,
    capital_reserve: float = 0.0,
    purchase_amount: float = 0.0,
    loan_amount: float = 0.0,
    tech_amount: float = 0.0,
    property_lease_amount: float = 0.0,
    is_small_low_profit: bool = True,
    tax_year: int = None,
) -> dict:
    """
    璁＄畻鍗拌姳绋?
    绋庣巼鍙傛暟浠?tax_policies.json 璇诲彇锛屾寜鐢虫姤骞村害鑷姩鍖归厤銆?
    鍙傛暟锛?      registered_capital:  鏈湡瀹炴敹璧勬湰鍙樺姩锛堝厓锛?      capital_increase:    鏈湡澧炶祫棰濓紙鍏冿級
      capital_reserve:     璧勬湰鍏Н鍙樺姩锛堝厓锛?      purchase_amount:     鏈湡璐攢鍚堝悓閲戦锛堝厓锛?      loan_amount:         鏈湡鍊熸鍚堝悓閲戦锛堝厓锛?      tech_amount:         鏈湡鎶€鏈悎鍚岄噾棰濓紙鍏冿級
      property_lease_amount: 鏈湡璐骇绉熻祦鍚堝悓閲戦锛堝厓锛?      is_small_low_profit: 鏄惁灏忓瀷寰埄浼佷笟
      tax_year:            鐢虫姤骞村害
    """
    pol = load_tax_policies(tax_year if tax_year else None)
    sd_pol = pol["stamp_duty"]
    half_enabled = sd_pol.get("half_enabled", True) and is_small_low_profit
    half = 0.5 if half_enabled else 1.0
    categories = sd_pol["categories"]
    sd_ref = sd_pol["policy_ref"]

    # ===== 鍚勭◣鐩绠?=====
    items = []

    def _fmt_rate(nominal, effective):
        """鏍煎紡鍖栫◣鐜囨樉绀?""
        return f"{nominal*100:.3f}%锛堜竾鍒嗕箣{nominal*10000:.1f}锛?, f"{effective*100:.4f}%锛堜竾鍒嗕箣{effective*10000:.2f}锛?

    # 1. 璧勯噾璐︾翱
    cap_cat = categories["capital_book"]
    capital_base = registered_capital + capital_increase + capital_reserve
    capital_tax = round(capital_base * cap_cat["effective_rate"], 2)
    if capital_base > 0:
        nr, er = _fmt_rate(cap_cat["nominal_rate"], cap_cat["effective_rate"])
        items.append({
            "绋庣洰": cap_cat["name"],
            "鍝佺被": cap_cat["basis"],
            "鍚嶄箟绋庣巼": nr,
            "浼樻儬鍚庣◣鐜?: er,
            "璁＄◣鍩虹锛堝厓锛?: capital_base,
            "搴旂撼绋庨锛堝厓锛?: capital_tax,
            "璇存槑": f"娉ㄥ唽璧勬湰鍒颁綅/澧炶祫 {capital_base:,.2f} 鍏? + (" 鍏◣涓よ垂鍑忓崐" if half_enabled else ""),
        })

    # 2. 璐攢鍚堝悓
    pur_cat = categories["purchase_contract"]
    purchase_tax = round(purchase_amount * pur_cat["effective_rate"], 2)
    if purchase_amount > 0:
        nr, er = _fmt_rate(pur_cat["nominal_rate"], pur_cat["effective_rate"])
        items.append({
            "绋庣洰": pur_cat["name"],
            "鍝佺被": pur_cat["basis"],
            "鍚嶄箟绋庣巼": nr,
            "浼樻儬鍚庣◣鐜?: er,
            "璁＄◣鍩虹锛堝厓锛?: purchase_amount,
            "搴旂撼绋庨锛堝厓锛?: purchase_tax,
            "璇存槑": f"璐攢閲戦 {purchase_amount:,.2f} 鍏? + (" 鍏◣涓よ垂鍑忓崐" if half_enabled else ""),
        })

    # 3. 鍊熸鍚堝悓
    loan_cat = categories["loan_contract"]
    loan_tax = round(loan_amount * loan_cat["effective_rate"], 2)
    if loan_amount > 0:
        nr, er = _fmt_rate(loan_cat["nominal_rate"], loan_cat["effective_rate"])
        items.append({
            "绋庣洰": loan_cat["name"],
            "鍝佺被": loan_cat["basis"],
            "鍚嶄箟绋庣巼": nr,
            "浼樻儬鍚庣◣鐜?: er,
            "璁＄◣鍩虹锛堝厓锛?: loan_amount,
            "搴旂撼绋庨锛堝厓锛?: loan_tax,
            "璇存槑": f"鍊熸閲戦 {loan_amount:,.2f} 鍏? + (" 鍏◣涓よ垂鍑忓崐" if half_enabled else ""),
        })

    # 4. 鎶€鏈悎鍚?    tech_cat = categories["tech_contract"]
    tech_tax = round(tech_amount * tech_cat["effective_rate"], 2)
    if tech_amount > 0:
        nr, er = _fmt_rate(tech_cat["nominal_rate"], tech_cat["effective_rate"])
        items.append({
            "绋庣洰": tech_cat["name"],
            "鍝佺被": tech_cat["basis"],
            "鍚嶄箟绋庣巼": nr,
            "浼樻儬鍚庣◣鐜?: er,
            "璁＄◣鍩虹锛堝厓锛?: tech_amount,
            "搴旂撼绋庨锛堝厓锛?: tech_tax,
            "璇存槑": f"鎶€鏈悎鍚岄噾棰?{tech_amount:,.2f} 鍏? + (" 鍏◣涓よ垂鍑忓崐" if half_enabled else ""),
        })

    # 5. 璐骇绉熻祦鍚堝悓
    prop_cat = categories["property_lease"]
    property_tax = round(property_lease_amount * prop_cat["effective_rate"], 2)
    if property_lease_amount > 0:
        nr, er = _fmt_rate(prop_cat["nominal_rate"], prop_cat["effective_rate"])
        items.append({
            "绋庣洰": prop_cat["name"],
            "鍝佺被": prop_cat["basis"],
            "鍚嶄箟绋庣巼": nr,
            "浼樻儬鍚庣◣鐜?: er,
            "璁＄◣鍩虹锛堝厓锛?: property_lease_amount,
            "搴旂撼绋庨锛堝厓锛?: property_tax,
            "璇存槑": f"绉熻祦閲戦 {property_lease_amount:,.2f} 鍏? + (" 鍏◣涓よ垂鍑忓崐" if half_enabled else ""),
        })

    total_stamp_duty = round(sum(i["搴旂撼绋庨锛堝厓锛?] for i in items), 2)
    nominal_total = round(sum(i["璁＄◣鍩虹锛堝厓锛?] * cats_nominal_rate(categories, i["绋庣洰"]) for i in items), 2)
    relief = round(nominal_total - total_stamp_duty, 2)

    return {
        "鏄庣粏": items,
        "绋庣洰鏁伴噺": len(items),
        "鍗拌姳绋庡悎璁★紙鍚嶄箟锛?: nominal_total,
        "鍏◣涓よ垂鍑忓厤": relief,
        "鍗拌姳绋庡悎璁★紙搴旂即锛?: total_stamp_duty,
        "鏄惁鍏◣涓よ垂鍑忓崐": "鏄? if half_enabled else "鍚?,
        "鏀跨瓥渚濇嵁": sd_ref,
        "鐢虫姤鏂瑰紡": "鎸夋鎴栨寜鏈熸眹鎬?鈫?婀栧寳鐪佺數瀛愮◣鍔″眬 鈫?銆屽嵃鑺辩◣鐢虫姤銆?,
        "鎻愮ず": "璧勯噾璐︾翱浠呭湪鍒濆鍒颁綅鎴栧璧勬椂缂寸撼锛屽凡缂撮儴鍒嗕笉閲嶅寰佹敹",
        "_鏀跨瓥鍖洪棿": pol["_meta"]["period"],
    }


def cats_nominal_rate(categories: dict, name: str) -> float:
    """浠?categories 鍙嶅悜鏌ユ壘鍚嶄箟绋庣巼锛堢敤浜庡噺鍏嶉噾棰濊绠楋級"""
    for key, cat in categories.items():
        if cat["name"] == name:
            return cat["nominal_rate"]
    return 0.0


def format_corporate_tax_report(result: dict, quarter: int, year: int, vat_data: dict = None) -> str:
    """鐢熸垚浼佷笟鎵€寰楃◣鍙婄◣璐规祴绠楃敵鎶ヨ鏄庢枃瀛楋紙鍖归厤A200000鏍煎紡锛?""
    lines = [
        f"{'='*70}",
        f"  {year}骞寸{quarter}瀛ｅ害 浼佷笟鎵€寰楃◣棰勭即 + 澧炲€肩◣鍙婇檮鍔犳祴绠楄鏄?,
        f"  锛堝尮閰?A200000 鐢虫姤琛ㄦ牸寮?| 鍚鍊肩◣/鍩庡缓绋?鏁欒偛璐归檮鍔狅級",
        f"{'='*70}",
        "",
        f"涓€銆佸熀鏈俊鎭?,
        f"  绾崇◣浜哄悕绉帮細    姝︽眽閲戣壋榫欑鎶€鏈夐檺鍏徃",
        f"  鎵€灞炴湡闂达細      {year}骞磠[1,4,7,10][quarter-1]}鏈?1鏃?鑷?{year}骞磠[3,6,9,12][quarter-1]}鏈?1鏃?,
        f"  浼佷笟绫诲瀷锛?    {result['鏄惁灏忓瀷寰埄浼佷笟']}锛堝皬鍨嬪井鍒╀紒涓氾級",
        f"  浠庝笟浜烘暟锛?    {result['浠庝笟浜烘暟']} 浜?,
        f"  璧勪骇鎬婚锛?    {result['璧勪骇鎬婚_涓囧厓']:.2f} 涓囧厓",
        "",
        f"{'鈹€'*50}",
        f"浜屻€佹敹鍏ユ垚鏈埄娑︼紙鐢虫姤琛ㄧ1~3琛岋級",
        f"{'鈹€'*50}",
        f"  绗?琛?钀ヤ笟鏀跺叆锛?      {result['钀ヤ笟鏀跺叆']:>15,.2f} 鍏?,
        f"  绗?琛?钀ヤ笟鎴愭湰锛?      {result['钀ヤ笟鎴愭湰']:>15,.2f} 鍏?,
        f"  绗?琛?鍒╂鼎鎬婚锛?      {result['鍒╂鼎鎬婚']:>15,.2f} 鍏?,
        "",
        f"{'鈹€'*50}",
        f"涓夈€佸簲绾崇◣鎵€寰楅璁＄畻锛堢敵鎶ヨ〃绗?~8琛岋級",
        f"{'鈹€'*50}",
        f"  绗?琛?鐗瑰畾涓氬姟璋冩暣锛?   {0:>15,.2f}",
        f"  绗?琛?涓嶅緛绋庢敹鍏ワ細       {0:>15,.2f}",
        f"  绗?琛?鍥哄畾璧勪骇鎶樻棫璋冩暣锛?{0:>15,.2f}",
        f"  绗?琛?寮ヨˉ浠ュ墠骞村害浜忔崯锛?{0:>15,.2f}",
        f"  鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€",
        f"  绗?琛?瀹為檯鍒╂鼎棰濓細       {result['瀹為檯鍒╂鼎棰?]:>15,.2f} 鍏?,
        "",
        f"{'鈹€'*50}",
        f"鍥涖€佺◣娆捐绠楋紙鐢虫姤琛ㄧ9~13琛岋級",
        f"{'鈹€'*50}",
        f"  绗?琛?绋庣巼锛?5%锛夛細       {'25%':>15s}",
        f"  绗?0琛?搴旂撼鎵€寰楃◣棰濓細     {result['搴旂撼绋庨_鏍囧噯']:>15,.2f} 鍏?,
        f"  绗?1琛?鍑忓厤鎵€寰楃◣棰濓細     {result['鍑忓厤鎵€寰楃◣棰?]:>15,.2f} 鍏?,
        f"  绗?2琛?鏈勾绱宸查缂达細   {result['鏈勾绱宸查缂?]:>15,.2f} 鍏?,
        f"  鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€",
        f"  绗?3琛?鏈湡搴旇ˉ(閫€)绋庨锛?{result['鏈湡搴旇ˉ(閫€)绋庨']:>15,.2f} 鍏?,
        "",
        f"{'鈹€'*50}",
        f"浜斻€佽绠楄鏄?,
        f"{'鈹€'*50}",
    ]

    if result['鍒╂鼎鎬婚'] <= 0:
        lines.extend([
            f"  銆愭湰鏈熶簭鎹熴€戝埄娑︽€婚涓?{result['鍒╂鼎鎬婚']:,.2f} 鍏冿紙璐熸暟锛夛紝",
            f"             瀹為檯鍒╂鼎棰濆彇0鎴栦繚鐣欒礋鏁帮紝鏃犻渶缂寸撼浼佷笟鎵€寰楃◣銆?,
            f"",
            f"  绗?0琛屽簲绾虫墍寰楃◣棰?= max(瀹為檯鍒╂鼎棰? 0) 脳 25% = 0 鍏?,
            f"  绗?1琛屽噺鍏嶆墍寰楃◣棰?= 0 鍏冿紙浜忔崯鏃犲噺鍏嶏級",
            f"  绗?3琛屾湰鏈熷簲琛ラ€€绋庨 = 0 鍏?,
        ])
    else:
        if result['鏄惁灏忓瀷寰埄浼佷笟'] == '鏄?:
            lines.extend([
                f"  銆愬皬鍨嬪井鍒╀紒涓氫紭鎯犮€?024-2027骞存斂绛栵細",
                f"  - 鍑忔寜25%璁″叆搴旂撼绋庢墍寰楅锛屾寜20%绋庣巼寰佹敹",
                f"  - 瀹為檯绋庤礋 = 25% 脳 20% = 5%",
                f"",
                f"  绗?0琛屽簲绾虫墍寰楃◣棰?= {result['搴旂撼绋庢墍寰楅']:,.2f} 脳 25% = {result['搴旂撼绋庨_鏍囧噯']:,.2f} 鍏?,
                f"  绗?1琛屽噺鍏嶆墍寰楃◣棰?= {result['搴旂撼绋庨_鏍囧噯']:,.2f} - {result['鏈湡搴旂撼绋庨']:,.2f} = {result['鍑忓厤鎵€寰楃◣棰?]:,.2f} 鍏?,
                f"  绗?3琛屾湰鏈熷簲琛ラ€€绋庨 = {result['鏈湡搴旂撼绋庨']:,.2f} - {result['鏈勾绱宸查缂?]:,.2f} = {result['鏈湡搴旇ˉ(閫€)绋庨']:,.2f} 鍏?,
            ])
        else:
            lines.extend([
                f"  銆愪竴鑸紒涓氥€戦€傜敤鏍囧噯绋庣巼 25%",
                f"  绗?0琛屽簲绾虫墍寰楃◣棰?= {result['搴旂撼绋庢墍寰楅']:,.2f} 脳 25% = {result['搴旂撼绋庨_鏍囧噯']:,.2f} 鍏?,
                f"  绗?1琛屽噺鍏嶆墍寰楃◣棰?= 0 鍏?,
                f"  绗?3琛屾湰鏈熷簲琛ラ€€绋庨 = {result['鏈湡搴旂撼绋庨']:,.2f} 鍏?,
            ])

    lines.extend([
        "",
        f"{'鈹€'*50}",
        f"鍏€佸鍊肩◣鍙婇檮鍔犵◣娴嬬畻锛堝弬鑰冿級",
        f"{'鈹€'*50}",
    ])

    if vat_data:
        lines.extend([
            f"  澧炲€肩◣绫诲瀷锛?   {'灏忚妯＄撼绋庝汉3%' if vat_data['鏄惁灏忚妯＄撼绋庝汉']=='鏄? else '涓€鑸撼绋庝汉'}",
            f"  瀛ｅ害鍚◣鏀跺叆锛? {vat_data['瀛ｅ害鍚◣鏀跺叆']:>15,.2f} 鍏?,
            f"  瀛ｅ害涓嶅惈绋庢敹鍏ワ細{vat_data['瀛ｅ害涓嶅惈绋庢敹鍏?]:>15,.2f} 鍏?,
            f"  澧炲€肩◣璇存槑锛?   {vat_data['澧炲€肩◣鍏嶇◣璇存槑']}",
            f"  澧炲€肩◣搴旂即锛?   {vat_data['澧炲€肩◣搴旂即']:>15,.2f} 鍏?,
            f"  鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€",
            f"  鍩庡缓绋?7%)锛?   {vat_data['鍩庡缓绋?7%)']:>15,.2f} 鍏?,
            f"  鏁欒偛璐归檮鍔?3%)锛歿vat_data['鏁欒偛璐归檮鍔?3%)']:>15,.2f} 鍏?,
            f"  鍦版柟鏁欒偛闄勫姞(2%)锛歿vat_data['鍦版柟鏁欒偛闄勫姞(2%)']:>13,.2f} 鍏?,
            f"  闄勫姞绋庡悎璁★細    {vat_data['闄勫姞绋庡悎璁?]:>15,.2f} 鍏?,
            f"  鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€",
            f"  澧炲€肩◣+闄勫姞鍚堣锛歿vat_data['澧炲€肩◣鍙婇檮鍔犲悎璁?]:>14,.2f} 鍏?,
        ])
    else:
        lines.append("  锛堟湭褰曞叆澧炲€肩◣淇℃伅锛岃鍦ㄧ敵鎶ョ晫闈㈠～鍐欏搴︽敹鍏ュ悗娴嬬畻锛?)

    lines.extend([
        "",
        f"{'鈹€'*50}",
        f"涓冦€佹湰鏈熺◣璐规眹鎬?,
        f"{'鈹€'*50}",
        f"  浼佷笟鎵€寰楃◣锛堟湰鏈熷簲琛ョ即锛夛細{result['鏈湡搴旇ˉ(閫€)绋庨']:>12,.2f} 鍏?,
        f"  澧炲€肩◣搴旂即锛?             {result.get('澧炲€肩◣搴旂即', 0.0):>12,.2f} 鍏?,
        f"  闄勫姞绋庡悎璁★細              {result.get('闄勫姞绋庡悎璁?, 0.0):>12,.2f} 鍏?,
        f"  鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€",
        f"  鏈湡绋庤垂鍚堣锛?           {result.get('鏈湡绋庤垂鍚堣', result['鏈湡搴旇ˉ(閫€)绋庨']):>12,.2f} 鍏?,
        "",
        f"{'鈹€'*50}",
        f"鍏€佺敵鎶ユ彁閱?,
        f"{'鈹€'*50}",
        "  1. 璇锋牳瀵瑰埄娑︽€婚涓庡埄娑﹁〃锛堝皬浼佷笟浼氳鍑嗗垯锛変竴鑷达紱",
        "  2. 灏忓瀷寰埄浼佷笟浼樻儬鐢辩郴缁熻嚜鍔ㄥ垽鍒紝鏃犻渶棰濆澶囨锛?,
        "  3. 鐢虫姤鎴鏃堕棿涓哄搴︾粓浜嗗悗15鏃ュ唴锛?鏈堛€?鏈堛€?0鏈堛€佹骞?鏈?5鏃ュ墠锛夛紱",
        "  4. 璇峰強鏃跺湪鍥藉绋庡姟鎬诲眬婀栧寳鐪佺數瀛愮◣鍔″眬瀹屾垚棰勭即鐢虫姤銆?,
        "",
        f"{'='*70}",
        f"  鈥斺€?鐢?閲戣壋榫橝I绋庡姟鍔╂墜 鑷姩鐢熸垚 路 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"{'='*70}",
    ])
    return "\n".join(lines)


# ===============================================
#  閾惰娴佹按鑷姩鍒嗙被锛堥伒寰皬浼佷笟浼氳鍑嗗垯锛?# ===============================================

def classify_bank_transaction(desc: str) -> dict:
    """
    鏍规嵁閾惰娴佹按鎽樿锛岃嚜鍔ㄥ垎绫诲埌灏忎紒涓氫細璁″噯鍒欏埄娑﹁〃椤圭洰
    杩斿洖锛歿"category": "钀ヤ笟鏀跺叆", "pl_item": "钀ヤ笟鏀跺叆", "褰卞搷鍒╂鼎": "鏀跺叆"}
    """
    desc = str(desc).lower()
    
    # 涓€銆佽惀涓氭敹鍏ワ紙鍒╂鼎琛ㄧ1琛岋級
    if any(k in desc for k in ["璐ф", "閿€鍞敹鍏?, "鏈嶅姟璐?, "鍜ㄨ璐?, "鏀舵", 
                               "涓昏惀涓氬姟鏀跺叆", "鍏朵粬涓氬姟鏀跺叆", "閿€鍞?, "鏈嶅姟鏀跺叆"]):
        return {
            "category": "钀ヤ笟鏀跺叆",
            "pl_item": "钀ヤ笟鏀跺叆",
            "type": "鏀跺叆",
            "account": "涓昏惀涓氬姟鏀跺叆"
        }
    
    # 浜屻€佽惀涓氭垚鏈紙鍒╂鼎琛ㄧ2琛岋級
    elif any(k in desc for k in ["閲囪喘", "杩涜揣", "鏉愭枡鎴愭湰", "涓昏惀涓氬姟鎴愭湰", 
                                 "鏉愭枡", "鎴愭湰", "杩涜揣鎴愭湰"]):
        return {
            "category": "钀ヤ笟鎴愭湰",
            "pl_item": "钀ヤ笟鎴愭湰",
            "type": "鏀嚭",
            "account": "涓昏惀涓氬姟鎴愭湰"
        }
    
    # 涓夈€佺◣閲戝強闄勫姞锛堝埄娑﹁〃绗?琛岋級
    elif any(k in desc for k in ["绋庨噾", "闄勫姞璐?, "鍩庡缓绋?, "鏁欒偛璐归檮鍔?, 
                                 "鍦版柟鏁欒偛闄勫姞", "鍗拌姳绋?, "鎴夸骇绋?, "鍦熷湴浣跨敤绋?]):
        return {
            "category": "绋庨噾鍙婇檮鍔?,
            "pl_item": "绋庨噾鍙婇檮鍔?,
            "type": "鏀嚭",
            "account": "绋庨噾鍙婇檮鍔?
        }
    
    # 鍥涖€佺鐞嗚垂鐢紙鍒╂鼎琛ㄧ5琛岋級
    elif any(k in desc for k in ["宸ヨ祫", "绀句繚", "鍏Н閲?, "绂忓埄璐?, "濂栭噾", 
                                 "鍏昏€侀噾", "鍖讳繚", "鍖荤枟淇濋櫓", "鐢熻偛淇濋櫓", "澶变笟淇濋櫓", "宸ヤ激淇濋櫓"]):
        return {
            "category": "绠＄悊璐圭敤-浜哄伐",
            "pl_item": "绠＄悊璐圭敤",
            "type": "鏀嚭",
            "account": "绠＄悊璐圭敤-宸ヨ祫绀句繚"
        }
    
    elif any(k in desc for k in ["姘寸數", "鐗╀笟", "鎴跨", "绉熻祦", "鍔炲叕鐢ㄥ搧", 
                                 "鐢佃瘽璐?, "缃戠粶璐?, "缁翠慨璐?]):
        return {
            "category": "绠＄悊璐圭敤-鍔炲叕",
            "pl_item": "绠＄悊璐圭敤",
            "type": "鏀嚭",
            "account": "绠＄悊璐圭敤-鍔炲叕璐?
        }
    
    elif any(k in desc for k in ["宸梾", "浜ら€?, "椁愰ギ", "鎷涘緟", "浼氳璐?, 
                                 "鍩硅璐?, "鍜ㄨ璐?, "瀹¤璐?]):
        return {
            "category": "绠＄悊璐圭敤-鍏朵粬",
            "pl_item": "绠＄悊璐圭敤",
            "type": "鏀嚭",
            "account": "绠＄悊璐圭敤-涓氬姟鎷涘緟璐?
        }
    
    # 浜斻€佽储鍔¤垂鐢紙鍒╂鼎琛ㄧ6琛岋級
    elif any(k in desc for k in ["鍒╂伅", "鎵嬬画璐?, "閾惰鎵嬬画璐?, "姹囨鎵嬬画璐?, 
                                 "璐锋鍒╂伅", "瀛樻鍒╂伅", "缁撴伅"]):
        return {
            "category": "璐㈠姟璐圭敤",
            "pl_item": "璐㈠姟璐圭敤",
            "type": "鏀嚭",
            "account": "璐㈠姟璐圭敤-鎵嬬画璐?
        }
    
    # 鍏€佽惀涓氬鏀跺叆锛堝埄娑﹁〃绗?0琛岋級
    elif any(k in desc for k in ["鏀垮簻琛ュ姪", "琛ヨ创", "缃氭鏀跺叆", "杩濈害閲戞敹鍏?, 
                                 "鎹愯禒鏀跺叆", "鐩樼泩"]):
        return {
            "category": "钀ヤ笟澶栨敹鍏?,
            "pl_item": "钀ヤ笟澶栨敹鍏?,
            "type": "鏀跺叆",
            "account": "钀ヤ笟澶栨敹鍏?
        }
    
    # 涓冦€佽惀涓氬鏀嚭锛堝埄娑﹁〃绗?1琛岋級
    elif any(k in desc for k in ["缃氭", "鎹愯禒", "鎹熷け", "鐩樹簭", "鑷劧鐏惧鎹熷け", 
                                 "杩濈害閲戞敮鍑?]):
        return {
            "category": "钀ヤ笟澶栨敮鍑?,
            "pl_item": "钀ヤ笟澶栨敮鍑?,
            "type": "鏀嚭",
            "account": "钀ヤ笟澶栨敮鍑?
        }
    
    # 鍏€佹姇璧勬敹鐩婏紙鍒╂鼎琛ㄧ8琛岋級
    elif any(k in desc for k in ["鍒嗙孩", "鎶曡祫鏀剁泭", "鑲℃伅", "鐞嗚储鏀剁泭", 
                                 "鎶曡祫鏀跺叆"]):
        return {
            "category": "鎶曡祫鏀剁泭",
            "pl_item": "鎶曡祫鏀剁泭",
            "type": "鏀跺叆",
            "account": "鎶曡祫鏀剁泭"
        }
    
    else:
        return {
            "category": "寰呭垎绫?,
            "pl_item": "寰呭垎绫?,
            "type": "鏈煡",
            "account": "寰呯‘璁?
        }


def generate_profit_statement(df_txns: object) -> dict:
    """
    鏍规嵁閾惰娴佹按DataFrame锛岀敓鎴愬皬浼佷笟浼氳鍑嗗垯鍒╂鼎琛?    df_txns 蹇呴』鍖呭惈鍒楋細["鎽樿", "鏀跺叆閲戦", "鏀嚭閲戦", "鑷姩鍒嗙被"]
    
    杩斿洖鍒╂鼎琛ㄥ悇椤圭洰閲戦锛堝崟浣嶏細鍏冿級
    """
    # 钀ヤ笟鏀跺叆锛堢1琛岋級= 鎵€鏈夎惀涓氭敹鍏ュ垎绫荤殑鏀跺叆閲戦涔嬪拰
    revenue = df_txns[df_txns["鑷姩鍒嗙被"] == "钀ヤ笟鏀跺叆"]["鏀跺叆閲戦"].sum()
    
    # 钀ヤ笟鎴愭湰锛堢2琛岋級= 鎵€鏈夎惀涓氭垚鏈垎绫荤殑鏀嚭閲戦涔嬪拰
    cost = df_txns[df_txns["鑷姩鍒嗙被"] == "钀ヤ笟鎴愭湰"]["鏀嚭閲戦"].sum()
    
    # 绋庨噾鍙婇檮鍔狅紙绗?琛岋級
    tax_expense = df_txns[df_txns["鑷姩鍒嗙被"] == "绋庨噾鍙婇檮鍔?]["鏀嚭閲戦"].sum()
    
    # 绠＄悊璐圭敤锛堢5琛岋級= 鎵€鏈夌鐞嗚垂鐢ㄥ瓙鍒嗙被鐨勬敮鍑洪噾棰濅箣鍜?    manage_expense = df_txns[
        df_txns["鑷姩鍒嗙被"].str.contains("绠＄悊璐圭敤", na=False)
    ]["鏀嚭閲戦"].sum()
    
    # 璐㈠姟璐圭敤锛堢6琛岋級
    finance_expense = df_txns[df_txns["鑷姩鍒嗙被"] == "璐㈠姟璐圭敤"]["鏀嚭閲戦"].sum()
    
    # 鎶曡祫鏀剁泭锛堢8琛岋級
    investment_income = df_txns[df_txns["鑷姩鍒嗙被"] == "鎶曡祫鏀剁泭"]["鏀跺叆閲戦"].sum()
    
    # 钀ヤ笟鍒╂鼎锛堢9琛岋級= 钀ヤ笟鏀跺叆 - 钀ヤ笟鎴愭湰 - 绋庨噾鍙婇檮鍔?- 绠＄悊璐圭敤 - 璐㈠姟璐圭敤 + 鎶曡祫鏀剁泭
    operating_profit = revenue - cost - tax_expense - manage_expense - finance_expense + investment_income
    
    # 钀ヤ笟澶栨敹鍏ワ紙绗?0琛岋級
    other_income = df_txns[df_txns["鑷姩鍒嗙被"] == "钀ヤ笟澶栨敹鍏?]["鏀跺叆閲戦"].sum()
    
    # 钀ヤ笟澶栨敮鍑猴紙绗?1琛岋級
    other_expense = df_txns[df_txns["鑷姩鍒嗙被"] == "钀ヤ笟澶栨敮鍑?]["鏀嚭閲戦"].sum()
    
    # 鍒╂鼎鎬婚锛堢12琛岋級= 钀ヤ笟鍒╂鼎 + 钀ヤ笟澶栨敹鍏?- 钀ヤ笟澶栨敮鍑?    total_profit = operating_profit + other_income - other_expense
    
    # 鎵€寰楃◣璐圭敤锛堢13琛岋級= 鍒╂鼎鎬婚 脳 灏忓瀷寰埄瀹為檯绋庣巼
    if total_profit > 0:
        pol = load_tax_policies()
        eff_rate = pol["corporate_income_tax"]["small_low_profit_effective_rate"]
        income_tax = total_profit * eff_rate
    else:
        income_tax = 0.0
    
    # 鍑€鍒╂鼎锛堢14琛岋級= 鍒╂鼎鎬婚 - 鎵€寰楃◣璐圭敤
    net_profit = total_profit - income_tax
    
    return {
        "钀ヤ笟鏀跺叆": round(revenue, 2),
        "钀ヤ笟鎴愭湰": round(cost, 2),
        "绋庨噾鍙婇檮鍔?: round(tax_expense, 2),
        "绠＄悊璐圭敤": round(manage_expense, 2),
        "璐㈠姟璐圭敤": round(finance_expense, 2),
        "鎶曡祫鏀剁泭": round(investment_income, 2),
        "钀ヤ笟鍒╂鼎": round(operating_profit, 2),
        "钀ヤ笟澶栨敹鍏?: round(other_income, 2),
        "钀ヤ笟澶栨敮鍑?: round(other_expense, 2),
        "鍒╂鼎鎬婚": round(total_profit, 2),
        "鎵€寰楃◣璐圭敤": round(income_tax, 2),
        "鍑€鍒╂鼎": round(net_profit, 2),
    }


def validate_quarterly_declaration(profit_data: dict, revenue: float, cost: float, period_profit: float) -> list:
    """
    鏍￠獙鍒╂鼎琛ㄦ暟鎹笌浼佷笟鎵€寰楃◣瀛ｅ害鐢虫姤琛ㄦ暟鎹槸鍚︿竴鑷?    
    鍙傛暟锛?      profit_data: generate_profit_statement() 鐨勮繑鍥炲€?      revenue: 鐢虫姤琛ㄧ1琛?钀ヤ笟鏀跺叆
      cost: 鐢虫姤琛ㄧ2琛?钀ヤ笟鎴愭湰
      period_profit: 鐢虫姤琛ㄧ3琛?鍒╂鼎鎬婚
    
    杩斿洖锛氭牎楠岀粨鏋滃垪琛紝姣忎釜鍏冪礌涓?(鏄惁閫氳繃, 鎻愮ず淇℃伅)
    """
    results = []
    
    # 鏍￠獙1锛氳惀涓氭敹鍏?    if abs(profit_data["钀ヤ笟鏀跺叆"] - revenue) > 1:
        results.append((False, f"钀ヤ笟鏀跺叆涓嶄竴鑷达細鍒╂鼎琛▄profit_data['钀ヤ笟鏀跺叆']:.2f} vs 鐢虫姤琛▄revenue:.2f}"))
    else:
        results.append((True, f"钀ヤ笟鏀跺叆鏍￠獙閫氳繃锛歿revenue:.2f} 鍏?))
    
    # 鏍￠獙2锛氳惀涓氭垚鏈?    if abs(profit_data["钀ヤ笟鎴愭湰"] - cost) > 1:
        results.append((False, f"钀ヤ笟鎴愭湰涓嶄竴鑷达細鍒╂鼎琛▄profit_data['钀ヤ笟鎴愭湰']:.2f} vs 鐢虫姤琛▄cost:.2f}"))
    else:
        results.append((True, f"钀ヤ笟鎴愭湰鏍￠獙閫氳繃锛歿cost:.2f} 鍏?))
    
    # 鏍￠獙3锛氬埄娑︽€婚
    if abs(profit_data["鍒╂鼎鎬婚"] - period_profit) > 1:
        results.append((False, f"鍒╂鼎鎬婚涓嶄竴鑷达細鍒╂鼎琛▄profit_data['鍒╂鼎鎬婚']:.2f} vs 鐢虫姤琛▄period_profit:.2f}"))
    else:
        results.append((True, f"鍒╂鼎鎬婚鏍￠獙閫氳繃锛歿period_profit:.2f} 鍏?))
    
    return results


# ===============================================
#  涓荤▼搴忥紙绀轰緥锛?# ===============================================
if __name__ == "__main__":
    print("姝︽眽閲戣壋榫欑鎶€ - 涓◣绀句繚璁＄畻宸ュ叿 v1.0")
    print("锛堟棤闇€瀹夎浠讳綍渚濊禆锛岀洿鎺ヨ繍琛岋級\n")

    employees = [
        {
            "name": "鍛樺伐A",
            "gross_salary": 10522,
            "si_base": 5000,
            "si_personal_actual": 522,
            "special_deductions": 5000,
            "child_education": 2000,
            "infant_care": 2000,
            "elderly_care": 1000,
        },
        # 澧炲姞鍛樺伐鍙渶澶嶅埗涓婃柟瀛楀吀锛屼慨鏀瑰鍚嶅拰宸ヨ祫閲戦
        # {
        #     "name": "鍛樺伐B",
        #     "gross_salary": 8000,
        #     ...
        # },
    ]

    results = process_employees(employees)
    print_results(results)
    export_csv(results)

    print("\n[鎻愮ず] 浣跨敤鎻愮ず锛?)
    print("  1. 淇敼涓婃柟 employees 鍒楄〃锛屽鍔?淇敼鍛樺伐鏁版嵁")
    print("  2. 涓撻」闄勫姞鎵ｉ櫎濡傛湁鍙樺寲锛屼慨鏀?special_deductions 瀛楁")
    print("  3. 杩愯锛歱ython tax_calculator.py")
    print("  4. CSV搴曠鍙洿鎺ュ鍏xcel鎴栧彂閫佺粰璐㈠姟")


# ===============================================
#  宸ヨ祫鏁版嵁鏍￠獙锛堥摱琛屾祦姘?/ 涓◣鐢虫姤 / 骞存姤涓夐儴鍒嗭級
# ===============================================

def validate_salary_data(
    employees: list[dict],
    bank_df: "pd.DataFrame | None" = None,
    tax_filing_df: "pd.DataFrame | None" = None,
    annual_total_salary: float = 0.0,
) -> dict:
    """
    涓夐噸鏍￠獙宸ヨ祫鏁版嵁锛岃繑鍥炴牎楠岀粨鏋滃瓧鍏搞€?
    鍙傛暟锛?    - employees: 绯荤粺褰曞叆鐨勫憳宸ュ垪琛紙calc_one_employee 杈撳叆鏍煎紡锛?    - bank_df: 閾惰娴佹按 DataFrame锛岄渶鍚€屾憳瑕併€嶃€屾敮鍑洪噾棰濄€嶅垪
    - tax_filing_df: 涓◣鐢虫姤璁板綍 DataFrame锛岄渶鍚€屽鍚嶃€嶃€岀疮璁℃敹鍏ャ€嶅垪
    - annual_total_salary: 骞存姤涓殑銆屽叏骞村伐璧勬€婚銆嶏紙鐢ㄤ簬绗笁閲嶆牎楠岋級

    杩斿洖锛?    {
        "bank_match": [...],    # 閾惰娴佹按 vs 绯荤粺宸ヨ祫
        "tax_match": [...],    # 涓◣鐢虫姤 vs 绯荤粺宸ヨ祫
        "annual_match": {...},  # 骞存姤宸ヨ祫鎬婚 vs 绯荤粺骞村伐璧勫悎璁?        "warnings": [...],     # 鎵€鏈夎鍛婁俊鎭?    }
    """
    import pandas as pd

    result = {
        "bank_match": [],
        "tax_match": [],
        "annual_match": {},
        "warnings": [],
    }

    # 鈹€鈹€ 绯荤粺宸ヨ祫鍚堣锛堝勾锛?鈹€鈹€
    sys_annual_total = 0.0
    for emp in employees:
        m = emp.get("gross_salary", 0) or 0
        sys_annual_total += m * 12

    # ============================================================
    #  鏍￠獙1锛氶摱琛屾祦姘?vs 绯荤粺宸ヨ祫
    # ============================================================
    if bank_df is not None and len(bank_df) > 0:
        df = bank_df.copy()

        # 鍏煎鍒楀悕
        col_map = {}
        for col in df.columns:
            cl = str(col).strip().lower()
            if any(k in cl for k in ["鎽樿", "澶囨敞", "鐢ㄩ€?, "description"]):
                col_map[col] = "鎽樿"
            elif any(k in cl for k in ["鏀嚭", "鍊熸柟", "鍙栨", "debit", "杞嚭"]):
                col_map[col] = "鏀嚭閲戦"
            elif any(k in cl for k in ["閲戦", "鍙戠敓棰?, "transaction"]):
                col_map[col] = "閲戦"
        df = df.rename(columns=col_map)

        # 鐢?classify_bank_transaction 璇嗗埆宸ヨ祫绫绘敮鍑?        def is_salary_row(desc):
            category = classify_bank_transaction(str(desc))["category"]
            return category in ("绠＄悊璐圭敤-浜哄伐",)

        # 宸ヨ祫鍏抽敭璇嶄簩娆″厹搴?        salary_keywords = ["宸ヨ祫", "钖祫", "缁╂晥", "濂栭噾", "钖叕", "钖按", " salary", "salary", "payroll"]

        def is_salary_desc(desc):
            d = str(desc).lower()
            return any(k in d for k in salary_keywords)

        # 鎻愬彇鏀嚭閲戦鍒?        amount_col = None
        for c in ["鏀嚭閲戦", "閲戦"]:
            if c in df.columns:
                amount_col = c
                break
        if amount_col is None:
            for c in df.columns:
                if any(k in str(c).lower() for k in ["鏀嚭", "鍊熸柟", "amount", "閲戦"]):
                    amount_col = c
                    break

        if amount_col:
            df["_is_salary"] = df["鎽樿"].apply(lambda x: is_salary_row(x) or is_salary_desc(x))
            salary_txns = df[df["_is_salary"] == True].copy()

            if len(salary_txns) > 0:
                bank_salary_total = salary_txns[amount_col].astype(float).sum()
                diff = sys_annual_total - bank_salary_total
                pct = (diff / bank_salary_total * 100) if bank_salary_total > 0 else 0

                result["bank_match"] = {
                    "bank_salary_total": round(bank_salary_total, 2),
                    "sys_annual_total": round(sys_annual_total, 2),
                    "diff": round(diff, 2),
                    "diff_pct": round(pct, 2),
                    "match": abs(diff) < max(bank_salary_total * 0.05, 500),  # 5% 鎴?500 鍏冧互鍐呰涓轰竴鑷?                    "txn_count": len(salary_txns),
                }

                if not result["bank_match"]["match"]:
                    result["warnings"].append(
                        f"鈿狅笍 閾惰娴佹按宸ヨ祫鏀嚭 {bank_salary_total:,.0f} 鍏?"
                        f"涓庣郴缁熷勾宸ヨ祫 {sys_annual_total:,.0f} 鍏冧笉涓€鑷达紙宸?{diff:+,.0f} 鍏冿紝{pct:+.1f}%锛?
                    )
                else:
                    result["warnings"].append(
                        f"鉁?閾惰娴佹按宸ヨ祫鏀嚭涓庣郴缁熷伐璧勪竴鑷达紙宸?{diff:+,.0f} 鍏冿級"
                    )
            else:
                result["warnings"].append("鈿狅笍 閾惰娴佹按涓湭璇嗗埆鍒板伐璧?濂栭噾绫绘敮鍑猴紝璇锋鏌ユ憳瑕佸叧閿瘝")
        else:
            result["warnings"].append("鈿狅笍 閾惰娴佹按鏂囦欢涓湭鎵惧埌鏀嚭閲戦鍒楋紝鏃犳硶鏍￠獙宸ヨ祫")

    # ============================================================
    #  鏍￠獙2锛氫釜绋庣敵鎶ヨ褰?vs 绯荤粺宸ヨ祫
    # ============================================================
    if tax_filing_df is not None and len(tax_filing_df) > 0:
        df_tax = tax_filing_df.copy()

        # 鍏煎鍒楀悕
        col_map2 = {}
        for col in df_tax.columns:
            cl = str(col).strip().lower()
            if "濮撳悕" in col or "name" in cl:
                col_map2[col] = "濮撳悕"
            if any(k in cl for k in ["绱鏀跺叆", "鏀跺叆棰?, "宸ヨ祫钖噾", "搴旂撼绋庢墍寰楅", "鏀跺叆"]):
                col_map2[col] = "绱鏀跺叆"
        df_tax = df_tax.rename(columns=col_map2)

        if "濮撳悕" in df_tax.columns and "绱鏀跺叆" in df_tax.columns:
            # 鎸夊憳宸ュ尮閰?            emp_map = {e.get("name", ""): e for e in employees}
            for _, row in df_tax.iterrows():
                name = str(row.get("濮撳悕", "")).strip()
                try:
                    tax_income = float(row.get("绱鏀跺叆", 0) or 0)
                except (ValueError, TypeError):
                    continue
                if name in emp_map:
                    sys_annual = emp_map[name].get("gross_salary", 0) * 12
                    diff = sys_annual - tax_income
                    result["tax_match"].append({
                        "name": name,
                        "sys_annual": round(sys_annual, 2),
                        "tax_filing_income": round(tax_income, 2),
                        "diff": round(diff, 2),
                        "match": abs(diff) < max(sys_annual * 0.01, 100),  # 1% 鎴?100 鍏冧互鍐?                    })
                    if abs(diff) >= max(sys_annual * 0.01, 100):
                        result["warnings"].append(
                            f"鈿狅笍 鍛樺伐銆寋name}銆嶄釜绋庣敵鎶ョ疮璁℃敹鍏?{tax_income:,.0f} 鍏?"
                            f"涓庣郴缁熷勾宸ヨ祫 {sys_annual:,.0f} 鍏冨樊 {diff:+,.0f} 鍏?
                        )

            if len(result["tax_match"]) == 0:
                result["warnings"].append("鈿狅笍 涓◣鐢虫姤璁板綍涓湭鎵惧埌鍖归厤鐨勫憳宸ュ鍚?)
        else:
            result["warnings"].append("鈿狅笍 涓◣鐢虫姤鏂囦欢涓湭鎵惧埌銆屽鍚嶃€嶅拰銆岀疮璁℃敹鍏ャ€嶅垪")

    # ============================================================
    #  鏍￠獙3锛氬勾鎶ュ伐璧勬€婚 vs 绯荤粺骞村伐璧勫悎璁?    # ============================================================
    if annual_total_salary and annual_total_salary > 0:
        diff = sys_annual_total - annual_total_salary
        pct = (diff / annual_total_salary * 100) if annual_total_salary > 0 else 0
        result["annual_match"] = {
            "annual_total_salary": round(annual_total_salary, 2),
            "sys_annual_total": round(sys_annual_total, 2),
            "diff": round(diff, 2),
            "diff_pct": round(pct, 2),
            "match": abs(diff) < max(annual_total_salary * 0.03, 1000),  # 3% 鎴?1000 鍏冧互鍐?        }
        if not result["annual_match"]["match"]:
            result["warnings"].append(
                f"鈿狅笍 骞存姤宸ヨ祫鎬婚 {annual_total_salary:,.0f} 鍏?"
                f"涓庣郴缁熷勾宸ヨ祫鍚堣 {sys_annual_total:,.0f} 鍏冧笉涓€鑷达紙宸?{diff:+,.0f} 鍏冿紝{pct:+.1f}%锛?
            )
        else:
            result["warnings"].append(
                f"鉁?骞存姤宸ヨ祫鎬婚涓庣郴缁熷伐璧勪竴鑷达紙宸?{diff:+,.0f} 鍏冿級"
            )

    return result
