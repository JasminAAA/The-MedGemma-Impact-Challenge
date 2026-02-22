import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from medgemma_client import MedGemmaClient
from pipeline import NeuroBriefPipeline

# -------------------------
# Configuration
# -------------------------

USE_REAL_MODEL = st.sidebar.checkbox(
    "🧠 Use Real MedGemma (requires GPU)",
    value=False,  # DEFAULT TO FALSE - DEMO MODE WORKS INSTANTLY
    help="Enable to use actual MedGemma 1.5 model. Disable for faster demo mode."
)


# -------------------------
# Utility Functions
# -------------------------

def load_case(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_severity_badge(scale, score):
    """Return color-coded severity badge for clinical assessments"""
    if scale == "PHQ-9":
        if score >= 20:
            return "🔴 Severe"
        elif score >= 15:
            return "🟠 Moderately Severe"
        elif score >= 10:
            return "🟡 Moderate"
        elif score >= 5:
            return "🟢 Mild"
        else:
            return "⚪ Minimal"
    elif scale == "GAD-7":
        if score >= 15:
            return "🔴 Severe"
        elif score >= 10:
            return "🟠 Moderate"
        elif score >= 5:
            return "🟡 Mild"
        else:
            return "⚪ Minimal"
    return ""


def build_timeline(events, assessments, flags):
    items = []

    for event in events:
        items.append(
            {
                "date": event["date"],
                "type": event["type"],
                "label": event["label"],
                "excerpt": event["excerpt"],
                "source_id": event["source_id"],
            }
        )

    for assessment in assessments:
        severity = get_severity_badge(assessment["scale"], assessment["score"])
        items.append(
            {
                "date": assessment["date"],
                "type": "assessment",
                "label": f"{assessment['scale']} {assessment['score']} {severity}",
                "excerpt": assessment.get("excerpt", ""),
                "source_id": assessment.get("source_id", "assessment"),
            }
        )

    if not items:
        return None

    df = pd.DataFrame(items)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Professional clinical color scheme
    color_map = {
        "medication": "#2E86AB",  # Professional blue
        "symptom": "#A23B72",  # Muted red
        "assessment": "#2A9D8F",  # Teal
        "therapy": "#8B5FBF",  # Calming purple
        "test": "#E76F51",  # Warm orange
    }

    fig = go.Figure()

    # Add timeline markers with better styling
    for _, row in df.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["date"]],
                y=[row["label"]],
                mode="markers",
                marker=dict(
                    size=12,
                    color=color_map.get(row["type"], "#333"),
                    line=dict(width=2, color='white')
                ),
                name=row["type"],
                hovertemplate=(
                    f"<b>{row['label']}</b><br>"
                    f"Date: {row['date'].date()}<br>"
                    f"Excerpt: {row['excerpt']}<br>"
                    f"Source: {row['source_id']}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # Add uncertainty windows
    for flag in flags:
        try:
            start = pd.to_datetime(flag["window_start"])
            end = pd.to_datetime(flag["window_end"])

            fig.add_vrect(
                x0=start,
                x1=end,
                fillcolor="orange",
                opacity=0.15,
                layer="below",
                line_width=0,
                annotation_text="⚠️ Attribution Uncertainty",
                annotation_position="top left",
            )
        except Exception:
            continue

    fig.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="Date",
        yaxis_title="Clinical Events",
        yaxis=dict(autorange="reversed"),
        plot_bgcolor='rgba(248,249,250,0.8)',
    )

    return fig


# -------------------------
# Main App
# -------------------------

