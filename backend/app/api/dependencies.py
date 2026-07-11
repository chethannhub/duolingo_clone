from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import models
from app.database import get_db


def get_current_learner(db: Session = Depends(get_db)) -> models.Learner:
    learner = (
        db.query(models.Learner)
        .options(joinedload(models.Learner.stats))
        .filter(models.Learner.id == 1, models.Learner.is_active == 1)
        .first()
    )
    if not learner:
        raise HTTPException(status_code=404, detail="Seeded learner not found")
    return learner
