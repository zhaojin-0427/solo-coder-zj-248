from fastapi import APIRouter
from typing import Optional

from ..models import (
    success_response, error_response, TrainingState
)
from ..analyzer import StrokeAnalyzer
from ..storage import DataStore
from ..state_manager import StateManager
from ..session_storage import SessionManager
from ..session_analyzer import SessionStrokeAnalyzer

router = APIRouter(prefix="/api/statistics", tags=["统计分析"])

analyzer = StrokeAnalyzer()
store = DataStore()
state_manager = StateManager()
session_manager = SessionManager()


@router.get("/overview")
async def get_overview(session_id: Optional[str] = None):
    try:
        if session_id:
            session_analyzer = SessionStrokeAnalyzer(session_id)
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            
            sync_rate = session_analyzer.calculate_sync_rate()
            active_seats = session_store.get_active_seats()
            device_info = session_store.get_device_info()
            anomalies = session_store.get_anomalies(limit=10)
            current_state = session_store.get_current_state()
            stability = session_analyzer.calculate_stability_ranking()
            
            sync_trend = session_analyzer.get_sync_rate_trend(limit=20)
        else:
            sync_rate = analyzer.calculate_sync_rate()
            active_seats = store.get_active_seats()
            device_info = store.get_device_info()
            anomalies = store.get_anomalies(limit=10)
            current_state = state_manager.get_current_state()
            stability = analyzer.calculate_stability_ranking()
            
            sync_trend = analyzer.get_sync_rate_trend(limit=20)
        
        avg_sync = (
            sum(s.overall_sync_rate for s in sync_trend) / len(sync_trend)
            if sync_trend else None
        )
        
        return success_response({
            "current_state": current_state,
            "sync_rate": sync_rate.model_dump() if sync_rate else None,
            "avg_sync_rate": avg_sync,
            "active_seats": active_seats,
            "total_devices": len(device_info),
            "online_devices": len(active_seats),
            "recent_anomalies_count": len(anomalies),
            "stability_top": [s.model_dump() for s in stability[:3]] if stability else [],
            "session_id": session_id,
            "timestamp": int(__import__("time").time() * 1000)
        }, "概览查询成功")
    except Exception as e:
        return error_response(500, f"查询概览失败: {str(e)}")


@router.get("/training-load")
async def get_training_load(start_time: Optional[int] = None,
                           end_time: Optional[int] = None,
                           session_id: Optional[str] = None):
    try:
        if session_id:
            session_analyzer = SessionStrokeAnalyzer(session_id)
            load_data = session_analyzer.calculate_training_load(start_time, end_time)
        else:
            load_data = analyzer.calculate_training_load(start_time, end_time)
        
        load_data["session_id"] = session_id
        return success_response(load_data, "训练负荷统计完成")
    except Exception as e:
        return error_response(500, f"计算训练负荷失败: {str(e)}")


@router.get("/improvement")
async def get_improvement_trend(session_id: Optional[str] = None):
    try:
        if session_id:
            session_analyzer = SessionStrokeAnalyzer(session_id)
            improvement = session_analyzer.calculate_improvement_trend()
        else:
            improvement = analyzer.calculate_improvement_trend()
        
        improvement["session_id"] = session_id
        return success_response(improvement, "技术改进趋势分析完成")
    except Exception as e:
        return error_response(500, f"分析改进趋势失败: {str(e)}")


@router.get("/sync-trend")
async def get_sync_trend(start_time: Optional[int] = None, limit: int = 100, session_id: Optional[str] = None):
    try:
        if session_id:
            session_analyzer = SessionStrokeAnalyzer(session_id)
            trend = session_analyzer.get_sync_rate_trend(start_time, limit)
        else:
            trend = analyzer.get_sync_rate_trend(start_time, limit)
        
        if trend:
            avg_overall = sum(s.overall_sync_rate for s in trend) / len(trend)
            avg_rate_sync = sum(s.stroke_rate_sync for s in trend) / len(trend)
            avg_angle_sync = sum(s.angle_sync for s in trend) / len(trend)
            avg_force_sync = sum(s.force_sync for s in trend) / len(trend)
        else:
            avg_overall = avg_rate_sync = avg_angle_sync = avg_force_sync = 0
        
        return success_response({
            "count": len(trend),
            "session_id": session_id,
            "averages": {
                "overall_sync_rate": avg_overall,
                "stroke_rate_sync": avg_rate_sync,
                "angle_sync": avg_angle_sync,
                "force_sync": avg_force_sync
            },
            "trend": [s.model_dump() for s in trend]
        }, "同步率趋势查询成功")
    except Exception as e:
        return error_response(500, f"查询同步趋势失败: {str(e)}")


