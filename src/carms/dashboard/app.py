"""Streamlit analytics dashboard for CaRMS program data."""

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://carms:carms@localhost:5432/carms")
API_URL = os.environ.get("API_URL", "http://localhost:8000")


@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)


def query_df(sql: str) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn)


# --- Page Config ---
st.set_page_config(
    page_title="CaRMS Program Explorer - Analytics",
    page_icon="🏥",
    layout="wide",
)

st.markdown(
    "<style>.block-container{padding-top:2rem;}</style>",
    unsafe_allow_html=True,
)

# --- Sidebar ---
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select page",
    [
        "Overview",
        "By Discipline",
        "By School",
        "Geographic",
        "Program Explorer",
        "Search",
        "Reports",
    ],
)

# === Overview ===
if page == "Overview":
    st.title("CaRMS Program Explorer")
    st.markdown("Analytics dashboard for Canadian medical residency programs")

    try:
        col1, col2, col3 = st.columns(3)

        programs = query_df("SELECT COUNT(*) AS cnt FROM programs").iloc[0]["cnt"]
        disciplines = query_df("SELECT COUNT(*) AS cnt FROM disciplines").iloc[0]["cnt"]
        schools = query_df("SELECT COUNT(*) AS cnt FROM schools").iloc[0]["cnt"]

        col1.metric("Total Programs", f"{programs:,}")
        col2.metric("Disciplines", disciplines)
        col3.metric("Schools", schools)

        try:
            embeddings = query_df("SELECT COUNT(*) AS cnt FROM program_embeddings").iloc[0]["cnt"]
            st.metric("Embedding Chunks", f"{embeddings:,}")
        except Exception:
            pass

        st.subheader("Top 10 Disciplines by Program Count")
        df = query_df("""
            SELECT d.name AS discipline, COUNT(p.id) AS programs
            FROM disciplines d
            JOIN programs p ON d.id = p.discipline_id
            GROUP BY d.name ORDER BY programs DESC LIMIT 10
        """)
        fig = px.bar(
            df,
            x="programs",
            y="discipline",
            orientation="h",
            color="programs",
            color_continuous_scale="Blues",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("Make sure the database is running and ETL has been executed.")

# === By Discipline ===
elif page == "By Discipline":
    st.header("Programs by Discipline")

    df = query_df("""
        SELECT d.name AS discipline, COUNT(p.id) AS programs
        FROM disciplines d
        LEFT JOIN programs p ON d.id = p.discipline_id
        GROUP BY d.name ORDER BY programs DESC
    """)

    fig = px.bar(
        df,
        x="programs",
        y="discipline",
        orientation="h",
        color="programs",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=800)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df.rename(columns={"discipline": "Discipline", "programs": "Programs"}),
        use_container_width=True,
    )

# === By School ===
elif page == "By School":
    st.header("Programs by School")

    df = query_df("""
        SELECT s.name AS school, COUNT(p.id) AS programs
        FROM schools s
        JOIN programs p ON s.id = p.school_id
        GROUP BY s.name ORDER BY programs DESC
    """)

    fig = px.bar(
        df,
        x="programs",
        y="school",
        orientation="h",
        color="programs",
        color_continuous_scale="Sunset",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df.rename(columns={"school": "School", "programs": "Programs"}), use_container_width=True
    )

