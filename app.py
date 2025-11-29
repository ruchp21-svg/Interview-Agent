import streamlit as st
import uuid
import os
import json
from agent import interviewer, question_bank, evaluator
from utils import storage, pdf_generator
from config import prompts, settings

st.set_page_config(page_title="AI Interview Agent", layout="wide")


def _safe_rerun():
    """Call a Streamlit rerun in a way that works across versions.
    Newer/older Streamlit exposes either `st.rerun` or `st.experimental_rerun`.
    If neither exists fall back to toggling a session_state flag which forces UI updates.
    """
    if hasattr(st, "rerun"):
        try:
            st.rerun()
            return
        except Exception:
            pass

    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
            return
        except Exception:
            pass

    # last resort: flip a session_state value to trigger a rerun on next run
    st.session_state['_rerun_requested'] = not st.session_state.get('_rerun_requested', False)

# Header
st.markdown("# AI Interview Agent: Production-Ready Architecture")
st.markdown("Built for Rooman Technologies")
st.write("---")

# Sidebar: Job description selection and settings
st.sidebar.header("Interview Setup")
job_desc_list = storage.list_job_descriptions()
job_selected = st.sidebar.selectbox("Select job description", options=job_desc_list)

# Interviewer details (so the interviewer can add their info to the session/report)
st.sidebar.markdown("---")
st.sidebar.header("Interviewer (you)")
interviewer_name = st.sidebar.text_input("Name", key='interviewer_name')
interviewer_title = st.sidebar.text_input("Title", key='interviewer_title')
interviewer_bio = st.sidebar.text_area("Short bio / contact", key='interviewer_bio')
st.sidebar.markdown("---")

num_questions = st.sidebar.slider("Number of questions", min_value=1, max_value=10, value=settings.MAX_QUESTIONS_DEFAULT)
model_provider = st.sidebar.selectbox("Model Provider", ["mock", "openai", "anthropic"], index=0)
question_type = st.sidebar.selectbox("Question type", ["general", "technical", "behavioral", "design"], index=1)
difficulty = st.sidebar.selectbox("Difficulty", ["basic", "intermediate", "advanced"], index=0)
compare_providers = st.sidebar.checkbox("Compare providers (mock / openai / anthropic)", value=False)
vector_db = st.sidebar.selectbox("Vector DB (RAG)", ["none", "chroma", "pinecone"], index=1)
storage_backend = st.sidebar.selectbox("Storage Backend", ["local_json", "gsheet", "supabase"], index=0)

