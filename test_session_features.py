#!/usr/bin/env python3
import requests
import time
import random
import json
import sys
import subprocess
import signal

BASE_URL = "http://localhost:9801"

server_process = None


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def kill_port_process(port):
    try:
        result = subprocess.run(
            ["lsof", "-t", "-i", f":{port}"],
            capture_output=True, text=True
        )
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            if pid:
                try:
                    subprocess.run(["kill", "-9", pid], capture_output=True)
                    print(f"  已终止进程 {pid} 占用端口 {port}")
                except:
                    pass
        time.sleep(1)
    except:
        pass


def start_server():
    global server_process
    print("启动服务器...")
    
    kill_port_process(9801)
    
    server_log = open("server_log.txt", "w")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "rowing_api.main:app", "--host", "0.0.0.0", "--port", "9801"],
        stdout=server_log,
        stderr=server_log
    )
    time.sleep(5)
    print("服务器已启动")
    
    print("等待服务器就绪...")
    last_error = None
    last_response = None
    for i in range(15):
        if server_process.poll() is not None:
            print(f"服务器进程已退出，代码: {server_process.returncode}")
            server_log.close()
            with open("server_log.txt", "r") as f:
                print("服务器日志:")
                print(f.read())
            raise RuntimeError("服务器启动失败")
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            last_response = f"status={response.status_code}, text={response.text[:100]}"
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('code') == 200:
                        print(f"服务器在第 {i+1} 次尝试时就绪")
                        return
                except:
                    last_error = f"JSON解析失败: {response.text[:100]}"
        except Exception as e:
            last_error = str(e)
        time.sleep(1)
    
    server_log.close()
    print(f"警告：服务器可能未完全就绪，最后错误: {last_error}")
    print(f"最后响应: {last_response}")
    with open("server_log.txt", "r") as f:
        print("服务器日志:")
        print(f.read()[-1000:])


def stop_server():
    global server_process
    if server_process:
        print("停止服务器...")
        server_process.send_signal(signal.SIGINT)
        server_process.wait()
        print("服务器已停止")


def generate_telemetry_data(session_id, base_ts, seat, stroke_rate=30, angle=45, force=150):
    return {
        "device_id": f"sensor_{session_id}_seat_{seat}",
        "seat_position": seat,
        "timestamp": base_ts,
        "stroke_rate": stroke_rate + random.uniform(-0.3, 0.3),
        "entry_angle": angle + random.uniform(-0.5, 0.5),
        "pull_force": force + random.uniform(-3, 3),
        "hull_acceleration": 0.5 + random.uniform(-0.1, 0.1)
    }


def test_health_check():
    print_section("1. 健康检查")
    response = requests.get(f"{BASE_URL}/health")
    result = response.json()
    print(f"状态码: {result['code']}")
    print(f"服务状态: {result['data']['status']}")
    assert result['code'] == 200
    assert result['data']['status'] == 'healthy'
    print("✓ 健康检查通过")


