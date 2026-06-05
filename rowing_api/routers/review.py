from fastapi import APIRouter
from typing import Optional

from ..models import (
    success_response, error_response,
    TrainingReviewResponse
)
from ..session_storage import SessionManager
from ..session_analyzer import SessionStrokeAnalyzer

router = APIRouter(prefix="/api/review", tags=["训练复盘"])

session_manager = SessionManager()


@router.get("/{session_id}")
async def get_training_review(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        review = analyzer.generate_training_review()
        
        if not review:
            return error_response(400, f"会话 {session_id} 数据不足，无法生成复盘报告")
        
        return success_response(review.model_dump(), "训练复盘报告生成成功")
    except Exception as e:
        return error_response(500, f"生成复盘报告失败: {str(e)}")


@router.get("/{session_id}/sync-curve")
async def get_phase_sync_curve(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        review = analyzer.generate_training_review()
        
        if not review:
            return error_response(400, f"会话 {session_id} 数据不足")
        
        return success_response({
            "session_id": session_id,
            "phase_summary": review.phase_summary,
            "phase_sync_rate_curve": [p.model_dump() for p in review.phase_sync_rate_curve],
            "curve_points_count": len(review.phase_sync_rate_curve)
        }, "分阶段同步率曲线查询成功")
    except Exception as e:
        return error_response(500, f"查询同步率曲线失败: {str(e)}")


@router.get("/{session_id}/anomaly-durations")
async def get_anomaly_duration_stats(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        review = analyzer.generate_training_review()
        
        if not review:
            return error_response(400, f"会话 {session_id} 数据不足")
        
        return success_response({
            "session_id": session_id,
            "anomaly_duration_stats": [a.model_dump() for a in review.anomaly_duration_stats],
            "total_anomaly_types": len(review.anomaly_duration_stats)
        }, "异常持续时间统计查询成功")
    except Exception as e:
        return error_response(500, f"查询异常持续时间失败: {str(e)}")


@router.get("/{session_id}/desync-segments")
async def get_key_desync_segments(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        review = analyzer.generate_training_review()
        
        if not review:
            return error_response(400, f"会话 {session_id} 数据不足")
        
        return success_response({
            "session_id": session_id,
            "key_desync_segments": [s.model_dump() for s in review.key_desync_segments],
            "segments_count": len(review.key_desync_segments)
        }, "关键失步片段查询成功")
    except Exception as e:
        return error_response(500, f"查询失步片段失败: {str(e)}")


@router.get("/{session_id}/seat-deficiencies")
async def get_seat_technical_deficiencies(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        review = analyzer.generate_training_review()
        
        if not review:
            return error_response(400, f"会话 {session_id} 数据不足")
        
        return success_response({
            "session_id": session_id,
            "seat_technical_deficiencies": [d.model_dump() for d in review.seat_technical_deficiencies],
            "deficiencies_count": len(review.seat_technical_deficiencies)
        }, "各桨位技术短板查询成功")
    except Exception as e:
        return error_response(500, f"查询技术短板失败: {str(e)}")


@router.get("/{session_id}/load-peaks")
async def get_training_load_peaks(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        review = analyzer.generate_training_review()
        
        if not review:
            return error_response(400, f"会话 {session_id} 数据不足")
        
        return success_response({
            "session_id": session_id,
            "training_load_peaks": [p.model_dump() for p in review.training_load_peaks],
            "peaks_count": len(review.training_load_peaks)
        }, "训练负荷峰值区间查询成功")
    except Exception as e:
        return error_response(500, f"查询负荷峰值失败: {str(e)}")


@router.get("/{session_id}/strategy-comparison")
async def get_strategy_effect_comparison(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        review = analyzer.generate_training_review()
        
        if not review:
            return error_response(400, f"会话 {session_id} 数据不足")
        
        return success_response({
            "session_id": session_id,
            "strategy_effect_comparisons": [c.model_dump() for c in review.strategy_effect_comparisons],
            "comparisons_count": len(review.strategy_effect_comparisons),
            "overall_score": review.overall_score
        }, "策略调整效果对比查询成功")
    except Exception as e:
        return error_response(500, f"查询策略效果对比失败: {str(e)}")


@router.get("/{session_id}/summary")
async def get_review_summary(session_id: str):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return error_response(404, f"会话 {session_id} 不存在")
        
        analyzer = SessionStrokeAnalyzer(session_id)
        review = analyzer.generate_training_review()
        
        if not review:
            return error_response(400, f"会话 {session_id} 数据不足")
        
        top_deficiency = review.seat_technical_deficiencies[0] if review.seat_technical_deficiencies else None
        top_desync = review.key_desync_segments[0] if review.key_desync_segments else None
        
        summary = {
            "session_id": session_id,
            "total_duration_seconds": review.total_duration_seconds,
            "overall_score": review.overall_score,
            "phase_count": len(review.phase_summary),
            "anomaly_types_count": len(review.anomaly_duration_stats),
            "desync_segments_count": len(review.key_desync_segments),
            "deficiencies_count": len(review.seat_technical_deficiencies),
            "load_peaks_count": len(review.training_load_peaks),
            "strategy_adjustments_count": len(review.strategy_effect_comparisons),
            "top_issue": top_deficiency.model_dump() if top_deficiency else None,
            "worst_desync": top_desync.model_dump() if top_desync else None,
            "grade": _calculate_grade(review.overall_score)
        }
        
        return success_response(summary, "复盘摘要查询成功")
    except Exception as e:
        return error_response(500, f"查询复盘摘要失败: {str(e)}")


def _calculate_grade(score: float) -> str:
    if score >= 0.9:
        return "A"
    elif score >= 0.8:
        return "B"
    elif score >= 0.7:
        return "C"
    elif score >= 0.6:
        return "D"
    else:
        return "E"
