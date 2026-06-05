from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database import get_db
from models import Favorite, KitListing, Tutorial, Artwork
from schemas import FavoriteOut, KitListingOut, TutorialSummaryOut, ArtworkOut

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
def get_favorites(
    user_id: int = Query(...),
    target_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Favorite).filter(Favorite.user_id == user_id)
    if target_type:
        query = query.filter(Favorite.target_type == target_type)
    
    favorites = query.order_by(Favorite.created_at.desc()).all()
    
    result = []
    for fav in favorites:
        item_data: Dict[str, Any] = {
            "id": fav.id,
            "user_id": fav.user_id,
            "target_type": fav.target_type,
            "target_id": fav.target_id,
            "created_at": fav.created_at,
            "target": None
        }
        
        if fav.target_type == "listing":
            listing = db.query(KitListing).filter(KitListing.id == fav.target_id).first()
            if listing:
                item_data["target"] = KitListingOut.model_validate(listing)
        elif fav.target_type == "tutorial":
            tutorial = db.query(Tutorial).filter(Tutorial.id == fav.target_id).first()
            if tutorial:
                item_data["target"] = TutorialSummaryOut.model_validate(tutorial)
        elif fav.target_type == "artwork":
            artwork = db.query(Artwork).filter(Artwork.id == fav.target_id).first()
            if artwork:
                item_data["target"] = ArtworkOut.model_validate(artwork)
        
        if item_data["target"] is not None:
            result.append(item_data)
    
    return result


@router.delete("/{favorite_id}")
def delete_favorite(favorite_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    favorite = (
        db.query(Favorite)
        .filter(Favorite.id == favorite_id, Favorite.user_id == user_id)
        .first()
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="收藏未找到")
    
    if favorite.target_type == "listing":
        listing = db.query(KitListing).filter(KitListing.id == favorite.target_id).first()
        if listing:
            listing.favorites = max(0, listing.favorites - 1)
    elif favorite.target_type == "tutorial":
        tutorial = db.query(Tutorial).filter(Tutorial.id == favorite.target_id).first()
        if tutorial:
            tutorial.favorites = max(0, tutorial.favorites - 1)
    elif favorite.target_type == "artwork":
        artwork = db.query(Artwork).filter(Artwork.id == favorite.target_id).first()
        if artwork:
            artwork.favorites = max(0, artwork.favorites - 1)
    
    db.delete(favorite)
    db.commit()
    return {"message": "收藏已删除"}


@router.get("/check")
def check_favorite(
    user_id: int = Query(...),
    target_type: str = Query(...),
    target_id: int = Query(...),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user_id,
            Favorite.target_type == target_type,
            Favorite.target_id == target_id,
        )
        .first()
    )
    return {"favorited": existing is not None, "favorite_id": existing.id if existing else None}
