import streamlit as st
import pandas as pd

# --- ページ設定（スマホ対応） ---
st.set_page_config(page_title="My Tax Manager", layout="wide")

# --- サイドバー：設定メニュー ---
st.sidebar.header("🔧 設定・シミュレーション")

# 給与入力（スライダーで直感的に）
monthly_salary = st.sidebar.number_input("基本給与（万円）", min_value=15, max_value=200, value=40)
bonus = st.sidebar.number_input("ボーナス（年間・万円）", min_value=0, max_value=500, value=100)

# 控除シミュレーション
st.sidebar.subheader("節税アクション")
dc_contribution = st.sidebar.slider("iDeCo/DC 掛金（円/月）", 0, 55000, 15000, step=1000)
furusato = st.sidebar.slider("ふるさと納税（円/年）", 0, 200000, 30000, step=1000)

# --- 計算ロジック（簡易版） ---
# ※あくまで動作確認用の概算です。後ほど精密化します。
annual_income = (monthly_salary * 12) + bonus
social_insurance = annual_income * 0.15  # 社会保険料（約15%と仮定）
income_deduction = dc_contribution * 12  # 所得控除
taxable_income = annual_income - social_insurance - income_deduction - 480000 # 基礎控除
if taxable_income < 0: taxable_income = 0

# 所得税・住民税（概算）
income_tax = taxable_income * 0.10 # 仮の税率
resident_tax = taxable_income * 0.10

# 手取り
net_income = annual_income - social_insurance - income_tax - resident_tax

# --- メイン画面：スマホで見やすいダッシュボード ---
st.title("💰 My Tax Manager")
st.markdown("### 今年の見込み")

# 重要な数字を大きく表示
col1, col2 = st.columns(2)
col1.metric("額面年収", f"{annual_income/10000:.1f}万円")
col2.metric("手取り予測", f"{net_income/10000:.1f}万円", delta_color="normal")

st.divider()

# グラフで可視化
st.markdown("##### 💸 給与から引かれるもの")
data = {
    "項目": ["手取り", "社会保険料", "所得税", "住民税"],
    "金額": [net_income, social_insurance, income_tax, resident_tax]
}
df = pd.DataFrame(data)
st.bar_chart(df.set_index("項目"), color=["#4CAF50"]) # 緑色

# アラート機能
st.info(f"💡 **節税効果:** iDeCoとふるさと納税で、今のところ約**{(dc_contribution*12*0.2 + 2000):,}円**の税金を取り戻しています。")

if resident_tax > 300000:
    st.warning("⚠️ **注意:** 来年の住民税が高額になる予測です。現金を確保してください。")
