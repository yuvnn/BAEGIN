import os
import json
import time
import requests
import chromadb
from sqlalchemy import create_engine, text

# Configuration
MONITORING_URL = "http://localhost:18085/monitor/run"
PAPER_API_URL = "http://localhost:18083/papers"
DB_URL = "mysql+pymysql://baegin_user:baegin_password@localhost:3306/baegin_db"

def test_pipeline():
    print("=== 1. 모니터링 서비스(A) 트리거 (논문 검색 및 Kafka 전송) ===")
    try:
        response = requests.post(MONITORING_URL, json={
            "keyword": "AI",
            "max_results": 1,
            "source": "arxiv"
        })
        response.raise_for_status()
        data = response.json()
        print(f"✅ 모니터링 성공: {data['fetched']}개 가져옴, {data['kafka_published']}개 Kafka 전송됨")
        if data['fetched'] == 0:
            print("⚠️ 검색된 논문이 없습니다. 테스트를 종료합니다.")
            return
    except Exception as e:
        print(f"❌ 모니터링 서비스 호출 실패: {e}")
        print("💡 Docker 컨테이너(monitoring-service 등)가 켜져 있는지 확인하세요.")
        return

    print("\n=== 2. Paper-Service(B) Kafka 처리 대기 (약 15초) ===")
    time.sleep(15)

    print("\n=== 3. MariaDB (RDB) 저장 결과 확인 ===")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT paper_id, category, md_summary FROM paper_summary LIMIT 1")).fetchone()
            if result:
                print(f"✅ RDB 'paper_summary' 저장 확인!")
                print(f"   - ID: {result[0]}")
                print(f"   - Category: {result[1]}")
                print(f"   - 요약 본문 (앞부분): {result[2][:100]}...\n")
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
        # ChromaDB는 컨테이너 안에 있으므로, paper-service의 GET /papers API를 호출하여 확인
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
