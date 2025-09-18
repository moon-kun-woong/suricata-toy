# Suricata Monitor API

Suricata와 FastAPI를 통합한 최소한의 네트워크 모니터링 API 서버임임

## 주요 기능

- Suricata 프로세스 상태 모니터링
- 실시간 알림 로그 파싱 및 캐싱
- Suricata 규칙 관리 (추가/리로드)
- RESTful API 제공

## 설치 및 실행

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. Suricata 설치 (Ubuntu/Debian):
```bash
sudo apt-get install suricata
sudo suricata-update
```

3. 서버 실행:
```bash
python -m app.main
```

4. 클라이언트 테스트:
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

`app/core/config.py`에서 로그 파일 경로 및 규칙 디렉토리를 수정가능능

## 주의사항

- 이 프로젝트는 최소한의 구현임임
- 실제 운영 환경에서는 추가적인 보안 및 에러 처리가 필요
- Suricata 로그 파일 경로를 시스템에 맞게 수정
