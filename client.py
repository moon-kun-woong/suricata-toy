import requests
import json
from typing import Dict, Any

class SuricataClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def get_status(self) -> Dict[str, Any]:
        """Suricata 상태 조회"""
        response = requests.get(f"{self.base_url}/status")
        return response.json()
    
    def get_alerts(self, limit: int = 100) -> list:
        """최근 알림 조회"""
        response = requests.get(
            f"{self.base_url}/alerts",
            params={"limit": limit}
        )
        return response.json()
    
    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """통계 조회"""
        response = requests.get(
            f"{self.base_url}/alerts/stats",
            params={"hours": hours}
        )
        return response.json()
    
    def add_rule(self, rule_content: str) -> Dict[str, Any]:
        """규칙 추가"""
        response = requests.post(
            f"{self.base_url}/rules/add",
            json={"rule_content": rule_content}
        )
        return response.json()

# 사용 예제
if __name__ == "__main__":
    client = SuricataClient()
    
    # 상태 확인
    print("Suricata Status:", client.get_status())
    
    # 최근 알림 조회
    alerts = client.get_alerts(limit=10)
    print(f"Recent Alerts: {len(alerts)} found")
    
    # 규칙 추가 예제
    client.add_rule('alert tcp any any -> any any (msg:"Test rule"; sid:1000001; rev:1;)')