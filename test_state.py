import requests
import time

BASE_URL = 'http://localhost:9801'

print('=== 对齐数据 ===')
r = requests.get(f'{BASE_URL}/api/analysis/alignment/latest?limit=5')
data = r.json()['data']
print(f'时间戳数: {data["timestamps_count"]}, 总点数: {data["total_points"]}')
for ts, points in sorted(data['data'].items()):
    seats = sorted([p['seat_position'] for p in points])
    print(f'  {ts}: 桨位 {seats}')

print()
print('=== 状态历史 ===')
r = requests.get(f'{BASE_URL}/api/state/history')
data = r.json()['data']
print(f'状态记录数: {data["count"]}')
for record in data['history']:
    print(f'  {record["state"]}: 持续{record["duration_seconds"]}秒, 异常{record["anomaly_count"]}次')

print()
print('=== 测试状态流转 - 持续上报异常数据 ===')
requests.post(f'{BASE_URL}/api/state/reset')
print('已重置，开始持续上报异常数据...')

for i in range(50):
    ts = int(time.time() * 1000)
    batch = []
    for seat in range(1, 5):
        if seat == 1:
            rate, angle, force = 30, 45, 150
        elif seat == 2:
            rate, angle, force = 36, 45, 150
        elif seat == 3:
            rate, angle, force = 30, 58, 150
        else:
            rate, angle, force = 30, 45, 240
        
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
    
    if i % 10 == 0 or state.get('transitioned'):
        current_state = state.get('current_state', 'normal_training')
        sync_rate = res['data']['sync_rate']['overall_sync_rate']
        print(f'批次{i}: 同步率={sync_rate:.3f}, 状态={current_state}')
        if state.get('transitioned'):
            print(f'  -> 状态变更: {state["previous_state"]} -> {state["current_state"]}')
            print(f'    原因: {state["reason"]}')
            for s in state.get('suggestions', [])[:2]:
                print(f'    建议: {s}')
    
    time.sleep(0.15)

print()
print('=== 最终状态 ===')
r = requests.get(f'{BASE_URL}/api/state/current')
print(f'当前状态: {r.json()["data"]["state"]}')

print()
print('=== 状态流转历史 ===')
r = requests.get(f'{BASE_URL}/api/state/history')
for record in r.json()['data']['history']:
    print(f'  {record["state"]}: {record["duration_seconds"]}秒')
