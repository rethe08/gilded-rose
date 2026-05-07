# Phase 1 설계 문서 — Unit Test 작성

## 목적

리팩토링 전 기존 동작을 테스트 코드로 고정한다.
이 테스트 스위트가 이후 모든 Phase의 안전망(regression guard)이 된다.

코드 변경 없음 — `gilded_rose.py`는 이 Phase에서 일절 수정하지 않는다.

---

## 테스트 파일 위치

```
tests/test_gilded_rose.py   ← 기존 파일에 추가 (test_foo는 유지)
```

---

## 테스트 구조

pytest의 클래스 기반 그룹핑을 사용한다.
각 클래스는 아이템 유형 하나에 대응한다.

```
TestNormalItem
TestAgedBrie
TestBackstagePass
TestSulfuras
TestEdgeCases
```

---

## 헬퍼

반복되는 `GildedRose([Item(...)]).update_quality()` 패턴을 줄이기 위해
모듈 수준 헬퍼 함수를 하나 둔다.

```python
def run_update(name, sell_in, quality, days=1):
    """days 횟수만큼 update_quality를 실행한 뒤 item을 반환한다."""
    item = Item(name, sell_in, quality)
    gilded_rose = GildedRose([item])
    for _ in range(days):
        gilded_rose.update_quality()
    return item
```

---

## 테스트 케이스 명세

### TestNormalItem

| 테스트 메서드 | 초기값 (sell_in, quality) | days | 검증 대상 | 기대값 |
|---|---|---|---|---|
| `test_quality_decreases_by_1` | (5, 10) | 1 | quality | 9 |
| `test_sell_in_decreases_by_1` | (5, 10) | 1 | sell_in | 4 |
| `test_quality_decreases_twice_after_sell_in_expires` | (0, 10) | 1 | quality | 8 |
| `test_quality_never_goes_below_zero` | (5, 0) | 1 | quality | 0 |
| `test_quality_zero_after_sell_in_expired` | (0, 1) | 1 | quality | 0 |

> `sell_in = 0` 일 때 update 후 `sell_in = -1`이 되므로 만료 조건(`sell_in < 0`) 진입 → quality 추가 감소.

---

### TestAgedBrie

| 테스트 메서드 | 초기값 (sell_in, quality) | days | 검증 대상 | 기대값 |
|---|---|---|---|---|
| `test_quality_increases_by_1` | (5, 10) | 1 | quality | 11 |
| `test_sell_in_decreases` | (5, 10) | 1 | sell_in | 4 |
| `test_quality_increases_twice_after_sell_in_expires` | (0, 10) | 1 | quality | 12 |
| `test_quality_capped_at_50` | (5, 50) | 1 | quality | 50 |
| `test_quality_does_not_exceed_50_near_cap` | (5, 49) | 2 | quality | 50 |

---

### TestBackstagePass

| 테스트 메서드 | 초기값 (sell_in, quality) | days | 검증 대상 | 기대값 |
|---|---|---|---|---|
| `test_quality_increases_by_1_when_far` | (15, 10) | 1 | quality | 11 |
| `test_quality_increases_by_2_when_10_days_left` | (10, 10) | 1 | quality | 12 |
| `test_quality_increases_by_2_when_6_days_left` | (6, 10) | 1 | quality | 12 |
| `test_quality_increases_by_3_when_5_days_left` | (5, 10) | 1 | quality | 13 |
| `test_quality_increases_by_3_when_1_day_left` | (1, 10) | 1 | quality | 13 |
| `test_quality_drops_to_zero_after_concert` | (0, 10) | 1 | quality | 0 |
| `test_quality_capped_at_50` | (10, 49) | 1 | quality | 50 |
| `test_sell_in_decreases` | (5, 10) | 1 | sell_in | 4 |

> `sell_in = 10` 경계: update 전 sell_in이 10이면 update 후 sell_in = 9 (< 11 조건 진입) → +2.
> `sell_in = 5` 경계: update 전 sell_in이 5이면 update 후 sell_in = 4 (< 6 조건 진입) → +3.

---

### TestSulfuras

| 테스트 메서드 | 초기값 (sell_in, quality) | days | 검증 대상 | 기대값 |
|---|---|---|---|---|
| `test_quality_never_changes` | (0, 80) | 1 | quality | 80 |
| `test_sell_in_never_changes` | (0, 80) | 1 | sell_in | 0 |
| `test_unchanged_over_multiple_days` | (0, 80) | 10 | quality, sell_in | 80, 0 |

---

### TestEdgeCases

| 테스트 메서드 | 내용 |
|---|---|
| `test_multiple_items_updated_independently` | 서로 다른 아이템 2개를 함께 넣었을 때 각각 독립적으로 업데이트됨을 검증 |
| `test_normal_item_quality_0_stays_0_after_expiry` | 이미 quality=0 이고 sell_in도 만료된 경우 질적 변화 없음 |

---

## 경계값 해설

현재 `update_quality()` 코드의 실행 순서 때문에 발생하는 미묘한 경계:

```
sell_in 감소 → sell_in < 0 조건 평가
```

즉, **update 호출 시점의 `sell_in`이 0이면** 감소 후 -1이 되어 만료 조건에 진입한다.
테스트 초기값은 이 순서를 기준으로 작성되어 있다.

---

## 실행 방법

```bash
cd C:\reviewer\workspace\gilded-rose
python -m pytest tests/ -v
```

---

## 완료 기준

- 모든 테스트 케이스가 GREEN
- 기존 `test_foo` 포함 전체 테스트 통과
