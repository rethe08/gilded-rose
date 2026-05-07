# Gilded Rose Refactoring Plan

## 목표

레거시 `update_quality()` 로직을 안전하게 리팩토링하고 Conjured 아이템 기능을 추가한다.
**모든 단계는 테스트가 통과된 상태를 유지하며 진행한다.**

---

## 원칙

- `Item` 클래스는 절대 수정하지 않는다 (카타 규칙).
- 각 단계 완료 후 전체 테스트를 실행하여 회귀(regression)가 없음을 확인한다.
- 변경 범위가 작은 것 → 큰 것 순서로 진행한다.
- 각 브랜치 작업 전 해당 Phase의 설계 문서(`docs/design/`)를 작성하고 검토 후 진행한다.

---

## 브랜치 전략

작업은 3개의 브랜치로 분리하여 순차적으로 머지한다.

```
main
 ├── branch/1-unit-tests          → PR → main
 ├── branch/2-method-refactoring  → PR → main
 └── branch/3-class-refactoring   → PR → main
```

| 브랜치 | 목적 | 포함 Phase | 핵심 검증 |
|--------|------|-----------|-----------|
| `branch/1-unit-tests` | 리팩토링 안전망 확보 | Phase 1 | coverage 측정 |
| `branch/2-method-refactoring` | 가독성 개선 | Phase 2, 3 | 기존 Unit Test 전부 GREEN |
| `branch/3-class-refactoring` | 확장성 개선 (OCP) | Phase 4, 5 | 기존 Unit Test 전부 GREEN + Conjured 테스트 GREEN |

---

## Branch 1 — `branch/1-unit-tests`

> 설계 문서: `docs/design/phase1_unit_tests.md`
> 머지 전제: coverage 목표치 달성 확인

## Phase 1 — Unit Test 작성 (코드 변경 없음)

> 목적: 리팩토링의 안전망 확보. 현재 동작을 모두 문서화한다.
> coverage 측정 도구: `pytest-cov` (`--cov=gilded_rose --cov-report=term-missing`)

### 1-1. 일반 아이템 (Normal Item)
- [ ] sell_in > 0 일 때 quality가 1 감소한다
- [ ] sell_in > 0 일 때 sell_in이 1 감소한다
- [ ] sell_in = 0 을 지나면 quality가 2씩 감소한다 (만료 후 2배 감소)
- [ ] quality는 0 미만으로 내려가지 않는다

### 1-2. Aged Brie
- [ ] sell_in > 0 일 때 quality가 1 증가한다
- [ ] sell_in 만료 후 quality가 2씩 증가한다
- [ ] quality는 50을 초과하지 않는다

### 1-3. Backstage Passes
- [ ] sell_in > 10 일 때 quality가 1 증가한다
- [ ] sell_in 6~10 일 때 quality가 2 증가한다
- [ ] sell_in 1~5 일 때 quality가 3 증가한다
- [ ] sell_in = 0 이 되면 (콘서트 당일 이후) quality가 0이 된다
- [ ] quality는 50을 초과하지 않는다

### 1-4. Sulfuras, Hand of Ragnaros
- [ ] quality가 변하지 않는다 (항상 80)
- [ ] sell_in이 변하지 않는다

### 1-5. 경계값(Edge Case)
- [ ] quality = 0 인 일반 아이템은 더 이상 감소하지 않는다
- [ ] quality = 50 인 Aged Brie는 더 이상 증가하지 않는다
- [ ] 여러 아이템을 동시에 처리해도 각각 독립적으로 동작한다

---

## Branch 2 — `branch/2-method-refactoring`

> 설계 문서: `docs/design/phase2_method_refactoring.md`
> 머지 전제: Branch 1 머지 완료 + 전체 Unit Test GREEN 확인

## Phase 2 — 표면적 정리 (Small Refactoring)

> 목적: 동작 변경 없이 가독성만 개선한다.

### 2-1. 매직 스트링 → 상수 추출
```python
AGED_BRIE = "Aged Brie"
BACKSTAGE_PASS = "Backstage passes to a TAFKAL80ETC concert"
SULFURAS = "Sulfuras, Hand of Ragnaros"
CONJURED = "Conjured Mana Cake"
MAX_QUALITY = 50
MIN_QUALITY = 0
```

