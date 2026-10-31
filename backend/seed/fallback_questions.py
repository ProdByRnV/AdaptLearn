"""Every curated fallback question, keyed by topic id. The questions themselves are in seed/questions/."""

from seed.questions import Bank
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


FALLBACK_QUESTIONS: Bank = merge(FOUNDATIONS, WEB_DEVELOPMENT, PYTHON)
