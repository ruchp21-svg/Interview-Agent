import json
import math
import os
import sys

# Ensure the project root is on sys.path when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import storage
from agent import question_bank

# Generates a dataset of questions spread across job descriptions

def generate_dataset(total_questions: int = 120, question_types=None, difficulties=None, provider='mock'):
    if question_types is None:
        question_types = ['technical', 'behavioral', 'design']
    if difficulties is None:
        difficulties = ['basic', 'intermediate', 'advanced']

    jds = storage.list_job_descriptions()
    if not jds:
        raise RuntimeError('No job descriptions found in data/job_descriptions')

    # evenly divide
    per_job = total_questions // len(jds)
    remainder = total_questions % len(jds)

    dataset = {}
    idx = 0
    for i, jd_name in enumerate(jds):
        ask = per_job + (1 if i < remainder else 0)
        text = storage.load_job_description(jd_name)

        # generate questions for this job in a round-robin of type+difficulty
        questions = []
        gen_index = 0
        tt = len(question_types)
        dd = len(difficulties)
        while len(questions) < ask:
            qtype = question_types[gen_index % tt]
            diff = difficulties[(gen_index // tt) % dd]
            # generate in small batches of 1 (you can increase to 2-3 for speed)
            q = question_bank.generate_questions(text, n=1, provider=provider, question_type=qtype, difficulty=diff)
            questions.extend(q)
            gen_index += 1

        # trim to ask
        dataset[jd_name] = questions[:ask]
        idx += ask

    # Save file
    out_path = 'data/question_bank/questions_{}.json'.format(total_questions)
    import os
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(dataset, fh, indent=2)

    return out_path


if __name__ == '__main__':
    path = generate_dataset(total_questions=120)
    print('Wrote dataset to', path)
