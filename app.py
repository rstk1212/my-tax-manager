import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="My Perfect Tax Manager", layout="wide")

# --- タイトル ---
st.title("🛡️ My Perfect Tax Manager")
st.markdown("あなたの資産を守り、未来の税金を予測する戦略的ダッシュボード")

# ==========================================
# 1. 左サイドバー：完璧な属性設定 (Profile)
# ==========================================
st.sidebar.header("👤 あなたの税務属性")

# --- 基本収入 ---
with st.sidebar.expander("💰 収入情報", expanded=True):
    monthly_salary = st.number_input("月額給与（額面・万円）", 20, 200, 40)
    bonus_annual = st.number_input("年間ボーナス（額面・万円）", 0, 1000, 100)
    overtime_avg = st.number_input("月平均残業代（万円）", 0, 50, 5)
    
    # 年収計算
    total_salary_monthly = monthly_salary + overtime_avg
    annual_income_raw = (total_salary_monthly * 12) + bonus_annual

# --- 家族・扶養 ---
with st.sidebar.expander("👨‍👩‍👧‍👦 家族・扶養", expanded=False):
    has_spouse = st.checkbox("配偶者あり", value=True)
    spouse_income = 0
    if has_spouse:
        spouse_income = st.number_input("配偶者の年収（万円）", 0, 1000, 0)
    
    num_dependents_u16 = st.number_input("扶養親族 (16歳未満)", 0, 5, 1)
    num_dependents_general = st.number_input("扶養親族 (一般:16-18, 23-69)", 0, 5, 0)
    num_dependents_specific = st.number_input("特定扶養親族 (19-22歳)", 0, 5, 0)

# --- 社会保険・控除 ---
with st.sidebar.expander("🛡️ 保険・iDeCo・住宅ローン", expanded=False):
    # 社会保険料率（東京都・協会けんぽR6目安）
    st.caption("社会保険設定")
    age = st.number_input("年齢", 20, 70, 35)
    
    st.caption("節税アクション")
    dc_monthly = st.number_input("iDeCo/企業型DC 掛金（円/月）", 0, 55000, 20000, step=1000)
    furusato_annual = st.number_input("ふるさと納税 年間寄付額（円）", 0, 500000, 50000, step=1000)
    
    st.caption("民間保険控除")
    life_insurance_pay = st.number_input("一般生命保険料（年間・円）", 0, 200000, 80000)
    medical_insurance_pay = st.number_input("介護医療保険料（年間・円）", 0, 200000, 40000)
    earthquake_insurance_pay = st.number_input("地震保険料（年間・円）", 0, 50000, 15000)

    st.caption("🏠 住宅ローン控除設定")
    has_loan = st.checkbox("住宅ローンあり", value=True)
    loan_deduction = 0
    if has_loan:
        loan_balance = st.number_input("年末ローン残高（万円）", 0, 10000, 5000)
        house_type = st.selectbox("住宅の種類", ["ZEH水準・省エネ", "長期優良・低炭素", "一般（2023以前入居）"])
        # 簡易判定ロジック（実際は入居年でさらに分岐しますが今回はZEH重視）
        limit_table = {"ZEH水準・省エネ": 4500, "長期優良・低炭素": 5000, "一般（2023以前入居）": 3000}
        limit = limit_table[house_type]
        calc_base = min(loan_balance, limit)
        loan_deduction = calc_base * 10000 * 0.007 # 0.7%

# ==========================================
# 2. 計算エンジン (Tax Logic)
# ==========================================

# A. 給与所得控除の計算
def calc_salary_deduction(income_man):
    income = income_man * 10000
    if income <= 1625000: return 550000
    elif income <= 1800000: return income * 0.4 - 100000
    elif income <= 3600000: return income * 0.3 + 80000
    elif income <= 6600000: return income * 0.2 + 440000
    elif income <= 8500000: return income * 0.1 + 1100000
    else: return 1950000

salary_deduction = calc_salary_deduction(annual_income_raw / 10000)
salary_income = (annual_income_raw * 10000) - salary_deduction
if salary_income < 0: salary_income = 0

# B. 社会保険料計算（概算）
# 40歳以上は介護保険料加算
rate_health = 0.0998 # 協会けんぽ東京
rate_pension = 0.183
rate_kaigo = 0.0182 if age >= 40 else 0
rate_employ = 0.006 # 雇用保険（本人負担）

# 標準報酬月額を用いた簡易計算
shaho_total = (annual_income_raw * 10000) * ((rate_health + rate_pension + rate_kaigo)/2 + rate_employ)

# C. 各種所得控除
# 基礎控除
basic_deduction = 480000 
# 配偶者控除（簡易：本人の所得1000万以下前提）
spouse_deduction = 380000 if (has_spouse and spouse_income <= 103) else 0
# 扶養控除
dep_deduction = (num_dependents_general * 380000) + (num_dependents_specific * 630000)
# 社会保険料控除
ins_deduction = shaho_total
# iDeCo
ideco_deduction = dc_monthly * 12
# 生命保険料控除（新制度計算式・簡易版）
def calc_life_ins_deduction(amount):
    if amount <= 20000: return amount
    elif amount <= 40000: return amount * 0.5 + 10000
    elif amount <= 80000: return amount * 0.25 + 20000
    else: return 40000
