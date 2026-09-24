"""Research Agent API endpoints for Falsifiable Hypotheses and Experiments."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.research.research_agent import ResearchAgent
from backend.app.database.session import get_db
from backend.app.models.research import Experiment, Hypothesis
from backend.app.schemas.research import ExperimentResponse, HypothesisCreate, HypothesisResponse

router = APIRouter(prefix="/research", tags=["Research & Hypotheses"])


@router.get("/hypotheses", response_model=List[HypothesisResponse])
async def list_hypotheses(db: AsyncSession = Depends(get_db)):
    """Retrieve all logged falsifiable research hypotheses."""
    query = select(Hypothesis).order_by(Hypothesis.created_at.desc())
    result = await db.execute(query)
    records = result.scalars().all()
    return records


@router.post("/hypotheses", response_model=HypothesisResponse)
async def create_hypothesis(req: HypothesisCreate, db: AsyncSession = Depends(get_db)):
    """Submit a new falsifiable trading hypothesis."""
    agent = ResearchAgent(db_session=db)
    record = await agent.create_hypothesis(req)
    return record


@router.get("/experiments")
async def list_experiments(db: AsyncSession = Depends(get_db)):
    """Retrieve all recorded empirical experiments with full comparative metrics."""
    from backend.app.api.v1.endpoints.research_pipeline import list_experiments as pipeline_list_experiments
    return await pipeline_list_experiments(limit=50, offset=0, db=db)

