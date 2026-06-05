from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), nullable=False, default="player")
    avatar = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    listings = relationship("KitListing", back_populates="user")
    tutorials = relationship("Tutorial", back_populates="user")
    artworks = relationship("Artwork", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")


class KitListing(Base):
    __tablename__ = "kit_listings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    type = Column(String(10), nullable=False)
    scale = Column(String(20), nullable=False)
    manufacturer = Column(String(100), default="")
    condition = Column(String(20), default="sealed")
    missing_parts = Column(Text, default="")
    subject = Column(String(100), nullable=False)
    price = Column(Float, default=0.0)
    description = Column(Text, default="")
    images = Column(JSON, default=list)
    status = Column(String(20), default="active")
    favorites = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="listings")
    sell_matches = relationship("KitMatch", foreign_keys="KitMatch.sell_listing_id", back_populates="sell_listing")
    buy_matches = relationship("KitMatch", foreign_keys="KitMatch.buy_listing_id", back_populates="buy_listing")


class KitMatch(Base):
    __tablename__ = "kit_matches"

    id = Column(Integer, primary_key=True, index=True)
    sell_listing_id = Column(Integer, ForeignKey("kit_listings.id"), nullable=False)
    buy_listing_id = Column(Integer, ForeignKey("kit_listings.id"), nullable=False)
    match_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sell_listing = relationship("KitListing", foreign_keys=[sell_listing_id], back_populates="sell_matches")
    buy_listing = relationship("KitListing", foreign_keys=[buy_listing_id], back_populates="buy_matches")


class Tutorial(Base):
    __tablename__ = "tutorials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    subject = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False, default="beginner")
    cover_image = Column(String(255), default="")
    views = Column(Integer, default=0)
    completions = Column(Integer, default=0)
    favorites = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tutorials")
    steps = relationship("TutorialStep", back_populates="tutorial", cascade="all, delete-orphan")
    paints = relationship("PaintRecord", back_populates="tutorial", cascade="all, delete-orphan")
    weathering_details = relationship("WeatheringDetail", back_populates="tutorial", cascade="all, delete-orphan")


class TutorialStep(Base):
    __tablename__ = "tutorial_steps"

    id = Column(Integer, primary_key=True, index=True)
    tutorial_id = Column(Integer, ForeignKey("tutorials.id"), nullable=False)
    order_num = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    image = Column(String(255), default="")
    technique = Column(String(100), default="")

    tutorial = relationship("Tutorial", back_populates="steps")


class PaintRecord(Base):
    __tablename__ = "paint_records"

    id = Column(Integer, primary_key=True, index=True)
    tutorial_id = Column(Integer, ForeignKey("tutorials.id"), nullable=False)
    name = Column(String(100), nullable=False)
    brand = Column(String(100), default="")
    color_code = Column(String(50), default="")
    usage = Column(String(200), default="")

    tutorial = relationship("Tutorial", back_populates="paints")


class WeatheringDetail(Base):
    __tablename__ = "weathering_details"

    id = Column(Integer, primary_key=True, index=True)
    tutorial_id = Column(Integer, ForeignKey("tutorials.id"), nullable=False)
    type = Column(String(100), nullable=False)
    products = Column(JSON, default=list)
    technique = Column(String(200), default="")
    description = Column(Text, default="")

    tutorial = relationship("Tutorial", back_populates="weathering_details")


class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    subject = Column(String(100), nullable=False)
    scale = Column(String(20), default="")
    kit_name = Column(String(200), default="")
    images = Column(JSON, default=list)
    paints = Column(JSON, default=list)
    techniques = Column(JSON, default=list)
    weathering = Column(JSON, default=list)
    likes = Column(Integer, default=0)
    favorites = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="artworks")


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)
    brand = Column(String(100), default="")
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    description = Column(Text, default="")
    image = Column(String(255), default="")
    recommended_by = Column(JSON, default=list)


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
