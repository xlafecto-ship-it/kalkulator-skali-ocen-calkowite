import streamlit as st
import math
import pandas as pd
import re

# ============================
# Helpers: half-point grid (0.5)
# ============================
def round_up_to_half(value: float) -> float:
    return math.ceil(value * 2) / 2

# ============================
# Teacher input parser
# ============================
def parse_points_expression(expr: str) -> float | None:
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
# ============================
SCALE_SIMPLE = [
    ("1", 0, 27),
    ("2", 28, 47),
    ("3", 48, 67),
    ("4", 68, 82),
    ("5", 83, 93),
    ("6", 94, 100),
]

# ============================
# Thresholds (half grid)
# ============================
def build_thresholds(max_points: float):
    thresholds = []
    for grade, p_min, p_max in SCALE_SIMPLE:
        start = math.ceil(max_points * p_min / 100 * 2) / 2
        end = math.floor(max_points * p_max / 100 * 2) / 2
        thresholds.append((grade, start, end, p_min, p_max))
    return thresholds

def grade_for_points(points: float, thresholds):
    for grade, start, end, *_ in thresholds:
        if start <= points <= end:
            return grade
    return thresholds[-1][0]

def percent_str(points: float, max_points: float) -> str:
    return f"{(points / max_points) * 100:g}%"

# ============================
# UI
# ============================
st.title("Kalkulator ocen")

# ⚠️ CSS – MUSI mieć unsafe_allow_html=True
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
    value=25.0
)

thresholds = build_thresholds(max_points)

st.subheader("Sprawdź wynik")

possible_points = [x / 2 for x in range(0, int(max_points * 2) + 1)]

c1, c2 = st.columns(2)

with c1:
    manual_points = st.selectbox("Zdobyte punkty", possible_points)

with c2:
    expr = st.text_input("Suma punktów (np. 2+1,5+0,5)")

parsed = parse_points_expression(expr)

# ---- SUMA ----
if parsed is not None:
    st.markdown(
        f"""
        <div class="result-box box-sum">
            Suma punktów: {parsed:g} / {max_points:g}
        </div>
        """,
        unsafe_allow_html=True
    )
    raw_points = min(parsed, max_points)
else:
    raw_points = manual_points

# ✅ zaokrąglanie w górę (na korzyść ucznia)
points_half = round_up_to_half(raw_points)

grade = grade_for_points(points_half, thresholds)
percent = percent_str(points_half, max_points)

# ---- WYNIK ----
r1, r2 = st.columns(2)

with r1:
    cls = "box-grade-fail" if grade == "1" else "box-grade"
    st.markdown(
        f"<div class='result-box {cls}'>Ocena: {grade}</div>",
        unsafe_allow_html=True
    )

with r2:
    st.markdown(
        f"<div class='result-box box-percent'>Procent: {percent}</div>",
        unsafe_allow_html=True
    )

st.caption(f"Punkty (połówki, zaokr. w górę): {points_half:g} / {max_points:g}")

# ---- SKALA ----
st.markdown("<h2 style='text-align: center;'>Skala ocen</h2>", unsafe_allow_html=True)

df = pd.DataFrame([
    {
        "Ocena": g,
        "Punkty od": f"{s:g}",
        "Punkty do": f"{e:g}",
        "Procent": f"{p1}–{p2}%"
    }
    for g, s, e, p1, p2 in thresholds
])

df.index = [""] * len(df)
st.table(df)
