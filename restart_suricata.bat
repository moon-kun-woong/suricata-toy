@echo off
REM Windows에서 WSL Suricata 재시작 스크립트 실행

echo Suricata 재시작 중...
wsl bash -c "sudo /mnt/c/project/suricata-toy/restart_suricata.sh"

pause