### 2-2. 중복/불명확 표현 제거
- `item.quality = item.quality - item.quality` → `item.quality = 0` 으로 교체
- 중복 `if item.quality < 50` 조건 통합

---

## Phase 3 — 로직 평탄화 (Medium Refactoring)

> 목적: 중첩된 if/else를 품목별로 분리하여 흐름을 명확하게 만든다.

### 3-1. 헬퍼 함수 추출
```python
def _increment_quality(item, amount=1): ...
def _decrement_quality(item, amount=1): ...
```
- quality의 상한(50)·하한(0) 클램핑 로직을 한 곳에서 관리

### 3-2. 아이템별 업데이트 함수 분리
```python
def _update_normal(item): ...
def _update_aged_brie(item): ...
def _update_backstage_pass(item): ...
def _update_sulfuras(item): ...   # no-op
```
- `update_quality()` 의 본체를 dispatch 형태로 단순화

---

## Branch 3 — `branch/3-class-refactoring`

> 설계 문서: `docs/design/phase3_class_refactoring.md`
> 머지 전제: Branch 2 머지 완료 + 전체 Unit Test GREEN 확인

## Phase 4 — 구조적 개선 (Large Refactoring)

> 목적: 새 아이템 추가 시 기존 코드를 수정하지 않아도 되는 구조로 개선한다 (OCP 적용).

### 4-1. 전략(Strategy) 패턴 적용
- 각 아이템 유형별 업데이트 로직을 `dict` 또는 함수 매핑으로 관리
```python
_UPDATERS = {
    AGED_BRIE: _update_aged_brie,
    BACKSTAGE_PASS: _update_backstage_pass,
    SULFURAS: _update_sulfuras,
    CONJURED: _update_conjured,
}
```
- 해당 없는 키는 `_update_normal` 로 폴백(fallback)

### 4-2. `update_quality()` 최종 형태
```python
def update_quality(self):
    for item in self.items:
        updater = _UPDATERS.get(item.name, _update_normal)
        updater(item)
```

---

## Phase 5 — Conjured 아이템 구현

> 목적: 신규 요구사항 추가. Phase 4 구조 덕분에 기존 코드 수정 최소화.

### 5-1. 테스트 먼저 작성
- [ ] sell_in > 0 일 때 quality가 2 감소한다
- [ ] sell_in 만료 후 quality가 4 감소한다
- [ ] quality는 0 미만으로 내려가지 않는다

### 5-2. `_update_conjured` 함수 구현
- `_UPDATERS`에 등록하여 완성

---

## 진행 체크리스트

### Branch 1 — `branch/1-unit-tests`

| 항목 | 상태 |
|------|------|
| 설계 문서 작성 (`phase1_unit_tests.md`) | ✅ |
| 설계 문서 검토 및 승인 | ✅ |
| Phase 1: Unit Test 전체 작성 | ✅ |
| coverage 측정 및 목표치 달성 확인 | ✅ |
| PR → main 머지 | ✅ |

### Branch 2 — `branch/2-method-refactoring`

| 항목 | 상태 |
|------|------|
| 설계 문서 작성 (`phase2_method_refactoring.md`) | ✅ |
| 설계 문서 검토 및 승인 | ✅ |
| Phase 2: 매직 스트링 상수화 + 표현 정리 | ⬜ |
| Phase 3: 헬퍼 함수 + 아이템별 함수 분리 | ⬜ |
| 전체 Unit Test GREEN 확인 | ⬜ |
| PR → main 머지 | ⬜ |

### Branch 3 — `branch/3-class-refactoring`

| 항목 | 상태 |
|------|------|
| 설계 문서 작성 (`phase3_class_refactoring.md`) | ⬜ |
| 설계 문서 검토 및 승인 | ⬜ |
| Phase 4: Strategy 패턴으로 OCP 구조화 | ⬜ |
| Phase 5: Conjured 테스트 + 구현 | ⬜ |
| 전체 Unit Test GREEN 확인 | ⬜ |
| PR → main 머지 | ⬜ |
