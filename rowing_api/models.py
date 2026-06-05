from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AnomalyType(str, Enum):
    STROKE_RATE_MISMATCH = "stroke_rate_mismatch"
    ENTRY_ANGLE_DEVIATION = "entry_angle_deviation"
    FORCE_IMBALANCE = "force_imbalance"
    RHYTHM_DISORDER = "rhythm_disorder"
    DEVICE_OFFLINE = "device_offline"


class TrainingState(str, Enum):
    NORMAL_TRAINING = "normal_training"
    POSTURE_WARNING = "posture_warning"
    TECHNICAL_ADJUSTMENT = "technical_adjustment"
    REST_RECOVERY = "rest_recovery"
    TRAINING_ENDED = "training_ended"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class TrainingPhase(str, Enum):
    WARMUP = "warmup"
    INTENSITY = "intensity"
    ENDURANCE = "endurance"
    COOLDOWN = "cooldown"
    INTERVAL = "interval"


class TelemetryData(BaseModel):
    device_id: str = Field(..., description="传感器设备ID")
    seat_position: int = Field(..., ge=1, description="桨位编号")
    timestamp: int = Field(..., description="时间戳(毫秒)")
    stroke_rate: float = Field(..., ge=0, description="桨频(桨/分钟)")
    entry_angle: float = Field(..., description="入水角度(度)")
    pull_force: float = Field(..., ge=0, description="拉桨力量(牛顿)")
    hull_acceleration: float = Field(..., description="船体加速度(m/s²)")


class AlignedDataPoint(BaseModel):
    timestamp: int
    seat_position: int
    device_id: str
    stroke_rate: float
    entry_angle: float
    pull_force: float
    hull_acceleration: float
    stroke_phase: Optional[float] = None


class AnomalyRecord(BaseModel):
    anomaly_type: AnomalyType
    severity: float = Field(..., ge=0, le=1, description="严重程度")
    timestamp: int
    seat_positions: List[int]
    description: str
    suggestion: str


class SyncRateResult(BaseModel):
    timestamp: int
    overall_sync_rate: float = Field(..., ge=0, le=1)
    seat_sync_rates: Dict[int, float]
    stroke_rate_sync: float
    angle_sync: float
    force_sync: float


class StrokeStability(BaseModel):
    seat_position: int
    device_id: str
    stability_score: float = Field(..., ge=0, le=1)
    stroke_rate_cv: float
    force_cv: float
    angle_cv: float
    anomaly_count: int


class TrainingStateRecord(BaseModel):
    state: TrainingState
    start_time: int
    end_time: Optional[int] = None
    duration_seconds: int = 0
    anomalies: List[AnomalyRecord] = []
    suggestions: List[str] = []


class ApiResponse(BaseModel):
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


def success_response(data: Any = None, message: str = "success") -> Dict[str, Any]:
    return {"code": 200, "message": message, "data": data}


def error_response(code: int, message: str, data: Any = None) -> Dict[str, Any]:
    return {"code": code, "message": message, "data": data}


class CoachStrategyConfig(BaseModel):
    boat_id: str = Field(..., description="艇次ID")
    stroke_rate_target_min: float = Field(25.0, ge=10, le=60, description="桨频目标下限(桨/分钟)")
    stroke_rate_target_max: float = Field(35.0, ge=10, le=60, description="桨频目标上限(桨/分钟)")
    entry_angle_tolerance: float = Field(5.0, ge=0.5, le=20, description="入水角度容忍区间(度)")
    force_balance_weight: float = Field(1.0, ge=0.1, le=3.0, description="力量均衡权重")
    offline_threshold_ms: int = Field(5000, ge=1000, le=30000, description="设备离线阈值(毫秒)")
    rhythm_stability_threshold: float = Field(0.15, ge=0.05, le=0.5, description="节奏稳定阈值(CV)")
    consecutive_anomaly_threshold: int = Field(3, ge=1, le=10, description="连续异常触发干预阈值")
    sync_score_threshold: float = Field(0.75, ge=0.5, le=0.95, description="同步率合格阈值")


class StrategyConfigResponse(BaseModel):
    strategy_id: str
    boat_id: str
    config: CoachStrategyConfig
    created_at: int
    updated_at: int


class TrainingSession(BaseModel):
    session_id: str
    team_id: str
    boat_id: str
    session_name: Optional[str] = None
    status: SessionStatus
    created_at: int
    started_at: Optional[int] = None
    ended_at: Optional[int] = None
    seat_positions: List[int] = Field(default_factory=list)
    current_phase: TrainingPhase = TrainingPhase.WARMUP
    current_state: TrainingState = TrainingState.NORMAL_TRAINING
    strategy_id: Optional[str] = None


class SessionCreateRequest(BaseModel):
    team_id: str
    boat_id: str
    session_name: Optional[str] = None
    seat_positions: List[int] = Field(default_factory=lambda: [1, 2, 3, 4])
    strategy_id: Optional[str] = None


class SessionTelemetryData(TelemetryData):
    session_id: str


class PhaseSyncRatePoint(BaseModel):
    phase: TrainingPhase
    timestamp: int
    overall_sync_rate: float
    seat_sync_rates: Dict[int, float]


class AnomalyDurationStats(BaseModel):
    anomaly_type: AnomalyType
    total_duration_seconds: float
    count: int
    avg_duration_seconds: float
    max_duration_seconds: float


class KeyDesyncSegment(BaseModel):
    start_timestamp: int
    end_timestamp: int
    duration_seconds: float
    min_sync_rate: float
    anomaly_types: List[AnomalyType]
    affected_seats: List[int]
    description: str


class SeatTechnicalDeficiency(BaseModel):
    seat_position: int
    primary_issue: AnomalyType
    issue_count: int
    avg_severity: float
    description: str
    improvement_suggestion: str


class TrainingLoadPeak(BaseModel):
    start_timestamp: int
    end_timestamp: int
    duration_seconds: float
    peak_load_score: float
    avg_stroke_rate: float
    avg_force: float
    affected_seats: List[int]


class StrategyEffectComparison(BaseModel):
    strategy_id: str
    applied_at: int
    before_period: Dict[str, Any]
    after_period: Dict[str, Any]
    improvement_score: float
    key_metrics_changed: List[str]


class TrainingReviewResponse(BaseModel):
    session_id: str
    session_name: Optional[str] = None
    total_duration_seconds: float
    phase_summary: Dict[str, Dict[str, Any]]
    phase_sync_rate_curve: List[PhaseSyncRatePoint]
    anomaly_duration_stats: List[AnomalyDurationStats]
    key_desync_segments: List[KeyDesyncSegment]
    seat_technical_deficiencies: List[SeatTechnicalDeficiency]
    training_load_peaks: List[TrainingLoadPeak]
    strategy_effect_comparisons: List[StrategyEffectComparison]
    overall_score: float


class SeatInterventionSuggestion(BaseModel):
    seat_position: int
    action_type: str
    parameter: str
    target_value: float
    current_value: float
    urgency: str
    description: str


class RealTimeInterventionResponse(BaseModel):
    session_id: str
    timestamp: int
    current_state: TrainingState
    consecutive_anomaly_count: int
    requires_intervention: bool
    seat_suggestions: List[SeatInterventionSuggestion]
    overall_suggestion: str
    recommended_state_transition: Optional[TrainingState]


class SessionStateTransitionResponse(BaseModel):
    session_id: str
    previous_state: TrainingState
    current_state: TrainingState
    transitioned: bool
    reason: str
    timestamp: int