def test_multi_session_isolation():
    print_section("2. 多会话隔离测试")
    
    session_ids = []
    for i in range(3):
        response = requests.post(f"{BASE_URL}/api/session/create", json={
            "team_id": f"team_{i + 1}",
            "boat_id": f"boat_{i + 1}",
            "session_name": f"训练会话_{i + 1}",
            "seat_positions": [1, 2, 3, 4]
        })
        result = response.json()
        assert result['code'] == 200
        session_id = result['data']['session_id']
        session_ids.append(session_id)
        print(f"  创建会话 {i + 1}: {session_id}")
    
    assert len(session_ids) == 3
    assert len(set(session_ids)) == 3
    
    response = requests.get(f"{BASE_URL}/api/session/list")
    result = response.json()
    assert result['code'] == 200
    assert result['data']['count'] >= 3
    assert len(result['data']['sessions']) >= 3
    print(f"  会话列表包含 {result['data']['count']} 个会话")
    
    for i, session_id in enumerate(session_ids):
        base_ts = int(time.time() * 1000) + i * 100000
        for batch in range(10):
            batch_data = []
            for seat in range(1, 5):
                base_rate = 28 + i * 2
                base_angle = 43 + i * 2
                base_force = 140 + i * 10
                batch_data.append(generate_telemetry_data(
                    session_id, base_ts + batch * 200, seat,
                    base_rate, base_angle, base_force
                ))
            
            response = requests.post(
                f"{BASE_URL}/api/telemetry/batch-report",
                params={"session_id": session_id},
                json=batch_data
            )
            result = response.json()
            assert result['code'] == 200
        
        response = requests.get(
            f"{BASE_URL}/api/telemetry/latest/1",
            params={"session_id": session_id, "limit": 5}
        )
        result = response.json()
        assert result['code'] == 200
        assert result['data']['session_id'] == session_id
        assert result['data']['seat_position'] == 1
        assert len(result['data']['data']) > 0
        
        force_values = [d['pull_force'] for d in result['data']['data']]
        avg_force = sum(force_values) / len(force_values)
        expected_min = 140 + i * 10 - 10
        expected_max = 140 + i * 10 + 10
        assert expected_min <= avg_force <= expected_max, f"会话{i + 1}力量值未隔离: {avg_force}"
        print(f"  会话 {i + 1} 数据隔离验证通过，平均力量: {avg_force:.1f}N")
    
    print("✓ 多会话隔离测试通过")
    return session_ids


def test_strategy_config_and_effectiveness():
    print_section("3. 教练策略配置与生效测试")
    
    response = requests.post(f"{BASE_URL}/api/strategy/create", json={
        "boat_id": "boat_strategy_test",
        "stroke_rate_target_min": 28.0,
        "stroke_rate_target_max": 32.0,
        "entry_angle_tolerance": 3.0,
        "force_balance_weight": 2.0,
        "offline_threshold_ms": 8000,
        "rhythm_stability_threshold": 0.1,
        "consecutive_anomaly_threshold": 2,
        "sync_score_threshold": 0.8
    })
    result = response.json()
    assert result['code'] == 200
    strategy_id = result['data']['strategy_id']
    print(f"  创建策略: {strategy_id}")
    
    response = requests.get(f"{BASE_URL}/api/strategy/list")
    result = response.json()
    assert result['code'] == 200
    assert any(s['strategy_id'] == strategy_id for s in result['data']['strategies'])
    print("  策略列表查询通过")
    
    response = requests.put(f"{BASE_URL}/api/strategy/{strategy_id}", json={
        "boat_id": "boat_strategy_test",
        "stroke_rate_target_min": 29.0,
        "stroke_rate_target_max": 31.0,
        "entry_angle_tolerance": 2.5,
        "force_balance_weight": 2.5,
        "offline_threshold_ms": 6000,
        "rhythm_stability_threshold": 0.08,
        "consecutive_anomaly_threshold": 2,
        "sync_score_threshold": 0.85
    })
    result = response.json()
    assert result['code'] == 200
    assert result['data']['config']['stroke_rate_target_min'] == 29.0
    print("  策略更新通过")
    
    response = requests.post(f"{BASE_URL}/api/session/create", json={
        "team_id": "team_strategy",
        "boat_id": "boat_strategy_test",
        "session_name": "策略测试会话"
    })
    result = response.json()
    session_id = result['data']['session_id']
    
    response = requests.post(f"{BASE_URL}/api/strategy/{strategy_id}/apply/{session_id}")
    result = response.json()
    assert result['code'] == 200
    assert result['data']['applied'] == True
    print(f"  策略 {strategy_id} 应用到会话 {session_id}")
    
    base_ts = int(time.time() * 1000)
    for batch in range(15):
        batch_data = []
        for seat in range(1, 5):
            rate = 35.0 if seat == 3 else 30.0
            angle = 55.0 if seat == 4 else 45.0
            force = 200.0 if seat == 2 else 150.0
            batch_data.append(generate_telemetry_data(
                session_id, base_ts + batch * 200, seat,
                rate, angle, force
            ))
        
        response = requests.post(
            f"{BASE_URL}/api/telemetry/batch-report",
            params={"session_id": session_id},
            json=batch_data
        )
        result = response.json()
        assert result['code'] == 200
    
    response = requests.get(
        f"{BASE_URL}/api/analysis/anomalies",
        params={"session_id": session_id, "limit": 50}
    )
    result = response.json()
    assert result['code'] == 200
    
    anomaly_types = [a['anomaly_type'] for a in result['data']['anomalies']]
    print(f"  检测到异常类型: {set(anomaly_types)}")
    
    has_stroke_rate_anomaly = any('stroke_rate' in t for t in anomaly_types)
    has_angle_anomaly = any('angle' in t for t in anomaly_types)
    has_force_anomaly = any('force' in t for t in anomaly_types)
    
    assert has_stroke_rate_anomaly, "桨频异常未检测到（策略应更严格）"
    assert has_angle_anomaly, "角度异常未检测到（策略应更严格）"
    assert has_force_anomaly, "力量异常未检测到（策略应更严格）"
    
    print("  策略生效：所有预期异常均被检测到")
    print("✓ 教练策略配置与生效测试通过")
    
    return session_id, strategy_id


