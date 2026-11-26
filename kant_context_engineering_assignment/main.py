"""main.py의 todo(...) 부분을 작성하세요. support.py와 checks.py는 그대로 사용합니다."""
import copy
import hashlib
import json
import sys

import support


def todo(message):
    raise NotImplementedError(message)


# 필수 1. 필요한 자료와 사용자 기억 관리하기
def select_context(items, user_id, now):
    kept = []
    for item in items:
        # allowed = todo("접근 범위, 신뢰, 현행 여부와 만료 조건")
        allowed = (
            (item['user_id'] == 'public' or item['user_id'] == user_id)
            and (item['trusted'] and item['active'])
            and (item['expires_at'] is None or item['expires_at'] > now)
            )
        if allowed:
            kept.append(copy.deepcopy(item))
    # 이유: 높은 우선순위의 자료를 먼저 고르면 어떤 문제가 생기는지 적으세요.
    '''
    우선순위를 먼저 보면 접근 권한이 없거나(user_id), 신뢰되지 않거나(trusted), 
    만료(expires_at)·비활성(active)인 자료가 높은 순위로 컨텍스트에 들어갈 수 있습니다.
    그렇게 되면 개인정보 유출·오답·인젝션 위험이 생기고 예산도 낭비하게 됩니다. 
    그래서 필터로 자격을 먼저 확인한 뒤 남은 것만 우선순위로 정렬합니다.
    '''
    return sorted(kept, key=lambda item: (-item["priority"], item["id"]))


def memory_action(records, user_id, action, name, value=None):
    support.validate_memory_input(user_id, action, name, value)
    key = f"{user_id}:{name}"
    if action == "read":
        # return todo("현재 사용자의 기억 조회")
        return copy.deepcopy(records.get(key))
    if action == "create":
        if key in records:
            raise ValueError("이미 있는 기억입니다. update를 사용하세요.")
        # records[key] = todo("새 기억 저장")
        records[key] = copy.deepcopy(value)
    elif action == "update":
        if key not in records:
            raise KeyError("수정할 기억이 없습니다.")
        # records[key] = todo("기존 기억 수정")
        records[key] = copy.deepcopy(value)
    elif action == "delete":
        # return todo("현재 사용자의 기억 삭제")
        return records.pop(key, None)
    return copy.deepcopy(records[key])


def build_messages(prefix, question, context, turns, summary):
    data = json.dumps({"reference_data": context, "summary": summary}, ensure_ascii=False)
    history = [message for turn in turns for message in turn["messages"]]
    # 이유: 장기 기억과 세션 상태의 차이, 자료와 지시를 나누는 이유를 적으세요.
    '''
    - 세션 상태: 현재 대화 안에서만 유효한 정보. 명시적으로 생성, 수정, 삭제. 사용자별로 격리.
    - 장기 기억: 대화가 끝나도 남기는 사용자 정보. 대화가 길어지면 요약하거나 창(window)으로 자름.
    
    - 자료와 지시를 나누는 이유
        외부 자료 속 문장이 지시로 실행되는 것(프롬프트 인젝션)을 막기 용이함
        시스템이 신뢰하는 규칙(prefix)과 신뢰할 수 없는 내용(자료)의 권한 수준 구분 가능
        고정 지시를 앞에 두어 캐시를 재사용 가능
        지시를 고치거나 자료를 교체할 때 서로 영향을 주지 않고, 문제가 생겼을 때 어디서 왔는지 추적하기 쉬움
    '''
    # return todo("고정 지시, 참고 자료, 대화, 현재 질문 순서의 메시지")
    return [
        {"role": "developer", "content": prefix},
        {"role": "user", "content": data},
        *history,
        {"role": "user", "content": question},
    ]


# 필수 2. 긴 대화를 줄이고 반복 입력 재사용하기
def summarize(turns):
    summary = {}
    for turn in turns:
        for name, value in support.fact_lines(turn["messages"][0]["content"]):
            # summary[name] = todo("최신 값과 출처 턴")
            summary[name] = {
                'value' : value,
                'source_turn_id' : turn['id']
            }
    return summary


