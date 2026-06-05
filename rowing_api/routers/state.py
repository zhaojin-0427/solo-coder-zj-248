from fastapi import APIRouter
from typing import Optional

from ..models import (
    TrainingState, success_response, error_response
)
from ..state_manager import StateManager
from ..storage import DataStore
from ..analyzer import StrokeAnalyzer
from ..session_storage import SessionManager
from ..session_analyzer import SessionStrokeAnalyzer

router = APIRouter(prefix="/api/state", tags=["状态管理"])

state_manager = StateManager()
store = DataStore()
analyzer = StrokeAnalyzer()
session_manager = SessionManager()


@router.get("/current")
async def get_current_state(session_id: Optional[str] = None):
    try:
        if session_id:
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            state = session_store.get_current_state()
        else:
            state = state_manager.get_current_state()
        
        state["session_id"] = session_id
        return success_response(state, "状态查询成功")
    except Exception as e:
        return error_response(500, f"查询状态失败: {str(e)}")


@router.get("/history")
async def get_state_history(session_id: Optional[str] = None):
    try:
        if session_id:
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            history = session_store.get_state_history()
        else:
            history = state_manager.get_state_history()
        
        return success_response({
            "count": len(history),
            "session_id": session_id,
            "history": history
        }, "状态历史查询成功")
    except Exception as e:
        return error_response(500, f"查询状态历史失败: {str(e)}")


@router.post("/transition")
async def manual_transition(target_state: TrainingState, reason: Optional[str] = None, session_id: Optional[str] = None):
    try:
        if session_id:
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            result = session_store.set_state(target_state, reason or "手动切换")
        else:
            result = state_manager.manual_transition(target_state, reason or "手动切换")
        
        result["session_id"] = session_id
        return success_response(result, f"已切换到{target_state.value}状态")
    except Exception as e:
        return error_response(500, f"状态切换失败: {str(e)}")


@router.post("/end-training")
async def end_training(session_id: Optional[str] = None):
    try:
        if session_id:
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            
            result = session_store.set_state(TrainingState.TRAINING_ENDED, "手动结束训练")
            session_analyzer = SessionStrokeAnalyzer(session_id)
            
            load_data = session_analyzer.calculate_training_load()
            stability = session_analyzer.calculate_stability_ranking()
            improvement = session_analyzer.calculate_improvement_trend()
        else:
            result = state_manager.end_training()
            
            load_data = analyzer.calculate_training_load()
            stability = analyzer.calculate_stability_ranking()
            improvement = analyzer.calculate_improvement_trend()
        
        result["training_load"] = load_data
        result["stability_ranking"] = [s.model_dump() for s in stability]
        result["improvement"] = improvement
        result["session_id"] = session_id
        
        return success_response(result, "训练已结束，统计报告已生成")
    except Exception as e:
        return error_response(500, f"结束训练失败: {str(e)}")


@router.post("/reset")
async def reset_all(session_id: Optional[str] = None):
    try:
        if session_id:
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            
            session_store.clear_all()
            session_store.set_state(TrainingState.NORMAL_TRAINING, "重置会话")
        else:
            state_manager.reset()
            store.clear_all()
        
        return success_response({
            "state": TrainingState.NORMAL_TRAINING,
            "reset": True,
            "session_id": session_id
        }, "已重置所有数据和状态")
    except Exception as e:
        return error_response(500, f"重置失败: {str(e)}")


@router.get("/suggestions")
async def get_pending_suggestions(session_id: Optional[str] = None):
    try:
        if session_id:
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            
            current_state = session_store.get_current_state()
            recent_anomalies = session_store.get_anomalies(limit=20)
        else:
            current_state = state_manager.get_current_state()
            recent_anomalies = store.get_anomalies(limit=20)
        
        suggestions = []
        for a in recent_anomalies:
            suggestions.append({
                "timestamp": a.timestamp,
                "type": a.anomaly_type.value,
                "severity": a.severity,
                "seats": a.seat_positions,
                "suggestion": a.suggestion
            })
        
        return success_response({
            "current_state": current_state["state"],
            "pending_suggestions": current_state.get("pending_suggestions", []),
            "recent_suggestions": suggestions,
            "session_id": session_id
        }, "建议查询成功")
    except Exception as e:
        return error_response(500, f"查询建议失败: {str(e)}")


@router.get("/summary")
async def get_training_summary(session_id: Optional[str] = None):
    try:
        if session_id:
            session_analyzer = SessionStrokeAnalyzer(session_id)
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            
            sync_history = session_analyzer.get_sync_rate_trend(limit=200)
            anomalies = session_store.get_anomalies()
            load_data = session_analyzer.calculate_training_load()
            stability = session_analyzer.calculate_stability_ranking()
            improvement = session_analyzer.calculate_improvement_trend()
            state_history = session_store.get_state_history()
        else:
            sync_history = analyzer.get_sync_rate_trend(limit=200)
            anomalies = store.get_anomalies()
            load_data = analyzer.calculate_training_load()
            stability = analyzer.calculate_stability_ranking()
            improvement = analyzer.calculate_improvement_trend()
            state_history = state_manager.get_state_history()
        
        anomaly_summary = {}
        for a in anomalies:
            t = a.anomaly_type.value
            if t not in anomaly_summary:
                anomaly_summary[t] = {"count": 0, "max_severity": 0}
            anomaly_summary[t]["count"] += 1
            anomaly_summary[t]["max_severity"] = max(
                anomaly_summary[t]["max_severity"], a.severity
            )
        
        if sync_history:
            sync_stats = {
                "avg": sum(s.overall_sync_rate for s in sync_history) / len(sync_history),
                "min": min(s.overall_sync_rate for s in sync_history),
                "max": max(s.overall_sync_rate for s in sync_history),
                "latest": sync_history[-1].overall_sync_rate if sync_history else 0
            }
        else:
            sync_stats = None
        
        return success_response({
            "sync_statistics": sync_stats,
            "anomaly_summary": anomaly_summary,
            "training_load": load_data,
            "improvement_trend": improvement,
            "stability_ranking": [s.model_dump() for s in stability],
            "state_history_count": len(state_history),
            "session_id": session_id
        }, "训练总结查询成功")
    except Exception as e:
        return error_response(500, f"查询总结失败: {str(e)}")
