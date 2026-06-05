import time
import threading
from typing import List, Optional, Dict, Callable
from collections import deque

from .config import Config
from .storage import DataStore
from .analyzer import StrokeAnalyzer
from .models import (
    TrainingState, TrainingStateRecord,
    AnomalyRecord, AnomalyType, SyncRateResult
)


class StateManager:
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
        self.current_state: TrainingState = TrainingState.NORMAL_TRAINING
        self.state_history: List[TrainingStateRecord] = []
        self.current_state_record: Optional[TrainingStateRecord] = None
        self._state_start_time: int = int(time.time() * 1000)
        self._pending_suggestions: List[str] = []
        self._consecutive_warnings: int = 0
        self._last_sync_rates: deque = deque(maxlen=20)
        self._notification_callbacks: List[Callable] = []
        self._state_transition_config = Config.STATE_TRANSITION_CONFIG
        
        self._start_new_state(TrainingState.NORMAL_TRAINING)

    def _start_new_state(self, state: TrainingState) -> None:
        current_time = int(time.time() * 1000)
        
        if self.current_state_record:
            self.current_state_record.end_time = current_time
            self.current_state_record.duration_seconds = (
                current_time - self.current_state_record.start_time
            ) // 1000
        
        new_record = TrainingStateRecord(
            state=state,
            start_time=current_time
        )
        
        self.state_history.append(new_record)
        self.current_state_record = new_record
        self.current_state = state
        self._state_start_time = current_time
        self._consecutive_warnings = 0

    def _get_state_duration_ms(self) -> int:
        return int(time.time() * 1000) - self._state_start_time

    def update(self, sync_rate: Optional[SyncRateResult], 
               anomalies: List[AnomalyRecord]) -> Dict:
        with self._lock:
            if sync_rate:
                self._last_sync_rates.append(sync_rate.overall_sync_rate)
            
            if anomalies:
                for anomaly in anomalies:
                    if self.current_state_record:
                        self.current_state_record.anomalies.append(anomaly)
                    self._pending_suggestions.append(anomaly.suggestion)

            result = self._evaluate_state_transition(sync_rate, anomalies)
            
            self._notify_callbacks({
                "state": self.current_state,
                "anomalies": anomalies,
                "sync_rate": sync_rate,
                "suggestions": self._pending_suggestions
            })
            
            return result

    def _evaluate_state_transition(self, sync_rate: Optional[SyncRateResult],
                                   anomalies: List[AnomalyRecord]) -> Dict:
        threshold = Config.ANOMALY_THRESHOLDS["sync_score_threshold"]
        current_time = int(time.time() * 1000)
        duration_ms = self._get_state_duration_ms()
        duration_s = duration_ms / 1000

        transition_result = {
            "previous_state": self.current_state,
            "current_state": self.current_state,
            "transitioned": False,
            "reason": "",
            "suggestions": []
        }

        avg_sync = (sum(self._last_sync_rates) / len(self._last_sync_rates) 
                   if self._last_sync_rates else 1.0)
        
        has_critical_anomalies = any(
            a.severity > 0.7 for a in anomalies
        )
        
        has_warning_anomalies = any(
            a.severity > 0.4 for a in anomalies
        )

        if self.current_state == TrainingState.NORMAL_TRAINING:
            if has_critical_anomalies or (avg_sync < threshold and duration_s > 5):
                self._consecutive_warnings += 1
                if self._consecutive_warnings >= 3 or has_critical_anomalies:
                    self._start_new_state(TrainingState.POSTURE_WARNING)
                    transition_result.update({
                        "current_state": TrainingState.POSTURE_WARNING,
                        "transitioned": True,
                        "reason": "检测到严重划姿问题或持续低同步率",
                        "suggestions": self._generate_warning_suggestions(anomalies)
                    })
                    self._add_suggestions_to_current(transition_result["suggestions"])

        elif self.current_state == TrainingState.POSTURE_WARNING:
            warning_duration = self._state_transition_config["warning_duration"]
            
            if avg_sync >= threshold and not has_warning_anomalies and duration_s > warning_duration:
                self._start_new_state(TrainingState.NORMAL_TRAINING)
                transition_result.update({
                    "current_state": TrainingState.NORMAL_TRAINING,
                    "transitioned": True,
                    "reason": "划姿恢复正常，同步率达标",
                    "suggestions": ["继续保持良好的划姿和节奏"]
                })
            elif duration_s > warning_duration and has_warning_anomalies:
                self._start_new_state(TrainingState.TECHNICAL_ADJUSTMENT)
                transition_result.update({
                    "current_state": TrainingState.TECHNICAL_ADJUSTMENT,
                    "transitioned": True,
                    "reason": "警告期内问题未改善，需要技术调整",
                    "suggestions": self._generate_adjustment_suggestions(anomalies)
                })
                self._add_suggestions_to_current(transition_result["suggestions"])

        elif self.current_state == TrainingState.TECHNICAL_ADJUSTMENT:
            adj_duration = self._state_transition_config["adjustment_duration"]
            
            if avg_sync >= threshold * 0.9 and not has_critical_anomalies and duration_s > adj_duration:
                self._start_new_state(TrainingState.NORMAL_TRAINING)
                transition_result.update({
                    "current_state": TrainingState.NORMAL_TRAINING,
                    "transitioned": True,
                    "reason": "技术调整见效，恢复正常训练",
                    "suggestions": ["技术调整完成，继续保持"]
                })
            elif duration_s > adj_duration * 2:
                self._start_new_state(TrainingState.REST_RECOVERY)
                transition_result.update({
                    "current_state": TrainingState.REST_RECOVERY,
                    "transitioned": True,
                    "reason": "长时间技术调整未见明显改善，建议休息",
                    "suggestions": ["建议休息2-3分钟，放松肌肉后再尝试"]
                })
                self._add_suggestions_to_current(transition_result["suggestions"])

        elif self.current_state == TrainingState.REST_RECOVERY:
            rest_duration = self._state_transition_config["rest_duration"]
            
            if duration_s > rest_duration:
                self._start_new_state(TrainingState.NORMAL_TRAINING)
                transition_result.update({
                    "current_state": TrainingState.NORMAL_TRAINING,
                    "transitioned": True,
                    "reason": "休息恢复完成，可继续训练",
                    "suggestions": ["休息结束，建议从轻强度开始恢复训练"]
                })

        if not transition_result["suggestions"] and self._pending_suggestions:
            transition_result["suggestions"] = list(self._pending_suggestions)
            self._pending_suggestions = []

        return transition_result

    def _generate_warning_suggestions(self, anomalies: List[AnomalyRecord]) -> List[str]:
        suggestions = []
        for a in anomalies:
            if a.anomaly_type == AnomalyType.STROKE_RATE_MISMATCH:
                suggestions.append("⚠️ 注意桨频同步，观察前后队员的划桨节奏")
            elif a.anomaly_type == AnomalyType.ENTRY_ANGLE_DEVIATION:
                suggestions.append("⚠️ 调整入水角度，保持与其他队员一致")
            elif a.anomaly_type == AnomalyType.FORCE_IMBALANCE:
                suggestions.append("⚠️ 注意力量输出均衡，避免单侧用力过猛")
            elif a.anomaly_type == AnomalyType.RHYTHM_DISORDER:
                suggestions.append("⚠️ 稳定划桨节奏，保持入水出水时机一致")
        return suggestions

    def _generate_adjustment_suggestions(self, anomalies: List[AnomalyRecord]) -> List[str]:
        suggestions = ["🔧 进入技术调整阶段，请集中注意力改善以下问题:"]
        
        anomaly_types = set(a.anomaly_type for a in anomalies)
        
        if AnomalyType.STROKE_RATE_MISMATCH in anomaly_types:
            suggestions.append("• 降低桨频，先保证动作同步再考虑速度")
            suggestions.append("• 听教练口令，统一划桨节奏")
        
        if AnomalyType.ENTRY_ANGLE_DEVIATION in anomaly_types:
            suggestions.append("• 注意转肩和提桨动作，保持入水角度一致")
            suggestions.append("• 观察镜面或队友动作，调整入水姿势")
        
        if AnomalyType.FORCE_IMBALANCE in anomaly_types:
            suggestions.append("• 保持拉桨力度均匀，避免爆发力过猛")
            suggestions.append("• 注意蹬腿-拉臂-回桨的力量传导")
        
        if AnomalyType.RHYTHM_DISORDER in anomaly_types:
            suggestions.append("• 心里默数节拍，保持稳定的划桨频率")
            suggestions.append("• 入水要轻，拉桨要稳，出水要快")
        
        return suggestions

    def _add_suggestions_to_current(self, suggestions: List[str]) -> None:
        if self.current_state_record:
            self.current_state_record.suggestions.extend(suggestions)

    def end_training(self) -> Dict:
        with self._lock:
            self._start_new_state(TrainingState.TRAINING_ENDED)
            
            stats = self._calculate_training_summary()
            return {
                "state": TrainingState.TRAINING_ENDED,
                "summary": stats,
                "suggestions": self._generate_final_suggestions(stats)
            }

    def _calculate_training_summary(self) -> Dict:
        total_duration = 0
        state_durations = {}
        
        for record in self.state_history:
            if record.end_time:
                duration = (record.end_time - record.start_time) // 1000
            else:
                duration = (int(time.time() * 1000) - record.start_time) // 1000
            
            total_duration += duration
            
            if record.state not in state_durations:
                state_durations[record.state] = 0
            state_durations[record.state] += duration

        all_anomalies = []
        for record in self.state_history:
            all_anomalies.extend(record.anomalies)

        anomaly_counts = {}
        for a in all_anomalies:
            if a.anomaly_type not in anomaly_counts:
                anomaly_counts[a.anomaly_type] = 0
            anomaly_counts[a.anomaly_type] += 1

        return {
            "total_duration_seconds": total_duration,
            "state_durations": state_durations,
            "total_anomalies": len(all_anomalies),
            "anomaly_counts": anomaly_counts,
            "state_history_count": len(self.state_history)
        }

    def _generate_final_suggestions(self, stats: Dict) -> List[str]:
        suggestions = ["📊 训练结束，以下是本次训练的改进建议:"]
        
        anomaly_counts = stats.get("anomaly_counts", {})
        
        if AnomalyType.STROKE_RATE_MISMATCH in anomaly_counts:
            suggestions.append(f"• 桨频不齐共{anomaly_counts[AnomalyType.STROKE_RATE_MISMATCH]}次，建议加强全队节奏训练")
        
        if AnomalyType.ENTRY_ANGLE_DEVIATION in anomaly_counts:
            suggestions.append(f"• 入水角度偏差共{anomaly_counts[AnomalyType.ENTRY_ANGLE_DEVIATION]}次，建议进行专项技术训练")
        
        if AnomalyType.FORCE_IMBALANCE in anomaly_counts:
            suggestions.append(f"• 力量输出不均共{anomaly_counts[AnomalyType.FORCE_IMBALANCE]}次，建议加强力量均衡训练")
        
        if AnomalyType.RHYTHM_DISORDER in anomaly_counts:
            suggestions.append(f"• 节奏混乱共{anomaly_counts[AnomalyType.RHYTHM_DISORDER]}次，建议进行节拍器辅助训练")
        
        if AnomalyType.DEVICE_OFFLINE in anomaly_counts:
            suggestions.append(f"• 设备离线共{anomaly_counts[AnomalyType.DEVICE_OFFLINE]}次，建议训练前检查设备连接")

        if not anomaly_counts:
            suggestions.append("• 本次训练表现优秀，继续保持！")

        return suggestions

    def get_current_state(self) -> Dict:
        with self._lock:
            duration_ms = self._get_state_duration_ms()
            return {
                "state": self.current_state,
                "start_time": self._state_start_time,
                "duration_seconds": duration_ms // 1000,
                "pending_suggestions": list(self._pending_suggestions),
                "current_anomalies": (
                    self.current_state_record.anomalies 
                    if self.current_state_record else []
                )
            }

    def get_state_history(self) -> List[Dict]:
        with self._lock:
            result = []
            for record in self.state_history:
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

    def register_notification_callback(self, callback: Callable) -> None:
        with self._lock:
            self._notification_callbacks.append(callback)

    def _notify_callbacks(self, data: Dict) -> None:
        for callback in self._notification_callbacks:
            try:
                callback(data)
            except Exception:
                pass

    def manual_transition(self, target_state: TrainingState, reason: str = "") -> Dict:
        with self._lock:
            previous = self.current_state
            self._start_new_state(target_state)
            
            return {
                "previous_state": previous,
                "current_state": target_state,
                "transitioned": True,
                "reason": reason or "手动状态切换",
                "suggestions": []
            }

    def reset(self) -> None:
        with self._lock:
            self._initialize()
