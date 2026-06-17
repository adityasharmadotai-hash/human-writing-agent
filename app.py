"""Human Writing Agent — main Streamlit application."""

import io
import logging
import sys
from pathlib import Path
from typing import Optional

import streamlit as st

# ── path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.extractor import extract_text
from core.humanizer import humanize_text, get_ai_explanation
from core.analyzer import analyze_text, AnalysisResult
from utils.helpers import clean_text, word_count, validate_api_key

# ── logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Human Writing Agent",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── font import ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── root palette ── */
:root {
    --bg:        #0F0F14;
    --surface:   #17171F;
    --surface2:  #1E1E28;
    --border:    #2A2A38;
    --accent:    #7C6AF7;
    --accent2:   #A594FF;
    --text:      #E8E6F0;
    --muted:     #7E7C8E;
    --success:   #4ADE80;
    --warning:   #FCD34D;
    --danger:    #F87171;
}

/* ── hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2rem 4rem; max-width: 1400px; }

/* ── sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stTextInput input {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
}
section[data-testid="stSidebar"] .stTextInput input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(124,106,247,0.25);
}

/* ── hero header ── */
.hero {
    padding: 2.5rem 2rem 2rem;
    background: linear-gradient(135deg, #13131C 0%, #1A1828 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(124,106,247,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text);
    margin: 0 0 0.4rem;
    letter-spacing: -0.5px;
}
.hero-sub {
    font-size: 0.95rem;
    color: var(--muted);
    margin: 0;
    line-height: 1.6;
}
.accent-dot { color: var(--accent2); }

/* ── section cards ── */
.section-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
}
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--accent2);
    margin-bottom: 0.75rem;
}

/* ── metric cards ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 0.75rem;
    margin: 1rem 0;
}
.metric-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 0.9rem 0.8rem;
    text-align: center;
    position: relative;
}
.metric-card.primary { border-color: rgba(124,106,247,0.45); }
.metric-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-value.accent  { color: var(--accent2); }
.metric-value.success { color: var(--success); }
.metric-value.warning { color: var(--warning); }
.metric-value.danger  { color: var(--danger); }
.metric-label {
    font-size: 0.68rem;
    color: var(--muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ── score ring placeholder (CSS arc via border) ── */
.score-ring {
    width: 80px; height: 80px;
    border-radius: 50%;
    border: 6px solid var(--border);
    border-top-color: var(--accent);
    margin: 0 auto 0.5rem;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent2);
}

/* ── progress bars ── */
.prog-row { margin-bottom: 0.8rem; }
.prog-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    margin-bottom: 0.3rem;
    color: var(--text);
}
.prog-label { font-weight: 500; }
.prog-val   { color: var(--muted); }
.prog-track {
    height: 6px;
    background: var(--border);
    border-radius: 99px;
    overflow: hidden;
}
.prog-fill {
    height: 100%;
    border-radius: 99px;
    transition: width 0.4s ease;
}

/* ── comparison columns ── */
.compare-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0.35rem 0.7rem;
    border-radius: 6px;
    display: inline-block;
    margin-bottom: 0.6rem;
}
.compare-label.original   { background: rgba(248,113,113,0.15); color: var(--danger); }
.compare-label.humanized  { background: rgba(74,222,128,0.15);  color: var(--success); }

/* ── explanation box ── */
.explanation-box {
    background: rgba(124,106,247,0.08);
    border: 1px solid rgba(124,106,247,0.25);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-size: 0.9rem;
    color: var(--text);
    line-height: 1.65;
    font-style: italic;
}

/* ── tag pill ── */
.tag {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 99px;
    font-size: 0.7rem;
    font-weight: 600;
    margin-right: 0.4rem;
}
.tag-light     { background: rgba(74,222,128,0.15);  color: var(--success); }
.tag-moderate  { background: rgba(252,211,77,0.15);  color: var(--warning); }
.tag-aggressive{ background: rgba(248,113,113,0.15); color: var(--danger); }

/* ── text areas ── */
.stTextArea textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    line-height: 1.7 !important;
    resize: vertical;
}
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(124,106,247,0.2) !important;
}

