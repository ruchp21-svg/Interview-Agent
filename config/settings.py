import os

# Model provider settings
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "mock")  # mock, openai, anthropic

# API keys (read from environment in production)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Vector DB settings
VECTOR_DB = os.environ.get("VECTOR_DB", "chroma")  # chroma, pinecone

# Storage
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local_json")  # gsheet, supabase, local_json

# Other settings
MAX_QUESTIONS_DEFAULT = 5
