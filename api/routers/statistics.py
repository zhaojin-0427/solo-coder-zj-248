from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import KitListing, KitMatch, Tutorial, Favorite, TutorialStep
from schemas import (
    PopularSubjectOut,
    TurnoverSpeedOut,
    TutorialCompletionOut,
    TechniqueFavoriteOut,
)

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/popular-subjects", response_model=list[PopularSubjectOut])
def popular_subjects(db: Session = Depends(get_db)):
    results = (
        db.query(KitListing.scale, KitListing.subject, func.count(KitListing.id).label("count"))
        .group_by(KitListing.scale, KitListing.subject)
        .order_by(func.count(KitListing.id).desc())
        .all()
    )
    return [PopularSubjectOut(scale=r[0], subject=r[1], count=r[2]) for r in results]


@router.get("/turnover-speed", response_model=list[TurnoverSpeedOut])
def turnover_speed(db: Session = Depends(get_db)):
    matches = db.query(KitMatch).all()
    from collections import defaultdict
    monthly = defaultdict(list)

    for m in matches:
        sell = db.query(KitListing).filter(KitListing.id == m.sell_listing_id).first()
        if sell and m.created_at and sell.created_at:
            month_key = m.created_at.strftime("%Y-%m")
            delta_days = (m.created_at - sell.created_at).days
            if delta_days >= 0:
                monthly[month_key].append(delta_days)

    result = []
    for month, days_list in sorted(monthly.items()):
        avg = sum(days_list) / len(days_list) if days_list else 0
        result.append(TurnoverSpeedOut(month=month, avg_days=round(avg, 1)))
    return result


@router.get("/tutorial-completion", response_model=list[TutorialCompletionOut])
def tutorial_completion(db: Session = Depends(get_db)):
    tutorials = db.query(Tutorial).all()
    result = []
    for t in tutorials:
        rate = (t.completions / t.views * 100) if t.views > 0 else 0
        result.append(
            TutorialCompletionOut(
                tutorial_id=t.id,
                title=t.title,
                views=t.views,
                completions=t.completions,
                completion_rate=round(rate, 1),
            )
        )
    return result


@router.get("/technique-favorites", response_model=list[TechniqueFavoriteOut])
def technique_favorites(db: Session = Depends(get_db)):
    favorites = (
        db.query(Favorite)
        .filter(Favorite.target_type == "technique")
        .all()
    )

    from collections import Counter
    technique_counts = Counter()
    for fav in favorites:
        if fav.target_type == "technique":
            step = db.query(TutorialStep).filter(TutorialStep.id == fav.target_id).first()
            if step and step.technique:
                technique_counts[step.technique] += 1

    result = []
    for technique, count in technique_counts.most_common(20):
        result.append(TechniqueFavoriteOut(technique=technique, favorite_count=count))
    return result
