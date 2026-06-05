#!/usr/bin/env python3
import requests
import time
import random
import json

BASE_URL = "http://localhost:9801"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    print_section("1. 健康检查")
    response = requests.get(f"{BASE_URL}/health")
    result = response.json()
    print(f"状态码: {result['code']}")
    print(f"消息: {result['message']}")
    print(f"服务状态: {result['data']['status']}")
    assert result['code'] == 200
    assert result['data']['status'] == 'healthy'
    print("✓ 健康检查通过")

def test_reset():
    print_section("2. 重置数据")
    response = requests.post(f"{BASE_URL}/api/state/reset")
    result = response.json()
    print(f"状态码: {result['code']}")
    print(f"消息: {result['message']}")
    print("✓ 数据已重置")

def test_telemetry_report():
    print_section("3. 遥测数据上报测试")
    
    timestamp = int(time.time() * 1000)
    
    # 上报4个桨位的数据
    for i in range(15):
        ts = timestamp + i * 200
        batch_data = []
        
        for seat in range(1, 5):
            # 制造一些差异来测试异常检测
            if seat == 1:
                rate = 30 + random.uniform(-0.5, 0.5)
                angle = 45 + random.uniform(-1, 1)
                force = 150 + random.uniform(-5, 5)
            elif seat == 2:
                rate = 30 + random.uniform(-0.5, 0.5)
                angle = 45 + random.uniform(-1, 1)
                force = 150 + random.uniform(-5, 5)
            elif seat == 3:
                rate = 33 + random.uniform(-0.5, 0.5)  # 桨频偏高
                angle = 45 + random.uniform(-1, 1)
                force = 150 + random.uniform(-5, 5)
            else:  # seat 4
                rate = 30 + random.uniform(-0.5, 0.5)
                angle = 52 + random.uniform(-1, 1)  # 角度偏大
                force = 190 + random.uniform(-5, 5)  # 力量偏大
            
            data = {
                "device_id": f"sensor_seat_{seat}",
                "seat_position": seat,
                "timestamp": ts + seat * 5,
                "stroke_rate": rate,
                "entry_angle": angle,
                "pull_force": force,
                "hull_acceleration": 0.5 + random.uniform(-0.1, 0.1)
            }
            batch_data.append(data)
        
        response = requests.post(f"{BASE_URL}/api/telemetry/batch-report", json=batch_data)
        result = response.json()
        
        if result.get('data') and result['data'].get('sync_rate'):
            sr = result['data']['sync_rate']
            anomalies = result['data'].get('anomalies', [])
            state = result['data'].get('state_update', {})
            
            print(f"批次{i+1:2d}: 同步率={sr['overall_sync_rate']:.3f}, "
                  f"异常数={len(anomalies)}, 状态={state.get('current_state', 'normal_training')}")
        
        time.sleep(0.1)
    
    print("✓ 遥测数据上报完成")

def test_devices():
    print_section("4. 设备状态查询")
    response = requests.get(f"{BASE_URL}/api/telemetry/devices")
    result = response.json()
    data = result['data']
    print(f"总设备数: {data['total_devices']}")
    print(f"在线设备: {data['online_count']}")
    print(f"离线设备: {data['offline_count']}")
    print(f"活跃桨位: {data['active_seats']}")
    assert result['code'] == 200
    print("✓ 设备状态查询通过")

def test_alignment():
    print_section("5. 时序对齐数据查询")
    response = requests.get(f"{BASE_URL}/api/analysis/alignment/latest?limit=10")
    result = response.json()
    data = result['data']
    print(f"时间戳数量: {data['timestamps_count']}")
    print(f"总数据点数: {data['total_points']}")
    
    # 打印每个时间戳的桨位数据
    for ts, points in sorted(data['data'].items()):
        seats = sorted([p['seat_position'] for p in points])
        print(f"  时间戳 {ts}: 桨位 {seats}")
    
    assert result['code'] == 200
    print("✓ 时序对齐查询通过")

