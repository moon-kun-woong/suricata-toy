from app.util.clickhouse_client import clickhouse_client
from datetime import datetime, timedelta

def print_section(title):
    """섹션 헤더 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print_section("ClickHouse 데이터 조회 스크립트")
    
    if not clickhouse_client.connect():
        print("연결 실패!")
        return
    
    try:
        print_section("1. 전체 이벤트 수")
        result = clickhouse_client.client.query("SELECT count() FROM suricata.events")
        total_count = result.result_rows[0][0] if result.result_rows else 0
        print(f"전체 이벤트: {total_count:,}개")
        
        print_section("2. 이벤트 타입별 통계")
        query = """
        SELECT 
            event_type,
            count() as cnt,
            formatReadableQuantity(cnt) as readable
        FROM suricata.events
        GROUP BY event_type
        ORDER BY cnt DESC
        """
        result = clickhouse_client.client.query(query)
        if result.result_rows:
            print(f"{'이벤트 타입':<20} {'개수':>15} {'읽기 쉬운 형식':>20}")
            print("-" * 70)
            for row in result.result_rows:
                print(f"{row[0]:<20} {row[1]:>15,} {row[2]:>20}")
        else:
            print("데이터 없음")
        
        print_section("3. 최근 Alert 10개")
        query = """
        SELECT 
            timestamp,
            alert_signature,
            alert_severity,
            src_ip,
            src_port,
            dest_ip,
            dest_port
        FROM suricata.events
        WHERE event_type = 'alert'
        ORDER BY timestamp DESC
        LIMIT 10
        """
        result = clickhouse_client.client.query(query)
        if result.result_rows:
            for i, row in enumerate(result.result_rows, 1):
                print(f"\n[{i}] {row[0]}")
                print(f"    시그니처: {row[1]}")
                print(f"    심각도: {row[2]}")
                print(f"    {row[3]}:{row[4]} → {row[5]}:{row[6]}")
        else:
            print("Alert 없음")
        
        print_section("4. 시간대별 Alert 통계 (최근 24시간)")
        query = """
        SELECT 
            toStartOfHour(timestamp) as hour,
            count() as cnt
        FROM suricata.events
        WHERE event_type = 'alert'
          AND timestamp >= now() - INTERVAL 24 HOUR
        GROUP BY hour
        ORDER BY hour DESC
        LIMIT 24
        """
        result = clickhouse_client.client.query(query)
        if result.result_rows:
            print(f"{'시간':<20} {'Alert 수':>15}")
            print("-" * 70)
            for row in result.result_rows:
                print(f"{row[0]:<20} {row[1]:>15,}")
        else:
            print("최근 24시간 내 Alert 없음")
        
        print_section("5. 상위 공격 시그니처 TOP 10")
        query = """
        SELECT 
            alert_signature,
            count() as cnt,
            max(timestamp) as last_seen
        FROM suricata.events
        WHERE event_type = 'alert'
          AND alert_signature IS NOT NULL
        GROUP BY alert_signature
        ORDER BY cnt DESC
        LIMIT 10
        """
        result = clickhouse_client.client.query(query)
        if result.result_rows:
            print(f"{'순위':<6} {'발생횟수':>12} {'마지막 발생 시간':<25} 시그니처")
            print("-" * 70)
            for i, row in enumerate(result.result_rows, 1):
                print(f"{i:<6} {row[1]:>12,} {str(row[2]):<25} {row[0]}")
        else:
            print("Alert 없음")
        
        print_section("6. 상위 출발지 IP TOP 10")
        query = """
        SELECT 
            src_ip,
            count() as cnt,
            countIf(event_type = 'alert') as alert_cnt
        FROM suricata.events
        WHERE src_ip != '0.0.0.0'
        GROUP BY src_ip
        ORDER BY cnt DESC
        LIMIT 10
        """
        result = clickhouse_client.client.query(query)
        if result.result_rows:
            print(f"{'순위':<6} {'IP 주소':<20} {'전체 이벤트':>15} {'Alert 수':>15}")
            print("-" * 70)
            for i, row in enumerate(result.result_rows, 1):
                print(f"{i:<6} {row[0]:<20} {row[1]:>15,} {row[2]:>15,}")
        else:
            print("데이터 없음")
        
        print_section("7. HTTP 요청 통계")
        query = """
        SELECT 
            http_http_method as method,
            count() as cnt
        FROM suricata.events
        WHERE event_type = 'http'
          AND http_http_method IS NOT NULL
        GROUP BY method
        ORDER BY cnt DESC
        """
        result = clickhouse_client.client.query(query)
        if result.result_rows:
            print(f"{'HTTP 메소드':<15} {'요청 수':>15}")
            print("-" * 70)
            for row in result.result_rows:
                print(f"{row[0]:<15} {row[1]:>15,}")
        else:
            print("HTTP 데이터 없음")
        
        print_section("8. 데이터 저장 통계")
        query = """
        SELECT 
            formatReadableSize(sum(bytes_on_disk)) as disk_size,
            formatReadableSize(sum(data_compressed_bytes)) as compressed,
            formatReadableSize(sum(data_uncompressed_bytes)) as uncompressed,
            count() as parts
        FROM system.parts
        WHERE database = 'suricata' AND table = 'events' AND active
        """
        result = clickhouse_client.client.query(query)
        if result.result_rows:
            row = result.result_rows[0]
            print(f"디스크 사용량: {row[0]}")
            print(f"압축된 크기: {row[1]}")
            print(f"압축 전 크기: {row[2]}")
            print(f"파티션 수: {row[3]}")
        
    except Exception as e:
        print(f"\n 오류 발생: {e}")
    
    finally:
        clickhouse_client.disconnect()
        print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
