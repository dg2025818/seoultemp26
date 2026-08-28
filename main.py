import csv
from datetime import datetime
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 기온 순위 검색기",
    page_icon="🌡️",
    layout="centered"
)

# 커스텀 CSS 적용 (깔끔하고 예쁜 UI 스타일링)
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    .highlight-rank {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ff4b4b;
        margin: 0.5rem 0;
    }
    .stat-label {
        font-size: 0.95rem;
        color: #555;
    }
    .stat-value {
        font-size: 1.4rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data(file_path):
    """표준 csv 라이브러리를 사용하여 seoul.csv 데이터를 로드하고 파싱"""
    records = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # 날짜 파싱 (YYYY-MM-DD)
                date_str = row['날짜'].strip()
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                # 기온 데이터 파싱
                avg_temp = float(row['평균기온(℃)']) if row['평균기온(℃)'] else None
                min_temp = float(row['최저기온(℃)']) if row['최저기온(℃)'] else None
                max_temp = float(row['최고기온(℃)']) if row['최고기온(℃)'] else None

                if avg_temp is not None:
                    records.append({
                        'date': date_obj,
                        'avg_temp': avg_temp,
                        'min_temp': min_temp,
                        'max_temp': max_temp
                    })
            except (ValueError, KeyError):
                # 데이터 결측치 또는 헤더 오류 처리
                continue
    return records


# 데이터 불러오기
try:
    data = load_data('seoul.csv')
except FileNotFoundError:
    st.error("`seoul.csv` 파일을 찾을 수 없습니다. 깃허브 저장소에 파일이 올바르게 업로드되었는지 확인해주세요.")
    st.stop()

if not data:
    st.error("데이터를 불러올 수 없거나 형식이 올바르지 않습니다.")
    st.stop()

# 데이터셋 전체 기간 정보 추출
min_date = min(r['date'] for r in data)
max_date = max(r['date'] for r in data)
total_days = len(data)

# 앱 타이틀 영역
st.markdown("<h1 class='main-title'>🌡️ 서울 역대 기온 순위 조회</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>달력에서 원하는 날짜를 선택하여 해당 날짜의 기온 순위를 확인해보세요.</p>", unsafe_allow_html=True)

# sidebar: 선택 방식 및 옵션
with st.sidebar:
    st.header("⚙️ 검색 설정")
    metric_type = st.radio(
        "기준 기온 선택",
        ["평균기온", "최고기온", "최저기온"],
        help="순위를 매길 기온 항목을 선택합니다."
    )
    
    st.markdown("---")
    st.caption(f"📅 **데이터 수집 기간**\n{min_date} ~ {max_date}")
    st.caption(f"📊 **총 데이터 수**: {total_days:,}일")

# 기온 타입 매핑
metric_key = {
    "평균기온": "avg_temp",
    "최고기온": "max_temp",
    "최저기온": "min_temp"
}[metric_type]

# 메인 화면: 기간 선택 영역
st.subheader("📅 기간 선택")
selected_dates = st.date_input(
    "조회할 단일 날짜 또는 기간을 지정하세요",
    value=(max_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="YYYY-MM-DD"
)

# 날짜 선택 검증
start_date, end_date = None, None
if isinstance(selected_dates, tuple) or isinstance(selected_dates, list):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
else:
    start_date = end_date = selected_dates

if start_date and end_date:
    # 해당 기간 동안의 데이터 필터링
    filtered_records = [r for r in data if start_date <= r['date'] <= end_date]
    
    if not filtered_records:
        st.warning("선택한 기간에 해당하는 데이터가 없습니다.")
    else:
        # 선택 기간 내 통계 산출
        temps = [r[metric_key] for r in filtered_records if r[metric_key] is not None]
        
        if not temps:
            st.warning("선택한 기간의 기온 데이터가 유효하지 않습니다.")
        else:
            period_avg = sum(temps) / len(temps)
            period_max = max(temps)
            period_min = min(temps)
            
            # 전체 역대 데이터 정렬 (내림차순, 오름차순)
            all_temps = [r[metric_key] for r in data if r[metric_key] is not None]
            all_temps_desc = sorted(all_temps, reverse=True)
            all_temps_asc = sorted(all_temps)
            
            # 높은 순위 (더웠던 순), 낮은 순위 (추웠던 순) 계산
            rank_high = sum(1 for t in all_temps_desc if t > period_avg) + 1
            rank_low = sum(1 for t in all_temps_asc if t < period_avg) + 1
            
            top_percent_high = (rank_high / len(all_temps)) * 100
            top_percent_low = (rank_low / len(all_temps)) * 100

            st.markdown("---")
            st.subheader("📊 순위 분석 결과")
            
            # 기간 표시
            if start_date == end_date:
                st.markdown(f"**선택일:** `{start_date}`")
            else:
                st.markdown(f"**선택 기간:** `{start_date}` ~ `{end_date}` ({len(filtered_records)}일간)")

            # 주요 지표 강조 영역 (컬럼 배치)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="stat-label">🔥 역대 고온 순위</div>
                    <div class="highlight-rank">{rank_high:,} 위</div>
                    <div class="stat-label">상위 <b>{top_percent_high:.2f}%</b> (더웠던 날)</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="stat-label">❄️ 역대 저온 순위</div>
                    <div class="highlight-rank" style="color:#2b6cb0;">{rank_low:,} 위</div>
                    <div class="stat-label">상위 <b>{top_percent_low:.2f}%</b> (추웠던 날)</div>
                </div>
                """, unsafe_allow_html=True)

            st.write("")
            
            # 선택 기간 세부 정보 카드
            st.markdown("### 🌡️ 기간 내 기온 상세")
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("기간 평균", f"{period_avg:.1f} ℃")
            metric_col2.metric("기간 최고", f"{period_max:.1f} ℃")
            metric_col3.metric("기간 최저", f"{period_min:.1f} ℃")

            # 대중적인 인사이트 제공 메세지
            st.info(
                f"💡 선택하신 기간의 **{metric_type} 평균({period_avg:.1f}℃)**은 "
                f"전체 관측 역사({len(all_temps):,}일) 중 **{rank_high:,}번째로 높은 기온**입니다."
            )
