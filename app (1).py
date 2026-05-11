"""
Spillway Slab — Tension Analysis
Calavera method + FRC contribution + Maperod bar validation
"""

import math
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Spillway Slab Design",
    page_icon="🏗️",
    layout="wide",
)

st.markdown("""
<style>
.block-container { padding-top:1.2rem; }
.res  { background:#f0f4f8; border-left:4px solid #2c5f8a;
        padding:0.5rem 1rem; border-radius:4px; margin:0.25rem 0; }
.ok   { border-left-color:#2e7d32; background:#f1f8f1; }
.warn { border-left-color:#c62828; background:#fdf1f1; }
.info { border-left-color:#e67e22; background:#fef9f0; }
h3    { color:#1F4E79; border-bottom:2px solid #1F4E79;
        padding-bottom:3px; margin-top:1.2rem; }
</style>
""", unsafe_allow_html=True)

def box(label, value, unit="", fmt=".3f", kind=""):
    val = f"{value:{fmt}}" if isinstance(value,(int,float)) else str(value)
    st.markdown(
        f'<div class="res {kind}"><b>{label}:</b> '
        f'<span style="font-size:1.05em">{val}</span> {unit}</div>',
        unsafe_allow_html=True)

# ─── SIDEBAR — ALL INPUTS ────────────────────────────────────────────────────
st.sidebar.title("⚙️ Input Parameters")

st.sidebar.subheader("Geometry")
h   = st.sidebar.number_input("Slab thickness  h  [m]",        0.02, 0.50, 0.05, 0.005, format="%.3f")
L   = st.sidebar.number_input("Slab length  L  [m]",           1.0,  50.0, 15.0, 0.5)
H   = st.sidebar.number_input("Slope ratio  H  (H:1V)",        0.5,  5.0,  1.35, 0.05)

st.sidebar.subheader("Materials")
fck  = st.sidebar.number_input("Concrete  fck  [MPa]",          12.0, 70.0, 25.0, 1.0)
gamma= st.sidebar.number_input("Unit weight γ  [kN/m³]",        20.0, 26.0, 25.0, 0.5)
alpha= st.sidebar.number_input("Thermal expansion α  [×10⁻⁶/°C]",6.0,12.0,10.0,0.5) * 1e-6
er   = st.sidebar.number_input("Shrinkage strain  εr  [×10⁻³]", 0.10, 1.00, 0.35, 0.05) * 1e-3

st.sidebar.subheader("Loading")
dT   = st.sidebar.number_input("Temperature drop  |ΔT|  [°C]",  0.0,  50.0, 20.0, 1.0)

st.sidebar.subheader("FRC — Fibre Reinforced Concrete")
fR3k = st.sidebar.number_input("Residual strength  fR3k  [MPa]",0.5,  6.0,  1.8,  0.1)
gc   = st.sidebar.number_input("Partial factor  γc",             1.0,  2.0,  1.5,  0.1)

st.sidebar.subheader("Maperod Bars")
FC   = st.sidebar.number_input("Max. force Maperod C  [kN/bar]",5.0, 100.0,35.0, 1.0)
FG   = st.sidebar.number_input("Max. force Maperod G  [kN/bar]",1.0,  50.0,10.0, 1.0)

st.sidebar.subheader("Friction scenarios (μ)")
mu1  = st.sidebar.number_input("μ — Scenario 1",  0.1, 5.0, 0.5, 0.1)
mu2  = st.sidebar.number_input("μ — Scenario 2",  0.1, 5.0, 1.0, 0.1)
mu3  = st.sidebar.number_input("μ — Scenario 3",  0.1, 5.0, 2.0, 0.1)

st.sidebar.subheader("Bar spacing per scenario  [mm]")
sC1  = st.sidebar.number_input("Maperod C spacing — Sc1",  25, 1000, 100, 25)
sC2  = st.sidebar.number_input("Maperod C spacing — Sc2",  25, 1000, 100, 25)
sC3  = st.sidebar.number_input("Maperod C spacing — Sc3",  25, 1000,  75, 25)
sG1  = st.sidebar.number_input("Maperod G spacing — Sg1",  25, 1000, 150, 25)
sG2  = st.sidebar.number_input("Maperod G spacing — Sg2",  25, 1000, 150, 25)
sG3  = st.sidebar.number_input("Maperod G spacing — Sg3",  25, 1000, 100, 25)

# ─── CALCULATIONS ────────────────────────────────────────────────────────────
theta = math.degrees(math.atan(1.0/H))
sin_t = math.sin(math.radians(theta))
cos_t = math.cos(math.radians(theta))

# fctm — EC2 Table 3.1
fctm = 0.30 * fck**(2/3)

# Self-weight components
w      = gamma * h
w_par  = w * sin_t
g_eff  = w * cos_t

# Displacements
dLt = alpha * dT * L * 1000   # mm
dLr = er    * L   * 1000      # mm
Kt  = max((dLt + dLr) / 1.5, 1.0)

# FRC
fFtu_k = fR3k / 3.0
fFtu_d = fFtu_k / gc
Nfrc   = fFtu_d * h * 1000    # kN/m

