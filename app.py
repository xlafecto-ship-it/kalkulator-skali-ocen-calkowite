import streamlit as st
import math
import pandas as pd
import re

# ============================
# Helpers: half-point grid (0.5)
# ============================
def round_down_to_half(value: float) -> float:
    return math.floor(value * 2) / 2

def round_up_to_half(value: float) -> float:
    return math.ceil(value * 2) / 2

# ============================
# Teacher input parser (comma decimals)
# ============================
def parse_points_expression(expr: str) -> float | None:
    """
    Parsuje np. '3+5+2,5+0,5'
    Przecinek = separator dziesiętny
    """
    if not expr:
        return None

    expr = expr.replace(" ", "")
    if not re.fullmatch(r"[0-9+,]+", expr):
        return None

    try:
        return sum(float(p.replace(",", ".")) for p in expr.split("+") if p)
    except ValueError:
        return None

# ============================
# STAŁA SKALA 1–6 (bez +/-)
# (zmergowane zakresy z Twojej starej skali)
# 1: 0–29, 2: 30–45, 3: 46–69, 4: 70–84, 5: 85–95, 6: 96–100
# ============================
SCALE_SIMPLE = [
    ("1", 0, 29),
    ("2", 30, 45),
    ("3", 46, 69),
    ("4", 70, 84),
    ("5", 85, 95),
    ("6", 96, 100),
]

# ============================
# Build POINT thresholds (half-first)
# ============================
def build_thresholds_point_first(max_points: float):
    raw = []
    for grade, p_min, p_max in SCALE_SIMPLE:
        start_pts = round_up_to_half(max_points * (p_min / 100))
        end_pts   = round_down_to_half(max_points * (p_max / 100))
        raw.append((grade, start_pts, end_pts, p_min, p_max))

    raw.sort(key=lambda x: x[1])

    fixed = []
    last_end = None

    for grade, start_pts, end_pts, p_min, p_max in raw:
        if start_pts > end_pts:
            continue

        # usuwanie nakładek: pilnujemy kroków co 0.5
        if last_end is not None and start_pts <= last_end:
            start_pts = round_up_to_half(last_end + 0.5)

        if start_pts > end_pts:
            continue

        fixed.append((grade, start_pts, end_pts, p_min, p_max))
        last_end = end_pts

    return fixed

def grade_for_points(earned_pts_h: float, thresholds):
    if not thresholds:
        return "N/A"

    for grade, start_pts, end_pts, *_ in thresholds:
        if start_pts <= earned_pts_h <= end_pts:
            return grade

    # poniżej pierwszego progu -> najniższa ocena
    if earned_pts_h < thresholds[0][1]:
        return thresholds[0][0]

    # powyżej ostatniego -> najwyższa
    return thresholds[-1][0]

# ============================
# Percent formatting (no trailing .00)
# ============================
def percent_info_str(earned_pts_h: float, max_points: float) -> str:
    if not max_points:
        return "0%"
    return f"{(earned_pts_h / max_points) * 100:g}%"

# ============================
# UI
# ============================
st.title("Kalkulator ocen")

# Wycentruj tytuł
st.markdown(
    """
    <style>
    h1 { text-align: center; }

    .result-box {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 70px;
        border-radius: 0.6rem;
        font-weight: 600;
        text-align: center;
        color: white;
        margin-top: 0.25rem;
    }

    .box-sum { background-color: #1f4b6e; }
    .box-grade { background-color: #1f6e3f; }
    .box-grade-fail { background-color: #8b1e1e; }
    .box-percent { background-color: #6f42c1; }
    </style>
    """,
    unsafe_allow_html=True
)

max_points = st.number_input(
    "Maksymalna liczba punktów",
    min_value=1.0,
    step=1.0,
    value=25.0,
)

thresholds = build_thresholds_point_first(max_points)

st.subheader("Sprawdź wynik")

# lista możliwych punktów co 0.5
possible_points = [x / 2 for x in range(0, int(max_points * 2) + 1)]

col1, col2 = st.columns(2)

with col1:
    earned_select = st.selectbox("Zdobyte punkty", possible_points)

with col2:
    expr_input = st.text_input("Suma punktów (np. 2+1,5+0,5)")

parsed_sum = parse_points_expression(expr_input)

# ---- SUMA (box) ----
if parsed_sum is not None:
    st.markdown(
        f"""
        <div class="result-box box-sum">
            Suma punktów: {parsed_sum:g} / {max_points:g}
        </div>
        """,
        unsafe_allow_html=True
    )
    earned_raw = min(parsed_sum, max_points)
else:
    earned_raw = float(earned_select)

# ✅ ZAOKRĄGLANIE NA KORZYŚĆ UCZNIA: zawsze w górę do 0.5
earned_h = round_up_to_half(earned_raw)

found_grade = grade_for_points(earned_h, thresholds)
percent_str = percent_info_str(earned_h, max_points)

# ---- WYNIK: ocena | procent ----
res_col1, res_col2 = st.columns(2)

with res_col1:
    grade_class = "box-grade-fail" if found_grade == "1" else "box-grade"
    st.markdown(
        f"""
        <div class="result-box {grade_class}">
            Ocena: {found_grade}
        </div>
        """,
        unsafe_allow_html=True
    )

with res_col2:
    st.markdown(
        f"""
        <div class="result-box box-percent">
            Procent: {percent_str}
        </div>
        """,
        unsafe_allow_html=True
    )

st.caption(f"Punkty (połówki, zaokr. w górę): {earned_h:g} / {max_points:g}")

# ---- Skala ocen (wycentrowany nagłówek) ----
st.markdown("<h2 style='text-align: center;'>Skala ocen</h2>", unsafe_allow_html=True)

rows = []
for grade, start_pts, end_pts, p_min, p_max in thresholds:
    rows.append({
        "Punkty od": f"{start_pts:g}",
        "Punkty do": f"{end_pts:g}",
        "Ocena": grade,
        "Procent (źródło)": f"{p_min}–{p_max}%",
    })

df = pd.DataFrame(rows)
df.index = [""] * len(df)
st.table(df)

# ---- Diagnostyka (opcjonalnie) ----
with st.expander("Diagnostyka (opcjonalnie)"):
    if not thresholds:
        st.warning("Brak poprawnych progów (sprawdź max_points).")
    else:
        gaps = []
        for i in range(len(thresholds) - 1):
            _, _, end_i, *_ = thresholds[i]
            _, start_j, _, *_ = thresholds[i + 1]
            if start_j > end_i + 0.5:
                gaps.append((end_i + 0.5, start_j - 0.5))

        if gaps:
            st.warning("Wykryto luki (połówki, które nie należą do żadnej oceny):")
            st.write(gaps)
        else:
            st.success("Brak luk między progami na siatce 0.5.")

        st.write(f"Najniższy próg zaczyna się od: {thresholds[0][1]:g}")
        st.write(f"Najwyższy próg kończy się na: {thresholds[-1][2]:g}")
