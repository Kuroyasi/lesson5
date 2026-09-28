import numpy as np
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

# ── 구역 2: 장르 안의 영화별 총 관객 (트리맵) ─────────────────────
st.header("2. 장르별 영화 트리맵 (칸 크기 = 총 관객)")

fig_tree = px.treemap(
    df,
    path=[px.Constant("전체"), "genre", "movieNm"],
    values="total_audi",
)
fig_tree.update_traces(
    root_color="lightgrey",
    textinfo="label",
    hovertemplate="<b>%{label}</b><br>총 관객: %{value:,}명<extra></extra>",
)
fig_tree.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=650)
st.plotly_chart(fig_tree, use_container_width=True)

st.info("💡 **이 그래프로 알 수 있는 것:** (여기에 한 문장을 적어 주세요.)")

st.divider()

# ── 구역 3: 총 관객 히스토그램 ─────────────────────────────────────
st.header("3. 총 관객 분포 (히스토그램)")

BIN_SIZE = 100_000  # 구간 폭: 10만 명

fig_hist = px.histogram(
    df,
    x="total_audi",
    labels={"total_audi": "총 관객(명)", "count": "영화 편수"},
)
fig_hist.update_traces(
    xbins=dict(start=0, size=BIN_SIZE),
    hovertemplate="총 관객(명): %{x}<br>영화 편수: %{y}편<extra></extra>",
)
fig_hist.update_layout(
    xaxis_title="총 관객(명) · 구간 폭 10만 명",
    yaxis_title="영화 편수",
    bargap=0.05,
    margin=dict(t=20, b=20, l=10, r=10),
    height=500,
)
st.plotly_chart(fig_hist, use_container_width=True)

# 가장 영화가 많이 몰린 구간과 관객이 가장 많은 영화를 계산
bins = np.arange(0, df["total_audi"].max() + BIN_SIZE, BIN_SIZE)
counts, _ = np.histogram(df["total_audi"], bins=bins)
peak = int(counts.argmax())
lo, hi = int(bins[peak]), int(bins[peak + 1])
peak_n = int(counts[peak])
peak_share = peak_n / len(df) * 100

top = df.loc[df["total_audi"].idxmax()]

lo_txt = "0" if lo == 0 else f"{lo // 10_000:,}만"
st.info(
    f"💡 **이 그래프로 알 수 있는 것:** "
    f"전체 {len(df)}편 가운데 **{peak_n}편({peak_share:.0f}%)** 이 "
    f"총 관객 **{lo_txt} ~ {hi // 10_000:,}만 명** 구간에 몰려 있습니다. "
    f"관객이 가장 많은 영화는 **{top['movieNm']}** "
    f"(총 {int(top['total_audi']):,}명)입니다."
)

st.divider()

# ── 구역 4: 개봉일 스크린수와 총 관객 (산점도) ────────────────────
st.header("4. 개봉일 스크린수와 총 관객의 관계 (산점도)")

log_y = st.checkbox("총 관객 축을 로그 눈금으로 보기 (몰려 있는 점을 펼쳐 볼 때)", value=False)

fig_scatter = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    hover_data={"genre": False, "first_scrn": ":,", "total_audi": ":,"},
    labels={
        "first_scrn": "개봉일 스크린수(개)",
        "total_audi": "총 관객(명)",
        "genre": "장르",
    },
    log_y=log_y,
)
fig_scatter.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=0.5, color="white")))
fig_scatter.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=600)
st.plotly_chart(fig_scatter, use_container_width=True)

st.info("💡 **이 그래프로 알 수 있는 것:** (여기에 한 문장을 적어 주세요.)")

st.divider()

# ── 구역 5: 장르별 총 관객 상자 그림 (10편 이상 장르만) ──────────
st.header("5. 장르별 총 관객 분포 (상자 그림)")

MIN_MOVIES = 10
genre_n = df["genre"].value_counts()
big_genres = genre_n[genre_n >= MIN_MOVIES].index.tolist()  # 편수 많은 순
df_big = df[df["genre"].isin(big_genres)]

st.caption(
    f"영화가 {MIN_MOVIES}편 이상인 장르 {len(big_genres)}개만 골랐습니다: "
    + ", ".join(f"{g}({genre_n[g]}편)" for g in big_genres)
)

