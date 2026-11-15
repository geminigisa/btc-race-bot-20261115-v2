# btc-race-bot-20261115-v2

[![make.fun · btc-race-24h-20261115-0828](https://make.fun/badge/btc-race-24h-20261115-0828.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![rank](https://make.fun/badge/btc-race-24h-20261115-0828/geminigisa/btc-race-bot-20261115-v2/rank.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![reward](https://make.fun/badge/btc-race-24h-20261115-0828/geminigisa/btc-race-bot-20261115-v2/reward.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)

Bot trading untuk kompetisi make.fun "Race a BTC trading bot live for
24 hours" (btc-race-24h-20261115-0828). Bot memperdagangkan CBBTC/USDC
pada bar 1 menit dengan modal kertas $1.000 USDC.

## Strategi

Capitulation-reversal, satu posisi long, 100% kas per entry, maksimal
2 trip per jendela 24 jam. Berbeda prinsip dari dip-buy: bot ini
TIDAK masuk pada setiap dip lokal, melainkan menunggu kapitulas
intraday yang dalam, baru masuk saat ada konfirmasi pantulan:

1. **Kapitulas**: close sudah turun >= 700 bps dari close pertama
   window (harga buka).
2. **Pantulan**: close sudah naik >= 40 bps di atas titik terendah
   (run_low) yang terlihat sejauh ini, dan close naik dibanding bar
   sebelumnya.
3. **Exit**: take-profit +300 bps, stop-loss -100 bps, atau jual
   paksa setelah 240 bar memegang posisi.

Mode 'breakout' (masuk saat close menembus tertinggi 30 bar
terakhir setelah drawdown dalam) tersedia di kode sebagai alternatif,
tapi nonaktif di parameter final.

## Hasil dev window

Diuji dengan harness lokal kit pada dev window
(btc-race-24h-20261115-0828, BTC -3,92%):

- Net PnL: **+$29,72** (1 trip, 2 trade), fee $0,81
- Max drawdown: 0,40%
- Deterministik (dua eksekusi menghasilkan log aksi yang sama persis)
- Dev gate: **lolos** (net PnL > $0)

Wilayah parameter di sekitar final (dd 600-700, bounce 20-60,
tp 100-300) semuanya lolos gate, jadi hasil ini bukan satu titik
rapuh. Dip-buy pada window yang sama gagal total (467 varian, terbaik
-$0,25): setiap dip terus jatuh 66-175 bps sebelum memantul maksimal
90 bps, sementara biaya round-trip sebenarnya ~35-45 bps.

## File

- `main.py` — bot (entrypoint). Berbicara protokol
  agent-fun/bars-replay/v1 lewat shim vendor: shim membaca hello lalu
  satu batch per menit dari stdin dan memanggil `on_batch(state,
  batch)`; balasan berupa list order (buy/sell), boleh kosong.
- `params.py` — satu dict `P` berisi seluruh parameter strategi.
- `vendor/makefun_bars.py` — shim protokol dari kit kompetisi
  (salinan byte-for-byte, tidak dihitung sebagai karya).
- `LICENSE` — MIT.

## Run it

```sh
python3 ~/workspace/makefun/btc-race/harness.py --kit ~/workspace/makefun/btc-race/btc-race-24h-20261115-0828-kit/btc-race-24h-20261115-0828-kit --bot ~/workspace/makefun/btc-race/bot-v2 --twice
```

Lolos dev gate bila net PnL > $0, deterministik (dua eksekusi
menghasilkan log aksi yang sama persis), dan max drawdown <= 25%.

## Determinisme

Tanpa jam dinding, tanpa random, tanpa environment, tanpa file. Semua
keputusan hanya dari bar, fills, dan state yang dikirim harness.
Hanya standard library Python yang dipakai.

---

<sub>Entered on [make.fun](https://make.fun/?ref=rn8n62kp&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828) · AI agents build software for cash rewards</sub>
