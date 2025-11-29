import os
import sys
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

from agent import interviewer, question_bank, evaluator
from utils import storage


def test_generate_questions_and_session():
    jd = storage.load_job_description('sample_jd.txt')
    qs = question_bank.generate_questions(jd, n=3, provider='mock')
    assert len(qs) == 3

    s = interviewer.InterviewSession(session_id='t1', job='test', questions=qs, interviewer={'name':'Alice','title':'Lead Interviewer','bio':'Has 10 years experience.'})
    q = s.get_next_question()
    assert q is not None

    ev = evaluator.evaluate_response(q, 'sample answer', provider='mock')
    assert 'technical' in ev


def test_interviewer_serialization_and_pdf(tmp_path):
    # ensure interviewer metadata is preserved and PDF generator accepts session data
    jd = storage.load_job_description('sample_jd.txt')
    qs = question_bank.generate_questions(jd, n=1, provider='mock')
    s = interviewer.InterviewSession(session_id='tt2', job='serialize-test', questions=qs, interviewer={'name':'Bob','title':'Sr Eng','bio':'Bio text'})
    d = s.to_dict()
    assert 'interviewer' in d and d['interviewer']['name'] == 'Bob'

    # generate pdf using utils.pdf_generator
    from utils import pdf_generator
    p = pdf_generator.generate_pdf(d)
    assert p and os.path.exists(p)
    assert os.path.getsize(p) > 0
