# Phase 3 설계 문서 — 클래스 레벨 리팩토링 (OCP)

## 목적

새로운 아이템 유형을 추가할 때 **기존 코드를 수정하지 않아도** 되는 구조를 만든다.
Open-Closed Principle(OCP): 확장에 열려 있고, 수정에 닫혀 있어야 한다.

아울러 Conjured 아이템(신규 요구사항)을 구현한다.

---

## 현재 구조의 문제점

`update_quality()` 의 if/elif 체인은 새 아이템 추가 시 반드시 이 메서드를 수정해야 한다.

```python
# 새 아이템 추가 시 여기를 건드려야 함 → OCP 위반
def update_quality(self):
    for item in self.items:
        if item.name == _AGED_BRIE:
            ...
        elif item.name == _BACKSTAGE_PASS:
            ...
        elif item.name == _SULFURAS:
            ...
        elif item.name == _CONJURED:      # ← 추가할 때마다 수정
            ...
        else:
            _update_normal(item)
```

---

## 설계 방향: Strategy 패턴 (dict dispatch)

아이템 이름 → 업데이트 함수를 딕셔너리로 매핑한다.
새 아이템은 딕셔너리에 항목만 추가하면 되며, `GildedRose` 클래스는 수정하지 않는다.

```python
_UPDATERS: dict[str, Callable] = {
    _AGED_BRIE:      _update_aged_brie,
    _BACKSTAGE_PASS: _update_backstage_pass,
    _SULFURAS:       _update_sulfuras,
    _CONJURED:       _update_conjured,   # 신규 추가
}
```

`update_quality()` 는 dispatch만 담당한다.

```python
def update_quality(self):
    for item in self.items:
        updater = _UPDATERS.get(item.name, _update_normal)
        updater(item)
```

**새 아이템 추가 흐름:**
1. `_update_xxx(item)` 함수 작성
2. `_UPDATERS`에 `{이름: 함수}` 한 줄 추가
3. `GildedRose` 클래스 수정 없음 ✓

---

## Phase 4 — Strategy 패턴 적용

### 변경 사항

`gilded_rose.py` 에서 if/elif 체인 제거, `_UPDATERS` 딕셔너리 추가:

```python
_UPDATERS = {
    _AGED_BRIE:      _update_aged_brie,
    _BACKSTAGE_PASS: _update_backstage_pass,
    _SULFURAS:       _update_sulfuras,
    _CONJURED:       _update_conjured,
}

class GildedRose(object):
    def __init__(self, items):
        self.items = items

    def update_quality(self):
        for item in self.items:
            updater = _UPDATERS.get(item.name, _update_normal)
            updater(item)
```

---

## Phase 5 — Conjured 아이템 구현

### 비즈니스 규칙

- 일반 아이템의 **2배** 속도로 quality 감소
- sell_in 만료 후에도 2배 감소 (만료 전 -2, 만료 후 -4)
- quality는 0 미만으로 내려가지 않는다

### 테스트 케이스 (테스트 먼저 작성)

`tests/test_gilded_rose.py` 에 `TestConjured` 클래스 추가:

| 테스트 메서드 | 초기값 (sell_in, quality) | days | 기대값 |
|---|---|---|---|
| `test_quality_decreases_by_2` | (5, 10) | 1 | quality=8 |
| `test_sell_in_decreases` | (5, 10) | 1 | sell_in=4 |
| `test_quality_decreases_by_4_after_sell_in_expires` | (0, 10) | 1 | quality=6 |
| `test_quality_never_goes_below_zero` | (5, 1) | 1 | quality=0 |
| `test_quality_zero_stays_zero_after_expiry` | (0, 0) | 1 | quality=0 |

### `_update_conjured` 구현

```python
def _update_conjured(item):
    _decrease_quality(item, amount=2)
    item.sell_in -= 1
    if item.sell_in < 0:
        _decrease_quality(item, amount=2)
```

`_decrease_quality` 의 클램핑 덕분에 quality < 0 보호가 자동으로 처리된다.

---

## 최종 `gilded_rose.py` 전체 구조

```
[상수]
  _AGED_BRIE, _BACKSTAGE_PASS, _SULFURAS, _CONJURED
  _MAX_QUALITY, _MIN_QUALITY

[헬퍼]
  _increase_quality(item, amount)
  _decrease_quality(item, amount)

[아이템별 업데이트 함수]
  _update_normal(item)
  _update_aged_brie(item)
  _update_backstage_pass(item)
  _update_sulfuras(item)       ← no-op
  _update_conjured(item)       ← 신규

[dispatch 테이블]
  _UPDATERS = { ... }

[클래스]
  GildedRose.update_quality()  ← dispatch만 담당, 수정 없음
  Item                         ← 변경 없음
```

---

## 검증 계획

1. **테스트 먼저**: `TestConjured` 5개 케이스 작성 → RED 확인 (구현 전)
2. `_update_conjured` 구현 → GREEN 확인
3. 기존 24개 테스트 전부 GREEN 유지 확인
4. `pytest --cov=gilded_rose --cov-report=term-missing` → coverage 측정

---

## 완료 기준

- 기존 24개 + Conjured 5개 = **총 29개 테스트 GREEN**
- `GildedRose.update_quality()` 에 if/elif 미존재
- 새 아이템 추가 시 `_UPDATERS` 딕셔너리와 함수만 추가하면 됨 (OCP 달성)
- `Item` 클래스 무변경
