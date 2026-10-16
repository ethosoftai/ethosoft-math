"""Matematik dataset'lerini indirip TEK ORTAK BICIME cevirir (ceviri oncesi asama).

Ortak kayit (JSONL, satir basina bir kayit):

    id        "<kaynak>:<alt>:<split>:<sira>"      kararli kimlik
    source    HF dataset adi                       "openai/gsm8k"
    subset    config/alt kume                      "main", "algebra" ...
    split     "train" | "test" ...
    index     kaynaktaki sira
    problem   Ingilizce soru
    solution  Ingilizce adim adim cozum (kaynaktaki haliyle)
    answer    son cevap (varsa/cikarilabiliyorsa)  "72", "\\frac{1}{2}"
    kind      "word_problem" | "competition" | "mcq" | "code" | "reasoning" ...
    topic     konu etiketi (varsa)
    level     zorluk (varsa)
    has_code  cozum Python kodu iceriyor mu
    lang      "en"
    meta      kaynaga ozgu ek alanlar

Kullanim (TRUBA login node, internet gerekir):

    python -m ethosoft_math.data list
    python -m ethosoft_math.data collect --out $ROOT/raw --limit 0            # hepsi
    python -m ethosoft_math.data collect --out $ROOT/raw --sources gsm8k,math --limit 1000
    python -m ethosoft_math.data merge   --inp $ROOT/raw --out $ROOT/all.jsonl
    python -m ethosoft_math.data stats   --inp $ROOT/all.jsonl

`datasets` yalnizca collect sirasinda (tembel) ice aktarilir; paketin zorunlu bagimliligi degildir.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List, Optional

_CODE_RE = re.compile(r"^\s*(print\(|def |import |from \w+ import |for .+ in |return )|```python", re.M)


# ------------------------------------------------------------------ yardimcilar
def extract_boxed(text: str) -> Optional[str]:
    """Metindeki SON \\boxed{...} icerigi (ic ice suslu parantezli)."""
    if not text:
        return None
    last = None
    for m in re.finditer(r"\\boxed\s*\{", text):
        i, depth = m.end(), 1
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        if depth == 0:
            last = text[m.end():i - 1].strip()
    return last


def _clean(s) -> str:
    if s is None:
        return ""
    return str(s).replace("\r\n", "\n").replace("\r", "\n").strip()


def _topic_level(r, topic_key="type", level_key="level"):
    return r.get(topic_key), r.get(level_key)


# ------------------------------------------------------------------ kaynak esleyiciler
# Her esleyici: ham satir -> dict(problem, solution, answer?, kind?, topic?, level?, meta?)
def _gsm8k(r):
    sol = _clean(r["answer"])
    return dict(problem=r["question"], solution=sol, answer=sol.split("####")[-1].strip() if "####" in sol else None,
                kind="word_problem")


def _math(r):
    sol = _clean(r["solution"])
    return dict(problem=r["problem"], solution=sol, answer=extract_boxed(sol), kind="competition",
                topic=r.get("type"), level=r.get("level"))


def _metamath(r):
    sol = _clean(r["response"])
    m = re.search(r"The answer is:\s*(.+?)\s*$", sol, re.S)
    ans = m.group(1).strip() if m else extract_boxed(sol)
    return dict(problem=r["query"], solution=sol, answer=ans, kind="word_problem", topic=r.get("type"),
                meta={"original_question": r.get("original_question")})


def _orca(r):
    return dict(problem=r["question"], solution=_clean(r["answer"]), kind="word_problem")


def _mathinstruct(r):
    out = _clean(r["output"])
    return dict(problem=r["instruction"], solution=out, kind="code" if _CODE_RE.search(out) else "reasoning",
                meta={"origin": r.get("source")})


def _openr1(r):
    sol = _clean(r.get("solution"))
    return dict(problem=r["problem"], solution=sol, answer=r.get("answer"), kind="competition",
                topic=r.get("problem_type"), meta={"source": r.get("source"), "question_type": r.get("question_type")})


def _deepmath(r):
    return dict(problem=r["question"], solution=_clean(r.get("r1_solution_1")), answer=r.get("final_answer"),
                kind="reasoning", topic=r.get("topic"), level=r.get("difficulty"))


def _numina(r):
    return dict(problem=r["problem"], solution=_clean(r["solution"]), answer=extract_boxed(_clean(r["solution"])),
                kind="competition", meta={"source": r.get("source")})


def _numina_tir(r):
    return dict(problem=r["problem"], solution=_clean(r["solution"]), answer=extract_boxed(_clean(r["solution"])),
                kind="code")


def _deepscaler(r):
    return dict(problem=r["problem"], solution=_clean(r.get("solution")), answer=r.get("answer"), kind="competition")


def _aqua(r):
    opts = r.get("options") or []
    problem = _clean(r["question"])
    if opts:
        problem += "\n" + "\n".join(str(o) for o in opts)
    return dict(problem=problem, solution=_clean(r.get("rationale")), answer=r.get("correct"), kind="mcq")


def _openmathinstruct2(r):
    return dict(problem=r["problem"], solution=_clean(r["generated_solution"]), answer=r.get("expected_answer"),
                kind="word_problem" if "gsm8k" in str(r.get("problem_source")) else "competition",
                meta={"problem_source": r.get("problem_source")})


def _openmathreasoning(r):
    return dict(problem=r["problem"], solution=_clean(r["generated_solution"]), answer=r.get("expected_answer"),
                kind="reasoning", topic=r.get("problem_type"),
                meta={"problem_source": r.get("problem_source"), "pass_rate_72b_tir": r.get("pass_rate_72b_tir")})


def _nemotron_v2(r):
    sol = ""
    for m in r.get("messages") or []:
        if isinstance(m, dict) and m.get("role") == "assistant":
            sol = _clean(m.get("content") or m.get("reasoning_content"))
    return dict(problem=r.get("problem"), solution=sol, answer=r.get("expected_answer"), kind="reasoning",
                meta={"data_source": r.get("data_source")})


@dataclass
class Source:
    key: str
    path: str
    mapper: Callable
    splits: tuple = ("train",)
    configs: tuple = (None,)
    split_overrides: Dict[Optional[str], tuple] = field(default_factory=dict)
    heavy: bool = False
    note: str = ""


_MATH_CONFIGS = ("algebra", "counting_and_probability", "geometry", "intermediate_algebra",
                 "number_theory", "prealgebra", "precalculus")

SOURCES: Dict[str, Source] = {s.key: s for s in [
    Source("gsm8k", "openai/gsm8k", _gsm8k, splits=("train", "test"), configs=("main",)),
    Source("math", "EleutherAI/hendrycks_math", _math, splits=("train", "test"), configs=_MATH_CONFIGS),
    Source("metamathqa", "meta-math/MetaMathQA", _metamath),
    Source("orca-math", "microsoft/orca-math-word-problems-200k", _orca),
    Source("mathinstruct", "TIGER-Lab/MathInstruct", _mathinstruct),
    Source("openr1", "open-r1/OpenR1-Math-220k", _openr1, configs=("default",)),
    Source("deepmath", "zwhe99/DeepMath-103K", _deepmath, note="r1_solution_1 (uzun akil yurutme)"),
    Source("numina-cot", "AI-MO/NuminaMath-CoT", _numina),
    Source("numina-tir", "AI-MO/NuminaMath-TIR", _numina_tir),
    Source("deepscaler", "agentica-org/DeepScaleR-Preview-Dataset", _deepscaler),
    Source("aqua-rat", "deepmind/aqua_rat", _aqua, splits=("train", "validation", "test"), configs=("raw",)),
    Source("openmathinstruct2", "nvidia/OpenMathInstruct-2", _openmathinstruct2, splits=("train_1M",),
           note="NVIDIA'nin resmi 1M alt kumesi; tamami icin splits=train (14M)"),
    Source("openmathreasoning-cot", "nvidia/OpenMathReasoning", _openmathreasoning, splits=("cot",), heavy=True,
           note="3.2M uzun cozum, ~72GB"),
    Source("nemotron-math-v2-low", "nvidia/Nemotron-Math-v2", _nemotron_v2, splits=("low",), heavy=True),
]}


# ------------------------------------------------------------------ normallestirme
def normalize_row(src: Source, row: dict, subset: Optional[str], split: str, index: int) -> Optional[dict]:
    """Ham satir -> ortak kayit. Problem veya cozum bossa None."""
    try:
        m = src.mapper(row)
    except (KeyError, TypeError):
        return None
    problem, solution = _clean(m.get("problem")), _clean(m.get("solution"))
    if not problem or not solution:
        return None
    has_code = bool(_CODE_RE.search(solution))
    kind = m.get("kind") or "reasoning"
    if has_code and kind not in ("mcq",):
        kind = "code"
    sub = subset or "-"
    meta = {k: v for k, v in (m.get("meta") or {}).items() if v is not None}
    return {
        "id": f"{src.key}:{sub}:{split}:{index}",
        "source": src.path,
        "subset": subset,
        "split": split,
        "index": index,
        "problem": problem,
        "solution": solution,
        "answer": None if m.get("answer") is None else _clean(m.get("answer")),
        "kind": kind,
        "topic": m.get("topic"),
        "level": m.get("level"),
        "has_code": has_code,
        "lang": "en",
        "meta": meta,
    }


def iter_source(key: str, limit: int = 0, streaming: bool = True, cache_dir: Optional[str] = None) -> Iterator[dict]:
    """Bir kaynagin tum config/split'lerini ortak kayit olarak uretir. limit=0: sinirsiz (config/split basina)."""
    from datasets import load_dataset  # tembel

    src = SOURCES[key]
    for cfg in src.configs:
        for split in src.split_overrides.get(cfg, src.splits):
            kw = dict(path=src.path, split=split, streaming=streaming)
            if cfg is not None:
                kw["name"] = cfg
            if cache_dir:
                kw["cache_dir"] = cache_dir
            ds = load_dataset(**kw)
            for i, row in enumerate(ds):
                if limit and i >= limit:
                    break
                rec = normalize_row(src, row, cfg, split, i)
                if rec is not None:
                    yield rec


