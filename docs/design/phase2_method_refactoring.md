# Phase 2 설계 문서 — 메서드 레벨 리팩토링

## 목적

`update_quality()` 의 깊이 중첩된 if/else 구조를 **가독성 중심**으로 정리한다.
동작은 변경하지 않으며, Branch 1에서 작성한 24개 Unit Test가 전부 GREEN을 유지해야 한다.

코드 변경 범위: `gilded_rose.py` 만 수정. `Item` 클래스는 건드리지 않는다.

---

## 포함 Phase

| Phase | 내용 |
|-------|------|
| Phase 2 | 매직 스트링 상수화 + 불명확 표현 정리 |
| Phase 3 | 헬퍼 함수 추출 + 아이템별 업데이트 함수 분리 |

---

## Phase 2 — 표면적 정리

### 2-1. 매직 스트링 → 모듈 상수 추출

현재 `update_quality()` 안에 아이템 이름이 문자열 리터럴로 4회 중복 등장한다.
오타에 취약하고 향후 Branch 3의 dispatch 구조를 준비하기 위해 상수로 올린다.

```python
# gilded_rose.py 상단에 추가
_AGED_BRIE       = "Aged Brie"
_BACKSTAGE_PASS  = "Backstage passes to a TAFKAL80ETC concert"
_SULFURAS        = "Sulfuras, Hand of Ragnaros"
_CONJURED        = "Conjured Mana Cake"

_MAX_QUALITY = 50
_MIN_QUALITY = 0
```

> 언더스코어 prefix(`_`)를 붙여 모듈 내부 상수임을 명시한다.
> 테스트 파일의 상수(`AGED_BRIE` 등)는 독립적으로 선언되어 있으므로 변경하지 않는다.

### 2-2. 불명확 표현 제거

| 위치 | 현재 코드 | 변경 후 |
|------|-----------|---------|
| `gilded_rose.py:30` | `item.quality = item.quality - item.quality` | `item.quality = _MIN_QUALITY` |

---

## Phase 3 — 로직 평탄화

### 3-1. 헬퍼 함수 2개 추출

quality 변경 시 항상 상한(50)·하한(0) 클램핑이 필요하다.
이 로직을 헬퍼로 한 곳에서 관리하면 중복 `if quality < 50` / `if quality > 0` 조건이 사라진다.

```python
def _increase_quality(item, amount=1):
    item.quality = min(item.quality + amount, _MAX_QUALITY)

def _decrease_quality(item, amount=1):
    item.quality = max(item.quality - amount, _MIN_QUALITY)
```

### 3-2. 아이템별 업데이트 함수 4개 추출

`update_quality()` 의 if/else 분기를 아이템 유형별 함수로 분리한다.
각 함수는 **sell_in 감소 포함** 완결된 하루치 처리를 담당한다.

#### `_update_normal(item)`
```python
def _update_normal(item):
    _decrease_quality(item)
    item.sell_in -= 1
    if item.sell_in < 0:
        _decrease_quality(item)
```

#### `_update_aged_brie(item)`
```python
def _update_aged_brie(item):
    _increase_quality(item)
    item.sell_in -= 1
    if item.sell_in < 0:
        _increase_quality(item)
```

#### `_update_backstage_pass(item)`
```python
def _update_backstage_pass(item):
    _increase_quality(item)
    if item.sell_in < 11:
        _increase_quality(item)
    if item.sell_in < 6:
        _increase_quality(item)
    item.sell_in -= 1
    if item.sell_in < 0:
        item.quality = _MIN_QUALITY
```

> **주의**: Backstage Pass는 sell_in 감소 전에 증가 판정을 해야 기존 동작과 동일하다.
> 현재 코드의 실행 순서를 그대로 보존한다.

#### `_update_sulfuras(item)` — no-op
```python
def _update_sulfuras(item):
    pass  # sell_in, quality 모두 변경하지 않는다
```

### 3-3. `update_quality()` 최종 형태

```python
def update_quality(self):
    for item in self.items:
        if item.name == _AGED_BRIE:
            _update_aged_brie(item)
        elif item.name == _BACKSTAGE_PASS:
            _update_backstage_pass(item)
        elif item.name == _SULFURAS:
            _update_sulfuras(item)
        else:
            _update_normal(item)
```

중첩 depth: 기존 최대 5단계 → **2단계**로 감소.

---

## 변경 전/후 비교

### 변경 전 (`update_quality` 본체, 34줄)
```python
def update_quality(self):
    for item in self.items:
        if item.name != "Aged Brie" and item.name != "Backstage passes to a TAFKAL80ETC concert":
            if item.quality > 0:
                if item.name != "Sulfuras, Hand of Ragnaros":
                    item.quality = item.quality - 1
        else:
            if item.quality < 50:
                item.quality = item.quality + 1
                if item.name == "Backstage passes to a TAFKAL80ETC concert":
                    if item.sell_in < 11:
                        if item.quality < 50:
                            item.quality = item.quality + 1
                    if item.sell_in < 6:
                        if item.quality < 50:
                            item.quality = item.quality + 1
        if item.name != "Sulfuras, Hand of Ragnaros":
            item.sell_in = item.sell_in - 1
        if item.sell_in < 0:
            if item.name != "Aged Brie":
                if item.name != "Backstage passes to a TAFKAL80ETC concert":
                    if item.quality > 0:
                        if item.name != "Sulfuras, Hand of Ragnaros":
                            item.quality = item.quality - 1
                else:
                    item.quality = item.quality - item.quality
            else:
                if item.quality < 50:
                    item.quality = item.quality + 1
```

### 변경 후 (`update_quality` 본체, 8줄)
```python
def update_quality(self):
    for item in self.items:
        if item.name == _AGED_BRIE:
            _update_aged_brie(item)
        elif item.name == _BACKSTAGE_PASS:
            _update_backstage_pass(item)
        elif item.name == _SULFURAS:
            _update_sulfuras(item)
        else:
            _update_normal(item)
```

---

## 검증 계획

1. 리팩토링 완료 후 `pytest tests/ -v` 실행 → 24개 전부 GREEN
2. `pytest tests/ --cov=gilded_rose --cov-report=term-missing` → coverage 97% 이상 유지
3. 신규 Conjured 테스트는 추가하지 않는다 (Branch 3 범위)

---

## 완료 기준

- 24개 기존 Unit Test 전부 GREEN
- `gilded_rose.py` 에 매직 스트링 리터럴 미존재
- `update_quality()` 중첩 depth 2 이하
- `Item` 클래스 무변경
