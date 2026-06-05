from fastapi import APIRouter
from typing import List, Optional

from ..models import (
    AnomalyType, TrainingState,
    success_response, error_response
)
from ..analyzer import StrokeAnalyzer
from ..storage import DataStore
from ..state_manager import StateManager

router = APIRouter(prefix="/api/analysis", tags=["划姿分析"])

analyzer = StrokeAnalyzer()
store = DataStore()
state_manager = StateManager()


@router.get("/sync-rate")
async def get_sync_rate():
    try:
        sync_rate = analyzer.calculate_sync_rate()
        
        if sync_rate:
            return success_response(sync_rate.model_dump(), "同步率计算完成")
        else:
            return success_response(None, "数据不足，无法计算同步率")
    except Exception as e:
        return error_response(500, f"计算同步率失败: {str(e)}")


@router.get("/sync-rate/history")
async def get_sync_rate_history(start_time: Optional[int] = None, limit: int = 100):
    try:
        history = analyzer.get_sync_rate_trend(start_time, limit)
        
        return success_response({
            "count": len(history),
            "trend": [s.model_dump() for s in history]
        }, "同步率趋势查询成功")
    except Exception as e:
        return error_response(500, f"查询同步率历史失败: {str(e)}")


@router.get("/anomalies")
async def get_anomalies(start_time: Optional[int] = None,
                       anomaly_types: Optional[str] = None,
                       limit: int = 100):
    try:
        types = None
        if anomaly_types:
            type_list = anomaly_types.split(",")
            types = [AnomalyType(t) for t in type_list]
        
        anomalies = store.get_anomalies(start_time, types, limit)
        
        anomaly_summary = {}
        for a in anomalies:
            t = a.anomaly_type.value
            if t not in anomaly_summary:
                anomaly_summary[t] = 0
            anomaly_summary[t] += 1
        
        return success_response({
            "count": len(anomalies),
            "summary": anomaly_summary,
            "anomalies": [a.model_dump() for a in anomalies]
        }, "异常记录查询成功")
    except Exception as e:
        return error_response(500, f"查询异常记录失败: {str(e)}")


@router.get("/detect")
async def detect_anomalies_now():
    try:
        anomalies = analyzer.detect_anomalies()
        sync_rate = analyzer.calculate_sync_rate()
        
        return success_response({
            "sync_rate": sync_rate.model_dump() if sync_rate else None,
            "anomalies": [a.model_dump() for a in anomalies],
            "anomaly_count": len(anomalies)
        }, "实时分析完成")
    except Exception as e:
        return error_response(500, f"实时分析失败: {str(e)}")


@router.get("/stability/ranking")
async def get_stability_ranking(start_time: Optional[int] = None,
                             end_time: Optional[int] = None):
    try:
        rankings = analyzer.calculate_stability_ranking(start_time, end_time)
        
        return success_response({
            "count": len(rankings),
            "rankings": [r.model_dump() for r in rankings]
        }, "稳定性排行计算完成")
    except Exception as e:
        return error_response(500, f"计算稳定性排行失败: {str(e)}")


@router.get("/alignment/latest")
async def get_latest_aligned_data(limit: int = 50):
    try:
        aligned_data = store.get_aligned_data()
        if limit and len(aligned_data) > limit:
            aligned_data = aligned_data[-limit:]
        
        by_timestamp = {}
        for p in aligned_data:
            ts = p.timestamp
            if ts not in by_timestamp:
                by_timestamp[ts] = []
            by_timestamp[ts].append(p.model_dump())
        
        return success_response({
            "timestamps_count": len(by_timestamp),
            "total_points": len(aligned_data),
            "data": by_timestamp
        }, "对齐数据查询成功")
    except Exception as e:
        return error_response(500, f"查询对齐数据失败: {str(e)}")


@router.get("/alignment/verify")
async def verify_alignment():
    try:
        aligned_by_time = store.get_latest_aligned_by_timestamp()
        
        stats = {}
        for ts, points in aligned_by_time.items():
            seats = sorted([p.seat_position for p in points])
            stats[ts] = {
                "seat_count": len(points),
                "seats": seats,
                "missing_seats": [s for s in range(1, max(seats) + 1) if s not in seats]
            }
        
        return success_response({
            "alignment_count": len(aligned_by_time),
            "details": stats
        }, "对齐验证完成")
    except Exception as e:
        return error_response(500, f"对齐验证失败: {str(e)}")
