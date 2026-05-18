"""SchemeShield AI Streamlit app."""

import html

import pandas as pd
import streamlit as st

from utils.eligibility import (
    find_eligible_schemes,
    get_recommended_schemes,
    load_schemes,
)
from utils.fraud_detector import analyze_scheme_message


# Safety warning is kept in one place so every page gives consistent guidance.
SAFETY_WARNING = (
    "Do not share OTP, bank details, Aadhaar photo, or pay money without "
    "verifying from official sources."
)

WHY_THIS_MATTERS = (
    "Official portals help users apply. SchemeShield AI helps users understand, "
    "verify, and decide before they apply."
)

SAMPLE_FAKE_MESSAGE = (
    "Congratulations! You have been selected for PM Modi Gift Scheme. You will "
    "receive \u20b910,000 in your bank account. Pay \u20b999 processing fee and "
    "share your bank details to claim now."
)

SAMPLE_ELIGIBILITY_PROFILE = {
    "name": "Riya",
    "state": "Rajasthan",
    "age": 20,
    "annual_income": 180000,
    "user_type": "Student",
    "category": "SC",
    "location_type": "Rural",
}

SAMPLE_ELIGIBILITY_WIDGET_VALUES = {
    "name": SAMPLE_ELIGIBILITY_PROFILE["name"],
    "state": SAMPLE_ELIGIBILITY_PROFILE["state"],
    "age": int(SAMPLE_ELIGIBILITY_PROFILE["age"]),
    "income": int(SAMPLE_ELIGIBILITY_PROFILE["annual_income"]),
    "user_type": SAMPLE_ELIGIBILITY_PROFILE["user_type"],
    "category": SAMPLE_ELIGIBILITY_PROFILE["category"],
    "location_type": SAMPLE_ELIGIBILITY_PROFILE["location_type"],
}

# Dropdown options include all Indian states plus Delhi for the sample dataset.
STATE_OPTIONS = [
    "All India",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]

PAGE_OPTIONS = ["Impact Dashboard", "Fraud Detector", "Scheme Eligibility"]

AUTO_FILL_WIDGET_DEFAULTS = {
    "fraud_message": "",
    "name": "",
    "state": "All India",
    "age": 20,
    "income": 200000,
    "user_type": "Student",
    "category": "General",
    "location_type": "Rural",
}

AUTO_FILL_WIDGET_KEYS = list(AUTO_FILL_WIDGET_DEFAULTS.keys())


