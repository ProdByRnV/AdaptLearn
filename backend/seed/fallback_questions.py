"""Every curated fallback question, keyed by topic id. The questions themselves are in seed/questions/."""

from seed.questions import Bank
from seed.questions.ai_ml import QUESTIONS as AI_ML
from seed.questions.cs_core import QUESTIONS as CS_CORE
from seed.questions.data_science import QUESTIONS as DATA_SCIENCE
from seed.questions.databases import QUESTIONS as DATABASES
from seed.questions.foundations import QUESTIONS as FOUNDATIONS
from seed.questions.python import QUESTIONS as PYTHON
from seed.questions.web_development import QUESTIONS as WEB_DEVELOPMENT


def merge(*banks: Bank) -> Bank:
    merged: Bank = {}
    for bank in banks:
        for topic_id, items in bank.items():
            if topic_id in merged:
                raise ValueError(f"fallback questions for {topic_id} are defined twice")
            merged[topic_id] = items
    return merged


FALLBACK_QUESTIONS: Bank = merge(
    FOUNDATIONS, WEB_DEVELOPMENT, PYTHON, DATA_SCIENCE, AI_ML, DATABASES, CS_CORE,
)