def test_training_review():
    print_section("4. 训练复盘接口测试")
    
    response = requests.post(f"{BASE_URL}/api/strategy/create", json={
        "boat_id": "boat_review",
        "stroke_rate_target_min": 29.0,
        "stroke_rate_target_max": 31.0,
        "entry_angle_tolerance": 2.0,
        "force_balance_weight": 2.0,
        "offline_threshold_ms": 5000,
        "rhythm_stability_threshold": 0.08,
        "consecutive_anomaly_threshold": 2,
        "sync_score_threshold": 0.85
    })
    result = response.json()
    strategy_id = result['data']['strategy_id']
    
    response = requests.post(f"{BASE_URL}/api/session/create", json={
        "team_id": "team_review",
        "boat_id": "boat_review",
        "session_name": "复盘测试会话"
    })
    result = response.json()
    session_id = result['data']['session_id']
    print(f"  创建复盘会话: {session_id}")
    
    response = requests.post(f"{BASE_URL}/api/strategy/{strategy_id}/apply/{session_id}")
    result = response.json()
    assert result['data']['applied'] == True
    print(f"  严格策略已应用到复盘会话")
    
    base_ts = int(time.time() * 1000)
    phase_configs = [
        (0, 20, 25, 42, 130),
        (20, 50, 32, 45, 160),
        (50, 80, 30, 44, 150),
        (80, 110, 35, 46, 170),
        (110, 140, 22, 40, 110),
    ]
    
    for batch in range(140):
        for start, end, rate, angle, force in phase_configs:
            if start <= batch < end:
                base_rate, base_angle, base_force = rate, angle, force
                break
        
        batch_data = []
        for seat in range(1, 5):
            sr = base_rate
            ag = base_angle
            fc = base_force
            
            if batch > 25 and batch < 65:
                if seat == 1:
                    sr = max(5, sr + 35)
                    ag = max(5, ag + 40)
                    fc = max(10, fc + 180)
                if seat == 2:
                    sr = max(5, sr * 0.3)
                    ag = max(5, ag * 0.3)
                    fc = max(10, fc * 0.3)
                if seat == 3:
                    sr = max(5, sr + 40)
                    ag = max(5, ag + 45)
                    fc = max(10, fc + 200)
                if seat == 4:
                    sr = max(5, sr * 0.25)
                    ag = max(5, ag * 0.25)
                    fc = max(10, fc * 0.25)
            
            if batch > 75 and batch < 115:
                if seat == 1:
                    sr = max(5, sr * 0.2)
                    ag = max(5, ag * 0.2)
                    fc = max(10, fc * 0.2)
                if seat == 2:
                    sr = max(5, sr + 35)
                    ag = max(5, ag + 45)
                    fc = max(10, fc + 180)
                if seat == 3:
                    sr = max(5, sr * 0.25)
                    ag = max(5, ag * 0.25)
                    fc = max(10, fc * 0.25)
                if seat == 4:
                    sr = max(5, sr + 40)
                    ag = max(5, ag + 50)
                    fc = max(10, fc + 200)
            
            batch_data.append(generate_telemetry_data(
                session_id, base_ts + batch * 200, seat, sr, ag, fc
            ))
        
        response = requests.post(
            f"{BASE_URL}/api/telemetry/batch-report",
            params={"session_id": session_id},
            json=batch_data,
            proxies=None
        )
        
        if batch in [30, 40, 50, 80, 90, 100]:
            try:
                result = response.json()
                if 'code' in result and result['code'] == 200 and result['data'].get('sync_rate'):
                    sync = result['data']['sync_rate']['overall_sync_rate']
                    print(f"  Batch {batch} sync rate: {sync:.4f}")
                else:
                    print(f"  Batch {batch} response: {response.text[:200]}")
            except Exception as e:
                print(f"  Batch {batch} error: {e}, response: {response.text[:200]}")
    
    response = requests.get(f"{BASE_URL}/api/review/{session_id}")
    print(f"  复盘接口状态码: {response.status_code}")
    print(f"  复盘接口响应: {response.text[:500]}")
    result = response.json()
    assert result['code'] == 200, f"复盘接口返回错误: {result}"
    review_data = result['data']
    
    required_fields = [
        'session_id', 'session_name', 'phase_sync_rate_curve', 'anomaly_duration_stats',
        'key_desync_segments', 'seat_technical_deficiencies', 'training_load_peaks',
        'strategy_effect_comparisons'
    ]
    for field in required_fields:
        assert field in review_data, f"复盘结果缺少字段: {field}"
    
    print(f"  分阶段同步率曲线点数: {len(review_data['phase_sync_rate_curve'])}")
    assert len(review_data['phase_sync_rate_curve']) > 0
    
    print(f"  异常持续时间统计类型数: {len(review_data['anomaly_duration_stats'])}")
    
    print(f"  关键失步片段数: {len(review_data['key_desync_segments'])}")
    assert len(review_data['key_desync_segments']) > 0
    
    print(f"  各桨位技术短板数: {len(review_data['seat_technical_deficiencies'])}")
    assert len(review_data['seat_technical_deficiencies']) > 0
    
    for deficiency in review_data['seat_technical_deficiencies']:
        assert 'seat_position' in deficiency
        assert 'primary_issue' in deficiency
        assert 'avg_severity' in deficiency
    
    print(f"  训练负荷峰值区间数: {len(review_data['training_load_peaks'])}")
    assert len(review_data['training_load_peaks']) > 0
    
    print("✓ 训练复盘接口测试通过")
    
    response = requests.get(f"{BASE_URL}/api/review/{session_id}/sync-curve")
    result = response.json()
    assert result['code'] == 200
    assert 'phase_sync_rate_curve' in result['data']
    print("  同步率曲线子接口通过")
    
    response = requests.get(f"{BASE_URL}/api/review/{session_id}/summary")
    result = response.json()
    assert result['code'] == 200
    assert 'overall_score' in result['data']
    print("  复盘摘要子接口通过")
    
    return session_id


