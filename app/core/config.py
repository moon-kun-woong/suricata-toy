from pathlib import Path
import os

class Settings:
    PROJECT_NAME: str = "Suricata Monitor API"
    
    SURICATA_LOG_PATH: Path = Path("/var/log/suricata/eve.json")
    SURICATA_RULES_PATH: Path = Path("/etc/suricata/rules")
    
    # ClickHouse 설정
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "qwe123")
    CLICKHOUSE_DATABASE: str = os.getenv("CLICKHOUSE_DATABASE", "suricata")
    CLICKHOUSE_TABLE: str = "events"
    
    # 배치 삽입 설정
    CLICKHOUSE_BATCH_SIZE: int = 100
    CLICKHOUSE_BATCH_INTERVAL: int = 5  # seconds

settings = Settings()