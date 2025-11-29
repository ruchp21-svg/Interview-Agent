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

try:
    job_desc_list = storage.list_job_descriptions()
    job_selected = st.sidebar.selectbox("Select job description", options=job_desc_list)
except Exception as e:
    st.error(f"Error loading job descriptions: {e}")
    st.stop()

num_questions = st.sidebar.slider("Number of questions", 1, 10, 5)
model_provider = st.sidebar.selectbox("Model Provider", ["mock", "openai", "anthropic"], index=0)

# Load JD
job_text = storage.load_job_description(job_selected)

st.subheader("Job Description")
st.write(job_text or "No job description selected")

# Generate questions
if st.button("Generate Questions"):
    questions = question_bank.generate_questions(job_text, n=num_questions, provider=model_provider)
    session_id = str(uuid.uuid4())
    s = interviewer.InterviewSession(session_id=session_id, job=job_selected, questions=questions)
    storage.save_session(session_id, s.to_dict())
    st.session_state['session_id'] = session_id
    st.session_state['session_data'] = s.to_dict()
    st.rerun()

# Interview session
if 'session_id' in st.session_state:
    session = interviewer.InterviewSession.from_dict(st.session_state['session_data'])
    
    st.subheader("Interview Session")
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
        if st.button("Export PDF"):
            try:
                pdf_path = pdf_generator.generate_pdf(session.to_dict())
                with open(pdf_path, "rb") as fp:
                    st.download_button("Download PDF", data=fp, file_name=f"interview_{session.session_id}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
