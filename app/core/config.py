from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Suricata Monitor API"
    
    SURICATA_LOG_PATH: Path = Path("/var/log/suricata/eve.json")
    SURICATA_RULES_PATH: Path = Path("/etc/suricata/rules")

settings = Settings()