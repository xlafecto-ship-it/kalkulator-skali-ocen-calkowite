import streamlit as st
import math
import pandas as pd

# ----------------------------
# Skala ocen (źródło prawdy: procenty)
# ----------------------------
SCALE = [
    ("1",   0, 25),
    ("1+", 26, 27),
    ("2-", 28, 29),
    ("2",  30, 45),
    ("2+", 46, 47),
    ("3-", 48, 49),
    ("3",  50, 65),
    ("3+", 66, 67),
    ("4-", 68, 69),
    ("4",  70, 80),
    ("4+", 81, 82),
    ("5-", 83, 84),
    ("5",  85, 91),
    ("5+", 92, 93),
    ("6-", 94, 94),
    ("6",  95, 100),
]

# ----------------------------
# Budowa progów punktowych (TYLKO pełne punkty)
# ----------------------------
def build_thresholds_points_only(max_points: int):
    thresholds = []

    for grade, p_min, p_max in SCALE:
        start_pts = math.ceil(max_points * p_min / 100)
        end_pts   = math.floor(max_points * p_max / 100)

        if start_pts <= end_pts:
            thresholds.append((grade, start_pts, end_pts, p_min, p_max))

    thresholds.sort(key=lambda x: x[1])
    return thresholds

# ----------------------------
# Decyzja o ocenie
# Polityka: luka → zaokrąglenie w górę
# ----------------------------
def grade_for_points(earned_pts: int, thresholds):
    if not thresholds:
        return "N/A"

    # Trafienie bezpośrednie
    for grade, start, end, *_ in thresholds:
        if start <= earned_pts <= end:
            return grade

    first_grade, first_start, *_ = thresholds[0]
    last_grade, _, last_end, *_ = thresholds[-1]

    # Poniżej skali
    if earned_pts < first_start:
        return first_grade

    # Powyżej skali
    if earned_pts > last_end:
        return last_grade

    # Luka → wyższa ocena
    for grade, start, *_ in thresholds:
        if earned_pts < start:
            return grade

    return last_grade  # safety net

# ----------------------------
# UI
# ----------------------------
st.title("Kalkulator skali ocen (pełne punkty)")

max_points = st.number_input(
    "Maksymalna liczba punktów",
    min_value=1,
    step=1,
    value=20,
)

max_points = int(max_points)

thresholds = build_thresholds_points_only(max_points)

st.subheader("Sprawdź ocenę")

earned = st.selectbox(
    "Zdobyte punkty",
    list(range(0, max_points + 1))
)

percent = (earned / max_points) * 100
grade = grade_for_points(earned, thresholds)

result_box = st.empty()

if grade in ("1", "1+"):
    result_box.error(f"Ocena: **{grade}**")
else:
    result_box.success(f"Ocena: **{grade}**")

st.caption(
    f"Punkty: {earned} / {max_points} | Procent (informacyjnie): {percent:.2f}%"
)

# ----------------------------
# Tabela progów
# ----------------------------
st.subheader("Skala ocen (punkty → ocena)")

rows = []
for grade, start, end, p_min, p_max in thresholds:
    rows.append({
        "Punkty od": start,
        "Punkty do": end,
        "Ocena": grade,
        "Procent (źródło)": f"{p_min}–{p_max}%",
    })

df = pd.DataFrame(rows)
df.index = [""] * len(df)

st.table(df)

# ----------------------------
# Diagnostyka (opcjonalna)
# ----------------------------
with st.expander("Diagnostyka"):
    if not thresholds:
        st.warning("Brak poprawnych progów.")
    else:
        gaps = []
        for i in range(len(thresholds) - 1):
            _, _, end_i, *_ = thresholds[i]
            _, start_j, _, *_ = thresholds[i + 1]
            if start_j > end_i + 1:
                gaps.append((end_i + 1, start_j - 1))

        if gaps:
            st.warning("Luki punktowe (dozwolone):")
            st.write(gaps)
        else:
            st.success("Brak luk punktowych.")

        st.write(f"Zakres skali: {thresholds[0][1]} – {thresholds[-1][2]}")