def scenario(mu, sC_mm, sG_mm):
    N_sw_raw = (w_par - mu*g_eff)*L
    N_sw     = max(N_sw_raw, 0.0)
    sig_sw   = N_sw / h / 1000

    N_kt  = Kt * mu * g_eff * L
    sig_kt= N_kt / h / 1000

    N_tot = N_sw + N_kt
    sig_tot = N_tot / h / 1000

    N_res = max(N_tot - Nfrc, 0.0)

    nC = 1000.0/sC_mm
    FC_bar = N_res / nC if nC>0 else 0
    util_C = FC_bar/FC*100 if FC>0 else 0
    ok_C   = FC_bar <= FC

    nG = 1000.0/sG_mm
    FG_bar = N_res / nG if nG>0 else 0
    util_G = FG_bar/FG*100 if FG>0 else 0
    ok_G   = FG_bar <= FG

    return dict(
        mu=mu, N_sw_raw=N_sw_raw, N_sw=N_sw, sig_sw=sig_sw,
        N_kt=N_kt, sig_kt=sig_kt, N_tot=N_tot, sig_tot=sig_tot,
        N_res=N_res, frc_pct=Nfrc/N_tot*100 if N_tot>0 else 0,
        sC=sC_mm, nC=nC, FC_bar=FC_bar, util_C=util_C, ok_C=ok_C,
        sG=sG_mm, nG=nG, FG_bar=FG_bar, util_G=util_G, ok_G=ok_G,
    )

sc = [scenario(mu1,sC1,sG1), scenario(mu2,sC2,sG2), scenario(mu3,sC3,sG3)]

# ─── MAIN PAGE ───────────────────────────────────────────────────────────────
st.title("🏗️ Spillway Slab — Tension Analysis")
st.caption("Calavera friction method · FRC contribution (CE 2021 / fib MC2010) · Maperod bar validation")

# ── Section A: Intermediate results ──────────────────────────────────────────
with st.expander("📐 A.  Geometry & Intermediate Calculations", expanded=True):
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("**Geometry**")
        box("Inclination θ",      theta,  "°",     ".2f")
        box("sin θ / cos θ",      f"{sin_t:.4f} / {cos_t:.4f}", kind="")
        box("Self-weight  w",     w,      "kN/m²", ".3f")
        box("w∥  (parallel)",     w_par,  "kN/m²", ".4f")
        box("g_eff  (perp.)",     g_eff,  "kN/m²", ".4f")
    with c2:
        st.markdown("**Displacements & Kt**")
        box("δLt  (thermal)",     dLt,    "mm",    ".2f")
        box("δLr  (shrinkage)",   dLr,    "mm",    ".2f")
        box("δLt + δLr",         dLt+dLr,"mm",    ".2f")
        box("Kt = (δLr+δLt)/1.5  ≥ 1", Kt, "–",  ".2f", kind="info")
    with c3:
        st.markdown("**Concrete & FRC**")
        box("fck",                fck,    "MPa",   ".1f")
        box("fctm = 0.30·fck^⅔", fctm,   "MPa",   ".3f")
        box("fFtu,k = fR3k/3",    fFtu_k, "MPa",   ".3f")
        box("fFtu,d = fFtu,k/γc", fFtu_d, "MPa",   ".3f")
        box("N_frc = fFtu,d·h·1000", Nfrc,"kN/m",  ".2f", kind="info")

# ── Section B: Results per scenario ──────────────────────────────────────────
st.markdown("### B.  Results by friction scenario")

tabs = st.tabs([f"μ = {mu1}", f"μ = {mu2}", f"μ = {mu3}"])

for tab, s in zip(tabs, sc):
    with tab:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Membrane forces**")
            box("N_sw  (self-weight)",     s["N_sw"],  "kN/m", ".2f")
            box("N_Kt  (shrink+thermal)",  s["N_kt"],  "kN/m", ".2f")
            box("N_TOTAL",                 s["N_tot"], "kN/m", ".2f",
                kind="warn" if s["sig_tot"]>fctm else "ok")
            box("σ_TOTAL",                 s["sig_tot"],"MPa",".3f",
                kind="warn" if s["sig_tot"]>fctm else "ok")
            box("Concrete check (vs fctm="+f"{fctm:.3f} MPa)",
                "✗ CRACK" if s["sig_tot"]>fctm else "✓ OK",
                kind="warn" if s["sig_tot"]>fctm else "ok")

        with col2:
            st.markdown("**FRC deduction**")
            box("N_frc  (FRC capacity)",  Nfrc,        "kN/m", ".2f")
            box("% covered by FRC",       s["frc_pct"],"%" ,   ".1f")
            box("N_residual  (→ bars)",   s["N_res"],  "kN/m", ".2f",
                kind="info")

        with col3:
            st.markdown("**Bar validation**")
            st.markdown(f"*Maperod C — spacing {s['sC']} mm  ({s['nC']:.1f} bars/m)*")
            box("Force per bar  F_C", s["FC_bar"], "kN", ".2f",
                kind="ok" if s["ok_C"] else "warn")
            box("Utilisation", s["util_C"], "%", ".1f",
                kind="ok" if s["ok_C"] else "warn")
            box("CHECK C", "✓ OK" if s["ok_C"] else "✗ FAIL",
                kind="ok" if s["ok_C"] else "warn")

            st.markdown(f"*Maperod G — spacing {s['sG']} mm  ({s['nG']:.1f} bars/m)*")
            box("Force per bar  F_G", s["FG_bar"], "kN", ".2f",
                kind="ok" if s["ok_G"] else "warn")
            box("Utilisation", s["util_G"], "%", ".1f",
                kind="ok" if s["ok_G"] else "warn")
            box("CHECK G", "✓ OK" if s["ok_G"] else "✗ FAIL",
                kind="ok" if s["ok_G"] else "warn")

