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
