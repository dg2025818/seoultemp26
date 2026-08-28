import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 기온 역대 순위 검색기",
    page_icon="🌡️",
    layout="wide"
)

# 데이터 로드 및 전처리 함수 (캐싱 적용으로 빠른 실행)
@st.cache_data
def load_data():
    df = pd.read_csv("seoul.csv")
    # 날짜 공백 제거 및 datetime 변환
    df["날짜"] = df["날짜"].astype(str).str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"])
    df = df.dropna(subset=["날짜"]).sort_values("날짜").reset_index(drop=True)
    return df

df = load_data()

# 커스텀 CSS 스타일링
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #31333F;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #ff4b4b;
    }
    .metric-rank {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1f77b4;
        margin-top: 5px;
    }
    .sub-text {
        font-size: 0.85rem;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

# 헤더 영역
st.title("🌡️ 서울 기온 역대 순위 검색기")
st.caption("선택하신 기간의 기온이 역대 서울 기온 기록 중 몇 위인지 분석합니다.")

min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()

# 날짜 선택 영역
st.subheader("📅 조회할 기간을 선택하세요")
col_date1, col_date2 = st.columns(2)

with col_date1:
    selected_range = st.date_input(
        "달력에서 기간 선택 (시작일과 종료일을 순서대로 클릭)",
        value=(max_date.replace(year=max_date.year - 1), max_date),
        min_value=min_date,
        max_value=max_date
    )

# 기간 선택 검증
if isinstance(selected_range, tuple) and len(selected_range) == 2:
    start_date, end_date = selected_range
    
    if start_date > end_date:
        st.error("시작일은 종료일보다 이전이어야 합니다.")
    else:
        # 선택한 기간 계산
        days_count = (end_date - start_date).days + 1
        
        # 선택 기간 데이터 추출
        mask = (df["날짜"].dt.date >= start_date) & (df["날짜"].dt.date <= end_date)
        selected_df = df.loc[mask]
        
        if len(selected_df) == 0 or selected_df["평균기온"].isna().all():
            st.warning("선택한 기간에 유효한 기온 데이터가 없습니다.")
        else:
            # 선택한 기간의 평균값 계산
            user_avg_temp = selected_df["평균기온"].mean()
            user_min_temp = selected_df["최저기온"].mean()
            user_max_temp = selected_df["최고기온"].mean()

            # 동일 일수(N일) 슬라이딩 윈도우 방식으로 전체 기간 순위 계산
            df_temp = df.copy()
            
            # 이동평균을 활용하여 N일 간의 평균 구하기
            df_temp["rolling_avg"] = df_temp["평균기온"].rolling(window=days_count).mean()
            df_temp["rolling_min"] = df_temp["최저기온"].rolling(window=days_count).mean()
            df_temp["rolling_max"] = df_temp["최고기온"].rolling(window=days_count).mean()
            
            valid_periods = df_temp.dropna(subset=["rolling_avg"]).copy()
            total_periods = len(valid_periods)

            # 순위 계산 (더운 순)
            avg_rank = (valid_periods["rolling_avg"] > user_avg_temp).sum() + 1
            min_rank = (valid_periods["rolling_min"] > user_min_temp).sum() + 1
            max_rank = (valid_periods["rolling_max"] > user_max_temp).sum() + 1

            # 백분위 계산
            avg_top_pct = (avg_rank / total_periods) * 100

            st.markdown("---")
            
            # 요약 메시지
            st.success(f"**선택 기간:** {start_date} ~ {end_date} (총 **{days_count}일간**)")
            
            # 요약 강조 박스
            if avg_top_pct <= 10:
                st.fire(f"🔥 이 기간은 역대 상위 **{avg_top_pct:.1f}%**에 해당하는 매우 무더운 기간이었습니다!")
            elif avg_top_pct >= 90:
                st.snowflake(f"❄️ 이 기간은 역대 하위 **{100 - avg_top_pct:.1f}%**에 해당하는 매우 추운 기간이었습니다!")

            # 카드 형태로 메트릭 표시
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔥 평균기온 (평균)</div>
                    <div class="metric-value">{user_avg_temp:.1f} °C</div>
                    <div class="metric-rank">역대 {avg_rank:,}위 <span class="sub-text">(상위 {avg_top_pct:.1f}%)</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            with c2:
                min_top_pct = (min_rank / total_periods) * 100
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🌙 최저기온 (평균)</div>
                    <div class="metric-value">{user_min_temp:.1f} °C</div>
                    <div class="metric-rank">역대 {min_rank:,}위 <span class="sub-text">(상위 {min_top_pct:.1f}%)</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            with c3:
                max_top_pct = (max_rank / total_periods) * 100
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">☀️ 최고기온 (평균)</div>
                    <div class="metric-value">{user_max_temp:.1f} °C</div>
                    <div class="metric-rank">역대 {max_rank:,}위 <span class="sub-text">(상위 {max_top_pct:.1f}%)</span></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            
            # 상세 일자별 기온 데이터 및 차트 제공
            st.subheader("📈 해당 기간 일자별 기온 추이")
            chart_data = selected_df.set_index("날짜")[["평균기온", "최저기온", "최고기온"]]
            st.line_chart(chart_data)

            with st.expander("📄 선택한 기간의 일별 데이터 보기"):
                st.dataframe(selected_df[["날짜", "평균기온", "최저기온", "최고기온"]].reset_index(drop=True), use_container_width=True)

else:
    st.info("💡 달력에서 두 번째 날짜까지 클릭하여 기간을 선택해 주세요.")
