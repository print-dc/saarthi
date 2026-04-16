import html
import json
import os
import uuid
from datetime import datetime

import streamlit as st

from local_support import generate_support_response

try:
    import vertexai
    from google.oauth2 import service_account
    from vertexai import agent_engines
except Exception:  # pragma: no cover - optional dependency in free mode
    vertexai = None
    service_account = None
    agent_engines = None


APP_TITLE = "Saarthi"
APP_SUBTITLE = "Your AI mental health support companion"
APP_MODE_LOCAL = "local"
APP_MODE_VERTEX = "vertex"
WELCOME_MESSAGE = (
    "Hello, I'm Saarthi. I'm here to offer a calm, non-judgmental space "
    "for you to talk through what you're feeling. How are you doing today?"
)
FALLBACK_RESPONSE = (
    "I'm here with you. If you'd like, tell me a little more about what's "
    "been weighing on you."
)
DEFAULT_REGION = "global"
CRISIS_RESOURCES = {
    "global": [
        "If you may act on thoughts of self-harm or hurting someone else, call your local emergency number now.",
        "Reach out to a trusted person nearby and let them know you need immediate support.",
        "If calling feels hard, go to the nearest emergency room or urgent care center.",
    ],
    "us": [
        "Call or text 988 for the Suicide & Crisis Lifeline.",
        "If there is immediate danger, call 911 now.",
    ],
    "india": [
        "Call Tele-MANAS at 14416 or 1-800-891-4416 for mental health support in India.",
        "If there is immediate danger, call your local emergency services now.",
    ],
}


st.set_page_config(
    page_title="Saarthi",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    :root {
        --bg: #f6efe4;
        --card: #fffaf4;
        --ink: #1e293b;
        --muted: #5b6470;
        --accent: #d9714f;
        --accent-deep: #8c3b2a;
        --soft: #f4d8be;
        --danger: #9f1239;
        --success: #166534;
        --border: #e7d7c4;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(217, 113, 79, 0.18), transparent 30%),
            radial-gradient(circle at top right, rgba(140, 59, 42, 0.12), transparent 28%),
            linear-gradient(180deg, #fbf6ef 0%, var(--bg) 100%);
        color: var(--ink);
    }

    .hero {
        background: linear-gradient(135deg, rgba(255, 250, 244, 0.96), rgba(244, 216, 190, 0.92));
        border: 1px solid rgba(231, 215, 196, 0.9);
        border-radius: 28px;
        padding: 2.2rem;
        box-shadow: 0 24px 60px rgba(103, 63, 36, 0.10);
        margin-bottom: 1.25rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 3rem;
        color: var(--accent-deep);
    }

    .hero p {
        margin: 0.75rem 0 0;
        max-width: 54rem;
        color: var(--muted);
        font-size: 1.05rem;
        line-height: 1.6;
    }

    .notice {
        background: rgba(255, 250, 244, 0.92);
        border-left: 5px solid var(--danger);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 24px rgba(103, 63, 36, 0.08);
    }

    .notice strong {
        color: var(--danger);
    }

    .status-card {
        background: rgba(255, 250, 244, 0.92);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }

    .transcript-card {
        background: rgba(255, 250, 244, 0.84);
        border: 1px solid rgba(231, 215, 196, 0.82);
        border-radius: 20px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 10px 26px rgba(103, 63, 36, 0.05);
    }

    .transcript-role {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--accent-deep);
        margin-bottom: 0.45rem;
    }

    .transcript-meta {
        margin-top: 0.65rem;
        color: var(--muted);
        font-size: 0.85rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def read_setting(name: str, default: str | None = None) -> str | None:
    """Read config from Streamlit secrets first, then environment variables."""
    value = None
    if hasattr(st, "secrets") and name in st.secrets:
        value = st.secrets[name]
    elif name in os.environ:
        value = os.environ[name]
    return value if value not in ("", None) else default


def load_runtime_config() -> dict[str, str | None]:
    return {
        "project_id": read_setting("PROJECT_ID"),
        "location": read_setting("LOCATION"),
        "staging_bucket": read_setting("STAGING_BUCKET"),
        "resource_id": read_setting("RESOURCE_ID"),
        "service_account_key": read_setting("GOOGLE_SERVICE_ACCOUNT_KEY"),
        "default_region": read_setting("DEFAULT_REGION", DEFAULT_REGION),
        "app_mode": read_setting("SAARTHI_MODE", APP_MODE_LOCAL),
    }


def missing_required_config(config: dict[str, str | None]) -> list[str]:
    required = {
        "PROJECT_ID": config["project_id"],
        "LOCATION": config["location"],
        "STAGING_BUCKET": config["staging_bucket"],
        "RESOURCE_ID": config["resource_id"],
    }
    return [name for name, value in required.items() if not value]


def resolve_app_mode(config: dict[str, str | None]) -> str:
    requested_mode = (config.get("app_mode") or APP_MODE_LOCAL).strip().lower()
    if requested_mode == APP_MODE_VERTEX:
        return APP_MODE_VERTEX
    return APP_MODE_LOCAL


@st.cache_resource(show_spinner=False)
def initialize_agent(config: dict[str, str | None]):
    """Initialize the Vertex AI Agent Engine client."""
    if resolve_app_mode(config) != APP_MODE_VERTEX:
        return None, True, "Running in free local support mode."

    if vertexai is None or service_account is None or agent_engines is None:
        return None, False, "Vertex AI libraries are not installed in this environment."

    missing = missing_required_config(config)
    if missing:
        missing_text = ", ".join(missing)
        return None, False, f"Missing required configuration: {missing_text}"

    try:
        service_account_key = config.get("service_account_key")
        if service_account_key:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(service_account_key)
            )
            vertexai.init(
                project=config["project_id"],
                location=config["location"],
                staging_bucket=config["staging_bucket"],
                credentials=credentials,
            )
        else:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
            os.environ["GOOGLE_CLOUD_PROJECT"] = config["project_id"] or ""
            os.environ["GOOGLE_CLOUD_LOCATION"] = config["location"] or ""
            os.environ["GOOGLE_CLOUD_STAGING_BUCKET"] = config["staging_bucket"] or ""
            vertexai.init(
                project=config["project_id"],
                location=config["location"],
                staging_bucket=config["staging_bucket"],
            )

        remote_app = agent_engines.get(config["resource_id"])
        return remote_app, True, "Connected to Vertex AI Agent Engine."
    except Exception as exc:
        return None, False, f"Unable to connect to the deployed agent: {exc}"


def create_session(remote_app, user_id: str):
    try:
        session = remote_app.create_session(user_id=user_id)
        return session["id"], True, None
    except Exception as exc:
        return None, False, str(exc)


def get_agent_response(remote_app, user_id: str, session_id: str, message: str, debug: bool = False) -> str:
    try:
        response_text = ""
        for event in remote_app.stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        ):
            if debug:
                st.write("DEBUG Event:", event.get("author", "unknown"))
            if event.get("author") == "output_agent":
                for part in event.get("content", {}).get("parts", []):
                    text = part.get("text")
                    if text:
                        response_text = text.strip()
                        break
        return response_text or FALLBACK_RESPONSE
    except Exception as exc:
        return (
            "I'm having trouble reaching the support system right now. "
            f"Please try again in a moment. Technical detail: {exc}"
        )


