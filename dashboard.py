import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import urllib.parse

# 1. 頁面基礎配置
st.set_page_config(
    page_title="反恐情報儀表板 CCTR",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自訂 CSS (終極穿透寫法：確保 KPI 數值與標題強制放大並改色)
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; }
    .stApp { background-color: #0b111e; color: #e0e6ed; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3, h4, h5, h6 { color: #58a6ff; }
    
    /* KPI 容器放大內邊距，容納更大的字體 */
    div[data-testid="metric-container"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    
    /* 1. KPI 標題 (Label) 放大 */
    [data-testid="stMetricLabel"] * { color: #8b949e !important; font-size: 1.1rem !important; }
    
    /* 2. KPI 數值 (Value) 放大 60% (約 3.5rem) 並強制改為紅色 */
    [data-testid="stMetricValue"] * { color: #ff3366 !important; font-size: 3.5rem !important; font-weight: bold !important; line-height: 1.2 !important; }
    
    header {visibility: hidden;}
    .marquee-container { background-color: #0d1117; border-bottom: 1px solid #30363d; padding: 8px; margin-bottom: 20px; font-size: 0.85rem; color: #ff7b72; display: flex; align-items: center; }
    .marquee-label { font-weight: bold; margin-right: 15px; color: #ff7b72; white-space: nowrap; }
    .cctr-table .details-row { display: none; }
    .cctr-table tr:has(.row-toggle:checked) + .details-row { display: table-row; }
    .cctr-table tr:has(.row-toggle:checked) { background-color: #1c2128 !important; }
    .cctr-table tr:has(.row-toggle:checked) .arrow { display: inline-block; transform: rotate(90deg); }
    .cctr-table .arrow { display: inline-block; transition: transform 0.2s; font-size: 0.75rem; margin-right: 5px; color: #58a6ff; }
    .cctr-table label { cursor: pointer; display: block; width: 100%; height: 100%; margin: 0; }
    .cctr-table tr.main-row:hover { background-color: #161b22; }
    
    /* 強制確保所有 Plotly 圖表的游標預設為箭頭 */
    .js-plotly-plot .plotly .cursor-crosshair { cursor: default !important; }
    .js-plotly-plot .plotly .nsewdrag { cursor: default !important; }
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=300000, key="cctr_auto_refresher")

# ==========================================
# 頂部 Header、Logo & 語言選擇器整合
# ==========================================
col_logo, col_title, col_live, col_lang = st.columns([1.5, 6, 2, 1.5])

with col_lang:
    selected_lang = st.selectbox("🌐", ["繁體中文", "English"], label_visibility="collapsed")
is_en = selected_lang == "English"

# 介面 UI 字典
t = {
    "title": "CCTR COUNTER-TERRORISM DASHBOARD" if is_en else "反恐情報儀表板 CCTR",
    "subtitle": "COUNTER-TERRORISM INTELLIGENCE DATABASE",
    "marquee": "🚨 MAJOR EVENTS" if is_en else "🚨 重大事件",
    "unknown_date": "Unknown Date" if is_en else "未知日期",
    "dead": "Dead" if is_en else "死",
    "filters": "FILTERS" if is_en else "篩選條件 / FILTERS",
    "year": "Year" if is_en else "年份",
    "domain": "Domain" if is_en else "攻擊領域",
    "country": "Country/Region" if is_en else "國家/地區",
    "attack_type": "Attack Type" if is_en else "攻擊類型",
    "all": "All" if is_en else "全部",
    "physical": "Physical" if is_en else "實體",
    "cyber": "Cyber" if is_en else "網絡",
    "search": "🔍 Search incidents, actors..." if is_en else "🔍 搜尋事件、行為者...",
    "kpi1": "Incidents on record" if is_en else "事件總數 / Incidents on record",
    "kpi2": "Total fatalities" if is_en else "死亡總數 / Total fatalities",
    "kpi3": "Impacted countries" if is_en else "波及國家/地區 / Impacted countries",
    "kpi4": "Identified actors" if is_en else "涉案行為者 / Identified actors",
    "kpi5": "Zero-fatality plots" if is_en else "零傷亡案件 / Zero-fatality plots",
    "trend": "YEARLY TREND" if is_en else "年度趨勢 / YEARLY TREND",
    "vectors": "ATTACK VECTORS" if is_en else "攻擊類型分佈 / ATTACK VECTORS",
    "top_countries": "TOP 10 RISK COUNTRIES" if is_en else "高風險國家/地區 TOP 10",
    "top_actors": "TOP ACTORS" if is_en else "活躍行為者 / TOP ACTORS",
    "unit_incidents": "incidents" if is_en else "件",
    "unit_dead": "dead" if is_en else "死",
    "log": "INCIDENT LOG" if is_en else "事件紀錄 / INCIDENT LOG",
    "log_sub": "Click any row to expand details" if is_en else "點擊列即可展開 / 收合詳情",
    "th_date": "Date ▼" if is_en else "日期 ▼",
    "th_country": "Country" if is_en else "國家/地區",
    "th_city": "City" if is_en else "城市",
    "th_domain": "Domain" if is_en else "領域",
    "th_type": "Attack Type" if is_en else "攻擊類型",
    "th_actor": "Actor" if is_en else "行為者",
    "th_fatality": "Fatalities" if is_en else "死亡",
    "no_summary": "No detailed summary available" if is_en else "無詳細摘要",
    "lvl_label": "Threat Level: " if is_en else "威脅等級: ",
    "lvl_zero": "Threat Preparedness" if is_en else "零傷亡 / Threat Preparedness",
    "lvl_lethal": "Lethal Attack" if is_en else "實質傷亡 / Lethal Attack",
    "source": "Source 🔗" if is_en else "情報來源 🔗",
    "no_source": "(No source)" if is_en else "(未提供來源)",
    "no_data": "No matching incidents found." if is_en else "目前條件下無相符事件紀錄。",
    "events_cnt": "Incidents" if is_en else "事件數",
    "fatalities_cnt": "Fatalities" if is_en else "死亡數"
}

# 渲染 Logo 圖片 (圖片尺寸跟隨區塊寬度放大 50%)
with col_logo:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception as e:
        st.markdown("<div style='font-size: 4.5rem; text-align: center; margin-top: -10px;'>🛡️</div>", unsafe_allow_html=True)

# 標題強制置中對齊
with col_title:
    st.markdown(f"<h2 style='margin-bottom: 0px; text-align: center;'>{t['title']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #8b949e; font-size: 0.8rem; margin-top: 0px; text-align: center;'>{t['subtitle']}</p>", unsafe_allow_html=True)
    
with col_live:
    st.markdown("<div style='text-align: right; color: #3fb950; font-weight: bold; margin-top: 15px;'>● LIVE MONITOR</div>", unsafe_allow_html=True)

# 資料正規化字典
TO_EN = {
    "美國": "United States", "usa": "United States", "us": "United States",
    "英國": "United Kingdom", "uk": "United Kingdom", "england": "United Kingdom",
    "索馬利亞": "Somalia", "奈及利亞": "Nigeria", "沙烏地阿拉伯": "Saudi Arabia",
    "中國": "China", "伊拉克": "Iraq", "全球": "Global", "區域水域": "Regional Waters",
    "巴基斯坦": "Pakistan", "德國": "Germany", "香港": "Hong Kong", "印尼": "Indonesia",
    "阿富汗": "Afghanistan", "以色列": "Israel", "比利時": "Belgium", "菲律賓": "Philippines",
    "法國": "France", "奧地利": "Austria", "伊朗": "Iran", "土耳其": "Turkey",
    "俄羅斯": "Russia", "烏克蘭": "Ukraine", "印度": "India", "多個地區": "Multiple",
    "國際 (聯合國)": "International (UN)", "國際(聯合國)": "International (UN)",
    "義大利": "Italy", "意大利": "Italy", "約旦空域": "Jordan Airspace",
    "馬來西亞": "Malaysia", "美國 / 全球": "USA / Global", "美國/全球": "USA / Global",
    "約旦河西岸": "West Bank", "西岸": "West Bank",
    "紐約": "New York", "倫敦": "London", "倫敦 / 曼徹斯特": "London / Manchester",
    "曼徹斯特": "Manchester", "費爾福德": "Fairford", "安曼 / 途中": "Amman / En Route",
    "摩德納": "Modena", "錫斯坦和俾路支斯坦": "Sistan and Baluchestan", "伊斯坦堡": "Istanbul",
    "華盛頓特區": "Washington, D.C.", "washington, d.c.": "Washington, D.C.",
    "下謝貝利州": "Lower Shabelle", "lower shabelle": "Lower Shabelle",
    "博爾諾州": "Borno State", "borno state": "Borno State",
    "艾卜哈 / 利雅德": "Abha / Riyadh", "abha / riyadh": "Abha / Riyadh",
    "沃斯堡": "Fort Worth", "fort worth": "Fort Worth",
    "巴格達": "Baghdad", "baghdad": "Baghdad",
    "米爾頓凱恩斯": "Milton Keynes", "milton keynes": "Milton Keynes",
    "霍爾木茲海峽": "Strait of Hormuz", "strait of hormuz": "Strait of Hormuz",
    "利雅德": "Riyadh", "riyadh": "Riyadh",
    "坦克與拉基馬瓦特": "Tank & Lakki Marwat", "tank & lakki marwat": "Tank & Lakki Marwat",
    "多個省份": "Multiple Provinces", "multiple provinces": "Multiple Provinces",
    "身份驗證繞過與關鍵基礎設施入侵": "Authentication Bypass & Critical Infrastructure Compromise",
    "針對性反恐行動": "Targeted Counter-Terrorism Operation",
    "武裝襲擊": "Armed Assault", "武裝襲擊/槍擊": "Armed Assault", "槍擊案": "Armed Assault",
    "無人機與導彈襲擊": "Drone & Missile Strike",
    "威脅準備/防範政策": "Threat Preparedness / Policy", "威脅準備 / 防範政策": "Threat Preparedness / Policy",
    "自殺式襲擊陰謀": "Suicide Attack Plot",
    "關鍵基礎設施網絡入侵": "Critical Infrastructure Cyber Intrusion",
    "ics 遠程代碼執行": "ICS Remote Code Execution", "ics remote code execution": "ICS Remote Code Execution",
    "恐怖組織活動": "Terrorist Group Activity",
    "海上恐怖襲擊": "Maritime Terrorist Attack",
    "基地破壞/恐怖陰謀": "Base Sabotage / Terror Plot",
    "爆炸攻擊": "Explosive Attack", "爆炸襲擊": "Explosive Attack", "炸彈襲擊": "Explosive Attack",
    "持刀襲擊": "Stabbing", "車輛衝撞": "Vehicle Ramming",
    "網絡/破壞滲透": "Cyber Intrusion", "網絡攻擊": "Cyber Attack",
    "未遂陰謀/活動": "Foiled Plot / Activity", "綁架": "Kidnapping",
}

# 資料顯示字典
TO_ZH = {
    "United States": "美國", "United Kingdom": "英國", "Somalia": "索馬利亞",
    "Nigeria": "奈及利亞", "Saudi Arabia": "沙烏地阿拉伯", "China": "中國", "Iraq": "伊拉克",
    "Global": "全球", "Regional Waters": "區域水域", "Pakistan": "巴基斯坦",
    "Germany": "德國", "Hong Kong": "香港", "Indonesia": "印尼", "Afghanistan": "阿富汗",
    "Israel": "以色列", "Belgium": "比利時", "Philippines": "菲律賓", "France": "法國",
    "Austria": "奧地利", "Iran": "伊朗", "Turkey": "土耳其", "Russia": "俄羅斯",
    "Ukraine": "烏克蘭", "India": "印度", "Multiple": "多個地區",
    "International (UN)": "國際 (聯合國)", "Italy": "義大利", "Jordan Airspace": "約旦空域",
    "Malaysia": "馬來西亞", "USA / Global": "美國 / 全球", "West Bank": "約旦河西岸",
    "New York": "紐約", "London": "倫敦", "London / Manchester": "倫敦 / 曼徹斯特",
    "Manchester": "曼徹斯特", "Fairford": "費爾福德", "Amman / En Route": "安曼 / 途中",
    "Modena": "摩德納", "Sistan and Baluchestan": "錫斯坦和俾路支斯坦", "Istanbul": "伊斯坦堡",
    "Washington, D.C.": "華盛頓特區", "Lower Shabelle": "下謝貝利州", "Borno State": "博爾諾州",
    "Abha / Riyadh": "艾卜哈 / 利雅德", "Fort Worth": "沃斯堡", "Baghdad": "巴格達",
    "Milton Keynes": "米爾頓凱恩斯", "Strait of Hormuz": "霍爾木茲海峽", "Riyadh": "利雅德",
    "Tank & Lakki Marwat": "坦克與拉基馬瓦特", "Multiple Provinces": "多個省份",
    "Authentication Bypass & Critical Infrastructure Compromise": "身份驗證繞過與基礎設施入侵",
    "Targeted Counter-Terrorism Operation": "針對性反恐行動", "Armed Assault": "武裝襲擊",
    "Drone & Missile Strike": "無人機與導彈襲擊", "Threat Preparedness / Policy": "防範準備與政策",
    "Suicide Attack Plot": "自殺式襲擊陰謀", "Critical Infrastructure Cyber Intrusion": "基礎設施網絡入侵",
    "ICS Remote Code Execution": "ICS 遠程代碼執行", "Terrorist Group Activity": "恐怖組織活動",
    "Maritime Terrorist Attack": "海上恐怖襲擊", "Base Sabotage / Terror Plot": "基地破壞 / 恐怖陰謀",
    "Explosive Attack": "爆炸攻擊", "Stabbing": "持刀襲擊", "Vehicle Ramming": "車輛衝撞",
    "Cyber Intrusion": "網絡/破壞滲透", "Cyber Attack": "網絡攻擊",
    "Foiled Plot / Activity": "未遂陰謀/活動", "Kidnapping": "綁架",
    "Armed Assault & Bombing": "武裝襲擊與爆炸",
    "Armed Assault & Bomb": "武裝襲擊與炸彈",
    "Armed Clashes / Counter-Terrorism Operation": "武裝衝突 / 反恐行動",
    "Armed Clashes / Counter-Terrorism": "武裝衝突 / 反恐",
    "Assassination / Stabbing": "暗殺 / 持刀襲擊",
    "Assassination / Terror Plot": "暗殺 / 恐怖陰謀",
    "Assassination Plot": "暗殺陰謀",
    "Attempted Hijacking / Terror Plot": "企圖劫機 / 恐怖陰謀",
    "Attempted Hijacking / Plot": "企圖劫機 / 陰謀",
    "Attempted Hijacking": "企圖劫機",
    "Attempted Sabotage / Terror Plot": "企圖破壞 / 恐怖陰謀",
    "Attempted Sabotage / Plot": "企圖破壞 / 陰謀",
    "Attempted Sabotage": "企圖破壞"
}

def normalize_en(val):
    if pd.isna(val): return val
    v = str(val).strip()
    v_lower = v.lower()
    if v_lower in TO_EN: return TO_EN[v_lower]
    for en_val in TO_ZH.keys():
        if v_lower == en_val.lower(): return en_val
    return v

def to_display(val, is_english):
    if pd.isna(val): return val
    en_val = normalize_en(val)
    return en_val if is_english else TO_ZH.get(en_val, en_val)

def get_domain(en_type):
    en_lower = str(en_type).lower()
    if any(k in en_lower for k in ["cyber", "ics", "authentication", "網絡", "網路", "bypass", "intrusion"]):
        return "Cyber"
    return "Physical"

# 2. 讀取並處理資料
@st.cache_data(ttl=60)
def load_data():
    SHEET_ID = "1wRQveuT6LsrasNzU_bNb1bW9MV0KVx2w3IsO6ZLdmVQ"
    SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
        col_mapping = {
            '日期': 'incident_date', '事件日期': 'incident_date', 'date': 'incident_date',
            '國家': 'country', '國家/地區': 'country', 'country/region': 'country',
            '城市': 'city', '行為者': 'actor', '涉案行為者': 'actor',
            '攻擊類型': 'attack_type', '死亡': 'fatalities', '死亡數': 'fatalities',
            '摘要': 'summary', '情報來源': 'url', '連結': 'url', 'link': 'url', 'source': 'url'
        }
        df = df.rename(columns=col_mapping)
        expected_cols = ['incident_date', 'country', 'city', 'actor', 'attack_type', 'fatalities', 'summary', 'url']
        for col in expected_cols:
            if col not in df.columns: df[col] = None
        df['incident_date'] = pd.to_datetime(df['incident_date'], errors='coerce')
        df['fatalities'] = pd.to_numeric(df['fatalities'], errors='coerce').fillna(0).astype(int)
        df['year'] = df['incident_date'].dt.year
        return df
    except Exception as e:
        return pd.DataFrame(columns=['incident_date', 'country', 'city', 'actor', 'attack_type', 'fatalities', 'summary', 'url', 'year'])

df_raw = load_data().copy()
if df_raw.empty:
    st.error("⚠️ 無法讀取資料，請檢查 Google Sheet ID 是否正確。")
    st.stop()

df_raw['country_en_standard'] = df_raw['country'].apply(normalize_en)
df_raw['type_en_standard'] = df_raw['attack_type'].apply(normalize_en)
df_raw['domain_en'] = df_raw['type_en_standard'].apply(get_domain)

df_raw['country'] = df_raw['country'].apply(lambda x: to_display(x, is_en))
df_raw['city'] = df_raw['city'].apply(lambda x: to_display(x, is_en))
df_raw['attack_type'] = df_raw['attack_type'].apply(lambda x: to_display(x, is_en))
df_raw['domain'] = df_raw['domain_en'].map({"Cyber": t['cyber'], "Physical": t['physical']})

latest_events = df_raw.sort_values(by='incident_date', ascending=False).head(5)
marquee_text = " • ".join([f"{row['incident_date'].strftime('%Y-%m-%d') if pd.notnull(row['incident_date']) else t['unknown_date']} {row['country']} {row['fatalities']} {t['dead']}" for index, row in latest_events.iterrows()])
st.markdown(f"<div class='marquee-container'><div class='marquee-label'>{t['marquee']}</div><marquee scrollamount='5'>{marquee_text}</marquee></div>", unsafe_allow_html=True)

# ==========================================
# 篩選條件區 
# ==========================================
st.markdown(f"<div style='color: #58a6ff; font-size: 0.9rem; font-weight: bold; margin-bottom: 10px;'>{t['filters']}</div>", unsafe_allow_html=True)
f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([2, 2, 2, 2, 3])

with f_col1:
    available_years = sorted(df_raw['year'].dropna().unique().astype(int).tolist(), reverse=True)
    selected_year = st.multiselect(t['year'], available_years, default=available_years)
with f_col2:
    selected_domain = st.selectbox(t['domain'], [t['all'], t['physical'], t['cyber']])
with f_col3:
    available_countries = [t['all']] + sorted(df_raw['country'].dropna().unique().tolist())
    selected_country = st.selectbox(t['country'], available_countries)
with f_col4:
    available_types = [t['all']] + sorted(df_raw['attack_type'].dropna().unique().tolist())
    selected_type = st.selectbox(t['attack_type'], available_types)
with f_col5:
    search_query = st.text_input(t['search'], "")

df_filtered = df_raw.copy()
if selected_year: df_filtered = df_filtered[df_filtered['year'].isin(selected_year)]
if selected_domain != t['all']: df_filtered = df_filtered[df_filtered['domain'] == selected_domain]
if selected_country != t['all']: df_filtered = df_filtered[df_filtered['country'] == selected_country]
if selected_type != t['all']: df_filtered = df_filtered[df_filtered['attack_type'] == selected_type]
if search_query:
    search_mask = (
        df_filtered['summary'].astype(str).str.contains(search_query, case=False, na=False) |
        df_filtered['actor'].astype(str).str.contains(search_query, case=False, na=False) |
        df_filtered['city'].astype(str).str.contains(search_query, case=False, na=False) |
        df_filtered['country'].astype(str).str.contains(search_query, case=False, na=False)
    )
    df_filtered = df_filtered[search_mask]

# ==========================================
# KPI 區塊
# ==========================================
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric(t['kpi1'], len(df_filtered))
kpi2.metric(t['kpi2'], int(df_filtered['fatalities'].sum()))
kpi3.metric(t['kpi3'], df_filtered['country'].nunique())
kpi4.metric(t['kpi4'], df_filtered['actor'].nunique())
kpi5.metric(t['kpi5'], len(df_filtered[df_filtered['fatalities'] == 0]))

st.write("") 

# ==========================================
# 圖表區塊 (趨勢、分佈、國家、行為者)
# ==========================================
c_row1_col1, c_row1_col2 = st.columns([5, 5])
with c_row1_col1:
    st.markdown(f"<div style='color: #58a6ff; font-size: 0.9rem; font-weight: bold;'>{t['trend']}</div>", unsafe_allow_html=True)
    if not df_filtered.empty and not df_filtered['year'].dropna().empty:
        trend_df = df_filtered.groupby('year').agg(事件數=('year', 'count'), 死亡數=('fatalities', 'sum')).reset_index()
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(x=trend_df['year'], y=trend_df['事件數'], name=t['events_cnt'], marker_color='#00f0ff'))
        fig_trend.add_trace(go.Scatter(x=trend_df['year'], y=trend_df['死亡數'], name=t['fatalities_cnt'], yaxis='y2', mode='lines+markers', line=dict(color='#ff3366', width=3)))
        
        fig_trend.update_layout(
            dragmode=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#8b949e'), 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
            yaxis=dict(title=t['events_cnt'], showgrid=False, tickformat='d'), 
            yaxis2=dict(title=t['fatalities_cnt'], overlaying='y', side='right', showgrid=False, tickformat='d'), 
            xaxis=dict(showgrid=False, type='category'), margin=dict(l=0, r=0, t=30, b=0), height=380
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

with c_row1_col2:
    st.markdown(f"<div style='color: #58a6ff; font-size: 0.9rem; font-weight: bold;'>{t['vectors']}</div>", unsafe_allow_html=True)
    if not df_filtered.empty and not df_filtered['attack_type'].dropna().empty:
        type_counts = df_filtered['attack_type'].value_counts().reset_index()
        type_counts.columns = ['攻擊類型', '次數']
        fig_pie = px.pie(type_counts, values='次數', names='攻擊類型', hole=0.6, color_discrete_sequence=px.colors.qualitative.Set1)
        fig_pie.update_traces(textposition='inside', textinfo='percent')
        
        fig_pie.update_layout(
            dragmode=False,
            annotations=[dict(text=f"<span style='font-size: 28px; color: white; font-weight:bold;'>{len(df_filtered)}</span><br><span style='font-size: 13px; color: #8b949e;'>{t['events_cnt']}</span>", x=0.5, y=0.5, font_size=20, showarrow=False)], 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#8b949e'), showlegend=False, margin=dict(l=20, r=20, t=20, b=20), height=380
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

st.write("") 
c_row2_col1, c_row2_col2 = st.columns([5, 5])
with c_row2_col1:
    st.markdown(f"<div style='color: #58a6ff; font-size: 0.9rem; font-weight: bold; margin-bottom: 10px;'>{t['top_countries']}</div>", unsafe_allow_html=True)
    if not df_filtered.empty:
        country_counts = df_filtered['country'].value_counts().head(10).reset_index()
        country_counts.columns = ['國家', '事件數']
        country_counts = country_counts.sort_values(by='事件數', ascending=True)
        fig_bar = px.bar(country_counts, x='事件數', y='國家', orientation='h', color_discrete_sequence=['#00f0ff'])
        
        fig_bar.update_layout(
            dragmode=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#e0e6ed', size=12),
            xaxis=dict(showgrid=True, gridcolor='#30363d', title="", tickformat='d'), yaxis=dict(showgrid=False, title=""),
            margin=dict(l=0, r=0, t=10, b=0), height=320
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

with c_row2_col2:
    st.markdown(f"<div style='color: #58a6ff; font-size: 0.9rem; font-weight: bold; margin-bottom: 10px;'>{t['top_actors']}</div>", unsafe_allow_html=True)
    if not df_filtered.empty:
        actor_df = df_filtered.groupby('actor').agg(事件數=('actor', 'count'), 死亡數=('fatalities', 'sum')).sort_values(by='事件數', ascending=False).head(8).reset_index()
        max_events = actor_df['事件數'].max()
        actors_html = "<div style='display: flex; flex-direction: column; gap: 14px; padding-top: 5px;'>"
        for i, row in actor_df.iterrows():
            actor_name = str(row['actor']).strip()
            if actor_name in ['nan', 'None', '']: actor_name = "Unknown Actors"
            ev_count = row['事件數']
            dt_count = row['死亡數']
            pct = int((ev_count / max_events) * 100) if max_events > 0 else 0
            actors_html += f"<div><div style='display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 5px;'><span style='color: #e0e6ed; font-weight: bold;'><span style='color: #8b949e; margin-right: 8px;'>0{i+1}</span> {actor_name}</span><span style='color: #ff7b72;'>{ev_count} {t['unit_incidents']} • {dt_count} {t['unit_dead']}</span></div><div style='width: 100%; background-color: #21262d; height: 3px; border-radius: 2px;'><div style='width: {pct}%; background-color: #00f0ff; height: 100%; border-radius: 2px;'></div></div></div>"
        actors_html += "</div>"
        st.markdown(actors_html, unsafe_allow_html=True)

st.markdown("<hr style='border-color: #30363d; margin-top: 30px; margin-bottom: 30px;'>", unsafe_allow_html=True)

# ==========================================
# 下半部：高階互動式 HTML 表格 
# ==========================================
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom: 15px;'>
    <div style='color: #58a6ff; font-size: 0.9rem; font-weight: bold;'>{t['log']}</div>
    <div style='color: #8b949e; font-size: 0.8rem;'>{t['log_sub']}</div>
</div>
""", unsafe_allow_html=True)

if not df_filtered.empty:
    display_df = df_filtered.copy().sort_values(by='incident_date', ascending=False)
    
    table_html = '<table class="cctr-table" style="width: 100%; border-collapse: collapse; font-size: 0.85rem; color: #e0e6ed; table-layout: fixed;">'
    table_html += '<thead><tr style="background-color: #0d1117; color: #8b949e; border-bottom: 2px solid #30363d; text-align: left;">'
    table_html += '<th style="padding: 12px 5px; width: 5%;">#</th>'
    table_html += f'<th style="padding: 12px 10px; width: 11%;">{t["th_date"]}</th>'
    table_html += f'<th style="padding: 12px 10px; width: 12%;">{t["th_country"]}</th>'
    table_html += f'<th style="padding: 12px 10px; width: 12%;">{t["th_city"]}</th>'
    table_html += f'<th style="padding: 12px 10px; width: 10%;">{t["th_domain"]}</th>'
    table_html += f'<th style="padding: 12px 10px; width: 18%;">{t["th_type"]}</th>'
    table_html += f'<th style="padding: 12px 10px; width: 24%;">{t["th_actor"]}</th>'
    table_html += f'<th style="padding: 12px 10px; width: 8%; text-align: center;">{t["th_fatality"]}</th>'
    table_html += '</tr></thead><tbody>'
    
    total_records = len(display_df)
    
    for i, (idx, row) in enumerate(display_df.iterrows()):
        row_num = total_records - i
        
        date_str = row['incident_date'].strftime('%Y-%m-%d') if pd.notnull(row['incident_date']) else '-'
        country = str(row.get('country', '-'))
        city = str(row.get('city', '-'))
        domain = str(row.get('domain', '-'))
        domain_en = str(row.get('domain_en', 'Physical'))
        actor = str(row.get('actor', '-')).replace('nan', '-')
        attack_type = str(row.get('attack_type', '-'))
        summary = str(row.get('summary', t['no_summary'])).replace('nan', t['no_summary'])
        
        fatality_val = row['fatalities']
        try:
            f_num = int(fatality_val)
            f_color = "#3fb950" if f_num == 0 else "#ff7b72"
        except:
            f_color = "#8b949e"

        threat_level = t['lvl_zero'] if f_color == '#3fb950' else t['lvl_lethal']

        url_val = str(row.get('url', ''))
        if url_val and url_val.lower() not in ['nan', 'none', '']:
            source_link_html = f'<a href="{url_val}" target="_blank" style="color: #3fb950; text-decoration: none; font-size: 0.85rem; font-weight: bold;">{t["source"]}</a>'
        else:
            source_link_html = f'<span style="color: #8b949e; font-size: 0.85rem;">{t["no_source"]}</span>'

        dom_color = "#1f6feb" if domain_en == "Cyber" else "#bf3989"
        domain_badge = f"<span style='background-color: {dom_color}; color: #ffffff; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;'>{domain}</span>"

        table_html += f'<tr class="main-row" style="border-bottom: 1px solid #21262d; background-color: #0d1117; transition: background-color 0.2s;">'
        table_html += f'<td style="padding: 12px 5px; color: #8b949e;"><input type="checkbox" id="toggle-{idx}" class="row-toggle" style="display: none;"><label for="toggle-{idx}"><span class="arrow">▶</span> {row_num}</label></td>'
        table_html += f'<td style="padding: 12px 10px; color: #58a6ff;"><label for="toggle-{idx}">{date_str}</label></td>'
        table_html += f'<td style="padding: 12px 10px;"><label for="toggle-{idx}">{country}</label></td>'
        table_html += f'<td style="padding: 12px 10px; color: #8b949e;"><label for="toggle-{idx}">{city}</label></td>'
        table_html += f'<td style="padding: 12px 10px;"><label for="toggle-{idx}">{domain_badge}</label></td>'
        table_html += f'<td style="padding: 12px 10px;"><label for="toggle-{idx}"><span style="color: #d2a8ff; border: 1px solid #30363d; border-radius: 4px; padding: 2px 6px; font-size: 0.75rem;">{attack_type}</span></label></td>'
        table_html += f'<td style="padding: 12px 10px;"><label for="toggle-{idx}">{actor}</label></td>'
        table_html += f'<td style="padding: 12px 10px; color: {f_color}; font-weight: bold; text-align: center;"><label for="toggle-{idx}">{fatality_val}</label></td>'
        table_html += f'</tr>'
        
        table_html += f'<tr class="details-row" style="background-color: #0b111e;"><td colspan="8" style="padding: 0; border: none;">'
        table_html += f'<div style="padding: 15px 20px; background-color: #161b22; border-left: 3px solid {f_color}; margin: 10px 15px 15px 15px; border-radius: 0 4px 4px 0;">'
        table_html += f'<div style="color: #8b949e; font-size: 0.75rem; margin-bottom: 8px;">{t["lvl_label"]}{threat_level}</div>'
        table_html += f'<div style="color: #e0e6ed; font-size: 0.9rem; line-height: 1.6; margin-bottom: 12px;">{summary}</div>'
        table_html += f'{source_link_html}'
        table_html += f'</div></td></tr>'
        
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.info(t["no_data"])