@router.get("/stability/complete")
async def get_complete_stability(start_time: Optional[int] = None,
                                 end_time: Optional[int] = None,
                                 session_id: Optional[str] = None):
    try:
        if session_id:
            session_analyzer = SessionStrokeAnalyzer(session_id)
            rankings = session_analyzer.calculate_stability_ranking(start_time, end_time)
        else:
            rankings = analyzer.calculate_stability_ranking(start_time, end_time)
        
        if rankings:
            avg_stability = sum(r.stability_score for r in rankings) / len(rankings)
            avg_rate_cv = sum(r.stroke_rate_cv for r in rankings) / len(rankings)
            avg_force_cv = sum(r.force_cv for r in rankings) / len(rankings)
            avg_angle_cv = sum(r.angle_cv for r in rankings) / len(rankings)
            total_anomalies = sum(r.anomaly_count for r in rankings)
        else:
            avg_stability = avg_rate_cv = avg_force_cv = avg_angle_cv = 0
            total_anomalies = 0
        
        return success_response({
            "seat_count": len(rankings),
            "session_id": session_id,
            "overall_averages": {
                "avg_stability_score": avg_stability,
                "avg_stroke_rate_cv": avg_rate_cv,
                "avg_force_cv": avg_force_cv,
                "avg_angle_cv": avg_angle_cv,
                "total_anomalies": total_anomalies
            },
            "rankings": [r.model_dump() for r in rankings]
        }, "完整稳定性分析完成")
    except Exception as e:
        return error_response(500, f"完整稳定性分析失败: {str(e)}")


@router.get("/realtime")
async def get_realtime_data(session_id: Optional[str] = None):
    try:
        import time
        
        if session_id:
            session_analyzer = SessionStrokeAnalyzer(session_id)
            session_store = session_manager.get_session_store_or_none(session_id)
            if not session_store:
                return error_response(404, f"会话 {session_id} 不存在")
            
            sync_rate = session_analyzer.calculate_sync_rate()
            anomalies = session_analyzer.detect_anomalies()
            
            for anomaly in anomalies:
                session_store.add_state_anomaly(anomaly)
                session_store.add_state_suggestion(anomaly.suggestion)
            
            state_info = session_store.get_current_state()
            state_update = {
                "current_state": state_info["state"],
                "duration_seconds": state_info["duration_seconds"],
                "anomalies": [a.model_dump() for a in anomalies],
                "suggestions": [a.suggestion for a in anomalies]
            }
            active_seats = session_store.get_active_seats()
            aligned_data = session_store.get_aligned_data(limit=10)
        else:
            sync_rate = analyzer.calculate_sync_rate()
            anomalies = analyzer.detect_anomalies()
            state_update = state_manager.update(sync_rate, anomalies)
            active_seats = store.get_active_seats()
            aligned_data = store.get_aligned_data(limit=10)
        
        latest_by_seat = {}
        for p in aligned_data:
            seat = p.seat_position
            if seat not in latest_by_seat or p.timestamp > latest_by_seat[seat]["timestamp"]:
                latest_by_seat[seat] = p.model_dump()
        
        return success_response({
            "timestamp": int(time.time() * 1000),
            "session_id": session_id,
            "sync_rate": sync_rate.model_dump() if sync_rate else None,
            "anomalies": [a.model_dump() for a in anomalies],
            "state_update": state_update,
            "active_seats": active_seats,
            "latest_data": latest_by_seat
        }, "实时数据获取成功")
    except Exception as e:
        return error_response(500, f"获取实时数据失败: {str(e)}")