def test_sync_rate():
    print_section("6. 同步率计算")
    response = requests.get(f"{BASE_URL}/api/analysis/sync-rate")
    result = response.json()
    print(f"状态码: {result['code']}")
    print(f"消息: {result['message']}")
    
    if result['data']:
        sr = result['data']
        print(f"整体同步率: {sr['overall_sync_rate']:.4f}")
        print(f"桨频同步: {sr['stroke_rate_sync']:.4f}")
        print(f"角度同步: {sr['angle_sync']:.4f}")
        print(f"力量同步: {sr['force_sync']:.4f}")
        print("各桨位同步率:")
        for seat, rate in sorted(sr['seat_sync_rates'].items()):
            print(f"  {seat}号桨位: {rate:.4f}")
    else:
        print("数据不足")
    
    assert result['code'] == 200
    print("✓ 同步率计算通过")

def test_anomaly_detection():
    print_section("7. 异常检测")
    response = requests.get(f"{BASE_URL}/api/analysis/detect")
    result = response.json()
    data = result['data']
    
    print(f"异常数量: {data['anomaly_count']}")
    print("异常详情:")
    for a in data['anomalies']:
        print(f"  - {a['anomaly_type']}: {a['description']}")
        print(f"    严重程度: {a['severity']:.2f}")
        print(f"    建议: {a['suggestion']}")
    
    assert result['code'] == 200
    print("✓ 异常检测通过")

def test_anomaly_history():
    print_section("8. 异常记录查询")
    response = requests.get(f"{BASE_URL}/api/analysis/anomalies?limit=20")
    result = response.json()
    data = result['data']
    
    print(f"总异常数: {data['count']}")
    print("异常统计:")
    for atype, count in data['summary'].items():
        print(f"  {atype}: {count}次")
    
    assert result['code'] == 200
    print("✓ 异常记录查询通过")

def test_stability_ranking():
    print_section("9. 稳定性排行")
    response = requests.get(f"{BASE_URL}/api/analysis/stability/ranking")
    result = response.json()
    data = result['data']
    
    print(f"排行桨位数: {data['count']}")
    print("稳定性排行:")
    for i, r in enumerate(data['rankings']):
        print(f"  第{i+1}名: {r['seat_position']}号桨位")
        print(f"    稳定性分数: {r['stability_score']:.4f}")
        print(f"    桨频CV: {r['stroke_rate_cv']:.4f}")
        print(f"    力量CV: {r['force_cv']:.4f}")
        print(f"    角度CV: {r['angle_cv']:.4f}")
        print(f"    异常次数: {r['anomaly_count']}")
    
    assert result['code'] == 200
    print("✓ 稳定性排行通过")

def test_training_load():
    print_section("10. 训练负荷统计")
    response = requests.get(f"{BASE_URL}/api/statistics/training-load")
    result = response.json()
    data = result['data']
    
    print(f"总体负荷: {data['overall_load']:.2f}")
    print(f"总时长: {data['total_duration_seconds']:.1f}秒")
    print(f"数据点数: {data['data_points']}")
    print("各桨位负荷:")
    for seat, info in sorted(data['seat_loads'].items()):
        print(f"  {seat}号桨位:")
        print(f"    划桨次数: {info['total_strokes']}")
        print(f"    平均桨频: {info['avg_stroke_rate']:.2f}")
        print(f"    平均力量: {info['avg_force']:.2f}N")
        print(f"    负荷分数: {info['load_score']:.2f}")
    
    assert result['code'] == 200
    print("✓ 训练负荷统计通过")

def test_improvement_trend():
    print_section("11. 技术改进趋势")
    response = requests.get(f"{BASE_URL}/api/statistics/improvement")
    result = response.json()
    data = result['data']
    
    print(f"同步率改进: {data['sync_improvement']:.4f}")
    print(f"异常趋势: {data['anomaly_trend']}")
    print(f"总体改进: {data['overall_improvement']:.4f}")
    print(f"前半段平均同步率: {data['first_half_sync']:.4f}")
    print(f"后半段平均同步率: {data['second_half_sync']:.4f}")
    
    assert result['code'] == 200
    print("✓ 技术改进趋势通过")

def test_current_state():
    print_section("12. 当前训练状态")
    response = requests.get(f"{BASE_URL}/api/state/current")
    result = response.json()
    data = result['data']
    
    print(f"当前状态: {data['state']}")
    print(f"持续时间: {data['duration_seconds']}秒")
    print(f"待处理建议: {len(data['pending_suggestions'])}条")
    print(f"当前异常数: {len(data['current_anomalies'])}条")
    
    if data['pending_suggestions']:
        print("建议:")
        for s in data['pending_suggestions']:
            print(f"  - {s}")
    
    assert result['code'] == 200
    print("✓ 当前状态查询通过")

