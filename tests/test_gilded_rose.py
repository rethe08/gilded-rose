import pytest
from gilded_rose import Item, GildedRose

AGED_BRIE = "Aged Brie"
BACKSTAGE_PASS = "Backstage passes to a TAFKAL80ETC concert"
SULFURAS = "Sulfuras, Hand of Ragnaros"


def run_update(name, sell_in, quality, days=1):
    """days 횟수만큼 update_quality를 실행한 뒤 item을 반환한다."""
    item = Item(name, sell_in, quality)
    gilded_rose = GildedRose([item])
    for _ in range(days):
        gilded_rose.update_quality()
    return item


def test_foo():
    items = [Item('foo', 0, 0)]
    gilded_rose = GildedRose(items)
    gilded_rose.update_quality()
    assert items[0].name == 'foo'


class TestNormalItem:
    def test_quality_decreases_by_1(self):
        item = run_update("Normal Item", sell_in=5, quality=10)
        assert item.quality == 9

    def test_sell_in_decreases_by_1(self):
        item = run_update("Normal Item", sell_in=5, quality=10)
        assert item.sell_in == 4

    def test_quality_decreases_twice_after_sell_in_expires(self):
        item = run_update("Normal Item", sell_in=0, quality=10)
        assert item.quality == 8

    def test_quality_never_goes_below_zero(self):
        item = run_update("Normal Item", sell_in=5, quality=0)
        assert item.quality == 0

    def test_quality_zero_after_sell_in_expired_with_quality_1(self):
        item = run_update("Normal Item", sell_in=0, quality=1)
        assert item.quality == 0


class TestAgedBrie:
    def test_quality_increases_by_1(self):
        item = run_update(AGED_BRIE, sell_in=5, quality=10)
        assert item.quality == 11

    def test_sell_in_decreases(self):
        item = run_update(AGED_BRIE, sell_in=5, quality=10)
        assert item.sell_in == 4

    def test_quality_increases_twice_after_sell_in_expires(self):
        item = run_update(AGED_BRIE, sell_in=0, quality=10)
        assert item.quality == 12

    def test_quality_capped_at_50(self):
        item = run_update(AGED_BRIE, sell_in=5, quality=50)
        assert item.quality == 50

    def test_quality_does_not_exceed_50_near_cap(self):
        item = run_update(AGED_BRIE, sell_in=5, quality=49, days=2)
        assert item.quality == 50


class TestBackstagePass:
    def test_quality_increases_by_1_when_far(self):
        item = run_update(BACKSTAGE_PASS, sell_in=15, quality=10)
        assert item.quality == 11

    def test_quality_increases_by_2_when_10_days_left(self):
        item = run_update(BACKSTAGE_PASS, sell_in=10, quality=10)
        assert item.quality == 12

    def test_quality_increases_by_2_when_6_days_left(self):
        item = run_update(BACKSTAGE_PASS, sell_in=6, quality=10)
        assert item.quality == 12

    def test_quality_increases_by_3_when_5_days_left(self):
        item = run_update(BACKSTAGE_PASS, sell_in=5, quality=10)
        assert item.quality == 13

    def test_quality_increases_by_3_when_1_day_left(self):
        item = run_update(BACKSTAGE_PASS, sell_in=1, quality=10)
        assert item.quality == 13

    def test_quality_drops_to_zero_after_concert(self):
        item = run_update(BACKSTAGE_PASS, sell_in=0, quality=10)
        assert item.quality == 0

    def test_quality_capped_at_50(self):
        item = run_update(BACKSTAGE_PASS, sell_in=10, quality=49)
        assert item.quality == 50

    def test_sell_in_decreases(self):
        item = run_update(BACKSTAGE_PASS, sell_in=5, quality=10)
        assert item.sell_in == 4


class TestSulfuras:
    def test_quality_never_changes(self):
        item = run_update(SULFURAS, sell_in=0, quality=80)
        assert item.quality == 80

    def test_sell_in_never_changes(self):
        item = run_update(SULFURAS, sell_in=0, quality=80)
        assert item.sell_in == 0

    def test_unchanged_over_multiple_days(self):
        item = run_update(SULFURAS, sell_in=0, quality=80, days=10)
        assert item.quality == 80
        assert item.sell_in == 0


class TestEdgeCases:
    def test_multiple_items_updated_independently(self):
        normal = Item("Normal Item", sell_in=5, quality=10)
        brie = Item(AGED_BRIE, sell_in=5, quality=10)
        GildedRose([normal, brie]).update_quality()
        assert normal.quality == 9
        assert brie.quality == 11

    def test_normal_item_quality_0_stays_0_after_expiry(self):
        item = run_update("Normal Item", sell_in=0, quality=0)
        assert item.quality == 0