def crisis_region_key(region: str | None) -> str:
    if not region:
        return DEFAULT_REGION
    normalized = region.strip().lower()
    if normalized in CRISIS_RESOURCES:
        return normalized
    return DEFAULT_REGION


def session_defaults():
    defaults = {
        "messages": [],
        "session_id": None,
        "user_id": str(uuid.uuid4()),
        "agent_connected": False,
        "remote_app": None,
        "debug_mode": False,
        "composer_value": "",
        "connection_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_new_session(add_welcome: bool) -> bool:
    config = load_runtime_config()
    mode = resolve_app_mode(config)

    if mode == APP_MODE_LOCAL:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        if add_welcome:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": WELCOME_MESSAGE,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
            )
        st.session_state.connection_message = "New local session ready."
        return True

    if not st.session_state.remote_app:
        st.session_state.connection_message = "Connect to the app before starting a new session."
        return False

    session_id, success, error = create_session(
        st.session_state.remote_app,
        st.session_state.user_id,
    )
    if not success:
        st.session_state.connection_message = f"Unable to create a session: {error}"
        return False

    st.session_state.session_id = session_id
    st.session_state.messages = []
    if add_welcome:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        )
    st.session_state.connection_message = "New session ready."
    return True


def connect_if_needed(config: dict[str, str | None]) -> None:
    if resolve_app_mode(config) == APP_MODE_LOCAL:
        st.session_state.agent_connected = True
        st.session_state.remote_app = None
        st.session_state.connection_message = "Running in free local support mode."
        if not st.session_state.session_id:
            start_new_session(add_welcome=True)
        return

    if st.session_state.agent_connected and st.session_state.remote_app is not None:
        return

    remote_app, success, message = initialize_agent(config)
    st.session_state.connection_message = message
    if not success:
        st.session_state.remote_app = None
        st.session_state.agent_connected = False
        return

    st.session_state.remote_app = remote_app
    st.session_state.agent_connected = True
    if not st.session_state.session_id:
        start_new_session(add_welcome=True)


def render_header():
    st.markdown(
        f"""
    <section class="hero">
        <h1>{APP_TITLE}</h1>
        <p>{APP_SUBTITLE}. This assistant offers emotional support and general wellness guidance, but it is not a substitute for a licensed clinician or emergency service.</p>
    </section>
    """,
        unsafe_allow_html=True,
    )


