import json
import asyncio
import subprocess
from typing import Optional, List
from datetime import datetime

from app.model.alert import Alert
from app.core.config import settings

# 메모리 캐시
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
    """WSL 파일 모니터링"""
    global alert_cache
    
    # WSL 경로를 직접 문자열로 사용
    wsl_log_path = "/var/log/suricata/eve.json"
    print(f"로그 모니터링 시작: {wsl_log_path}")
    
    try:
        print("WSL 파일 모니터링 시작")
        
        # WSL 파일 직접 접근 테스트 (문자열 경로 사용)
        try:
            result = subprocess.run(
                ["wsl", "head", "-1", wsl_log_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("WSL 파일 접근 성공")
                print(f"첫 번째 라인: {result.stdout[:100]}...")
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
                        
                        # 새로운 라인들만 가져오기
                        new_lines = current_lines - last_lines_count
                        result = subprocess.run(
                            ["wsl", "tail", "-n", str(new_lines), wsl_log_path],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            lines = result.stdout.strip().split('\n')
                            
                            alert_found = False
                            for line in lines:
                                line = line.strip()
                                if line:
                                    # alert 이벤트만 처리하고 출력
                                    try:
                                        data = json.loads(line)
                                        event_type = data.get("event_type", "unknown")
                                        
                                        if event_type == "alert":
                                            alert_found = True
                                            alert = await parse_eve_log_line(line)
                                            if alert:
                                                alert_cache.append(alert)
                                                print(f"새 알림 발견: {alert.alert_signature} (심각도: {alert.alert_severity})")
                                                print(f"   - 출발지: {alert.src_ip}:{alert.src_port}")
                                                print(f"   - 목적지: {alert.dest_ip}:{alert.dest_port}")
                                                print(f"   - 현재 캐시: {len(alert_cache)}개")
                                                if len(alert_cache) > MAX_CACHE_SIZE:
                                                    alert_cache.pop(0)
                                    except json.JSONDecodeError:
                                        pass
                            
                            # alert가 없으면 간단히 표시
                            if not alert_found:
                                print(f"  → {new_lines}개 로그 처리 완료 (alert 없음)")
                        
                        last_lines_count = current_lines
                
                # 3초마다 체크
                await asyncio.sleep(3)
                
            except subprocess.TimeoutExpired:
                print("WSL 명령어 타임아웃, 재시도...")
                await asyncio.sleep(10)
            except Exception as e:
                print(f"로그 체크 오류: {e}")
                await asyncio.sleep(10)
                
    except Exception as e:
        print(f"로그 모니터링 치명적 오류: {e}")
        print("WSL 연결 문제일 가능성 높음")