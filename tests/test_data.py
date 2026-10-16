import json

from ethosoft_math import data as D


def test_extract_boxed_nested_and_last():
    assert D.extract_boxed(r"so \boxed{\frac{1}{2}} and then \boxed{3}") == "3"
    assert D.extract_boxed(r"x = \boxed{\frac{a}{b}}") == r"\frac{a}{b}"
    assert D.extract_boxed("no box") is None


def test_gsm8k_mapping():
    r = D.normalize_row(D.SOURCES["gsm8k"], {"question": "Q?", "answer": "48/2 = <<48/2=24>>24\n#### 24"},
                        "main", "train", 7)
    assert r["id"] == "gsm8k:main:train:7"
    assert r["answer"] == "24" and r["kind"] == "word_problem" and r["lang"] == "en"
    assert r["has_code"] is False


def test_math_mapping_extracts_boxed_and_level():
    r = D.normalize_row(D.SOURCES["math"], {"problem": "P", "solution": r"Thus $\boxed{12}$.",
                                            "level": "Level 3", "type": "Algebra"}, "algebra", "test", 0)
    assert r["answer"] == "12" and r["level"] == "Level 3" and r["topic"] == "Algebra"
    assert r["kind"] == "competition"


def test_metamath_answer_line():
    r = D.normalize_row(D.SOURCES["metamathqa"], {"query": "Q", "response": "work\nThe answer is: 42", "type": "GSM_Rephrased",
                                                  "original_question": "oq"}, None, "train", 1)
    assert r["answer"] == "42" and r["topic"] == "GSM_Rephrased"
    assert r["meta"]["original_question"] == "oq"


def test_code_solution_is_flagged():
    r = D.normalize_row(D.SOURCES["mathinstruct"], {"instruction": "Q", "output": "x = 3 + 4\nprint(x)", "source": "pot"},
                        None, "train", 0)
    assert r["has_code"] is True and r["kind"] == "code"


def test_aqua_options_in_problem_and_mcq():
    r = D.normalize_row(D.SOURCES["aqua-rat"], {"question": "Q", "options": ["A)1", "B)2"], "rationale": "R", "correct": "B"},
                        "raw", "train", 0)
    assert r["kind"] == "mcq" and "A)1" in r["problem"] and r["answer"] == "B"


def test_empty_rows_are_dropped():
    assert D.normalize_row(D.SOURCES["orca-math"], {"question": "", "answer": "x"}, None, "train", 0) is None
    assert D.normalize_row(D.SOURCES["orca-math"], {"nope": 1}, None, "train", 0) is None


def test_merge_dedupes_by_problem(tmp_path):
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    rec = lambda p, s: json.dumps({"problem": p, "solution": s, "source": "x", "kind": "reasoning"})
    a.write_text(rec("What is 2+2?", "4") + "\n" + rec("Other", "o") + "\n", encoding="utf-8")
    b.write_text(rec("what  is 2+2?", "four") + "\n", encoding="utf-8")
    out = tmp_path / "all.jsonl"
    st = D.merge(str(tmp_path), str(out), log=lambda *_: None)
    assert st["total_in"] == 3 and st["written"] == 2 and st["dup"] == 1
    assert D.stats(str(out))["rows"] == 2


def test_registry_has_expected_sources():
    for k in ("gsm8k", "math", "metamathqa", "orca-math", "mathinstruct", "openr1", "deepmath",
              "numina-cot", "deepscaler", "aqua-rat", "openmathinstruct2"):
        assert k in D.SOURCES
    assert D.SOURCES["openmathreasoning-cot"].heavy
