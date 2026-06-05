import time
import threading
from typing import Dict, List, Optional, Tuple
from collections import deque
import numpy as np

from .config import Config
from .models import TelemetryData, AlignedDataPoint, AnomalyType, AnomalyRecord


class DataStore:
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
        self._raw_data: Dict[int, deque] = {}
        self._aligned_data: deque = deque(maxlen=Config.MAX_HISTORY_SIZE)
        self._device_last_seen: Dict[str, int] = {}
        self._seat_device_map: Dict[int, str] = {}
        self._device_seat_map: Dict[str, int] = {}
        self._anomaly_history: List[AnomalyRecord] = []
        self._sync_rate_history: List = []
        self._alignment_buffer: Dict[int, List[TelemetryData]] = {}
        self._last_alignment_time: int = 0

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
                self._aligned_data.append(aligned_point)

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
            active = []
            for seat, device_id in self._seat_device_map.items():
                last_seen = self._device_last_seen.get(device_id, 0)
                if current_time - last_seen < Config.DEVICE_OFFLINE_THRESHOLD_MS:
                    active.append(seat)
            return sorted(active)

    def get_offline_devices(self) -> List[Tuple[int, str]]:
        with self._lock:
            current_time = int(time.time() * 1000)
            offline = []
            for seat, device_id in self._seat_device_map.items():
                last_seen = self._device_last_seen.get(device_id, 0)
                if current_time - last_seen >= Config.DEVICE_OFFLINE_THRESHOLD_MS:
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
            result = {}
            for seat, device_id in self._seat_device_map.items():
                last_seen = self._device_last_seen.get(device_id, 0)
                is_online = current_time - last_seen < Config.DEVICE_OFFLINE_THRESHOLD_MS
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

    def add_sync_rate(self, sync_rate) -> None:
        with self._lock:
            self._sync_rate_history.append(sync_rate)
            if len(self._sync_rate_history) > 1000:
                self._sync_rate_history = self._sync_rate_history[-1000:]

    def get_sync_rate_history(self, start_time: Optional[int] = None,
                             limit: int = 100) -> List:
        with self._lock:
            result = list(self._sync_rate_history)
            if start_time:
                result = [s for s in result if s.timestamp >= start_time]
            return result[-limit:]

    def clear_all(self) -> None:
        with self._lock:
            self._initialize()
