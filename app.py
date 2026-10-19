
import os
import json
import time
import random
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader

# -------------------- CONFIGURATION --------------------

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()

HISTORY_FILE = Path("chat_history.json")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# -------------------- PROFESSIONAL UI --------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1120, #111827 60%, #172033);
    color: #f8fafc;
}

.block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    padding-left: clamp(1rem, 4vw, 3rem);
    padding-right: clamp(1rem, 4vw, 3rem);
}

h1 {
    font-size: clamp(1.7rem, 4vw, 2.5rem) !important;
    line-height: 1.25 !important;
    font-weight: 750 !important;
    overflow-wrap: anywhere;
}

h2 { font-size: clamp(1.3rem, 3vw, 1.8rem) !important; }
h3 { font-size: clamp(1.1rem, 2.5vw, 1.4rem) !important; }

p, label, li {
    line-height: 1.65 !important;
    overflow-wrap: anywhere;
}

[data-testid="stSidebar"] {
    background: #0b1220;
    border-right: 1px solid #263247;
}

[data-testid="stChatMessage"] {
    background: rgba(30, 41, 59, 0.75);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}

.stButton button,
.stDownloadButton button,
.stFormSubmitButton button {
    min-height: 44px;
    border-radius: 11px;
    font-weight: 600;
    white-space: normal;
    transition: all 0.2s ease;
}

.stButton button:hover,
.stDownloadButton button:hover {
    border-color: #60a5fa;
}

.stTextInput input,
.stTextArea textarea {
    border-radius: 11px !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px;
    border-color: rgba(148, 163, 184, 0.22);
}

.hero {
    padding: 1.5rem;
    border: 1px solid #334155;
    border-radius: 20px;
    background: linear-gradient(135deg, #172554, #172033);
    margin-bottom: 1.3rem;
}

.hero p {
    color: #cbd5e1;
    margin-bottom: 0;
}

.small-muted {
    color: #94a3b8;
    font-size: 0.9rem;
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }

    [data-testid="stChatMessage"] {
        padding: 0.75rem;
        border-radius: 12px;
    }

    .hero {
        padding: 1rem;
    }

    .stButton button,
    .stDownloadButton button {
        width: 100%;
    }
}
</style>
""", unsafe_allow_html=True)


# -------------------- GEMINI CLIENT --------------------

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error(
        "GEMINI_API_KEY not found. Add it to your .env file "
        "and restart the app."
    )
    st.stop()

client = genai.Client(api_key=api_key)


def ask_gemini(prompt, retries=3):
    """Call Gemini with retries for temporary service errors."""
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            return response.text or "I couldn't generate a response. Try again."
        except Exception as exc:
            error_text = str(exc).lower()
            temporary = any(
                word in error_text
                for word in [
                    "503", "429", "500", "502",
                    "timeout", "temporarily unavailable",
                    "resource exhausted"
                ]
            )

            if temporary and attempt < retries - 1:
                time.sleep((2 ** attempt) + random.random())
                continue

            if "api key" in error_text or "permission" in error_text:
                return (
                    "API authentication problem. Check your Gemini API key "
                    "and API access."
                )

            return f"Gemini request failed: {exc}"

    return "Gemini is temporarily unavailable. Please try again."


# -------------------- CHAT HISTORY --------------------

def load_history():
    """Support both older list-format and dictionary-format history."""
    if not HISTORY_FILE.exists():
        return {}

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            raw = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}

    if isinstance(raw, dict):
        cleaned = {}
        for chat_id, chat in raw.items():
            if isinstance(chat, list):
                cleaned[chat_id] = {
                    "title": "Previous Chat",
                    "messages": chat,
                }
            elif isinstance(chat, dict):
                messages = chat.get("messages", [])
                if not isinstance(messages, list):
                    messages = []
                cleaned[chat_id] = {
                    "title": str(chat.get("title", "New Chat")),
                    "messages": messages,
                }
        return cleaned

    if isinstance(raw, list):
        return {
            "legacy_chat": {
                "title": "Previous Chat",
                "messages": raw,
            }
        }

    return {}


def save_history():
    try:
        with HISTORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                st.session_state.chats,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except OSError as exc:
        st.warning(f"Chat history could not be saved: {exc}")


if "chats" not in st.session_state:
    st.session_state.chats = load_history()

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False


def create_chat():
    chat_id = str(int(time.time() * 1000))
    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": [],
    }
    st.session_state.active_chat = chat_id
    save_history()


def get_active_chat():
    chat_id = st.session_state.active_chat
    if chat_id and chat_id in st.session_state.chats:
        return st.session_state.chats[chat_id]
    return None


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("# 🎓 Study AI")
    st.caption("Your personal AI learning companion")
    st.divider()

    if st.button("＋ New Chat", use_container_width=True):
        create_chat()
        st.rerun()

    mode = st.selectbox(
        "Choose assistant mode",
        ["Personal Work", "Study Help", "Coding Help"],
    )

    st.divider()
    st.markdown("### 📚 Your Chats")

    if not st.session_state.chats:
        st.caption("Your conversations will appear here.")
    else:
        for chat_id, chat in reversed(list(st.session_state.chats.items())):
            title = chat.get("title", "New Chat")
            label = f"💬 {title[:27]}"

            if st.button(
                label,
                key=f"open_{chat_id}",
                use_container_width=True,
            ):
                st.session_state.active_chat = chat_id
                st.rerun()

            if st.session_state.active_chat == chat_id:
                if st.button(
                    "🗑️ Delete this chat",
                    key=f"delete_{chat_id}",
                    use_container_width=True,
                ):
                    del st.session_state.chats[chat_id]
                    st.session_state.active_chat = None
                    save_history()
                    st.rerun()

    st.divider()
    if st.button("🧹 Clear All Chats", use_container_width=True):
        st.session_state.chats = {}
        st.session_state.active_chat = None
        save_history()
        st.rerun()

    st.caption("Keep your API key private.")


# -------------------- MAIN HEADER --------------------

st.markdown("""
<div class="hero">
    <h1>✨ AI Study Assistant</h1>
    <p>Learn smarter. Ask questions. Practice coding. Create study notes.</p>
