"""
streamlit_app.py — VitalTriage Priority Queue Dashboard

Run locally:
    cd backend
    streamlit run streamlit_app.py

Requires SUPABASE_URL and SUPABASE_KEY in a .env file (or environment).
Falls back to an in-memory heap if no Supabase credentials are found.
"""

import os
import time
import math
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

from heap_4ary import FourAryHeap

load_dotenv()

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VitalTriage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* background */
    .stApp { background-color: #080c14; color: #f3f4f6; }
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1f2937;
    }

    /* hide default Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid #1f2937;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: 1px solid #1f2937;
        border-radius: 8px 8px 0 0;
        color: #9ca3af;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(59,130,246,0.12) !important;
        border-color: #3b82f6 !important;
        color: #fff !important;
    }

    /* metric cards */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 0.6rem 1rem;
    }
    [data-testid="stMetricValue"] { color: #f3f4f6; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #9ca3af; font-size: 0.78rem; }

    /* primary button */
    .stButton > button[kind="primary"] {
        background: #3b82f6;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(59,130,246,0.4);
    }
    .stButton > button[kind="primary"]:hover {
        background: #2563eb;
        box-shadow: 0 6px 16px rgba(59,130,246,0.5);
    }

    /* slider thumb */
    [data-testid="stSlider"] .rc-slider-handle { border-color: #3b82f6; }
    [data-testid="stSlider"] .rc-slider-track  { background: #3b82f6; }

    /* form inputs */
    .stTextInput input, .stTextArea textarea {
        background: rgba(0,0,0,0.25) !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
        color: #f3f4f6 !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.25) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Supabase initialisation ───────────────────────────────────────────────────
@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if url and key:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception:
            return None
    return None


supabase = init_supabase()

# In-memory fallback — persists for the lifetime of the Streamlit session
if "fallback_heap" not in st.session_state:
    st.session_state.fallback_heap = FourAryHeap()


# ── Data layer ────────────────────────────────────────────────────────────────

# Real Supabase table columns:
#   id (uuid), patient_name, phone_number, symptoms, severity_score, created_at
# The heap and UI use normalised keys: name, priority, created_at, phone_number

def _normalise(row: dict) -> dict:
    """Map Supabase column names to the internal field names the app uses."""
    out = dict(row)
    out["name"]     = row.get("patient_name") or row.get("name", "Unknown")
    out["priority"] = int(row.get("severity_score") or row.get("priority") or 0)
    return out


def load_heap() -> FourAryHeap:
    """Fetch all records from urgent_care_calls and load into a fresh heap."""
    if supabase:
        try:
            resp = (
                supabase.table("urgent_care_calls")
                .select("*")
                .execute()
            )
            normalised = [_normalise(r) for r in resp.data]
            return FourAryHeap.build_from_list(normalised)
        except Exception as exc:
            st.warning(f"Supabase error — using in-memory fallback. ({exc})")
            return st.session_state.fallback_heap
    return st.session_state.fallback_heap


def db_add_patient(data: dict) -> None:
    """Insert a new call using the real column names."""
    if supabase:
        supabase.table("urgent_care_calls").insert({
            "patient_name":  data["name"],
            "phone_number":  data.get("phone_number", ""),
            "symptoms":      data.get("symptoms", ""),
            "severity_score": data["priority"],
        }).execute()
    else:
        st.session_state.fallback_heap.insert(data)


def db_delete_patient(patient_id: str) -> None:
    """Remove a processed call from the table (no status column exists)."""
    if supabase:
        supabase.table("urgent_care_calls").delete().eq("id", patient_id).execute()


# ── Colour helpers ────────────────────────────────────────────────────────────

def priority_tier(score: int) -> Tuple[str, str, str]:
    """Return (label, hex_colour, semi-transparent_bg) for a priority score."""
    if score >= 15:
        return "CRITICAL", "#ef4444", "rgba(239,68,68,0.12)"
    if score >= 8:
        return "MODERATE", "#f59e0b", "rgba(245,158,11,0.12)"
    return "LOW", "#10b981", "rgba(16,185,129,0.12)"


def format_wait(ts) -> str:
    """Accept either an ISO datetime string or epoch-ms integer."""
    try:
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            mins = max(0, int((datetime.now(timezone.utc) - dt).total_seconds() / 60))
        else:
            mins = max(0, int((time.time() * 1000 - int(ts)) / 60_000))
    except Exception:
        return "unknown"
    if mins < 1:
        return "< 1 min"
    if mins < 60:
        return f"{mins} min"
    return f"{mins // 60}h {mins % 60}m"


# ── Plotly tree builder ───────────────────────────────────────────────────────

def _compute_positions(n: int) -> Dict[int, Tuple[float, float]]:
    """
    Recursively assign (x, y) display coordinates.
    Root → (0.5, 0).  Each subtree gets an equal horizontal slice.
    y = −depth so the root renders at the top in Plotly's default orientation.
    """
    positions: dict[int, tuple[float, float]] = {}

    def _recurse(i: int, depth: int, left: float, right: float) -> None:
        if i >= n:
            return
        positions[i] = ((left + right) / 2.0, float(-depth))
        slot = (right - left) / 4.0
        for k in range(1, 5):
            _recurse(4 * i + k, depth + 1, left + (k - 1) * slot, left + k * slot)

    _recurse(0, 0, 0.0, 1.0)
    return positions


def build_heap_figure(heap_array: list[dict]) -> go.Figure:
    """Return a Plotly Figure visualising the 4-ary max-heap tree."""
    if not heap_array:
        fig = go.Figure()
        fig.add_annotation(
            text="Queue is empty — admit a patient to see the tree",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=16, color="#6b7280"),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=340,
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            margin=dict(l=0, r=0, t=0, b=0),
        )
        return fig

    n = len(heap_array)
    pos = _compute_positions(n)
    max_depth = int(max(-v[1] for v in pos.values()))

    # ── Edge trace ────────────────────────────────────────────────────────────
    ex: list = []
    ey: list = []
    for i in range(n):
        for k in range(1, 5):
            c = 4 * i + k
            if c < n:
                x0, y0 = pos[i]
                x1, y1 = pos[c]
                ex += [x0, x1, None]
                ey += [y0, y1, None]

    # ── Node attributes ───────────────────────────────────────────────────────
    xs = [pos[i][0] for i in range(n)]
    ys = [pos[i][1] for i in range(n)]
    node_colors = [priority_tier(heap_array[i].get("priority", 0))[1] for i in range(n)]
    node_text   = [str(heap_array[i].get("priority", "?")) for i in range(n)]
    hover_text  = [
        (
            f"<b>{heap_array[i].get('name', 'Unknown')}</b><br>"
            f"Severity : {heap_array[i].get('priority', 0)}/20<br>"
            f"Phone    : {heap_array[i].get('phone_number', 'N/A')}<br>"
            f"Symptoms : {heap_array[i].get('symptoms', 'N/A')}<br>"
            f"Heap idx : {i}  |  depth : {int(-pos[i][1])}"
        )
        for i in range(n)
    ]

    fig = go.Figure()

    # edges
    fig.add_trace(go.Scatter(
        x=ex, y=ey, mode="lines",
        line=dict(width=1.5, color="rgba(255,255,255,0.18)"),
        hoverinfo="none",
    ))

    # node fill circles
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        marker=dict(
            size=38,
            color=node_colors,
            opacity=0.88,
            line=dict(width=2, color="rgba(255,255,255,0.22)"),
        ),
        text=node_text,
        textfont=dict(size=12, color="white", family="monospace"),
        textposition="middle center",
        hovertext=hover_text,
        hoverinfo="text",
        hoverlabel=dict(bgcolor="#1f2937", bordercolor="#374151",
                        font=dict(color="white", size=12)),
    ))

    # white ring on root to mark it as max
    fig.add_trace(go.Scatter(
        x=[xs[0]], y=[ys[0]],
        mode="markers",
        marker=dict(size=50, color="rgba(0,0,0,0)",
                    line=dict(width=3, color="white")),
        hoverinfo="skip",
    ))

    # depth-level labels on left margin
    seen_depths: set = set()
    for i in range(n):
        d = int(-pos[i][1])
        if d not in seen_depths:
            seen_depths.add(d)
            fig.add_annotation(
                x=-0.015, y=pos[i][1], xref="x", yref="y",
                text=f"L{d}",
                showarrow=False,
                font=dict(size=9, color="#4b5563"),
                xanchor="right",
            )

    fig.update_layout(
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(360, max_depth * 110 + 160),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.06, 1.06]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=45, r=20, t=30, b=20),
        font=dict(color="white"),
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 VitalTriage")
    st.caption("4-ary Max-Heap Priority Queue")

    # Live stats (loaded once per rerun)
    _heap_sb = load_heap()
    _queue_sb = _heap_sb.get_sorted_patients()

    c1, c2 = st.columns(2)
    c1.metric("In Queue", _heap_sb.size)
    c2.metric(
        "Top Priority",
        f"{_queue_sb[0]['priority']}/20" if _queue_sb else "—",
    )

    st.divider()
    st.markdown("#### Admit Patient")

    with st.form("admit_form", clear_on_submit=True):
        p_name     = st.text_input("Patient Name", placeholder="Full name")
        p_phone    = st.text_input("Phone Number", placeholder="e.g. 720-473-1234")
        p_priority = st.slider("Severity  (1 = minor  ·  20 = critical)", 1, 20, 10)
        p_symptoms = st.text_area("Symptoms", placeholder="Describe presenting symptoms", height=90)
        submitted  = st.form_submit_button("Admit →", use_container_width=True, type="primary")

        if submitted:
            if not p_name.strip():
                st.error("Patient name is required.")
            else:
                new_patient = {
                    "name":         p_name.strip(),
                    "phone_number": p_phone.strip(),
                    "priority":     p_priority,
                    "symptoms":     p_symptoms.strip(),
                }
                try:
                    db_add_patient(new_patient)
                    st.success(f"Admitted — {p_name} (P{p_priority}/20)")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")

    st.divider()

    if _queue_sb:
        next_name = _queue_sb[0]["name"]
        if st.button(
            f"✓  Process Next  ({next_name})",
            use_container_width=True,
        ):
            h = load_heap()
            processed = h.extract_max()
            if processed:
                try:
                    db_delete_patient(processed["id"])
                    st.success(f"Processed: {processed['name']}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")
    else:
        st.info("Queue is empty")

    st.divider()
    if not supabase:
        st.warning("No Supabase credentials — running in in-memory mode")
    else:
        st.success("Connected to Supabase")


