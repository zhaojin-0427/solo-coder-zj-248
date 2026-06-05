from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Artwork, Favorite
from schemas import ArtworkCreate, ArtworkOut

router = APIRouter(prefix="/api/artworks", tags=["artworks"])


@router.get("", response_model=List[ArtworkOut])
def get_artworks(
    subject: Optional[str] = Query(None),
    technique: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Artwork)
    if subject:
        query = query.filter(Artwork.subject == subject)
    if technique:
        query = query.filter(Artwork.techniques.contains(technique))
    return query.order_by(Artwork.created_at.desc()).all()


@router.post("", response_model=ArtworkOut)
def create_artwork(artwork: ArtworkCreate, db: Session = Depends(get_db)):
    db_artwork = Artwork(**artwork.model_dump())
    db.add(db_artwork)
    db.commit()
    db.refresh(db_artwork)
    return db_artwork


@router.get("/{artwork_id}", response_model=ArtworkOut)
def get_artwork(artwork_id: int, db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="作品未找到")
    return artwork


@router.post("/{artwork_id}/like")
def like_artwork(artwork_id: int, db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="作品未找到")
    artwork.likes += 1
    db.commit()
    return {"message": "点赞成功", "likes": artwork.likes}


@router.post("/{artwork_id}/favorite")
def favorite_artwork(artwork_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="作品未找到")

    existing = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user_id,
            Favorite.target_type == "artwork",
            Favorite.target_id == artwork_id,
        )
        .first()
    )
    if existing:
        return {"message": "已收藏过该作品", "favorited": False, "favorites": artwork.favorites}

    favorite = Favorite(user_id=user_id, target_type="artwork", target_id=artwork_id)
    db.add(favorite)
    artwork.favorites += 1
    db.commit()
    return {"message": "收藏成功", "favorited": True, "favorites": artwork.favorites}
