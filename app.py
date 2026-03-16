"""
IMADATA Market Intelligence Dashboard
MSc Business Analytics Dissertation | Durham University | 2025 | Amrit Sharma
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IMADATA Market Intelligence — Mexico",
    page_icon="🇲🇽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "outputs")
GEO  = os.path.join(BASE, "mexico-geojson-main", "2020", "mexico.json")

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY   = "#0D2B45"
TEAL   = "#3B9ED4"
ORANGE = "#E65100"
RED    = "#C62828"
GREEN  = "#1B7A6E"
BLUE   = "#1565C0"
GRAY   = "#8892A4"

QUAD_COLORS = {
    "Priority":  TEAL,
    "Contested": ORANGE,
    "Monitor":   BLUE,
    "Avoid":     RED,
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0D2B45; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label { color: #8892A4 !important; font-size: 0.78rem; }
.metric-card {
    background: #0D2B45; border-radius: 8px; padding: 18px 20px;
    border-left: 4px solid #3B9ED4; margin-bottom: 8px;
}
.metric-card .val { font-size: 2rem; font-weight: 700; color: #3B9ED4; }
.metric-card .lbl { font-size: 0.78rem; color: #8892A4; margin-top: 2px; }
.section-header {
    font-size: 1.4rem; font-weight: 700; color: #0D2B45;
    border-bottom: 3px solid #3B9ED4; padding-bottom: 6px; margin-bottom: 18px;
}
.quad-pill {
    display: inline-block; border-radius: 4px;
    padding: 2px 10px; font-size: 0.72rem; font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    opp   = pd.read_csv(os.path.join(OUT, "state_opportunity_scores.csv"))
    cii   = pd.read_csv(os.path.join(OUT, "state_competitive_intensity.csv"))
    mat   = pd.read_csv(os.path.join(OUT, "market_entry_matrix.csv"))
    prio  = pd.read_csv(os.path.join(OUT, "priority_markets.csv"))
    munis = pd.read_csv(os.path.join(OUT, "municipality_hotspots.csv"))
    segs  = pd.read_csv(os.path.join(OUT, "customer_segments.csv"))

    # normalise state names
    for df in [opp, cii, mat, prio, munis]:
        df["state_name"] = df["state_name"].str.strip().str.title()

    return opp, cii, mat, prio, munis, segs

@st.cache_resource
def load_geojson():
    with open(GEO, encoding="utf-8") as f:
        return json.load(f)

opp, cii, mat, prio, munis, segs = load_data()
geojson = load_geojson()

# ── Build state-level GeoJSON (dissolve municipalities → states) ──────────────
_STATE_GEO_CACHE = os.path.join(BASE, "outputs", "state_mexico_cached.json")

@st.cache_data
def build_state_geojson():
    """Dissolve municipality polygons into state polygons using shapely.
    Result cached to disk — subsequent starts load the 1.6 MB file instantly."""
    if os.path.exists(_STATE_GEO_CACHE):
        with open(_STATE_GEO_CACHE, encoding="utf-8") as f:
            return json.load(f)

    import unicodedata
    from collections import defaultdict
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union

    def strip_accents(s):
        return "".join(
            c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
        )

    state_shapes = defaultdict(list)
    for feat in geojson["features"]:
        raw  = feat["properties"].get("NOM_ENT", "").strip()
        name = strip_accents(raw).title()
        try:
            geom = shape(feat["geometry"])
            state_shapes[name].append(geom if geom.is_valid else geom.buffer(0))
        except Exception:
            pass

    features = []
    for state, shapes in state_shapes.items():
        dissolved  = unary_union(shapes)
        simplified = dissolved.simplify(0.01, preserve_topology=True)
        features.append({
            "type": "Feature", "id": state,
            "properties": {"name": state},
            "geometry": mapping(simplified),
        })

    result = {"type": "FeatureCollection", "features": features}
    with open(_STATE_GEO_CACHE, "w", encoding="utf-8") as f:
        json.dump(result, f)
    return result

state_geo = build_state_geojson()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇲🇽 IMADATA")
    st.markdown("**Market Intelligence Framework**")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Overview", "Customer Segmentation", "Competitive Intelligence",
         "Market Entry Matrix", "Entry Rankings", "Priority Markets"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**MSc Business Analytics**")
    st.markdown("Durham University · 2025")
    st.markdown("Amrit Sharma")
    st.markdown("---")
    st.caption("Data: DENUE / INEGI (public domain)")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.markdown("## Market Intelligence Framework — Mexico")
    st.markdown(
        "A data-driven market entry strategy for **IMADATA** built entirely on open DENUE data. "
        "Three analytical stages: customer segmentation, competitive intelligence, and market entry scoring."
    )

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, lbl in zip(
        [c1, c2, c3, c4, c5],
        ["43,330", "20,874", "32", "8", "3"],
        ["Wholesale-trade firms analysed", "Competitor firms mapped",
         "Mexican states scored", "Priority markets identified", "Notebook pipeline stages"],
    ):
        col.markdown(
            f'<div class="metric-card"><div class="val">{val}</div>'
            f'<div class="lbl">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Map + quadrant summary side by side
    col_map, col_quad = st.columns([2, 1])

    with col_map:
        st.markdown('<div class="section-header">State Entry Score Map</div>', unsafe_allow_html=True)
        map_metric = st.selectbox(
            "Colour map by",
            ["entry_score", "opportunity_score", "competitive_intensity"],
            format_func=lambda x: {
                "entry_score": "Entry Score",
                "opportunity_score": "Opportunity Score",
                "competitive_intensity": "Competitive Intensity (CII)",
            }[x],
        )
        fig_map = px.choropleth(
            mat,
            geojson=state_geo,
            locations="state_name",
            featureidkey="properties.name",
            color=map_metric,
            color_continuous_scale="Blues" if map_metric != "competitive_intensity" else "Reds",
            hover_name="state_name",
            hover_data={"entry_score": ":.3f", "opportunity_score": ":.3f",
                        "competitive_intensity": ":.3f", "quadrant": True},
            scope="north america",
        )
        fig_map.update_geos(
            fitbounds="locations", visible=False,
            lataxis_range=[14, 33], lonaxis_range=[-118, -86],
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="white",
            coloraxis_colorbar=dict(title="Score", thickness=12, len=0.6),
            height=360,
        )
        st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

    with col_quad:
        st.markdown('<div class="section-header">Quadrant Summary</div>', unsafe_allow_html=True)
        quad_counts = mat["quadrant"].value_counts()
        for quad in ["Priority", "Contested", "Monitor", "Avoid"]:
            count = quad_counts.get(quad, 0)
            descs = {
                "Priority":  "High opp + Low CII — enter now",
                "Contested": "High opp + High CII — differentiate",
                "Monitor":   "Low opp + Low CII — watch",
                "Avoid":     "Low opp + High CII — skip",
            }
            st.markdown(
                f'<div style="border-left:4px solid {QUAD_COLORS[quad]}; '
                f'padding:10px 14px; margin-bottom:10px; border-radius:4px; background:#f9f9f9;">'
                f'<b style="color:{QUAD_COLORS[quad]}">{quad}</b> &nbsp; '
                f'<span style="font-size:1.3rem; font-weight:700">{count}</span> states<br>'
                f'<span style="font-size:0.75rem; color:{GRAY}">{descs[quad]}</span></div>',
                unsafe_allow_html=True,
            )

    # Pipeline overview
    st.markdown("---")
    st.markdown('<div class="section-header">Three-Stage Analytical Pipeline</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    for col, nb, nb_title, col_hex, pts in [
        (p1, "NB01", "Customer Segmentation", TEAL,
         ["43,330 wholesale firms (Sector 43)",
          "K-Means on 6 features (Calinski-Harabasz k=4)",
          "4 customer tiers by strategic value",
          "State opportunity scores (0-1 normalised)"]),
        (p2, "NB02", "Competitive Intelligence", ORANGE,
         ["20,874 competitor firms (Sector 541)",
          "Keyword + override CSV classifier",
          "CII = Density·0.45 + Gini·0.20 + HHI·0.20 + CAGR·0.15",
          "State CII scores + municipality hotspots"]),
        (p3, "NB03", "Market Entry Framework", BLUE,
         ["2×2 matrix: median-split quadrants",
          "Entry Score = (0.7·Quality + 0.3·log-Vol) − 0.6·CII",
          "Full 32-state ranked table",
          "Municipality drill-down by C/C ratio"]),
    ]:
        pts_html = "".join(f"<li style='margin:4px 0; color:#555'>{p}</li>" for p in pts)
        col.markdown(
            f'<div style="border:2px solid {col_hex}; border-radius:8px; padding:16px; height:220px;">'
            f'<div style="color:{col_hex}; font-weight:700; font-size:0.8rem">{nb}</div>'
            f'<div style="font-weight:700; font-size:1rem; margin-bottom:10px">{nb_title}</div>'
            f'<ul style="padding-left:16px; font-size:0.8rem">{pts_html}</ul></div>',
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CUSTOMER SEGMENTATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Customer Segmentation":
    st.markdown('<div class="section-header">Customer Segmentation — NB01</div>', unsafe_allow_html=True)
    st.caption(
        "K-Means clustering on 43,330 wholesale-trade firms using 6 features. "
        "Calinski-Harabasz criterion selected optimal k; business floor k≥4 enforced."
    )

    # Tier cards
    tiers = [
        ("Tier 1 — Anchor", TEAL,
         "50+ employees · Full digital (email + web + phone)",
         "Highest — enterprise deals · Immediate priority"),
        ("Tier 2 — Growth", "#2196D3",
         "11–50 employees · Partial digital (2 of 3 channels)",
         "High — upsell potential · High priority"),
        ("Tier 3 — Emerging", ORANGE,
         "6–10 employees · Email only",
         "Medium — volume plays · Medium priority"),
        ("Tier 4+ — Micro", RED,
         "1–5 employees · Phone only or none",
         "Low — low deal value · Deprioritise"),
    ]
    cols = st.columns(4)
    for col, (t_name, t_col, t_profile, t_value) in zip(cols, tiers):
        col.markdown(
            f'<div style="border:2px solid {t_col}; border-radius:8px; padding:14px;">'
            f'<div style="color:{t_col}; font-weight:700; font-size:0.9rem; margin-bottom:8px">{t_name}</div>'
            f'<div style="font-size:0.78rem; color:#555; margin-bottom:8px">{t_profile}</div>'
            f'<div style="font-size:0.75rem; color:{GRAY}; border-top:1px solid #eee; padding-top:8px">{t_value}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_bar, col_scatter = st.columns([1.4, 1])

    with col_bar:
        st.markdown("#### Top States by Opportunity Score")
        top_n = st.slider("Show top N states", 5, 32, 15)
        opp_sorted = opp.nlargest(top_n, "opportunity_score")
        fig_bar = px.bar(
            opp_sorted,
            x="opportunity_score", y="state_name",
            orientation="h",
            color="opportunity_score",
            color_continuous_scale=[[0, "#BEE3F8"], [1, TEAL]],
            labels={"opportunity_score": "Opportunity Score", "state_name": ""},
            text="opportunity_score",
        )
        fig_bar.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        fig_bar.update_layout(
            height=min(60 * top_n, 700),
            showlegend=False,
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0, r=60, t=10, b=10),
            xaxis_range=[0, 1.12],
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    with col_scatter:
        st.markdown("#### Cluster Distribution (PCA)")
        tier_map = {1: "Tier 1", 2: "Tier 2", 3: "Tier 3", 4: "Tier 4+"}
        segs_sample = segs.sample(min(1500, len(segs)), random_state=42)
        segs_sample["Tier"] = segs_sample["tier"].map(tier_map).fillna("Tier 4+")
        tier_colors = {
            "Tier 1": TEAL, "Tier 2": "#2196D3", "Tier 3": ORANGE, "Tier 4+": RED
        }
        fig_pca = px.scatter(
            segs_sample, x="pca1", y="pca2", color="Tier",
            color_discrete_map=tier_colors,
            opacity=0.5, size_max=4,
            labels={"pca1": "PC1", "pca2": "PC2"},
        )
        fig_pca.update_traces(marker_size=3)
        fig_pca.update_layout(
            height=420, margin=dict(l=0, r=0, t=10, b=10),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_pca, use_container_width=True, config={"displayModeBar": False})

        st.markdown("#### Tier Breakdown")
        tier_counts = segs["tier"].value_counts().sort_index()
        tier_labels = [tier_map.get(t, f"Tier {t}") for t in tier_counts.index]
        fig_pie = px.pie(
            names=tier_labels,
            values=tier_counts.values,
            color=tier_labels,
            color_discrete_map=tier_colors,
            hole=0.45,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0),
                               showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — COMPETITIVE INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Competitive Intelligence":
    st.markdown('<div class="section-header">Competitive Intelligence — NB02</div>', unsafe_allow_html=True)
    st.caption(
        "Competitor Intensity Index (CII) built from 20,874 classified Sector 541 firms across 32 states."
    )

    # Formula
    st.markdown(
        '<div style="background:#0D2B45; border-radius:8px; padding:14px 20px; '
        'color:white; font-weight:700; font-size:1rem; text-align:center; margin-bottom:20px">'
        'CII = &nbsp; 0.45 × Density &nbsp; + &nbsp; 0.20 × Gini &nbsp; '
        '+ &nbsp; 0.20 × HHI &nbsp; + &nbsp; 0.15 × CAGR'
        '</div>',
        unsafe_allow_html=True,
    )

    # Metric cards
    m1, m2, m3, m4 = st.columns(4)
    for col, metric, weight, col_hex, why in [
        (m1, "Competitor Density", "0.45", TEAL,
         "Direct competitors per state. Most predictive of sales difficulty."),
        (m2, "Gini Coefficient", "0.20", "#2196D3",
         "Geographic concentration. High Gini = rivals in few cities; others open."),
        (m3, "HHI", "0.20", ORANGE,
         "Activity code concentration. High HHI = one type dominates; niche entry possible."),
        (m4, "CAGR 2019-24", "0.15", RED,
         "Competitor growth rate. Fast-growing markets attract more rivals."),
    ]:
        col.markdown(
            f'<div style="border:2px solid {col_hex}; border-radius:8px; padding:12px;">'
            f'<div style="font-size:0.7rem; font-weight:700; color:{col_hex}">w = {weight}</div>'
            f'<div style="font-weight:700; font-size:0.9rem; margin:4px 0">{metric}</div>'
            f'<div style="font-size:0.75rem; color:{GRAY}">{why}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### CII by State — Full Ranking")
        cii_sorted = cii.sort_values("competitive_intensity", ascending=False)
        fig_cii = px.bar(
            cii_sorted,
            x="competitive_intensity", y="state_name",
            orientation="h",
            color="competitive_intensity",
            color_continuous_scale=[[0, "#E0F7F5"], [0.5, ORANGE], [1, RED]],
            text="competitive_intensity",
            labels={"competitive_intensity": "CII", "state_name": ""},
        )
        fig_cii.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        fig_cii.update_layout(
            height=700, showlegend=False, coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0, r=60, t=10, b=10),
            xaxis_range=[0, 0.65],
        )
        st.plotly_chart(fig_cii, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown("#### CII Component Breakdown")
        selected_state = st.selectbox(
            "Select state to inspect",
            sorted(cii["state_name"].unique()),
        )
        row = cii[cii["state_name"] == selected_state].iloc[0]
        components = {
            "Density (w=0.45)": row["density_norm"] * 0.45,
            "Gini (w=0.20)":    row["gini_geo"] * 0.20 if "gini_geo" in row else 0,
            "HHI (w=0.20)":     row["hhi_norm"] * 0.20,
            "CAGR (w=0.15)":    row["cagr_norm"] * 0.15,
        }
        fig_comp = go.Figure(go.Bar(
            x=list(components.values()),
            y=list(components.keys()),
            orientation="h",
            marker_color=[TEAL, "#2196D3", ORANGE, RED],
            text=[f"{v:.3f}" for v in components.values()],
            textposition="outside",
        ))
        fig_comp.update_layout(
            height=250, margin=dict(l=0, r=60, t=10, b=10),
            xaxis_title="Weighted contribution to CII",
            xaxis_range=[0, max(components.values()) * 1.3 + 0.05],
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})

        # State summary
        total_cii = row["competitive_intensity"]
        cii_rank  = (cii["competitive_intensity"] >= total_cii).sum()
        st.metric("Total CII", f"{total_cii:.3f}", f"Rank #{cii_rank} of 32")

        st.markdown("#### Municipality Hotspots")
        state_munis = munis[munis["state_name"] == selected_state].copy()
        if not state_munis.empty:
            state_munis["hotspot"] = state_munis["is_hotspot"].map(
                {True: "Yes", False: "No", 1: "Yes", 0: "No"}
            )
            show_cols = ["municipality_name", "total_direct", "hotspot"]
            available = [c for c in show_cols if c in state_munis.columns]
            hotspot_df = state_munis[available].rename(columns={
                "municipality_name": "Municipality",
                "total_direct": "Direct Competitors",
                "hotspot": "Hotspot",
            }).sort_values("Direct Competitors", ascending=False).head(10)
            st.dataframe(hotspot_df, use_container_width=True, hide_index=True)
        else:
            st.info("No hotspot data available for this state.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — MARKET ENTRY MATRIX
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Market Entry Matrix":
    st.markdown('<div class="section-header">Market Opportunity Matrix — NB03</div>', unsafe_allow_html=True)
    st.caption(
        "All 32 states plotted on opportunity (x) vs. competitive intensity (y). "
        "Quadrant boundaries use data-driven median splits — not fixed thresholds."
    )

    opp_median = mat["opportunity_score"].median()
    cii_median = mat["competitive_intensity"].median()

    fig = px.scatter(
        mat,
        x="opportunity_score",
        y="competitive_intensity",
        color="quadrant",
        color_discrete_map=QUAD_COLORS,
        size="total_companies",
        size_max=40,
        hover_name="state_name",
        hover_data={
            "entry_score": ":.3f",
            "opportunity_score": ":.3f",
            "competitive_intensity": ":.3f",
            "total_companies": ":,",
            "quadrant": True,
        },
        text="state_name",
    )
    fig.update_traces(textposition="top center", textfont_size=9)

    # Quadrant dividers
    fig.add_hline(y=cii_median, line_dash="dot", line_color=GRAY, line_width=1.5,
                  annotation_text=f"CII median = {cii_median:.3f}",
                  annotation_position="right")
    fig.add_vline(x=opp_median, line_dash="dot", line_color=GRAY, line_width=1.5,
                  annotation_text=f"Opp median = {opp_median:.3f}",
                  annotation_position="top")

    # Quadrant labels
    for label, x, y in [
        ("PRIORITY",  0.85, 0.08),
        ("CONTESTED", 0.85, 0.38),
        ("MONITOR",   0.2,  0.08),
        ("AVOID",     0.2,  0.38),
    ]:
        fig.add_annotation(
            x=x, y=y, text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(color=QUAD_COLORS.get(label.title(), GRAY), size=13),
            xref="x", yref="y",
        )

    fig.update_layout(
        height=540,
        xaxis_title="Opportunity Score →",
        yaxis_title="Competitive Intensity (CII) →",
        legend=dict(orientation="h", y=-0.12, title=""),
        margin=dict(l=60, r=30, t=20, b=80),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Summary table
    st.markdown("---")
    st.markdown("#### All 32 States")
    display_mat = mat[[
        "entry_rank", "state_name", "quadrant",
        "opportunity_score", "competitive_intensity", "entry_score", "total_companies"
    ]].rename(columns={
        "entry_rank": "Rank", "state_name": "State", "quadrant": "Quadrant",
        "opportunity_score": "Opp Score", "competitive_intensity": "CII",
        "entry_score": "Entry Score", "total_companies": "Firms",
    }).sort_values("Rank")

    def color_quad(val):
        colors = {
            "Priority":  f"color: {TEAL}; font-weight:700",
            "Contested": f"color: {ORANGE}; font-weight:700",
            "Monitor":   f"color: {BLUE}; font-weight:700",
            "Avoid":     f"color: {RED}; font-weight:700",
        }
        return colors.get(val, "")

    st.dataframe(
        display_mat.style.format({
            "Opp Score": "{:.3f}", "CII": "{:.3f}", "Entry Score": "{:.3f}", "Firms": "{:,}"
        }).applymap(color_quad, subset=["Quadrant"]),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — ENTRY RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Entry Rankings":
    st.markdown('<div class="section-header">Market Entry Rankings — All 32 States</div>',
                unsafe_allow_html=True)
    st.caption(
        "Entry Score = (0.7 × Opportunity + 0.3 × log-Volume) − 0.6 × CII. "
        "Log-dampening prevents large-firm-count states from dominating."
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        quad_filter = st.multiselect(
            "Filter by quadrant",
            ["Priority", "Contested", "Monitor", "Avoid"],
            default=["Priority", "Contested"],
        )
    with col_f2:
        min_score = st.slider("Minimum entry score", 0.0, 0.75, 0.0, 0.05)

    mat_filt = mat[
        (mat["quadrant"].isin(quad_filter)) &
        (mat["entry_score"] >= min_score)
    ].sort_values("entry_rank")

    # Visual ranking bars — single px.bar call (much faster than per-trace loop)
    mat_filt = mat_filt.copy()
    mat_filt["label"] = "#" + mat_filt["entry_rank"].astype(int).astype(str) + "  " + mat_filt["state_name"]
    fig_rank = px.bar(
        mat_filt,
        x="entry_score",
        y="label",
        orientation="h",
        color="quadrant",
        color_discrete_map=QUAD_COLORS,
        text="entry_score",
        hover_name="state_name",
        hover_data={
            "quadrant": True,
            "entry_score": ":.3f",
            "opportunity_score": ":.3f",
            "competitive_intensity": ":.3f",
            "total_companies": ":,",
            "label": False,
        },
        labels={"entry_score": "Entry Score", "label": ""},
    )
    fig_rank.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig_rank.update_layout(
        height=max(400, 30 * len(mat_filt)),
        xaxis_range=[0, 0.85],
        margin=dict(l=200, r=60, t=10, b=10),
        yaxis=dict(autorange="reversed", categoryorder="array",
                   categoryarray=mat_filt.sort_values("entry_rank", ascending=False)["label"].tolist()),
        xaxis_title="Entry Score",
        bargap=0.3,
        legend=dict(orientation="h", y=-0.12, title=""),
    )
    st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar": False})

    # Entry score decomposition
    st.markdown("---")
    st.markdown("#### Entry Score Decomposition — Select State")
    sel_state = st.selectbox("State", mat.sort_values("entry_rank")["state_name"].tolist())
    row = mat[mat["state_name"] == sel_state].iloc[0]

    quality_contrib  = 0.7 * row["opportunity_score"]
    volume_contrib   = 0.3 * row["volume_norm"]
    cii_penalty      = 0.6 * row["competitive_intensity"]
    final_score      = quality_contrib + volume_contrib - cii_penalty

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Quality (0.7 × Opp)", f"+{quality_contrib:.3f}")
    d2.metric("Volume (0.3 × log-Vol)", f"+{volume_contrib:.3f}")
    d3.metric("CII Penalty (0.6 × CII)", f"−{cii_penalty:.3f}")
    d4.metric("Final Entry Score", f"{final_score:.3f}",
              f"Rank #{int(row['entry_rank'])} of 32")

    fig_decomp = go.Figure(go.Waterfall(
        x=["Quality\n(0.7×Opp)", "Volume\n(0.3×logVol)", "CII Penalty\n(−0.6×CII)", "Entry Score"],
        y=[quality_contrib, volume_contrib, -cii_penalty, 0],
        measure=["relative", "relative", "relative", "total"],
        text=[f"+{quality_contrib:.3f}", f"+{volume_contrib:.3f}",
              f"−{cii_penalty:.3f}", f"{final_score:.3f}"],
        textposition="outside",
        increasing=dict(marker_color=TEAL),
        decreasing=dict(marker_color=RED),
        totals=dict(marker_color=NAVY),
        connector=dict(line_color=GRAY, line_width=1),
    ))
    fig_decomp.update_layout(height=320, margin=dict(l=20, r=20, t=10, b=10),
                              showlegend=False, yaxis_title="Score contribution")
    st.plotly_chart(fig_decomp, use_container_width=True, config={"displayModeBar": False})

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — PRIORITY MARKETS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Priority Markets":
    st.markdown('<div class="section-header">Priority Market Deep-Dive</div>', unsafe_allow_html=True)
    st.caption(
        "Within each Priority-quadrant state, municipalities are ranked by C/C ratio "
        "(customer-to-competitor) — identifying sub-state pockets of high demand with "
        "minimal incumbent presence."
    )

    priority_states = mat[mat["quadrant"] == "Priority"].sort_values("entry_rank")

    sel_state = st.selectbox(
        "Select Priority state",
        priority_states["state_name"].tolist(),
        format_func=lambda s: f"#{int(mat[mat['state_name']==s]['entry_rank'].values[0])}  {s}",
    )

    state_row = priority_states[priority_states["state_name"] == sel_state].iloc[0]
    muni_data = prio[prio["state_name"] == sel_state].copy()

    # State headline metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Entry Score", f"{state_row['entry_score']:.3f}",
              f"Rank #{int(state_row['entry_rank'])} nationally")
    m2.metric("Total Firms", f"{state_row['total_companies']:,}")
    m3.metric("Opportunity Score", f"{state_row['opportunity_score']:.3f}")
    m4.metric("CII", f"{state_row['competitive_intensity']:.3f}",
              "Low competition" if state_row["competitive_intensity"] < 0.2 else "Moderate competition")

    st.markdown("---")

    if not muni_data.empty and "municipality_name" in muni_data.columns:
        muni_clean = muni_data[[
            "municipality_name", "customer_count", "competitor_count", "opportunity_ratio"
        ]].rename(columns={
            "municipality_name": "Municipality",
            "customer_count":    "Customers",
            "competitor_count":  "Competitors",
            "opportunity_ratio": "C/C Ratio",
        }).sort_values("C/C Ratio", ascending=False).dropna()

        col_table, col_chart = st.columns([1, 1.3])

        with col_table:
            st.markdown("#### Municipality Rankings by C/C Ratio")
            st.caption("C/C = Customer-to-Competitor ratio. Higher = better entry conditions.")

            def highlight_ratio(val):
                if isinstance(val, (int, float)):
                    if val >= 5:    return f"color: {GREEN}; font-weight:700"
                    elif val >= 3:  return f"color: {TEAL}; font-weight:700"
                    elif val >= 1:  return f"color: {ORANGE}"
                    else:           return f"color: {RED}"
                return ""

            st.dataframe(
                muni_clean.style.format({
                    "Customers": "{:.0f}", "Competitors": "{:.0f}", "C/C Ratio": "{:.2f}"
                }).applymap(highlight_ratio, subset=["C/C Ratio"]),
                use_container_width=True,
                hide_index=True,
                height=400,
            )

        with col_chart:
            st.markdown("#### Customer vs Competitor Presence")
            top_munis = muni_clean.head(12)

            fig_bubble = px.scatter(
                top_munis,
                x="Customers",
                y="C/C Ratio",
                size="Customers",
                size_max=40,
                color="C/C Ratio",
                color_continuous_scale=[[0, "#FFF3E0"], [0.5, TEAL], [1, GREEN]],
                hover_name="Municipality",
                text="Municipality",
                labels={"C/C Ratio": "C/C Ratio", "Customers": "Customer Firms"},
            )
            fig_bubble.update_traces(textposition="top center", textfont_size=9)
            fig_bubble.update_layout(
                height=360, margin=dict(l=20, r=20, t=10, b=10),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_bubble, use_container_width=True, config={"displayModeBar": False})

            # Top 3 highlight
            st.markdown("#### Top 3 Entry Points")
            for _, mrow in muni_clean.head(3).iterrows():
                ratio = mrow["C/C Ratio"]
                col_hex = GREEN if ratio >= 5 else (TEAL if ratio >= 3 else ORANGE)
                st.markdown(
                    f'<div style="border-left:4px solid {col_hex}; padding:8px 14px; '
                    f'margin-bottom:8px; border-radius:4px; background:#f9f9f9;">'
                    f'<b>{mrow["Municipality"]}</b> &nbsp; '
                    f'<span style="color:{col_hex}; font-weight:700">{ratio:.2f}:1</span> C/C ratio<br>'
                    f'<span style="font-size:0.75rem; color:{GRAY}">'
                    f'{int(mrow["Customers"])} customers · {int(mrow["Competitors"])} competitors</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("No sub-state municipality data available for this state. "
                "Entry opportunity is state-wide.")
        st.markdown(
            f'<div style="border:2px solid {TEAL}; border-radius:8px; padding:20px; text-align:center;">'
            f'<div style="font-size:1.2rem; font-weight:700; color:{TEAL}">State-wide Opportunity</div>'
            f'<div style="color:{GRAY}; margin-top:8px">No competitor concentration detected at sub-state level.<br>'
            f'Full {int(state_row["total_companies"]):,} firms accessible across the state.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Other Priority states summary
    st.markdown("---")
    st.markdown("#### All Priority States at a Glance")
    fig_prio = px.bar(
        priority_states,
        x="state_name", y="entry_score",
        color="entry_score",
        color_continuous_scale=[[0, "#BEE3F8"], [1, TEAL]],
        text="entry_score",
        labels={"entry_score": "Entry Score", "state_name": ""},
    )
    fig_prio.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig_prio.update_layout(
        height=300, coloraxis_showscale=False,
        yaxis_range=[0, 0.85],
        margin=dict(l=20, r=20, t=10, b=60),
    )
    st.plotly_chart(fig_prio, use_container_width=True, config={"displayModeBar": False})
