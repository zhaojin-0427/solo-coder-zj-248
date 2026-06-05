import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base, DB_DIR, SessionLocal
from routers import listings, tutorials, artworks, tools, statistics, favorites


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(DB_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from models import User
        if db.query(User).first() is None:
            from seed import seed_database
            seed_database()
            print("数据库为空，已自动填充种子数据")
    finally:
        db.close()

    yield


app = FastAPI(
    title="军模交易与涂装技法分享平台",
    description="Military Model Kit Trading and Painting Technique Sharing Platform API",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router)
app.include_router(tutorials.router)
app.include_router(artworks.router)
app.include_router(tools.router)
app.include_router(statistics.router)
app.include_router(favorites.router)


@app.get("/")
def root():
    return {"message": "军模交易与涂装技法分享平台 API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
