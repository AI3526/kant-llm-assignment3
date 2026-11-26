# AI 사용 기록

AI는 개념 질문과 직접 작성한 코드의 오류 원인을 확인할 때 사용할 수 있습니다. 미작성 빈칸, 과제 전체, 평가 사례나 선택 심화의 설계를 대신 완성해 달라고 요청하지 않습니다. 실제 실행 결과를 만들거나 고쳐 달라고 요청하지 않습니다.

사용하지 않았다면 아래에 사용하지 않음이라고 적으세요. 사용했다면 필요한 만큼 기록하세요. API 키나 원문 개인정보를 대화에 넣지 않습니다.

## 사용 도구:
- 제미나이
- 챗지피티
- 클로드코드

## 질문과 관련 함수:
#### 1. text = todo("문단의 연속 공백을 한 칸으로 정리하세요.")
- 요청 : 연속 공백을 한 칸으로 정리하는 re 정규식 작성해줘
- 답변 : cleaned_text = re.sub(r'\s+', ' ', text)
- 이해한 내용:
    \s: 공백 문자(스페이스, 탭 \t, 줄바꿈 \n 등)를 모두 포함하는 정규식 패턴
    +: 바로 앞의 패턴(\s)이 1번 이상 연속으로 나타나는 경우를 의미
    따라서 re.sub(r'\s+', ' ', text)는 연속해서 나타나는 모든 공백 문자 덩어리를 하나의 스페이스(' ')로 치환
- 직접 수정한 부분: check 통과 못해서 뒤에 strip 추가   
    기존 코드는 중간의 연속 공백만 한 칸으로 줄어들고 양 끝 공백 그대로

#### 2. context = todo("각 검색 결과를 [chunk_id] 본문으로 묶고 빈 줄로 연결하세요.")
- 요청 : f"[{row['chunk_id']}] {row['text']}" for row in row 결과를 빈 줄로 연결하려면 어떻게 해야 돼?
- 답변 : context = "\n\n".join(f"[{row['chunk_id']}] {row['text']}" for row in rows)
- 이해한 내용 :
    "\n" 한 번 (줄바꿈 1번 → 빈 줄 없음)
    [doc1:0] 첫 번째 문단
    [doc1:1] 두 번째 문단

#### 3. 선택 심화 1. 두 검색 순위를 합쳐 근거를 모으기
- 요청 : 작성한 코드와 문제 조건 주고 리팩토링 요청
```python
def fuse_rankings(rankings, top_k=2) :

    if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 5:
        raise ValueError
    
    if rankings is None :
        return []

    wanted = set()
    trimmed = {}

    for i, ranking in enumerate(rankings) :
        trimmed[i] = set()
        for rank in ranking :
            for _, v in rank.items() :
                wanted.add(v)
                trimmed[i].add(v)

    result = {}
    for w in list(wanted) :
        result[w] =[]
    for k, v in trimmed.items() :
        for i, want in enumerate(list(v)) :
            score = 1 / (61 + i)
            result[want].append(score)

    result_final = {}
    for k, v in result.items() :
        result_final[k] = sum(v)

    ranked = dict(sorted(result_final.items(), key = lambda item : (-item[1], item[0])))

    return list(ranked.keys())[:top_k]
```

#### 4. 관측: 실제 evaluate 결과에서 개선, 악화 질문과 답변 본문을 확인해 기록합니다.
- 요청 : 직접 확인 후, 클로드코드에게 답변 작성 요청
