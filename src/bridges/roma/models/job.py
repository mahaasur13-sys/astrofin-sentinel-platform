from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON
from db.engine import Base
import uuid
from datetime import datetime, timezone


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task = Column(String, nullable=False)
    status = Column(String, default="queued")
    priority = Column(Integer, default=5)
    execution_mode = Column(String, default="k8s_job")
    gpu_required = Column(Boolean, default=False)
    roma_dispatch = Column(JSON)
    dag = Column(JSON)
    estimated_resources = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(String, nullable=True)
