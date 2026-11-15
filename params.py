"""Parameter strategi capitulation-reversal (lihat main.py).

mode: 'bounce' (masuk saat close memantul bounce_bps di atas run_low)
    atau 'breakout' (masuk saat close menembus tertinggi breakout_n
    bar terakhir).
dd_bps: close harus sudah turun sekian bps dari close pertama window.
bounce_bps: konfirmasi pantulan, close harus naik sekian bps di atas
    titik terendah sejauh ini (mode bounce).
breakout_n: jendela tertinggi untuk breakout (mode breakout).
up_confirm: bila 1, close harus naik dibanding bar sebelumnya
    (mode bounce).
tp_bps: take-profit di atas cost (basis poin).
sl_bps: stop-loss di bawah cost (basis poin).
max_hold: jual paksa setelah sekian bar memegang posisi.
trail_bps: trailing stop setelah TP tercapai (nonaktif bila None).
max_trips: jumlah maksimum trip (buy fill) dalam satu jendela.
no_entry_last: jangan entry pada sekian bar terakhir jendela.
size_bps: ukuran posisi sebagai bps dari kas (10000 = penuh).

Parameter final (terverifikasi harness --twice, dev gate lolos):
dd 700 / bounce 40 / tp 300 / sl 100 / max_hold 240 / trips 2.
Net PnL dev window +$29,72, 1 trip, max drawdown 0,40%.
Dipilih karena wilayah sekitarnya juga lolos (dd 600-700, bounce
20-60, tp 100-300 semuanya positif), bukan satu titik rapuh.
"""

P = {'mode': 'bounce', 'dd_bps': 700, 'bounce_bps': 40, 'breakout_n': 30,
     'up_confirm': 1, 'tp_bps': 300, 'sl_bps': 100, 'max_hold': 240,
     'trail_bps': None, 'max_trips': 2, 'no_entry_last': 60,
     'size_bps': 10000}
