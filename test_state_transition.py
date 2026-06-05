import requests
import time

BASE_URL = 'http://localhost:9801'

# 重置
requests.post(f'{BASE_URL}/api/state/reset')
print('已重置，制造严重异常测试状态流转...')
print()

# 制造非常严重的异常，同步率应该低于 0.75
for i in range(80):
    ts = int(time.time() * 1000)
    batch = []
    for seat in range(1, 5):
        if seat == 1:
            rate, angle, force = 25, 40, 120
        elif seat == 2:
            rate, angle, force = 40, 40, 120
        elif seat == 3:
            rate, angle, force = 25, 65, 120
        else:
            rate, angle, force = 25, 40, 250
        
        batch.append({
            'device_id': f'sensor_{seat}',
            'seat_position': seat,
            'timestamp': ts,
            'stroke_rate': rate,
            'entry_angle': angle,
            'pull_force': force,
            'hull_acceleration': 0.5
        })
    
    r = requests.post(f'{BASE_URL}/api/telemetry/batch-report', json=batch)
    res = r.json()
    state = res['data'].get('state_update', {})
    
    if i % 15 == 0 or state.get('transitioned'):
        current_state = state.get('current_state', 'normal_training')
        sync_rate = res['data']['sync_rate']['overall_sync_rate']
        anomalies = len(res['data'].get('anomalies', []))
        print(f'批次{i}: 同步率={sync_rate:.3f}, 异常={anomalies}, 状态={current_state}')
        if state.get('transitioned'):
            print(f'  *** 状态变更: {state["previous_state"]} -> {state["current_state"]}')
            print(f'      原因: {state["reason"]}')
            for s in state.get('suggestions', []):
                print(f'      {s}')
            print()
    
    time.sleep(0.2)

print()
print('=== 最终状态 ===')
r = requests.get(f'{BASE_URL}/api/state/current')
data = r.json()['data']
print(f'当前状态: {data["state"]}')
print(f'持续时间: {data["duration_seconds"]}秒')

print()
print('=== 状态流转历史 ===')
r = requests.get(f'{BASE_URL}/api/state/history')
for record in r.json()['data']['history']:
    print(f'  {record["state"]}: {record["duration_seconds"]}秒, 异常{record["anomaly_count"]}次')

print()
print('=== 结束训练 ===')
r = requests.post(f'{BASE_URL}/api/state/end-training')
print(f'最终状态: {r.json()["data"]["state"]}')
for s in r.json()['data']['suggestions']:
    print(f'  {s}')
