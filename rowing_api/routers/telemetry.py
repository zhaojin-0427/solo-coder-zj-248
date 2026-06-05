from fastapi import APIRouter, HTTPException
from typing import List

from ..models import (
    TelemetryData, success_response, error_response,
    AnomalyType, TrainingState
)
from ..storage import DataStore
from ..analyzer import StrokeAnalyzer
from ..state_manager import StateManager

router = APIRouter(prefix="/api/telemetry", tags=["遥测数据"])

store = DataStore()
analyzer = StrokeAnalyzer()
state_manager = StateManager()


@router.post("/report")
async def report_telemetry(data: TelemetryData):
    try:
        store.add_telemetry(data)
        
        store.trigger_alignment()
        
        sync_rate = analyzer.calculate_sync_rate()
        anomalies = analyzer.detect_anomalies()
        
        state_update = state_manager.update(sync_rate, anomalies)
        
        response_data = {
            "received": True,
            "timestamp": data.timestamp,
            "seat_position": data.seat_position,
            "sync_rate": sync_rate.model_dump() if sync_rate else None,
            "anomalies": [a.model_dump() for a in anomalies],
            "state_update": state_update
        }
        
        return success_response(response_data, "数据上报成功")
    except Exception as e:
        return error_response(500, f"数据上报失败: {str(e)}")


@router.post("/batch-report")
async def batch_report_telemetry(data_list: List[TelemetryData]):
    try:
        results = []
        for data in data_list:
            store.add_telemetry(data)
            results.append({
                "device_id": data.device_id,
                "seat_position": data.seat_position,
                "timestamp": data.timestamp,
                "success": True
            })
        
        store.trigger_alignment()
        
        sync_rate = analyzer.calculate_sync_rate()
        anomalies = analyzer.detect_anomalies()
        state_update = state_manager.update(sync_rate, anomalies)
        
        response_data = {
            "received_count": len(results),
            "results": results,
            "sync_rate": sync_rate.model_dump() if sync_rate else None,
            "anomalies": [a.model_dump() for a in anomalies],
            "state_update": state_update
        }
        
        return success_response(response_data, f"成功接收{len(results)}条数据")
    except Exception as e:
        return error_response(500, f"批量上报失败: {str(e)}")


@router.get("/latest/{seat}")
async def get_latest_telemetry(seat: int, limit: int = 10):
    try:
        data = store.get_raw_data(seat, limit)
        return success_response({
            "seat_position": seat,
            "count": len(data),
            "data": [d.model_dump() for d in data]
        })
    except Exception as e:
        return error_response(500, f"查询失败: {str(e)}")


@router.get("/devices")
async def get_device_status():
    try:
        device_info = store.get_device_info()
        active_seats = store.get_active_seats()
        offline_devices = store.get_offline_devices()
        
        return success_response({
            "devices": device_info,
            "active_seats": active_seats,
            "offline_devices": [
                {"seat": s, "device_id": d} for s, d in offline_devices
            ],
            "total_devices": len(device_info),
            "online_count": len(active_seats),
            "offline_count": len(offline_devices)
        })
    except Exception as e:
        return error_response(500, f"查询设备状态失败: {str(e)}")


@router.get("/raw-data")
async def get_raw_data(start_time: int = None, end_time: int = None, 
                      seats: str = None, limit: int = 100):
    try:
        seat_list = [int(s) for s in seats.split(",")] if seats else None
        data = store.get_aligned_data(start_time, end_time, seat_list)
        
        if limit and len(data) > limit:
            data = data[-limit:]
        
        return success_response({
            "count": len(data),
            "time_range": {
                "start": data[0].timestamp if data else None,
                "end": data[-1].timestamp if data else None
            },
            "data": [d.model_dump() for d in data]
        })
    except Exception as e:
        return error_response(500, f"查询原始数据失败: {str(e)}")