log_box = st.checkbox("총 관객 축을 로그 눈금으로 보기", value=False, key="log_box")

fig_box = px.box(
    df_big,
    x="genre",
    y="total_audi",
    color="genre",
    points="outliers",
    hover_name="movieNm",
    hover_data={"genre": False, "total_audi": ":,"},
    category_orders={"genre": big_genres},
    labels={"genre": "장르", "total_audi": "총 관객(명)"},
    log_y=log_box,
)
fig_box.update_layout(showlegend=False, margin=dict(t=20, b=20, l=10, r=10), height=600)
st.plotly_chart(fig_box, use_container_width=True)

st.info("💡 **이 그래프로 알 수 있는 것:** (여기에 한 문장을 적어 주세요.)")

st.divider()

# ── 구역 6: 스크린수와 총 관객 (버블 그래프, 점 크기 = 첫 주 관객) ─
st.header("6. 스크린수·총 관객·첫 주 관객 (버블 그래프)")
st.caption("4번 산점도와 같은 그래프에서 점의 크기를 개봉 첫 주 관객(first_week_audi)으로 나타냈습니다.")

log_bubble = st.checkbox("총 관객 축을 로그 눈금으로 보기", value=False, key="log_bubble")

fig_bubble = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi",
    color="genre",
    size_max=50,
    hover_name="movieNm",
    hover_data={
        "genre": False,
        "first_scrn": ":,",
        "total_audi": ":,",
        "first_week_audi": ":,",
    },
    labels={
        "first_scrn": "개봉일 스크린수(개)",
        "total_audi": "총 관객(명)",
        "first_week_audi": "첫 주 관객(명)",
        "genre": "장르",
    },
    log_y=log_bubble,
)
fig_bubble.update_traces(marker=dict(opacity=0.6, line=dict(width=0.5, color="white")))
fig_bubble.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=650)
st.plotly_chart(fig_bubble, use_container_width=True)

st.info("💡 **이 그래프로 알 수 있는 것:** (여기에 한 문장을 적어 주세요.)")

st.divider()

# ── 구역 7: 제작 국가 → 장르 선버스트 (칸 크기 = 영화 편수) ──────
st.header("7. 제작 국가에서 장르로 (선버스트)")
st.caption("안쪽 고리는 제작 국가, 바깥 고리는 그 나라 영화의 장르이며, 칸의 크기는 영화 편수입니다.")

nation_genre = (
    df.assign(nation=df["nation"].fillna("미상"))
    .groupby(["nation", "genre"])
    .size()
    .reset_index(name="편수")
)

fig_sun = px.sunburst(
    nation_genre,
    path=["nation", "genre"],
    values="편수",
)
fig_sun.update_traces(
    textinfo="label",
    hovertemplate="<b>%{label}</b><br>영화 편수: %{value}편<br>전체 대비: %{percentRoot:.1%}<extra></extra>",
)
fig_sun.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=700)
st.plotly_chart(fig_sun, use_container_width=True)

st.info("💡 **이 그래프로 알 수 있는 것:** (여기에 한 문장을 적어 주세요.)")

st.divider()

# ── 구역 8: 10위권 체류 기간과 총 관객 (산점도) ──────────────────
st.header("8. 10위권 체류 기간과 총 관객 (산점도)")

log_stay = st.checkbox("총 관객 축을 로그 눈금으로 보기", value=False, key="log_stay")

fig_stay = px.scatter(
    df,
    x="days_in_top10",
    y="total_audi",
    hover_name="movieNm",
    hover_data={"days_in_top10": ":,", "total_audi": ":,"},
    labels={
        "days_in_top10": "10위권에 머문 날수(일)",
        "total_audi": "총 관객(명)",
    },
    title="10위권에 오래 머문 영화는 총 관객도 많은가",
    log_y=log_stay,
)
fig_stay.update_traces(marker=dict(size=9, opacity=0.75, line=dict(width=0.5, color="white")))
fig_stay.update_layout(margin=dict(t=60, b=20, l=10, r=10), height=600)
st.plotly_chart(fig_stay, use_container_width=True)

st.info("💡 **이 그래프로 알 수 있는 것:** (여기에 한 문장을 적어 주세요.)")

st.divider()
