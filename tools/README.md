# tools/

Gelistirme ve olcum betikleri (paketin parcasi degildir).

- `fetch_samples.py`, `fetch_holdout.py`: HF'ten orneklem indirir (`samples/`, `samples_ho/`)
- `analyze.py samples_ho [--aggressive] [--show N]`: kapsami olcer, kapsanmayan satirlari siniflar
- `show_unc.py`, `resid.py`, `agg_check.py`: kapsanmayan/agresif donusumleri incelemek icin
- `gap_test.py`: hesap makinesi icin serbest ifade denemeleri

Calistirma: `PYTHONPATH=src python tools/analyze.py samples`
