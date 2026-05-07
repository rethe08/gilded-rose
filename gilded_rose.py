_AGED_BRIE      = "Aged Brie"
_BACKSTAGE_PASS = "Backstage passes to a TAFKAL80ETC concert"
_SULFURAS       = "Sulfuras, Hand of Ragnaros"
_CONJURED       = "Conjured Mana Cake"

_MAX_QUALITY = 50
_MIN_QUALITY = 0


def _increase_quality(item, amount=1):
    item.quality = min(item.quality + amount, _MAX_QUALITY)


def _decrease_quality(item, amount=1):
    item.quality = max(item.quality - amount, _MIN_QUALITY)


def _update_normal(item):
    _decrease_quality(item)
    item.sell_in -= 1
    if item.sell_in < 0:
        _decrease_quality(item)


def _update_aged_brie(item):
    _increase_quality(item)
    item.sell_in -= 1
    if item.sell_in < 0:
        _increase_quality(item)


def _update_backstage_pass(item):
    _increase_quality(item)
    if item.sell_in < 11:
        _increase_quality(item)
    if item.sell_in < 6:
        _increase_quality(item)
    item.sell_in -= 1
    if item.sell_in < 0:
        item.quality = _MIN_QUALITY


def _update_sulfuras(item):
    pass


def _update_conjured(item):
    _decrease_quality(item, amount=2)
    item.sell_in -= 1
    if item.sell_in < 0:
        _decrease_quality(item, amount=2)


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


class Item:
    def __init__(self, name, sell_in, quality):
        self.name = name
        self.sell_in = sell_in
        self.quality = quality

    def __repr__(self):
        return "%s, %s, %s" % (self.name, self.sell_in, self.quality)
