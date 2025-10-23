#!/bin/bash

# Suricata 자동 재시작 스크립트
# 사용법: sudo ./restart_suricata.sh

echo "Suricata 클린 재시작 시작..."

# 1. 모든 Suricata 프로세스 강제 종료
echo "[1/5] Suricata 프로세스 강제 종료 중..."
sudo killall -9 suricata 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✓ Suricata 프로세스 종료 완료"
else
    echo "  ℹ Suricata 프로세스가 실행 중이 아닙니다"
fi
sleep 1

# 2. PID 및 소켓 파일 삭제
echo "[2/5] PID 및 소켓 파일 삭제 중..."
sudo rm -f /var/run/suricata.pid /var/run/suricata-command.socket
echo "  ✓ PID 및 소켓 파일 삭제 완료"

# 3. 로그 파일 초기화
echo "[3/5] 로그 파일 초기화 중..."
sudo rm -f /var/log/suricata/eve.json
sudo touch /var/log/suricata/eve.json
sudo chmod 644 /var/log/suricata/eve.json
echo "  ✓ eve.json 초기화 완료"

# 4. Suricata 재시작
echo "[4/5] Suricata 시작 중..."
sudo suricata -c /etc/suricata/suricata.yaml -i eth0 -D

if [ $? -eq 0 ]; then
    echo "  ✓ Suricata 시작 명령 실행 완료"
else
    echo "  ✗ Suricata 시작 실패!"
    exit 1
fi

# 초기화 대기
sleep 5

# 5. 상태 확인
echo "[5/5] Suricata 상태 확인 중..."
SURICATA_PID=$(pgrep -f suricata)

if [ -n "$SURICATA_PID" ]; then
    echo "  ✓ Suricata 실행 중 (PID: $SURICATA_PID)"
    echo ""
    echo "최근 로그:"
    sudo tail -3 /var/log/suricata/suricata.log | grep -E "Engine started|Notice|Info"
    echo ""
    echo "=========================================="
    echo "✓ Suricata 재시작 성공!"
    echo "=========================================="
else
    echo "  ✗ Suricata 프로세스를 찾을 수 없습니다"
    echo ""
    echo "로그 확인:"
    sudo tail -10 /var/log/suricata/suricata.log
    echo ""
    echo "=========================================="
    echo "✗ Suricata 재시작 실패!"
    echo "=========================================="
    exit 1
fi
