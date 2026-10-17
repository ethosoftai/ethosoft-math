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
em.calculate("17 mod 5")           # '2'
em.calculate("50'nin %20'si")      # '10'
em.calculate("3 < 5")              # 'dogru'
em.calculate("100 / 3", decimals=2)  # '33.33'
em.calculate("(a+b)^2 = a^2+2ab+b^2")  # 'dogru'
em.calculate("bana 12 * 12 yi hesapla")  # '144'

em.execute('coz("x^2 - 4 = 0", "x")')   # '[-2, 2]'
em.verify(em.convert(text))             # (cagri_sayisi, hatali_sayisi)
em.convert(text, lang="en")             # <tool_call>add(3, 4)</tool_call>...
```

## Araç çalıştırıcı (modelin hesap makinesi)

Model `<arac_cagrisi>` bloğunu yazar; kütüphane içindeki çağrıyı çalıştırıp
`<arac_sonucu>` arasına sonucu yazar:

```python
em.fill_results("<arac_cagrisi>bol(48, 2)</arac_cagrisi>")
# '<arac_cagrisi>bol(48, 2)</arac_cagrisi><arac_sonucu>24</arac_sonucu>'

em.result_block("bol(48, 2)")   # '<arac_sonucu>24</arac_sonucu>'   (sadece sonuç bloğu)
```

Üretim döngüsünde: model `</arac_cagrisi>` yazınca dur → `result_block(metin)` → dönen bloğu ekleyip devam et.
Hata olursa sonuç `HATA: neden` olur; `tanimla(...)` tanımları aynı metinde sonraki çağrılarda geçerlidir.

## Düz metin → tool-use

```python
em.tool_use("Mayıs'ta 48 / 2 = 24 kart, toplam 48 + 24 = 72.")
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

## Translation (EN → TR) — `Ethosoft-Math-Translator`

Since 0.5.0 the library can translate math text to Turkish with the fine-tuned
[`Ethosoft/Ethosoft-Math-Translator`](https://huggingface.co/Ethosoft/Ethosoft-Math-Translator)
(built on [NedoTranslator](https://huggingface.co/nmsofficial/NedoTranslator)). Formulas, symbols, code
and numbers are masked (`[[n]]`), the words are translated, the formulas are put back byte-for-byte; a
row whose formulas cannot be guaranteed is rejected instead of corrupted.

```bash
pip install "Ethosoft-Math[translate]"
```

```python
from ethosoft_math.translate import MathTranslator

t = MathTranslator()
print(t.translate("If $x^2 = 9$, then x = ±3."))
row = t.translate_record({"problem": "What is $1+1$?", "solution": "It is $2$."})   # None if a formula was at risk
```

```bash
ethosoft-math translate "Compute $x^2$ for x = 3."
ethosoft-math translate --input data.jsonl --output data_tr.jsonl
```

The model card lives in `docs/MODEL_CARD.md`.

### Turkish text → tool format

The tool converter understands Turkish solutions too (Unicode units such as `öğrenci`, decimal comma `4,50`,
thousands dot `50.000`, `4,50 $` currency suffix, `x` multiplication, `çarpı / bölü / artı / eksi / eşittir`).
Numbers in the untouched prose keep their Turkish formatting.

```python
import ethosoft_math as em
em.convert("Her biri 4,50 $ olan 2 hamur işi alır, yani bu 2*4,50 = 9,00 $'dır.")
# '… yani bu <arac_cagrisi>carp(2, 4.5)</arac_cagrisi><arac_sonucu>9</arac_sonucu> $'dır.'

# translate EN → TR and convert the calculations to tool calls in one step
from ethosoft_math.translate import MathTranslator
MathTranslator().translate_record({"problem": "...", "solution": "..."}, tools=True)
```

```bash
ethosoft-math translate --input data.jsonl --output data_tr_tools.jsonl --tools
```
