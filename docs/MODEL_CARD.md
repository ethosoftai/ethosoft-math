---
language:
- en
- tr
license: cc-by-nc-4.0
library_name: transformers
pipeline_tag: translation
base_model: nmsofficial/NedoTranslator
tags:
- translation
- marian
- english
- turkish
- math
- latex
- symbol-preserving
- mathematics
- ethosoft
---

<div align="center">

# 🧮 Ethosoft-Math-Translator

### English → Turkish translation for **mathematics** — formulas, symbols and numbers survive intact.

[![Base](https://img.shields.io/badge/base-NedoTranslator-blue)](https://huggingface.co/nmsofficial/NedoTranslator)
[![Params](https://img.shields.io/badge/params-236.9M-informational)]()
[![Pairs](https://img.shields.io/badge/fine--tune%20pairs-161K-success)]()
[![Placeholder%20integrity](https://img.shields.io/badge/formula%20integrity-99.3%25-brightgreen)]()
[![Library](https://img.shields.io/badge/pip-Ethosoft--Math-orange)](https://github.com/ethosoftai/ethosoft-math)

</div>

General-purpose MT models are good at prose and terrible at math: they translate `\frac{a}{b}` into
nonsense, "fix" decimal points, drop `±`, `√`, `∑`, CJK characters, and silently change numbers.
**Ethosoft-Math-Translator** is [NedoTranslator](https://huggingface.co/nmsofficial/NedoTranslator)
fine-tuned so that mathematical content is treated as *untouchable*: it translates the words around
the math and hands every formula back byte-for-byte.

```text
EN  Since $x^2-4=(x-2)(x+2)$, the solutions are x = ±2, so the sum is 0.
TR  $x^2-4=(x-2)(x+2)$ olduğundan, çözümler x = ±2'dir, bu yüzden toplam 0'dır.

EN  Compute $\sqrt{16} + 3^2$. First, $\sqrt{16}=4$ and $3^2=9$, hence the total is $13$.
TR  $\sqrt{16} + 3^2$ değerini hesaplayın. Önce $\sqrt{16}=4$ ve $3^2=9$, dolayısıyla toplam $13$'tür.

EN  Evaluate ∑_{k=1}^{10} k × 2 ≤ 110. 你好
TR  ∑_{k=1}^{10} k × 2 ≤ 110 değerini hesaplayın. 你好
```

*(real, unedited outputs of the released checkpoint)*

## How it works

```
  text ──► mask ──► translate line by line ──► check ──► restore ──► Turkish text
           │                                     │
           │  LaTeX ($..$, $$..$$, \[..\], \begin..\end),
           │  code, URLs, tool-call blocks, math Unicode (±×÷√∑∫≤≥≠…),
           │  CJK, and characters missing from the vocabulary
           └─► become  [[1]] [[2]] …  (renumbered per line)
```

The model was fine-tuned to **copy `[[n]]` placeholders exactly** while translating everything else.
After translation every placeholder is verified and substituted back; a line whose placeholders were
damaged is rejected instead of being silently corrupted. This is why formulas can never be
"translated" or altered.

## Quick start

The easiest way is the [`Ethosoft-Math`](https://github.com/ethosoftai/ethosoft-math) library, which
ships the masking / restoring pipeline:

```bash
pip install "Ethosoft-Math[translate]"
```

```python
from ethosoft_math.translate import MathTranslator

t = MathTranslator()   # downloads Ethosoft/Ethosoft-Math-Translator
print(t.translate("If $x^2 = 9$, then x = ±3.\nThe answer is $\\boxed{3}$ or $-3$."))
# Eğer $x^2 = 9$ ise, x = ±3.
# Cevap $\boxed{3}$ veya $-3$'tür.

# whole records (e.g. dataset rows); returns None if any formula could not be preserved
row = t.translate_record({"problem": "What is $\\frac{1}{2}+\\frac{1}{3}$?", "solution": "It is $\\frac{5}{6}$."})
```

Or from the command line:

```bash
ethosoft-math translate "Compute $\\sqrt{16} + 3^2$."
ethosoft-math translate --input data.jsonl --output data_tr.jsonl     # adds problem_tr / solution_tr
```

### Plain 🤗 Transformers

The raw model works on **already masked** text. If you call it directly, mask math yourself
(see `ethosoft_math.translate.protect_all`) – feeding raw LaTeX to the model is not what it was trained for.

```python
from transformers import MarianMTModel, MarianTokenizer
tok = MarianTokenizer.from_pretrained("Ethosoft/Ethosoft-Math-Translator")
model = MarianMTModel.from_pretrained("Ethosoft/Ethosoft-Math-Translator")

batch = tok(["Therefore the value of [[1]] is [[2]]."], return_tensors="pt")
out = model.generate(**batch, num_beams=4, max_new_tokens=256)
print(tok.batch_decode(out, skip_special_tokens=True))   # Turkish sentence with [[1]] and [[2]] kept verbatim
```

## Results

Held-out evaluation (rows never seen in fine-tuning; hash-based split):

| Metric | NedoTranslator (base) | **Ethosoft-Math-Translator** |
|---|---:|---:|
| Validation loss (masked lines) | 0.701 | **0.373** |
| Placeholder integrity, line level (all `[[n]]` reproduced) | 68.5 % | **99.3 %** |
| End-to-end rows passing *all* quality gates¹ (276 unseen rows) | – | **94.9 %** |

¹ numbers unchanged, formulas unchanged, answer preserved, no foreign scripts, Turkish output, same structure.
Of the 5.1 % rejected rows, 11 were placeholder failures and 3 changed a number – they are *dropped*, not emitted.

On sampled rows the output is close to the teacher's translations (see below); we did not run a
human evaluation, so treat fluency claims accordingly.

## In production: 755,035 rows translated

The released checkpoint was run over the full pool of math corpora (on top of the 27,768 teacher-translated
rows used for training). Every row went through the same quality gate; rows that failed were **deleted, not repaired**.

| Dataset | Translated | Rejected | Pass rate |
|---|---:|---:|---:|
| MetaMathQA | 382,532 | 8,180 | 97.9 % |
| MathInstruct | 111,186 | 6,061 | 94.8 % |
| OpenR1-Math | 78,894 | 10,767 | 88.0 % |
| NuminaMath-TIR | 64,772 | 4,944 | 92.9 % |
| Orca-Math | 59,239 | 2,584 | 95.8 % |
| AQuA-RAT | 40,103 | 1,295 | 96.9 % |
| MATH | 7,886 | 858 | 90.2 % |
| GSM8K | 6,228 | 171 | 97.3 % |
| DeepScaleR | 4,195 | 1,537 | 73.2 % |
| **Total** | **755,035** | **36,397** | **95.4 %** |

Main rejection reasons: a placeholder was damaged (17.7 k), a number changed (17.2 k), answer lost (0.6 k),
formula changed (0.5 k), output not Turkish (0.4 k). Throughput on a single H100: ~10–19 rows/s (beam 4).
Hard competition sets such as DeepScaleR lose the most rows because their solutions are dense with formulas.

## Training

* **Base**: [`nmsofficial/NedoTranslator`](https://huggingface.co/nmsofficial/NedoTranslator) (MarianMT, 236.9 M parameters),
  itself fine-tuned from [`Helsinki-NLP/opus-mt-tc-big-en-tr`](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-tr).
* **Teacher data**: 27,768 math problems + solutions translated into Turkish by a strong LLM
  (DeepSeek-V4 Flash, reasoning off, via the Evren LLM gateway) under a strict quality gate, then
  masked and split into **161,085 aligned line pairs** (1,412 held out).
  Source corpora: GSM8K, MATH, MetaMathQA, Orca-Math, MathInstruct, OpenR1-Math, NuminaMath-TIR,
  DeepScaleR, AQuA-RAT.
* **Quality gate** for teacher output (rows failing any check were deleted, ~4–10 % per dataset):
  number multiset preserved · every formula block preserved · gold answer still present ·
  every CJK/math symbol of the source present · no foreign script added · Turkish-ness · line structure.
* **Recipe**: 3 epochs, AdamW, lr 5e-5 (linear warm-up/decay), label smoothing 0.1, bf16, ~12 k tokens/batch,
  1 × H100 (≈ 4 minutes), TRUBA HPC.

## Intended use & limitations

* ✅ Translating math word problems, solutions, proofs and textbook-style exposition EN → TR, especially to build Turkish math datasets.
* ✅ Pipelines that must keep formulas/numbers exactly (the library rejects rows it cannot guarantee).
* ⚠️ Text *inside* masked blocks (e.g. `\text{if } n …` inside a LaTeX block, or code comments) is **not translated**.
* ⚠️ Translations inherit the teacher model's style and mistakes; terminology is not hand-verified.
* ⚠️ Long lines are truncated at 256 tokens – the library splits input by line, so keep one idea per line.
* ⚠️ English → Turkish only.

## License

Released under **CC BY-NC 4.0**. The upstream NedoTranslator card lists `cc-by-nc-2.0` in its metadata and
"CC BY 4.0" in its text; we adopt the more restrictive non-commercial terms until that is clarified.
Please also retain attribution to the upstream models below.

## Attribution & citation

This work stands on **NedoTranslator** by *nmsofficial* — please credit it:
<https://huggingface.co/nmsofficial/NedoTranslator> — which in turn builds on Helsinki-NLP's OPUS-MT:

```bibtex
@inproceedings{tiedemann-thottingal-2020-opus,
  title     = {{OPUS-MT} -- Building open translation services for the World},
  author    = {Tiedemann, J{\"o}rg and Thottingal, Santhosh},
  booktitle = {Proceedings of the 22nd Annual Conference of the European Association for Machine Translation},
  year      = {2020}
}
```

If you use Ethosoft-Math-Translator:

```bibtex
@misc{ethosoft_math_translator_2026,
  title        = {Ethosoft-Math-Translator: Symbol-Preserving English-to-Turkish Mathematical Translation},
  author       = {Ethosoft},
  year         = {2026},
  howpublished = {\url{https://huggingface.co/Ethosoft/Ethosoft-Math-Translator}},
  note         = {Fine-tuned from NedoTranslator (nmsofficial)}
}
```

<div align="center"><sub>Made by <a href="https://github.com/ethosoftai">Ethosoft</a> · Ethosoft-Math library: <a href="https://github.com/ethosoftai/ethosoft-math">github.com/ethosoftai/ethosoft-math</a></sub></div>
