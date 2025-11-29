from typing import List, Dict
import random
import os
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

from config import prompts, settings

# This module contains a simple question generator with placeholders for a LangChain or LLM-based implementation.

TEMPLATE_QUESTIONS = [
    "Explain the most challenging bug you solved and the steps you took.",
    "Design a scalable system for {domain} that handles 1M users. Describe components and tradeoffs.",
    "Write the SQL and explain how you'd optimize this query for large scale.",
    "How would you approach testing a distributed caching layer?",
    "Explain the difference between optimistic and pessimistic concurrency control.",
    "How do you prioritize features when time is limited?",
]

# provider-specific mock templates (used when LLM provider unavailable or for mock provider)
PROVIDER_TEMPLATES = {
    "mock": TEMPLATE_QUESTIONS,
    "openai": [
        "Given this job, write a technical problem solving question focusing on algorithms or system design for {domain}.",
        "Ask the candidate to optimize this SQL pattern for scale in {domain} and discuss tradeoffs.",
        "Give a live-coding style prompt for implementing a short function that manipulates data structures used in {domain}.",
        "Design API endpoints for a service in {domain} that need to handle high throughput. Explain scalability choices.",
    ],
    "anthropic": [
        "Describe a behavioral scenario and ask how they'd resolve a team conflict while building {domain} features.",
        "Ask for a thoughtful explanation of system tradeoffs and request specific metrics they'd monitor for {domain}.",
        "Pose a product-scenario question: how would you prioritize features and handle stakeholder tradeoffs for {domain}?",
        "Give a situational question that explores cross-team collaboration, incident response, and post-incident analysis for {domain}.",
    ],
}

