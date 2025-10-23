import subprocess
from typing import Optional
import time

class SuricataManager:
    @staticmethod
    def is_running() -> bool:
        """Suricata 실행 상태 확인 (WSL에서)"""
        try:
            result = subprocess.run(
                ["wsl", "pgrep", "-f", "suricata"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def get_pid() -> Optional[int]:
        """Suricata PID 가져오기 (WSL에서)"""
        try:
            result = subprocess.run(
                ["wsl", "pgrep", "-f", "suricata"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                return int(pids[0]) if pids[0] else None
        except:
            pass
        return None
    
    @staticmethod
    async def start():
        """Suricata 시작 (WSL에서)"""
        try:
            # 먼저 실행 중인지 확인
            if SuricataManager.is_running():
                print("Suricata가 이미 실행 중입니다.")
                return True
            
            # stale pidfile 삭제
            subprocess.run(
                ["wsl", "sudo", "rm", "-f", "/var/run/suricata.pid"],
                capture_output=True
            )
            
            # Suricata 시작
            result = subprocess.run(
                ["wsl", "sudo", "suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "eth0", "-D"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("Suricata 시작 성공")
                return True
            else:
                print(f"Suricata 시작 실패: {result.stderr}")
                return False
        except Exception as e:
            print(f"Suricata 시작 오류: {e}")
            return False
    
    @staticmethod
    async def stop():
        """Suricata 중지 (WSL에서)"""
        try:
            result = subprocess.run(
                ["wsl", "sudo", "pkill", "-f", "suricata"],
                capture_output=True,
                text=True
            )
            time.sleep(1)

            check_result = subprocess.run(
                ["wsl", "pgrep", "-f", "suricata"],
                capture_output=True,
                text=True
            )

            if check_result.returncode == 0:
                subprocess.run(
                    ["wsl", "sudo", "pkill", "-9", "-f", "suricata"],
                    capture_output=True,
                    text=True
                )

            return True
        except Exception as e:
            print(f"Stop error: {e}")
            return False
    
    @staticmethod
    async def reload_rules():
        """Suricata 규칙 리로드 (WSL에서)"""
        try:
            result = subprocess.run(
                ["wsl", "pgrep", "-f", "suricata"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:  # 빈 문자열이 아닌 경우만 처리
                        subprocess.run(
                            ["wsl", "sudo", "kill", "-USR2", pid],
                            check=True
                        )
            return True
        except:
            return False