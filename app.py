"""Streamlit dashboard for the NovaMind content pipeline."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
from html import escape

from config import PERSONAS, ensure_directories
from services.workflow_runner import run_workflow


DEFAULT_TOPIC = "AI automation for small creative agencies"


def main() -> None:
    """Render the Streamlit dashboard and run the workflow on demand."""
    st.set_page_config(page_title="NovaMind Content Pipeline", page_icon="NM", layout="wide")
    st.markdown(
        """
        <style>
        div[data-testid="stDecoration"] {
            background-image: linear-gradient(90deg, #EC4899, #7C3AED, #4F8DFD);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    ensure_directories()

    st.title("NovaMind Content Pipeline")
    st.caption("AI-powered content generation, CRM/email workflow simulation, performance analysis, and optimization.")

    with st.sidebar:
        st.header("Run Workflow")
        topic = st.text_area("Blog topic", value=DEFAULT_TOPIC, height=90)
        send_emails = st.checkbox("Send emails through Brevo", value=False)
        st.caption("Safe demo default: emails are not sent unless this is checked.")
        run_clicked = st.button("Run Workflow", type="primary", use_container_width=True)

    if run_clicked:
        with st.spinner("Running the NovaMind workflow..."):
            try:
                st.session_state["workflow_result"] = run_workflow(topic, send_emails=send_emails)
                st.success("Workflow completed successfully.")
            except Exception as exc:
                st.error(f"Workflow failed: {exc}")

    result = st.session_state.get("workflow_result")
    if not result:
        st.info("Enter a topic in the sidebar and click **Run Workflow** to generate the latest campaign.")
        return

    render_run_metadata(result)

    content_tab, performance_tab, summary_tab, optimization_tab = st.tabs(
        ["Content", "Performance", "Summary", "Optimization"]
    )
    with content_tab:
        render_content_results(result["content"])
        render_newsletters(result["content"])
    with performance_tab:
        render_performance(result)
    with summary_tab:
        render_summary(result)
    with optimization_tab:
        render_recommendations(result)


def render_run_metadata(result: dict) -> None:
    """Show quick run status cards."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Contacts", result["contact_count"])
    col2.metric("Content Mode", result["generation_mode"])
    col3.metric("Model", result["model"])
    col4.metric("CRM Provider", result["crm_provider"])

    st.caption(
        f"Latest run: {result['latest_run_timestamp']} | "
        f"Email sending: {'enabled' if result['send_emails'] else 'disabled'}"
    )

    with st.expander("Contact Distribution", expanded=True):
        dist_cols = st.columns(len(PERSONAS))
        for index, persona in enumerate(PERSONAS):
            dist_cols[index].metric(persona, result["persona_distribution"].get(persona, 0))
        list_rows = [
            {
                "Persona": entry.get("persona", ""),
                "Brevo List ID": entry.get("brevo_list_id", ""),
                "Contacts": entry.get("total_contacts", 0),
                "Send Status": entry.get("brevo_send_status", ""),
            }
            for entry in result.get("crm_result", {}).get("campaign_entries", [])
        ]
        if list_rows:
            st.dataframe(pd.DataFrame(list_rows), use_container_width=True, hide_index=True)


def render_content_results(content: dict) -> None:
    """Render blog content and title options."""
    st.subheader("Generated Blog")
    st.markdown(f"### {content.get('blog_title', 'Untitled blog')}")

    with st.expander("Blog Title Options", expanded=True):
        for title in content.get("blog_title_options", []):
            st.write(f"- {title}")

    with st.expander("Blog Draft Preview", expanded=True):
        draft = content.get("blog_draft", "")
        preview = draft[:1400] + ("..." if len(draft) > 1400 else "")
        st.markdown(
            f"""
            <div style="
                background: #F8FAFC;
                color: #1F2937;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                padding: 18px 20px;
                max-height: 360px;
                overflow-y: auto;
                white-space: pre-wrap;
                line-height: 1.65;
                font-size: 0.96rem;
            ">{escape(preview)}</div>
            """,
            unsafe_allow_html=True,
        )


def render_newsletters(content: dict) -> None:
    """Render selected persona newsletters and copy options."""
    st.subheader("Persona Newsletters")
    newsletters = content.get("newsletters", [])
    for newsletter in newsletters:
        persona = newsletter.get("persona", "Unknown persona")
        with st.expander(persona, expanded=True):
            st.markdown(f"**Selected subject:** {newsletter.get('subject_line', '')}")
            st.markdown(f"**Preview text:** {newsletter.get('preview_text', '')}")
            st.write(newsletter.get("body", ""))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Subject line options**")
                for subject in newsletter.get("subject_line_options", []):
                    st.write(f"- {subject}")
            with col2:
                st.markdown("**Preview text options**")
                for preview in newsletter.get("preview_text_options", []):
                    st.write(f"- {preview}")


def render_performance(result: dict) -> None:
    """Render performance metrics and a grouped horizontal chart."""
    st.subheader("Performance Snapshot")
    metrics = result.get("metrics", [])
    if not metrics:
        st.warning("No performance metrics were generated.")
        return

    metric_cols = st.columns(len(metrics))
    for index, record in enumerate(metrics):
        persona = record.get("persona", "Unknown")
        open_rate = record.get("modeled_open_rate", record.get("open_rate", 0.0))
        click_rate = record.get("modeled_click_rate", record.get("click_rate", 0.0))
        unsub_rate = record.get("modeled_unsubscribe_rate", record.get("unsubscribe_rate", 0.0))
        with metric_cols[index]:
            st.metric(f"{persona} Open", f"{open_rate:.1%}")
            st.caption(f"Click: {click_rate:.1%} | Unsub: {unsub_rate:.1%}")

    chart_rows = []
    for record in metrics:
        persona = record.get("persona", "Unknown")
        chart_rows.extend(
            [
                {
                    "Persona": persona,
                    "Metric": "Open rate",
                    "Rate": record.get("modeled_open_rate", record.get("open_rate", 0.0)),
                },
                {
                    "Persona": persona,
                    "Metric": "Click rate",
                    "Rate": record.get("modeled_click_rate", record.get("click_rate", 0.0)),
                },
                {
                    "Persona": persona,
                    "Metric": "Unsubscribe rate",
                    "Rate": record.get("modeled_unsubscribe_rate", record.get("unsubscribe_rate", 0.0)),
                },
            ]
        )

    chart_df = pd.DataFrame(chart_rows)
    fig = px.bar(
        chart_df,
        x="Rate",
        y="Persona",
        color="Metric",
        orientation="h",
        barmode="group",
        text=chart_df["Rate"].map(lambda value: f"{value:.1%}"),
        color_discrete_map={
            "Open rate": "#4F8DFD",
            "Click rate": "#7C3AED",
            "Unsubscribe rate": "#EC4899",
        },
    )
    fig.update_layout(
        xaxis_tickformat=".0%",
        xaxis_title="Modeled rate",
        yaxis_title="",
        legend_title="Metric",
        height=360,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Metric Details", expanded=False):
        detail_rows = [
            {
                "Persona": record.get("persona", "Unknown"),
                "Recipients": record.get("recipient_count", record.get("total_contacts", 0)),
                "Opened": record.get("opened_count", 0),
                "Clicked": record.get("clicked_count", 0),
                "Unsubscribed": record.get("unsubscribed_count", 0),
                "Simulation Mode": record.get("simulation_mode", ""),
            }
            for record in metrics
        ]
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)


def render_summary(result: dict) -> None:
    """Render markdown output from the analysis layer."""
    st.subheader("Latest Campaign Summary")
    st.markdown(result.get("summary", ""))


def render_recommendations(result: dict) -> None:
    """Render markdown output from the optimization layer."""
    st.subheader("Strategist Optimization Memo")
    st.markdown(result.get("recommendations", ""))


if __name__ == "__main__":
    main()