# Role specific templates to ensure different roles receive distinct question sets
ROLE_TEMPLATES = {
    "ml_engineer": [
        "Explain the model architecture you would choose for {domain} and why. Discuss tradeoffs for latency vs accuracy.",
        "Walk me through how you'd build a feature pipeline for {domain} and how you'd ensure data quality.",
        "Describe how you'd evaluate model performance in production and detect model drift for {domain}.",
    ],
    "ml_engineer_technical": [
        "Explain the model architecture you would choose for {domain} and why. Discuss tradeoffs for latency vs accuracy.",
        "Walk me through training, validation and deployment steps you would use for a production ML pipeline in {domain}.",
        "How would you optimize inference performance (latency and throughput) for models serving {domain} traffic?",
    ],
    "ml_engineer_technical_basic": [
        "What is a machine learning model? Give a simple example for {domain}.",
        "Describe in simple terms how you would build a training pipeline for {domain}.",
        "What steps would you take to evaluate a model quickly for {domain}?",
    ],
    "ml_engineer_behavioral_basic": [
        "Tell me in simple words how you work with engineers and product to ship an ML feature in {domain}.",
        "Describe a small example where model results changed product decisions and what you did next.",
        "How do you explain model limitations to non-technical stakeholders?",
    ],
    "ml_engineer_design_basic": [
        "Sketch a simple design for serving a model for {domain} users with high-level components.",
        "What monitoring would you set up to know if a model in {domain} is performing badly?",
        "How would you keep model inference fast and simple for a small-scale service?",
    ],
    "ml_engineer_behavioral": [
        "Tell me about a time you had to balance model accuracy vs engineering constraints; how did you communicate tradeoffs?",
        "Describe a situation where data quality impacted a model in production and how you handled it in {domain}.",
        "How do you collaborate across teams (infra, product, data) when shipping ML features for {domain}?",
    ],
    "ml_engineer_design": [
        "Design an online inference system for {domain} with high availability and autoscaling. Explain component choices.",
        "Propose an ML monitoring and alerting plan for production models in {domain}. Include metrics and thresholds.",
        "Sketch a feature-store and experiment-tracking architecture for reproducible ML in {domain}.",
    ],
    "data_scientist": [
        "Describe the statistical tests you would use to validate a new hypothesis in {domain}.",
        "How would you design an experiment to measure the impact of a product change for {domain}?",
        "Explain feature selection and feature engineering strategies for {domain} datasets.",
    ],
    "data_scientist_technical": [
        "Explain which statistical tests are appropriate for validating A/B experiments in {domain} and why.",
        "How would you preprocess a noisy dataset from {domain} before modeling?",
        "Describe model evaluation metrics and cross-validation strategies suited for {domain} data.",
    ],
    "data_scientist_behavioral": [
        "Describe a time you had to interpret model results for non-technical stakeholders and how you handled it.",
        "How do you design stakeholder-facing experimentation to reduce bias when evaluating features for {domain}?",
    ],
    "data_scientist_design": [
        "Design an experiment to measure user engagement improvements for a new recommendation feature in {domain}.",
        "Explain how you'd build a pipeline to monitor data drift and signal when to retrain models for {domain}.",
    ],
    "data_scientist_technical_basic": [
        "Explain a simple test to check if a new feature improves a metric in {domain}.",
        "Describe basic preprocessing steps you would apply to messy data from {domain}.",
    ],
    "data_scientist_behavioral_basic": [
        "How would you briefly summarize insights from data to a product manager for {domain}?",
        "Tell a concise example of when an experiment changed a roadmap decision.",
    ],
    "data_scientist_design_basic": [
        "Design a simple experiment to test a recommendation change for {domain} users.",
    ],
    "senior_backend_engineer": [
        "Design a scalable API for {domain} and explain caching and database strategies.",
        "How would you optimize database schema and queries for high throughput in {domain} systems?",
        "Explain your approach to distributed tracing and observability for backend systems in {domain}.",
    ],
    "frontend_engineer": [
        "Describe how you'd build a performant, accessible UI for {domain} with React.",
        "How would you diagnose and fix a memory leak or performance regression in a React app?",
        "Design a component library pattern for large-scale frontend apps used in {domain}.",
    ],
    "frontend_engineer_technical": [
        "Explain how you'd optimize rendering performance and minimize bundle size for a React app in {domain}.",
        "How would you design responsive components and ensure accessibility for a product in {domain}?",
    ],
    "frontend_engineer_behavioral": [
        "Describe a time you resolved a cross-team UX conflict and the steps you took to reach agreement.",
        "How do you balance quick engineering fixes versus long-term code health when shipping features in {domain}?",
    ],
    "frontend_engineer_design": [
        "Design a reusable component library for {domain} products; what patterns and constraints would you include?",
        "How would you plan incremental migration from a legacy UI to a modern framework for {domain}?",
    ],
    "frontend_engineer_technical_basic": [
        "How do you make a React UI feel faster? Name a couple of ways.",
        "Describe in simple terms how you would ensure accessibility in a UI component.",
    ],
    "frontend_engineer_behavioral_basic": [
        "Tell about a time you had to communicate a UI tradeoff to a designer or PM.",
    ],
    "frontend_engineer_design_basic": [
        "Sketch a simple component to render a list of items with good performance.",
    ],
    "devops_engineer": [
        "Explain the CI/CD pipeline you'd put in place for deploying services in {domain}.",
        "How do you approach incident response and postmortems for production outages in {domain}?",
        "Describe how you would design scalable infrastructure for high availability in {domain}.",
    ],
    "product_manager": [
        "How would you prioritize features and balance stakeholder needs for a product in {domain}?",
        "Describe a roadmap and metrics you'd use to measure success for a product in {domain}.",
        "Explain a market research approach you'd use to validate a new feature for {domain}.",
    ],
}


def detect_role(job_text: str) -> str:
    """Try to detect role from job_text content or return a normalized 'other' key.
    We check the first line or common role keywords.
    """
    if not job_text:
        return "other"
    first_line = job_text.splitlines()[0].strip().lower()
    # standard mappings
    role_keys = [
        ("ml", "ml_engineer"),
        ("machine learning engineer", "ml_engineer"),
        ("data scientist", "data_scientist"),
        ("senior backend", "senior_backend_engineer"),
        ("backend engineer", "senior_backend_engineer"),
        ("frontend", "frontend_engineer"),
        ("devops", "devops_engineer"),
        ("site reliability", "devops_engineer"),
        ("product manager", "product_manager"),
        ("pm", "product_manager"),
    ]
    lowered = job_text.lower()
    for k, val in role_keys:
        if k in first_line or k in lowered:
            return val
    return "other"


