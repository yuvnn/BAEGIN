import os
import json
import time
import requests
from sqlalchemy import create_engine, text

# Configuration
MONITORING_URL = "http://localhost:18085/monitor/run"
PAPER_API_URL = "http://localhost:18083/papers"
DB_URL = "mysql+pymysql://baegin_user:baegin_password@localhost:3306/baegin_db"

def test_pipeline():
    engine = create_engine(DB_URL)
    
    print("=== 0. 테스트 환경 초기화 (기존 RDB 데이터 삭제) ===")
    try:
        with engine.connect() as conn:
            # Foreign key constraints might exist, so delete in order
            conn.execute(text("DELETE FROM paper_relate"))
            conn.execute(text("DELETE FROM paper_summary"))
            conn.commit()
            print("✅ MariaDB 초기화 완료. 신규 데이터 수집 준비됨.")
    except Exception as e:
        print(f"⚠️ 초기화 중 오류 (테이블이 아직 없을 수 있음): {e}")

    print("\n=== 1. 모니터링 서비스(A) 트리거 (논문 검색 및 Kafka 전송) ===")
    print("💡 팁: 'rm data/reports/seen_papers.json'을 삭제한 상태여야 신규 논문이 Kafka로 발송됩니다.")
    try:
        response = requests.post(MONITORING_URL, json={
            "keyword": "large language model",
            "max_results": 3,
            "source": "arxiv"
        })
        response.raise_for_status()
        data = response.json()
        print(f"✅ 모니터링 성공: {data['fetched']}개 가져옴, {data['kafka_published']}개 Kafka 전송됨")
        if data['kafka_published'] == 0:
            print("⚠️ Kafka로 전송된 신규 논문이 없습니다. 이전 실행 기록 때문일 수 있습니다.")
            print("   터미널에서 'rm data/reports/seen_papers.json' 실행 후 다시 시도하세요.")
            return
    except Exception as e:
        print(f"❌ 모니터링 서비스 호출 실패: {e}")
        print("💡 Docker 컨테이너(monitoring-service 등)가 켜져 있는지 확인하세요.")
        return

    print("\n=== 2. Paper-Service(B) 처리 대기 (최대 10분, AI Scientist 평가/요약 진행 중...) ===")
    print("💡 이 과정은 5인 앙상블 및 5회 반성 루프(총 25단계 이상)를 거치므로 2~5분 정도 소요됩니다.")
    found = False
    max_wait = 600 # 10 minutes
    interval = 10
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT paper_id FROM paper_summary LIMIT 1")).fetchone()
                if result:
                    print(f"\n✅ 신규 데이터 감지됨! (약 {elapsed}초 소요)")
                    found = True
                    break
        except Exception:
            pass # Table might be being recreated
        
        print(f"   > {elapsed}초 경과... 모델이 심사숙고 중입니다. (Docker logs에서 'Reflection loop' 확인 가능)", end="\r")
        time.sleep(interval)
        elapsed += interval
    
    if not found:
        print("\n❌ 타임아웃: 10분 내에 데이터가 RDB에 적재되지 않았습니다.")
        print("💡 팁: 'docker compose logs -f paper-service'를 통해 오류 여부를 확인하세요.")
        return

    print("\n=== 3. MariaDB (RDB) 저장 상세 결과 확인 ===")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT paper_id, category, md_summary FROM paper_summary LIMIT 1")).fetchone()
            if result:
                print(f"✅ RDB 'paper_summary' 저장 확인!")
                print(f"   - ID: {result[0]}")
                print(f"   - Category: {result[1]}")
                print(f"   - 요약 본문 (앞부분):\n{result[2][:200]}...\n")
            else:
                print("❌ RDB에 paper_summary 데이터가 없습니다.")

            relate_result = conn.execute(text("SELECT paper_id, internal_doc_id, rank, reason FROM paper_relate LIMIT 1")).fetchone()
            if relate_result:
                print(f"✅ RDB 'paper_relate' 저장 확인!")
                print(f"   - Paper ID: {relate_result[0]}")
                print(f"   - Internal Doc ID: {relate_result[1]}")
                print(f"   - Rank: {relate_result[2]}")
                print(f"   - Reason (앞부분): {relate_result[3][:100]}...\n")
            else:
                print("⚠️ RDB에 paper_relate 데이터가 없습니다. (내부 문서가 없거나 매칭되지 않았을 수 있음)")
    except Exception as e:
        print(f"❌ MariaDB 조회 실패: {e}")

    print("\n=== 4. ChromaDB (VectorDB) 저장 결과 확인 ===")
    try:
        response = requests.get(f"{PAPER_API_URL}?limit=1")
        response.raise_for_status()
        papers = response.json()
        if papers:
            paper = papers[0]
            print(f"✅ ChromaDB 'papers' 컬렉션 API 조회 성공!")
            print(f"   - Paper ID: {paper['paper_id']}")
            print(f"   - Metadata: {json.dumps(paper['metadata'], ensure_ascii=False)}")
        else:
            print("❌ ChromaDB에 저장된 논문이 없습니다.")
    except Exception as e:
        print(f"❌ ChromaDB API 조회 실패: {e}")

if __name__ == "__main__":
    test_pipeline()
