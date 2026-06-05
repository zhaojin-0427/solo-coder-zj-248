from fastapi import APIRouter
from typing import Optional, List

from ..models import (
    success_response, error_response,
    TrainingSession, SessionCreateRequest, SessionStatus,
    TrainingPhase, TrainingState, TelemetryData,
    SessionTelemetryData, SessionStateTransitionResponse
)
from ..session_storage import SessionManager
from ..session_analyzer import SessionStrokeAnalyzer

router = APIRouter(prefix="/api/session", tags=["训练会话"])

session_manager = SessionManager()


@router.post("/create")
async def create_session(request: SessionCreateRequest):
    try:
        session = session_manager.create_session(
            team_id=request.team_id,
            boat_id=request.boat_id,
            session_name=request.session_name,
            seat_positions=request.seat_positions,
            strategy_id=request.strategy_id
        )
        return success_response(session.model_dump(), "训练会话创建成功")
    except Exception as e:
        return error_response(500, f"创建训练会话失败: {str(e)}")


@router.get("/list")
async def list_sessions(team_id: Optional[str] = None, status: Optional[SessionStatus] = None):
    try:
        sessions = session_manager.list_sessions(team_id=team_id, status=status)
        return success_response({
            "count": len(sessions),
            "sessions": [s.model_dump() for s in sessions]
        }, "会话列表查询成功")
    except Exception as e:
        return error_response(500, f"查询会话列表失败: {str(e)}")


