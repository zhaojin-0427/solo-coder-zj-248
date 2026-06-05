from fastapi import APIRouter
from typing import Optional

from ..models import (
    success_response, error_response,
    RealTimeInterventionResponse, TrainingState,
    SessionStateTransitionResponse
)
from ..session_storage import SessionManager
from ..session_analyzer import SessionStrokeAnalyzer

router = APIRouter(prefix="/api/intervention", tags=["实时干预"])

session_manager = SessionManager()


@router.get("/{session_id}")
async def get_real_time_intervention(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        intervention = analyzer.generate_real_time_intervention()
        
        if not intervention:
            return error_response(400, f"会话 {session_id} 数据不足")
        
        return success_response(intervention.model_dump(), "实时干预建议生成成功")
    except Exception as e:
        return error_response(500, f"生成干预建议失败: {str(e)}")


@router.post("/{session_id}/suggestions")
async def get_pending_suggestions(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        store = session_manager.get_session_store_or_none(session_id)
        if not store:
            return error_response(404, f"会话 {session_id} 不存在")
        
        state_info = store.get_current_state()
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
            "session_id": session_id,
            "current_state": state_info["state"],
            "pending_suggestions": state_info["pending_suggestions"] if "pending_suggestions" in state_info else [],
            "recent_suggestions": suggestions
        }, "待处理建议查询成功")
    except Exception as e:
        return error_response(500, f"查询建议失败: {str(e)}")


@router.post("/{session_id}/execute")
async def execute_intervention(session_id: str, auto_apply: Optional[bool] = False):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        intervention = analyzer.generate_real_time_intervention()
        
        if not intervention:
            return error_response(400, f"会话 {session_id} 数据不足，无法生成干预建议")
        
        transition_result = None
        if auto_apply and intervention.recommended_state_transition:
            transition_data = session_manager.update_session_state(
                session_id,
                intervention.recommended_state_transition,
                "自动应用干预建议"
            )
            if transition_data:
                transition_result = SessionStateTransitionResponse(
                    session_id=session_id,
                    previous_state=transition_data["previous_state"],
                    current_state=transition_data["current_state"],
                    transitioned=transition_data["transitioned"],
                    reason=transition_data["reason"],
                    timestamp=transition_data["timestamp"]
                )
        
        return success_response({
            "session_id": session_id,
            "intervention": intervention.model_dump(),
            "state_transition": transition_result.model_dump() if transition_result else None,
            "auto_applied": auto_apply and transition_result is not None
        }, "干预建议执行成功")
    except Exception as e:
        return error_response(500, f"执行干预失败: {str(e)}")


@router.post("/{session_id}/transition")
async def manual_intervention_transition(session_id: str, target_state: TrainingState,
                                     reason: Optional[str] = None):
    try:
        result = session_manager.update_session_state(
            session_id, target_state, reason or "手动干预状态切换"
        )
        if not result:
            return error_response(404, f"会话 {session_id} 不存在")
        
        response = SessionStateTransitionResponse(
            session_id=session_id,
            previous_state=result["previous_state"],
            current_state=result["current_state"],
            transitioned=result["transitioned"],
            reason=result["reason"],
            timestamp=result["timestamp"]
        )
        
        return success_response(response.model_dump(), "干预状态切换成功")
    except Exception as e:
        return error_response(500, f"状态切换失败: {str(e)}")


@router.post("/{session_id}/acknowledge")
async def acknowledge_suggestions(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        store = session_manager.get_session_store_or_none(session_id)
        if not store:
            return error_response(404, f"会话 {session_id} 不存在")
        
        store.reset_consecutive_anomaly_count()
        
        return success_response({
            "session_id": session_id,
            "acknowledged": True,
            "consecutive_anomaly_count": 0
        }, "建议已确认，连续异常计数已重置")
    except Exception as e:
        return error_response(500, f"确认建议失败: {str(e)}")


@router.get("/{session_id}/status")
async def get_intervention_status(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        store = session_manager.get_session_store_or_none(session_id)
        if not store:
            return error_response(404, f"会话 {session_id} 不存在")
        
        consecutive_count = store.get_consecutive_anomaly_count()
        state_info = store.get_current_state()
        state_history = store.get_state_history()
        
        return success_response({
            "session_id": session_id,
            "current_state": state_info["state"],
            "consecutive_anomaly_count": consecutive_count,
            "state_duration_seconds": state_info.get("duration_seconds", 0),
            "current_anomalies_count": len(state_info.get("current_anomalies", [])),
            "state_transitions_count": len(state_history),
            "requires_intervention": consecutive_count >= 3
        }, "干预状态查询成功")
    except Exception as e:
        return error_response(500, f"查询干预状态失败: {str(e)}")