/* ── primary button ── */
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7C6AF7 0%, #9B8BFF 100%);
    border: none;
    border-radius: 10px;
    color: #fff;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.65rem 2rem;
    transition: opacity 0.15s, transform 0.1s;
    box-shadow: 0 4px 16px rgba(124,106,247,0.35);
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

/* ── download buttons ── */
div[data-testid="stDownloadButton"] button {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.85rem;
    padding: 0.5rem 1.2rem;
    transition: border-color 0.15s;
}
div[data-testid="stDownloadButton"] button:hover {
    border-color: var(--accent);
    color: var(--accent2);
}

/* ── radio ── */
div[data-testid="stRadio"] label { font-size: 0.88rem; }

/* ── tab styling ── */
button[data-baseweb="tab"] {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent2) !important;
    border-bottom-color: var(--accent) !important;
}

/* ── alerts ── */
div[data-testid="stAlert"] {
    border-radius: 10px;
    font-size: 0.88rem;
}

/* ── divider ── */
hr { border-color: var(--border); }
</style>
""",
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers / sub-components
# ═══════════════════════════════════════════════════════════════════════════════


def _score_color(score: float) -> str:
    if score >= 75:
        return "success"
    if score >= 50:
        return "warning"
    return "danger"


def _render_progress(label: str, value: float, color: str = "#7C6AF7") -> None:
    pct = max(0.0, min(100.0, value))
    st.markdown(
        f"""
        <div class="prog-row">
            <div class="prog-header">
                <span class="prog-label">{label}</span>
                <span class="prog-val">{pct:.0f} / 100</span>
            </div>
            <div class="prog-track">
                <div class="prog-fill" style="width:{pct}%; background:{color};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_analysis(result: AnalysisResult, title: str = "Analysis") -> None:
    hl = result.human_likeness_score
    hl_color = _score_color(hl)

    st.markdown(f"<div class='section-label'>{title}</div>", unsafe_allow_html=True)

    # Big score + metrics row
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card primary">
                <div class="metric-value {hl_color}">{hl:.0f}</div>
                <div class="metric-label">Human-Likeness</div>
            </div>
            <div class="metric-card">
                <div class="metric-value {_score_color(result.vocabulary_diversity)}">{result.vocabulary_diversity:.0f}</div>
                <div class="metric-label">Vocabulary Diversity</div>
            </div>
            <div class="metric-card">
                <div class="metric-value {_score_color(result.sentence_variety)}">{result.sentence_variety:.0f}</div>
                <div class="metric-label">Sentence Variety</div>
            </div>
            <div class="metric-card">
                <div class="metric-value {_score_color(result.readability_score)}">{result.readability_score:.0f}</div>
                <div class="metric-label">Readability</div>
            </div>
            <div class="metric-card">
                <div class="metric-value {_score_color(result.repetition_score)}">{result.repetition_score:.0f}</div>
                <div class="metric-label">Repetition Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value accent">{result.word_count:,}</div>
                <div class="metric-label">Words</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_progress("Human-Likeness", hl, "#7C6AF7")
    _render_progress("Vocabulary Diversity", result.vocabulary_diversity, "#A594FF")
    _render_progress("Sentence Variety", result.sentence_variety, "#4ADE80")
    _render_progress("Readability", result.readability_score, "#FCD34D")
    _render_progress("Repetition Score (higher = less repetition)", result.repetition_score, "#67E8F9")

    st.markdown(
        f"<div class='explanation-box'>{result.explanation}</div>",
        unsafe_allow_html=True,
    )


def _make_docx_bytes(text: str) -> bytes:
    """Create a DOCX file in memory."""
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            p = doc.add_paragraph(para)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════════


