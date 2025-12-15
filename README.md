# Greenlight: Policy Choice Optimizer

A Streamlit app that ranks project options using **Present Value of Expected Total Net Benefits** (PV(ETNB)) under **discounting + uncertainty**.

This project applies core Econ 351 ideas:
- **Present Value (PV)** for a stream of net benefits  
- **Expected value under uncertainty** using outcome probabilities  
- **Policy ranking** by maximizing PV(ETNB)

---

## What the app does

✅ Lets you define multiple **policies** (A–D)  
✅ Each policy has multiple **outcomes** (E–G) with probabilities  
✅ Computes per-outcome PV(TNB) and the weighted sum:

**PV(ETNB\_j) = Σ P\_{ij} × PV(TNB\_{ij})**

✅ Ranks policies from best to worst  
✅ Shows detailed calculations and allows CSV export

---

## Input modes

### 1) Enter PV(TNB) directly
Use this when you already have PV(TNB) for each outcome.

Columns:
- `Policy`, `Outcome`, `Prob`, `PV_TNB`

### 2) Enter a net-benefit stream (B0..B3)
Use this when you want the app to compute PV from a time stream.

PV is computed as:

**PV(stream) = Σ B_t / (1 + r)^t**

Columns:
- `Policy`, `Outcome`, `Prob`, `B0`, `B1`, `B2`, `B3`

---

## How to run locally

### 1) Clone the repo
```bash
git clone https://github.com/Mlamichhane1/greenlight-policy-optimizer.git
cd greenlight-policy-optimizer
