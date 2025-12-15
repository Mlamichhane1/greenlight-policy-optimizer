import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Greenlight: Policy Choice Optimizer", layout="wide")

st.title("Greenlight: Policy Choice Optimizer")
st.caption("Ranks policy options by PV(Expected Total Net Benefits), using Econ 351 discounting + probabilities.")

# Helpers
def pv_stream(B: list[float], r: float) -> float:
    # PV(B0..Bn) = Σ Bi/(1+r)^i
    return float(sum(B[i] / ((1 + r) ** i) for i in range(len(B))))

def compute_policy_scores(df: pd.DataFrame, r: float, mode: str) -> pd.DataFrame:
    work = df.copy()

    if mode == "Enter PV(TNB) directly":
        work["PV_TNB"] = pd.to_numeric(work["PV_TNB"], errors="coerce")
    else:
        # Stream mode: compute PV from B0..B3
        for c in ["B0", "B1", "B2", "B3"]:
            work[c] = pd.to_numeric(work[c], errors="coerce")
        work["PV_TNB"] = work.apply(lambda row: pv_stream([row["B0"], row["B1"], row["B2"], row["B3"]], r), axis=1)

    work["Prob"] = pd.to_numeric(work["Prob"], errors="coerce")
    work["Weighted_PV_TNB"] = work["Prob"] * work["PV_TNB"]

    scores = (
        work.groupby("Policy", as_index=False)
            .agg(PV_ETNB=("Weighted_PV_TNB", "sum"),
                 Prob_Sum=("Prob", "sum"))
            .sort_values("PV_ETNB", ascending=False)
            .reset_index(drop=True)
    )
    scores["Rank"] = np.arange(1, len(scores) + 1)
    return scores, work

# UI
tabs = st.tabs(["Policy Optimizer", "PV Calculator", "Bonus: Depletable Resource (2-period)"])

with tabs[0]:
    st.subheader("1) Policy Optimizer (PV(ETNB) Ranking)")

    mode = st.radio(
        "Input mode",
        ["Enter PV(TNB) directly", "Enter net-benefit stream (B0..B3) and compute PV using r"],
        horizontal=True,
    )

    r = st.slider("Discount rate (r)", min_value=0.0, max_value=0.30, value=0.07, step=0.005)

    st.markdown(
        "Econ 351 formulas used:\n"
        "- PV(Bn) = Bn / (1+r)^n and PV(stream) = Σ Bi/(1+r)^i\n"
        "- PV(ETNBj) = Σ Pij * PV(TNBij)\n"
    )

    # Default table: 4 policies x 3 outcomes (matches notes structure)
    if "df" not in st.session_state:
        base = []
        policies = ["A", "B", "C", "D"]
        outcomes = ["E", "F", "G"]
        for p in policies:
            for o in outcomes:
                base.append({"Policy": p, "Outcome": o, "Prob": 0.333, "PV_TNB": 0.0,
                             "B0": 0.0, "B1": 0.0, "B2": 0.0, "B3": 0.0})
        st.session_state.df = pd.DataFrame(base)

    df = st.session_state.df.copy()

    if mode == "Enter PV(TNB) directly":
        edit_cols = ["Policy", "Outcome", "Prob", "PV_TNB"]
    else:
        edit_cols = ["Policy", "Outcome", "Prob", "B0", "B1", "B2", "B3"]

    st.info("Tip: For each policy, make Prob values sum to ~1 across its outcomes (E/F/G).")

    edited = st.data_editor(
        df[edit_cols],
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
    )

    # Merge edits back into session df
    for col in edit_cols:
        st.session_state.df[col] = edited[col]

    scores, expanded = compute_policy_scores(st.session_state.df, r, mode)

    c1, c2 = st.columns([1, 1])

    with c1:
        st.write("### Ranking (higher PV(ETNB) is better)")
        st.dataframe(scores[["Rank", "Policy", "PV_ETNB", "Prob_Sum"]], use_container_width=True)

        best = scores.iloc[0]
        st.success(f"Recommended policy: **{best['Policy']}** (PV(ETNB) = {best['PV_ETNB']:.2f})")

    with c2:
        st.write("### Detailed calculations (per outcome)")
        show_cols = ["Policy", "Outcome", "Prob", "PV_TNB", "Weighted_PV_TNB"]
        st.dataframe(expanded[show_cols].sort_values(["Policy", "Outcome"]), use_container_width=True)

    # Probability check warnings
    bad = scores[np.abs(scores["Prob_Sum"] - 1.0) > 0.02]
    if not bad.empty:
        st.warning("Some policies have Prob sums not close to 1. Fix Prob for E/F/G under each policy to improve validity.")

with tabs[1]:
    st.subheader("2) PV Calculator (Quick sanity-check)")
    r2 = st.slider("Discount rate (r) for PV calculator", 0.0, 0.30, 0.07, 0.005, key="pv_calc_r")

    cols = st.columns(4)
    B = []
    for i, col in enumerate(cols):
        B.append(col.number_input(f"B{i}", value=0.0, step=100.0, help="Net benefits in period i"))

    pv = pv_stream(B, r2)
    st.metric("PV(B0..B3)", f"{pv:,.2f}")
    st.caption("Uses PV(stream) = Σ Bi/(1+r)^i")

with tabs[2]:
    st.subheader("Bonus) Depletable Resource Allocation (2-period dynamic efficiency)")
    st.caption("Solves q1*, q2* using P1−MC1 = (P2−MC2)/(1+r) with Q=q1+q2 (Econ 351).")

    a = st.number_input("a (from inverse demand P = a − bq)", value=8.0)
    b = st.number_input("b", value=0.4)
    mc = st.number_input("MC (constant)", value=2.0)
    r3 = st.number_input("r", value=0.10, step=0.01)
    Q = st.number_input("Total reserves Q", value=20.0)

    # Closed-form solution for linear demand + constant MC
    # MNB1 = (a-mc) - b q1 ; MNB2 = (a-mc) - b q2 ; condition: MNB1 = MNB2/(1+r), q2=Q-q1
    if b <= 0:
        st.error("b must be > 0")
    else:
        q1 = (r3 * (a - mc) + b * Q) / (b * (2 + r3))
        q2 = Q - q1
        P1 = a - b * q1
        P2 = a - b * q2

        st.write("### Solution")
        st.metric("q1*", f"{q1:.4f}")
        st.metric("q2*", f"{q2:.4f}")
        st.write(f"P1* = {P1:.4f}, P2* = {P2:.4f}")

        lhs = (P1 - mc)
        rhs = (P2 - mc) / (1 + r3)
        st.caption(f"Check: P1−MC = {lhs:.4f} and (P2−MC)/(1+r) = {rhs:.4f} (should match).")
