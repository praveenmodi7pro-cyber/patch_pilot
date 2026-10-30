import asyncio
from typing import Optional
from app.workers.pipeline import AnalysisPipelineRunner


class JobQueue:
    """Dispatches background analysis and test execution jobs."""

    @staticmethod
    def enqueue_analysis(analysis_id: str):
        """Enqueue asynchronous analysis pipeline execution."""
        asyncio.create_task(AnalysisPipelineRunner.run_pipeline(analysis_id))


job_queue = JobQueue()

