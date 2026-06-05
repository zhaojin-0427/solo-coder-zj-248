import time
import threading
import uuid
from typing import Dict, List, Optional, Tuple, Deque, Union, Any
from collections import deque
import numpy as np

from .config import Config
from .models import (
    TelemetryData, AlignedDataPoint, AnomalyType, AnomalyRecord,
    TrainingSession, SessionStatus, TrainingState, TrainingPhase,
    CoachStrategyConfig, StrategyConfigResponse, SyncRateResult,
    TrainingStateRecord
)
from .storage import DataStore


class SessionDataStore:
    def __init__(self, session_id: str, strategy: Optional[CoachStrategyConfig] = None):
        self.session_id = session_id
        self.strategy = strategy
        self._lock = threading.Lock()
        
        self._raw_data: Dict[int, deque] = {}
        self._aligned_data: deque = deque(maxlen=Config.MAX_HISTORY_SIZE)
        self._device_last_seen: Dict[str, int] = {}
        self._seat_device_map: Dict[int, str] = {}
        self._device_seat_map: Dict[str, int] = {}
        self._anomaly_history: List[AnomalyRecord] = []
        self._sync_rate_history: List[SyncRateResult] = []
        self._alignment_buffer: Dict[int, List[TelemetryData]] = {}
        self._last_alignment_time: int = 0
        
        self._time_window_index: Dict[int, List[AlignedDataPoint]] = {}
        self._window_start_times: List[int] = []
        
        self._consecutive_anomaly_count: int = 0
        self._last_anomaly_time: int = 0
        self._anomaly_start_times: Dict[AnomalyType, int] = {}
        
        self._state_history: List[TrainingStateRecord] = []
        self._current_state_record: Optional[TrainingStateRecord] = None
        self._current_state: TrainingState = TrainingState.NORMAL_TRAINING
        self._state_start_time: int = int(time.time() * 1000)
        
        self._phase_start_times: Dict[TrainingPhase, int] = {}
        self._current_phase: TrainingPhase = TrainingPhase.WARMUP
        
        self._strategy_application_times: List[Tuple[int, str]] = []

    def _get_thresholds(self) -> Dict[str, float]:
        if self.strategy:
            return {
                "stroke_rate_deviation": (self.strategy.stroke_rate_target_max - self.strategy.stroke_rate_target_min) / 2,
                "entry_angle_deviation": self.strategy.entry_angle_tolerance,
                "force_imbalance_ratio": 0.25 / self.strategy.force_balance_weight,
                "rhythm_cv_threshold": self.strategy.rhythm_stability_threshold,
                "sync_score_threshold": self.strategy.sync_score_threshold,
                "offline_threshold_ms": self.strategy.offline_threshold_ms,
                "consecutive_anomaly_threshold": self.strategy.consecutive_anomaly_threshold,
            }
        return {
            **Config.ANOMALY_THRESHOLDS,
            "offline_threshold_ms": Config.DEVICE_OFFLINE_THRESHOLD_MS,
            "consecutive_anomaly_threshold": 3,
        }

    def add_telemetry(self, data: TelemetryData) -> None:
        with self._lock:
            seat = data.seat_position
            if seat not in self._raw_data:
                self._raw_data[seat] = deque(maxlen=1000)
            
            self._raw_data[seat].append(data)
            self._device_last_seen[data.device_id] = data.timestamp
            self._seat_device_map[seat] = data.device_id
            self._device_seat_map[data.device_id] = seat

            if seat not in self._alignment_buffer:
                self._alignment_buffer[seat] = []
            self._alignment_buffer[seat].append(data)

    def trigger_alignment(self) -> None:
        with self._lock:
            current_time = int(time.time() * 1000)
            min_seats_for_alignment = 2
            seats_with_data = sum(
                1 for buffer in self._alignment_buffer.values() 
                if len(buffer) > 0
            )
            
            if seats_with_data >= min_seats_for_alignment:
                self._perform_alignment(current_time)
                self._last_alignment_time = current_time

    def _perform_alignment(self, target_time: int) -> None:
        window_start = target_time - Config.ALIGNMENT_WINDOW_MS * 5
        window_end = target_time + Config.ALIGNMENT_WINDOW_MS * 5

        seat_points: Dict[int, TelemetryData] = {}
        
        for seat, buffer in self._alignment_buffer.items():
            valid_points = [p for p in buffer if window_start <= p.timestamp <= window_end]
            if valid_points:
                closest = min(valid_points, key=lambda p: abs(p.timestamp - target_time))
                seat_points[seat] = closest

        if len(seat_points) >= 2:
            aligned_points = []
            for seat, data in seat_points.items():
                aligned_point = AlignedDataPoint(
                    timestamp=target_time,
                    seat_position=seat,
                    device_id=data.device_id,
                    stroke_rate=data.stroke_rate,
                    entry_angle=data.entry_angle,
                    pull_force=data.pull_force,
                    hull_acceleration=data.hull_acceleration
                )
                aligned_points.append(aligned_point)
                self._aligned_data.append(aligned_point)
            
            window_key = target_time // 1000
            if window_key not in self._time_window_index:
                self._time_window_index[window_key] = []
                self._window_start_times.append(window_key)
            self._time_window_index[window_key].extend(aligned_points)
            
            if len(self._window_start_times) > 3600:
                old_key = self._window_start_times.pop(0)
                if old_key in self._time_window_index:
                    del self._time_window_index[old_key]

            for seat in self._alignment_buffer:
                self._alignment_buffer[seat] = [
                    p for p in self._alignment_buffer[seat]
                    if p.timestamp > window_end
                ]

    def get_aligned_data(self, start_time: Optional[int] = None, 
                         end_time: Optional[int] = None,
                         seats: Optional[List[int]] = None,
                         limit: Optional[int] = None) -> List[AlignedDataPoint]:
        with self._lock:
            result = list(self._aligned_data)
            
            if start_time:
                result = [p for p in result if p.timestamp >= start_time]
            if end_time:
                result = [p for p in result if p.timestamp <= end_time]
            if seats:
                result = [p for p in result if p.seat_position in seats]
            if limit and len(result) > limit:
                result = result[-limit:]
            
            return result

    def get_data_by_window(self, window_start: int, window_end: int) -> List[AlignedDataPoint]:
        with self._lock:
            result = []
            start_key = window_start // 1000
            end_key = window_end // 1000
            
            for key in range(start_key, end_key + 1):
                if key in self._time_window_index:
                    result.extend(self._time_window_index[key])
            
            result = [p for p in result if window_start <= p.timestamp <= window_end]
            return result

    def get_latest_aligned_by_timestamp(self) -> Dict[int, List[AlignedDataPoint]]:
        with self._lock:
            result: Dict[int, List[AlignedDataPoint]] = {}
            for point in self._aligned_data:
                if point.timestamp not in result:
                    result[point.timestamp] = []
                result[point.timestamp].append(point)
            return result

    def get_active_seats(self) -> List[int]:
        with self._lock:
            current_time = int(time.time() * 1000)
            thresholds = self._get_thresholds()
            offline_threshold = thresholds["offline_threshold_ms"]
            active = []
            for seat, device_id in self._seat_device_map.items():
                last_seen = self._device_last_seen.get(device_id, 0)
                if current_time - last_seen < offline_threshold:
                    active.append(seat)
            return sorted(active)

    def get_offline_devices(self) -> List[Tuple[int, str]]:
        with self._lock:
            current_time = int(time.time() * 1000)
            thresholds = self._get_thresholds()
            offline_threshold = thresholds["offline_threshold_ms"]
            offline = []
            for seat, device_id in self._seat_device_map.items():
                last_seen = self._device_last_seen.get(device_id, 0)
                if current_time - last_seen >= offline_threshold:
                    offline.append((seat, device_id))
            return offline

    def check_device_offline(self) -> List[AnomalyRecord]:
        offline = self.get_offline_devices()
        anomalies = []
        current_time = int(time.time() * 1000)
        
        for seat, device_id in offline:
            last_seen = self._device_last_seen.get(device_id, 0)
            offline_duration = (current_time - last_seen) / 1000
            severity = min(1.0, offline_duration / 30.0)
            
            existing = [a for a in self._anomaly_history 
                       if a.anomaly_type == AnomalyType.DEVICE_OFFLINE
                       and seat in a.seat_positions
                       and current_time - a.timestamp < 5000]
            
            if not existing:
                anomaly = AnomalyRecord(
                    anomaly_type=AnomalyType.DEVICE_OFFLINE,
                    severity=severity,
                    timestamp=current_time,
                    seat_positions=[seat],
                    description=f"{seat}号桨位设备离线",
                    suggestion=f"请检查{seat}号桨位传感器连接状态"
                )
                anomalies.append(anomaly)
                self._anomaly_history.append(anomaly)
        
        return anomalies

    def get_raw_data(self, seat: int, limit: int = 100) -> List[TelemetryData]:
        with self._lock:
            if seat not in self._raw_data:
                return []
            return list(self._raw_data[seat])[-limit:]

    def get_device_info(self) -> Dict[int, Dict]:
        with self._lock:
            current_time = int(time.time() * 1000)
            thresholds = self._get_thresholds()
            offline_threshold = thresholds["offline_threshold_ms"]
            result = {}
            for seat, device_id in self._seat_device_map.items():
                last_seen = self._device_last_seen.get(device_id, 0)
                is_online = current_time - last_seen < offline_threshold
                result[seat] = {
                    "device_id": device_id,
                    "last_seen": last_seen,
                    "is_online": is_online,
                    "offline_duration_ms": max(0, current_time - last_seen) if not is_online else 0
                }
            return result

    def add_anomaly(self, anomaly: AnomalyRecord) -> None:
        with self._lock:
            self._anomaly_history.append(anomaly)
            
            current_time = int(time.time() * 1000)
            if current_time - self._last_anomaly_time < 3000:
                self._consecutive_anomaly_count += 1
            else:
                self._consecutive_anomaly_count = 1
            self._last_anomaly_time = current_time
            
            if anomaly.anomaly_type not in self._anomaly_start_times:
                self._anomaly_start_times[anomaly.anomaly_type] = current_time

    def get_anomalies(self, start_time: Optional[int] = None,
                     anomaly_types: Optional[List[AnomalyType]] = None,
                     limit: int = 100) -> List[AnomalyRecord]:
        with self._lock:
            result = list(self._anomaly_history)
            if start_time:
                result = [a for a in result if a.timestamp >= start_time]
            if anomaly_types:
                result = [a for a in result if a.anomaly_type in anomaly_types]
            return result[-limit:]

    def get_consecutive_anomaly_count(self) -> int:
        with self._lock:
            current_time = int(time.time() * 1000)
            if current_time - self._last_anomaly_time > 5000:
                self._consecutive_anomaly_count = 0
            return self._consecutive_anomaly_count

    def reset_consecutive_anomaly_count(self) -> None:
        with self._lock:
            self._consecutive_anomaly_count = 0

    def add_sync_rate(self, sync_rate: SyncRateResult) -> None:
        with self._lock:
            self._sync_rate_history.append(sync_rate)
            if len(self._sync_rate_history) > 1000:
                self._sync_rate_history = self._sync_rate_history[-1000:]

    def get_sync_rate_history(self, start_time: Optional[int] = None,
                             limit: int = 100) -> List[SyncRateResult]:
        with self._lock:
            result = list(self._sync_rate_history)
            if start_time:
                result = [s for s in result if s.timestamp >= start_time]
            return result[-limit:]

    def get_current_state(self) -> Dict:
        with self._lock:
            duration_ms = int(time.time() * 1000) - self._state_start_time
            return {
                "state": self._current_state,
                "start_time": self._state_start_time,
                "duration_seconds": duration_ms // 1000,
                "current_anomalies": (
                    self._current_state_record.anomalies 
                    if self._current_state_record else []
                )
            }

    def set_state(self, state: TrainingState, reason: str = "") -> Dict:
        with self._lock:
            current_time = int(time.time() * 1000)
            previous = self._current_state
            
            if self._current_state_record:
                self._current_state_record.end_time = current_time
                self._current_state_record.duration_seconds = (
                    current_time - self._current_state_record.start_time
                ) // 1000
            
            new_record = TrainingStateRecord(
                state=state,
                start_time=current_time
            )
            self._state_history.append(new_record)
            self._current_state_record = new_record
            self._current_state = state
            self._state_start_time = current_time
            
            return {
                "previous_state": previous,
                "current_state": state,
                "transitioned": previous != state,
                "reason": reason,
                "timestamp": current_time
            }

    def get_state_history(self) -> List[Dict]:
        with self._lock:
            result = []
            for record in self._state_history:
                item = {
                    "state": record.state,
                    "start_time": record.start_time,
                    "end_time": record.end_time,
                    "duration_seconds": record.duration_seconds,
                    "anomaly_count": len(record.anomalies),
                    "suggestions": record.suggestions
                }
                result.append(item)
            return result

    def set_phase(self, phase: TrainingPhase) -> None:
        with self._lock:
            self._current_phase = phase
            self._phase_start_times[phase] = int(time.time() * 1000)

    def get_current_phase(self) -> TrainingPhase:
        with self._lock:
            return self._current_phase

    def get_phase_start_time(self, phase: TrainingPhase) -> Optional[int]:
        with self._lock:
            return self._phase_start_times.get(phase)

    def add_state_anomaly(self, anomaly: AnomalyRecord) -> None:
        with self._lock:
            if self._current_state_record:
                self._current_state_record.anomalies.append(anomaly)

    def add_state_suggestion(self, suggestion: str) -> None:
        with self._lock:
            if self._current_state_record:
                self._current_state_record.suggestions.append(suggestion)

    def record_strategy_application(self, strategy_id: str) -> None:
        with self._lock:
            self._strategy_application_times.append((int(time.time() * 1000), strategy_id))

    def get_strategy_application_times(self) -> List[Tuple[int, str]]:
        with self._lock:
            return list(self._strategy_application_times)

    def get_anomaly_durations(self) -> Dict[AnomalyType, List[Tuple[int, int]]]:
        with self._lock:
            durations: Dict[AnomalyType, List[Tuple[int, int]]] = {}
            active_anomalies: Dict[AnomalyType, int] = {}
            
            for anomaly in sorted(self._anomaly_history, key=lambda a: a.timestamp):
                atype = anomaly.anomaly_type
                if atype not in active_anomalies:
                    active_anomalies[atype] = anomaly.timestamp
                
                recent = [a for a in self._anomaly_history 
                         if a.anomaly_type == atype 
                         and 0 <= anomaly.timestamp - a.timestamp <= 3000]
                
                if len(recent) == 0:
                    if atype in active_anomalies:
                        if atype not in durations:
                            durations[atype] = []
                        durations[atype].append((active_anomalies[atype], anomaly.timestamp))
                        del active_anomalies[atype]
            
            for atype, start_time in active_anomalies.items():
                if atype not in durations:
                    durations[atype] = []
                durations[atype].append((start_time, int(time.time() * 1000)))
            
            return durations

    def clear(self) -> None:
        with self._lock:
            self._raw_data = {}
            self._aligned_data = deque(maxlen=Config.MAX_HISTORY_SIZE)
            self._device_last_seen = {}
            self._seat_device_map = {}
            self._device_seat_map = {}
            self._anomaly_history = []
            self._sync_rate_history = []
            self._alignment_buffer = {}
            self._last_alignment_time = 0
            self._time_window_index = {}
            self._window_start_times = []
            self._consecutive_anomaly_count = 0
            self._last_anomaly_time = 0

    def clear_all(self) -> None:
        self.clear()