def test_state_transition():
    print_section("5. 会话状态流转测试")
    
    response = requests.post(f"{BASE_URL}/api/session/create", json={
        "team_id": "team_state",
        "boat_id": "boat_state",
        "session_name": "状态流转测试"
    })
    result = response.json()
    session_id = result['data']['session_id']
    print(f"  创建状态测试会话: {session_id}")
    
    response = requests.get(
        f"{BASE_URL}/api/state/current",
        params={"session_id": session_id}
    )
    result = response.json()
    assert result['code'] == 200
    current_state = result['data']['state']
    assert current_state == 'normal_training', f"初始状态应为 normal_training，实际: {current_state}"
    print(f"  初始状态: {current_state}")
    
    response = requests.post(
        f"{BASE_URL}/api/state/transition",
        params={
            "target_state": "posture_warning",
            "reason": "测试划姿预警",
            "session_id": session_id
        }
    )
    result = response.json()
    assert result['code'] == 200
    assert result['data']['current_state'] == 'posture_warning'
    print("  状态切换到 posture_warning 成功")
    
    response = requests.get(
        f"{BASE_URL}/api/state/history",
        params={"session_id": session_id}
    )
    result = response.json()
    assert result['code'] == 200
    assert len(result['data']['history']) >= 2
    states = [h['state'] for h in result['data']['history']]
    assert 'normal_training' in states
    assert 'posture_warning' in states
    print(f"  状态历史记录数: {len(result['data']['history'])}")
    
    for state in ['technical_adjustment', 'rest_recovery', 'training_ended']:
        response = requests.post(
            f"{BASE_URL}/api/state/transition",
            params={
                "target_state": state,
                "reason": f"测试{state}",
                "session_id": session_id
            }
        )
        result = response.json()
        assert result['code'] == 200
        assert result['data']['current_state'] == state
        print(f"  状态切换到 {state} 成功")
    
    response = requests.get(
        f"{BASE_URL}/api/state/history",
        params={"session_id": session_id}
    )
    result = response.json()
    states = [h['state'] for h in result['data']['history']]
    expected_states = ['normal_training', 'posture_warning', 'technical_adjustment', 'rest_recovery', 'training_ended']
    for state in expected_states:
        assert state in states, f"状态历史缺少 {state}"
    
    print("✓ 会话状态流转测试通过")
    return session_id