# ── Main content ──────────────────────────────────────────────────────────────
heap  = load_heap()
queue = heap.get_sorted_patients()

tab_queue, tab_tree = st.tabs(["  Priority Queue  ", "  Heap Tree  "])


# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Priority Queue
# ══════════════════════════════════════════════════════════════════════════════
with tab_queue:
    if not queue:
        st.info("No active patients in the queue. Admit one using the sidebar →")
    else:
        # ── Next-Up hero card ─────────────────────────────────────────────────
        nxt = queue[0]
        lbl, clr, bg = priority_tier(nxt["priority"])
        pct = int((nxt["priority"] / 20) * 100)
        wait_str = format_wait(nxt.get("created_at", nxt.get("timestamp", int(time.time() * 1000))))
        syms_full = nxt.get("symptoms") or "No symptoms reported"

        st.markdown(
            f"""
            <div style="
                background:{bg};
                border:2px solid {clr};
                border-radius:16px;
                padding:1.6rem 2rem;
                margin-bottom:1.5rem;
                position:relative;
            ">
              <div style="
                font-size:0.65rem; font-weight:800; letter-spacing:0.15em;
                color:{clr}; text-transform:uppercase; margin-bottom:0.45rem;
              ">▶ NEXT UP</div>

              <div style="font-size:2rem; font-weight:700; margin-bottom:0.1rem;">
                {nxt['name']}
              </div>

              <div style="display:flex; align-items:center; gap:0.8rem; margin:0.55rem 0;">
                <span style="
                  font-size:0.72rem; font-weight:700; color:{clr};
                  background:rgba(0,0,0,0.3); border-radius:99px;
                  padding:0.15rem 0.75rem; text-transform:uppercase;
                  border:1px solid {clr};
                ">{lbl} · {nxt['priority']}/20</span>
                <span style="color:#9ca3af; font-size:0.8rem;">Wait: {wait_str}</span>
              </div>

              <!-- severity bar -->
              <div style="height:6px; background:rgba(0,0,0,0.35); border-radius:99px; margin:0.65rem 0;">
                <div style="height:100%; width:{pct}%; background:{clr}; border-radius:99px;"></div>
              </div>

              <div style="color:#d1d5db; font-size:0.95rem; margin-top:0.5rem;">
                {syms_full}
              </div>
              {f'<div style="color:#6b7280; font-size:0.8rem; margin-top:0.4rem;">📞 {nxt["phone_number"]}</div>' if nxt.get("phone_number") else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Full queue list ───────────────────────────────────────────────────
        st.markdown(f"#### All Patients in Queue &nbsp; `{len(queue)}`",
                    unsafe_allow_html=True)

        for rank, p in enumerate(queue, 1):
            lbl_r, clr_r, bg_r = priority_tier(p["priority"])
            wait_r  = format_wait(p.get("created_at") or p.get("timestamp", int(time.time() * 1000)))
            name_r  = p.get("name", "Unknown")
            phone_r = p.get("phone_number", "")
            syms_r  = (p.get("symptoms") or "No symptoms")
            if len(syms_r) > 65:
                syms_r = syms_r[:65] + "…"

            highlight_border = "rgba(239,68,68,0.45)" if rank == 1 else "#1f2937"
            highlight_bg     = "rgba(239,68,68,0.05)" if rank == 1 else "rgba(255,255,255,0.02)"

            st.markdown(
                f"""
                <div style="
                    display:flex; align-items:center; gap:1rem;
                    padding:0.85rem 1.2rem; border-radius:12px;
                    border:1px solid {highlight_border};
                    background:{highlight_bg};
                    margin-bottom:0.5rem;
                ">
                  <span style="color:#6b7280; font-size:0.75rem; width:22px; flex-shrink:0;">
                    #{rank}
                  </span>
                  <span style="flex:0 0 170px; font-weight:600; white-space:nowrap;
                               overflow:hidden; text-overflow:ellipsis;">
                    {name_r}
                    {f'<span style="display:block;font-size:0.7rem;font-weight:400;color:#6b7280;">{phone_r}</span>' if phone_r else ""}
                  </span>
                  <span style="flex:1; font-size:0.84rem; color:#9ca3af;
                               white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {syms_r}
                  </span>
                  <span style="
                    padding:0.15rem 0.7rem; border-radius:99px;
                    font-size:0.7rem; font-weight:700;
                    color:{clr_r}; background:rgba(0,0,0,0.3);
                    border:1px solid {clr_r}; flex-shrink:0;
                    text-transform:uppercase; letter-spacing:0.04em;
                  ">{lbl_r}&nbsp;{p['priority']}/20</span>
                  <span style="color:#6b7280; font-size:0.78rem;
                               flex-shrink:0; width:68px; text-align:right;">
                    {wait_r}
                  </span>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Heap Tree
# ══════════════════════════════════════════════════════════════════════════════
with tab_tree:
    st.markdown("#### 4-ary Max-Heap Tree")
    st.caption(
        "Each node holds up to **4 children**.  "
        "The heap property guarantees every parent's priority ≥ its children's, "
        "so the **root (white ring) always holds the most urgent patient**.  "
        "Node labels show the priority score; hover for full patient details."
    )

    fig = build_heap_figure(heap.heap)
    st.plotly_chart(fig, use_container_width=True)

    # ── Colour legend ─────────────────────────────────────────────────────────
    lc1, lc2, lc3 = st.columns(3)
    for col, (label, clr, bg) in zip(
        [lc1, lc2, lc3],
        [
            ("CRITICAL", "#ef4444", "rgba(239,68,68,0.12)"),
            ("MODERATE", "#f59e0b", "rgba(245,158,11,0.12)"),
            ("LOW",      "#10b981", "rgba(16,185,129,0.12)"),
        ],
    ):
        with col:
            st.markdown(
                f'<div style="background:{bg}; border:1px solid {clr}; border-radius:8px;'
                f' padding:0.55rem 1rem; text-align:center;">'
                f'<b style="color:{clr}">{label}</b><br>'
                f'<span style="color:#9ca3af; font-size:0.78rem;">'
                f'{"15–20" if label == "CRITICAL" else "8–14" if label == "MODERATE" else "1–7"}'
                f'</span></div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Heap array view ───────────────────────────────────────────────────────
    st.markdown("#### Underlying Heap Array")
    st.caption(
        "The heap lives in a flat Python list.  "
        "**Parent of index i → `(i−1) // 4`.**  "
        "**Children of index i → `4i+1`, `4i+2`, `4i+3`, `4i+4`.**  "
        "Each cell below shows `[index]`, priority score, and the first 8 chars of the name."
    )

    if heap.heap:
        # Show up to 8 cells per row
        COLS = 8
        rows = math.ceil(len(heap.heap) / COLS)
        for row in range(rows):
            cols = st.columns(COLS)
            for k in range(COLS):
                idx = row * COLS + k
                if idx >= len(heap.heap):
                    break
                p = heap.heap[idx]
                _, clr_a, bg_a = priority_tier(p.get("priority", 0))
                with cols[k]:
                    st.markdown(
                        f'<div style="background:{bg_a}; border:1px solid {clr_a};'
                        f' border-radius:8px; padding:0.45rem 0.3rem; text-align:center;'
                        f' margin-bottom:0.4rem;">'
                        f'<div style="font-size:0.62rem; color:#9ca3af;">[{idx}]</div>'
                        f'<div style="font-size:1.15rem; font-weight:700; color:{clr_a};">'
                        f'{p.get("priority","?")}</div>'
                        f'<div style="font-size:0.62rem; color:#d1d5db; white-space:nowrap;'
                        f' overflow:hidden; text-overflow:ellipsis;">'
                        f'{p.get("name","?")[:8]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.info("Heap array is empty.")

    st.divider()

    # ── Depth levels ──────────────────────────────────────────────────────────
    st.markdown("#### Level-by-Level Breakdown")
    st.caption("Each row below is one depth level of the heap tree.")

    levels = heap.depth_levels()
    if levels:
        for d, level in enumerate(levels):
            max_p   = max(p.get("priority", 0) for p in level)
            _, clr_d, _ = priority_tier(max_p)
            names   = ", ".join(p.get("name") or p.get("patient_name", "?") for p in level)
            scores  = " · ".join(str(p.get("priority", "?")) for p in level)
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:1rem;'
                f' padding:0.6rem 1rem; border-radius:10px;'
                f' border:1px solid #1f2937; background:rgba(255,255,255,0.02);'
                f' margin-bottom:0.4rem;">'
                f'<span style="color:#6b7280; font-size:0.75rem; width:48px; flex-shrink:0;">'
                f'Level {d}</span>'
                f'<span style="flex:1; font-size:0.85rem; color:#d1d5db;">{names}</span>'
                f'<span style="font-family:monospace; font-size:0.8rem; color:{clr_d};">'
                f'{scores}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No data to display.")