StoreType = Union[SessionDataStore, DataStore]


class SessionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._sessions: Dict[str, Tuple[TrainingSession, SessionDataStore]] = {}
        self._strategies: Dict[str, Tuple[CoachStrategyConfig, StrategyConfigResponse]] = {}
        self._default_store = DataStore()

    def create_session(self, team_id: str, boat_id: str, 
                      session_name: Optional[str] = None,
                      seat_positions: Optional[List[int]] = None,
                      strategy_id: Optional[str] = None) -> TrainingSession:
        with self._lock:
            session_id = str(uuid.uuid4())
            current_time = int(time.time() * 1000)
            
            strategy = None
            if strategy_id and strategy_id in self._strategies:
                strategy = self._strategies[strategy_id][0]
            
            session = TrainingSession(
                session_id=session_id,
                team_id=team_id,
                boat_id=boat_id,
                session_name=session_name,
                status=SessionStatus.ACTIVE,
                created_at=current_time,
                started_at=current_time,
                seat_positions=seat_positions or [1, 2, 3, 4],
                strategy_id=strategy_id
            )
            
            store = SessionDataStore(session_id, strategy)
            self._sessions[session_id] = (session, store)
            
            return session

    def get_session(self, session_id: str) -> Optional[TrainingSession]:
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id][0]
            return None

    def get_session_store(self, session_id: Optional[str]) -> StoreType:
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id][1]
            return self._default_store

    def get_session_store_or_none(self, session_id: Optional[str]) -> Optional[SessionDataStore]:
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id][1]
            return None

    def list_sessions(self, team_id: Optional[str] = None, 
                     status: Optional[SessionStatus] = None) -> List[TrainingSession]:
        with self._lock:
            result = []
            for session, _ in self._sessions.values():
                if team_id and session.team_id != team_id:
                    continue
                if status and session.status != status:
                    continue
                result.append(session)
            return sorted(result, key=lambda s: s.created_at, reverse=True)

    def update_session_status(self, session_id: str, status: SessionStatus) -> Optional[TrainingSession]:
        with self._lock:
            if session_id not in self._sessions:
                return None
            session, store = self._sessions[session_id]
            session.status = status
            if status == SessionStatus.COMPLETED:
                session.ended_at = int(time.time() * 1000)
            self._sessions[session_id] = (session, store)
            return session

    def update_session_phase(self, session_id: str, phase: TrainingPhase) -> Optional[TrainingSession]:
        with self._lock:
            if session_id not in self._sessions:
                return None
            session, store = self._sessions[session_id]
            session.current_phase = phase
            store.set_phase(phase)
            self._sessions[session_id] = (session, store)
            return session

    def update_session_state(self, session_id: str, state: TrainingState, 
                           reason: str = "") -> Optional[Dict]:
        with self._lock:
            if session_id not in self._sessions:
                return None
            session, store = self._sessions[session_id]
            result = store.set_state(state, reason)
            session.current_state = state
            self._sessions[session_id] = (session, store)
            return result

    def end_session(self, session_id: str) -> Optional[TrainingSession]:
        with self._lock:
            if session_id not in self._sessions:
                return None
            session, store = self._sessions[session_id]
            session.status = SessionStatus.COMPLETED
            session.ended_at = int(time.time() * 1000)
            store.set_state(TrainingState.TRAINING_ENDED, "训练结束")
            self._sessions[session_id] = (session, store)
            return session

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def create_strategy(self, config: CoachStrategyConfig) -> StrategyConfigResponse:
        with self._lock:
            strategy_id = str(uuid.uuid4())
            current_time = int(time.time() * 1000)
            
            response = StrategyConfigResponse(
                strategy_id=strategy_id,
                boat_id=config.boat_id,
                config=config,
                created_at=current_time,
                updated_at=current_time
            )
            
            self._strategies[strategy_id] = (config, response)
            return response

    def update_strategy(self, strategy_id: str, 
                       config: CoachStrategyConfig) -> Optional[StrategyConfigResponse]:
        with self._lock:
            if strategy_id not in self._strategies:
                return None
            
            current_time = int(time.time() * 1000)
            response = StrategyConfigResponse(
                strategy_id=strategy_id,
                boat_id=config.boat_id,
                config=config,
                created_at=self._strategies[strategy_id][1].created_at,
                updated_at=current_time
            )
            
            self._strategies[strategy_id] = (config, response)
            
            for sid, (session, store) in self._sessions.items():
                if session.strategy_id == strategy_id:
                    store.strategy = config
                    store.record_strategy_application(strategy_id)
                    self._sessions[sid] = (session, store)
            
            return response

    def get_strategy(self, strategy_id: str) -> Optional[StrategyConfigResponse]:
        with self._lock:
            if strategy_id in self._strategies:
                return self._strategies[strategy_id][1]
            return None

    def list_strategies(self, boat_id: Optional[str] = None) -> List[StrategyConfigResponse]:
        with self._lock:
            result = []
            for _, response in self._strategies.values():
                if boat_id and response.boat_id != boat_id:
                    continue
                result.append(response)
            return sorted(result, key=lambda s: s.updated_at, reverse=True)

    def apply_strategy_to_session(self, strategy_id: str, session_id: str) -> bool:
        with self._lock:
            if strategy_id not in self._strategies or session_id not in self._sessions:
                return False
            
            config = self._strategies[strategy_id][0]
            session, store = self._sessions[session_id]
            session.strategy_id = strategy_id
            store.strategy = config
            store.record_strategy_application(strategy_id)
            self._sessions[session_id] = (session, store)
            return True

    def get_default_store(self) -> DataStore:
        return self._default_store
