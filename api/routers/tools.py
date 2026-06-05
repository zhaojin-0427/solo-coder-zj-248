from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Tool
from schemas import ToolOut

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("", response_model=List[ToolOut])
def get_tools(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Tool)
    if category:
        query = query.filter(Tool.category == category)
    return query.all()


@router.get("/{tool_id}", response_model=ToolOut)
def get_tool(tool_id: int, db: Session = Depends(get_db)):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="工具未找到")
    return tool
