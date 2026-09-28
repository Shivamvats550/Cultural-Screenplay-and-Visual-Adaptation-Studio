import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root directory to sys.path so 'app' package imports work
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.llm.gemini_provider import GeminiProvider
from app.workflow import CultureAdaptWorkflow

st.set_page_config(page_title="CultureAdapt AI", page_icon="🎬", layout="wide")

st.title("🎬 CultureAdapt AI")
st.caption("Agentic Cultural Screenplay & Visual Adaptation Studio")

with st.sidebar:
    st.header("Cultural Target")
    culture = st.selectbox(
        "Culture Preset",
        ["Rajasthani", "UP / Hindi Heartland", "South Indian", "Punjabi", "Haryanvi"]
    )

    if culture == "Rajasthani":
        default_dialect = "Marwari"
        default_region = "Rajasthan"
    elif culture == "UP / Hindi Heartland":
        default_dialect = "Awadhi"
        default_region = "Uttar Pradesh"
    elif culture == "South Indian":
        default_dialect = "Tamil"
        default_region = "South India"
    elif culture == "Punjabi":
        default_dialect = "Majhi"
        default_region = "Punjab"
    else:
        default_dialect = "Bangru"
        default_region = "Haryana"

    dialect = st.text_input("Exact dialect", default_dialect)
    region = st.text_input("Region", default_region)
    setting = st.selectbox("Setting", ["Rural", "Urban"])
    output_language = st.selectbox("Output Language", ["Hindi", "English", "Regional Dialect"])
    output_script = st.selectbox("Output script", ["Devanagari", "Roman (Latin)", "Gurmukhi", "Regional"])

# Input method: Upload file or paste text directly
st.subheader("1. Screenplay Input")
input_option = st.radio("Choose Input Method", ["Upload Screenplay File", "Paste Screenplay Text"], horizontal=True)

raw_screenplay_text = None

if input_option == "Upload Screenplay File":
    uploaded = st.file_uploader("Upload screenplay (TXT, PDF, DOCX)", type=["txt", "pdf", "docx"])
    if uploaded:
        st.write(f"**Uploaded File:** {uploaded.name}")
else:
    uploaded = None
    raw_screenplay_text = st.text_area("Paste screenplay text here", height=200, placeholder="INT. VILLAGE HOUSE - DAY\nAMAR (30) sits with BEBE (60)...")

for key, default in [
    ("source", None),
    ("extraction", None),
    ("plan", None),
    ("approved", False),
    ("adapted", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.button("1. Analyze Screenplay", type="primary"):
    source_text = None
    tmp_path = None

    try:
        workflow = CultureAdaptWorkflow(GeminiProvider())

        if uploaded:
            suffix = Path(uploaded.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getbuffer())
                tmp_path = tmp.name
            with st.spinner("Gemini is extracting screenplay structure from file..."):
                source_text, extraction = workflow.extract(tmp_path)
        elif raw_screenplay_text and raw_screenplay_text.strip():
            with st.spinner("Gemini is extracting screenplay structure from text..."):
                extraction = workflow.llm.extract_screenplay(raw_screenplay_text)
                source_text = raw_screenplay_text
        else:
            st.warning("Please upload a file or paste text before analyzing.")
            st.stop()

        st.session_state.source = source_text
        st.session_state.extraction = extraction
        st.session_state.plan = None
        st.session_state.approved = False
        st.session_state.adapted = None
        st.success("Extraction complete!")

    except Exception as exc:
        st.error(str(exc))

    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

if st.session_state.extraction:
    extraction = st.session_state.extraction

    st.header("2. Extracted Story Structure")
    a, b, c, d = st.columns(4)
    a.metric("Characters", len(extraction.characters))
    b.metric("Scenes", len(extraction.scenes))
    c.metric("Costumes", len(extraction.costumes))
    d.metric("Props", len(extraction.props))

    exp1, exp2, exp3, exp4 = st.tabs(["Characters", "Scenes", "Costumes", "Props"])
    with exp1:
        for x in extraction.characters:
            st.json(x.model_dump())
    with exp2:
        for x in extraction.scenes:
            st.json(x.model_dump())
    with exp3:
        for x in extraction.costumes:
            st.json(x.model_dump())
    with exp4:
        for x in extraction.props:
            st.json(x.model_dump())

    if st.button("3. Create Cultural Adaptation Plan"):
        try:
            workflow = CultureAdaptWorkflow(GeminiProvider())

            with st.spinner("Gemini is creating the adaptation plan..."):
                st.session_state.plan = workflow.plan(
                    st.session_state.source,
                    extraction,
                    culture,
                    dialect,
                    region,
                    setting,
                    output_script,
                    output_language,
                )
            st.session_state.approved = False
        except Exception as exc:
            st.error(str(exc))

if st.session_state.plan:
    plan = st.session_state.plan

    st.header("4. Cultural Adaptation Plan Review")
    for i, decision in enumerate(plan.decisions, start=1):
        st.subheader(f"Decision {i}: {decision.category}")
        st.write("**Source Element:**", decision.source_element)
        st.write("**Adapted Element:**", decision.adapted_element)
        st.write("**Reason:**", decision.reason)
        st.write("**Confidence:**", f"{decision.confidence:.0%}")
        if decision.requires_review:
            st.warning("Human review recommended.")

    reviewed = st.checkbox("I have reviewed the cultural adaptation plan.")

    if reviewed and st.button("5. Approve Plan"):
        st.session_state.approved = True
        st.success("Plan approved.")

if st.session_state.approved:
    st.header("6. Generate & Compare Adapted Screenplay")

    if st.button("Generate Adapted Screenplay"):
        try:
            workflow = CultureAdaptWorkflow(GeminiProvider())
            with st.spinner("Generating adapted screenplay..."):
                st.session_state.adapted = workflow.adapt(
                    st.session_state.source,
                    st.session_state.plan,
                )
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.adapted:
        tab_source, tab_adapted, tab_side = st.tabs(["Source Screenplay", "Adapted Screenplay", "Side-by-Side Comparison"])
        with tab_source:
            st.text_area("Source Screenplay", st.session_state.source, height=400)
        with tab_adapted:
            st.text_area("Adapted Screenplay", st.session_state.adapted, height=400)
        with tab_side:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Original Source")
                st.text_area("Source Text", st.session_state.source, height=400, key="side_source")
            with col2:
                st.markdown(f"### Adapted ({output_language} / {output_script})")
                st.text_area("Adapted Text", st.session_state.adapted, height=400, key="side_adapted")

    st.header("7. Continuity Verification")

    if st.button("Run Continuity Checks"):
        report = CultureAdaptWorkflow(GeminiProvider()).verify(
            st.session_state.extraction
        )

        for item in report:
            if item["status"] == "PASS":
                st.success(item["message"])
            elif item["status"] == "WARNING":
                st.warning(item["message"])
            else:
                st.error(item["message"])

    st.header("8. Generate Visual Production Pack")

    st.caption(
        "Free demo mode: local production cards. "
        "Use the optional image provider only if you have image-model billing/access."
    )

    if st.button("Generate Visual Pack"):
        paths = CultureAdaptWorkflow(GeminiProvider()).generate_visual_pack(
            st.session_state.extraction,
            "generated/visual_pack",
        )

        for path in paths:
            st.image(path)

    export = {
        "extraction": extraction.model_dump(),
        "adaptation_plan": plan.model_dump(),
        "adapted_screenplay": st.session_state.adapted,
    }

    st.download_button(
        "Download Project JSON",
        data=json.dumps(export, indent=2, ensure_ascii=False),
        file_name="cultureadapt_project.json",
        mime="application/json",
    )
