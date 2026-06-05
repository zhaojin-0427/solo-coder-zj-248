import time
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from .config import Config
from .models import (
    AlignedDataPoint, AnomalyRecord, AnomalyType,
    SyncRateResult, StrokeStability, CoachStrategyConfig,
    TrainingPhase, PhaseSyncRatePoint, AnomalyDurationStats,
    KeyDesyncSegment, SeatTechnicalDeficiency, TrainingLoadPeak,
    StrategyEffectComparison, TrainingReviewResponse,
    SeatInterventionSuggestion, RealTimeInterventionResponse,
    TrainingState
)
from .session_storage import SessionDataStore, SessionManager, StoreType


class SessionStrokeAnalyzer:
    def __init__(self, session_id: Optional[str] = None):
        self.session_manager = SessionManager()
        self.session_id = session_id
        self.store: StoreType = self.session_manager.get_session_store(session_id)
        self.session_store: Optional[SessionDataStore] = self.session_manager.get_session_store_or_none(session_id)
        
        if self.session_store and self.session_store.strategy:
            self.strategy = self.session_store.strategy
            self.thresholds = self.session_store._get_thresholds()
        else:
            self.strategy = None
            self.thresholds = {
                **Config.ANOMALY_THRESHOLDS,
                "offline_threshold_ms": Config.DEVICE_OFFLINE_THRESHOLD_MS,
                "consecutive_anomaly_threshold": 3,
            }

    def _refresh_strategy(self):
        if self.session_id:
            self.session_store = self.session_manager.get_session_store_or_none(self.session_id)
            if self.session_store:
                self.store = self.session_store
                if self.session_store.strategy:
                    self.strategy = self.session_store.strategy
                    self.thresholds = self.session_store._get_thresholds()

    def calculate_sync_rate(self) -> Optional[SyncRateResult]:
        self._refresh_strategy()
        aligned_by_time = self.store.get_latest_aligned_by_timestamp()
        if not aligned_by_time:
            return None

        latest_timestamp = max(aligned_by_time.keys())
        points = aligned_by_time.get(latest_timestamp, [])
        
        if len(points) < 2:
            return None

        seat_data = {p.seat_position: p for p in points}
        seats = list(seat_data.keys())

        stroke_rates = [seat_data[s].stroke_rate for s in seats]
        entry_angles = [seat_data[s].entry_angle for s in seats]
        pull_forces = [seat_data[s].pull_force for s in seats]

        stroke_rate_sync = self._calc_coefficient_of_variation(stroke_rates)
        angle_sync = self._calc_coefficient_of_variation(entry_angles)
        force_sync = self._calc_coefficient_of_variation(pull_forces)

        stroke_rate_sync_norm = max(0, 1 - stroke_rate_sync)
        angle_sync_norm = max(0, 1 - angle_sync / 10)
        force_sync_norm = max(0, 1 - force_sync)

        if self.strategy:
            overall_sync = (
                stroke_rate_sync_norm * 0.35 + 
                angle_sync_norm * 0.25 + 
                force_sync_norm * 0.25 +
                (1 - min(1, stroke_rate_sync / self.thresholds["rhythm_cv_threshold"])) * 0.15
            )
        else:
            overall_sync = (
                stroke_rate_sync_norm * 0.4 + 
                angle_sync_norm * 0.3 + 
                force_sync_norm * 0.3
            )

        seat_sync_rates = {}
        avg_rate = np.mean(stroke_rates)
        avg_angle = np.mean(entry_angles)
        avg_force = np.mean(pull_forces)

        for s in seats:
            rate_deviation = abs(seat_data[s].stroke_rate - avg_rate) / max(avg_rate, 1)
            angle_deviation = abs(seat_data[s].entry_angle - avg_angle) / max(abs(avg_angle), 1)
            force_deviation = abs(seat_data[s].pull_force - avg_force) / max(avg_force, 1)
            
            seat_sync = 1 - (rate_deviation * 0.4 + angle_deviation * 0.3 + force_deviation * 0.3)
            seat_sync_rates[s] = max(0, min(1, seat_sync))

        result = SyncRateResult(
            timestamp=latest_timestamp,
            overall_sync_rate=overall_sync,
            seat_sync_rates=seat_sync_rates,
            stroke_rate_sync=stroke_rate_sync_norm,
            angle_sync=angle_sync_norm,
            force_sync=force_sync_norm
        )

        self.store.add_sync_rate(result)
        return result

    def _calc_coefficient_of_variation(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        arr = np.array(values)
        mean = np.mean(arr)
        if mean == 0:
            return 0.0
        return np.std(arr) / abs(mean)

    def detect_anomalies(self) -> List[AnomalyRecord]:
        self._refresh_strategy()
        anomalies = []
        
        offline_anomalies = self.store.check_device_offline()
        anomalies.extend(offline_anomalies)

        aligned_data = self.store.get_aligned_data()
        if not aligned_data:
            return anomalies

        recent_data = aligned_data[-50:] if len(aligned_data) > 50 else aligned_data
        
        by_seat: Dict[int, List[AlignedDataPoint]] = {}
        for p in recent_data:
            if p.seat_position not in by_seat:
                by_seat[p.seat_position] = []
            by_seat[p.seat_position].append(p)

        if len(by_seat) < 2:
            return anomalies

        stroke_rate_anomalies = self._detect_stroke_rate_mismatch(by_seat)
        anomalies.extend(stroke_rate_anomalies)

        angle_anomalies = self._detect_entry_angle_deviation(by_seat)
        anomalies.extend(angle_anomalies)

        force_anomalies = self._detect_force_imbalance(by_seat)
        anomalies.extend(force_anomalies)

        rhythm_anomalies = self._detect_rhythm_disorder(by_seat)
        anomalies.extend(rhythm_anomalies)

        for anomaly in anomalies:
            if anomaly.anomaly_type != AnomalyType.DEVICE_OFFLINE:
                self.store.add_anomaly(anomaly)
                if self.session_store:
                    self.session_store.add_state_anomaly(anomaly)

        return anomalies

    def _detect_stroke_rate_mismatch(self, by_seat: Dict[int, List[AlignedDataPoint]]) -> List[AnomalyRecord]:
        anomalies = []
        threshold = self.thresholds["stroke_rate_deviation"]
        
        seat_avg_rates = {}
        for seat, points in by_seat.items():
            rates = [p.stroke_rate for p in points if p.stroke_rate > 0]
            if rates:
                seat_avg_rates[seat] = np.mean(rates)
        
        if len(seat_avg_rates) < 2:
            return anomalies
        
        if self.strategy:
            target_min = self.strategy.stroke_rate_target_min
            target_max = self.strategy.stroke_rate_target_max
            target_center = (target_min + target_max) / 2
        else:
            target_center = np.mean(list(seat_avg_rates.values()))
        
        overall_mean = np.mean(list(seat_avg_rates.values()))
        
        problem_seats = []
        deviations = {}
        for seat, avg_rate in seat_avg_rates.items():
            dev_from_target = abs(avg_rate - target_center)
            dev_from_mean = abs(avg_rate - overall_mean)
            dev = max(dev_from_target, dev_from_mean)
            deviations[seat] = dev
            if dev > threshold:
                problem_seats.append(seat)
        
        if problem_seats:
            max_dev = max(deviations.values())
            severity = min(1.0, max_dev / (threshold * 3))
            current_time = int(time.time() * 1000)
            
            desc = f"桨频不齐: {', '.join([f'{s}号' for s in problem_seats])}桨位与目标值偏差超过{threshold:.1f}桨/分钟"
            suggestion = self._generate_stroke_rate_suggestion(seat_avg_rates, target_center, problem_seats)
            
            anomaly = AnomalyRecord(
                anomaly_type=AnomalyType.STROKE_RATE_MISMATCH,
                severity=severity,
                timestamp=current_time,
                seat_positions=problem_seats,
                description=desc,
                suggestion=suggestion
            )
            anomalies.append(anomaly)
        
        return anomalies

    def _generate_stroke_rate_suggestion(self, seat_rates: Dict[int, float], 
                                       target_center: float, 
                                       problem_seats: List[int]) -> str:
        slow = [s for s in problem_seats if seat_rates[s] < target_center]
        fast = [s for s in problem_seats if seat_rates[s] > target_center]
        
        suggestions = []
        if slow:
            suggestions.append(f"请{', '.join([f'{s}号' for s in slow])}桨位加快划桨频率")
        if fast:
            suggestions.append(f"请{', '.join([f'{s}号' for s in fast])}桨位降低划桨频率")
        
        if self.strategy:
            suggestions.append(f"全队目标桨频区间: {self.strategy.stroke_rate_target_min:.0f}-{self.strategy.stroke_rate_target_max:.0f}桨/分钟")
        else:
            suggestions.append(f"全队目标桨频: {target_center:.1f}桨/分钟")
        
        return "; ".join(suggestions)

    def _detect_entry_angle_deviation(self, by_seat: Dict[int, List[AlignedDataPoint]]) -> List[AnomalyRecord]:
        anomalies = []
        threshold = self.thresholds["entry_angle_deviation"]
        
        seat_avg_angles = {}
        for seat, points in by_seat.items():
            angles = [p.entry_angle for p in points]
            if angles:
                seat_avg_angles[seat] = np.mean(angles)
        
        if len(seat_avg_angles) < 2:
            return anomalies
        
        overall_mean = np.mean(list(seat_avg_angles.values()))
        
        problem_seats = []
        deviations = {}
        for seat, avg_angle in seat_avg_angles.items():
            dev = abs(avg_angle - overall_mean)
            deviations[seat] = dev
            if dev > threshold:
                problem_seats.append(seat)
        
        if problem_seats:
            max_dev = max(deviations.values())
            severity = min(1.0, max_dev / (threshold * 3))
            current_time = int(time.time() * 1000)
            
            desc = f"入水角度偏差: {', '.join([f'{s}号' for s in problem_seats])}桨位与平均值偏差超过{threshold:.1f}度"
            suggestion = self._generate_angle_suggestion(seat_avg_angles, overall_mean, problem_seats)
            
            anomaly = AnomalyRecord(
                anomaly_type=AnomalyType.ENTRY_ANGLE_DEVIATION,
                severity=severity,
                timestamp=current_time,
                seat_positions=problem_seats,
                description=desc,
                suggestion=suggestion
            )
            anomalies.append(anomaly)
        
        return anomalies

    def _generate_angle_suggestion(self, seat_angles: Dict[int, float],
                                  overall_mean: float,
                                  problem_seats: List[int]) -> str:
        low = [s for s in problem_seats if seat_angles[s] < overall_mean]
        high = [s for s in problem_seats if seat_angles[s] > overall_mean]
        
        suggestions = []
        if low:
            suggestions.append(f"请{', '.join([f'{s}号' for s in low])}桨位增大入水角度")
        if high:
            suggestions.append(f"请{', '.join([f'{s}号' for s in high])}桨位减小入水角度")
        
        if self.strategy:
            suggestions.append(f"入水角度容忍区间: ±{self.strategy.entry_angle_tolerance:.1f}度")
        suggestions.append(f"全队平均入水角度: {overall_mean:.1f}度")
        
        return "; ".join(suggestions)

    def _detect_force_imbalance(self, by_seat: Dict[int, List[AlignedDataPoint]]) -> List[AnomalyRecord]:
        anomalies = []
        threshold = self.thresholds["force_imbalance_ratio"]
        
        seat_avg_forces = {}
        for seat, points in by_seat.items():
            forces = [p.pull_force for p in points if p.pull_force > 0]
            if forces:
                seat_avg_forces[seat] = np.mean(forces)
        
        if len(seat_avg_forces) < 2:
            return anomalies
        
        overall_mean = np.mean(list(seat_avg_forces.values()))
        
        problem_seats = []
        deviations = {}
        for seat, avg_force in seat_avg_forces.items():
            if overall_mean > 0:
                dev_ratio = abs(avg_force - overall_mean) / overall_mean
            else:
                dev_ratio = 0
            deviations[seat] = dev_ratio
            if dev_ratio > threshold:
                problem_seats.append(seat)
        
        if problem_seats:
            max_dev = max(deviations.values())
            severity = min(1.0, max_dev / (threshold * 3))
            current_time = int(time.time() * 1000)
            
            weight_info = f" (权重: {self.strategy.force_balance_weight:.1f})" if self.strategy else ""
            desc = f"力量输出不均{weight_info}: {', '.join([f'{s}号' for s in problem_seats])}桨位力量偏差超过{threshold*100:.0f}%"
            suggestion = self._generate_force_suggestion(seat_avg_forces, overall_mean, problem_seats)
            
            anomaly = AnomalyRecord(
                anomaly_type=AnomalyType.FORCE_IMBALANCE,
                severity=severity,
                timestamp=current_time,
                seat_positions=problem_seats,
                description=desc,
                suggestion=suggestion
            )
            anomalies.append(anomaly)
        
        return anomalies

    def _generate_force_suggestion(self, seat_forces: Dict[int, float],
                                  overall_mean: float,
                                  problem_seats: List[int]) -> str:
        weak = [s for s in problem_seats if seat_forces[s] < overall_mean]
        strong = [s for s in problem_seats if seat_forces[s] > overall_mean]
        
        suggestions = []
        if weak:
            suggestions.append(f"请{', '.join([f'{s}号' for s in weak])}桨位增加拉桨力量")
        if strong:
            suggestions.append(f"请{', '.join([f'{s}号' for s in strong])}桨位控制拉桨力量")
        suggestions.append(f"全队平均力量: {overall_mean:.1f}N")
        
        return "; ".join(suggestions)

    def _detect_rhythm_disorder(self, by_seat: Dict[int, List[AlignedDataPoint]]) -> List[AnomalyRecord]:
        anomalies = []
        threshold = self.thresholds["rhythm_cv_threshold"]
        
        problem_seats = []
        cv_values = {}
        
        for seat, points in by_seat.items():
            if len(points) < 10:
                continue
            
            stroke_rates = [p.stroke_rate for p in points if p.stroke_rate > 0]
            
            if len(stroke_rates) < 5:
                continue
            
            rate_cv = self._calc_coefficient_of_variation(stroke_rates)
            cv_values[seat] = rate_cv
            
            if rate_cv > threshold:
                problem_seats.append(seat)
        
        if problem_seats:
            max_cv = max(cv_values.values())
            severity = min(1.0, max_cv / (threshold * 2))
            current_time = int(time.time() * 1000)
            
            threshold_info = f" (阈值: {self.strategy.rhythm_stability_threshold:.3f})" if self.strategy else ""
            desc = f"节奏混乱{threshold_info}: {', '.join([f'{s}号' for s in problem_seats])}桨位划桨节奏变异系数超过{threshold*100:.0f}%"
            suggestion = "请保持稳定的划桨节奏，注意入水和出水时机的一致性"
            
            anomaly = AnomalyRecord(
                anomaly_type=AnomalyType.RHYTHM_DISORDER,
                severity=severity,
                timestamp=current_time,
                seat_positions=problem_seats,
                description=desc,
                suggestion=suggestion
            )
            anomalies.append(anomaly)
        
        return anomalies

    def calculate_stability_ranking(self, start_time: Optional[int] = None,
                                    end_time: Optional[int] = None) -> List[StrokeStability]:
        self._refresh_strategy()
        aligned_data = self.store.get_aligned_data(start_time, end_time)
        if not aligned_data:
            return []

        by_seat: Dict[int, List[AlignedDataPoint]] = {}
        for p in aligned_data:
            if p.seat_position not in by_seat:
                by_seat[p.seat_position] = []
            by_seat[p.seat_position].append(p)

        device_info = self.store.get_device_info()
        anomalies = self.store.get_anomalies(start_time)

        rankings = []
        for seat, points in by_seat.items():
            if len(points) < 5:
                continue

            stroke_rates = [p.stroke_rate for p in points if p.stroke_rate > 0]
            forces = [p.pull_force for p in points if p.pull_force > 0]
            angles = [p.entry_angle for p in points]

            rate_cv = self._calc_coefficient_of_variation(stroke_rates) if stroke_rates else 1.0
            force_cv = self._calc_coefficient_of_variation(forces) if forces else 1.0
            angle_cv = self._calc_coefficient_of_variation(angles) if angles else 1.0

            seat_anomalies = [a for a in anomalies if seat in a.seat_positions]
            anomaly_count = len(seat_anomalies)

            force_weight = self.strategy.force_balance_weight if self.strategy else 1.0
            rhythm_threshold = self.thresholds["rhythm_cv_threshold"]

            stability = (
                (1 - min(1, rate_cv * 2 / rhythm_threshold)) * 0.35 +
                (1 - min(1, force_cv * 2 * force_weight)) * 0.35 +
                (1 - min(1, angle_cv * 2)) * 0.15 +
                max(0, 1 - anomaly_count * 0.1) * 0.15
            )

            stability = max(0, min(1, stability))

            ranking = StrokeStability(
                seat_position=seat,
                device_id=device_info.get(seat, {}).get("device_id", "unknown"),
                stability_score=stability,
                stroke_rate_cv=rate_cv,
                force_cv=force_cv,
                angle_cv=angle_cv,
                anomaly_count=anomaly_count
            )
            rankings.append(ranking)

        rankings.sort(key=lambda x: x.stability_score, reverse=True)
        return rankings

    def get_sync_rate_trend(self, start_time: Optional[int] = None,
                           limit: int = 100) -> List[SyncRateResult]:
        return self.store.get_sync_rate_history(start_time, limit)

    def calculate_training_load(self, start_time: Optional[int] = None,
                               end_time: Optional[int] = None) -> Dict:
        aligned_data = self.store.get_aligned_data(start_time, end_time)
        if not aligned_data:
            return {"overall_load": 0, "seat_loads": {}}

        by_seat: Dict[int, List[AlignedDataPoint]] = {}
        for p in aligned_data:
            if p.seat_position not in by_seat:
                by_seat[p.seat_position] = []
            by_seat[p.seat_position].append(p)

        seat_loads = {}
        for seat, points in by_seat.items():
            if len(points) < 2:
                continue
            
            time_span = (points[-1].timestamp - points[0].timestamp) / 1000
            if time_span <= 0:
                continue
            
            avg_stroke_rate = np.mean([p.stroke_rate for p in points if p.stroke_rate > 0])
            avg_force = np.mean([p.pull_force for p in points if p.pull_force > 0])
            
            force_weight = self.strategy.force_balance_weight if self.strategy else 1.0
            load = (avg_stroke_rate * avg_force * force_weight * time_span) / 1000
            seat_loads[seat] = {
                "total_strokes": len(points),
                "duration_seconds": time_span,
                "avg_stroke_rate": avg_stroke_rate,
                "avg_force": avg_force,
                "load_score": load
            }

        overall_load = sum([v["load_score"] for v in seat_loads.values()])

        return {
            "overall_load": overall_load,
            "seat_loads": seat_loads,
            "total_duration_seconds": (aligned_data[-1].timestamp - aligned_data[0].timestamp) / 1000,
            "data_points": len(aligned_data)
        }

    def calculate_improvement_trend(self) -> Dict:
        sync_history = self.store.get_sync_rate_history(limit=200)
        anomaly_history = self.store.get_anomalies(limit=200)

        if len(sync_history) < 10:
            return {
                "sync_improvement": 0,
                "anomaly_trend": "insufficient_data",
                "overall_improvement": 0
            }

        mid = len(sync_history) // 2
        first_half = sync_history[:mid]
        second_half = sync_history[mid:]

        first_avg = np.mean([s.overall_sync_rate for s in first_half])
        second_avg = np.mean([s.overall_sync_rate for s in second_half])

        sync_improvement = second_avg - first_avg

        if len(anomaly_history) >= 10:
            mid_a = len(anomaly_history) // 2
            first_anomalies = anomaly_history[:mid_a]
            second_anomalies = anomaly_history[mid_a:]
            
            if len(first_anomalies) > len(second_anomalies):
                anomaly_trend = "improving"
            elif len(first_anomalies) < len(second_anomalies):
                anomaly_trend = "worsening"
            else:
                anomaly_trend = "stable"
        else:
            anomaly_trend = "insufficient_data"

        overall_improvement = sync_improvement * 0.7 + (0.1 if anomaly_trend == "improving" else -0.1 if anomaly_trend == "worsening" else 0) * 0.3

        return {
            "sync_improvement": sync_improvement,
            "anomaly_trend": anomaly_trend,
            "overall_improvement": overall_improvement,
            "first_half_sync": first_avg,
            "second_half_sync": second_avg,
            "first_half_anomalies": len(first_anomalies) if anomaly_history else 0,
            "second_half_anomalies": len(second_anomalies) if len(anomaly_history) >= 10 else 0
        }

    def generate_training_review(self) -> Optional[TrainingReviewResponse]:
        if not self.session_store or not self.session_id:
            return None
        
        self._refresh_strategy()
        
        session = self.session_manager.get_session(self.session_id)
        if not session:
            return None
        
        aligned_data = self.store.get_aligned_data()
        if not aligned_data:
            return None
        
        start_time = aligned_data[0].timestamp
        end_time = aligned_data[-1].timestamp
        total_duration = (end_time - start_time) / 1000
        
        strategy_applications = self.session_store.get_strategy_application_times()
        
        sync_history = self.store.get_sync_rate_history()
        phase_sync_curve = self._generate_phase_sync_curve(sync_history, start_time, end_time)
        
        anomaly_durations = self._calculate_anomaly_durations()
        
        desync_segments = self._identify_key_desync_segments(sync_history, aligned_data)
        
        seat_deficiencies = self._analyze_seat_deficiencies(aligned_data)
        
        load_peaks = self._identify_training_load_peaks(aligned_data)
        
        strategy_comparisons = self._compare_strategy_effects(strategy_applications, sync_history)
        
        overall_score = self._calculate_overall_score(sync_history, anomaly_durations, seat_deficiencies)
        
        return TrainingReviewResponse(
            session_id=self.session_id,
            session_name=session.session_name,
            total_duration_seconds=total_duration,
            phase_summary=self._generate_phase_summary(sync_history, start_time, end_time),
            phase_sync_rate_curve=phase_sync_curve,
            anomaly_duration_stats=anomaly_durations,
            key_desync_segments=desync_segments,
            seat_technical_deficiencies=seat_deficiencies,
            training_load_peaks=load_peaks,
            strategy_effect_comparisons=strategy_comparisons,
            overall_score=overall_score
        )

    def _generate_phase_sync_curve(self, sync_history: List[SyncRateResult],
                                   start_time: int, end_time: int) -> List[PhaseSyncRatePoint]:
        if not sync_history:
            return []
        
        total_duration = (end_time - start_time) / 1000
        phase_points = []
        
        for sr in sync_history:
            elapsed = (sr.timestamp - start_time) / 1000
            phase = self._get_phase_for_time(elapsed, total_duration)
            phase_points.append(PhaseSyncRatePoint(
                phase=phase,
                timestamp=sr.timestamp,
                overall_sync_rate=sr.overall_sync_rate,
                seat_sync_rates=sr.seat_sync_rates
            ))
        
        return phase_points

    def _get_phase_for_time(self, elapsed: float, total_duration: float) -> TrainingPhase:
        if total_duration <= 0:
            return TrainingPhase.WARMUP
        
        progress = elapsed / total_duration
        
        if progress < 0.15:
            return TrainingPhase.WARMUP
        elif progress < 0.4:
            return TrainingPhase.INTENSITY
        elif progress < 0.75:
            return TrainingPhase.ENDURANCE
        elif progress < 0.9:
            return TrainingPhase.INTERVAL
        else:
            return TrainingPhase.COOLDOWN

    def _generate_phase_summary(self, sync_history: List[SyncRateResult],
                                start_time: int, end_time: int) -> Dict[str, Dict[str, Any]]:
        if not sync_history:
            return {}
        
        total_duration = (end_time - start_time) / 1000
        phase_data: Dict[TrainingPhase, List[SyncRateResult]] = {}
        
        for sr in sync_history:
            elapsed = (sr.timestamp - start_time) / 1000
            phase = self._get_phase_for_time(elapsed, total_duration)
            if phase not in phase_data:
                phase_data[phase] = []
            phase_data[phase].append(sr)
        
        summary = {}
        for phase, data in phase_data.items():
            if data:
                avg_sync = np.mean([s.overall_sync_rate for s in data])
                min_sync = min([s.overall_sync_rate for s in data])
                max_sync = max([s.overall_sync_rate for s in data])
                anomaly_count = len(self.store.get_anomalies(
                    start_time=data[0].timestamp,
                    limit=1000
                ))
                
                summary[phase.value] = {
                    "avg_sync_rate": float(avg_sync),
                    "min_sync_rate": float(min_sync),
                    "max_sync_rate": float(max_sync),
                    "data_points": len(data),
                    "anomaly_count": anomaly_count,
                    "duration_seconds": (data[-1].timestamp - data[0].timestamp) / 1000 if len(data) > 1 else 0
                }
        
        return summary

    def _calculate_anomaly_durations(self) -> List[AnomalyDurationStats]:
        if not self.session_store:
            return []
        
        raw_durations = self.session_store.get_anomaly_durations()
        stats = []
        
        for anomaly_type, intervals in raw_durations.items():
            if not intervals:
                continue
            
            durations = [(end - start) / 1000 for start, end in intervals]
            total_duration = sum(durations)
            count = len(durations)
            avg_duration = total_duration / count if count > 0 else 0
            max_duration = max(durations) if durations else 0
            
            stats.append(AnomalyDurationStats(
                anomaly_type=anomaly_type,
                total_duration_seconds=float(total_duration),
                count=count,
                avg_duration_seconds=float(avg_duration),
                max_duration_seconds=float(max_duration)
            ))
        
        return sorted(stats, key=lambda x: x.total_duration_seconds, reverse=True)

    def _identify_key_desync_segments(self, sync_history: List[SyncRateResult],
                                      aligned_data: List[AlignedDataPoint]) -> List[KeyDesyncSegment]:
        if not sync_history:
            return []
        
        threshold = self.thresholds["sync_score_threshold"] * 0.95
        segments = []
        current_segment: Optional[Dict] = None
        
        for sr in sync_history:
            if sr.overall_sync_rate < threshold:
                if current_segment is None:
                    current_segment = {
                        "start": sr.timestamp,
                        "end": sr.timestamp,
                        "min_sync": sr.overall_sync_rate,
                        "anomaly_types": set(),
                        "affected_seats": set()
                    }
                else:
                    current_segment["end"] = sr.timestamp
                    current_segment["min_sync"] = min(current_segment["min_sync"], sr.overall_sync_rate)
                
                anomalies = self.store.get_anomalies(
                    start_time=sr.timestamp - 2000,
                    limit=10
                )
                for a in anomalies:
                    if abs(a.timestamp - sr.timestamp) < 3000:
                        current_segment["anomaly_types"].add(a.anomaly_type)
                        for seat in a.seat_positions:
                            current_segment["affected_seats"].add(seat)
            else:
                if current_segment is not None:
                    duration = (current_segment["end"] - current_segment["start"]) / 1000
                    if duration >= 3:
                        segments.append(KeyDesyncSegment(
                            start_timestamp=current_segment["start"],
                            end_timestamp=current_segment["end"],
                            duration_seconds=float(duration),
                            min_sync_rate=float(current_segment["min_sync"]),
                            anomaly_types=list(current_segment["anomaly_types"]),
                            affected_seats=sorted(list(current_segment["affected_seats"])),
                            description=f"同步率低于{threshold:.2f}持续{duration:.1f}秒"
                        ))
                    current_segment = None
        
        if current_segment is not None:
            duration = (current_segment["end"] - current_segment["start"]) / 1000
            if duration >= 3:
                segments.append(KeyDesyncSegment(
                    start_timestamp=current_segment["start"],
                    end_timestamp=current_segment["end"],
                    duration_seconds=float(duration),
                    min_sync_rate=float(current_segment["min_sync"]),
                    anomaly_types=list(current_segment["anomaly_types"]),
                    affected_seats=sorted(list(current_segment["affected_seats"])),
                    description=f"同步率低于{threshold:.2f}持续{duration:.1f}秒"
                ))
        
        return sorted(segments, key=lambda x: x.duration_seconds, reverse=True)[:5]

    def _analyze_seat_deficiencies(self, aligned_data: List[AlignedDataPoint]) -> List[SeatTechnicalDeficiency]:
        if not aligned_data:
            return []
        
        anomalies = self.store.get_anomalies(limit=1000)
        seat_anomaly_counts: Dict[int, Dict[AnomalyType, List[float]]] = {}
        
        for a in anomalies:
            for seat in a.seat_positions:
                if seat not in seat_anomaly_counts:
                    seat_anomaly_counts[seat] = {}
                if a.anomaly_type not in seat_anomaly_counts[seat]:
                    seat_anomaly_counts[seat][a.anomaly_type] = []
                seat_anomaly_counts[seat][a.anomaly_type].append(a.severity)
        
        deficiencies = []
        for seat, anomaly_data in seat_anomaly_counts.items():
            if not anomaly_data:
                continue
            
            primary_issue = max(anomaly_data.items(), key=lambda x: len(x[1]))
            issue_count = len(primary_issue[1])
            avg_severity = np.mean(primary_issue[1])
            
            description = self._get_deficiency_description(primary_issue[0], seat)
            suggestion = self._get_deficiency_suggestion(primary_issue[0], seat)
            
            deficiencies.append(SeatTechnicalDeficiency(
                seat_position=seat,
                primary_issue=primary_issue[0],
                issue_count=issue_count,
                avg_severity=float(avg_severity),
                description=description,
                improvement_suggestion=suggestion
            ))
        
        return sorted(deficiencies, key=lambda x: x.issue_count, reverse=True)

    def _get_deficiency_description(self, issue: AnomalyType, seat: int) -> str:
        descriptions = {
            AnomalyType.STROKE_RATE_MISMATCH: f"{seat}号桨位桨频控制不稳定，与全队节奏偏差较大",
            AnomalyType.ENTRY_ANGLE_DEVIATION: f"{seat}号桨位入水角度控制不准确，动作一致性有待提高",
            AnomalyType.FORCE_IMBALANCE: f"{seat}号桨位力量输出不均衡，与全队配合不佳",
            AnomalyType.RHYTHM_DISORDER: f"{seat}号桨位划桨节奏不稳定，动作规律性不足",
            AnomalyType.DEVICE_OFFLINE: f"{seat}号桨位传感器连接不稳定"
        }
        return descriptions.get(issue, f"{seat}号桨位存在技术问题需要改进")

    def _get_deficiency_suggestion(self, issue: AnomalyType, seat: int) -> str:
        suggestions = {
            AnomalyType.STROKE_RATE_MISMATCH: "建议加强节拍器训练，保持稳定的划桨频率，注意观察前后队员的节奏",
            AnomalyType.ENTRY_ANGLE_DEVIATION: "建议进行专项入水技术训练，注意转肩和提桨动作的连贯性",
            AnomalyType.FORCE_IMBALANCE: "建议进行力量均衡训练，注意蹬腿-拉臂-回桨的力量传导节奏",
            AnomalyType.RHYTHM_DISORDER: "建议进行节奏稳定性训练，保持入水-拉桨-出水-回桨的完整动作周期",
            AnomalyType.DEVICE_OFFLINE: "建议检查传感器连接和电池状态，确保训练前设备正常"
        }
        return suggestions.get(issue, "建议加强基础技术训练，提高动作稳定性")

    def _identify_training_load_peaks(self, aligned_data: List[AlignedDataPoint]) -> List[TrainingLoadPeak]:
        if len(aligned_data) < 10:
            return []
        
        window_size = 30
        peaks = []
        
        by_seat: Dict[int, List[AlignedDataPoint]] = {}
        for p in aligned_data:
            if p.seat_position not in by_seat:
                by_seat[p.seat_position] = []
            by_seat[p.seat_position].append(p)
        
        timestamps = sorted(set([p.timestamp for p in aligned_data]))
        
        for i in range(0, len(timestamps) - window_size, window_size // 2):
            window_ts = timestamps[i:i + window_size]
            if len(window_ts) < 10:
                continue
            
            window_data = [p for p in aligned_data if p.timestamp in window_ts]
            if not window_data:
                continue
            
            by_seat_window: Dict[int, List[AlignedDataPoint]] = {}
            for p in window_data:
                if p.seat_position not in by_seat_window:
                    by_seat_window[p.seat_position] = []
                by_seat_window[p.seat_position].append(p)
            
            window_load = 0
            active_seats = []
            avg_rates = []
            avg_forces = []
            
            for seat, points in by_seat_window.items():
                if len(points) < 5:
                    continue
                active_seats.append(seat)
                rates = [p.stroke_rate for p in points if p.stroke_rate > 0]
                forces = [p.pull_force for p in points if p.pull_force > 0]
                if rates and forces:
                    avg_rate = np.mean(rates)
                    avg_force = np.mean(forces)
                    avg_rates.append(avg_rate)
                    avg_forces.append(avg_force)
                    duration = (points[-1].timestamp - points[0].timestamp) / 1000
                    window_load += (avg_rate * avg_force * duration) / 1000
            
            if window_load > 0 and active_seats:
                peaks.append(TrainingLoadPeak(
                    start_timestamp=window_ts[0],
                    end_timestamp=window_ts[-1],
                    duration_seconds=float((window_ts[-1] - window_ts[0]) / 1000),
                    peak_load_score=float(window_load),
                    avg_stroke_rate=float(np.mean(avg_rates)) if avg_rates else 0,
                    avg_force=float(np.mean(avg_forces)) if avg_forces else 0,
                    affected_seats=active_seats
                ))
        
        peaks.sort(key=lambda x: x.peak_load_score, reverse=True)
        return peaks[:3]

    def _compare_strategy_effects(self, applications: List[Tuple[int, str]],
                                  sync_history: List[SyncRateResult]) -> List[StrategyEffectComparison]:
        if not applications or not sync_history:
            return []
        
        comparisons = []
        
        for apply_time, strategy_id in applications:
            before_start = apply_time - 60000
            after_end = apply_time + 60000
            
            before_data = [s for s in sync_history if before_start <= s.timestamp < apply_time]
            after_data = [s for s in sync_history if apply_time <= s.timestamp <= after_end]
            
            if len(before_data) < 5 or len(after_data) < 5:
                continue
            
            before_avg = np.mean([s.overall_sync_rate for s in before_data])
            after_avg = np.mean([s.overall_sync_rate for s in after_data])
            
            before_anomalies = len(self.store.get_anomalies(start_time=before_start, limit=1000))
            after_anomalies = len(self.store.get_anomalies(start_time=apply_time, limit=1000))
            
            improvement = after_avg - before_avg
            
            metrics_changed = []
            if abs(before_avg - after_avg) > 0.05:
                metrics_changed.append("overall_sync_rate")
            if abs(before_anomalies - after_anomalies) > 2:
                metrics_changed.append("anomaly_count")
            
            comparisons.append(StrategyEffectComparison(
                strategy_id=strategy_id,
                applied_at=apply_time,
                before_period={
                    "avg_sync_rate": float(before_avg),
                    "anomaly_count": before_anomalies,
                    "data_points": len(before_data)
                },
                after_period={
                    "avg_sync_rate": float(after_avg),
                    "anomaly_count": after_anomalies,
                    "data_points": len(after_data)
                },
                improvement_score=float(improvement),
                key_metrics_changed=metrics_changed
            ))
        
        return comparisons

    def _calculate_overall_score(self, sync_history: List[SyncRateResult],
                                 anomaly_durations: List[AnomalyDurationStats],
                                 deficiencies: List[SeatTechnicalDeficiency]) -> float:
        if not sync_history:
            return 0.0
        
        avg_sync = np.mean([s.overall_sync_rate for s in sync_history])
        
        total_anomaly_duration = sum([a.total_duration_seconds for a in anomaly_durations])
        total_duration = (sync_history[-1].timestamp - sync_history[0].timestamp) / 1000
        anomaly_ratio = total_anomaly_duration / max(total_duration, 1)
        
        deficiency_penalty = sum([d.avg_severity * d.issue_count for d in deficiencies]) * 0.01
        
        score = avg_sync * 0.6 + (1 - min(1, anomaly_ratio)) * 0.25 + max(0, 1 - deficiency_penalty) * 0.15
        
        return max(0, min(1, float(score)))

    def generate_real_time_intervention(self) -> Optional[RealTimeInterventionResponse]:
        if not self.session_store or not self.session_id:
            return None
        
        self._refresh_strategy()
        
        current_time = int(time.time() * 1000)
        consecutive_count = self.session_store.get_consecutive_anomaly_count()
        threshold = self.thresholds["consecutive_anomaly_threshold"]
        requires_intervention = consecutive_count >= threshold
        
        session = self.session_manager.get_session(self.session_id)
        current_state = session.current_state if session else TrainingState.NORMAL_TRAINING
        
        seat_suggestions = self._generate_seat_suggestions()
        overall_suggestion = self._generate_overall_suggestion(consecutive_count, requires_intervention)
        
        recommended_transition = None
        if requires_intervention:
            if current_state == TrainingState.NORMAL_TRAINING:
                recommended_transition = TrainingState.POSTURE_WARNING
            elif current_state == TrainingState.POSTURE_WARNING and consecutive_count >= threshold * 2:
                recommended_transition = TrainingState.TECHNICAL_ADJUSTMENT
            elif current_state == TrainingState.TECHNICAL_ADJUSTMENT and consecutive_count >= threshold * 3:
                recommended_transition = TrainingState.REST_RECOVERY
        
        return RealTimeInterventionResponse(
            session_id=self.session_id,
            timestamp=current_time,
            current_state=current_state,
            consecutive_anomaly_count=consecutive_count,
            requires_intervention=requires_intervention,
            seat_suggestions=seat_suggestions,
            overall_suggestion=overall_suggestion,
            recommended_state_transition=recommended_transition
        )

    def _generate_seat_suggestions(self) -> List[SeatInterventionSuggestion]:
        suggestions = []
        
        aligned_data = self.store.get_aligned_data(limit=50)
        if not aligned_data:
            return suggestions
        
        by_seat: Dict[int, List[AlignedDataPoint]] = {}
        for p in aligned_data:
            if p.seat_position not in by_seat:
                by_seat[p.seat_position] = []
            by_seat[p.seat_position].append(p)
        
        if len(by_seat) < 2:
            return suggestions
        
        seat_avg_rates = {s: np.mean([p.stroke_rate for p in pts if p.stroke_rate > 0]) 
                         for s, pts in by_seat.items() if [p.stroke_rate for p in pts if p.stroke_rate > 0]}
        seat_avg_angles = {s: np.mean([p.entry_angle for p in pts]) 
                          for s, pts in by_seat.items()}
        seat_avg_forces = {s: np.mean([p.pull_force for p in pts if p.pull_force > 0]) 
                          for s, pts in by_seat.items() if [p.pull_force for p in pts if p.pull_force > 0]}
        
        if len(seat_avg_rates) < 2:
            return suggestions
        
        target_rate = np.mean(list(seat_avg_rates.values()))
        target_angle = np.mean(list(seat_avg_angles.values()))
        target_force = np.mean(list(seat_avg_forces.values()))
        
        rate_threshold = self.thresholds["stroke_rate_deviation"]
        angle_threshold = self.thresholds["entry_angle_deviation"]
        force_threshold = self.thresholds["force_imbalance_ratio"]
        
        for seat in by_seat.keys():
            if seat in seat_avg_rates:
                rate_dev = abs(seat_avg_rates[seat] - target_rate)
                if rate_dev > rate_threshold:
                    urgency = "high" if rate_dev > rate_threshold * 2 else "medium"
                    suggestions.append(SeatInterventionSuggestion(
                        seat_position=seat,
                        action_type="adjust_stroke_rate",
                        parameter="stroke_rate",
                        target_value=float(target_rate),
                        current_value=float(seat_avg_rates[seat]),
                        urgency=urgency,
                        description=f"桨频{'偏高' if seat_avg_rates[seat] > target_rate else '偏低'}，请{'降低' if seat_avg_rates[seat] > target_rate else '提高'}桨频"
                    ))
            
            if seat in seat_avg_angles:
                angle_dev = abs(seat_avg_angles[seat] - target_angle)
                if angle_dev > angle_threshold:
                    urgency = "high" if angle_dev > angle_threshold * 2 else "medium"
                    suggestions.append(SeatInterventionSuggestion(
                        seat_position=seat,
                        action_type="adjust_entry_angle",
                        parameter="entry_angle",
                        target_value=float(target_angle),
                        current_value=float(seat_avg_angles[seat]),
                        urgency=urgency,
                        description=f"入水角度{'偏大' if seat_avg_angles[seat] > target_angle else '偏小'}，请{'减小' if seat_avg_angles[seat] > target_angle else '增大'}入水角度"
                    ))
            
            if seat in seat_avg_forces and target_force > 0:
                force_dev_ratio = abs(seat_avg_forces[seat] - target_force) / target_force
                if force_dev_ratio > force_threshold:
                    urgency = "high" if force_dev_ratio > force_threshold * 2 else "medium"
                    suggestions.append(SeatInterventionSuggestion(
                        seat_position=seat,
                        action_type="adjust_force",
                        parameter="pull_force",
                        target_value=float(target_force),
                        current_value=float(seat_avg_forces[seat]),
                        urgency=urgency,
                        description=f"拉桨力量{'偏大' if seat_avg_forces[seat] > target_force else '偏小'}，请{'控制' if seat_avg_forces[seat] > target_force else '增加'}拉桨力量"
                    ))
        
        return suggestions

    def _generate_overall_suggestion(self, consecutive_count: int, requires_intervention: bool) -> str:
        if not requires_intervention:
            return "训练状态良好，继续保持当前节奏和技术动作"
        
        threshold = self.thresholds["consecutive_anomaly_threshold"]
        
        if consecutive_count >= threshold * 3:
            return "⚠️ 连续多次检测到严重异常，建议立即停止训练进行休息和技术调整"
        elif consecutive_count >= threshold * 2:
            return "⚠️ 异常持续存在，需要集中注意力进行技术调整，必要时降低训练强度"
        else:
            return "⚠️ 检测到连续异常，请关注划姿和节奏，及时调整动作"