</div>
""", unsafe_allow_html=True)

st.caption(f"Current mode: {mode}")

tab_chat, tab_pdf, tab_quiz, tab_notes = st.tabs(
    ["💬 AI Chat", "📄 PDF Reader", "🧠 Quiz", "📝 Study Notes"]
)


# -------------------- PDF EXTRACTION --------------------

with tab_pdf:
    st.subheader("📄 Chat with your PDF")
    st.write("Upload a PDF to extract its text for study questions.")

    uploaded_pdf = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        key="study_pdf",
    )

    if uploaded_pdf:
        try:
            reader = PdfReader(uploaded_pdf)
            extracted = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
            st.session_state.pdf_text = extracted

            st.success(
                f"PDF loaded: {len(reader.pages)} pages"
            )

            if extracted.strip():
                st.text_area(
                    "Extracted text preview",
                    extracted[:5000],
                    height=180,
                )
            else:
                st.warning(
                    "No selectable text found. This PDF may contain scanned "
                    "images and require OCR."
                )
        except Exception as exc:
            st.error(f"Could not read the PDF: {exc}")

    if st.session_state.pdf_text:
        st.info(
            "PDF text is available to the AI Chat, Quiz and Study Notes tabs."
        )


# -------------------- AI CHAT --------------------

with tab_chat:
    active_chat = get_active_chat()

    if active_chat is None:
        st.markdown("### 👋 Vanakkam! How can I help you?")
        st.write(
            "Ask a question, learn a topic, debug code, or study from your PDF."
        )

        col1, col2, col3 = st.columns(3)

        if col1.button("📘 Explain a topic", use_container_width=True):
            create_chat()
            st.session_state.suggested_prompt = (
                "Explain a difficult topic in simple English with examples."
            )
            st.rerun()

        if col2.button("💻 Help with coding", use_container_width=True):
            create_chat()
            st.session_state.suggested_prompt = (
                "Help me understand and debug my Python code."
            )
            st.rerun()

        if col3.button("📝 Prepare notes", use_container_width=True):
            create_chat()
            st.session_state.suggested_prompt = (
                "Help me prepare clear study notes."
            )
            st.rerun()

        if st.button("Start chatting", type="primary"):
            create_chat()
            st.rerun()

    else:
        for message in active_chat["messages"]:
            role = message.get("role", "assistant")
            content = message.get("content", "")
            with st.chat_message(
                "user" if role == "user" else "assistant"
            ):
                st.markdown(content)

    suggested = st.session_state.pop("suggested_prompt", None)
    prompt = st.chat_input("Message your AI assistant...")

    if suggested:
        prompt = suggested

    if prompt:
        if get_active_chat() is None:
            create_chat()

        active_chat = get_active_chat()
        active_chat["messages"].append(
            {"role": "user", "content": prompt}
        )

        if active_chat["title"] == "New Chat":
            active_chat["title"] = prompt[:35]

        with st.chat_message("user"):
            st.markdown(prompt)

        mode_instructions = {
            "Personal Work": (
                "Be a helpful personal assistant. Give clear, practical answers."
            ),
            "Study Help": (
                "Act as a patient tutor. Explain concepts step by step, "
                "with examples and simple language."
            ),
            "Coding Help": (
                "Act as a programming mentor. Explain code, debug carefully, "
                "and provide working examples."
            ),
        }

        context = ""
        if st.session_state.pdf_text:
            context = (
                "\nUse this uploaded PDF as reference when relevant. "
                "If the answer is not in the PDF, say so clearly.\n"
                + st.session_state.pdf_text[:20000]
            )

        conversation = active_chat["messages"][-12:]
        history_text = "\n".join(
            f"{'User' if m.get('role') == 'user' else 'Assistant'}: "
            f"{m.get('content', '')}"
            for m in conversation
        )

        full_prompt = f"""
{mode_instructions[mode]}

{context}

Conversation:
{history_text}

