import json
import asyncio
import subprocess
from typing import Optional, List
from datetime import datetime

from app.model.alert import Alert
from app.core.config import settings
from app.util.clickhouse_client import clickhouse_client

# 메모리 캐시 (임시로 만듦듦) - API 응답용
alert_cache: List[Alert] = []
MAX_CACHE_SIZE = 1000

async def parse_eve_log_line(line: str) -> Optional[Alert]:
    """EVE JSON 로그 라인 파싱"""
    try:
        line = line.strip()
        if not line:
            return None
            
        data = json.loads(line)
        
        # alert 이벤트만
        if data.get("event_type") == "alert":
            alert = Alert(
                timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
                event_type=data["event_type"],
                src_ip=data.get("src_ip", "unknown"),
                src_port=data.get("src_port"),
                dest_ip=data.get("dest_ip", "unknown"),
                dest_port=data.get("dest_port"),
                proto=data.get("proto", "unknown"),
                alert_signature=data.get("alert", {}).get("signature"),
                alert_severity=data.get("alert", {}).get("severity"),
                payload=data.get("payload")
            )
            return alert
            
    except json.JSONDecodeError:
        pass
    except Exception as e:
        print(f"예상치 못한 파싱 오류: {e}")
    
    return None

async def monitor_logs():
    """WSL 파일 모니터링 및 ClickHouse 저장"""
    global alert_cache
    
    # WSL 경로를 직접 문자열로 사용
    wsl_log_path = "/var/log/suricata/eve.json"
    print(f"로그 모니터링 시작: {wsl_log_path}")
    print(f"ClickHouse 활성화")
    
    try:
        try:
            result = subprocess.run(
                ["wsl", "head", "-1", wsl_log_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                pass
            else:
                print(f"WSL 파일 접근 실패: {result.stderr}")
                return
        except Exception as e:
            print(f"WSL 연결 오류: {e}")
            return
        
        last_lines_count = 0
        
        while True:
            try:
                # WSL을 통해 파일의 총 라인 수 확인
                result = subprocess.run(
                    ["wsl", "wc", "-l", wsl_log_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    current_lines = int(result.stdout.split()[0])
                    
                    if current_lines > last_lines_count:
                        print(f"새로운 로그 라인 감지: {last_lines_count} -> {current_lines}")
                        
                        new_lines = current_lines - last_lines_count
                        result = subprocess.run(
                            ["wsl", "tail", "-n", str(new_lines), wsl_log_path],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            lines = result.stdout.strip().split('\n')
                            
                            alert_count = 0
                            total_events = 0
                            
                            for line in lines:
                                line = line.strip()
                                if line:
                                    try:
                                        data = json.loads(line)
                                        event_type = data.get("event_type", "unknown")
                                        total_events += 1
                                        
                                        # ClickHouse에 모든 이벤트 저장
                                        await clickhouse_client.add_to_batch(data)
                                        
                                        # alert 이벤트는 메모리 캐시에도 저장 (API 응답용)
                                        if event_type == "alert":
                                            alert_count += 1
                                            alert = await parse_eve_log_line(line)
                                            if alert:
                                                alert_cache.append(alert)
                                                print(f"  → Alert: {alert.alert_signature} (심각도: {alert.alert_severity})")
                                                print(f"     출발지: {alert.src_ip}:{alert.src_port} → 목적지: {alert.dest_ip}:{alert.dest_port}")
                                                if len(alert_cache) > MAX_CACHE_SIZE:
                                                    alert_cache.pop(0)
                                    
                                    except json.JSONDecodeError:
                                        pass
                            
                            if total_events > 0:
                                print(f" {total_events}개 이벤트 처리 완료 (Alert: {alert_count}개)")
                        
                        last_lines_count = current_lines
                
                # 3초마다 체크
                await asyncio.sleep(3)
                
            except subprocess.TimeoutExpired:
                print("WSL 명령어 타임아웃...")
                await asyncio.sleep(10)
            except Exception as e:
                print(f"log monitor error: {e}")
                await asyncio.sleep(10)
                
    except Exception as e:
        print(f"log monitor error: {e}")