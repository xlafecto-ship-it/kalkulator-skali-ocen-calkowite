import streamlit as st
import math
import pandas as pd
import re

# ============================
# Helpers
# ============================
def round_up_to_half(value: float) -> float:
    return math.ceil(value * 2) / 2

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
# STAŁA SKALA 1–6
# ============================
SCALE_SIMPLE = [
    ("1", 0, 29),
    ("2", 30, 45),
    ("3", 46, 69),
    ("4", 70, 84),
    ("5", 85, 95),
    ("6", 96, 100),
]

def build_thresholds(max_points: float):
    thresholds = []
    for grade, p_min, p_max in SCALE_SIMPLE:
        start = math.ceil(max_points * p_min / 100 * 2) / 2
        end   = math.floor(max_points * p_max / 100 * 2) / 2
        thresholds.append((grade, start, end, p_min, p_max))
    return thresholds

def grade_for_points(points: float, thresholds):
    for grade, start, end, *_ in thresholds:
        if start <= points <= end:
            return grade
    return thresholds[-1][0]

def percent_str(points: float, max_points: float) -> str:
    return f"{int(round((points / max_points) * 100))}%"

# ============================
# UI
# ============================
st.title("Kalkulator ocen")

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
        text-align: center;
    }

    .box-sum { background-color: #1f4b6e; }
    .box-grade { background-color: #1f6e3f; }
    .box-grade-fail { background-color: #8b1e1e; }
    .box-percent { background-color: #6f42c1; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- MAX POINTS ----------
max_points = st.number_input(
    "Maksymalna liczba punktów",
    min_value=1.0,
    max_value=500.0,
    value=None,
    placeholder="np. 25"
)

if max_points is None:
    st.info("Wpisz maksymalną liczbę punktów, aby kontynuować.")
    st.stop()

thresholds = build_thresholds(max_points)

st.subheader("Sprawdź wynik")

c1, c2 = st.columns(2)

# ---------- MANUAL POINTS ----------
with c1:
    manual_points = st.number_input(
        "Zdobyte punkty",
        min_value=0.0,
        max_value=float(max_points),
        value=0.0,
        step=0.5
    )

# ---------- SUM EXPRESSION ----------
with c2:
    expr = st.text_input("Suma punktów (np. 2+1,5+0,5)")

expr_clean = expr.strip()
parsed = parse_points_expression(expr_clean) if expr_clean else None

if expr_clean and parsed is None:
    st.error("Błędny zapis sumy punktów. Użyj np. 2+1,5+0,5.")

# ---------- SOURCE OF POINTS ----------
if parsed is not None:
    if parsed > max_points:
        st.warning(
            f"Suma punktów ({parsed:g}) przekracza maksymalną liczbę punktów "
            f"({max_points:g}). Do obliczeń przyjęto {max_points:g}."
        )
        raw_points = max_points
    else:
        raw_points = parsed

    st.markdown(
        f"""
        <div class="result-box box-sum">
            Suma punktów: {raw_points:g} / {max_points:g}
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    raw_points = manual_points

# ---------- ROUNDING ----------
points_half = round_up_to_half(raw_points)

grade = grade_for_points(points_half, thresholds)
percent = percent_str(points_half, max_points)

# ---------- RESULT ----------
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

# ---------- SCALE ----------
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