life_ins_deduction_total = calc_life_ins_deduction(life_insurance_pay) + calc_life_ins_deduction(medical_insurance_pay)
# 地震保険
earthquake_deduction = min(earthquake_insurance_pay, 50000)

total_income_deduction = (basic_deduction + spouse_deduction + dep_deduction + 
                          ins_deduction + ideco_deduction + life_ins_deduction_total + earthquake_deduction)

# 課税所得
taxable_income = salary_income - total_income_deduction
if taxable_income < 0: taxable_income = 0

# D. 所得税計算（累進課税）
def calc_income_tax(taxable):
    if taxable <= 1950000: return taxable * 0.05
    elif taxable <= 3300000: return taxable * 0.10 - 97500
    elif taxable <= 6950000: return taxable * 0.20 - 427500
    elif taxable <= 9000000: return taxable * 0.23 - 636000
    elif taxable <= 18000000: return taxable * 0.33 - 1536000
    else: return taxable * 0.40 - 2796000

income_tax_raw = calc_income_tax(taxable_income)
# 住宅ローン控除（所得税から引く）
final_income_tax = max(0, income_tax_raw - loan_deduction)

# E. 住民税計算（概算：一律10% + 均等割5000円）
# ふるさと納税控除（自己負担2000円を除く全額が引かれると仮定）
furusato_deduction = max(0, furusato_annual - 2000)
resident_tax_raw = (taxable_income * 0.10) + 5000
# 住宅ローン控除の住民税充当（所得税から引ききれない分、上限9.75万）
loan_deduction_resident = min(max(0, loan_deduction - income_tax_raw), 97500)

final_resident_tax = max(0, resident_tax_raw - furusato_deduction - loan_deduction_resident)

# F. 手取り
net_income = (annual_income_raw * 10000) - shaho_total - final_income_tax - final_resident_tax

# ==========================================
# 3. ダッシュボード表示 (Dashboard)
# ==========================================

# 上部サマリ
col1, col2, col3 = st.columns(3)
col1.metric("額面年収", f"{annual_income_raw/10000:,.1f} 万円")
col2.metric("手取り予測", f"{net_income/10000:,.1f} 万円", f"税負担率 {((1 - net_income/(annual_income_raw*10000))*100):.1f}%")
col3.metric("来年の住民税（月額目安）", f"{final_resident_tax/12:,.0f} 円", help="来年6月から給与天引きされる額です")

st.divider()

# --- アラートセクション ---
st.subheader("⚠️ 税務アラート & アドバイス")

alerts = []
# 1. 住民税アラート
if final_resident_tax > 300000:
    alerts.append(f"🔴 **住民税注意:** 来年の住民税が年間{final_resident_tax:,.0f}円になります。月々の手取り減少に備えてください。")
# 2. 社会保険の壁
if 4 <= pd.Timestamp.now().month <= 6:
    alerts.append("🟠 **4-6月の残業注意:** 現在は社会保険料算定期間です。今の残業代が9月からの手取りを減らします。")
# 3. 住宅ローン控除
if loan_deduction > 0:
    val = min(loan_deduction, income_tax_raw + 97500)
    alerts.append(f"🟢 **住宅ローン恩恵:** 年間最大**{val/10000:.1f}万円**の税金がチャラになっています（所得税＋住民税）。")
# 4. ふるさと納税
limit_furusato = (resident_tax_raw * 0.2) + 2000 # 簡易計算（本来はもっと複雑）
if furusato_annual > limit_furusato * 1.5: # ざっくり上限超え判定
    alerts.append("🔴 **ふるさと納税:** 寄付額が控除上限を超えている可能性があります。")

for alert in alerts:
    st.info(alert)

# --- グラフ：手取りの滝（ウォーターフォール） ---
st.subheader("💸 手取りへの道のり (Waterfall)")

fig = go.Figure(go.Waterfall(
    name = "20", orientation = "v",
    measure = ["relative", "relative", "relative", "relative", "total"],
    x = ["額面年収", "社会保険料", "所得税", "住民税", "手取り"],
    textposition = "outside",
    text = [f"{annual_income_raw/10000:.0f}", f"-{shaho_total/10000:.1f}", f"-{final_income_tax/10000:.1f}", f"-{final_resident_tax/10000:.1f}", f"{net_income/10000:.1f}"],
    y = [annual_income_raw/10000, -shaho_total/10000, -final_income_tax/10000, -final_resident_tax/10000, net_income/10000],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
))

fig.update_layout(title = "年収から手取りまでの内訳（単位：万円）", showlegend = False)
st.plotly_chart(fig, use_container_width=True)

# --- 控除の恩恵可視化 ---
st.subheader("🛡️ 税金を防いだ盾（控除の恩恵）")
tax_saved_data = {
    "項目": ["基礎控除", "社会保険料控除", "iDeCo控除", "扶養・配偶者控除", "住宅ローン減税"],
    "金額(万円)": [
        basic_deduction/10000, 
        ins_deduction/10000, 
        ideco_deduction/10000, 
        (spouse_deduction+dep_deduction)/10000, 
        min(loan_deduction, income_tax_raw+loan_deduction_resident)/10000 # 税額控除ベース
    ]
}
st.bar_chart(pd.DataFrame(tax_saved_data).set_index("項目"))
st.caption("※グラフが高いほど、課税対象を減らしてくれています（住宅ローンは直接税金を減らしています）")
