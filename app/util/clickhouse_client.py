import clickhouse_connect
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from app.core.config import settings

class ClickHouseClient:
    """ClickHouse 클라이언트 관리"""
    
    def __init__(self):
        self.client: Optional[clickhouse_connect.driver.client.Client] = None
        self.batch_buffer: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        self.is_connected = False
    
    def connect(self) -> bool:
        """ClickHouse 연결"""
        try:
            self.client = clickhouse_connect.get_client(
                host=settings.CLICKHOUSE_HOST,
                port=settings.CLICKHOUSE_PORT,
                username=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD,
                database=settings.CLICKHOUSE_DATABASE
            )
            self.is_connected = True
            print(f"ClickHouse connected: {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}")
            return True
        except Exception as e:
            print(f"✗ ClickHouse 연결 실패: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """ClickHouse 연결 종료"""
        if self.client:
            try:
                self.client.close()
                self.is_connected = False
                print(" ClickHouse 연결 종료")
            except Exception as e:
                print(f"✗ ClickHouse 연결 종료 중 오류: {e}")
    
    def ensure_database(self):
        """데이터베이스가 없으면 생성"""
        try:
            if not self.client:
                self.connect()
            
            self.client.command(f"CREATE DATABASE IF NOT EXISTS {settings.CLICKHOUSE_DATABASE}")
            print(f"DB: {settings.CLICKHOUSE_DATABASE}")
            
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {settings.CLICKHOUSE_DATABASE}.{settings.CLICKHOUSE_TABLE}
            (
                timestamp DateTime64(6),
                event_type String,
                src_ip String,
                src_port UInt16,
                dest_ip String,
                dest_port UInt16,
                proto String,
                
                -- Alert 관련 필드
                alert_signature Nullable(String),
                alert_category Nullable(String),
                alert_severity Nullable(UInt8),
                alert_action Nullable(String),
                
                -- Flow 관련 필드
                flow_id Nullable(UInt64),
                flow_pkts_toserver Nullable(UInt32),
                flow_pkts_toclient Nullable(UInt32),
                flow_bytes_toserver Nullable(UInt64),
                flow_bytes_toclient Nullable(UInt64),
                flow_start Nullable(DateTime64(6)),
                flow_end Nullable(DateTime64(6)),
                flow_age Nullable(UInt32),
                flow_state Nullable(String),
                flow_reason Nullable(String),
                
                -- HTTP 관련 필드
                http_hostname Nullable(String),
                http_url Nullable(String),
                http_http_user_agent Nullable(String),
                http_http_method Nullable(String),
                http_protocol Nullable(String),
                http_status Nullable(UInt16),
                http_length Nullable(UInt32),
                
                -- DNS 관련 필드
                dns_type Nullable(String),
                dns_id Nullable(UInt16),
                dns_rrname Nullable(String),
                dns_rrtype Nullable(String),
                dns_rcode Nullable(String),
                
                -- TLS 관련 필드
                tls_subject Nullable(String),
                tls_issuerdn Nullable(String),
                tls_fingerprint Nullable(String),
                tls_sni Nullable(String),
                tls_version Nullable(String),
                
                -- 원본 JSON 데이터 (분석용)
                raw_json String,
                
                -- 인덱스 필드
                date Date DEFAULT toDate(timestamp)
            )
            ENGINE = MergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (event_type, timestamp, src_ip, dest_ip)
            TTL date + INTERVAL 90 DAY
            SETTINGS index_granularity = 8192
            """
            
            self.client.command(create_table_query)
            print(f" table checked: {settings.CLICKHOUSE_TABLE}")
            return True
            
        except Exception as e:
            print(f"✗ 데이터베이스/테이블 생성 실패: {e}")
            return False
    
    async def add_to_batch(self, event: Dict[str, Any]):
        """배치 버퍼에 이벤트 추가"""
        async with self.batch_lock:
            self.batch_buffer.append(event)
            
            if len(self.batch_buffer) >= settings.CLICKHOUSE_BATCH_SIZE:
                await self.flush_batch()
    
    async def flush_batch(self):
        """배치 버퍼의 데이터를 ClickHouse에 삽입"""
        async with self.batch_lock:
            if not self.batch_buffer:
                return
            
            if not self.is_connected:
                print("⚠ ClickHouse 연결 안됨, 배치 버퍼 유지")
                return
            
            try:
                rows_dict = []
                for event in self.batch_buffer:
                    row = self._prepare_row(event)
                    rows_dict.append(row)
                
                if not rows_dict:
                    return
                
                column_names = list(rows_dict[0].keys())
                
                data_to_insert = []
                for row_dict in rows_dict:
                    row_list = [row_dict[col] for col in column_names]
                    data_to_insert.append(row_list)
                
                self.client.insert(
                    f"{settings.CLICKHOUSE_DATABASE}.{settings.CLICKHOUSE_TABLE}",
                    data_to_insert,
                    column_names=column_names
                )
                
                print(f" ClickHouse에 {len(self.batch_buffer)}개 이벤트 저장 완료")
                self.batch_buffer.clear()
                
            except Exception as e:
                import traceback
                print(f"✗ ClickHouse 배치 삽입 실패: {e}")
                print(f"상세 오류:\n{traceback.format_exc()}")
                # 실패 시 버퍼를 유지하여 다음에 재시도
    
    def _prepare_row(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """이벤트 데이터를 ClickHouse 행 형식으로 변환"""
        import json
        from dateutil import parser
        
        # timestamp 변환 (ISO 문자열 -> datetime 객체)
        timestamp_str = event.get('timestamp')
        if timestamp_str:
            try:
                timestamp = parser.isoparse(timestamp_str)
            except:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        row = {
            'timestamp': timestamp,
            'event_type': event.get('event_type', 'unknown'),
            'src_ip': event.get('src_ip', '0.0.0.0'),
            'src_port': event.get('src_port', 0),
            'dest_ip': event.get('dest_ip', '0.0.0.0'),
            'dest_port': event.get('dest_port', 0),
            'proto': event.get('proto', 'unknown'),
            'raw_json': json.dumps(event, ensure_ascii=False),
            'date': timestamp.date(),  # date 컬럼 추가
            
            'alert_signature': None,
            'alert_category': None,
            'alert_severity': None,
            'alert_action': None,
            
            'flow_id': None,
            'flow_pkts_toserver': None,
            'flow_pkts_toclient': None,
            'flow_bytes_toserver': None,
            'flow_bytes_toclient': None,
            'flow_start': None,
            'flow_end': None,
            'flow_age': None,
            'flow_state': None,
            'flow_reason': None,
            
            'http_hostname': None,
            'http_url': None,
            'http_http_user_agent': None,
            'http_http_method': None,
            'http_protocol': None,
            'http_status': None,
            'http_length': None,
            
            'dns_type': None,
            'dns_id': None,
            'dns_rrname': None,
            'dns_rrtype': None,
            'dns_rcode': None,
            
            'tls_subject': None,
            'tls_issuerdn': None,
            'tls_fingerprint': None,
            'tls_sni': None,
            'tls_version': None,
        }
        
        if 'alert' in event:
            alert = event['alert']
            row['alert_signature'] = alert.get('signature')
            row['alert_category'] = alert.get('category')
            row['alert_severity'] = alert.get('severity')
            row['alert_action'] = alert.get('action')
        
        if 'flow' in event:
            flow = event['flow']
            row['flow_id'] = flow.get('flow_id')
            row['flow_pkts_toserver'] = flow.get('pkts_toserver')
            row['flow_pkts_toclient'] = flow.get('pkts_toclient')
            row['flow_bytes_toserver'] = flow.get('bytes_toserver')
            row['flow_bytes_toclient'] = flow.get('bytes_toclient')
            
            # flow_start, flow_end를 datetime 객체로 변환
            from dateutil import parser as date_parser
            flow_start_str = flow.get('start')
            flow_end_str = flow.get('end')
            if flow_start_str:
                try:
                    row['flow_start'] = date_parser.isoparse(flow_start_str)
                except:
                    pass
            if flow_end_str:
                try:
                    row['flow_end'] = date_parser.isoparse(flow_end_str)
                except:
                    pass
            
            row['flow_age'] = flow.get('age')
            row['flow_state'] = flow.get('state')
            row['flow_reason'] = flow.get('reason')
        
        if 'http' in event:
            http = event['http']
            row['http_hostname'] = http.get('hostname')
            row['http_url'] = http.get('url')
            row['http_http_user_agent'] = http.get('http_user_agent')
            row['http_http_method'] = http.get('http_method')
            row['http_protocol'] = http.get('protocol')
            row['http_status'] = http.get('status')
            row['http_length'] = http.get('length')
        
        if 'dns' in event:
            dns = event['dns']
            row['dns_type'] = dns.get('type')
            row['dns_id'] = dns.get('id')
            row['dns_rrname'] = dns.get('rrname')
            row['dns_rrtype'] = dns.get('rrtype')
            row['dns_rcode'] = dns.get('rcode')
        
        if 'tls' in event:
            tls = event['tls']
            row['tls_subject'] = tls.get('subject')
            row['tls_issuerdn'] = tls.get('issuerdn')
            row['tls_fingerprint'] = tls.get('fingerprint')
            row['tls_sni'] = tls.get('sni')
            row['tls_version'] = tls.get('version')
        
        return row
    
    async def periodic_flush(self):
        """주기적으로 배치 버퍼 플러시 (백그라운드 태스크)"""
        while True:
            await asyncio.sleep(settings.CLICKHOUSE_BATCH_INTERVAL)
            await self.flush_batch()

clickhouse_client = ClickHouseClient()