# Load JD
job_text = storage.load_job_description(job_selected)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Job Description")
    st.write(job_text or "No job description selected")

    # Generate questions (minimal UI, one-click)
    if st.button("Generate Questions"):
        if model_provider == 'openai' and not (settings.OPENAI_API_KEY or os.environ.get('OPENAI_API_KEY')):
            st.warning("OpenAI provider selected but OPENAI_API_KEY not found in environment. Questions will fallback to mock generation. Set OPENAI_API_KEY to use real OpenAI generation.")

        if compare_providers:
            providers = ["mock", "openai", "anthropic"]
            all_sets = {}
            for p in providers:
                    all_sets[p] = question_bank.generate_questions(job_text, n=num_questions, provider=p, question_type=question_type, difficulty=difficulty)

            # store a session using the selected provider's set so the rest of the app can continue
            session_id = str(uuid.uuid4())
            s = interviewer.InterviewSession(session_id=session_id, job=job_selected, questions=all_sets[model_provider], interviewer={'name': interviewer_name, 'title': interviewer_title, 'bio': interviewer_bio})
            storage.save_session(session_id, s.to_dict())
            # keep the session state in-memory so UI updates instantly
            st.session_state['session_id'] = session_id
            st.session_state['session_data'] = s.to_dict()

            # show comparison results inline
            st.markdown("### Provider comparison")
            cols = st.columns(len(providers))
            for i, p in enumerate(providers):
                with cols[i]:
                    st.markdown(f"**{p.upper()}**")
                    for idx, q in enumerate(all_sets[p], start=1):
                        st.markdown(f"{idx}. {q['text']}")
        else:
            questions = question_bank.generate_questions(job_text, n=num_questions, provider=model_provider, question_type=question_type, difficulty=difficulty)
            session_id = str(uuid.uuid4())
            s = interviewer.InterviewSession(session_id=session_id, job=job_selected, questions=questions, interviewer={'name': interviewer_name, 'title': interviewer_title, 'bio': interviewer_bio})
            storage.save_session(session_id, s.to_dict())
            # initialize in-memory session data to keep the UI stateful
            st.session_state['session_id'] = session_id
            st.session_state['session_data'] = s.to_dict()
        _safe_rerun()

    # Start or resume session
    if 'session_id' in st.session_state:
        session_id = st.session_state['session_id']
        # prefer session_data in session_state to keep UI in-sync after submissions
        if 'session_data' in st.session_state:
            sdata = st.session_state['session_data']
        else:
            # load from persistence only if not in-memory
            sdata = storage.load_session(session_id)
            st.session_state['session_data'] = sdata
        session = interviewer.InterviewSession.from_dict(sdata)

        st.subheader("Interview Session")
        st.markdown(f"**Candidate ID:** {session.candidate_id}")
        st.markdown(f"**Job:** {session.job}")
        # show interviewer metadata if present
        if getattr(session, 'interviewer', None):
            iv = session.interviewer
            name = iv.get('name') or ''
            title = iv.get('title') or ''
            bio = iv.get('bio') or ''
            if name or title:
                st.markdown(f"**Interviewer:** {name} {f'— {title}' if title else ''}")
            if bio:
                st.caption(bio)

        next_q = session.get_next_question()
        if next_q:
            st.markdown(f"**Question {session.current_index + 1}/{len(session.questions)}**: {next_q['text']}")
            # Use a unique key for the text area so it's tied to the specific question index
            answer_key = f"answer_{session_id}_{session.current_index}"
            answer = st.text_area("Candidate Response", key=answer_key)
            # Use unique key for submit button to avoid accidental multiple triggers
            if st.button("Submit Answer", key=f"submit_{session_id}_{session.current_index}"):
                # Evaluate
                eval_result = evaluator.evaluate_response(next_q, answer, provider=model_provider)
                session.add_response(next_q, answer, eval_result)
                # update both in-memory and on-disk storage
                st.session_state['session_data'] = session.to_dict()
                storage.save_session(session.session_id, st.session_state['session_data'])
                # clear the text area for this question so the UI shows an empty box for the next question
                try:
                    st.session_state[answer_key] = ""
                except Exception:
                    # ignore if key doesn't exist
                    pass
                st.success("Response submitted and evaluated.")
                _safe_rerun()
        else:
            st.success("Interview complete. You can view the scorecard or export results.")
            if st.button("Generate Scorecard"):
                report = session.generate_scorecard()
                st.json(report)
            if st.button("Export PDF"):
                pdf_path = pdf_generator.generate_pdf(session.to_dict())
                with open(pdf_path, "rb") as fp:
                    btn = st.download_button(
                        label="Download PDF Report",
                        data=fp,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf"
                    )
            if st.button("Export JSON"):
                json_path = os.path.join('data', 'reports', f"{session.session_id}.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(session.to_dict(), f, indent=2)
                with open(json_path, 'rb') as fp:
                    st.download_button('Download JSON', data=fp, file_name=os.path.basename(json_path), mime='application/json')

with col2:
    # Minimal right column for quick controls and help
    st.subheader("Quick Actions")
    st.markdown("Select a job, choose provider & question type, then click **Generate Questions**.")
    st.write("\n")
    st.markdown("**Export:**")
    if 'session_id' in st.session_state:
        sid = st.session_state['session_id']
        st.write(f"Session: {sid}")
        if st.button("Download latest report (PDF)"):
            try:
                pdf_path = pdf_generator.generate_pdf(st.session_state['session_data'])
                with open(pdf_path, 'rb') as fp:
                    st.download_button('Download PDF', data=fp, file_name=os.path.basename(pdf_path), mime='application/pdf')
            except Exception as e:
                st.error('Failed to create PDF: ' + str(e))

    st.write('---')

# Show active session if any
if 'session_id' not in st.session_state:
    st.info("Generate questions to create a new interview session.")
