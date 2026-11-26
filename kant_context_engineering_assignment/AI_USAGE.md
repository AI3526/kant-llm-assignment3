# AI 사용 기록

AI는 개념 질문과 직접 작성한 코드의 오류 원인 확인에 사용할 수 있습니다. 과제 전체, 미작성 빈칸, 선택 심화의 설계나 정답을 대신 작성하도록 요청하지 않습니다. 설명을 이해한 뒤 직접 수정하고 다시 검사하세요.

사용하지 않았다면 아래에 사용하지 않음이라고 적습니다. 사용했다면 필요한 만큼 행을 추가하세요. API 키와 개인 정보는 기록하지 않습니다.

| 사용 도구 | 질문 | 이해한 내용 | 직접 수정한 부분 | 다시 실행한 명령과 결과 |
|---|---|---|---|---|
| | | | | |

### 1. return todo("현재 사용자의 기억 삭제")
- 요청 : 삭제 구현은 어떻게 해?
- 답변 : records.pop(key, None)을 쓰면 key가 있으면 삭제하고, 없더라도 KeyError 없이 안전하게 처리할 수 있습니다.
- 이해한 내용
    key가 records에 있으면 해당 항목을 지우고 삭제된 값을 반환합니다.
    key가 없어도 기본값 None을 돌려주므로 에러가 나지 않습니다.

### 2. return todo("사용자와 고정 지시로 만드는 캐시 키")
- 요청 : hashlib.sha256(...).hexdigest() 이거 어떻게 사용하는 거야?
- 답변 : hashlib.sha256() 안에는 str이 아니라 bytes 객체를 넣어야 합니다. 문자열이라면 .encode("utf-8")로 변환한 뒤 넘기세요.

### 3. 선택 심화 1. 새 대화만 반영하고 변경 이력 남기기
- 요청 : 
 1) 원래 previous를 변경해서 previous 그대로 두고 result 따로 만들어서 코드 수정 요청 -> 답변) deepcopy 부분 3줄 생성 및 previous 변수명을 result로 수정 
 2) 아래 코드 리팩토링 요청. summarize([turn]) 했을 때 오류 나서 하드코딩했는데 클로드코드가 하니까 되네...?
 ```python
 def merge_summary(previous, turns):
    result = {
        "current": copy.deepcopy(previous["current"]),
        "changes": copy.deepcopy(previous["changes"]),
        "processed_ids": list(previous["processed_ids"]),
    }

    wanted = ['담당자:', '마감일:', '승인조건:']

    for turn in turns :
        if turn['id'] in result['processed_ids'] :
            continue

        else :
            content_splitted = turn['messages'][0]['content'].split('\n')
            
            for splitted in content_splitted :
                for w in wanted : 
                    if w in splitted :
                        name = splitted.split(':')[0].strip()
                        value = splitted.split(':')[1].strip()

                        if name not in result['current'] : 
                            result['current'][name] = {
                                'value' : value,
                                'source_turn_id' : turn['id']
                            }

                        else :
                            old_value_dict = result['current'][name]

                            if value != old_value_dict['value']:
                                result['current'][name] = {
                                    'value': value,
                                    'source_turn_id': turn['id'],
                                }
                                result['changes'].append({
                                    'name': name,
                                    'before': old_value_dict,
                                    'after': result['current'][name],
                                })

                            if turn['id'] != old_value_dict['source_turn_id'] :
                                result['current'][name] = {
                                    'value': value,
                                    'source_turn_id': turn['id'],
                                }

            result['processed_ids'].append(turn['id'])

    return result
 ```

 ### 4. 주관식 문항
 - 클로드코드에 설명 요청해서 답변에 참고했습니다.