def render_notices(region: str):
    st.markdown(
        """
        <div class="notice">
            <strong>Immediate safety note:</strong> If you are in immediate danger or may act on thoughts of self-harm, contact local emergency services right now and reach out to a trusted person near you.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("See crisis support resources", expanded=False):
        for item in CRISIS_RESOURCES[DEFAULT_REGION]:
            st.markdown(f"- {item}")
        if region != DEFAULT_REGION:
            st.markdown("")
            st.markdown(f"Region-specific support for `{region}`:")
            for item in CRISIS_RESOURCES[region]:
                st.markdown(f"- {item}")


def render_sidebar(config: dict[str, str | None], region: str):
    with st.sidebar:
        st.subheader("App Status")
        status_text = "Connected" if st.session_state.agent_connected else "Disconnected"
        status_color = "var(--success)" if st.session_state.agent_connected else "var(--danger)"
        mode = resolve_app_mode(config)
        mode_label = "Free local mode" if mode == APP_MODE_LOCAL else "Vertex AI mode"
        st.markdown(
            f"""
            <div class="status-card">
                <div><strong>Status:</strong> <span style="color:{status_color};">{status_text}</span></div>
                <div><strong>Mode:</strong> {mode_label}</div>
                <div><strong>Region:</strong> {html.escape(region)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.connection_message:
            st.info(st.session_state.connection_message)

        st.session_state.debug_mode = st.checkbox(
            "Debug mode",
            value=st.session_state.debug_mode,
        )

        if st.button("Reconnect", use_container_width=True):
            initialize_agent.clear()
            st.session_state.agent_connected = False
            st.session_state.remote_app = None
            connect_if_needed(config)
            st.rerun()

        if st.button("Start fresh session", use_container_width=True):
            if start_new_session(add_welcome=True):
                st.rerun()

        if st.button("Clear transcript", use_container_width=True):
            st.session_state.messages = []
            st.session_state.composer_value = ""
            st.session_state.connection_message = "Transcript cleared for this browser session."
            st.rerun()

        if st.session_state.messages:
            transcript = json.dumps(st.session_state.messages, indent=2)
            st.download_button(
                label="Download transcript",
                data=transcript,
                file_name="saarthi-transcript.json",
                mime="application/json",
                use_container_width=True,
            )

        if mode == APP_MODE_VERTEX:
            st.divider()
            st.caption("Configuration")
            st.code(
                "\n".join(
                    [
                        f"PROJECT_ID={config['project_id'] or 'missing'}",
                        f"LOCATION={config['location'] or 'missing'}",
                        f"RESOURCE_ID={'set' if config['resource_id'] else 'missing'}",
                        f"STAGING_BUCKET={'set' if config['staging_bucket'] else 'missing'}",
                    ]
                )
            )
        else:
            st.divider()
            st.caption("Free deployment")
            st.write(
                "This mode uses Saarthi's built-in local support engine, so no Google Cloud setup is required."
            )


def render_transcript():
    if not st.session_state.messages:
        st.info("Your conversation will appear here once the session starts.")
        return

    for message in st.session_state.messages:
        role_label = "You" if message["role"] == "user" else "Saarthi"
        safe_content = html.escape(message["content"]).replace("\n", "<br>")
        safe_time = html.escape(message["timestamp"])
        st.markdown(
            f"""
            <article class="transcript-card">
                <div class="transcript-role">{role_label}</div>
                <div>{safe_content}</div>
                <div class="transcript-meta">{safe_time}</div>
            </article>
            """,
            unsafe_allow_html=True,
        )


def handle_message_send():
    user_message = st.session_state.composer_value.strip()
    if not user_message:
        st.warning("Write a message before sending.")
        return

    mode = resolve_app_mode(load_runtime_config())

    if not st.session_state.agent_connected:
        if mode == APP_MODE_VERTEX:
            st.error("The app is not connected to the deployed agent yet.")
        else:
            st.error("The local support engine is not ready yet.")
        return

    if not st.session_state.session_id and not start_new_session(add_welcome=False):
        st.error("A session could not be created.")
        return

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
    )

    with st.spinner("Saarthi is responding..."):
        if mode == APP_MODE_VERTEX:
            response = get_agent_response(
                st.session_state.remote_app,
                st.session_state.user_id,
                st.session_state.session_id,
                user_message,
                debug=st.session_state.debug_mode,
            )
        else:
            response = generate_support_response(user_message)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
    )
    st.session_state.composer_value = ""
    st.rerun()


def main():
    session_defaults()
    config = load_runtime_config()
    region = crisis_region_key(config.get("default_region"))

    render_header()
    render_notices(region)
    connect_if_needed(config)
    render_sidebar(config, region)
    render_transcript()

    st.markdown("### Share what is on your mind")
    st.text_area(
        label="Your message",
        placeholder="Write here. Saarthi will respond with empathy, clarity, and practical support when helpful.",
        height=140,
        key="composer_value",
        label_visibility="collapsed",
    )
    st.button(
        "Send message",
        type="primary",
        use_container_width=True,
        on_click=handle_message_send,
    )

    if st.session_state.debug_mode:
        st.divider()
        st.subheader("Debug")
        st.json(
            {
                "connected": st.session_state.agent_connected,
                "mode": resolve_app_mode(config),
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "message_count": len(st.session_state.messages),
                "missing_config": missing_required_config(config),
                "has_service_account_key": bool(config.get("service_account_key")),
            }
        )


if __name__ == "__main__":
    main()