def test_real_time_intervention():
    print_section("6. 实时干预建议测试")
    
    response = requests.post(f"{BASE_URL}/api/session/create", json={
        "team_id": "team_intervention",
        "boat_id": "boat_intervention",
        "session_name": "干预测试会话"
    })
    result = response.json()
    session_id = result['data']['session_id']
    print(f"  创建干预测试会话: {session_id}")
    
    response = requests.post(f"{BASE_URL}/api/strategy/create", json={
        "boat_id": "boat_intervention",
        "stroke_rate_target_min": 29.0,
        "stroke_rate_target_max": 31.0,
        "entry_angle_tolerance": 2.0,
        "force_balance_weight": 2.0,
        "offline_threshold_ms": 5000,
        "rhythm_stability_threshold": 0.08,
        "consecutive_anomaly_threshold": 3,
        "sync_score_threshold": 0.8
    })
    result = response.json()
    strategy_id = result['data']['strategy_id']
    
    response = requests.post(f"{BASE_URL}/api/strategy/{strategy_id}/apply/{session_id}")
    result = response.json()
    assert result['data']['applied'] == True
    
    base_ts = int(time.time() * 1000)
    for batch in range(20):
        batch_data = []
        for seat in range(1, 5):
            rate = 45.0 if seat == 3 else 30.0
            angle = 60.0 if seat == 4 else 45.0
            force = 250.0 if seat == 2 else 150.0
            batch_data.append(generate_telemetry_data(
                session_id, base_ts + batch * 200, seat, rate, angle, force
            ))
        
        response = requests.post(
            f"{BASE_URL}/api/telemetry/batch-report",
            params={"session_id": session_id},
            json=batch_data
        )
    
    response = requests.get(f"{BASE_URL}/api/intervention/{session_id}")
    result = response.json()
    assert result['code'] == 200
    intervention_data = result['data']
    
    assert 'session_id' in intervention_data
    assert 'current_state' in intervention_data
    assert 'consecutive_anomaly_count' in intervention_data
    assert 'seat_suggestions' in intervention_data
    assert 'recommended_state_transition' in intervention_data
    
    print(f"  连续异常计数: {intervention_data['consecutive_anomaly_count']}")
    print(f"  建议状态: {intervention_data['recommended_state_transition']}")
    print(f"  分桨位建议数: {len(intervention_data['seat_suggestions'])}")
    
    for suggestion in intervention_data['seat_suggestions']:
        assert 'seat_position' in suggestion
        assert 'action_type' in suggestion
        assert 'description' in suggestion
        assert 'urgency' in suggestion
        print(f"    桨位{suggestion['seat_position']}: {suggestion['description']}")
    
    assert len(intervention_data['seat_suggestions']) > 0
    
    if intervention_data['recommended_state_transition']:
        response = requests.post(
            f"{BASE_URL}/api/intervention/{session_id}/execute",
            params={"target_state": intervention_data['recommended_state_transition']}
        )
        result = response.json()
        assert result['code'] == 200
        print(f"  执行状态切换到 {intervention_data['recommended_state_transition']} 成功")
    
    response = requests.post(f"{BASE_URL}/api/intervention/{session_id}/acknowledge")
    result = response.json()
    assert result['code'] == 200
    print("  干预建议确认成功")
    
    print("✓ 实时干预建议测试通过")
    return session_id