# === Geographic ===
elif page == "Geographic":
    st.header("Geographic Distribution")

    df = query_df("""
        SELECT site, COUNT(*) AS programs
        FROM programs GROUP BY site ORDER BY programs DESC
    """)

    fig = px.treemap(
        df, path=["site"], values="programs", color="programs", color_continuous_scale="Teal"
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Programs by Site")
    st.dataframe(
        df.rename(columns={"site": "Site", "programs": "Programs"}), use_container_width=True
    )

# === Program Explorer ===
elif page == "Program Explorer":
    st.header("Program Explorer")

    col1, col2, col3 = st.columns(3)

    disciplines = query_df("SELECT id, name FROM disciplines ORDER BY name")
    schools = query_df("SELECT id, name FROM schools ORDER BY name")
    sites = query_df("SELECT DISTINCT site FROM programs ORDER BY site")

    with col1:
        disc_name = st.selectbox("Discipline", ["All"] + disciplines["name"].tolist())
    with col2:
        school_name = st.selectbox("School", ["All"] + schools["name"].tolist())
    with col3:
        site_name = st.selectbox("Site", ["All"] + sites["site"].tolist())

    conditions = []
    if disc_name != "All":
        disc_id = disciplines[disciplines["name"] == disc_name].iloc[0]["id"]
        conditions.append(f"p.discipline_id = {disc_id}")
    if school_name != "All":
        school_id = schools[schools["name"] == school_name].iloc[0]["id"]
        conditions.append(f"p.school_id = {school_id}")
    if site_name != "All":
        conditions.append(f"p.site = '{site_name}'")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    df = query_df(f"""
        SELECT p.id, p.name, d.name AS discipline, s.name AS school, p.site, p.stream
        FROM programs p
        JOIN disciplines d ON p.discipline_id = d.id
        JOIN schools s ON p.school_id = s.id
        {where}
        ORDER BY p.name
    """)

    st.write(f"**{len(df)} programs found**")
    st.dataframe(
        df.rename(
            columns={
                "id": "ID",
                "name": "Name",
                "discipline": "Discipline",
                "school": "School",
                "site": "Site",
                "stream": "Stream",
            }
        ),
        use_container_width=True,
        height=500,
    )

    if len(df) > 0:
        selected_id = st.number_input("Enter Program ID to view details", min_value=1, step=1)
        if st.button("Show Details"):
            detail = query_df(f"""
                SELECT pd.full_markdown
                FROM program_descriptions pd
                WHERE pd.program_id = {int(selected_id)}
            """)
            if len(detail) > 0 and detail.iloc[0]["full_markdown"]:
                st.markdown(detail.iloc[0]["full_markdown"])
            else:
                st.warning("No description available for this program.")

# === Search ===
elif page == "Search":
    st.header("Semantic Search")
    st.markdown("Search program descriptions using natural language.")

    query_text = st.text_input(
        "Search query", placeholder="e.g., rural family medicine with research"
    )
    top_k = st.slider("Number of results", 1, 30, 10)

    if st.button("Search") and query_text:
        try:
            res = requests.post(
                f"{API_URL}/search/",
                json={"query": query_text, "top_k": top_k},
                timeout=30,
            )
            data = res.json()

            if data.get("results"):
                st.write(f"**{data['count']} results for:** *{data['query']}*")
                for r in data["results"]:
                    with st.expander(
                        f"**{r['program_name']}** — {r['discipline']} | {r['school']} | "
                        f"Similarity: {r['similarity']:.4f}"
                    ):
                        st.write(f"**Site:** {r['site']} | **Stream:** {r['stream']}")
                        st.write(f"**Matching text:** {r['chunk_text']}")
            else:
                st.info("No results found. Try a different query.")

        except requests.ConnectionError:
            st.error("Cannot connect to API. Make sure the FastAPI server is running.")
        except Exception as e:
            st.error(f"Search error: {e}")

    # --- AI Question & Answer (RAG) ---
    st.divider()
    st.subheader("AI Question & Answer (RAG)")
    st.markdown("Ask a natural language question about CaRMS programs.")

    rag_query = st.text_input(
        "Your question", placeholder="e.g., Which programs emphasize rural family medicine?"
    )

    if st.button("Ask") and rag_query:
        try:
            rag_res = requests.post(
                f"{API_URL}/rag/ask",
                json={"question": rag_query, "top_k": 8},
                timeout=60,
            )
            if rag_res.status_code == 503:
                st.warning("RAG is not available. Set ANTHROPIC_API_KEY on the server.")
            elif rag_res.ok:
                rag_data = rag_res.json()
                st.markdown("**Answer:**")
                st.write(rag_data["answer"])

                if rag_data.get("sources"):
                    st.markdown("**Sources:**")
                    for src in rag_data["sources"]:
                        with st.expander(
                            f"{src.get('program_name', 'Unknown')} — "
                            f"{src.get('discipline', '')} | {src.get('school', '')}"
                        ):
                            st.write(f"**Site:** {src.get('site', 'N/A')}")
                            st.write(f"**Similarity:** {src.get('similarity', 0):.4f}")
                            st.write(f"**Excerpt:** {src.get('excerpt', '')}")
            else:
                st.error(f"RAG error: {rag_res.text}")
        except requests.ConnectionError:
            st.error("Cannot connect to API.")
        except Exception as e:
            st.error(f"RAG error: {e}")

# === Reports ===
elif page == "Reports":
    st.header("Reports")
    st.markdown("Generate pandas-based analytical reports on demand.")

    try:
        res = requests.get(f"{API_URL}/reports/", timeout=10)
        available = res.json()

        if available:
            names = [r["name"] for r in available]
            descriptions = {r["name"]: r["description"] for r in available}

            selected = st.selectbox(
                "Select a report",
                names,
                format_func=lambda n: f"{n} — {descriptions[n]}",
            )

            if st.button("Generate Report"):
                with st.spinner("Generating..."):
                    report_res = requests.get(f"{API_URL}/reports/{selected}", timeout=30)
                    report_data = report_res.json()

                    meta = report_data["metadata"]
                    st.subheader(meta["title"])
                    st.caption(
                        f"Generated at {meta['generated_at']} | "
                        f"{meta['row_count']} rows | "
                        f"{len(meta['columns'])} columns"
                    )

                    df = pd.DataFrame(report_data["data"])
                    st.dataframe(df, use_container_width=True)

                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{selected}.csv",
                        mime="text/csv",
                    )
        else:
            st.info("No reports available.")

    except requests.ConnectionError:
        st.error("Cannot connect to API. Make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"Error loading reports: {e}")