def generate_questions(job_text: str, n: int = 5, provider: str = "mock", question_type: str = None, difficulty: str = None) -> List[Dict[str, str]]:
    """
    Generate a list of interview questions for the provided job_text.

    provider: "mock" returns a quick heuristics-based set
              "langchain" or "openai" reserved for LLM-assisted generation
    """
    questions = []

    # If using a mock provider (or when providers fall back), create questions by combining provider-specific templates and job keywords
    # support provider-specific mock variants like "mock_openai" or "mock_anthropic"
    if provider == "mock" or provider.startswith("mock_") or provider not in ("openai", "anthropic"):
        keywords = []
        if job_text:
            tokens = job_text.split()
            # very naive keyword extraction
            keywords = [t.strip('.,()') for t in tokens if t[0].isupper() or len(t) > 6][:10]

            # If this is a mock provider variant (mock_openai/mock_anthropic) prefer provider-specific templates
            if provider.startswith("mock_"):
                key = provider.split("_", 1)[1]
                templates = PROVIDER_TEMPLATES.get(key, TEMPLATE_QUESTIONS)
            else:
                # pick role-specific templates (higher priority) then provider templates
                role = detect_role(job_text)
                # If a question_type and difficulty is provided, prefer role+type+difficulty templates, then role+type, then role templates
                k1 = f"{role}_{question_type}_{difficulty}" if question_type and difficulty else None
                k2 = f"{role}_{question_type}" if question_type else None
                if k1 and k1 in ROLE_TEMPLATES:
                    templates = ROLE_TEMPLATES[k1]
                elif k2 and k2 in ROLE_TEMPLATES:
                    templates = ROLE_TEMPLATES[k2]
                elif role in ROLE_TEMPLATES:
                    templates = ROLE_TEMPLATES[role]
                else:
                    templates = PROVIDER_TEMPLATES.get(provider, TEMPLATE_QUESTIONS)

        # choose a friendly domain label (prefer role display name)
        role = detect_role(job_text)
        ROLE_DISPLAY = {
            "ml_engineer": "Machine Learning Engineer",
            "data_scientist": "Data Scientist",
            "senior_backend_engineer": "Senior Backend Engineer",
            "frontend_engineer": "Frontend Engineer",
            "devops_engineer": "DevOps / SRE",
            "product_manager": "Product Manager",
        }

        domain_label = ROLE_DISPLAY.get(role, None)

        for i in range(n):
            base = random.choice(templates)
            if domain_label:
                domain = domain_label
            else:
                domain = keywords[i % len(keywords)] if keywords else "this domain"

            text = base.format(domain=domain)

            # If a basic difficulty was requested but we don't have dedicated basic templates,
            # make the phrasing simpler so users clearly see the difference.
            if difficulty == 'basic' and ('basic' not in templates[0] if templates else True):
                # simple heuristics to simplify phrasing
                simple_prefixes = ["In simple terms, ", "Briefly, ", "What is ", "Explain simply: "]
                # prefer shorter phrasing when possible
                if len(text.split()) > 12:
                    text = random.choice(simple_prefixes) + text[0].lower() + text[1:]
            questions.append({"id": str(i+1), "text": text, "metadata": {"source": provider}})

        return questions

    # Provider implementation for OpenAI
    if provider == "openai":
        api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            # no key available -> fall back to provider-specific mock behavior
            print("OpenAI API key not set; falling back to OpenAI-style mock question generation.")
            return generate_questions(job_text, n=n, provider="mock_openai")

        if not OPENAI_AVAILABLE:
            print("openai package not available; falling back to mock question generation.")
            return generate_questions(job_text, n=n, provider="mock")

        model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        openai.api_key = api_key

        prompt = (
            f"Create {n} interview questions for the following job description. Use the question type '{question_type or 'general'}' and difficulty '{difficulty or 'medium'}' to guide whether questions are technical/behavioral/design and the level of complexity. Return a JSON array of objects with keys: text, difficulty (easy|medium|hard), and tags (list). Job description:\n\n{job_text}\n"
        )

        try:
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "system", "content": prompts.QUESTION_GENERATION}, {"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.6,
            )
            raw = resp.choices[0].message.content.strip()

            # Attempt to parse JSON from the model response
            try:
                parsed = json.loads(raw)
            except Exception:
                # If it's not pure JSON, try to extract a JSON substring
                start = raw.find("[")
                end = raw.rfind("]")
                if start != -1 and end != -1:
                    parsed = json.loads(raw[start:end+1])
                else:
                    raise

            # normalize parsed into desired format
            out = []
            for i, item in enumerate(parsed[:n]):
                text = item.get("text") if isinstance(item, dict) else str(item)
                difficulty = item.get("difficulty") if isinstance(item, dict) else "medium"
                tags = item.get("tags") if isinstance(item, dict) else []
                out.append({"id": str(i+1), "text": text, "difficulty": difficulty, "tags": tags, "metadata": {"source": provider}})

            # If the model returned fewer than n, pad using provider templates
            templates = PROVIDER_TEMPLATES.get(provider, TEMPLATE_QUESTIONS)
            while len(out) < n:
                base = random.choice(templates)
                out.append({"id": str(len(out)+1), "text": base, "difficulty": "medium", "tags": [], "metadata": {"source": "fallback"}})

            return out
        except Exception as e:
            print("OpenAI generation failed, falling back to mock. Error:", e)
            return generate_questions(job_text, n=n, provider="mock")

    # Anthropic / Claude provider implementation
    try:
        import anthropic
        ANTHROPIC_AVAILABLE = True
    except Exception:
        ANTHROPIC_AVAILABLE = False

    if provider == "anthropic":
        api_key = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Anthropic API key not set; falling back to Anthropic-style mock question generation.")
            return generate_questions(job_text, n=n, provider="mock_anthropic")

        if not ANTHROPIC_AVAILABLE:
            print("anthropic package not available; falling back to Anthropic-style mock question generation.")
            return generate_questions(job_text, n=n, provider="mock_anthropic")

        # build a short prompt for Anthropic (expecting assistant-style completion)
        try:
            client = anthropic.Client(api_key=api_key)
            anth_prompt = f"{prompts.QUESTION_GENERATION}\nUse question type '{question_type or 'general'}' and difficulty '{difficulty or 'medium'}' to produce technical, behavioral, or design questions as appropriate.\nJob Description:\n{job_text}\nReturn a JSON array of {n} objects with keys text, difficulty, tags."
            resp = client.completions.create(model=os.environ.get("ANTHROPIC_MODEL", "claude-2.1"), prompt=anth_prompt, max_tokens=800, temperature=0.7)
            raw = resp.completion or resp.get('completion', '')
            raw = raw.strip()
            try:
                parsed = json.loads(raw)
            except Exception:
                start = raw.find("[")
                end = raw.rfind("]")
                if start != -1 and end != -1:
                    parsed = json.loads(raw[start:end+1])
                else:
                    raise

            out = []
            for i, item in enumerate(parsed[:n]):
                text = item.get("text") if isinstance(item, dict) else str(item)
                difficulty = item.get("difficulty") if isinstance(item, dict) else "medium"
                tags = item.get("tags") if isinstance(item, dict) else []
                out.append({"id": str(i+1), "text": text, "difficulty": difficulty, "tags": tags, "metadata": {"source": provider}})

            templates = PROVIDER_TEMPLATES.get(provider, TEMPLATE_QUESTIONS)
            while len(out) < n:
                base = random.choice(templates)
                out.append({"id": str(len(out)+1), "text": base.format(domain=(job_text.split()[0] if job_text else 'domain')), "difficulty": "medium", "tags": [], "metadata": {"source": "fallback"}})

            return out
        except Exception as e:
            print("Anthropic generation failed, falling back to mock. Error:", e)
            return generate_questions(job_text, n=n, provider="anthropic")

    # Placeholder: integrate LangChain or other providers here if desired
    for i in range(n):
        text = f"[LLM-generated question {i+1} for job excerpt]"
        questions.append({"id": str(i+1), "text": text, "metadata": {"source": provider}})

    return questions
