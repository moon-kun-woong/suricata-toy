"""
ClickHouse 데이터베이스 초기화 스크립트

이 스크립트는 ClickHouse 데이터베이스와 테이블을 수동으로 초기화합니다.
일반적으로 FastAPI 애플리케이션 시작 시 자동으로 초기화되지만,
별도로 실행할 필요가 있을 때 사용하세요.
"""

from app.util.clickhouse_client import clickhouse_client

def main():
    print("=" * 60)
    print("ClickHouse 데이터베이스 초기화 스크립트")
    print("=" * 60)
    
    if not clickhouse_client.connect():
        print("연결 실패")
        return
    
    if clickhouse_client.ensure_database():
        print("초기화 완료")
    else:
        print("초기화 실패")
        return
    
    print("\n3. ClickHouse Disconnected")
    clickhouse_client.disconnect()
    
    print("\n" + "=" * 60)
    print("초기화 완료")
    print("=" * 60)

if __name__ == "__main__":
    main()
