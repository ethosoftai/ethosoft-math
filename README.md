# Ethosoft-Math

Matematik çözümlerindeki **her hesabı** doğrulanmış bir araç çağrısına (tool-use) çeviren kütüphane.
Turn math solutions into verified tool-use traces: `3 + 4 = 7` → `topla(3, 4)` → `7`.

```python
import ethosoft_math as em

em.convert("Toplam 3 + 4 = 7 elma.")
# 'Toplam <arac_cagrisi>topla(3, 4)</arac_cagrisi><arac_sonucu>7</arac_sonucu> elma.'

em.calculate("4 + 5")              # '9'      <- hesap makinesi
em.calculate("2 uzeri 10")         # '1024'
em.calculate("1.250,50 + 3,5")     # '1254'   (Türkçe sayı yazımı)
em.calculate("4 + 5", trace=True)  # '<arac_cagrisi>topla(4, 5)</arac_cagrisi><arac_sonucu>9</arac_sonucu>'

em.execute('coz("x^2 - 4 = 0", "x")')   # '[-2, 2]'
em.verify(em.convert(text))             # (cagri_sayisi, hatali_sayisi)
em.convert(text, lang="en")             # <tool_call>add(3, 4)</tool_call>...
```

## Neden

LLM'e hesabı "kafadan" yaptırmak yerine aracı çağırtmak için eğitim verisi üretirsin.
Her çağrı, çevirme anında **yeniden çalıştırılıp doğrulanır**; tutmayan hiçbir şey çıktıya girmez.
Veride yanlış olan eşitlikler (`2 + 2 = 5`) olduğu gibi bırakılır.

## Protokol (v0.2: Türkçe)

```
<arac_cagrisi>FONKSIYON(arg1, arg2, ...)</arac_cagrisi><arac_sonucu>SONUC</arac_sonucu>
```

| İşlem | Türkçe ad | İngilizce ad |
|---|---|---|
| `a + b` | `topla` | `add` |
| `a - b` | `cikar` | `sub` |
| `a × b` | `carp` | `mul` |
| `a / b` | `bol` | `div` |
| `a ^ b` | `us` | `pow` |
| `√a` | `karekok` | `sqrt` |
| `n!` | `faktoriyel` | `fact` |
| `C(n,k)` | `kombinasyon` | `comb` |
| denklem çöz | `coz` | `solve` |
| serbest ifade | `hesapla` | `calc` |

- Türkçe ve İngilizce adların ikisi de çalışır (`execute("add(3, 4)")` = `execute("topla(3, 4)")`).
- Sonuç kelimeleri: `dogru` / `yanlis` / `bos` / `HATA: ...`.
- Gruplar: aritmetik, yüzde, sayı teorisi, üs/log, trigonometri, geometri, olasılık/istatistik,
  diziler, cebir, analiz, lineer cebir, fonksiyon tanımlama (`tanimla`).
- Tam liste: `ethosoft-math protocol`

## Komut satırı

```bash
ethosoft-math calc "4 + 5"
ethosoft-math exec "carp(topla(3, 4), 2)"
ethosoft-math protocol > PROTOCOL.md
ethosoft-math convert in.jsonl out.jsonl --field solution [--lang en] [--aggressive]
```

## Çalışma modları

| Mod | Ne yapar |
|---|---|
| `convert(text)` (varsayılan) | Yalnızca doğrulanabilen eşitlikleri, denklemleri, eşitsizlikleri, toplamları çevirir |
| `convert(text, aggressive=True)` | Ek olarak `=` içermeyen salt-sayısal işlemleri de çevirir |
| `lang="en"` | Etiket ve fonksiyon adlarını İngilizce üretir |

## Sınırlar

- Python/PoT kodu içeren çözümlere dokunmaz.
- İspat ve sözel anlatım satırlarında çağrı üretilmez (hesap yoktur).
- Çeviri modelinden önce çalıştırılmalıdır; araç blokları çeviriden korunmalıdır.

Lisans: MIT