# ── Section C: Comparison table ───────────────────────────────────────────────
st.markdown("### C.  Comparison table — all scenarios")

rows = []
for s in sc:
    rows.append({
        "μ":                  s["mu"],
        "N_sw [kN/m]":        round(s["N_sw"],2),
        "N_Kt [kN/m]":        round(s["N_kt"],2),
        "N_TOTAL [kN/m]":     round(s["N_tot"],2),
        "σ_TOTAL [MPa]":      round(s["sig_tot"],3),
        "Concrete":           "✓ OK" if s["sig_tot"]<=fctm else "✗ CRACK",
        "N_frc [kN/m]":       round(Nfrc,2),
        "N_residual [kN/m]":  round(s["N_res"],2),
        "% FRC":              round(s["frc_pct"],1),
        "sC [mm]":            s["sC"],
        "F_bar C [kN]":       round(s["FC_bar"],2),
        "Util_C [%]":         round(s["util_C"],1),
        "Check C":            "✓ OK" if s["ok_C"] else "✗ FAIL",
        "sG [mm]":            s["sG"],
        "F_bar G [kN]":       round(s["FG_bar"],2),
        "Util_G [%]":         round(s["util_G"],1),
        "Check G":            "✓ OK" if s["ok_G"] else "✗ FAIL",
    })

df = pd.DataFrame(rows)

def color_check(val):
    if "✓" in str(val):
        return "background-color:#e8f5e9; color:#1b5e20"
    elif "✗" in str(val):
        return "background-color:#ffebee; color:#b71c1c"
    return ""

st.dataframe(
    df.style.applymap(color_check, subset=["Concrete","Check C","Check G"]),
    use_container_width=True, hide_index=True)

# ── Section D: Sensitivity — spacing sweep ────────────────────────────────────
st.markdown("### D.  Spacing sweep — Maperod C  (scenario μ₁)")

spacings = list(range(25, 501, 25))
sweep_rows = []
for sp in spacings:
    s0 = sc[0]
    nC = 1000.0/sp
    F  = s0["N_res"]/nC if nC>0 else 0
    sweep_rows.append({
        "Spacing s [mm]": sp,
        "Bars/m":         round(nC,2),
        "Force/bar [kN]": round(F,2),
        "Utilisation [%]":round(F/FC*100 if FC>0 else 0,1),
        "Status":         "✓ OK" if F<=FC else "✗ FAIL",
    })

df_sweep = pd.DataFrame(sweep_rows)
st.dataframe(
    df_sweep.style.applymap(color_check, subset=["Status"]),
    use_container_width=True, hide_index=True)

# ── Section E: Notes ──────────────────────────────────────────────────────────
with st.expander("📋 E.  Method notes & references"):
    st.markdown("""
**Calculation flow:**
`N_total (Calavera)` → deduct `N_frc (FRC)` → `N_residual` → `F per bar = N_residual/n` → check `F ≤ F_max`

**Key assumptions:**
- **Kt** = (δLr + δLt)/1.5 ≥ 1 — single combined coefficient for shrinkage and thermal action
  (Calavera, *Hormigón Armado*, eq. 70.4).
- Full length **L** is used (not L/2): upper end fixed to dam, lower end free —
  all friction accumulates at the anchor.
- **N_sw = 0** when friction exceeds the sliding component (conservative — no compressive credit).
- **fctm** = 0.30·fck^(2/3) — EC2 Table 3.1 (valid for fck ≤ 50 MPa).
- **fFtu,d** = fR3k / (3·γc) — Annex 14, Structural Code 2021 / fib MC2010,
  softening behaviour (conservative).
- **N_frc** is independent of friction coefficient μ.

**References:**
- Calavera, J. (2008). *Cálculo, construcción, patología y rehabilitación de forjados de edificación*. INTEMAC, eq. 70.4–70.6.
- Código Estructural (RD 470/2021), Annex 14 — Fibre Reinforced Concrete.
- fib Model Code 2010, §5.6.
- EN 1992-1-1 (EC2), Table 3.1.
- Mapei — *Maperod C & G Technical Datasheet*.
    """)

st.markdown("---")
st.caption("Spillway Slab Design Tool · Calavera + FRC + Maperod · Built with Streamlit")
