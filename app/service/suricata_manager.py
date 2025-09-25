import subprocess
from typing import Optional

class SuricataManager:
    @staticmethod
    def is_running() -> bool:
        """Suricata 실행 상태 확인 (WSL에서)"""
        try:
            # WSL을 통해 Linux 명령어 실행 - pgrep -f 사용하여 전체 명령어 라인에서 검색
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
                # 여러 PID가 있을 경우 첫 번째 것을 사용
                pids = result.stdout.strip().split('\n')
                return int(pids[0]) if pids[0] else None
        except:
            pass
        return None
    
    @staticmethod
    async def start():
        """Suricata 시작 (WSL에서)"""
        try:
            subprocess.run(
                ["wsl", "sudo", "suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "eth0", "-D"],
                check=True
            )
            return True
        except:
            return False
    
    @staticmethod
    async def stop():
        """Suricata 중지 (WSL에서)"""
        try:
            # 먼저 SIGTERM으로 시도
            result = subprocess.run(
                ["wsl", "sudo", "pkill", "-f", "suricata"],
                capture_output=True,
                text=True
            )

            # 잠시 대기 후 프로세스가 여전히 실행 중이면 강제 종료
            import time
            time.sleep(1)

            # 여전히 실행 중인지 확인
            check_result = subprocess.run(
                ["wsl", "pgrep", "-f", "suricata"],
                capture_output=True,
                text=True
            )

            if check_result.returncode == 0:
                # 강제 종료 (SIGKILL)
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