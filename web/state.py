from src.ai_assistant.llm_client import LLMClient
from src.database.db import init_db, load_profile
from src.path_generator.path_builder import LearningPathGenerator
from src.profiling.profiler import load_all_items

init_db()

CATALOG = load_all_items()
LLM = LLMClient()
GENERATOR = LearningPathGenerator()

messages: list[dict] = []
learning_path = None
path_variants = None


def profile():
    return load_profile("default_user")
