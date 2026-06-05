from typing import Dict, Any

class Config:
    PORT = 9801
    HOST = "0.0.0.0"
    
    ALIGNMENT_WINDOW_MS = 100
    
    DEVICE_OFFLINE_THRESHOLD_MS = 5000
    
    MAX_HISTORY_SIZE = 10000
    
    ANOMALY_THRESHOLDS: Dict[str, Any] = {
        "stroke_rate_deviation": 3.0,
        "entry_angle_deviation": 5.0,
        "force_imbalance_ratio": 0.25,
        "rhythm_cv_threshold": 0.15,
        "sync_score_threshold": 0.75,
    }
    
    STATE_TRANSITION_CONFIG: Dict[str, Any] = {
        "warning_duration": 10,
        "adjustment_duration": 30,
        "rest_duration": 60,
    }
