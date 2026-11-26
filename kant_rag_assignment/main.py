"""KANT NEXT DevDesk RAG. 이 파일의 빈칸만 작성하세요."""
from qdrant_client import models

import support
import re

def todo(message):
    raise NotImplementedError(message)


# 필수 1. 문서를 저장하고 현행 자료만 검색하기
def prepare_chunks(documents):
    chunks = []
    for document in documents:
        seen = set()
        number = 0
        for paragraph in document["paragraphs"]:
            # text = todo("문단의 연속 공백을 한 칸으로 정리하세요.")
            text = re.sub(r'\s+', ' ', paragraph).strip()
            if not text or text == "KANT NEXT | 내부 문서" or text in seen:
                continue
            seen.add(text)
            # chunk = todo("문서 정보 5개와 chunk_id, text를 담은 사전을 만드세요.")
            chunk = {
                'document_id' : document['document_id'],
                'title' : document['title'],
                'category' : document['category'], 
                'status' : document['status'], 
                'source' : document['source'],
                'chunk_id' : f"{document['document_id']}:{number}",
                'text' : text
            }
            chunks.append(chunk)
            number += 1

    # 이유: 문단을 유지하는 이유와 보존해야 할 메타데이터를 한두 줄로 적으세요.
    '''
    문단을 청크 하나로 유지하면 의미가 보존되고 정확한 위치를 인용할 수 있습니다. 
    status, category, document_id, title, source를 모든 청크에 담아 두면 현행 문서 필터링과 출처 추적이 가능합니다.
    '''

    return chunks


def build_index(chunks, embedder):
    texts = ["passage: " + row["title"] + "\n" + row["text"] for row in chunks]
    # vectors = todo("texts를 정규화된 문서 벡터로 바꾸세요.")
    vectors = embedder.encode(texts, normalize_embeddings=True)
    client = support.empty_store(len(vectors[0]))
    points = []
    for i, (row, vector) in enumerate(zip(chunks, vectors, strict=True)):
        # point = todo("i, vector, row를 Qdrant PointStruct에 연결하세요.")
        point = models.PointStruct(
            id = i,
            payload = row,
            vector = vector
        )
        points.append(point)
    client.upsert(collection_name="devdesk", points=points, wait=True)
    return client


def search(client, embedder, question, category, top_k=2):
    if type(top_k) is not int or not 1 <= top_k <= 5:
        raise ValueError("top_k는 1~5의 정수여야 합니다.")
    vector = embedder.encode(["query: " + question], normalize_embeddings=True)[0]
    # scope = todo("현행 문서이면서 지정한 category인 Qdrant 필터를 만드세요.")
    scope = models.Filter(
        must=[
            models.FieldCondition(
                key="status", match=models.MatchValue(value="current")
            ),
            models.FieldCondition(
                key="category", match=models.MatchValue(value=category)
            ),
        ],
    )
    hits = client.query_points(collection_name="devdesk", query=list(vector),
                               query_filter=scope, limit=top_k, with_payload=True).points
    return [{**hit.payload, "score": hit.score} for hit in hits]


# 필수 2. 별칭 검색을 개선하고 답변을 비교하기
def rewrite_query(question, aliases):
    rewritten = question
    for alias, formal_name in aliases.items():
        # rewritten = todo("현재 문자열에서 alias를 formal_name으로 바꾸세요.")
        rewritten = rewritten.replace(alias, formal_name)
    return rewritten


def answer_question(question, rows, generate):
    print(rows)
    if not rows:
        return {"answer": "확인할 문서가 없습니다.", "citations": [], "needs_human": True}
    # context = todo("각 검색 결과를 [chunk_id] 본문으로 묶고 빈 줄로 연결하세요.")
    context = "\n\n".join(f"[{row['chunk_id']}] {row['text']}" for row in rows)
    reply = support.validate_shape(generate(question, context))
    allowed = {row["chunk_id"] for row in rows}
    # if todo("검색 결과에 없는 출처가 하나라도 있는지 검사하세요."):
    if not set(reply["citations"]).issubset(allowed) :
        raise ValueError("검색하지 않은 출처가 있습니다.")
    if reply["needs_human"] == bool(reply["citations"]):
        raise ValueError("답변에는 출처가 필요하며 담당자 확인에는 출처를 비웁니다.")
    return reply


def make_golden():
    # return todo("답이 있는 사례와 자료가 없는 사례를 하나씩 작성하세요.")
    return (
        [{
        'question_id' : 'Q01',
        'question' : '초록문을 사용하려면 어떻게 해야 하나요',
        'category': 'access',
        'reference_answer': 'VPN 원격 접속을 사용하려면 보안팀에 승인을 요청해야 합니다. 승인 후 회사 계정으로 로그인하고 다중 인증을 완료합니다.',
        'relevant_document_ids': ['vpn'],
        'required_terms': ['보안팀']
        },
        {
        'question_id': 'Q02',
        'question' : '개발환경에서 환경 변수는 어떻게 설정하나요?',
        'category': 'overseas',
        'reference_answer': '제공된 문서에는 개발환경의 Python 버전(Python 3.12)과 의존성 설치 방법(uv sync --frozen)만 안내되어 있으며, 환경 변수 설정 방법에 대한 내용은 확인할 수 없습니다.',
        'relevant_document_ids': [],
        'required_terms': []
        }]
        )


