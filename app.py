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
# STAŁA SKALA 1–6 (bez +/-)
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
    if points < thresholds[0][1]:
        return thresholds[0][0]
    return thresholds[-1][0]

def percent_str(points: float, max_points: float) -> str:
    # procent bez miejsc po przecinku
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
max_points_
