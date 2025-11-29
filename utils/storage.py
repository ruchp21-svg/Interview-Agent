import os
import json
from typing import List

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "data")
JOB_DIR = os.path.join(DATA_DIR, "job_descriptions")
SESSION_DIR = os.path.join(DATA_DIR, "sessions")

os.makedirs(JOB_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)


def list_job_descriptions() -> List[str]:
    files = [f for f in os.listdir(JOB_DIR) if os.path.isfile(os.path.join(JOB_DIR, f))]
    return files if files else ["sample_jd.txt"]


def load_job_description(name: str) -> str:
    path = os.path.join(JOB_DIR, name)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def session_path(session_id: str) -> str:
    return os.path.join(SESSION_DIR, f"{session_id}.json")


def save_session(session_id: str, data: dict):
    with open(session_path(session_id), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_session(session_id: str) -> dict:
    p = session_path(session_id)
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def list_sessions():
    return [f for f in os.listdir(SESSION_DIR) if f.endswith('.json')]
