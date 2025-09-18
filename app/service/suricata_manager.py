import subprocess
from typing import Optional

class SuricataManager:
    @staticmethod
    def is_running() -> bool:
        """Suricata 실행 상태 확인 (WSL에서)"""
        try:
            # WSL을 통해 Linux 명령어 실행
            result = subprocess.run(
                ["wsl", "pgrep", "-x", "suricata"], 
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
                ["wsl", "pgrep", "-x", "suricata"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except:
            pass
        return None
    
    @staticmethod
    async def start():
        """Suricata 시작 (WSL에서)"""
        try:
            subprocess.run(
                ["wsl", "sudo", "suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "any", "-D"],
                check=True
            )
            return True
        except:
            return False
    
    @staticmethod
    async def stop():
        """Suricata 중지 (WSL에서)"""
        try:
            result = subprocess.run(
                ["wsl", "pgrep", "-x", "suricata"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                pid = result.stdout.strip()
                subprocess.run(
                    ["wsl", "sudo", "kill", pid],
                    check=True
                )
            return True
        except:
            return False
    
    @staticmethod
    async def reload_rules():
        """Suricata 규칙 리로드 (WSL에서)"""
        try:
            result = subprocess.run(
                ["wsl", "pgrep", "-x", "suricata"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                pid = result.stdout.strip()
                subprocess.run(
                    ["wsl", "sudo", "kill", "-USR2", pid],
                    check=True
                )
            return True
        except:
            return False