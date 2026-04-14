from __future__ import annotations

from ..schemas.input import PaperSummary

_WILDDET3D_PAPER = PaperSummary(
    paper_id="arxiv:2604.08626",
    title="WildDet3D: Open-Vocabulary Monocular 3D Object Detection in the Wild",
    summary_md=(
            "## 문제 정의\n\n"
            "3D 객체 인식은 공간 지능의 핵심 요소로, 단일 이미지에서 객체의 위치, 크기 및 방향을 "
            "복구하는 단안 3D 객체 검출이 중요합니다. 그러나 기존 방법들은 단일 프롬프트 유형에만 "
            "최적화되어 있으며, 추가적인 기하학적 단서를 통합할 수 있는 메커니즘이 부족합니다. "
            "또한, 현재의 3D 데이터셋은 제한된 환경에서 좁은 범주의 객체만을 다루고 있어, 개방형 "
            "세계로의 일반화가 어렵습니다. 이 논문은 이러한 문제를 해결하기 위해 WildDet3D라는 "
            "새로운 접근 방식을 제안합니다.\n\n"
            "## 연구 방법론\n\n"
            "- WildDet3D 아키텍처: 텍스트, 포인트, 박스 프롬프트를 자연스럽게 수용하는 통합 기하학 "
            "인식 아키텍처를 도입하였으며, 추론 시 보조 깊이 신호를 통합할 수 있습니다.\n"
            "- WildDet3D-Data: 2D 주석에서 후보 3D 박스를 생성하고, 인간 검증을 통해 13,500개 이상의 "
            "범주에 걸쳐 100만 개 이상의 이미지를 포함하는 대규모 개방형 3D 검출 데이터셋을 "
            "구축하였습니다.\n"
            "- 입력 모달리티: RGB 이미지와 선택적 깊이 입력을 결합하여, 개방형 어휘 인식을 "
            "지원하면서도 기하학적 신호가 제공될 때 메트릭 스케일 모호성을 줄입니다.\n\n"
            "## 주요 실험 결과\n\n"
            "WildDet3D는 다양한 벤치마크에서 새로운 최첨단 성능을 달성했습니다. 개방형 세계 설정에서 "
            "WildDet3D-Bench에서 텍스트 및 박스 프롬프트로 각각 22.6/24.8 AP3D를 기록하였고, "
            "Omni3D에서는 34.2/36.4 AP3D를 달성했습니다. 제로샷 평가에서는 Argoverse 2와 ScanNet에서 "
            "각각 40.3/48.9 ODS를 기록했습니다. 특히, 추론 시 깊이 단서를 통합하면 평균적으로 "
            "+20.7 AP의 성능 향상을 가져왔습니다.\n\n"
            "## 핵심 기여 및 의의\n\n"
            "- 통합 프롬프트 지원: 텍스트, 포인트, 박스 프롬프트를 단일 아키텍처에서 지원하여 다양한 "
            "응용 프로그램에 적합합니다.\n"
            "- 대규모 데이터셋 구축: 인간 검증을 통해 다양한 실제 장면을 포괄하는 대규모 데이터셋을 "
            "제공하여 일반화 능력을 향상시킵니다.\n"
            "- 깊이 신호 통합: 선택적 깊이 신호를 활용하여 3D 위치 추정의 정확성을 높입니다.\n\n"
            "## 한계점 및 향후 연구\n\n"
            "- 깊이 신호 의존성: 깊이 신호가 없는 경우 성능이 저하될 수 있으며, 이를 보완하기 위한 "
            "추가 연구가 필요합니다.\n"
            "- 데이터셋의 편향성: 데이터셋이 특정 환경에 편향될 가능성이 있으며, 이를 해결하기 위한 "
            "다양한 환경에서의 데이터 수집이 필요합니다.\n"
            "- 실시간 처리: 실시간 응용을 위한 최적화가 필요하며, 이를 위한 경량화 모델 연구가 "
            "요구됩니다."
        ),
    paper_url="https://arxiv.org/pdf/2604.08626",
    authors=[
            "Weikai Huang",
            "Jieyu Zhang",
            "Sijun Li",
            "Taoyang Jia",
            "Jiafei Duan",
            "Yunqian Cheng",
            "Jaemin Cho",
            "Mattew Wallingford",
            "Rustin Soraki",
            "Chris Dongjoo Kim",
            "Donovan Clay",
            "Taira Anderson",
            "Winson Han",
            "Ali Farhadi",
            "Bharath Hariharan",
            "Zhongzheng Ren",
            "Ranjay Krishna",
    ],
    category="ML Foundation",
)

_MOCK_PAPERS: dict[str, PaperSummary] = {
    "arxiv:2604.08626": _WILDDET3D_PAPER,
    "paper-demo-001": _WILDDET3D_PAPER.model_copy(update={"paper_id": "paper-demo-001"}),
}


def get_paper_summary(paper_id: str) -> PaperSummary:
    if paper_id in _MOCK_PAPERS:
        return _MOCK_PAPERS[paper_id]

    return PaperSummary(
        paper_id=paper_id,
        title=f"Auto-generated paper for {paper_id}",
        summary_md=(
            "입력된 paper_id에 대한 사전 데이터가 없어 기본 논문 요약을 반환한다. "
            "요구사항-기술 매핑과 citation anchor 생성에 필요한 최소 정보를 포함한다."
        ),
        paper_url=f"https://example.org/{paper_id}",
        authors=["Unknown"],
        category="Unknown",
    )
