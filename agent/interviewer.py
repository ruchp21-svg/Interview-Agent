import uuid
import time
from typing import List, Dict, Any

class InterviewSession:
    def __init__(self, session_id: str, job: str, questions: List[Dict[str, Any]], candidate_id: str = None, interviewer: Dict[str, Any] = None):
        self.session_id = session_id
        self.job = job
        self.questions = questions
        self.candidate_id = candidate_id or str(uuid.uuid4())
        self.responses = []  # list of {question, answer, evaluation}
        self.current_index = 0
        self.started_at = time.time()
        # interviewer info: {name, title, bio, contact}
        self.interviewer = interviewer or {}

    def get_next_question(self):
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def add_response(self, question: Dict[str, Any], answer: str, evaluation: Dict[str, Any]):
        self.responses.append({
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
            "answered_at": time.time(),
        })
        self.current_index += 1

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "job": self.job,
            "candidate_id": self.candidate_id,
            "questions": self.questions,
            "responses": self.responses,
            "current_index": self.current_index,
            "started_at": self.started_at,
            "interviewer": self.interviewer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        inst = cls(session_id=data["session_id"], job=data.get("job"), questions=data.get("questions", []), candidate_id=data.get("candidate_id"), interviewer=data.get("interviewer"))
        inst.responses = data.get("responses", [])
        inst.current_index = data.get("current_index", 0)
        inst.started_at = data.get("started_at", time.time())
        inst.interviewer = data.get("interviewer", {})
        return inst

    def generate_scorecard(self):
        # Simple aggregation of evaluations
        if not self.responses:
            return {"message": "No responses yet"}

        aggregate = {"technical": 0, "communication": 0, "culture": 0}
        counts = {"technical": 0, "communication": 0, "culture": 0}

        for r in self.responses:
            ev = r.get("evaluation", {})
            for k in aggregate.keys():
                if k in ev and isinstance(ev[k], (int, float)):
                    aggregate[k] += ev[k]
                    counts[k] += 1

        scorecard = {}
        for k, total in aggregate.items():
            scorecard[k] = total / counts[k] if counts[k] else None

        scorecard["final_recommendation"] = "Proceed" if (scorecard.get("technical", 0) or 0) >= 3 else "Reject"
        scorecard["detail"] = self.responses
        return scorecard