def test_sync_trend():
    print_section("13. 同步率趋势")
    response = requests.get(f"{BASE_URL}/api/statistics/sync-trend?limit=20")
    result = response.json()
    data = result['data']
    
    print(f"数据点数: {data['count']}")
    print(f"平均整体同步率: {data['averages']['overall_sync_rate']:.4f}")
    print(f"平均桨频同步: {data['averages']['stroke_rate_sync']:.4f}")
    print(f"平均角度同步: {data['averages']['angle_sync']:.4f}")
    print(f"平均力量同步: {data['averages']['force_sync']:.4f}")
    
    assert result['code'] == 200
    print("✓ 同步率趋势查询通过")

def test_realtime():
    print_section("14. 实时数据")
    response = requests.get(f"{BASE_URL}/api/statistics/realtime")
    result = response.json()
    
    print(f"状态码: {result['code']}")
    print(f"消息: {result['message']}")
    
    if result['code'] == 200:
        data = result['data']
        if data.get('sync_rate'):
            print(f"同步率: {data['sync_rate']['overall_sync_rate']:.4f}")
        print(f"活跃桨位: {data['active_seats']}")
        print(f"最新数据桨位: {list(data['latest_data'].keys())}")
        print("✓ 实时数据查询通过")
    else:
        print(f"错误: {result['message']}")

def test_overview():
    print_section("15. 训练概览")
    response = requests.get(f"{BASE_URL}/api/statistics/overview")
    result = response.json()
    data = result['data']
    
    print(f"当前状态: {data['current_state']['state']}")
    if data.get('sync_rate'):
        print(f"当前同步率: {data['sync_rate']['overall_sync_rate']:.4f}")
    print(f"平均同步率: {data.get('avg_sync_rate', 'N/A')}")
    print(f"在线设备: {data['online_devices']}/{data['total_devices']}")
    print(f"近期异常数: {data['recent_anomalies_count']}")
    
    assert result['code'] == 200
    print("✓ 训练概览通过")

def test_suggestions():
    print_section("16. 改进建议")
    response = requests.get(f"{BASE_URL}/api/state/suggestions")
    result = response.json()
    data = result['data']
    
    print(f"当前状态: {data['current_state']}")
    print(f"待处理建议: {len(data['pending_suggestions'])}条")
    print(f"近期建议: {len(data['recent_suggestions'])}条")
    
    if data['recent_suggestions']:
        print("最近建议:")
        for s in data['recent_suggestions'][:5]:
            print(f"  - [{s['type']}] {s['suggestion']}")
    
    assert result['code'] == 200
    print("✓ 改进建议查询通过")

def test_summary():
    print_section("17. 训练总结")
    response = requests.get(f"{BASE_URL}/api/state/summary")
    result = response.json()
    data = result['data']
    
    if data.get('sync_statistics'):
        ss = data['sync_statistics']
        print(f"同步率统计: 平均={ss['avg']:.4f}, 最低={ss['min']:.4f}, 最高={ss['max']:.4f}")
    
    if data.get('anomaly_summary'):
        print("异常总结:")
        for atype, info in data['anomaly_summary'].items():
            print(f"  {atype}: {info['count']}次, 最大严重度={info['max_severity']:.2f}")
    
    assert result['code'] == 200
    print("✓ 训练总结通过")

def test_end_training():
    print_section("18. 结束训练")
    response = requests.post(f"{BASE_URL}/api/state/end-training")
    result = response.json()
    data = result['data']
    
    print(f"最终状态: {data['state']}")
    print(f"训练总结:")
    for s in data['suggestions']:
        print(f"  {s}")
    
    assert result['code'] == 200
    print("✓ 结束训练通过")

def main():
    print("\n" + "="*60)
    print("  赛艇训练数据实时分析 API 服务测试")
    print("="*60)
    
    try:
        test_health()
        test_reset()
        test_telemetry_report()
        test_devices()
        test_alignment()
        test_sync_rate()
        test_anomaly_detection()
        test_anomaly_history()
        test_stability_ranking()
        test_training_load()
        test_improvement_trend()
        test_current_state()
        test_sync_trend()
        test_realtime()
        test_overview()
        test_suggestions()
        test_summary()
        test_end_training()
        
        print("\n" + "="*60)
        print("  ✓ 所有测试通过！")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
