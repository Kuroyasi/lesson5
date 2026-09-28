import pandas as pd
import plotly.express as px
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/happykth/data/main/kobis_movies.csv"

st.set_page_config(page_title="영화 데이터 그래프 도감 2", page_icon="🎬", layout="wide")


@st.cache_data(show_spinner="데이터를 불러오는 중...")
def load_data(url: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(url)
    except UnicodeDecodeError:
        df = pd.read_csv(url, encoding="cp949")

    # 개봉일: 여덟 자리 숫자(예: 20240131) -> 날짜
    df["openDt"] = pd.to_datetime(
        df["openDt"].astype(str).str.replace(r"\.0$", "", regex=True),
        format="%Y%m%d",
        errors="coerce",
    )

    # 장르: '|'로 여러 개 적힌 경우 첫 번째 장르만 사용
    df["genre"] = (
        df["genre"].fillna("미분류").astype(str).str.split("|").str[0].str.strip()
    )
    df.loc[df["genre"] == "", "genre"] = "미분류"
    return df


st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.caption(
    "1년간 박스오피스 10위권에 든 영화 가운데 이 기간에 개봉한 영화들의 요약표를 그래프로 살펴봅니다."
)

try:
    df = load_data(DATA_URL)
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다. 주소를 확인해 주세요.\n\n{e}")
    st.stop()

with st.expander("데이터 미리보기", expanded=False):
    st.write(f"총 {len(df):,}편 · {df.shape[1]}개 열")
    st.dataframe(df.head(20), use_container_width=True)

st.divider()

# ── 구역 1: 장르별 영화 편수 (도넛 그래프) ─────────────────────────
st.header("1. 장르별 영화 편수")

genre_counts = (
    df["genre"].value_counts().rename_axis("장르").reset_index(name="편수")
)

fig_donut = px.pie(
    genre_counts,
    names="장르",
    values="편수",
    hole=0.5,
)
fig_donut.update_traces(
    textposition="inside",
    textinfo="label+percent",
    hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>",
)
fig_donut.update_layout(
    legend_title_text="장르",
    margin=dict(t=20, b=20, l=20, r=20),
    height=520,
    annotations=[
        dict(
            text=f"전체<br><b>{len(df)}편</b>",
            x=0.5,
            y=0.5,
            font_size=20,
            showarrow=False,
        )
    ],
)
st.plotly_chart(fig_donut, use_container_width=True)

st.info("💡 **이 그래프로 알 수 있는 것:** (여기에 한 문장을 적어 주세요.)")

st.divider()
