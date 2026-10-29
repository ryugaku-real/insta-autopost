const test = require('node:test');
const assert = require('node:assert');
const L = require('./logic.js');

function base() {
  return {
    cards: [
      { id: 'a', name: 'カードA', opening: 10000 },
      { id: 'b', name: 'カードB', opening: 5000 },
    ],
    tx: [],
    wishes: [],
  };
}

test('収入は残高を増やし、支出は減らす', () => {
  const s = base();
  s.tx.push({ id: '1', type: 'income', amount: 3000, cardId: 'a', category: '給料', date: '2026-10-01', memo: '' });
  s.tx.push({ id: '2', type: 'expense', amount: 800, cardId: 'a', category: '食費', date: '2026-10-02', memo: '' });
  s.tx.push({ id: '3', type: 'expense', amount: 200, cardId: 'b', category: '食費', date: '2026-10-02', memo: '' });
  assert.strictEqual(L.cardBalance(s, 'a'), 12200);
  assert.strictEqual(L.cardBalance(s, 'b'), 4800);
  assert.strictEqual(L.totalBalance(s), 17000);
});

test('カード間の移動は合計を変えず、収支にも数えない', () => {
  const s = base();
  s.tx.push({ id: '1', type: 'transfer', amount: 4000, cardId: 'a', toCardId: 'b', category: '', date: '2026-10-03', memo: '' });
  assert.strictEqual(L.cardBalance(s, 'a'), 6000);
  assert.strictEqual(L.cardBalance(s, 'b'), 9000);
  assert.strictEqual(L.totalBalance(s), 15000);
  assert.deepStrictEqual(L.monthSummary(s, '2026-10'), { income: 0, expense: 0, net: 0 });
});

test('月ごとの集計は指定した月だけを数える', () => {
  const s = base();
  s.tx.push({ id: '1', type: 'income', amount: 1000, cardId: 'a', category: '給料', date: '2026-10-31', memo: '' });
  s.tx.push({ id: '2', type: 'income', amount: 9000, cardId: 'a', category: '給料', date: '2026-11-01', memo: '' });
  s.tx.push({ id: '3', type: 'expense', amount: 400, cardId: 'b', category: '食費', date: '2026-10-05', memo: '' });
  assert.deepStrictEqual(L.monthSummary(s, '2026-10'), { income: 1000, expense: 400, net: 600 });
});

test('ほしい物は合計と1枚ごとで買えるか判定する', () => {
  const s = base();
  const ok = L.wishStatus(s, { id: 'w', name: 'イヤホン', price: 12000 });
  assert.strictEqual(ok.canBuyTotal, true);
  assert.strictEqual(ok.canBuyWithOneCard, false);
  assert.strictEqual(ok.perCard[0].short, 2000);
  const ng = L.wishStatus(s, { id: 'w', name: 'PC', price: 20000 });
  assert.strictEqual(ng.canBuyTotal, false);
  assert.strictEqual(ng.shortTotal, 5000);
});

test('ほしい物の合計と、全部買うのに足りない額', () => {
  const s = base();
  s.wishes.push({ id: '1', name: 'A', price: 9000 }, { id: '2', name: 'B', price: 10000 });
  assert.deepStrictEqual(L.wishlistSummary(s), { sum: 19000, short: 4000 });
});

test('不正なデータは読み込みで弾く', () => {
  assert.throws(() => L.normalizeState(null));
  assert.throws(() => L.normalizeState({ cards: [], tx: [] }));
  const s = base();
  s.tx.push({ id: '1', type: 'expense', amount: -5, cardId: 'a', date: '2026-10-01' });
  assert.throws(() => L.normalizeState(s));
  const same = base();
  same.tx.push({ id: '1', type: 'transfer', amount: 5, cardId: 'a', toCardId: 'a', date: '2026-10-01' });
  assert.throws(() => L.normalizeState(same));
});

test('正しいデータは読み込める', () => {
  const s = base();
  s.wishes.push({ id: '1', name: 'A', price: 100 });
  assert.deepStrictEqual(L.normalizeState(JSON.parse(JSON.stringify(s))).wishes[0].price, 100);
});

test('月の切り替えは年をまたぐ', () => {
  assert.strictEqual(L.shiftMonth('2026-12', 1), '2027-01');
  assert.strictEqual(L.shiftMonth('2026-01', -1), '2025-12');
});

test('円表記', () => {
  assert.strictEqual(L.formatYen(12345), '¥12,345');
  assert.strictEqual(L.formatYen(-500), '−¥500');
});
