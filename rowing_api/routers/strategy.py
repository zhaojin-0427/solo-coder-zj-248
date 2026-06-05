from fastapi import APIRouter
from typing import Optional, List

from ..models import (
    success_response, error_response,
    CoachStrategyConfig, StrategyConfigResponse
)
from ..session_storage import SessionManager

router = APIRouter(prefix="/api/strategy", tags=["教练策略配置"])

session_manager = SessionManager()


@router.post("/create")
async def create_strategy(config: CoachStrategyConfig):
    try:
        strategy = session_manager.create_strategy(config)
        return success_response(strategy.model_dump(), "策略配置创建成功")
    except Exception as e:
        return error_response(500, f"创建策略配置失败: {str(e)}")


@router.put("/{strategy_id}")
async def update_strategy(strategy_id: str, config: CoachStrategyConfig):
    try:
        strategy = session_manager.update_strategy(strategy_id, config)
        if not strategy:
            return error_response(404, f"策略 {strategy_id} 不存在")
        
        return success_response(strategy.model_dump(), "策略配置更新成功")
    except Exception as e:
        return error_response(500, f"更新策略配置失败: {str(e)}")


@router.get("/list")
async def list_strategies(boat_id: Optional[str] = None):
    try:
        strategies = session_manager.list_strategies(boat_id=boat_id)
        return success_response({
            "count": len(strategies),
            "strategies": [s.model_dump() for s in strategies]
        }, "策略列表查询成功")
    except Exception as e:
        return error_response(500, f"查询策略列表失败: {str(e)}")


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):
    try:
        strategy = session_manager.get_strategy(strategy_id)
        if not strategy:
            return error_response(404, f"策略 {strategy_id} 不存在")
        
        return success_response(strategy.model_dump(), "策略查询成功")
    except Exception as e:
        return error_response(500, f"查询策略失败: {str(e)}")


@router.post("/{strategy_id}/apply/{session_id}")
async def apply_strategy_to_session(strategy_id: str, session_id: str):
    try:
        success = session_manager.apply_strategy_to_session(strategy_id, session_id)
        if not success:
            return error_response(404, f"策略 {strategy_id} 或会话 {session_id} 不存在")
        
        strategy = session_manager.get_strategy(strategy_id)
        session = session_manager.get_session(session_id)
        
        return success_response({
            "strategy_id": strategy_id,
            "session_id": session_id,
            "applied": True,
            "strategy": strategy.model_dump() if strategy else None,
            "session": session.model_dump() if session else None
        }, "策略已应用到会话")
    except Exception as e:
        return error_response(500, f"应用策略失败: {str(e)}")


@router.get("/thresholds/default")
async def get_default_thresholds():
    try:
        from ..config import Config
        return success_response({
            "stroke_rate_deviation": Config.ANOMALY_THRESHOLDS["stroke_rate_deviation"],
            "entry_angle_deviation": Config.ANOMALY_THRESHOLDS["entry_angle_deviation"],
            "force_imbalance_ratio": Config.ANOMALY_THRESHOLDS["force_imbalance_ratio"],
            "rhythm_cv_threshold": Config.ANOMALY_THRESHOLDS["rhythm_cv_threshold"],
            "sync_score_threshold": Config.ANOMALY_THRESHOLDS["sync_score_threshold"],
            "offline_threshold_ms": Config.DEVICE_OFFLINE_THRESHOLD_MS,
            "consecutive_anomaly_threshold": 3
        }, "默认阈值查询成功")
    except Exception as e:
        return error_response(500, f"查询默认阈值失败: {str(e)}")
