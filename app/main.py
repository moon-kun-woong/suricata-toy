from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import asyncio
from pathlib import Path
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.model.alert import Alert
from app.model.suricata_status import SuricataStatus
from app.model.rule_update import RuleUpdate
from app.service.suricata_manager import SuricataManager
from app.util.logger import monitor_logs, alert_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(monitor_logs())
    yield
    monitor_task.cancel()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "running",
        "suricata_status": SuricataManager.is_running()
    }

@app.get("/status", response_model=SuricataStatus)
async def get_suricata_status():
    is_running = SuricataManager.is_running()
    pid = SuricataManager.get_pid() if is_running else None
    
    return SuricataStatus(
        is_running=is_running,
        pid=pid,
        uptime=None
    )

@app.post("/control/start")
async def start_suricata():
    if SuricataManager.is_running():
        raise HTTPException(status_code=400, detail="Suricata is already running")
    
    success = await SuricataManager.start()
    if success:
        return {"message": "Suricata started successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start Suricata")

@app.post("/control/stop")
async def stop_suricata():
    if not SuricataManager.is_running():
        raise HTTPException(status_code=400, detail="Suricata is not running")
    
    success = await SuricataManager.stop()
    if success:
        return {"message": "Suricata stopped successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop Suricata")

@app.get("/alerts", response_model=List[Alert])
async def get_alerts(
    limit: int = 100,
    severity: Optional[int] = None,
    src_ip: Optional[str] = None,
    dest_ip: Optional[str] = None
):
    alerts = alert_cache[-limit:]
    
    # 필터링
    if severity is not None:
        alerts = [a for a in alerts if a.alert_severity == severity]
    if src_ip:
        alerts = [a for a in alerts if a.src_ip == src_ip]
    if dest_ip:
        alerts = [a for a in alerts if a.dest_ip == dest_ip]
    
    return alerts

@app.post("/rules/add")
async def add_rule(rule: RuleUpdate):
    rule_path = Path(f"{settings.SURICATA_RULES_PATH}/{rule.rule_file}")
    
    try:
        with open(rule_path, "a") as f:
            f.write(f"\n{rule.rule_content}\n")
        
        success = await SuricataManager.reload_rules()
        
        if success:
            return {"message": "Rule added and reloaded successfully"}
        else:
            return {"message": "Rule added but reload failed"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)