def render_sidebar() -> tuple[Optional[str], str]:
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 1rem 0 1.5rem;">
                <div style="font-size:1.1rem; font-weight:700; color:#E8E6F0; margin-bottom:0.2rem;">
                    ✍️ Human Writing Agent
                </div>
                <div style="font-size:0.75rem; color:#7E7C8E;">
                    Powered by Google Gemini
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("**Gemini API Key**")
        api_key_input = st.text_input(
            "API Key",
            type="password",
            placeholder="AIza…",
            label_visibility="collapsed",
            help="Get your key at aistudio.google.com",
        )

        if api_key_input:
            if validate_api_key(api_key_input):
                st.success("API key set", icon="🔐")
            else:
                st.error("Key looks too short — double-check it.")

        st.markdown("---")
        st.markdown("**Humanization Level**")
        level = st.radio(
            "Level",
            options=["Light", "Moderate", "Aggressive"],
            index=1,
            label_visibility="collapsed",
            help=(
                "**Light** — subtle polish only.\n\n"
                "**Moderate** — balanced rewrite.\n\n"
                "**Aggressive** — deep restructuring."
            ),
        )

        level_map = {"Light": "light", "Moderate": "moderate", "Aggressive": "aggressive"}
        level_key = level_map[level]

        tag_class = {
            "light": "tag-light",
            "moderate": "tag-moderate",
            "aggressive": "tag-aggressive",
        }[level_key]

        st.markdown(
            f"<span class='tag {tag_class}'>{level}</span>"
            "<span style='font-size:0.78rem;color:#7E7C8E;'>"
            + {
                "light": "Minimal changes, close to original.",
                "moderate": "Balanced flow and clarity.",
                "aggressive": "Deep restructuring for maximum naturalness.",
            }[level_key]
            + "</span>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size:0.75rem; color:#7E7C8E; line-height:1.6;">
                <strong style="color:#E8E6F0;">About</strong><br>
                Transforms academic text into more natural, readable writing
                while preserving citations, technical terminology, and scholarly meaning.<br><br>
                Scores reflect writing quality characteristics — they are
                <em>not</em> a guarantee about AI detector results.
            </div>
            """,
            unsafe_allow_html=True,
        )

    return api_key_input or None, level_key


# ═══════════════════════════════════════════════════════════════════════════════
# Main app
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    api_key, level = render_sidebar()

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">Human Writing Agent<span class="accent-dot"> ·</span></div>
            <div class="hero-sub">
                Transform AI-generated academic prose into natural, publication-quality writing —
                preserving meaning, citations, and scholarly rigour throughout.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Input area ───────────────────────────────────────────────────────────
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Input</div>", unsafe_allow_html=True)

    input_tab, upload_tab = st.tabs(["📝  Paste Text", "📂  Upload File"])

    input_text: str = ""

    with input_tab:
        pasted = st.text_area(
            "Academic text",
            height=280,
            placeholder="Paste your academic text here — paragraphs, sections, or a full paper excerpt…",
            label_visibility="collapsed",
            key="pasted_text",
        )
        if pasted:
            input_text = pasted
            wc = word_count(pasted)
            st.caption(f"{wc:,} words · {len(pasted):,} characters")

    with upload_tab:
        uploaded = st.file_uploader(
            "Upload file",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
            help="PDF, DOCX, or TXT — max 50 MB",
        )
        if uploaded:
            with st.spinner(f"Reading {uploaded.name}…"):
                try:
                    raw = extract_text(uploaded.read(), uploaded.name)
                    raw = clean_text(raw)
                    input_text = raw
                    st.success(f"Extracted {word_count(raw):,} words from **{uploaded.name}**")
                    with st.expander("Preview extracted text"):
                        st.text(raw[:1200] + ("…" if len(raw) > 1200 else ""))
                except ValueError as e:
                    st.error(f"File error: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Action button ─────────────────────────────────────────────────────────
    col_btn, col_warn = st.columns([1, 3])
    with col_btn:
        run = st.button("✦  Humanize", use_container_width=True)
    with col_warn:
        if not api_key:
            st.warning("Add your Gemini API key in the sidebar to continue.")
        elif not input_text.strip():
            st.info("Paste text or upload a file above.")

    # ── Processing ────────────────────────────────────────────────────────────
    if run:
        if not api_key:
            st.error("Please provide a Gemini API key in the sidebar.")
            st.stop()
        if not input_text.strip():
            st.error("No input text found. Paste text or upload a file first.")
            st.stop()
        if word_count(input_text) < 20:
            st.warning("Text is very short (< 20 words). Results may be limited.")

        # ── Run humanization ─────────────────────────────────────────────
        with st.spinner("Rewriting with Gemini…"):
            try:
                humanized = humanize_text(
                    clean_text(input_text),
                    api_key=api_key,
                    level=level,
                )
            except ValueError as e:
                st.error(f"Humanization failed: {e}")
                logger.error("Humanization error: %s", e)
                st.stop()

        # ── Fetch AI explanation ─────────────────────────────────────────
        with st.spinner("Analysing humanized text…"):
            ai_explanation = get_ai_explanation(humanized, api_key)

        # ── Analyse both ─────────────────────────────────────────────────
        original_analysis = analyze_text(clean_text(input_text))
        humanized_analysis = analyze_text(humanized, gemini_explanation=ai_explanation)

        # ── Store in session state ────────────────────────────────────────
        st.session_state["original_text"] = clean_text(input_text)
        st.session_state["humanized_text"] = humanized
        st.session_state["original_analysis"] = original_analysis
        st.session_state["humanized_analysis"] = humanized_analysis

    # ── Results section ───────────────────────────────────────────────────────
    if "humanized_text" in st.session_state:
        original_text: str = st.session_state["original_text"]
        humanized_text: str = st.session_state["humanized_text"]
        orig_result: AnalysisResult = st.session_state["original_analysis"]
        human_result: AnalysisResult = st.session_state["humanized_analysis"]

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Comparison ────────────────────────────────────────────────────
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Side-by-Side Comparison</div>", unsafe_allow_html=True)

        col_orig, col_human = st.columns(2, gap="medium")

        with col_orig:
            st.markdown(
                "<span class='compare-label original'>Original</span>",
                unsafe_allow_html=True,
            )
            st.text_area(
                "Original text",
                value=original_text,
                height=400,
                disabled=True,
                label_visibility="collapsed",
                key="display_original",
            )
            st.caption(
                f"{orig_result.word_count:,} words · "
                f"{orig_result.sentence_count} sentences · "
                f"avg {orig_result.avg_sentence_length} words/sentence"
            )

        with col_human:
            st.markdown(
                "<span class='compare-label humanized'>Humanized</span>",
                unsafe_allow_html=True,
            )
            st.text_area(
                "Humanized text",
                value=humanized_text,
                height=400,
                disabled=True,
                label_visibility="collapsed",
                key="display_humanized",
            )
            st.caption(
                f"{human_result.word_count:,} words · "
                f"{human_result.sentence_count} sentences · "
                f"avg {human_result.avg_sentence_length} words/sentence"
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Analysis comparison ───────────────────────────────────────────
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Writing Quality Analysis</div>", unsafe_allow_html=True)

        delta_hl = human_result.human_likeness_score - orig_result.human_likeness_score
        delta_color = "#4ADE80" if delta_hl >= 0 else "#F87171"
        delta_sign = "+" if delta_hl >= 0 else ""

        st.markdown(
            f"""
            <div style="text-align:center; padding: 0.5rem 0 1.2rem;">
                <div style="font-size:0.78rem; color:#7E7C8E; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.3rem;">
                    Human-Likeness Improvement
                </div>
                <div style="font-size:2.5rem; font-weight:700; color:{delta_color};">
                    {delta_sign}{delta_hl:.1f}
                </div>
                <div style="font-size:0.8rem; color:#7E7C8E;">
                    {orig_result.human_likeness_score:.0f} → {human_result.human_likeness_score:.0f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_orig, tab_human = st.tabs(["📄 Original Analysis", "✅ Humanized Analysis"])

        with tab_orig:
            _render_analysis(orig_result, "Original Text")

        with tab_human:
            _render_analysis(human_result, "Humanized Text")

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Export ────────────────────────────────────────────────────────
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Export Humanized Text</div>", unsafe_allow_html=True)

        dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 2])

        with dl_col1:
            st.download_button(
                label="⬇ Download TXT",
                data=humanized_text.encode("utf-8"),
                file_name="humanized_text.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with dl_col2:
            try:
                docx_bytes = _make_docx_bytes(humanized_text)
                st.download_button(
                    label="⬇ Download DOCX",
                    data=docx_bytes,
                    file_name="humanized_text.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            except Exception as e:
                logger.warning("DOCX export failed: %s", e)
                st.caption("DOCX export unavailable.")

        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
