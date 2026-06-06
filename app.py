import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="超市銷售儀表板",
    page_icon="🛒",
    layout="wide"
)

# ── 登入邏輯 ───────────────────────────────────────────────────────────────
USERS = {
    st.secrets["user1_username"]: st.secrets["user1_password"],
    st.secrets["user2_username"]: st.secrets["user2_password"],
    st.secrets["user3_username"]: st.secrets["user3_password"],
}
NAMES = {
    st.secrets["user1_username"]: st.secrets["user1_name"],
    st.secrets["user2_username"]: st.secrets["user2_name"],
    st.secrets["user3_username"]: st.secrets["user3_name"],
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🛒 超市銷售儀表板")
    st.subheader("請登入")
    username = st.text_input("帳號")
    password = st.text_input("密碼", type="password")
    if st.button("登入"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("帳號或密碼錯誤")
    st.stop()

# ── 登出 ───────────────────────────────────────────────────────────────────
name = NAMES.get(st.session_state.username, st.session_state.username)
with st.sidebar:
    st.write(f"登入者：**{name}**")
    if st.button("登出"):
        st.session_state.logged_in = False
        st.rerun()

# ── 讀取資料 ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("supermarket_sales.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    return df

df = load_data()

# ── 側邊欄篩選器 ──────────────────────────────────────────────────────────
st.sidebar.title("篩選條件")
branches = st.sidebar.multiselect(
    "分店", options=sorted(df["Branch"].unique()),
    default=sorted(df["Branch"].unique())
)
product_lines = st.sidebar.multiselect(
    "商品類別", options=sorted(df["Product line"].unique()),
    default=sorted(df["Product line"].unique())
)
date_range = st.sidebar.date_input(
    "日期範圍",
    value=(df["Date"].min(), df["Date"].max()),
    min_value=df["Date"].min(),
    max_value=df["Date"].max()
)

filtered = df[
    df["Branch"].isin(branches) &
    df["Product line"].isin(product_lines) &
    (df["Date"] >= pd.Timestamp(date_range[0])) &
    (df["Date"] <= pd.Timestamp(date_range[1]))
]

# ── 標題 ──────────────────────────────────────────────────────────────────
st.title("🛒 超市銷售儀表板")
st.caption(f"已篩選 {len(filtered):,} 筆 / 共 {len(df):,} 筆")

# ── KPI ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("總營收", f"${filtered['Total'].sum():,.0f}")
k2.metric("總毛利", f"${filtered['gross income'].sum():,.0f}")
k3.metric("交易筆數", f"{len(filtered):,}")
k4.metric("平均評分", f"{filtered['Rating'].mean():.2f} / 10")

st.divider()

# ── 圖表第一排 ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("各分店營收")
    branch_rev = filtered.groupby("Branch")["Total"].sum().reset_index().sort_values("Total", ascending=False)
    fig = px.bar(branch_rev, x="Branch", y="Total", color="Branch",
                 text_auto=".2s", color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(showlegend=False, xaxis_title="分店", yaxis_title="營收 ($)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("商品類別銷售佔比")
    cat_rev = filtered.groupby("Product line")["Total"].sum().reset_index()
    fig = px.pie(cat_rev, names="Product line", values="Total",
                 color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ── 圖表第二排 ────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)
with col3:
    st.subheader("每週營收趨勢")
    weekly = filtered.groupby("Week")["Total"].sum().reset_index()
    fig = px.line(weekly, x="Week", y="Total", markers=True,
                  color_discrete_sequence=["#636EFA"])
    fig.update_layout(xaxis_title="週", yaxis_title="營收 ($)")
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("付款方式分佈")
    pay = filtered["Payment"].value_counts().reset_index()
    pay.columns = ["付款方式", "筆數"]
    fig = px.bar(pay, x="付款方式", y="筆數", color="付款方式",
                 text_auto=True, color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ── 圖表第三排 ────────────────────────────────────────────────────────────
col5, col6 = st.columns(2)
with col5:
    st.subheader("顧客評分分佈")
    fig = px.histogram(filtered, x="Rating", nbins=20,
                       color_discrete_sequence=["#EF553B"])
    fig.update_layout(xaxis_title="評分", yaxis_title="筆數", bargap=0.05)
    st.plotly_chart(fig, use_container_width=True)

with col6:
    st.subheader("各類別平均評分")
    cat_rating = filtered.groupby("Product line")["Rating"].mean().reset_index().sort_values("Rating")
    fig = px.bar(cat_rating, x="Rating", y="Product line", orientation="h",
                 text_auto=".2f", color_discrete_sequence=["#00CC96"])
    fig.update_layout(xaxis_title="平均評分", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# ── 原始資料 ──────────────────────────────────────────────────────────────
with st.expander("查看原始資料"):
    st.dataframe(filtered, use_container_width=True, height=300)
    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下載篩選資料 CSV", csv, "filtered_sales.csv", "text/csv")
