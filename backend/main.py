import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from db import neo4j_db, postgres
from errors import catch_unhandled_errors, register_error_handlers
from routers import auth, health, quiz, topics
from seed.seed_graph import seed_curriculum

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("adaptlearn")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Report connectivity on startup without refusing to boot, so /api/health
    # can still explain what is wrong if a database is down.
    try:
        postgres.check_connection()
        postgres.init_db()
        logger.info("PostgreSQL connection OK, tables ready")
    except Exception as exc:
        logger.warning("PostgreSQL is not ready at startup (tables not created; restart once it is up): %s", exc)
    try:
        neo4j_db.check_connection()
        logger.info("Neo4j connection OK")
        seed_curriculum()
    except Exception as exc:
        logger.warning("Neo4j is not ready at startup (curriculum not seeded; restart once it is up): %s", exc)
    yield
    neo4j_db.close_driver()
    postgres.engine.dispose()


app = FastAPI(
    title="AdaptLearn API",
    description="Adaptive learning platform: knowledge graph, Bayesian Knowledge Tracing and AI-generated quizzes.",
    version="1.0.0",
    lifespan=lifespan,
)

register_error_handlers(app)

# Order matters: middleware added later wraps earlier middleware, so CORS sits
# outside the error catcher and 500 responses still get CORS headers.
app.middleware("http")(catch_unhandled_errors)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(quiz.router, prefix="/api")


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {"message": "AdaptLearn API is running", "docs": "/docs", "health": "/api/health"}