def test_backward_compatibility():
    print_section("7. 现有接口兼容性测试")
    
    response = requests.post(f"{BASE_URL}/api/state/reset")
    result = response.json()
    assert result['code'] == 200
    print("  重置全局数据")
    
    base_ts = int(time.time() * 1000)
    for batch in range(10):
        batch_data = []
        for seat in range(1, 5):
            batch_data.append(generate_telemetry_data(
                "default", base_ts + batch * 200, seat, 30, 45, 150
            ))
        
        response = requests.post(f"{BASE_URL}/api/telemetry/batch-report", json=batch_data)
        result = response.json()
        assert result['code'] == 200
        assert 'session_id' not in result['data'] or result['data']['session_id'] is None
        assert result['data']['sync_rate'] is not None
    
    response = requests.get(f"{BASE_URL}/api/analysis/sync-rate")
    result = response.json()
    assert result['code'] == 200
    assert result['data']['session_id'] is None
    assert 'overall_sync_rate' in result['data']
    print("  同步率查询（无session_id）通过")
    
    response = requests.get(f"{BASE_URL}/api/statistics/overview")
    result = response.json()
    assert result['code'] == 200
    assert result['data']['session_id'] is None
    assert 'sync_rate' in result['data']
    print("  概览查询（无session_id）通过")
    
    response = requests.get(f"{BASE_URL}/api/state/current")
    result = response.json()
    assert result['code'] == 200
    assert result['data']['session_id'] is None
    assert 'state' in result['data']
    print("  状态查询（无session_id）通过")
    
    response = requests.get(f"{BASE_URL}/api/telemetry/devices")
    result = response.json()
    assert result['code'] == 200
    assert result['data']['session_id'] is None
    print("  设备状态查询（无session_id）通过")
    
    print("✓ 现有接口兼容性测试通过")


def run_all_tests():
    try:
        test_health_check()
        session_ids = test_multi_session_isolation()
        strategy_session_id, strategy_id = test_strategy_config_and_effectiveness()
        review_session_id = test_training_review()
        state_session_id = test_state_transition()
        intervention_session_id = test_real_time_intervention()
        test_backward_compatibility()
        
        print("\n" + "=" * 60)
        print("  ✓ 所有会话功能测试通过！")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    start_server()
    try:
        run_all_tests()
    finally:
        stop_server()
