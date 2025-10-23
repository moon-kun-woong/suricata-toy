# Suricata Monitor API

Suricata와 FastAPI를 통합한 네트워크 모니터링 API 서버

## 주요 기능

- Suricata 프로세스 상태 모니터링
- 실시간 로그 파싱 및 **ClickHouse DB 저장**
- 모든 Suricata 이벤트 타입 수집 (alert, flow, http, dns, tls 등)
- 메모리 캐시를 통한 빠른 Alert 조회
- Suricata 규칙 관리 (추가/리로드)
- RESTful API 제공

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. ClickHouse 설치 (선택사항이지만 권장)

**Windows:**
```powershell
# Docker를 사용하는 경우 (권장)
docker run -d --name clickhouse-server -p 8123:8123 -p 9000:9000 -e CLICKHOUSE_DB=suricata -e CLICKHOUSE_PASSWORD=qwe123 clickhouse/clickhouse-server
```

**Ubuntu/Debian:**
```bash
sudo apt-get install -y apt-transport-https ca-certificates dirmngr
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 8919F6BD2B48D754
echo "deb https://packages.clickhouse.com/deb stable main" | sudo tee /etc/apt/sources.list.d/clickhouse.list
sudo apt-get update
sudo apt-get install -y clickhouse-server clickhouse-client
sudo service clickhouse-server start
```

### 3. 환경 변수 설정
```bash
# .env.example을 .env로 복사
cp .env.example .env

# 필요시 ClickHouse 연결 정보 수정
# CLICKHOUSE_HOST=localhost
# CLICKHOUSE_PORT=8123
# CLICKHOUSE_USER=default
# CLICKHOUSE_PASSWORD=
```

### 4. ClickHouse 초기화 (선택사항)
```bash
# FastAPI 서버가 자동으로 초기화하지만, 수동으로 실행하려면:
python init_clickhouse.py
```

### 5. Suricata 설치 (WSL Ubuntu/Debian)
```bash
sudo apt-get install suricata
sudo suricata-update
```

### 6. 서버 실행
```bash
python -m app.main
```

### 7. 클라이언트 테스트
```bash
python client.py
```

## API 엔드포인트

- `GET /` - 서비스 상태 확인
- `GET /status` - Suricata 상태 조회
- `POST /control/start` - Suricata 시작
- `POST /control/stop` - Suricata 중지
- `GET /alerts` - 알림 목록 조회 (필터링 지원)
- `POST /rules/add` - 규칙 추가

## 설정

### 기본 설정
`app/core/config.py`에서 로그 파일 경로 및 규칙 디렉토리를 수정 가능

### ClickHouse 설정
`.env` 파일을 통해 ClickHouse 연결 설정:
- `CLICKHOUSE_HOST`: ClickHouse 서버 주소 (기본값: localhost)
- `CLICKHOUSE_PORT`: ClickHouse HTTP 포트 (기본값: 8123)
- `CLICKHOUSE_USER`: 사용자명 (기본값: default)
- `CLICKHOUSE_PASSWORD`: 비밀번호
- `CLICKHOUSE_DATABASE`: 데이터베이스명 (기본값: suricata)

## 로그 저장 구조

### ClickHouse 테이블 스키마
- **테이블명**: `suricata.events`
- **파티션**: 월별 (`toYYYYMM(date)`)
- **TTL**: 90일 (자동 삭제)
- **저장 데이터**:
  - Alert 정보 (signature, severity, category 등)
  - Flow 정보 (패킷 수, 바이트 수, 세션 시간 등)
  - HTTP 정보 (hostname, URL, method, status 등)
  - DNS 정보 (query, response 등)
  - TLS 정보 (certificate, SNI 등)
  - 원본 JSON 데이터

### ClickHouse 쿼리 예시
```sql
-- 최근 Alert 조회
SELECT timestamp, alert_signature, src_ip, dest_ip 
FROM suricata.events 
WHERE event_type = 'alert' 
ORDER BY timestamp DESC 
LIMIT 10;

-- 시간대별 이벤트 통계
SELECT 
    toStartOfHour(timestamp) as hour,
    event_type,
    count() as cnt
FROM suricata.events
GROUP BY hour, event_type
ORDER BY hour DESC;

-- 상위 공격 시그니처
SELECT 
    alert_signature,
    count() as cnt
FROM suricata.events
WHERE event_type = 'alert'
GROUP BY alert_signature
ORDER BY cnt DESC
LIMIT 20;
```

## 주의사항

- ClickHouse가 설치되어 있지 않아도 API 서버는 작동하지만, 로그는 메모리 캐시에만 저장됩니다
- 실제 운영 환경에서는 추가적인 보안 및 에러 처리가 필요합니다
- Suricata는 WSL 환경에서 실행되어야 합니다
- ClickHouse 연결 실패 시 자동으로 로컬 캐시 모드로 전환됩니다
