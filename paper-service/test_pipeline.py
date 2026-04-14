import os
import json
import logging
import chromadb
from dotenv import load_dotenv

# BAEGIN 최상위 폴더의 .env 파일을 불러옵니다. (앱 모듈 임포트 전에 실행)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.pdf_parser import download_and_parse_pdf
from app.evaluator import evaluate_paper
from app.summarizer import summarize_paper

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 테스트에 사용할 유명한 AI 논문 (Attention Is All You Need)
pdf_url = "https://arxiv.org/pdf/1706.03762v5.pdf"
doc_id = "arxiv-1706-03762"
title = "Attention Is All You Need"
keyword = "AI"
abstract = "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely."

def run_test():
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. API 키를 설정한 후 다시 실행해주세요.")
        logger.error("실행 방법: OPENAI_API_KEY='sk-...' python test_pipeline.py")
        return

    logger.info("=== 단계 1: 논문 평가 시작 (evaluator.py) ===")
    evaluation = evaluate_paper(keyword, title, abstract)
    logger.info(f"평가 결과: 통과 여부={evaluation.is_relevant}, 점수={evaluation.score}")
    logger.info(f"리뷰 코멘트: {evaluation.review}\n")

    if not evaluation.is_relevant:
        logger.info("논문이 평가를 통과하지 못했습니다. 테스트를 종료합니다.")
        return

    logger.info("=== 단계 2: PDF 원본 다운로드 및 파싱 (pdf_parser.py) ===")
    full_text = download_and_parse_pdf(pdf_url)
    logger.info(f"추출 완료! 전체 텍스트 길이: {len(full_text)} 글자\n")

    logger.info("=== 단계 3: AI 요약 진행 (summarizer.py) ===")
    summary_dict = summarize_paper(doc_id, title, abstract, body_text=full_text)
    
    logger.info("생성된 요약본 (JSON 객체):")
    print(json.dumps(summary_dict, indent=2, ensure_ascii=False))
    print("\n")

    logger.info("=== 단계 4: 로컬 ChromaDB에 적재 테스트 ===")
    metadata = {
        "source_type": "paper",
        "document_type": "paper",
        "access_level": "public",
        "title": title,
        "keyword": keyword,
        "evaluation_score": evaluation.score,
        "evaluation_review": evaluation.review
    }
    
    # Docker 없이 로컬 디스크에 바로 ChromaDB를 생성하여 테스트합니다.
    db_path = "./local_chroma_test_db"
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="papers")

    # DB 적재 로직 (소비자의 방식과 동일하게 저장)
    collection.upsert(
        ids=[doc_id],
        documents=[json.dumps(summary_dict, ensure_ascii=False)],
        metadatas=[metadata]
    )
    logger.info(f"✅ ChromaDB 저장 완료! (저장 위치: {db_path})\n")

    logger.info("=== 단계 5: ChromaDB에서 꺼내서 저장된 형태 확인 ===")
    results = collection.get(ids=[doc_id], include=["documents", "metadatas"])
    
    print("--------------------------------------------------")
    print("[DB에 저장된 메타데이터 (Metadata)]:")
    print(json.dumps(results['metadatas'][0], indent=2, ensure_ascii=False))
    print("\n[DB에 저장된 본문 (Document) - Stringified JSON 형태로 저장됨]:")
    print(results['documents'][0])
    print("--------------------------------------------------")
    logger.info("테스트 스크립트 실행이 완료되었습니다!")

if __name__ == "__main__":
    run_test()
