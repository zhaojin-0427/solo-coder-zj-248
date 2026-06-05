from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Tutorial, TutorialStep, PaintRecord, WeatheringDetail, Favorite
from schemas import (
    TutorialCreate,
    TutorialOut,
    TutorialSummaryOut,
    TutorialStepOut,
    PaintRecordOut,
    WeatheringDetailOut,
)

router = APIRouter(prefix="/api/tutorials", tags=["tutorials"])


@router.get("", response_model=List[TutorialSummaryOut])
def get_tutorials(
    subject: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Tutorial)
    if subject:
        query = query.filter(Tutorial.subject == subject)
    if difficulty:
        query = query.filter(Tutorial.difficulty == difficulty)
    return query.order_by(Tutorial.created_at.desc()).all()


@router.post("", response_model=TutorialOut)
def create_tutorial(tutorial: TutorialCreate, db: Session = Depends(get_db)):
    data = tutorial.model_dump(exclude={"steps", "paints", "weathering_details"})
    db_tutorial = Tutorial(**data)
    db.add(db_tutorial)
    db.commit()
    db.refresh(db_tutorial)

    for step in tutorial.steps:
        db_step = TutorialStep(tutorial_id=db_tutorial.id, **step.model_dump())
        db.add(db_step)

    for paint in tutorial.paints:
        db_paint = PaintRecord(tutorial_id=db_tutorial.id, **paint.model_dump())
        db.add(db_paint)

    for wd in tutorial.weathering_details:
        db_weathering = WeatheringDetail(tutorial_id=db_tutorial.id, **wd.model_dump())
        db.add(db_weathering)

    db.commit()
    db.refresh(db_tutorial)
    return db_tutorial


@router.get("/{tutorial_id}", response_model=TutorialOut)
def get_tutorial(tutorial_id: int, db: Session = Depends(get_db)):
    tutorial = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="教程未找到")
    tutorial.views += 1
    db.commit()
    db.refresh(tutorial)
    return tutorial


@router.post("/{tutorial_id}/favorite")
def favorite_tutorial(tutorial_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    tutorial = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="教程未找到")

    existing = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user_id,
            Favorite.target_type == "tutorial",
            Favorite.target_id == tutorial_id,
        )
        .first()
    )
    if existing:
        return {"message": "已收藏过该教程", "favorited": False, "favorites": tutorial.favorites}

    favorite = Favorite(user_id=user_id, target_type="tutorial", target_id=tutorial_id)
    db.add(favorite)
    tutorial.favorites += 1
    db.commit()
    return {"message": "收藏成功", "favorited": True, "favorites": tutorial.favorites}


@router.post("/{tutorial_id}/complete")
def complete_tutorial(tutorial_id: int, db: Session = Depends(get_db)):
    tutorial = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="教程未找到")
    tutorial.completions += 1
    db.commit()
    return {"message": "完成记录已更新", "completions": tutorial.completions}
