import streamlit as st
import uuid
import os
import json

# Import with error handling
try:
    from agent import interviewer, question_bank, evaluator
    from utils import storage, pdf_generator
    from config import settings
except Exception as e:
    st.error(f"Import error: {e}")
    st.stop()

st.set_page_config(page_title="AI Interview Agent", layout="wide")

# Header
st.markdown("# AI Interview Agent")
st.write("---")

# Sidebar
st.sidebar.header("Interview Setup")

# Session management
if st.sidebar.button("New Session"):
    for key in list(st.session_state.keys()):
        if key.startswith(('session_', 'answer_')):
            del st.session_state[key]
    st.rerun()

# Load existing sessions
sessions = storage.list_sessions()
if sessions:
    selected_session = st.sidebar.selectbox("Load Session", ["New"] + sessions)
    if selected_session != "New" and st.sidebar.button("Load"):
        session_id = selected_session.replace('.json', '')
        session_data = storage.load_session(session_id)
        st.session_state['session_id'] = session_id
        st.session_state['session_data'] = session_data
        st.rerun()

try:
    job_desc_list = storage.list_job_descriptions()
    job_selected = st.sidebar.selectbox("Select job description", options=job_desc_list)
except Exception as e:
    st.error(f"Error loading job descriptions: {e}")
    st.stop()

num_questions = st.sidebar.slider("Number of questions", 1, 10, 5)
model_provider = st.sidebar.selectbox("Model Provider", ["mock", "openai", "anthropic"], index=0)
question_type = st.sidebar.selectbox("Question Type", ["general", "technical", "behavioral", "design"], index=0)
difficulty = st.sidebar.selectbox("Difficulty", ["basic", "medium", "hard"], index=1)

# Interviewer Profile
st.sidebar.subheader("Interviewer Profile")
interviewer_name = st.sidebar.text_input("Name", value="")
interviewer_title = st.sidebar.text_input("Title", value="")
interviewer_bio = st.sidebar.text_area("Bio", value="", height=100)

# Load JD
job_text = storage.load_job_description(job_selected)

st.subheader("Job Description")
st.write(job_text or "No job description selected")

# Generate questions
if st.button("Generate Questions"):
    questions = question_bank.generate_questions(job_text, n=num_questions, provider=model_provider, question_type=question_type, difficulty=difficulty)
    session_id = str(uuid.uuid4())
    
    # Create interviewer profile
    interviewer_profile = {
        "name": interviewer_name,
        "title": interviewer_title,
        "bio": interviewer_bio
    }
    
    s = interviewer.InterviewSession(session_id=session_id, job=job_selected, questions=questions, interviewer=interviewer_profile)
    storage.save_session(session_id, s.to_dict())
    st.session_state['session_id'] = session_id
    st.session_state['session_data'] = s.to_dict()
    st.rerun()

# Interview session
if 'session_id' in st.session_state:
    session = interviewer.InterviewSession.from_dict(st.session_state['session_data'])
    
    st.subheader("Interview Session")
    
    # Display interviewer info
    interviewer_info = session.interviewer
    if interviewer_info and interviewer_info.get('name'):
        st.markdown(f"**Interviewer:** {interviewer_info.get('name')}")
        if interviewer_info.get('title'):
            st.markdown(f"**Title:** {interviewer_info.get('title')}")
        if interviewer_info.get('bio'):
            st.markdown(f"**Bio:** {interviewer_info.get('bio')}")
        st.write("---")
    
    st.markdown(f"**Candidate ID:** {session.candidate_id}")
    
    next_q = session.get_next_question()
    if next_q:
        st.markdown(f"**Question {session.current_index + 1}/{len(session.questions)}**: {next_q['text']}")
        answer = st.text_area("Candidate Response", key=f"answer_{session.current_index}")
        
        if st.button("Submit Answer"):
            eval_result = evaluator.evaluate_response(next_q, answer, provider=model_provider)
            session.add_response(next_q, answer, eval_result)
            st.session_state['session_data'] = session.to_dict()
            storage.save_session(session.session_id, st.session_state['session_data'])
            st.success("Response submitted")
            st.rerun()
    else:
        st.success("Interview complete!")
        
        # Show scorecard
        scorecard = session.generate_scorecard()
        st.subheader("Interview Scorecard")
        
        # Display interviewer signature
        interviewer_info = session.interviewer
        if interviewer_info and interviewer_info.get('name'):
            st.markdown(f"**Conducted by:** {interviewer_info.get('name')}")
            if interviewer_info.get('title'):
                st.markdown(f"**Title:** {interviewer_info.get('title')}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Technical", f"{scorecard.get('technical', 0):.1f}/5")
        with col2:
            st.metric("Communication", f"{scorecard.get('communication', 0):.1f}/5")
        with col3:
            st.metric("Culture Fit", f"{scorecard.get('culture', 0):.1f}/5")
        
        st.write(f"**Recommendation:** {scorecard.get('final_recommendation', 'N/A')}")
        
        if st.button("Export PDF"):
            try:
                pdf_path = pdf_generator.generate_pdf(session.to_dict())
                with open(pdf_path, "rb") as fp:
                    st.download_button("Download PDF", data=fp, file_name=f"interview_{session.session_id}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
