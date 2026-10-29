(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.MoneyLogic = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  var CATEGORIES = {
    expense: ['食費', '交通費', '日用品', '娯楽', 'その他'],
    income: ['給料', '副収入', 'その他'],
  };

  function sumBy(list, fn) {
    var total = 0;
    for (var i = 0; i < list.length; i++) total += fn(list[i]);
    return total;
  }

  // 移動は収支に数えず、2枚のカードの残高だけを動かす
  function cardBalance(state, cardId) {
    var card = state.cards.find(function (c) { return c.id === cardId; });
    if (!card) return 0;
    var balance = card.opening;
    state.tx.forEach(function (t) {
      if (t.type === 'income' && t.cardId === cardId) balance += t.amount;
      else if (t.type === 'expense' && t.cardId === cardId) balance -= t.amount;
      else if (t.type === 'transfer') {
        if (t.cardId === cardId) balance -= t.amount;
        if (t.toCardId === cardId) balance += t.amount;
      }
    });
    return balance;
  }

  function totalBalance(state) {
    return sumBy(state.cards, function (c) { return cardBalance(state, c.id); });
  }

  function monthSummary(state, ym) {
    var income = 0;
    var expense = 0;
    state.tx.forEach(function (t) {
      if (t.date.slice(0, 7) !== ym) return;
      if (t.type === 'income') income += t.amount;
      else if (t.type === 'expense') expense += t.amount;
    });
    return { income: income, expense: expense, net: income - expense };
  }

  function wishStatus(state, wish) {
    var total = totalBalance(state);
    var perCard = state.cards.map(function (c) {
      var bal = cardBalance(state, c.id);
      return { cardId: c.id, name: c.name, canBuy: bal >= wish.price, short: Math.max(0, wish.price - bal) };
    });
    return {
      canBuyTotal: total >= wish.price,
      shortTotal: Math.max(0, wish.price - total),
      canBuyWithOneCard: perCard.some(function (p) { return p.canBuy; }),
      perCard: perCard,
    };
  }

  function wishlistSummary(state) {
    var sum = sumBy(state.wishes, function (w) { return w.price; });
    return { sum: sum, short: Math.max(0, sum - totalBalance(state)) };
  }

  function toAmount(value) {
    var n = Number(value);
    return isFinite(n) && n >= 0 && Math.floor(n) === n ? n : null;
  }

  function normalizeState(raw) {
    if (!raw || typeof raw !== 'object') throw new Error('データの形式が正しくありません');
    if (!Array.isArray(raw.cards) || raw.cards.length !== 2) throw new Error('カードは2枚必要です');
    var cards = raw.cards.map(function (c) {
      var opening = Number(c.opening);
      if (!c || !c.id || !isFinite(opening) || Math.floor(opening) !== opening) throw new Error('カードの情報が正しくありません');
      return { id: String(c.id), name: String(c.name || 'カード'), opening: opening };
    });
    var ids = cards.map(function (c) { return c.id; });
    var tx = (raw.tx || []).map(function (t) {
      var amount = toAmount(t.amount);
      var ok = amount !== null && /^\d{4}-\d{2}-\d{2}$/.test(t.date) &&
        ['income', 'expense', 'transfer'].indexOf(t.type) >= 0 && ids.indexOf(t.cardId) >= 0 &&
        (t.type !== 'transfer' || (ids.indexOf(t.toCardId) >= 0 && t.toCardId !== t.cardId));
      if (!ok) throw new Error('取引のデータが正しくありません');
      return {
        id: String(t.id), type: t.type, amount: amount, cardId: t.cardId,
        toCardId: t.type === 'transfer' ? t.toCardId : undefined,
        category: String(t.category || ''), date: t.date, memo: String(t.memo || ''),
      };
    });
    var wishes = (raw.wishes || []).map(function (w) {
      var price = toAmount(w.price);
      if (price === null || !w.name) throw new Error('ほしい物のデータが正しくありません');
      return { id: String(w.id), name: String(w.name), price: price };
    });
    return { cards: cards, tx: tx, wishes: wishes, sample: raw.sample === true };
  }

  function formatYen(n) {
    var s = '¥' + Math.abs(n).toLocaleString('ja-JP');
    return n < 0 ? '−' + s : s;
  }

  function shiftMonth(ym, delta) {
    var y = Number(ym.slice(0, 4));
    var m = Number(ym.slice(5, 7)) - 1 + delta;
    y += Math.floor(m / 12);
    m = ((m % 12) + 12) % 12;
    return y + '-' + String(m + 1).padStart(2, '0');
  }

  function newId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  }

  return {
    CATEGORIES: CATEGORIES, cardBalance: cardBalance, totalBalance: totalBalance,
    monthSummary: monthSummary, wishStatus: wishStatus, wishlistSummary: wishlistSummary,
    normalizeState: normalizeState, formatYen: formatYen, shiftMonth: shiftMonth, newId: newId,
  };
});
