import sys
import os
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

from agent import question_bank


def test_provider_variations():
    jd = "Senior backend engineer with Python, distributed systems, caching and SQL"
    q_mock = question_bank.generate_questions(jd, n=2, provider='mock')
    q_openai = question_bank.generate_questions(jd, n=2, provider='openai')
    q_anth = question_bank.generate_questions(jd, n=2, provider='anthropic')

    assert len(q_mock) == 2
    assert len(q_openai) == 2
    assert len(q_anth) == 2

    # Ensure the questions differ between providers (mock templates are different)
    texts = (q_mock[0]['text'], q_openai[0]['text'], q_anth[0]['text'])
    assert len(set(texts)) == 3, f"Expected different first-question texts but got: {texts}"


def test_role_specific_questions():
    ml_jd = "Machine Learning Engineer\nWe build models and pipelines."
    fe_jd = "Frontend Engineer\nWe build UIs in React and optimize client performance."
    ds_jd = "Data Scientist\nAnalyze data, design experiments and validate hypotheses."

    q_ml = question_bank.generate_questions(ml_jd, n=2, provider='mock')
    q_fe = question_bank.generate_questions(fe_jd, n=2, provider='mock')
    q_ds = question_bank.generate_questions(ds_jd, n=2, provider='mock')

    assert len(q_ml) == 2
    assert len(q_fe) == 2
    assert len(q_ds) == 2

    # check that generated texts reflect role specialization
    ml_text = q_ml[0]['text'].lower()
    fe_text = q_fe[0]['text'].lower()
    ds_text = q_ds[0]['text'].lower()

    assert any(word in ml_text for word in ("model", "feature", "pipeline", "drift")), "ML question does not mention model/pipeline"
    assert any(word in fe_text for word in ("react", "ui", "frontend", "component", "performance")), "Frontend question missing UI/React clues"
    assert any(word in ds_text for word in ("statistical", "experiment", "feature", "hypothesis", "data")), "Data Scientist question missing statistical/experiment clues"

    # ensure the texts differ across roles
    assert ml_text != fe_text != ds_text


def test_basic_difficulty_generates_simple_questions():
    jd = "Machine Learning Engineer\nWe build models and pipelines."
    q_basic = question_bank.generate_questions(jd, n=2, provider='mock', question_type='technical', difficulty='basic')
    assert len(q_basic) == 2
    text = q_basic[0]['text'].lower()
    # basic templates include simpler phrasing like 'what is', 'simple', or 'describe in simple'
    assert (any(k in text for k in ("what is", "simple", "describe in simple", "brief", "quick", "steps", "in simple terms", "explain simply")) or len(text.split()) <= 14), f"Expected a simple/basic phrasing but got: {text}"


def test_question_type_variations():
    jd = "Machine Learning Engineer\nBuild models and pipelines for inference."
    tech = question_bank.generate_questions(jd, n=2, provider='mock', question_type='technical')
    beh = question_bank.generate_questions(jd, n=2, provider='mock', question_type='behavioral')
    des = question_bank.generate_questions(jd, n=2, provider='mock', question_type='design')

    assert len(tech) == 2 and len(beh) == 2 and len(des) == 2

    t0, b0, d0 = tech[0]['text'].lower(), beh[0]['text'].lower(), des[0]['text'].lower()
    # rough checks for keywords to ensure types differ
    assert any(k in t0 for k in ("model", "pipeline", "feature", "accuracy", "latency"))
    assert any(k in b0 for k in ("team", "stakeholder", "scenario", "behavior", "communication")) or len(b0.split()) > 3
    assert any(k in d0 for k in ("design", "api", "architecture", "scale", "tradeoff", "monitor", "alert", "plan"))
