# AI 사용 기록

AI는 개념 설명과 직접 작성한 코드의 오류 원인 확인에 사용할 수 있습니다. 과제 전체, 미작성 TODO, 프롬프트 문장, 선택 심화 설계를 대신 완성하도록 요청하지 않습니다.

사용하지 않았다면 아래에 사용하지 않음이라고 적습니다. 사용했다면 필요한 만큼 항목을 추가하세요. API 키나 개인정보는 기록하지 않습니다.

- 사용 도구: 제미나이, 클로드코드
- 질문한 내용:
- 이해한 내용:
- 직접 수정한 부분:
- 다시 실행한 명령과 확인 결과:

### 1. 필수 2 과제에서 검사 항목 13/15 통과인데 어느 부분이 틀린지 몰라서 필수 2 전체 코드를 제미나이에 입력하고 TODO 구현 틀린 부분 알려달라고 요청

- 틀린 부분:
1) TODO: 위 세 조건과 기대 출처 집합 일치를 모두 확인하세요.
return (action_ok
and required_ok
and forbidden_ok
and set(reply).issubset(expected))

2) TODO: 비용이 하나라도 None이면 None, 아니면 합계를 반환하세요.
"total_tokens": sum(tokens) if all(value is not None for value in tokens) else None

- 이해한 내용:
    현재는 reply의 키 이름이 expected의 부분집합인지만 확인하고 있음
    현재는 비용이 0인 요청이 하나라도 있으면 전체 합계가 None이 됨

- 직접 수정:
    reply와 expected의 source_ids 필드 직접 비교
    cost 각각이 None인지 판단한 후 all 적용


### 2. 선택 심화 1. 연속된 관측 구간으로 운영 대응 정하기
- 요청1 : 문제 조건이랑 다음 코드 주고 조건에 맞게 작성되었는지 질문
```python
for window in windows[-2:] :
    if (
        (not (window['requests'] >= 0 and isinstance(window['requests'], int)))
        or (not 0 <= window['error_rate'] <= 1)
        or (not (window['p95_latency_ms'] >= 0 and math.isfinite(window['p95_latency_ms'])))
    ) :
        raise ValueError('값이 범위를 벗어남')
```

- 이해한 내용 :
    error_rate나 p95_latency_ms가 None일 때 TypeError가 날 수 있음
    파이썬의 or은 앞 조건이 True면 뒤 조건을 평가하지 않음

- 요청2 : 좀 더 알아보기 쉽게 작성할 수 없는지 질문

- 답변 : 헬퍼 함수로 분리 추천

- 답변 참고해서 직접 수정 : is_valid 함수

```python
def decide_rollout(windows, *, min_requests=5, max_error_rate=0.2, max_p95_ms=3000):

    def is_valid(window) :
    requests = window['requests']
    error_rate = window['error_rate']
    p95 = window['p95_latency_ms']

    requests_ok = isinstance(requests, int) and requests >= 0
    error_ok = error_rate is not None and 0 <= error_rate <= 1
    p95_ok = p95 is not None and p95 >= 0 and math.isfinite(p95)

    return requests_ok and error_ok and p95_ok


    if len(windows) < 2 :
        return 'hold'


    else :
        temp =''
        should_rollback = []
        for window in windows[-2:] :
            if not is_valid(window) :
                raise ValueError('값이 범위를 벗어남')

        else :
            if window['requests'] < min_requests or window['error_rate'] is None or window['p95_latency_ms'] is None :
                temp = 'hold'

            if window['error_rate'] > max_error_rate or window['p95_latency_ms'] > max_p95_ms :
                should_rollback.append(True)

            else :
                should_rollback.append(False)

    if all(should_rollback) :
        temp = 'rollback'
    elif any(should_rollback) :
        temp = 'hold'
    else :
        temp = 'continue'

    return temp
```

- 요청3 : 위 함수로 검사 항목 9/10는 통과하는데 if window['requests'] < min_requests ~ 이 부분 temp랑 should_rollback이랑 섞여서 해결 불가. 해결 요청

- 답변 : 현재 main.py 코드와 거의 비슷한데 그래도 검사 항목 9/10였음

- 이해한 내용 : is_valid에서 지표가 None일 때 ValueError 발생시키면 안 되고 if window['requests'] < min_requests ~ 여기서 검사해서 hold로 return해야 함

- 직접 수정 : 현재 main.py


### 3. 주관식 질문에 클로드코드 설명 참고