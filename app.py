"""Second Brain — AI Personal Knowledge & Productivity Assistant.

Entry point: ``streamlit run app.py``

Requirements: set GROQ_API_KEY (or the relevant provider key) in a .env file.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

import streamlit as st

from core.config import settings

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Second Brain · AI Productivity Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (light/whitish theme) ─────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Light / Whitish Canvas */
    .stApp {
        background-color: #FAFBFD !important;
        color: #111318 !important;
    }

    /* Ensure readable text contrast across components */
    .stApp, .stApp * {
        color: #0F1720 !important;
    }

    /* Placeholder and muted text visibility */
    input::placeholder, textarea::placeholder {
        color: #6B7280 !important;
        opacity: 1 !important;
    }
    .stCaption, .caption, .css-rtk8m6, .small, small {
        color: #4B5563 !important;
    }

    /* Subtle top accent beam */
    .gemini-beam {
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, #6EA8FE 0%, #B388EB 50%, #FFB4A2 100%);
        background-size: 200% 200%;
        animation: geminiGlow 6s ease infinite;
        border-radius: 4px;
        margin-bottom: 1.2rem;
    }

    @keyframes geminiGlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Main Header Container */
    .main-header {
        background: linear-gradient(180deg, #FFFFFF 0%, #F6F8FB 100%);
        border: 1px solid #E6E9EE;
        padding: 2rem 2.4rem;
        border-radius: 16px;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 18px rgba(17, 19, 24, 0.04);
    }
    .main-header h1 {
        color: #0F1720 !important;
        margin: 0;
        font-family: 'Outfit', sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .main-header p {
        color: #4B5563 !important;
        margin: 0.4rem 0 0;
        font-size: 0.95rem;
        line-height: 1.4;
    }

    /* Sidebar - light drawer */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #EEF2F6 !important;
    }
    [data-testid="stSidebar"] * {
        color: #0F1720 !important;
    }

    /* Cards */
    .card {
        background: #FFFFFF;
        border: 1px solid #EEF2F6;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin: 0.6rem 0;
        transition: all 0.18s ease;
    }
    .card:hover {
        border-color: #BEE1FF;
        box-shadow: 0 8px 30px rgba(15, 23, 32, 0.06);
        transform: translateY(-4px);
    }

    /* Stat Boxes */
    .stat-box {
        background: #FFFFFF;
        border: 1px solid #EEF2F6;
        border-radius: 12px;
        padding: 1.2rem 1rem;
        text-align: center;
    }
    .stat-box .stat-number {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0B5FFF;
    }
    .stat-box .stat-label {
        font-size: 0.78rem;
        color: #6B7280;
        font-weight: 600;
        margin-top: 0.3rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    /* Section headers */
    .section-header {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #2563EB;
        margin: 1.2rem 0 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #EEF2F6;
    }

    /* Chat bubbles */
    [data-testid="stChatMessage"] {
        background: #FFFFFF !important;
        border: 1px solid #EEF2F6 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 0.7rem !important;
        color: #0F1720 !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg,#2563EB,#8B5CF6);
        color: #FFFFFF !important;
        border: none;
        border-radius: 12px !important;
        font-weight: 600;
        padding: 0.55rem 1.1rem;
    }
    .stButton > button:hover {
        filter: brightness(0.96);
        transform: translateY(-1px);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 6px;
        gap: 6px;
        border: 1px solid #EEF2F6;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 14px;
        color: #0F1720 !important;
        font-weight: 500;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #E6F0FF !important;
        color: #0B5FFF !important;
        font-weight: 600;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: #FFFFFF !important;
        border: 1px solid #E6EEF8 !important;
        color: #0F1720 !important;
        border-radius: 10px !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #8FB8FF !important;
        box-shadow: 0 0 0 4px rgba(43, 108, 255, 0.08) !important;
    }

    /* Priority Badges */
    .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; margin-left: 6px; }
    .badge-critical { background: rgba(255,77,79,0.10); color: #B91C1C; border: 1px solid rgba(255,77,79,0.18); }
    .badge-high     { background: rgba(250,204,21,0.10); color: #92400E; border: 1px solid rgba(250,204,21,0.18); }
    .badge-medium   { background: rgba(59,130,246,0.10); color: #1D4ED8; border: 1px solid rgba(59,130,246,0.18); }
    .badge-low      { background: rgba(34,197,94,0.10); color: #065F46; border: 1px solid rgba(34,197,94,0.18); }

    /* Intent Tag */
    .intent-tag { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; background: rgba(59,130,246,0.06); color: #0B5FFF; border: 1px solid rgba(59,130,246,0.12); margin-bottom: 0.4rem; }

    /* Briefing Section */
    .briefing-section { background: rgba(59,130,246,0.04); border-left: 4px solid #2563EB; padding: 1rem 1.2rem; border-radius: 0 12px 12px 0; margin: 0.6rem 0; }

    /* Sidebar Section Headers */
    .sidebar-section { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #6B7280 !important; margin: 1.2rem 0 0.5rem; }

    /* Scrollable list */
    .item-list { max-height: 300px; overflow-y: auto; padding-right: 4px; }

    /* Spinner / loading overlay visibility */
    [data-testid="stSpinner"], .stSpinner, [role="status"] {
        color: #0F1720 !important;
        background-color: rgba(250,251,253,0.98) !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        box-shadow: 0 8px 30px rgba(15, 23, 32, 0.06) !important;
        z-index: 9999 !important;
    }
    [data-testid="stSpinner"] *, .stSpinner * {
        color: #0F1720 !important;
    }
    /* progress / loading text */
    .stProgress, .stProgress * {
        color: #0F1720 !important;
    }
    /* make any aria-live loading text visible */
    [aria-live] {
        color: #0F1720 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state initialisation ──────────────────────────────────────────────

def _init_session() -> None:
    """Ensure all session state keys exist with sensible defaults."""
    defaults = {
        "session_id": str(uuid.uuid4()),
        "chat_history": [],          # list of {"role": "user"|"assistant", "content": str, "meta": dict}
        "chat_history_raw": [],      # list of {"role": str, "content": str} for LLM
        "uploaded_files": [],        # list of {"name": str, "data": bytes}
        "kb_built": False,
        "kb_num_chunks": 0,
        "last_briefing": None,       # DailyBriefing | None
        "tool_log": [],              # list of str (last N tool calls)
        "notes_editing": None,       # note_id being edited
        "tasks_filter": "all",
        "email_draft": "",
        "smtp_email": settings.SMTP_EMAIL,
        "smtp_app_password": settings.SMTP_APP_PASSWORD,
        "user_email_recipient": "",
        "auto_email_response": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()

# ── Lazy imports (avoid slowing initial render) ────────────────────────────────

@st.cache_resource(show_spinner="🧠 Loading AI models…")
def _get_coordinator():
    from agents.productivity_coordinator import ProductivityCoordinator
    return ProductivityCoordinator(user_id=settings.DEFAULT_USER_ID)


@st.cache_resource(show_spinner=False)
def _get_notes_agent():
    from agents.notes_agent import notes_agent
    return notes_agent


@st.cache_resource(show_spinner=False)
def _get_tasks_agent():
    from agents.tasks_agent import tasks_agent
    return tasks_agent


@st.cache_resource(show_spinner=False)
def _get_email_agent():
    from agents.email_agent import email_agent
    return email_agent


coord = _get_coordinator()
notes_ag = _get_notes_agent()
tasks_ag = _get_tasks_agent()
email_ag = _get_email_agent()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _priority_badge(priority: str) -> str:
    cls = f"badge-{priority.lower()}"
    return f'<span class="badge {cls}">{priority.upper()}</span>'


def _log_tool(msg: str) -> None:
    st.session_state["tool_log"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state["tool_log"]) > 20:
        st.session_state["tool_log"] = st.session_state["tool_log"][-20:]


def _add_chat(role: str, content: str, meta: dict | None = None) -> None:
    st.session_state["chat_history"].append({"role": role, "content": content, "meta": meta or {}})
    st.session_state["chat_history_raw"].append({"role": role, "content": content})


# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown('<div style="text-align:center;padding:0.5rem 0 1rem;">', unsafe_allow_html=True)
    st.markdown("## 🧠 Second Brain")
    st.markdown('<p style="color:#7070a0;font-size:0.82rem;margin-top:-0.5rem;">AI Productivity Assistant</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Knowledge Base ────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">📚 Knowledge Base</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload PDF or TXT files",
        accept_multiple_files=True,
        type=["pdf", "txt", "md"],
        help="Files are saved locally and embedded into ChromaDB.",
    )
    if uploaded:
        for u in uploaded:
            if not any(f["name"] == u.name for f in st.session_state["uploaded_files"]):
                st.session_state["uploaded_files"].append({"name": u.name, "data": u.getvalue()})

    files = st.session_state["uploaded_files"]
    if files:
        st.caption(f"**{len(files)}** file(s) queued: {', '.join(f['name'] for f in files)}")

    if st.button("🔨 Build Knowledge Base", use_container_width=True):
        if not files:
            st.warning("Upload files first.")
        else:
            from core.vectorstore import build_chroma_db_from_uploads

            with st.spinner("Embedding documents…"):
                result = build_chroma_db_from_uploads(files)
            if result.get("success"):
                st.session_state["kb_built"] = True
                st.session_state["kb_num_chunks"] = result.get("num_chunks", 0)
                _log_tool(f"Built KB from {len(files)} file(s) → {result['num_chunks']} chunks")
                st.success(f"✅ KB built — {result['num_chunks']} chunks indexed")
            else:
                st.error(f"❌ {result.get('error')}")

    if st.session_state["kb_built"]:
        st.markdown(
            f'<div class="card" style="padding:0.6rem 1rem;">'
            f'✅ KB active · <b>{st.session_state["kb_num_chunks"]}</b> chunks</div>',
            unsafe_allow_html=True,
        )

    # ── Quick Note ────────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">📝 Quick Note</div>', unsafe_allow_html=True)
    with st.expander("Add a note", expanded=False):
        qn_title = st.text_input("Title", key="qn_title", placeholder="Note title…")
        qn_content = st.text_area("Content", key="qn_content", height=80, placeholder="Write your note…")
        qn_tags = st.text_input("Tags", key="qn_tags", placeholder="tag1, tag2")
        if st.button("Save Note", key="save_quick_note", use_container_width=True):
            if qn_title.strip():
                tags = [t.strip() for t in qn_tags.split(",") if t.strip()]
                notes_ag.create_note(qn_title.strip(), qn_content, tags)
                _log_tool(f"Created note: {qn_title}")
                st.success("Note saved!")
                st.rerun()
            else:
                st.warning("Title is required.")

    # ── Quick Task ────────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">✅ Quick Task</div>', unsafe_allow_html=True)
    with st.expander("Add a task", expanded=False):
        qt_title = st.text_input("Task title", key="qt_title", placeholder="Task title…")
        qt_priority = st.selectbox("Priority", ["medium", "low", "high", "critical"], key="qt_priority")
        qt_due = st.date_input("Due date (optional)", key="qt_due", value=None)
        if st.button("Add Task", key="add_quick_task", use_container_width=True):
            if qt_title.strip():
                due_str = str(qt_due) if qt_due else None
                tasks_ag.add_task(qt_title.strip(), priority=qt_priority, due_date=due_str)
                _log_tool(f"Added task: {qt_title}")
                st.success("Task added!")
                st.rerun()
            else:
                st.warning("Title is required.")

    # ── Session ───────────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">🕐 Session</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["chat_history"] = []
            st.session_state["chat_history_raw"] = []
            st.session_state["session_id"] = str(uuid.uuid4())
            st.rerun()
    with col2:
        if st.button("📋 New Session", use_container_width=True):
            st.session_state["session_id"] = str(uuid.uuid4())
            st.success("New session started")

    with st.expander("Previous sessions", expanded=False):
        try:
            from core.memory import memory

            sessions = memory.get_sessions(settings.DEFAULT_USER_ID, limit=5)
            if sessions:
                for s in sessions:
                    started = s["started"][:10] if s.get("started") else "?"
                    st.markdown(
                        f'<div class="card" style="padding:0.4rem 0.8rem;font-size:0.8rem;">'
                        f'📅 {started} · {s["messages"]} msg(s)</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No previous sessions yet.")
        except Exception:
            st.caption("Could not load sessions.")

    # ── Google SMTP Setup ──────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">📧 Google SMTP Setup</div>', unsafe_allow_html=True)
    with st.expander("Configure Google App Password", expanded=not bool(st.session_state.get("smtp_email"))):
        se_val = st.text_input("Sender Gmail", value=st.session_state.get("smtp_email", ""), placeholder="your_email@gmail.com", key="se_input")
        sp_val = st.text_input("Google App Password", value=st.session_state.get("smtp_app_password", ""), type="password", placeholder="16-character app password", key="sp_input")
        if st.button("Save Credentials", key="save_smtp_btn", use_container_width=True):
            st.session_state["smtp_email"] = se_val.strip()
            st.session_state["smtp_app_password"] = sp_val.strip()
            settings.SMTP_EMAIL = se_val.strip()
            settings.SMTP_APP_PASSWORD = sp_val.strip()
            _log_tool(f"Saved SMTP email: {se_val.strip()}")
            st.success("SMTP credentials saved!")
            st.rerun()

    # ── Config ────────────────────────────────────────────────────────────────
    with st.expander("⚙️ System Config", expanded=False):
        smtp_status = "Configured ✅" if st.session_state.get("smtp_email") and st.session_state.get("smtp_app_password") else "Not Set ❌"
        st.code(
            f"Provider : {settings.LLM_PROVIDER}\n"
            f"Model    : {settings.GROQ_MODEL if settings.LLM_PROVIDER == 'groq' else settings.OPENAI_MODEL}\n"
            f"Embedder : {settings.EMBEDDING_MODEL}\n"
            f"SMTP Email: {st.session_state.get('smtp_email') or 'Not configured'}\n"
            f"SMTP Setup: {smtp_status}\n"
            f"SQLite   : {settings.SQLITE_PATH}\n"
            f"Chroma   : {settings.CHROMA_DIR}",
            language="text",
        )


# ════════════════════════════════════════════════════════════════════════════════
# MAIN AREA — Header & Google Gemini Workspace
# ════════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="gemini-beam"></div>', unsafe_allow_html=True)

st.markdown(
    '<div class="main-header">'
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">'
    '<h1>✨ Second Brain</h1>'
    '<span style="background:rgba(66,133,244,0.15);color:#A8C7FA;border:1px solid rgba(66,133,244,0.3);padding:4px 14px;border-radius:20px;font-size:0.75rem;font-weight:600;">✨ Gemini AI Core</span>'
    '</div>'
    "<p>Your AI-powered personal knowledge & productivity assistant — "
    "chat naturally, search documents with RAG, manage notes & tasks, and generate daily briefings.</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Quick stats row ───────────────────────────────────────────────────────────
try:
    all_tasks = tasks_ag.list_tasks()
    all_notes = notes_ag.list_notes()
    pending_count = sum(1 for t in all_tasks if t["status"] == "pending")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            f'<div class="stat-box"><div class="stat-number">{len(all_notes)}</div>'
            '<div class="stat-label">Notes</div></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f'<div class="stat-box"><div class="stat-number">{len(all_tasks)}</div>'
            '<div class="stat-label">Tasks</div></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            f'<div class="stat-box"><div class="stat-number">{pending_count}</div>'
            '<div class="stat-label">Pending</div></div>',
            unsafe_allow_html=True,
        )
    with s4:
        kb_status = "READY" if st.session_state["kb_built"] else "EMPTY"
        st.markdown(
            f'<div class="stat-box"><div class="stat-number" style="font-size:1.5rem;">{kb_status}</div>'
            '<div class="stat-label">Knowledge Base</div></div>',
            unsafe_allow_html=True,
        )
except Exception:
    pass

st.markdown("<br>", unsafe_allow_html=True)

# ── Gemini Smart Launcher Chips ───────────────────────────────────────────────
st.markdown('<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.08em;color:#A8C7FA;margin-bottom:0.4rem;">💡 SMART PROMPT CHIPS</div>', unsafe_allow_html=True)
sc1, sc2, sc3, sc4, sc5 = st.columns(5)
pending_chip_input = None

with sc1:
    if st.button("✨ Daily Briefing", key="chip_briefing", use_container_width=True):
        pending_chip_input = "Generate my daily briefing for today"
with sc2:
    if st.button("🔍 Search Docs", key="chip_kb", use_container_width=True):
        pending_chip_input = "What documents are in my knowledge base?"
with sc3:
    if st.button("📝 Recent Notes", key="chip_notes", use_container_width=True):
        pending_chip_input = "Show and summarize my recent notes"
with sc4:
    if st.button("✅ Critical Tasks", key="chip_tasks", use_container_width=True):
        pending_chip_input = "List all my pending high priority tasks"
with sc5:
    if st.button("📧 Draft Email", key="chip_email", use_container_width=True):
        pending_chip_input = "Draft a professional update email"

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════════

tab_chat, tab_briefing, tab_knowledge, tab_notes, tab_tasks, tab_email = st.tabs(
    ["💬 Chat Workspace", "🌅 Daily Briefing", "🔍 Knowledge RAG", "📝 Notes", "✅ Tasks", "📧 Email"]
)

# ─── TAB 1: CHAT WORKSPACE ───────────────────────────────────────────────────

with tab_chat:
    st.markdown('<div class="section-header">Gemini Conversational Core</div>', unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "✨"):
            meta = msg.get("meta", {})
            intent = meta.get("intent", "")
            if intent and msg["role"] == "assistant":
                st.markdown(f'<div class="intent-tag">🎯 {intent}</div>', unsafe_allow_html=True)
            st.markdown(msg["content"])

            # Inline data for notes/tasks responses
            if meta.get("type") == "notes" and meta.get("data"):
                with st.expander(f"📝 {len(meta['data'])} note(s)", expanded=False):
                    for n in meta["data"][:8]:
                        st.markdown(
                            f'<div class="card"><b>{n["title"]}</b>'
                            f'<br><span style="color:#C4C7C5;font-size:0.85rem;">{n["content"][:120]}…</span></div>',
                            unsafe_allow_html=True,
                        )

            if meta.get("type") == "tasks" and meta.get("data"):
                with st.expander(f"✅ {len(meta['data'])} task(s)", expanded=False):
                    for t in meta["data"][:10]:
                        badge = _priority_badge(t.get("priority", "medium"))
                        st.markdown(
                            f'<div class="card">{badge} <b>{t["title"]}</b>'
                            f'<br><span style="color:#C4C7C5;font-size:0.82rem;">Status: {t["status"]}'
                            + (f" · Due {t['due_date']}" if t.get("due_date") else "")
                            + "</span></div>",
                            unsafe_allow_html=True,
                        )

            if meta.get("type") == "knowledge" and meta.get("sources"):
                st.caption("📄 Sources: " + ", ".join(meta["sources"]))

            if meta.get("type") == "briefing" and meta.get("briefing"):
                st.info(f"Daily briefing generated! Switch to the **🌅 Daily Briefing** tab to view it.")

    # Email delivery option for long-running queries
    with st.expander("📩 Long Query Email Options (Send answers directly to your inbox)", expanded=False):
        c_em1, c_em2 = st.columns([1, 2])
        with c_em1:
            send_to_email = st.checkbox(
                "Email answers to me",
                value=st.session_state.get("auto_email_response", False),
                key="cb_send_email",
                help="Automatically emails generated responses to your inbox.",
            )
            st.session_state["auto_email_response"] = send_to_email
        with c_em2:
            to_email_input = st.text_input(
                "Recipient Email Address",
                value=st.session_state.get("user_email_recipient", ""),
                placeholder="your_email@domain.com",
                key="input_user_email",
            )
            if to_email_input:
                st.session_state["user_email_recipient"] = to_email_input.strip()

    # Chat input
    user_input = st.chat_input("Ask anything — search docs, manage notes, add tasks, get research…")
    if pending_chip_input:
        user_input = pending_chip_input

    if user_input:
        _add_chat("user", user_input)
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking…"):
                result = coord.handle_user_message(user_input, dict(st.session_state))

            intent = result.get("intent", "chat")
            st.markdown(f'<div class="intent-tag">🎯 {intent}</div>', unsafe_allow_html=True)

            # Handle briefing redirect
            if result.get("type") == "briefing" and result.get("briefing"):
                st.session_state["last_briefing"] = result["briefing"]
                response_text = result.get("response", "Daily briefing ready!")
                st.markdown(response_text)
                st.info("Switch to the **🌅 Daily Briefing** tab to view the full briefing.")

            else:
                # Format response text
                raw_resp = result.get("response") or result.get("answer") or result.get("summary", "")
                if not isinstance(raw_resp, str):
                    import json as _json
                    raw_resp = _json.dumps(raw_resp, indent=2, default=str)
                response_text = raw_resp
                st.markdown(response_text)

                # Inline data previews
                if result.get("type") == "notes" and result.get("data"):
                    with st.expander(f"📝 {len(result['data'])} note(s)", expanded=True):
                        for n in result["data"][:6]:
                            st.markdown(
                                f'<div class="card"><b>{n["title"]}</b>'
                                f'<br><span style="color:#9090c0;font-size:0.85rem;">{n["content"][:150]}…</span></div>',
                                unsafe_allow_html=True,
                            )

                if result.get("type") == "tasks" and result.get("data"):
                    with st.expander(f"✅ {len(result['data'])} task(s)", expanded=True):
                        for t in result["data"][:8]:
                            badge = _priority_badge(t.get("priority", "medium"))
                            st.markdown(
                                f'<div class="card">{badge} <b>{t["title"]}</b>'
                                f'<br><span style="color:#9090c0;font-size:0.82rem;">Status: {t["status"]}'
                                + (f" · Due {t['due_date']}" if t.get("due_date") else "")
                                + "</span></div>",
                                unsafe_allow_html=True,
                            )

                if result.get("sources"):
                    st.caption("📄 Sources: " + ", ".join(result["sources"]))

            # Send email via SMTP if user enabled email delivery option
            recipient_addr = st.session_state.get("user_email_recipient")
            if st.session_state.get("auto_email_response") and recipient_addr:
                from core.email_sender import send_email_async

                send_email_async(
                    to_email=recipient_addr,
                    subject=f"🧠 Second Brain AI Answer: {user_input[:35]}…",
                    body=(
                        f"Hi,\n\nHere is the answer to your query from Second Brain AI Assistant:\n\n"
                        f"--- QUERY ---\n{user_input}\n\n"
                        f"--- ANSWER ---\n{response_text}\n\n"
                        f"---\nSent automatically via Google SMTP."
                    ),
                    sender_email=st.session_state.get("smtp_email", ""),
                    app_password=st.session_state.get("smtp_app_password", ""),
                )
                _log_tool(f"Dispatched background email to {recipient_addr}")
                st.info(f"📩 Answer sent to **{recipient_addr}** via Google SMTP!")

            _add_chat("assistant", response_text, meta={**result, "intent": intent})
            _log_tool(f"handle_user_message → intent={intent}")

        st.rerun()


# ─── TAB 2: DAILY BRIEFING ────────────────────────────────────────────────────

with tab_briefing:
    st.markdown('<div class="section-header">Daily Briefing Generator</div>', unsafe_allow_html=True)
    st.markdown(
        "Generate a personalised briefing from your **tasks**, **notes**, **email**, "
        "and **latest AI/tech news** — all in one click."
    )

    if st.button("🌅 Generate Today's Briefing", use_container_width=True):
        with st.spinner("Gathering data from all agents in parallel…"):
            briefing = coord.generate_daily_briefing(settings.DEFAULT_USER_ID, dict(st.session_state))
        st.session_state["last_briefing"] = briefing
        _log_tool("generate_daily_briefing → RunnableParallel complete")
        st.success("Briefing generated! ✨")

    b = st.session_state.get("last_briefing")
    if b:
        # Support both dict and Pydantic object
        from schemas.briefing import DailyBriefing as _DB

        if isinstance(b, dict):
            try:
                b = _DB(**b)
            except Exception:
                pass

        if isinstance(b, _DB):
            st.markdown(
                f'<div class="briefing-section">'
                f'<b>📌 Summary</b><br>{b.daily_summary}</div>',
                unsafe_allow_html=True,
            )

            col_a, col_b = st.columns(2)

            with col_a:
                if b.pending_tasks:
                    with st.expander(f"✅ Pending Tasks ({len(b.pending_tasks)})", expanded=True):
                        for t in b.pending_tasks:
                            st.markdown(f"- {t}")

                if b.important_emails:
                    with st.expander(f"📧 Important Emails ({len(b.important_emails)})", expanded=True):
                        for e in b.important_emails:
                            st.markdown(f"- {e}")

                if b.latest_research:
                    with st.expander(f"🔬 Latest Research ({len(b.latest_research)})", expanded=True):
                        for r in b.latest_research:
                            st.markdown(f"- {r}")

            with col_b:
                if b.knowledge_base_highlights:
                    with st.expander(f"📚 Knowledge Highlights ({len(b.knowledge_base_highlights)})", expanded=True):
                        for h in b.knowledge_base_highlights:
                            st.markdown(f"- {h}")

                if b.recommendations:
                    with st.expander(f"💡 Recommendations ({len(b.recommendations)})", expanded=True):
                        for rec in b.recommendations:
                            st.markdown(f"- {rec}")

                if b.next_actions:
                    with st.expander(f"🚀 Next Actions ({len(b.next_actions)})", expanded=True):
                        for i, action in enumerate(b.next_actions, 1):
                            st.markdown(f"{i}. {action}")

            # Download & Email
            st.markdown("---")
            txt = b.to_text()
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                st.download_button(
                    "⬇️ Download Briefing as TXT",
                    data=txt,
                    file_name=f"briefing_{date.today().isoformat()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with bcol2:
                briefing_recipient = st.text_input(
                    "Recipient Email Address",
                    value=st.session_state.get("user_email_recipient", ""),
                    placeholder="user@domain.com",
                    key="briefing_email_input",
                )
                if st.button("📩 Send Briefing via Email", key="send_briefing_email_btn", use_container_width=True):
                    if briefing_recipient:
                        from core.email_sender import send_email_via_smtp

                        res = send_email_via_smtp(
                            to_email=briefing_recipient,
                            subject=f"🌅 Daily Briefing — {date.today().isoformat()}",
                            body=txt,
                            sender_email=st.session_state.get("smtp_email", ""),
                            app_password=st.session_state.get("smtp_app_password", ""),
                        )
                        if res.get("success"):
                            st.success(res["message"])
                            _log_tool(f"Sent briefing email to {briefing_recipient}")
                        else:
                            st.error(res["error"])
                    else:
                        st.warning("Please enter a valid recipient email address.")
    else:
        st.markdown(
            '<div class="card" style="text-align:center;padding:3rem;">'
            "<h3 style='color:#5a5a8a;margin:0;'>No briefing yet</h3>"
            "<p style='color:#4a4a7a;'>Click the button above to generate your daily briefing.</p>"
            "</div>",
            unsafe_allow_html=True,
        )


# ─── TAB 3: KNOWLEDGE SEARCH ──────────────────────────────────────────────────

with tab_knowledge:
    st.markdown('<div class="section-header">Search Your Knowledge Base</div>', unsafe_allow_html=True)

    if not st.session_state["kb_built"]:
        st.warning("⚠️ Knowledge base is empty. Upload documents in the sidebar and click **Build Knowledge Base**.")
    else:
        st.markdown(f"Knowledge base active · **{st.session_state['kb_num_chunks']}** indexed chunks")

    kb_query = st.text_input(
        "Ask a question about your documents",
        placeholder="What are the key concepts in chapter 3?",
        key="kb_query_input",
    )

    if st.button("🔍 Search", key="kb_search_btn") and kb_query:
        with st.spinner("Retrieving and generating answer…"):
            result = knowledge_agent.answer(kb_query)
            _log_tool(f"knowledge_agent.answer: {kb_query[:40]}")

        st.markdown("### 💡 Answer")
        st.markdown(
            f'<div class="briefing-section">{result["answer"]}</div>',
            unsafe_allow_html=True,
        )

        if result.get("sources"):
            st.caption("📄 Sources: " + " · ".join(result["sources"]))

        if result.get("documents"):
            with st.expander(f"📄 Retrieved Chunks ({len(result['documents'])})", expanded=False):
                for i, doc in enumerate(result["documents"], 1):
                    score = doc.get("score", 0)
                    src = doc.get("metadata", {}).get("source", "unknown")
                    st.markdown(
                        f'<div class="card"><b>Chunk {i}</b> · Score: {score:.4f} · Source: `{src}`'
                        f'<br><span style="color:#9090c0;font-size:0.85rem;">{doc["content"]}</span></div>',
                        unsafe_allow_html=True,
                    )

    # Similarity search (raw)
    with st.expander("🔎 Raw Similarity Search (no LLM)", expanded=False):
        raw_q = st.text_input("Similarity query", placeholder="Exact topic to search…", key="raw_q")
        if st.button("Search chunks", key="raw_search"):
            from core.vectorstore import query_knowledge_base

            res = query_knowledge_base(raw_q)
            if res.get("error"):
                st.error(res["error"])
            else:
                for i, doc in enumerate(res["documents"], 1):
                    st.markdown(
                        f'<div class="card"><b>#{i}</b> · Score: {doc["score"]}'
                        f'<br>{doc["content"][:400]}</div>',
                        unsafe_allow_html=True,
                    )


# ─── TAB 4: NOTES ─────────────────────────────────────────────────────────────

with tab_notes:
    st.markdown('<div class="section-header">Notes Manager</div>', unsafe_allow_html=True)

    # Create note form
    with st.expander("➕ Create New Note", expanded=False):
        with st.form("create_note_form"):
            n_title = st.text_input("Title *", placeholder="Note title…")
            n_content = st.text_area("Content", height=120, placeholder="Write your note here…")
            n_tags = st.text_input("Tags (comma-separated)", placeholder="python, ml, project")
            submitted = st.form_submit_button("💾 Save Note", use_container_width=True)
            if submitted:
                if n_title.strip():
                    tags = [t.strip() for t in n_tags.split(",") if t.strip()]
                    notes_ag.create_note(n_title.strip(), n_content, tags)
                    _log_tool(f"Created note: {n_title}")
                    st.success("Note saved!")
                    st.rerun()
                else:
                    st.warning("Title is required.")

    # Search
    col_s, col_c = st.columns([4, 1])
    with col_s:
        notes_search = st.text_input("🔍 Search notes", placeholder="Search by title or content…", key="notes_search_main")
    with col_c:
        st.markdown("<br>", unsafe_allow_html=True)

    # List notes
    notes_list = notes_ag.list_notes(filter_query=notes_search)
    st.markdown(f"**{len(notes_list)}** note(s) found")

    for note in notes_list:
        nid = note["id"]
        is_editing = st.session_state.get("notes_editing") == nid

        with st.expander(f"📝 {note['title']}", expanded=is_editing):
            if is_editing:
                edit_title = st.text_input("Title", value=note["title"], key=f"et_{nid}")
                edit_content = st.text_area("Content", value=note["content"], height=120, key=f"ec_{nid}")
                edit_tags = st.text_input(
                    "Tags", value=", ".join(note.get("tags", [])), key=f"etg_{nid}"
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("💾 Save", key=f"save_{nid}", use_container_width=True):
                        tags_upd = [t.strip() for t in edit_tags.split(",") if t.strip()]
                        notes_ag.update_note(nid, edit_title, edit_content, tags_upd)
                        st.session_state["notes_editing"] = None
                        _log_tool(f"Updated note: {edit_title}")
                        st.rerun()
                with c2:
                    if st.button("✖ Cancel", key=f"cancel_{nid}", use_container_width=True):
                        st.session_state["notes_editing"] = None
                        st.rerun()
            else:
                st.markdown(
                    f'<div class="card">'
                    f'<span style="color:#9090c0;font-size:0.82rem;">'
                    f'Updated: {note["updated_at"][:10]}'
                    + (f" · 🏷️ {', '.join(note['tags'])}" if note.get("tags") else "")
                    + "</span><br><br>"
                    + note["content"].replace("\n", "<br>")
                    + "</div>",
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ Edit", key=f"edit_{nid}", use_container_width=True):
                        st.session_state["notes_editing"] = nid
                        st.rerun()
                with c2:
                    if st.button("🗑️ Delete", key=f"del_{nid}", use_container_width=True):
                        notes_ag.delete_note(nid)
                        _log_tool(f"Deleted note: {note['title']}")
                        st.rerun()


# ─── TAB 5: TASKS ─────────────────────────────────────────────────────────────

with tab_tasks:
    st.markdown('<div class="section-header">Task Manager</div>', unsafe_allow_html=True)

    # Create task form
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("create_task_form"):
            tc1, tc2 = st.columns([3, 1])
            with tc1:
                t_title = st.text_input("Title *", placeholder="Task title…")
            with tc2:
                t_priority = st.selectbox("Priority", ["medium", "low", "high", "critical"])
            t_desc = st.text_area("Description (optional)", height=70, placeholder="More details…")
            td1, td2 = st.columns(2)
            with td1:
                t_due = st.date_input("Due date (optional)", value=None)
            with td2:
                t_tags = st.text_input("Tags", placeholder="work, study, project")
            t_sub = st.form_submit_button("➕ Add Task", use_container_width=True)
            if t_sub:
                if t_title.strip():
                    due_str = str(t_due) if t_due else None
                    tags = [x.strip() for x in t_tags.split(",") if x.strip()]
                    tasks_ag.add_task(t_title.strip(), t_desc, priority=t_priority, due_date=due_str, tags=tags)
                    _log_tool(f"Added task: {t_title}")
                    st.success("Task added!")
                    st.rerun()
                else:
                    st.warning("Title is required.")

    # Filter + Stats row
    f_col, stat_col = st.columns([2, 3])
    with f_col:
        task_filter = st.selectbox(
            "Filter", ["all", "pending", "in_progress", "completed", "cancelled"],
            key="task_filter_main"
        )
    with stat_col:
        try:
            stats = tasks_ag.stats()
            total = stats.get("total", 0)
            completed_n = stats.get("completed", 0)
            rate = stats.get("completion_rate", 0)
            st.markdown(
                f'<div class="stat-box" style="text-align:left;padding:0.5rem 1rem;">'
                f'<span style="font-size:0.85rem;">📊 Total: <b>{total}</b> · '
                f'Completed: <b>{completed_n}</b> · '
                f'Pending: <b>{stats.get("pending",0)}</b> · '
                f'Rate: <b>{rate}%</b></span></div>',
                unsafe_allow_html=True,
            )
            if total > 0:
                st.progress(int(rate))
        except Exception:
            pass

    task_list = tasks_ag.list_tasks(filter=task_filter if task_filter != "all" else None)
    st.markdown(f"**{len(task_list)}** task(s)")

    for task in task_list:
        tid = task["id"]
        badge = _priority_badge(task.get("priority", "medium"))
        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "cancelled": "❌"}.get(task["status"], "📌")
        due_str = f" · Due {task['due_date']}" if task.get("due_date") else ""

        with st.expander(f"{status_icon} {task['title']}", expanded=False):
            st.markdown(
                f'<div class="card">'
                f'{badge} <span style="color:#9090c0;font-size:0.82rem;">Status: <b>{task["status"]}</b>{due_str}</span>'
                + (f"<br><span style='color:#c0c0e8;'>{task['description']}</span>" if task.get("description") else "")
                + (f"<br><span style='color:#7070a0;font-size:0.8rem;'>🏷️ {', '.join(task['tags'])}</span>" if task.get("tags") else "")
                + "</div>",
                unsafe_allow_html=True,
            )
            tc1, tc2, tc3 = st.columns(3)
            with tc1:
                if task["status"] != "completed":
                    if st.button("✅ Complete", key=f"comp_{tid}", use_container_width=True):
                        tasks_ag.mark_complete(tid)
                        _log_tool(f"Completed: {task['title']}")
                        st.rerun()
            with tc2:
                new_status = st.selectbox(
                    "Status", ["pending", "in_progress", "completed", "cancelled"],
                    index=["pending", "in_progress", "completed", "cancelled"].index(task["status"]),
                    key=f"status_{tid}",
                )
                if new_status != task["status"]:
                    tasks_ag.update_task(tid, status=new_status)
                    st.rerun()
            with tc3:
                if st.button("🗑️ Delete", key=f"deltask_{tid}", use_container_width=True):
                    tasks_ag.delete_task(tid)
                    _log_tool(f"Deleted task: {task['title']}")
                    st.rerun()

    # Stats table
    if task_list:
        with st.expander("📊 Task Statistics (Python Tool)", expanded=False):
            stats = tasks_ag.stats()
            table = stats.get("table", [])
            if table:
                import pandas as pd

                df = pd.DataFrame(table)
                st.dataframe(df, use_container_width=True, hide_index=True)

            s_cols = st.columns(4)
            metrics = [
                ("Total", stats.get("total", 0)),
                ("Completed", stats.get("completed", 0)),
                ("Pending", stats.get("pending", 0)),
                ("Rate", f"{stats.get('completion_rate', 0)}%"),
            ]
            for col, (label, val) in zip(s_cols, metrics):
                col.metric(label, val)


# ─── TAB 6: EMAIL ─────────────────────────────────────────────────────────────

with tab_email:
    st.markdown('<div class="section-header">Email Manager</div>', unsafe_allow_html=True)

    # Inbox summary
    ecol1, ecol2 = st.columns([1, 1])

    with ecol1:
        st.markdown("#### 📬 Inbox")
        inbox = email_ag.get_inbox()
        unread = [e for e in inbox if not e["read"]]
        st.caption(f"{len(inbox)} total · {len(unread)} unread")

        for e in inbox:
            read_icon = "📧" if not e["read"] else "📨"
            imp_icon = "⭐" if e["important"] else ""
            with st.expander(f"{read_icon}{imp_icon} {e['subject']}", expanded=False):
                st.markdown(
                    f'<div class="card">'
                    f'<b>From:</b> {e["from"]}<br>'
                    f'<b>Date:</b> {e["date"]}<br><br>'
                    f'{e["body"]}</div>',
                    unsafe_allow_html=True,
                )

    with ecol2:
        st.markdown("#### 🤖 AI Summary")
        if st.button("Summarise Unread Emails", use_container_width=True):
            with st.spinner("Summarising…"):
                result = email_ag.summarize_inbox(unread_only=True)
                _log_tool("email_agent.summarize_inbox")
            st.markdown(
                f'<div class="briefing-section">{result["summary"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("#### ✍️ Draft an Email")
        draft_instructions = st.text_area(
            "Describe the email to draft",
            placeholder="e.g. Reply to my professor confirming I'll submit the project by Friday evening.",
            height=100,
            key="draft_instructions",
        )
        draft_context = st.text_area(
            "Additional context (optional)",
            height=60,
            placeholder="Subject, tone, recipient name…",
            key="draft_context",
        )
        if st.button("✍️ Generate Draft", use_container_width=True) and draft_instructions:
            with st.spinner("Drafting…"):
                draft = email_ag.draft_email(draft_instructions, draft_context)
                st.session_state["email_draft"] = draft
                _log_tool("email_agent.draft_email")
            st.rerun()

        if st.session_state.get("email_draft"):
            st.markdown("#### 📄 Generated Draft")
            st.text_area("Email body", value=st.session_state["email_draft"], height=200, key="draft_display")
            st.download_button(
                "⬇️ Download Draft",
                data=st.session_state["email_draft"],
                file_name="email_draft.txt",
                mime="text/plain",
            )

        st.markdown("---")
        st.markdown("#### 📤 Send Live Email (Google SMTP)")
        with st.form("send_live_email_form"):
            live_to = st.text_input("To Email *", placeholder="recipient@example.com", key="live_to_input")
            live_sub = st.text_input("Subject *", placeholder="Subject line…", key="live_sub_input")
            live_body = st.text_area("Body", value=st.session_state.get("email_draft", ""), height=150, key="live_body_input")
            sent_submit = st.form_submit_button("🚀 Send Email via Google SMTP", use_container_width=True)
            if sent_submit:
                if live_to.strip() and live_sub.strip():
                    from core.email_sender import send_email_via_smtp

                    with st.spinner("Sending email via Google SMTP…"):
                        res = send_email_via_smtp(
                            to_email=live_to.strip(),
                            subject=live_sub.strip(),
                            body=live_body,
                            sender_email=st.session_state.get("smtp_email", ""),
                            app_password=st.session_state.get("smtp_app_password", ""),
                        )
                    if res.get("success"):
                        st.success(res["message"])
                        _log_tool(f"Sent SMTP email to {live_to}")
                    else:
                        st.error(res["error"])
                else:
                    st.warning("Recipient email and subject are required.")


# ════════════════════════════════════════════════════════════════════════════════
# COMMON EXPANDERS — bottom of page
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("### 🛠️ Debug & Execution Info")

exp1, exp2, exp3, exp4 = st.columns(4)

with st.expander("🔧 Tool Execution Log", expanded=False):
    if st.session_state["tool_log"]:
        for entry in reversed(st.session_state["tool_log"]):
            st.markdown(f"`{entry}`")
    else:
        st.caption("No tool calls yet.")

with st.expander("📄 Retrieved Documents", expanded=False):
    up_files = st.session_state.get("uploaded_files", [])
    if up_files:
        for f in up_files:
            st.markdown(f"- 📎 `{f['name']}`")
    else:
        st.caption("No documents uploaded yet.")

with st.expander("📧 Email Quick View", expanded=False):
    important = email_ag.get_important_emails()
    for e in important:
        st.markdown(f"- ⭐ **{e['subject']}** — *{e['from']}*")

with st.expander("📝 Recent Notes", expanded=False):
    recent_n = notes_ag.list_notes()[:5]
    if recent_n:
        for n in recent_n:
            st.markdown(f"- **{n['title']}** · {n['updated_at'][:10]}")
    else:
        st.caption("No notes yet.")

with st.expander("✅ Pending Tasks", expanded=False):
    pending_t = tasks_ag.list_tasks(filter="pending")[:8]
    if pending_t:
        for t in pending_t:
            badge_html = _priority_badge(t.get("priority", "medium"))
            st.markdown(
                f'{badge_html} **{t["title"]}**'
                + (f" · Due {t['due_date']}" if t.get("due_date") else ""),
                unsafe_allow_html=True,
            )
    else:
        st.caption("No pending tasks.")

st.markdown(
    '<p style="text-align:center;color:#3a3a6a;font-size:0.75rem;margin-top:2rem;">'
    "🧠 Second Brain · Built with LangChain + ChromaDB + Groq LLaMA 3.3 · Final Year Project"
    "</p>",
    unsafe_allow_html=True,
)
