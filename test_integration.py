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

    print("\n=== 1. 모니터링 서비스(A) 트리거 (논문 검색 및 Kafka 전송) ===")
    print("💡 팁: Docker 볼륨의 'seen_papers.json'을 삭제한 상태여야 신규 논문이 Kafka로 발송됩니다.")
    try:
        response = requests.post(MONITORING_URL, json={
            "max_results": 50
        })
        response.raise_for_status()
        data = response.json()
        print(f"✅ 모니터링 응답:")
        print(f"   - 수집(collected):           {data.get('collected', 0)}개")
        print(f"   - 중복제거(after_dedup):      {data.get('after_dedup', 0)}개")
        print(f"   - 메타필터(after_metadata):   {data.get('after_metadata_filter', 0)}개")
        print(f"   - 시맨틱필터(after_semantic): {data.get('after_semantic_filter', 0)}개")
        print(f"   - 고영향도(high_impact):      {data.get('high_impact', 0)}개")
        print(f"   - Kafka 전송(kafka_published): {data.get('kafka_published', 0)}개")

        if data.get('kafka_published', 0) == 0:
            if data.get('after_metadata_filter', 0) == 0:
                print("\n⚠️ 메타데이터 필터(conference mention / HF 5+ upvote)를 통과한 논문이 없습니다.")
                print("   → 최근 arXiv 논문은 학술대회 멘션이 없어 필터링될 수 있습니다.")
                print("   → paper-service 파이프라인은 Kafka 메시지 없이도 아래 단계에서 직접 확인합니다.")
            elif data.get('after_dedup', 0) == 0:
                print("\n⚠️ 모든 논문이 이미 처리됨(dedup). seen_papers.json을 초기화하려면:")
                print("   docker compose exec monitoring-service rm /app/reports/seen_papers.json")
            else:
                print("\n⚠️ Kafka로 전송된 신규 논문이 없습니다.")
    except Exception as e:
        print(f"❌ 모니터링 서비스 호출 실패: {e}")
        print("💡 Docker 컨테이너(monitoring-service 등)가 켜져 있는지 확인하세요.")
        return

    kafka_published = data.get('kafka_published', 0)

    # kafka_published > 0 일 때만 DB를 초기화하여 신규 결과를 검증
    if kafka_published > 0:
        print("\n=== 0. 테스트 환경 초기화 (기존 RDB 데이터 삭제) ===")
        try:
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM paper_relate"))
                conn.execute(text("DELETE FROM paper_summary"))
                conn.commit()
                print("✅ MariaDB 초기화 완료. 신규 데이터 수집 준비됨.")
        except Exception as e:
            print(f"⚠️ 초기화 중 오류 (테이블이 아직 없을 수 있음): {e}")

    print("\n=== 2. Paper-Service(B) 처리 대기 ===")

    if kafka_published > 0:
        print(f"💡 {kafka_published}개 논문이 Kafka로 전송됨. AI Scientist 평가/요약 완료까지 대기합니다...")
        print("   (3명 심사위원 × 1회 반성 루프 + Area Chair 메타리뷰 → 논문당 약 30~60초)")
    else:
        print("💡 이번 실행에서 Kafka 전송된 논문은 없습니다.")
        print("   기존에 저장된 RDB/ChromaDB 데이터 확인으로 진행합니다.")

    found = False
    max_wait = 600 if kafka_published > 0 else 5  # 전송 논문 없으면 짧게 대기
    interval = 10
    elapsed = 0

    while elapsed < max_wait:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT paper_id FROM paper_summary LIMIT 1")).fetchone()
                if result:
                    if kafka_published > 0:
                        print(f"\n✅ 신규 데이터 감지됨! (약 {elapsed}초 소요)")
                    found = True
                    break
        except Exception:
            pass

        if kafka_published > 0:
            print(f"   > {elapsed}초 경과... 모델이 심사숙고 중입니다. (Docker logs에서 진행 상황 확인 가능)", end="\r")
        time.sleep(interval)
        elapsed += interval

    if not found:
        if kafka_published > 0:
            print("\n❌ 타임아웃: 10분 내에 데이터가 RDB에 적재되지 않았습니다.")
            print("💡 팁: 'docker compose logs -f paper-service'를 통해 오류 여부를 확인하세요.")
            return
        else:
            print("   RDB에 기존 저장 데이터 없음. 아래 단계를 건너뜁니다.")
            return

    print("\n=== 3. MariaDB (RDB) 저장 상세 결과 확인 ===")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT paper_id, category, paper_url, md_summary FROM paper_summary LIMIT 1")).fetchone()
            if result:
                print(f"✅ RDB 'paper_summary' 저장 확인!")
                print(f"   - ID:       {result[0]}")
                print(f"   - Category: {result[1]}")
                print(f"   - PDF URL:  {result[2]}")
                summary_len = len(result[3]) if result[3] else 0
                print(f"   - 요약 길이: {summary_len}자")
                print(f"   - 요약 본문 (앞부분):\n{result[3][:300]}...\n")
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
