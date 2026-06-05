import requests
import time
import random

BASE_URL = 'http://localhost:9801'

requests.post(f'{BASE_URL}/api/state/reset')
print('重置完成')

for i in range(30):
    ts = int(time.time() * 1000)
    batch = []
    for seat in range(1, 5):
        if seat == 1:
            rate, angle, force = 30, 45, 150
        elif seat == 2:
            rate, angle, force = 35, 45, 150
        elif seat == 3:
            rate, angle, force = 30, 55, 150
        else:
            rate, angle, force = 30, 45, 220
        
        batch.append({
            'device_id': f'sensor_{seat}',
            'seat_position': seat,
            'timestamp': ts,
            'stroke_rate': rate + random.uniform(-0.5, 0.5),
            'entry_angle': angle + random.uniform(-0.5, 0.5),
            'pull_force': force + random.uniform(-5, 5),
            'hull_acceleration': 0.5
        })
    
    r = requests.post(f'{BASE_URL}/api/telemetry/batch-report', json=batch)
    res = r.json()
    
    if i % 10 == 0:
        sr = res['data'].get('sync_rate')
        anomalies = res['data'].get('anomalies', [])
        state = res['data'].get('state_update', {})
        print(f'批次{i}: 同步率={sr["overall_sync_rate"]:.3f}, 异常={len(anomalies)}, 状态={state.get("current_state")}')
        for a in anomalies[:3]:
            print(f'  - {a["anomaly_type"]}: {a["suggestion"][:50]}...')
    
    time.sleep(0.1)

print()
print('=== 最终状态 ===')
r = requests.get(f'{BASE_URL}/api/state/current')
print(f'状态: {r.json()["data"]["state"]}')

print()
print('=== 异常统计 ===')
r = requests.get(f'{BASE_URL}/api/analysis/anomalies')
for t, c in r.json()['data']['summary'].items():
    print(f'  {t}: {c}次')

print()
print('=== 稳定性排行 ===')
r = requests.get(f'{BASE_URL}/api/analysis/stability/ranking')
for rank in r.json()['data']['rankings']:
    print(f'  {rank["seat_position"]}号: {rank["stability_score"]:.3f} (异常{rank["anomaly_count"]}次)')

print()
print('=== 训练负荷 ===')
r = requests.get(f'{BASE_URL}/api/statistics/training-load')
data = r.json()['data']
print(f'总体负荷: {data["overall_load"]:.2f}')
for seat, info in sorted(data['seat_loads'].items()):
    print(f'  {seat}号: 负荷={info["load_score"]:.2f}, 平均桨频={info["avg_stroke_rate"]:.1f}')
