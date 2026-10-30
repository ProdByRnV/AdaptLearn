"""Which domains a learner has joined, and whether they've been through each one's onboarding.

Joining only records interest (decision 12: no domain has priority, so learners join any domains
in any order). Progress belongs to topics, so joining never changes a topic's status.
"""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models import DomainEnrolment
from services.topic_service import ensure_domain


def get_enrolments(db: Session, user_id: int) -> dict[str, DomainEnrolment]:
    """The learner's enrolments by domain id (callers look up supported domains only)."""
    rows = db.scalars(select(DomainEnrolment).where(DomainEnrolment.user_id == user_id))
    return {row.domain_id: row for row in rows}


def is_onboarded(db: Session, user_id: int, domain: str) -> bool:
    onboarded_at = db.scalar(
        select(DomainEnrolment.onboarded_at).where(
            DomainEnrolment.user_id == user_id, DomainEnrolment.domain_id == domain
        )
    )
    return onboarded_at is not None


def join_domain(db: Session, user_id: int, domain: str) -> tuple[DomainEnrolment, bool]:
    """Join a domain. Returns (enrolment, joined_now); joining again changes nothing. Commits."""
    ensure_domain(domain)
    inserted = db.scalar(
        insert(DomainEnrolment)
        .values(user_id=user_id, domain_id=domain)
        .on_conflict_do_nothing(index_elements=["user_id", "domain_id"])
        .returning(DomainEnrolment.id)
    )
    db.commit()
    enrolment = db.scalar(
        select(DomainEnrolment).where(DomainEnrolment.user_id == user_id, DomainEnrolment.domain_id == domain)
    )
    return enrolment, inserted is not None


def mark_onboarded(db: Session, user_id: int, domain: str) -> None:
    """Onboarding joins the domain if needed and records when it was first completed. Does not commit."""
    stmt = insert(DomainEnrolment).values(user_id=user_id, domain_id=domain, onboarded_at=func.now())
    db.execute(
        stmt.on_conflict_do_update(
            index_elements=["user_id", "domain_id"],
            set_={"onboarded_at": func.coalesce(DomainEnrolment.__table__.c.onboarded_at, stmt.excluded.onboarded_at)},
        )
    )
