from fastapi import APIRouter
from typing import Optional

from ..models import (
    TrainingState, success_response, error_response
)
from ..state_manager import StateManager
from ..storage import DataStore
from ..analyzer import StrokeAnalyzer

router = APIRouter(prefix="/api/state", tags=["状态管理"])

state_manager = StateManager()
store = DataStore()
analyzer = StrokeAnalyzer()


@router.get("/current")
async def get_current_state():
    try:
        state = state_manager.get_current_state()
        return success_response(state, "状态查询成功")
    except Exception as e:
        return error_response(500, f"查询状态失败: {str(e)}")


@router.get("/history")
async def get_state_history():
    try:
        history = state_manager.get_state_history()
        return success_response({
            "count": len(history),
            "history": history
        }, "状态历史查询成功")
    except Exception as e:
        return error_response(500, f"查询状态历史失败: {str(e)}")


@router.post("/transition")
async def manual_transition(target_state: TrainingState, reason: Optional[str] = None):
    try:
        result = state_manager.manual_transition(target_state, reason or "手动切换")
        return success_response(result, f"已切换到{target_state.value}状态")
    except Exception as e:
        return error_response(500, f"状态切换失败: {str(e)}")


@router.post("/end-training")
async def end_training():
    try:
        result = state_manager.end_training()
        
        load_data = analyzer.calculate_training_load()
        stability = analyzer.calculate_stability_ranking()
        improvement = analyzer.calculate_improvement_trend()
        
        result["training_load"] = load_data
        result["stability_ranking"] = [s.model_dump() for s in stability]
        result["improvement"] = improvement
        
        return success_response(result, "训练已结束，统计报告已生成")
    except Exception as e:
        return error_response(500, f"结束训练失败: {str(e)}")


@router.post("/reset")
async def reset_all():
    try:
        state_manager.reset()
        store.clear_all()
        
        return success_response({
            "state": TrainingState.NORMAL_TRAINING,
            "reset": True
        }, "已重置所有数据和状态")
    except Exception as e:
        return error_response(500, f"重置失败: {str(e)}")


@router.get("/suggestions")
async def get_pending_suggestions():
    try:
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
            "pending_suggestions": current_state["pending_suggestions"],
            "recent_suggestions": suggestions
        }, "建议查询成功")
    except Exception as e:
        return error_response(500, f"查询建议失败: {str(e)}")


@router.get("/summary")
async def get_training_summary():
    try:
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
            "state_history_count": len(state_history)
        }, "训练总结查询成功")
    except Exception as e:
        return error_response(500, f"查询总结失败: {str(e)}")