Respond to the latest user message. Be clear, accurate and helpful.
"""

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = ask_gemini(full_prompt)
            st.markdown(answer)

        active_chat["messages"].append(
            {"role": "assistant", "content": answer}
        )
        save_history()
        st.rerun()


# -------------------- QUIZ MODE --------------------

with tab_quiz:
    st.subheader("🧠 Practice Quiz")
    st.write("Generate multiple-choice questions from a topic or your PDF.")

    quiz_topic = st.text_input(
        "Quiz topic",
        placeholder="Example: Python loops, SQL joins, or uploaded PDF",
    )

    quiz_count = st.slider(
        "Number of questions",
        min_value=3,
        max_value=10,
        value=5,
    )

    if st.button("Generate Quiz", type="primary"):
        source = st.session_state.pdf_text[:15000] if (
            st.session_state.pdf_text and not quiz_topic.strip()
        ) else quiz_topic.strip()

        if not source:
            st.warning("Enter a topic or upload a PDF first.")
        else:
            quiz_prompt = f"""
Create exactly {quiz_count} multiple-choice quiz questions.
Topic/source:
{source}

Return ONLY valid JSON in this format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["A", "B", "C", "D"],
      "answer": 0,
      "explanation": "Short explanation"
    }}
  ]
}}
The answer must be the zero-based index of the correct option.
Do not include markdown fences.
"""
            with st.spinner("Creating your quiz..."):
                result = ask_gemini(quiz_prompt)

            try:
                cleaned = result.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                    cleaned = cleaned.rsplit("```", 1)[0]

                data = json.loads(cleaned)
                questions = data.get("questions", [])

                if not questions:
                    raise ValueError("No questions returned.")

                st.session_state.quiz_data = questions
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()
            except (json.JSONDecodeError, ValueError, AttributeError):
                st.error(
                    "Quiz format could not be read. Please try generating it again."
                )

    questions = st.session_state.quiz_data

    if questions:
        st.divider()
        st.markdown("### Your Questions")

        with st.form("quiz_form"):
            for i, question in enumerate(questions):
                st.markdown(f"**Q{i + 1}. {question.get('question', '')}**")
                options = question.get("options", [])

                if not isinstance(options, list) or not options:
                    options = ["No options provided"]

                st.radio(
                    "Choose one answer",
                    options,
                    key=f"quiz_q_{i}",
                    index=None,
                    label_visibility="collapsed",
                )

            submitted = st.form_submit_button(
                "Submit Answers",
                type="primary",
            )

        if submitted:
            st.session_state.quiz_submitted = True
            st.rerun()

        if st.session_state.quiz_submitted:
            score = 0

            for i, question in enumerate(questions):
                options = question.get("options", [])
                selected = st.session_state.get(f"quiz_q_{i}")
                correct_index = question.get("answer", -1)

                correct_option = (
                    options[correct_index]
                    if isinstance(correct_index, int)
                    and 0 <= correct_index < len(options)
                    else None
                )

                if selected == correct_option:
                    score += 1
                    st.success(f"Q{i + 1}: Correct!")
                else:
                    st.error(
                        f"Q{i + 1}: Correct answer: {correct_option}"
                    )

                explanation = question.get("explanation", "")
                if explanation:
                    st.caption(explanation)

            st.metric("Your Score", f"{score} / {len(questions)}")

            if st.button("Try another quiz"):
                st.session_state.quiz_data = None
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()


# -------------------- STUDY NOTES --------------------

with tab_notes:
    st.subheader("📝 Study Notes Generator")
    st.write("Create structured notes and download them as a text file.")

    notes_topic = st.text_input(
        "Topic for notes",
        placeholder="Example: Python functions or database normalization",
    )

    notes_language = st.selectbox(
        "Notes language",
        ["Simple English", "Thanglish"],
    )

    notes_length = st.selectbox(
        "Notes format",
        ["Quick Revision", "Detailed Notes", "Exam Preparation"],
    )

    if st.button("Generate Study Notes", type="primary"):
        source = st.session_state.pdf_text[:15000] if (
            st.session_state.pdf_text and not notes_topic.strip()
        ) else notes_topic.strip()

        if not source:
            st.warning("Enter a topic or upload a PDF first.")
        else:
            notes_prompt = f"""
Create {notes_length.lower()} for:
{source}

Language: {notes_language}
Include:
- Title and introduction
- Main concepts with headings
- Simple examples
- Important points to remember
- A short summary
Use readable formatting and avoid unsupported claims.
"""
            with st.spinner("Preparing your notes..."):
                notes = ask_gemini(notes_prompt)

            st.session_state.generated_notes = notes
            st.session_state.notes_filename = (
                "study_notes_" + str(int(time.time())) + ".txt"
            )

    if st.session_state.get("generated_notes"):
        st.markdown("### Notes Preview")
        st.markdown(st.session_state.generated_notes)

        st.download_button(
            "⬇️ Download Study Notes",
            data=st.session_state.generated_notes,
            file_name=st.session_state.get(
                "notes_filename", "study_notes.txt"
            ),
            mime="text/plain",
            use_container_width=True,
        )


# -------------------- FOOTER --------------------

st.divider()
st.markdown(
    '<p class="small-muted" style="text-align:center">'
    'AI Study Assistant · Learn • Practice • Improve</p>',
    unsafe_allow_html=True,
)