def measure(case, rows, reply):
    expected = set(case["relevant_document_ids"])
    found = {row["document_id"] for row in rows}
    # recall = todo("필요한 문서 중 찾은 비율을 계산하세요. 필요한 문서가 없으면 None입니다.")
    recall = len(found & expected) / len(expected) if expected else None
    answer_ok = (all(term in reply["answer"] for term in case["required_terms"])
                 and not reply["needs_human"]) if expected else reply["needs_human"]
    failure = "없음"
    if expected and recall < 1:
        failure = "검색 누락"
    elif not answer_ok:
        failure = "답변 확인 필요" if expected else "보류 실패"

    # 관측: 실제 evaluate 결과에서 개선, 악화 질문과 답변 본문을 확인해 기록합니다.

    '''
    ### 개선 질문: Q01 (초록문)
    - 질문: "초록문을 사용하려면 어떻게 해야 하나요"
    - baseline: 별칭을 그대로 검색해서 엉뚱한 door:0(출입문 문서)이 나왔습니다. recall은 0.0이고 실패 유형은 "검색 누락"입니다.
    - 답변: "제공된 문서에는 '초록문(VPN 원격 접속)' 사용 방법이 안내되어 있지 않습니다. 문서에는 출입문이 열리지 않을 때 총무팀에 출입 권한을 요청하고, 출입 카드가 초록색으로 표시되면 문을 열 수 있다고만 나와 있습니다." 출처 없이 담당자 확인으로 넘겼습니다.

    - rewritten: aliases.json이 "초록문"을 "VPN 원격 접속"으로 바꿔서 vpn:0을 찾았습니다. recall은 1.0입니다.
    - 답변: "VPN 원격 접속을 사용하려면 보안팀에 승인을 요청해야 합니다. 승인 후 회사 계정으로 로그인하고 다중 인증을 완료하세요." 출처는 vpn:0이고, 필수 용어 '보안팀'이 들어 있습니다.
    - 이유: 임베딩은 '초록문'이라는 사내 별칭을 모릅니다. 그래서 글자가 비슷한 '출입문' 문서가 선택됐습니다.

    ### 악화 질문: 없음
    모든 질문에서 rewritten이 baseline보다 나빠지지 않았습니다. 그래도 눈여겨볼 두 가지가 있습니다.
    - given-token: 두 방법 모두 token:0을 찾아 성공했습니다. 다만 rewritten의 검색 문장은 "API 토큰를 어디에서…"로 조사가 어색합니다. 지금은 영향이 없지만, 치환이 늘어나면 악화 위험이 있는 지점입니다.
    - Q02: 두 방법 모두 검색 결과가 비어서 "확인할 문서가 없습니다."로 보류했고, 이는 정답입니다. 개선도 악화도 아닙니다.
    - given-python: 별칭이 없어 검색 문장이 같고 결과도 같습니다.
    '''

    return {"document_recall": recall, "answer_check": bool(answer_ok), "failure": failure}


# 선택 심화 1. 두 검색 순위를 합쳐 근거를 모으기
def fuse_rankings(rankings, top_k=2):
    # 선택 심화: 문제의 RRF 규칙에 맞춰 직접 작성하세요.
    # return todo("검색 순위 목록을 RRF 점수로 합치세요.")
    from collections import defaultdict

    if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 5:
        raise ValueError

    scores = defaultdict(float)
    chunks = {}

    for ranking in rankings:
        unique_chunks = dict.fromkeys(
            item["chunk_id"] for item in ranking
        )

        for item in ranking:
            chunk_id = item["chunk_id"]

            if chunk_id not in chunks:
                chunks[chunk_id] = item

        for rank, chunk_id in enumerate(unique_chunks, start=1):
            scores[chunk_id] += 1 / (60 + rank)

    ranked = sorted(
        scores,
        key=lambda chunk_id: (-scores[chunk_id], chunk_id)
    )

    result = []

    for chunk_id in ranked[:top_k]:
        chunk = chunks[chunk_id].copy()
        chunk["score"] = scores[chunk_id]
        result.append(chunk)

    '''
    필수 용어 '보안팀'과 승인 절차가 그대로 들어 있습니다. 
    RRF는 두 순위에서 모두 상위인 vpn:0, vpn:1은 올리고 한쪽에만 나온 token:0, door:0은 밀어내 중복·노이즈를 줄입니다.
    '''
    
    return result



if __name__ == "__main__":
    support.cli(globals())