def main():
    st.set_page_config(
        page_title="NeuroBrief",
        page_icon="🧠",
        layout="wide"
    )

    # Custom CSS for professional styling
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
        }
        h1 {
            color: #2E86AB !important;
        }
        h2, h3 {
            color: #2A9D8F !important;
        }
        .stMetric {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    # Professional header
    st.title("🧠 NeuroBrief")

    st.markdown("""
    <div style='background: linear-gradient(90deg, #2E86AB 0%, #2A9D8F 100%); 
                padding: 1.5rem; 
                border-radius: 10px; 
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h3 style='color: white; margin: 0; font-weight: 600;'>
            Clinical Documentation Intelligence for Psychiatric Care
        </h3>
        <p style='color: #E8F4F8; margin: 0.5rem 0 0 0; font-size: 0.95rem;'>
            Transforming fragmented notes into structured clinical timelines
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("🔬 Demo-only. Synthetic data. No PHI.")

    # Display mode indicator
    if USE_REAL_MODEL:
        st.success("🧠 Powered by MedGemma 1.5 - Medical AI Language Model")
    else:
        st.info("⚡ Demo Mode: Optimized heuristic extraction (fast, no GPU required)")

    data_dir = Path(__file__).parent / "synthetic_data"
    case_files = sorted(data_dir.glob("*.json"))

    if not case_files:
        st.error("No synthetic cases found.")
        return

    case_names = [path.stem for path in case_files]
    selection = st.selectbox("📁 Select synthetic case", case_names)
    case_path = data_dir / f"{selection}.json"

    if st.button("▶️ Run Agentic Pipeline", type="primary") or "result" not in st.session_state:
        case_data = load_case(case_path)
        notes = case_data["notes"]

        with st.spinner("🔄 Processing with agentic pipeline..."):
            # Cache client to avoid reloading (only matters for MedGemma mode)
            if "client" not in st.session_state or st.session_state.get("model_mode") != USE_REAL_MODEL:
                st.session_state.client = MedGemmaClient(use_real_model=USE_REAL_MODEL)
                st.session_state.model_mode = USE_REAL_MODEL

            client = st.session_state.client
            pipeline = NeuroBriefPipeline(client)
            st.session_state.result = pipeline.process_case(notes)
            st.session_state.case_data = case_data

    result = st.session_state.get("result")
    case_data = st.session_state.get("case_data")

    if not result or not case_data:
        return

    # Main content area
    col_left, col_right = st.columns([2, 1])

    # -------------------------
    # LEFT COLUMN - Timeline
    # -------------------------
    with col_left:
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Timeline View", "💊 Medications", "📈 Outcomes"])

        with tab1:
            st.markdown("### 📊 Longitudinal Clinical Timeline")

            fig = build_timeline(
                result["events"],
                result["assessments"],
                result["flags"],
            )

            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timeline events detected.")

        with tab2:
            st.markdown("### 💊 Medication History")
            meds = [e for e in result["events"] if e["type"] == "medication"]

            if meds:
                for med in meds:
                    with st.expander(f"💊 {med['label']} - Started {med['date']}"):
                        st.write(f"**Source:** {med['excerpt']}")
                        st.caption(f"📄 Note ID: {med['source_id']}")
            else:
                st.info("No medications documented in this case.")

        with tab3:
            st.markdown("### 📈 Assessment Trajectory")

            if result["assessments"]:
                # Group by scale
                scales = list(set([a["scale"] for a in result["assessments"]]))

                for scale in scales:
                    scale_assessments = [a for a in result["assessments"] if a["scale"] == scale]

                    if len(scale_assessments) >= 2:
                        df_assess = pd.DataFrame(scale_assessments)
                        df_assess["date"] = pd.to_datetime(df_assess["date"])
                        df_assess = df_assess.sort_values("date")

                        fig = px.line(
                            df_assess,
                            x="date",
                            y="score",
                            title=f"{scale} Trajectory",
                            markers=True
                        )
                        fig.update_traces(line_color='#2A9D8F', marker_size=10)
                        fig.update_layout(plot_bgcolor='rgba(248,249,250,0.8)')
                        st.plotly_chart(fig, use_container_width=True)

                        # Show trend
                        first_score = df_assess.iloc[0]["score"]
                        last_score = df_assess.iloc[-1]["score"]
                        change = last_score - first_score

                        if change < -5:
                            st.success(f"✅ Significant improvement: {abs(change)} points")
                        elif change > 5:
                            st.error(f"⚠️ Worsening symptoms: +{change} points")
                        else:
                            st.info(f"→ Stable: {abs(change)} point change")
            else:
                st.info("No assessment scores documented.")

        st.markdown("### 📝 Pre-Session Brief")
        st.write(result["summary"])

    # -------------------------
    # RIGHT COLUMN - Metrics & Details
    # -------------------------
    with col_right:
        st.markdown("### 📋 Case Summary")

        # Metrics
        meds = [e for e in result["events"] if e["type"] == "medication"]
        symptoms = [e for e in result["events"] if e["type"] == "symptom"]
        therapy = [e for e in result["events"] if e["type"] == "therapy"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💊 Meds", len(meds))
        with col2:
            st.metric("🩺 Symptoms", len(symptoms))
        with col3:
            st.metric("🧘 Therapy", len(therapy))

        # Attribution Uncertainty
        st.markdown("### ⚠️ Attribution Uncertainty")

        if result["flags"]:
            for idx, flag in enumerate(result["flags"]):
                with st.expander(
                        f"⚠️ {flag['scale']} change on {flag['date']} "
                        f"({flag['previous_score']} → {flag['current_score']})",
                        expanded=(idx == 0)  # Expand first flag
                ):
                    st.write(flag["explanation"])

                    st.markdown("**Interventions in window:**")
                    for intervention in flag["interventions"]:
                        st.write(
                            f"- 📅 {intervention['date']} | "
                            f"{intervention['type'].title()} | "
                            f"**{intervention['label']}**"
                        )
        else:
            st.success("✅ No attribution uncertainty detected.")

        # Clinical Insights
        if len(result["assessments"]) >= 2:
            st.markdown("### 💡 Clinical Insights")

            first = result["assessments"][0]
            last = result["assessments"][-1]

            if first["scale"] == last["scale"]:
                change = last['score'] - first['score']

                with st.expander("Treatment Response Pattern", expanded=True):
                    if change < -5:
                        st.success(f"✅ Significant improvement detected")
                        st.write(f"{first['scale']}: {first['score']} → {last['score']} ({change} points)")
                    elif change > 5:
                        st.warning(f"⚠️ Symptom worsening detected")
                        st.write(f"{first['scale']}: {first['score']} → {last['score']} (+{change} points)")
                    else:
                        st.info(f"→ Relatively stable presentation")
                        st.write(f"{first['scale']}: {first['score']} → {last['score']} ({abs(change)} point change)")

        # Source Traceability
        st.markdown("### 🔍 Source Traceability")

        notes_by_id = {
            note["note_id"]: note["text"] for note in case_data["notes"]
        }

        event_labels = {}
        for event in result["events"]:
            key = f"{event['date']} | {event['type']} | {event['label']}"
            event_labels[key] = event

        if event_labels:
            selected = st.selectbox(
                "Select event to view source note",
                list(event_labels.keys()),
                label_visibility="collapsed"
            )
            event = event_labels[selected]
            source_text = notes_by_id.get(
                event["source_id"], "Source note not found."
            )

            st.code(source_text, language="text")
        else:
            st.info("No events available for traceability.")


if __name__ == "__main__":
    main()