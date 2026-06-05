from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import KitListing, KitMatch
from schemas import KitListingCreate, KitListingOut, KitMatchOut, ListingStatusUpdate

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("", response_model=List[KitListingOut])
def get_listings(
    type: Optional[str] = Query(None),
    scale: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(KitListing)
    if type:
        query = query.filter(KitListing.type == type)
    if scale:
        query = query.filter(KitListing.scale == scale)
    if manufacturer:
        query = query.filter(KitListing.manufacturer == manufacturer)
    if subject:
        query = query.filter(KitListing.subject == subject)
    if status:
        query = query.filter(KitListing.status == status)
    return query.order_by(KitListing.created_at.desc()).all()


@router.post("", response_model=KitListingOut)
def create_listing(listing: KitListingCreate, db: Session = Depends(get_db)):
    db_listing = KitListing(**listing.model_dump())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)

    _auto_match(db, db_listing)

    return db_listing


@router.get("/{listing_id}", response_model=KitListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(KitListing).filter(KitListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="挂单未找到")
    return listing


@router.get("/{listing_id}/matches", response_model=List[KitMatchOut])
def get_listing_matches(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(KitListing).filter(KitListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="挂单未找到")

    if listing.type == "sell":
        matches = db.query(KitMatch).filter(KitMatch.sell_listing_id == listing_id).all()
    else:
        matches = db.query(KitMatch).filter(KitMatch.buy_listing_id == listing_id).all()
    return matches


@router.put("/{listing_id}/status", response_model=KitListingOut)
def update_listing_status(listing_id: int, update: ListingStatusUpdate, db: Session = Depends(get_db)):
    listing = db.query(KitListing).filter(KitListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="挂单未找到")
    listing.status = update.status
    db.commit()
    db.refresh(listing)
    return listing


def _auto_match(db: Session, new_listing: KitListing):
    opposite_type = "buy" if new_listing.type == "sell" else "sell"
    candidates = (
        db.query(KitListing)
        .filter(
            KitListing.type == opposite_type,
            KitListing.status == "active",
            KitListing.id != new_listing.id,
        )
        .all()
    )

    for candidate in candidates:
        score = 0.0
        if candidate.scale == new_listing.scale:
            score += 40
        if candidate.subject == new_listing.subject:
            score += 40
        if candidate.manufacturer and candidate.manufacturer == new_listing.manufacturer:
            score += 20

        if score > 50:
            sell_id = new_listing.id if new_listing.type == "sell" else candidate.id
            buy_id = candidate.id if new_listing.type == "sell" else new_listing.id

            existing = (
                db.query(KitMatch)
                .filter(
                    KitMatch.sell_listing_id == sell_id,
                    KitMatch.buy_listing_id == buy_id,
                )
                .first()
            )
            if not existing:
                match = KitMatch(sell_listing_id=sell_id, buy_listing_id=buy_id, match_score=score)
                db.add(match)

    db.commit()