def select_window(turns, limit, reserve, margin, make_messages, count):
    support.validate_budget(limit, reserve, margin)
    # budget = todo("입력에 쓸 수 있는 예산")
    budget = limit - reserve - margin
    if budget <= 0 or count(make_messages([])) > budget:
        raise ValueError("고정 입력만으로 예산을 넘었습니다.")
    kept = []
    for turn in reversed(turns):
        candidate = [turn, *kept]
        # if todo("전체 후보 입력이 예산을 넘는지"):
        if count(make_messages(candidate)) > budget:
            break
        kept = candidate
    # 관측: 압축 비교 후 토큰 수, 빠진 사실, 선택한 한도를 기록합니다.
    '''
    관측(live 1회 실행, artifacts/compare-live.json 기준): 
    전체 대화 : 1938 토큰, 빠진 사실 없음, exact_fields 3/3, $0.0004416 / 3109.6ms
    최근 대화 : 1699 토큰, 담당자·마감일 빠짐, 승인조건은 원문과 다르게 답함, exact_fields 0/3, $0.000407 / 1807.9ms 
    요약+최근 : 1695 토큰, 빠진 사실 없음, exact_fields 3/3, $0.000393 / 1373.8ms
    
    요약+최근 대화를 선택한다. 
    최근 대화만으로는 잘려 나간 앞쪽 턴의 사실이 사라지고, 
    요약을 함께 쓰면 같은 한도에서 최신 값과 출처를 보존해 전체 대화와 같은 답을 내기 때문이다. 
    요약 방식이 전체 대화보다 약 11% 저렴하다. 단, 7턴짜리 작은 예제 1회 실행이라 절감폭과 지연 차이는 일반화하기 어렵다.
    '''
    return kept


def cache_key(prefix, user_id):
    # return todo("사용자와 고정 지시로 만드는 캐시 키")
    # 관측: 실제 캐시 읽기/쓰기와 비용을 확인하고 미관측이면 그대로 적습니다.
    '''
    관측(live 1회, artifacts/cache-live.json, 가격 data/prices.json 2026-11-04 확인): 
    - 캐시 비사용 : $0.0003066, latency 1906ms
    - 첫 사용은 : cache_write 1228 토큰, 읽기 0, $0.000368(비사용에 비해 약 +20%), latency 1431ms
    - 재사용 : cached 1228 토큰, 읽기 관측, $0.0000856(비사용에 비해 약 -72%), latency 1098ms
    - 캐시 쓰기도 비용이라 첫 사용은 더 비쌌고 재사용이 있어야 이득 
    - latency(1906/1431/1098ms)는 1회 측정이라 속도 향상으로 일반화하지 않는다. 
    - 오염 자료 2개(tainted-document, unverified-tool)는 artifacts 결과에서 발견되지 않았다.
    '''
    return hashlib.sha256((user_id + '\n' + prefix).encode("utf-8")).hexdigest()



# 선택 심화 1. 새 대화만 반영하고 변경 이력 남기기
def merge_summary(previous, turns):
    # return todo("선택 심화: 새 턴의 요약과 변경 이력")
    current = copy.deepcopy(previous["current"])
    changes = copy.deepcopy(previous["changes"])
    processed_ids = list(previous["processed_ids"])
    seen = set(processed_ids)

    for turn in turns:
        if turn["id"] in seen:
            continue
        for name, new in summarize([turn]).items():
            old = current.get(name)
            # 변경 이력은 기존 값이 있고 값이 다를 때만 남깁니다.
            if old is not None and old["value"] != new["value"]:
                changes.append({"name": name, "before": old, "after": copy.deepcopy(new)})
            # 현재 값은 같은 값 재확인이어도 최신 출처 턴으로 갱신합니다.
            current[name] = new
        processed_ids.append(turn["id"])
        seen.add(turn["id"])

    return {"current": current, "changes": changes, "processed_ids": processed_ids}


if __name__ == "__main__":
    raise SystemExit(support.cli(sys.modules[__name__]))
