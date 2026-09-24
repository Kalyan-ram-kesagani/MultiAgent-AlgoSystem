"""Machine Learning model registry and versioning models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base, TimestampMixin


class MLModelRecord(Base, TimestampMixin):
    """Machine learning model registry record."""
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)  # REGIME_CLASSIFICATION, SIGNAL_FILTER
    current_version: Mapped[str] = mapped_column(String(32), default="v1.0.0", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="TRAINING", nullable=False)


class MLModelVersion(Base, TimestampMixin):
    """Immutable trained model snapshot with features, parameters, and evaluation scores."""
    __tablename__ = "ml_model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)  # RandomForest, LightGBM, GradientBoosting, etc.
    training_data_period: Mapped[str] = mapped_column(String(128), nullable=False)
    features_json: Mapped[str] = mapped_column(Text, nullable=False)
    hyperparameters_json: Mapped[str] = mapped_column(Text, nullable=False)

    validation_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    out_of_sample_f1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_artifact_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="TRAINING", nullable=False)  # TRAINING, VALIDATED, PAPER, PRODUCTION, RETIRED

    __table_args__ = (
        Index("idx_model_version", "model_id", "version", unique=True),
    )
