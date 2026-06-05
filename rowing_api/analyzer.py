import time
from typing import Dict, List, Tuple, Optional
import numpy as np

from .config import Config
from .storage import DataStore
from .models import (
    AlignedDataPoint, AnomalyRecord, AnomalyType,
    SyncRateResult, StrokeStability
)


class StrokeAnalyzer:
    def __init__(self):
        self.store = DataStore()
        self.thresholds = Config.ANOMALY_THRESHOLDS

    def calculate_sync_rate(self) -> Optional[SyncRateResult]:
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

        overall_sync = (stroke_rate_sync_norm * 0.4 + 
                       angle_sync_norm * 0.3 + 
                       force_sync_norm * 0.3)

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
        
        overall_mean = np.mean(list(seat_avg_rates.values()))
        
        problem_seats = []
        deviations = {}
        for seat, avg_rate in seat_avg_rates.items():
            dev = abs(avg_rate - overall_mean)
            deviations[seat] = dev
            if dev > threshold:
                problem_seats.append(seat)
        
        if problem_seats:
            max_dev = max(deviations.values())
            severity = min(1.0, max_dev / (threshold * 3))
            current_time = int(time.time() * 1000)
            
            desc = f"桨频不齐: {', '.join([f'{s}号' for s in problem_seats])}桨位与平均值偏差超过{threshold}桨/分钟"
            suggestion = self._generate_stroke_rate_suggestion(seat_avg_rates, overall_mean, problem_seats)
            
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
                                       overall_mean: float, 
                                       problem_seats: List[int]) -> str:
        slow = [s for s in problem_seats if seat_rates[s] < overall_mean]
        fast = [s for s in problem_seats if seat_rates[s] > overall_mean]
        
        suggestions = []
        if slow:
            suggestions.append(f"请{', '.join([f'{s}号' for s in slow])}桨位加快划桨频率")
        if fast:
            suggestions.append(f"请{', '.join([f'{s}号' for s in fast])}桨位降低划桨频率")
        suggestions.append(f"全队目标桨频: {overall_mean:.1f}桨/分钟")
        
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
            
            desc = f"入水角度偏差: {', '.join([f'{s}号' for s in problem_seats])}桨位与平均值偏差超过{threshold}度"
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
        suggestions.append(f"全队目标入水角度: {overall_mean:.1f}度")
        
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
            
            desc = f"力量输出不均: {', '.join([f'{s}号' for s in problem_seats])}桨位力量偏差超过{threshold*100:.0f}%"
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
            
            timestamps = [p.timestamp for p in points]
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
            
            desc = f"节奏混乱: {', '.join([f'{s}号' for s in problem_seats])}桨位划桨节奏变异系数超过{threshold*100:.0f}%"
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

            stability = (
                (1 - min(1, rate_cv * 2)) * 0.35 +
                (1 - min(1, force_cv * 2)) * 0.35 +
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
            
            load = (avg_stroke_rate * avg_force * time_span) / 1000
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