def apply_custom_css():
    """Apply stable dark theme styling without changing Streamlit behavior."""
    st.markdown(
        """
        <style>
        :root {
            --navy-950: #030712;
            --navy-900: #071426;
            --navy-800: #0b1d33;
            --cyan-400: #22d3ee;
            --cyan-300: #67e8f9;
            --blue-500: #3b82f6;
            --text-main: #f8fafc;
            --text-muted: #cbd5e1;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --card-bg: rgba(15, 30, 80, 0.70);
            --card-bg-strong: rgba(8, 22, 55, 0.88);
            --card-border: rgba(103, 232, 249, 0.24);
        }

        ::selection {
            background: #22c55e !important;
            color: #000000 !important;
        }

        ::-moz-selection {
            background: #22c55e !important;
            color: #000000 !important;
        }

        textarea::selection,
        input::selection,
        code::selection {
            background: #22c55e !important;
            color: #000000 !important;
        }

        textarea::-moz-selection,
        input::-moz-selection,
        code::-moz-selection {
            background: #22c55e !important;
            color: #000000 !important;
        }

        @keyframes cardEnter {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        [data-testid="stDecoration"],
        #MainMenu,
        footer {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }

        /* Keep Streamlit header available so the native sidebar expand button works. */
        [data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            background: transparent !important;
        }

        /* Do not force-hide the toolbar/header area; sidebar controls depend on it. */
        [data-testid="stToolbar"] {
            background: transparent !important;
        }

        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            z-index: 999999 !important;
        }

        [data-testid="stSidebar"] {
            pointer-events: auto !important;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(34, 211, 238, 0.18), transparent 32rem),
                radial-gradient(circle at 86% 18%, rgba(59, 130, 246, 0.14), transparent 30rem),
                radial-gradient(circle at 50% 110%, rgba(14, 165, 233, 0.10), transparent 38rem),
                linear-gradient(135deg, #020617 0%, #071426 48%, #0b1d33 100%);
            color: var(--text-main);
        }

        html,
        body,
        .stApp {
            overflow-x: hidden;
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                radial-gradient(circle at 18% 22%, rgba(34, 211, 238, 0.08), transparent 18rem),
                radial-gradient(circle at 78% 36%, rgba(59, 130, 246, 0.08), transparent 22rem);
            z-index: 0;
        }

        .stApp > div {
            position: relative;
            z-index: 1;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(2, 6, 23, 0.98) 0%, rgba(7, 20, 38, 0.96) 100%);
            border-right: 1px solid rgba(103, 232, 249, 0.16);
            box-shadow: 12px 0 36px rgba(0, 0, 0, 0.22);
        }

        [data-testid="stSidebar"] * {
            color: var(--text-main);
        }

        [data-testid="stSidebar"] [data-testid="stAlert"] {
            background: rgba(15, 30, 80, 0.60);
            border: 1px solid rgba(103, 232, 249, 0.20);
            border-radius: 16px;
            color: var(--text-main);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            border-radius: 12px;
            padding: 0.25rem 0.35rem;
        }

        .block-container {
            padding-top: 0.6rem;
            padding-bottom: 2rem;
            max-width: 1040px;
        }

        h1, h2, h3, h4, h5, h6, p, li, label, span {
            color: var(--text-main);
        }

        p, li, .stMarkdown, [data-testid="stCaptionContainer"] {
            color: var(--text-muted);
        }

        .hero-card {
            padding: 1.55rem 1.75rem;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(15, 30, 80, 0.78), rgba(8, 22, 55, 0.78));
            border: 1px solid rgba(103, 232, 249, 0.34);
            box-shadow:
                0 22px 54px rgba(0, 0, 0, 0.32),
                0 0 34px rgba(34, 211, 238, 0.10);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            margin-bottom: 0.9rem;
            animation: cardEnter 0.45s ease both;
            transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
        }

        .hero-card:hover {
            transform: translateY(-2px);
            border-color: rgba(103, 232, 249, 0.48);
            box-shadow:
                0 26px 64px rgba(0, 0, 0, 0.36),
                0 0 42px rgba(34, 211, 238, 0.14);
        }

        .hero-kicker {
            color: var(--cyan-400);
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .hero-title {
            color: var(--text-main);
            font-size: 2.45rem;
            line-height: 1.05;
            font-weight: 800;
            margin: 0;
        }

        .hero-subtitle {
            color: #dbeafe;
            font-size: 1.05rem;
            font-weight: 650;
            margin-top: 0.4rem;
        }

        .hero-description {
            color: var(--text-muted);
            max-width: 760px;
            margin-top: 0.45rem;
            margin-bottom: 0;
            font-size: 0.95rem;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            box-shadow: 0 16px 38px rgba(0, 0, 0, 0.24);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            animation: cardEnter 0.38s ease both;
            transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-2px);
            border-color: rgba(103, 232, 249, 0.38);
            box-shadow: 0 22px 48px rgba(0, 0, 0, 0.30);
        }

        div.stButton > button,
        div.stFormSubmitButton > button {
            background: linear-gradient(135deg, var(--cyan-300), var(--cyan-400) 42%, var(--blue-500));
            color: #020617;
            border: 0;
            border-radius: 14px;
            font-weight: 800;
            min-height: 2.7rem;
            box-shadow: 0 10px 24px rgba(34, 211, 238, 0.22);
            transition: transform 0.25s ease, box-shadow 0.25s ease, filter 0.25s ease;
        }

        div.stButton > button:hover,
        div.stFormSubmitButton > button:hover {
            color: #020617;
            transform: translateY(-2px);
            filter: saturate(1.06);
            box-shadow: 0 16px 34px rgba(34, 211, 238, 0.32);
        }

        div.stTextInput input,
        div.stNumberInput input,
        textarea,
        [data-baseweb="select"] > div {
            background-color: rgba(2, 8, 23, 0.78) !important;
            color: #ffffff !important;
            border: 1px solid rgba(103, 232, 249, 0.30) !important;
            border-radius: 12px !important;
        }

        textarea,
        input {
            color: #ffffff !important;
        }

        textarea::placeholder,
        input::placeholder {
            color: rgba(203, 213, 225, 0.72) !important;
            opacity: 1 !important;
        }

        [data-baseweb="select"] span,
        [data-baseweb="select"] input {
            color: var(--text-main) !important;
        }

        div[data-baseweb="popover"],
        [data-baseweb="popover"] ul,
        [role="listbox"] {
            background-color: #071426 !important;
            color: var(--text-main) !important;
            border: 1px solid rgba(103, 232, 249, 0.25) !important;
        }

        [role="option"] {
            color: var(--text-main) !important;
            background-color: #071426 !important;
        }

        [role="option"]:hover,
        [aria-selected="true"] {
            background-color: rgba(34, 211, 238, 0.16) !important;
        }

        div.stTextInput input:focus,
        div.stNumberInput input:focus,
        textarea:focus {
            border-color: var(--cyan-400) !important;
            box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.35) !important;
        }

        .metric-card {
            padding: 0.8rem 0.9rem;
            border-radius: 16px;
            background: var(--card-bg);
            border: 1px solid rgba(103, 232, 249, 0.22);
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.20);
            min-height: 88px;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            animation: cardEnter 0.42s ease both;
            transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
        }

        .metric-card::before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 3px;
            background: linear-gradient(90deg, var(--cyan-400), var(--blue-500));
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(103, 232, 249, 0.42);
            box-shadow: 0 18px 42px rgba(0, 0, 0, 0.28);
        }

        @keyframes fadeUp {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        [data-testid="stMainBlockContainer"] {
            animation: fadeUp 0.35s ease both;
        }

        [data-testid="stAlert"] {
            border-radius: 14px;
            animation: fadeUp 0.28s ease both;
        }

        .metric-label {
            color: var(--text-muted);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .metric-value {
            color: var(--text-main);
            font-size: 1.45rem;
            font-weight: 800;
            margin-top: 0.25rem;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.45rem 0.82rem;
            font-size: 0.9rem;
            font-weight: 800;
            border: 1px solid transparent;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }

        .status-real {
            color: #dcfce7;
            background: rgba(34, 197, 94, 0.18);
            border-color: rgba(34, 197, 94, 0.50);
            box-shadow: 0 0 22px rgba(34, 197, 94, 0.10);
        }

        .status-warning {
            color: #ffedd5;
            background: rgba(245, 158, 11, 0.20);
            border-color: rgba(245, 158, 11, 0.54);
            box-shadow: 0 0 22px rgba(245, 158, 11, 0.12);
        }

        .status-danger {
            color: #fee2e2;
            background: rgba(239, 68, 68, 0.20);
            border-color: rgba(239, 68, 68, 0.62);
            box-shadow: 0 0 0 1px rgba(239, 68, 68, 0.16), 0 0 28px rgba(239, 68, 68, 0.14);
        }

        .danger-panel {
            padding: 1rem;
            border-radius: 14px;
            background: rgba(127, 29, 29, 0.32);
            border: 1px solid rgba(239, 68, 68, 0.45);
        }

        .subtle-panel {
            padding: 1rem;
            border-radius: 14px;
            background: rgba(15, 23, 42, 0.42);
            border: 1px solid rgba(148, 163, 184, 0.18);
        }

        .section-eyebrow {
            color: var(--cyan-400);
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }

        div[data-testid="stExpander"] {
            background: rgba(2, 6, 23, 0.46);
            border: 1px solid rgba(103, 232, 249, 0.20);
            border-radius: 14px;
        }

        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, var(--cyan-400), var(--blue-500));
        }

        code {
            color: #dbeafe;
        }

        @media (max-width: 900px) {
            .hero-title {
                font-size: 2.35rem;
            }

            .hero-card {
                padding: 1.55rem;
            }

            .metric-card {
                min-height: 96px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state():
    """Create default values used by the dashboard and different pages."""
    default_values = {
        "fraud_risk_score": 0,
        "fraud_result_category": "Not checked yet",
        "eligible_schemes_count": 0,
        "eligible_schemes_df": pd.DataFrame(),
        "recommended_schemes_df": pd.DataFrame(),
        "last_user_name": "",
        "eligibility_checked": False,
        "active_page": "Impact Dashboard",
        "sample_loaded_message": "",
        "sample_fraud_loaded": False,
        "sample_eligibility_loaded": False,
        "pending_sample_target": "",
        "pending_active_page": "",
    }
    default_values.update(AUTO_FILL_WIDGET_DEFAULTS)

    for key, default_value in default_values.items():
        persisted_key = get_persisted_key(key)
        has_persisted_value = persisted_key in st.session_state

        if key not in st.session_state:
            if has_persisted_value:
                st.session_state[key] = st.session_state[persisted_key]
            else:
                st.session_state[key] = default_value
        elif (
            key in AUTO_FILL_WIDGET_DEFAULTS
            and has_persisted_value
            and st.session_state[key] == default_value
            and st.session_state[persisted_key] != default_value
        ):
            st.session_state[key] = st.session_state[persisted_key]


def get_persisted_key(key):
    """Return the backing-store key used to survive page navigation."""
    return f"persisted_sample_value_{key}"


def sync_persisted_widget_values(keys=None):
    """Store current widget values in stable backing keys."""
    keys_to_sync = keys or AUTO_FILL_WIDGET_KEYS

    for key in keys_to_sync:
        if key in st.session_state:
            st.session_state[get_persisted_key(key)] = st.session_state[key]


def set_autofill_widget_value(key, value, force=False):
    """Set a widget key before rendering so Streamlit shows the new value."""
    if force and key in st.session_state:
        del st.session_state[key]

    st.session_state[key] = value
    st.session_state[get_persisted_key(key)] = value


def restore_loaded_sample_values():
    """Restore loaded sample values if Streamlit widget cleanup removes them."""
    if st.session_state.get("pending_sample_target") == "fraud":
        load_sample_fraud_message(force=True)
    elif st.session_state.get("sample_fraud_loaded") and not st.session_state.get(
        "fraud_message"
    ):
        set_autofill_widget_value("fraud_message", SAMPLE_FAKE_MESSAGE)

    if st.session_state.get("pending_sample_target") == "eligibility":
        load_sample_eligibility_profile(force=True)
    elif st.session_state.get("sample_eligibility_loaded"):
        for key, sample_value in SAMPLE_ELIGIBILITY_WIDGET_VALUES.items():
            default_value = AUTO_FILL_WIDGET_DEFAULTS[key]
            if st.session_state.get(key) == default_value:
                set_autofill_widget_value(key, sample_value)

        sync_persisted_widget_values(SAMPLE_ELIGIBILITY_WIDGET_VALUES.keys())


def preserve_widget_state_across_pages():
    """Keep widget-bound values alive while users navigate between pages."""
    for key in AUTO_FILL_WIDGET_KEYS:
        persisted_key = get_persisted_key(key)
        default_value = AUTO_FILL_WIDGET_DEFAULTS[key]

        if (
            persisted_key in st.session_state
            and st.session_state.get(key) == default_value
            and st.session_state[persisted_key] != default_value
        ):
            st.session_state[key] = st.session_state[persisted_key]

        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
            st.session_state[persisted_key] = st.session_state[key]


def ensure_selectbox_values_are_valid():
    """Avoid Streamlit selectbox errors by falling back to valid options."""
    if st.session_state.get("active_page") not in PAGE_OPTIONS:
        st.session_state["active_page"] = PAGE_OPTIONS[0]

    selectbox_options = {
        "state": STATE_OPTIONS,
        "user_type": ["Student", "Farmer", "Woman", "General"],
        "category": ["General", "OBC", "SC", "ST", "EWS"],
        "location_type": ["Rural", "Urban"],
    }

    for key, options in selectbox_options.items():
        if st.session_state.get(key) not in options:
            st.session_state[key] = options[0]
            st.session_state[get_persisted_key(key)] = options[0]


def render_sample_loaded_feedback():
    """Show one-run feedback after sample data is loaded."""
    if st.session_state.get("sample_loaded_message"):
        st.success(st.session_state["sample_loaded_message"])


def rerun_after_sample_load(message, target_page):
    """Refresh the UI once after a sample button click."""
    st.session_state["sample_loaded_message"] = message
    st.session_state["pending_active_page"] = target_page
    st.rerun()


def apply_pending_navigation():
    """Apply queued page changes before the sidebar widget is rendered."""
    pending_page = st.session_state.get("pending_active_page")
    if pending_page in PAGE_OPTIONS:
        st.session_state["active_page"] = pending_page
    st.session_state["pending_active_page"] = ""


def render_sidebar():
    """Render sidebar navigation and return the selected page name."""
    st.sidebar.title("SchemeShield AI")
    st.sidebar.caption("Citizen safety and scheme discovery")

    selected_page = st.sidebar.radio(
        "Navigate",
        PAGE_OPTIONS,
        key="active_page",
    )

    st.sidebar.divider()
    st.sidebar.info(SAFETY_WARNING)
    return selected_page


def render_hero_section():
    """Show the product hero with premium visual hierarchy."""
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">CITIZEN SAFETY INTELLIGENCE</div>
            <h1 class="hero-title">SchemeShield AI</h1>
            <div class="hero-subtitle">Fraud Detection + Scheme Eligibility Assistant</div>
            <p class="hero-description">
                Verify forwarded scheme messages and discover suitable schemes before
                sharing sensitive details or applying.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label, value):
    """Render a modern metric card using controlled HTML."""
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{safe_label}</div>
            <div class="metric-value">{safe_value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_metrics(total_schemes):
    """Display dashboard metrics that update after fraud and eligibility checks."""
    metric_columns = st.columns(4)

    with metric_columns[0]:
        render_metric_card("Total Schemes", total_schemes)
    with metric_columns[1]:
        render_metric_card("Eligible Matches", st.session_state.eligible_schemes_count)
    with metric_columns[2]:
        render_metric_card(
            "Latest Risk Score",
            f"{st.session_state.fraud_risk_score}/100",
        )
    with metric_columns[3]:
        render_metric_card("Latest Risk Category", st.session_state.fraud_result_category)


def get_safety_advice(category):
    """Return actionable advice based on the current fraud category."""
    if category == "Likely Real":
        return (
            "Low risk signals found, but still verify scheme details on an "
            "official government website or at e-Mitra before sharing documents."
        )

    if category == "Suspicious":
        return (
            "Do not click links or share personal details yet. Check the scheme "
            "name on an official portal and ask an e-Mitra operator if needed."
        )

    return (
        "Stop immediately. Do not pay fees, scan QR codes, share OTP, or send "
        "bank/Aadhaar details. Report the message and verify only from official "
        "sources."
    )


def get_category_badge_class(category):
    """Return the CSS class for a risk category badge."""
    if category == "Likely Real":
        return "status-real"
    if category == "Suspicious":
        return "status-warning"
    return "status-danger"


def render_category_badge(category):
    """Render a color-coded risk category badge."""
    badge_class = get_category_badge_class(category)
    safe_category = html.escape(category)
    st.markdown(
        f'<span class="status-badge {badge_class}">{safe_category}</span>',
        unsafe_allow_html=True,
    )


def render_fraud_result(result):
    """Show fraud score, category, reasons, matched keywords, and safety advice."""
    risk_score = result["score"]
    result_category = result["category"]

    with st.container(border=True):
        st.markdown('<div class="section-eyebrow">Result</div>', unsafe_allow_html=True)
        st.subheader("Risk Score")
        score_columns = st.columns([1, 2])

        with score_columns[0]:
            st.metric("Score", f"{risk_score}/100")
            render_category_badge(result_category)

        with score_columns[1]:
            st.write("Risk level")
            st.progress(risk_score / 100)

        st.markdown("**Hybrid analysis**")
        hybrid_columns = st.columns(5)
        with hybrid_columns[0]:
            st.metric("Rule Score", f"{result.get('rule_score', risk_score)}/100")
        with hybrid_columns[1]:
            st.metric("ML Score", f"{result.get('ml_score', 0)}/100")
        with hybrid_columns[2]:
            st.metric("ML Prediction", str(result.get("ml_label", "real")).title())
        with hybrid_columns[3]:
            st.metric("Confidence", f"{result.get('confidence', 0)}%")
        with hybrid_columns[4]:
            st.metric("Hybrid Final", f"{risk_score}/100")

        if not result.get("model_available", False):
            st.caption("ML model unavailable; showing rule-based fallback result.")

        if result_category == "Likely Fake":
            st.markdown(
                """
                <div class="danger-panel">
                    This message contains high-risk fraud indicators. Treat it as unsafe
                    until verified through official sources.
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.container(border=True):
        st.subheader("Why this result?")
        for reason in result["reasons"]:
            st.markdown(f"- {reason}")

        if result["matched_keywords"]:
            matched_text = ", ".join(result["matched_keywords"])
            st.caption(f"Detected indicators: {matched_text}")

    with st.container(border=True):
        st.subheader("Safety Advice")
        st.write(get_safety_advice(result_category))
        st.warning(SAFETY_WARNING)


def load_sample_fraud_message(force=False):
    """Fill the fraud text area with the sample risky message."""
    st.session_state["sample_fraud_loaded"] = True
    set_autofill_widget_value("fraud_message", SAMPLE_FAKE_MESSAGE, force=force)


def load_sample_fraud_message_from_dashboard():
    """Load sample fraud data from the dashboard helper section."""
    load_sample_fraud_message()
    st.session_state["pending_sample_target"] = "fraud"
    rerun_after_sample_load(
        "Sample fraud message loaded. Redirecting to Fraud Detector...",
        "Fraud Detector",
    )


def render_fraud_sample_section():
    """Render a sample helper for the fraud detector page."""
    with st.expander("Try a sample risky message"):
        st.write(SAMPLE_FAKE_MESSAGE)
        if st.button("Use this message"):
            load_sample_fraud_message_from_dashboard()


def render_fraud_detector_page():
    """Render the fraud detector input and output section."""
    if st.session_state.get("pending_sample_target") == "fraud":
        load_sample_fraud_message(force=True)
        st.session_state["pending_sample_target"] = ""

    st.header("Fraud Detector")
    render_sample_loaded_feedback()

    with st.container(border=True):
        st.markdown(
            '<div class="section-eyebrow">Message verification</div>',
            unsafe_allow_html=True,
        )
        st.write(
            "Paste any WhatsApp, SMS, or social media scheme message. The app "
            "checks critical risk signals like OTP requests, bank details, fees, "
            "short links, and fake government reward language."
        )

        render_fraud_sample_section()

        user_message = st.text_area(
            "Paste scheme message",
            height=180,
            key="fraud_message",
            placeholder=SAMPLE_FAKE_MESSAGE,
        )
        sync_persisted_widget_values(["fraud_message"])

        analyze_button = st.button("Analyze Message", type="primary")

    if analyze_button:
        if not user_message.strip():
            st.warning("Please paste a message before analyzing.")
            return

        result = analyze_scheme_message(user_message)
        st.session_state.fraud_risk_score = result["score"]
        st.session_state.fraud_result_category = result["category"]
        render_fraud_result(result)


def render_scheme_card(scheme):
    """Render one eligible scheme as a professional card."""
    with st.container(border=True):
        st.markdown(f"### **{scheme['scheme_name']}**")
        st.write(scheme["description"])
        st.markdown(f"**Documents required:** {scheme['documents']}")
        st.markdown(f"**Apply mode:** {scheme['apply_mode']}")
        st.caption(
            f"State: {scheme['state']} | For: {scheme['for_whom']} | "
            f"Category: {scheme['category']} | Location: {scheme['location_type']}"
        )

        if "match_reasons" in scheme and isinstance(scheme["match_reasons"], list):
            st.markdown("**Why eligible?**")
            for reason in scheme["match_reasons"]:
                st.markdown(f"- {reason}")


def render_recommended_scheme_card(scheme):
    """Render one manual recommendation when no exact eligible schemes match."""
    with st.container(border=True):
        st.markdown(f"### **{scheme['scheme_name']}**")
        st.write(scheme["description"])
        st.markdown(f"**Documents required:** {scheme['documents']}")
        st.markdown(f"**Apply mode:** {scheme['apply_mode']}")
        st.info(scheme["recommendation_reason"])


def load_sample_eligibility_profile(force=False):
    """Fill eligibility form fields with the sample user profile."""
    st.session_state["sample_eligibility_loaded"] = True
    for key, sample_value in SAMPLE_ELIGIBILITY_WIDGET_VALUES.items():
        set_autofill_widget_value(key, sample_value, force=force)


def load_sample_eligibility_profile_from_dashboard():
    """Load sample eligibility data from the dashboard helper section."""
    load_sample_eligibility_profile()
    st.session_state["pending_sample_target"] = "eligibility"
    rerun_after_sample_load(
        "Sample eligibility data loaded. Redirecting to Scheme Eligibility...",
        "Scheme Eligibility",
    )


def render_eligibility_sample_section():
    """Render a quick sample profile helper for testing."""
    with st.expander("Try sample eligibility inputs"):
        st.write(
            "Name: Riya | State: Rajasthan | Age: 20 | Annual income: 180000 | "
            "User type: Student | Category: SC | Location: Rural"
        )
        if st.button("Load sample profile"):
            load_sample_eligibility_profile_from_dashboard()


def render_eligibility_checker_page():
    """Render eligibility form and eligible scheme cards."""
    if st.session_state.get("pending_sample_target") == "eligibility":
        load_sample_eligibility_profile(force=True)
        st.session_state["pending_sample_target"] = ""

    st.header("Scheme Eligibility")
    render_sample_loaded_feedback()

    with st.container(border=True):
        st.markdown(
            '<div class="section-eyebrow">Profile matching</div>',
            unsafe_allow_html=True,
        )
        st.write(
            "Enter basic details to discover schemes that may match your profile. "
            "The matching logic checks state, user type, age, income, category, "
            "and rural or urban location."
        )
        render_eligibility_sample_section()

    with st.container(border=True):
        with st.form("eligibility_form"):
            form_columns = st.columns(2)

            with form_columns[0]:
                name = st.text_input("Name", key="name")
                state = st.selectbox(
                    "State",
                    STATE_OPTIONS,
                    key="state",
                )
                age = st.number_input(
                    "Age",
                    min_value=0,
                    max_value=120,
                    step=1,
                    key="age",
                )
                annual_income = st.number_input(
                    "Annual family income (INR)",
                    min_value=0,
                    step=10000,
                    key="income",
                )

            with form_columns[1]:
                user_type = st.selectbox(
                    "User type",
                    ["Student", "Farmer", "Woman", "General"],
                    key="user_type",
                )
                category = st.selectbox(
                    "Category",
                    ["General", "OBC", "SC", "ST", "EWS"],
                    key="category",
                )
                location_type = st.selectbox(
                    "Location type",
                    ["Rural", "Urban"],
                    key="location_type",
                )

            submitted = st.form_submit_button(
                "Find Matching Schemes",
                type="primary",
            )

    sync_persisted_widget_values(
        ["name", "state", "age", "income", "user_type", "category", "location_type"]
    )

    if submitted:
        if not name.strip():
            st.warning("Please enter your name before checking eligibility.")
            return

        user_details = {
            "name": name,
            "state": state,
            "age": age,
            "annual_income": annual_income,
            "user_type": user_type,
            "category": category,
            "location_type": location_type,
        }

        eligible_schemes_df = find_eligible_schemes(user_details)
        st.session_state.eligible_schemes_df = eligible_schemes_df
        st.session_state.eligible_schemes_count = len(eligible_schemes_df)
        st.session_state.last_user_name = name
        st.session_state.eligibility_checked = True

        if eligible_schemes_df.empty:
            st.session_state.recommended_schemes_df = get_recommended_schemes()
        else:
            st.session_state.recommended_schemes_df = pd.DataFrame()

    if not st.session_state.eligibility_checked:
        return

    if not st.session_state.eligible_schemes_df.empty:
        st.success(
            f"Found {st.session_state.eligible_schemes_count} matching scheme(s) "
            f"for {st.session_state.last_user_name}."
        )

        for _, scheme in st.session_state.eligible_schemes_df.iterrows():
            render_scheme_card(scheme)
    else:
        st.warning(
            "No exact scheme found. Try checking official portal/e-Mitra or "
            "adjust filters."
        )

        st.subheader("Recommended to check manually")
        for _, scheme in st.session_state.recommended_schemes_df.iterrows():
            render_recommended_scheme_card(scheme)


def render_testing_inputs_section():
    """Show complete test inputs in one place for validation."""
    with st.container(border=True):
        st.subheader("Quick Demo Inputs")
        st.caption("Click a button, then the app will automatically redirect to the relevant page.")

        button_columns = st.columns(2)
        with button_columns[0]:
            if st.button(
                "Use Sample Fraud Message",
                use_container_width=True,
            ):
                load_sample_fraud_message_from_dashboard()
        with button_columns[1]:
            if st.button(
                "Use Sample Eligibility Data",
                use_container_width=True,
            ):
                load_sample_eligibility_profile_from_dashboard()

        render_sample_loaded_feedback()

        st.markdown("**Fraud Detector test case**")
        st.code(SAMPLE_FAKE_MESSAGE, language="text")

        st.markdown("**Scheme Eligibility test case**")
        st.code(
            "Name: Riya\n"
            "State: Rajasthan\n"
            "Age: 20\n"
            "Annual income: 180000\n"
            "User type: Student\n"
            "Category: SC\n"
            "Location type: Rural",
            language="text",
        )


def render_impact_dashboard_page(total_schemes):
    """Render the impact dashboard with current app metrics."""
    st.header("Impact Dashboard")

    with st.container(border=True):
        st.subheader("Safety Impact")
        st.write(
            "SchemeShield AI gives users a safer first checkpoint before they "
            "trust forwarded scheme messages or share sensitive documents."
        )
        st.info(
            "Impact: better discovery, clearer eligibility checks, and fewer "
            "fraud attempts reaching vulnerable users."
        )

    with st.container(border=True):
        st.subheader("Why this matters")
        st.write(WHY_THIS_MATTERS)

    with st.container(border=True):
        st.subheader("System Summary")
        render_summary_metrics(total_schemes)

    render_testing_inputs_section()


def main():
    """Run the Streamlit application."""
    st.set_page_config(
        page_title="SchemeShield AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_custom_css()
    initialize_session_state()
    restore_loaded_sample_values()
    preserve_widget_state_across_pages()
    ensure_selectbox_values_are_valid()
    apply_pending_navigation()
    schemes_df = load_schemes()
    total_schemes = len(schemes_df)
    selected_page = render_sidebar()

    render_hero_section()
    if selected_page == "Fraud Detector":
        render_fraud_detector_page()
    elif selected_page == "Scheme Eligibility":
        render_eligibility_checker_page()
    else:
        render_impact_dashboard_page(total_schemes)


if __name__ == "__main__":
    main()