# ------------------------------------------------------------------ toplama / birlestirme
def collect(out_dir: str, keys: Iterable[str], limit: int = 0, force: bool = False, include_heavy: bool = False,
            cache_dir: Optional[str] = None, log=print) -> Dict[str, dict]:
    """Her kaynagi <out_dir>/<key>.jsonl dosyasina yazar (var olan dosya atlanir: devam edilebilir)."""
    os.makedirs(out_dir, exist_ok=True)
    report = {}
    for key in keys:
        src = SOURCES[key]
        if src.heavy and not include_heavy:
            log(f"[atla] {key} (agir; --include-heavy ile)")
            continue
        path = os.path.join(out_dir, f"{key}.jsonl")
        if os.path.exists(path) and not force:
            log(f"[var ] {key} -> {path}")
            continue
        tmp = path + ".part"
        t0, n, skipped = time.time(), 0, 0
        with open(tmp, "w", encoding="utf-8") as f:
            try:
                for rec in iter_source(key, limit=limit, cache_dir=cache_dir):
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
                    if n % 20000 == 0:
                        log(f"  {key}: {n} satir ({time.time() - t0:.0f}s)")
            except Exception as ex:  # tek kaynagin hatasi digerlerini durdurmasin
                log(f"[HATA] {key}: {type(ex).__name__}: {str(ex)[:200]}")
                report[key] = {"error": str(ex)[:300], "rows": n}
                continue
        os.replace(tmp, path)
        report[key] = {"rows": n, "seconds": round(time.time() - t0, 1), "path": path}
        log(f"[tamam] {key}: {n} satir")
    with open(os.path.join(out_dir, "_collect_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def _fingerprint(rec: dict) -> str:
    norm = re.sub(r"\s+", " ", rec["problem"].lower()).strip()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def merge(in_dir: str, out_path: str, dedupe: str = "problem", log=print) -> dict:
    """<in_dir>/*.jsonl dosyalarini tek dosyada birlestirir.

    dedupe='problem': ayni soru metni (kucuk harf, bosluk normal) ilk gorulen kaynakta kalir.
    dedupe='none'   : hicbir sey atilmaz.
    """
    seen, stats = set(), {"total_in": 0, "written": 0, "dup": 0, "by_source": {}, "by_kind": {}}
    files = sorted(p for p in os.listdir(in_dir) if p.endswith(".jsonl"))
    with open(out_path, "w", encoding="utf-8") as out:
        for name in files:
            with open(os.path.join(in_dir, name), encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    stats["total_in"] += 1
                    if dedupe == "problem":
                        fp = _fingerprint(rec)
                        if fp in seen:
                            stats["dup"] += 1
                            continue
                        seen.add(fp)
                    out.write(line if line.endswith("\n") else line + "\n")
                    stats["written"] += 1
                    stats["by_source"][rec["source"]] = stats["by_source"].get(rec["source"], 0) + 1
                    stats["by_kind"][rec["kind"]] = stats["by_kind"].get(rec["kind"], 0) + 1
    log(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


def stats(path: str) -> dict:
    n = chars_p = chars_s = 0
    by_kind, by_src, code = {}, {}, 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            n += 1
            chars_p += len(r["problem"])
            chars_s += len(r["solution"])
            code += bool(r.get("has_code"))
            by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
            by_src[r["source"]] = by_src.get(r["source"], 0) + 1
    return {"rows": n, "avg_problem_chars": round(chars_p / max(1, n)), "avg_solution_chars": round(chars_s / max(1, n)),
            "total_chars": chars_p + chars_s, "with_code": code, "by_kind": by_kind, "by_source": by_src}


# ------------------------------------------------------------------ komut satiri
def main(argv: Optional[List[str]] = None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="python -m ethosoft_math.data")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="kaynaklari listele")

    c = sub.add_parser("collect", help="kaynaklari indir ve ortak bicime cevir")
    c.add_argument("--out", required=True)
    c.add_argument("--sources", default="", help="virgullu anahtarlar; bos = hepsi (agirlar haric)")
    c.add_argument("--limit", type=int, default=0, help="config/split basina en fazla N satir (0 = hepsi)")
    c.add_argument("--force", action="store_true")
    c.add_argument("--include-heavy", action="store_true")
    c.add_argument("--cache-dir", default=None)

    m = sub.add_parser("merge", help="ham dosyalari tek dosyada birlestir (+tekilleştir)")
    m.add_argument("--inp", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--dedupe", choices=["problem", "none"], default="problem")

    s = sub.add_parser("stats", help="birlesik dosyanin ozeti")
    s.add_argument("--inp", required=True)

    a = ap.parse_args(argv)
    if a.cmd == "list":
        for k, s_ in SOURCES.items():
            flag = " [agir]" if s_.heavy else ""
            print(f"{k:24s} {s_.path}{flag}  {s_.note}")
    elif a.cmd == "collect":
        keys = [k.strip() for k in a.sources.split(",") if k.strip()] or list(SOURCES)
        bad = [k for k in keys if k not in SOURCES]
        if bad:
            sys.exit(f"bilinmeyen kaynak: {bad}")
        collect(a.out, keys, limit=a.limit, force=a.force, include_heavy=a.include_heavy, cache_dir=a.cache_dir)
    elif a.cmd == "merge":
        merge(a.inp, a.out, dedupe=a.dedupe)
    elif a.cmd == "stats":
        print(json.dumps(stats(a.inp), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
