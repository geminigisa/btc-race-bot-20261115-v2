"""Bot trading capitulation-reversal untuk kompetisi make.fun
"Race a BTC trading bot" (race btc-race-24h-20261115-0828).

Strategi
--------
Berbeda prinsip dari dip-buy: bot ini TIDAK masuk pada setiap dip
lokal. Ia menunggu sampai harga jatuh DALAM dari harga buka window
(kapitulas intraday), baru masuk saat ada konfirmasi pantulan:

* mode 'bounce': close sudah turun >= dd_bps dari close pertama
  window, DAN close sudah naik >= bounce_bps di atas titik terendah
  (run_low) yang terlihat sejauh ini, DAN (bila up_confirm) close
  naik dibanding bar sebelumnya;
* mode 'breakout': close sudah turun >= dd_bps dari close pertama,
  DAN close menembus di atas tertinggi breakout_n bar terakhir
  (menangkap kaki pemulihan setelah dasar terbentuk).

Satu posisi long CBBTC/USDC per trip, maksimal max_trips trip dalam
jendela 1440 bar. Ukuran posisi size_bps dari kas (10000 = penuh).

Exit satu posisi, yang mana dulu tercapai:

* take-profit tp_bps di atas cost (atau trailing bila trail_bps
  diisi), stop-loss sl_bps di bawah cost, atau max_hold bar.

Protokol
--------
Berbicara agent-fun/bars-replay/v1 lewat shim vendor: shim membaca
NDJSON dari stdin (hello, lalu satu batch per menit, lalu done) dan
memanggil on_batch(state, batch); balasan berupa list order (boleh
kosong). Satu batch membawa bar yang baru tutup, fills dari order
batch sebelumnya, dan akun. Order yang diputuskan pada batch menit t
terisi pada open bar berikutnya.

Determinisme
------------
Penuh: tanpa jam dinding, tanpa random, tanpa environment, tanpa file.
Semua state berasal dari bar, fills, dan state yang dikirim harness.
Dua eksekusi pada data yang sama menghasilkan order yang sama persis.
Hanya standard library yang dipakai.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "vendor"))

import makefun_bars

from params import P

SYMBOL = "CBBTC"
BPS = 10000
WINDOW_BARS = 1440

# Riwayat harga per bar CBBTC.
closes = []

# State strategi.
trips_started = 0   # berapa buy fill yang sudah diterima
entry_seq = None    # seq batch saat posisi sekarang mulai dipegang
peak_value = None   # nilai posisi tertinggi sejak entry (untuk trailing)


def on_batch(state, batch):
    global trips_started, entry_seq, peak_value

    # 1. Serap semua bar CBBTC dari batch ini (o/h/l/c bisa berupa
    #    angka atau string angka, jadi pakai int()).
    for bar in batch.get("bars", []):
        if bar.get("symbol") != SYMBOL:
            continue
        closes.append(int(bar["c"]))

    # 2. Hitung buy fill: tiap buy yang terisi memulai satu trip.
    for fill in batch.get("fills", []):
        if (fill.get("symbol") == SYMBOL
                and fill.get("status") == "filled"
                and fill.get("side") == "buy"):
            trips_started += 1

    # 3. Lacak posisi: catat entry_seq dan peak_value saat posisi baru
    #    muncul; bersihkan saat posisi sudah tidak ada.
    held = state.positions.get(SYMBOL)
    holding = held is not None and held.qty
    if holding:
        # Posisi baru pertama kali terlihat pada batch setelah fill buy
        # dilaporkan, jadi entry_seq menandai batch itu dan bars_held
        # dihitung dari sana (bukan dari batch saat order dikirim).
        if entry_seq is None:
            entry_seq = state.seq
            peak_value = state.value(SYMBOL, held.qty)
    else:
        entry_seq = None
        peak_value = None

    # 4. EXIT: bila sedang memegang posisi.
    if holding:
        value = state.value(SYMBOL, held.qty)
        cost = held.cost
        if peak_value is None or value > peak_value:
            peak_value = value
        bars_held = state.seq - entry_seq

        sell = False
        if P["trail_bps"] is not None:
            armed = peak_value * BPS >= cost * (BPS + P["tp_bps"])
            if armed and value * BPS <= peak_value * (BPS - P["trail_bps"]):
                sell = True
        elif value * BPS >= cost * (BPS + P["tp_bps"]):
            sell = True
        if not sell:
            if P["sl_bps"] is not None and value * BPS <= cost * (BPS - P["sl_bps"]):
                sell = True
            elif bars_held >= P["max_hold"]:
                sell = True
        if sell:
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": 100}]
        return []

    # 5. ENTRY: bila tidak memegang posisi.
    if trips_started >= P["max_trips"]:
        return []
    if len(closes) < 2:
        return []
    if state.seq >= WINDOW_BARS - P["no_entry_last"]:
        return []

    close = closes[-1]
    open_price = closes[0]
    run_low = min(closes)

    # Filter kapitulas: close harus sudah turun >= dd_bps dari harga
    # buka window.
    if close * BPS > open_price * (BPS - P["dd_bps"]):
        return []

    mode = P["mode"]
    if mode == "bounce":
        # Konfirmasi pantulan: close naik >= bounce_bps di atas titik
        # terendah sejauh ini.
        if close * BPS < run_low * (BPS + P["bounce_bps"]):
            return []
        if P["up_confirm"] and close <= closes[-2]:
            return []
    elif mode == "breakout":
        # Konfirmasi breakout: close menembus tertinggi breakout_n
        # bar terakhir (tidak termasuk bar ini).
        n = P["breakout_n"]
        if len(closes) < n + 1:
            return []
        if close <= max(closes[-n - 1:-1]):
            return []
    else:
        return []

    # Beli size_bps dari kas (dibatasi weight_room), selama di atas
    # notional minimum. max_slippage 100bps dipertahankan seperti bot
    # asli: pada pengujian, batas ini justru menolak entry lompatan
    # curam yang merugi (batas 200 malah mengisi entry tersebut dan
    # mengubah hasil jadi -$25,31).
    amount = min(state.cash, state.weight_room(SYMBOL))
    amount = amount * P["size_bps"] // BPS
    if amount < int(state.hello["fees"]["min_notional_quote_units"]):
        return []
    return [{"side": "buy", "symbol": SYMBOL,
             "notional_quote_units": amount, "max_slippage_bps": 100}]


makefun_bars.run(on_batch)