@router.get("/{session_id}")
async def get_session(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        store = session_manager.get_session_store_or_none(session_id)
        state_info = store.get_current_state() if store else None
        state_history = store.get_state_history() if store else []
        
        return success_response({
            "session": session.model_dump(),
            "current_state": state_info,
            "state_history_count": len(state_history)
        }, "会话查询成功")
    except Exception as e:
        return error_response(500, f"查询会话失败: {str(e)}")


@router.post("/{session_id}/telemetry")
async def report_session_telemetry(data: SessionTelemetryData):
    try:
        store = session_manager.get_session_store_or_none(data.session_id)
        if not store:
            return error_response(404, f"会话 {data.session_id} 不存在")
        
        session = session_manager.get_session(data.session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            return error_response(400, f"会话 {data.session_id} 未处于活跃状态")
        
        telemetry_data = TelemetryData(
            device_id=data.device_id,
            seat_position=data.seat_position,
            timestamp=data.timestamp,
            stroke_rate=data.stroke_rate,
            entry_angle=data.entry_angle,
            pull_force=data.pull_force,
            hull_acceleration=data.hull_acceleration
        )
        
        store.add_telemetry(telemetry_data)
        store.trigger_alignment()
        
        analyzer = SessionStrokeAnalyzer(data.session_id)
        sync_rate = analyzer.calculate_sync_rate()
        anomalies = analyzer.detect_anomalies()
        
        for anomaly in anomalies:
            store.add_state_anomaly(anomaly)
            store.add_state_suggestion(anomaly.suggestion)
        
        state_info = store.get_current_state()
        
        response_data = {
            "received": True,
            "session_id": data.session_id,
            "timestamp": data.timestamp,
            "seat_position": data.seat_position,
            "sync_rate": sync_rate.model_dump() if sync_rate else None,
            "anomalies": [a.model_dump() for a in anomalies],
            "current_state": state_info
        }
        
        return success_response(response_data, "会话遥测数据上报成功")
    except Exception as e:
        return error_response(500, f"会话遥测数据上报失败: {str(e)}")


@router.post("/{session_id}/batch-telemetry")
async def batch_report_session_telemetry(data_list: List[SessionTelemetryData]):
    try:
        if not data_list:
            return error_response(400, "数据列表不能为空")
        
        session_id = data_list[0].session_id
        store = session_manager.get_session_store_or_none(session_id)
        if not store:
            return error_response(404, f"会话 {session_id} 不存在")
        
        session = session_manager.get_session(session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            return error_response(400, f"会话 {session_id} 未处于活跃状态")
        
        results = []
        for data in data_list:
            telemetry_data = TelemetryData(
                device_id=data.device_id,
                seat_position=data.seat_position,
                timestamp=data.timestamp,
                stroke_rate=data.stroke_rate,
                entry_angle=data.entry_angle,
                pull_force=data.pull_force,
                hull_acceleration=data.hull_acceleration
            )
            store.add_telemetry(telemetry_data)
            results.append({
                "device_id": data.device_id,
                "seat_position": data.seat_position,
                "timestamp": data.timestamp,
                "success": True
            })
        
        store.trigger_alignment()
        
        analyzer = SessionStrokeAnalyzer(session_id)
        sync_rate = analyzer.calculate_sync_rate()
        anomalies = analyzer.detect_anomalies()
        
        for anomaly in anomalies:
            store.add_state_anomaly(anomaly)
            store.add_state_suggestion(anomaly.suggestion)
        
        state_info = store.get_current_state()
        
        return success_response({
            "session_id": session_id,
            "received_count": len(results),
            "results": results,
            "sync_rate": sync_rate.model_dump() if sync_rate else None,
            "anomalies": [a.model_dump() for a in anomalies],
            "current_state": state_info
        }, f"成功接收{len(results)}条会话数据")
    except Exception as e:
        return error_response(500, f"批量上报会话数据失败: {str(e)}")


@router.patch("/{session_id}/phase")
async def update_session_phase(session_id: str, phase: TrainingPhase):
    try:
        session = session_manager.update_session_phase(session_id, phase)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        return success_response(session.model_dump(), f"已切换到{phase.value}阶段")
    except Exception as e:
        return error_response(500, f"切换训练阶段失败: {str(e)}")


@router.post("/{session_id}/transition")
async def transition_session_state(session_id: str, target_state: TrainingState, 
                                  reason: Optional[str] = None):
    try:
        result = session_manager.update_session_state(
            session_id, target_state, reason or "手动状态切换"
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
        
        return success_response(response.model_dump(), "状态切换成功")
    except Exception as e:
        return error_response(500, f"状态切换失败: {str(e)}")


@router.get("/{session_id}/state")
async def get_session_state(session_id: str):
    try:
        store = session_manager.get_session_store_or_none(session_id)
        if not store:
            return error_response(404, f"会话 {session_id} 不存在")
        
        state_info = store.get_current_state()
        state_history = store.get_state_history()
        
        return success_response({
            "session_id": session_id,
            "current_state": state_info,
            "state_history": state_history,
            "history_count": len(state_history)
        }, "会话状态查询成功")
    except Exception as e:
        return error_response(500, f"查询会话状态失败: {str(e)}")


@router.post("/{session_id}/end")
async def end_session(session_id: str):
    try:
        session = session_manager.end_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        load_data = analyzer.calculate_training_load()
        stability = analyzer.calculate_stability_ranking()
        improvement = analyzer.calculate_improvement_trend()
        review = analyzer.generate_training_review()
        
        store = session_manager.get_session_store_or_none(session_id)
        state_history = store.get_state_history() if store else []
        
        total_duration = 0
        state_durations = {}
        for record in state_history:
            duration = record["duration_seconds"]
            total_duration += duration
            state = record["state"].value if hasattr(record["state"], "value") else record["state"]
            if state not in state_durations:
                state_durations[state] = 0
            state_durations[state] += duration
        
        return success_response({
            "session": session.model_dump(),
            "total_duration_seconds": total_duration,
            "state_durations": state_durations,
            "training_load": load_data,
            "stability_ranking": [s.model_dump() for s in stability],
            "improvement": improvement,
            "review_summary": review.model_dump() if review else None,
            "state_history_count": len(state_history)
        }, "训练会话已结束，统计报告已生成")
    except Exception as e:
        return error_response(500, f"结束训练会话失败: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            return error_response(404, f"会话 {session_id} 不存在")
        
        return success_response({"session_id": session_id, "deleted": True}, "会话已删除")
    except Exception as e:
        return error_response(500, f"删除会话失败: {str(e)}")
