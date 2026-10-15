"""Serbest yazilmis ifadeler icin hesap makinesi: "4 + 5" -> 9.

    >>> from ethosoft_math.calc import calculate
    >>> calculate("4 + 5")
    '9'
    >>> calculate("(3 + 4) x 2 ?")
    '14'
    >>> calculate("2 uzeri 10")
    '1024'
    >>> calculate("1.250,50 + 3,5")
    '1254'
"""
import re
from fractions import Fraction

import sympy

from . import protocol as _P
from .protocol import ToolError, run, to_text

# Turkce / Ingilizce soz -> sembol (sayilar arasinda). Uzunluk degisebilir, ofset gerekmez.
_WORD_OPS = [
    (r"\b(?:arti|artı|plus|ile toplami)\b", " + "),
    (r"\b(?:eksi|minus)\b", " - "),
    (r"\b(?:carpi|çarpı|kere|kez|times|multiplied by)\b", " * "),
    (r"\b(?:bolu|bölü|bolunur|divided by|over)\b", " / "),
    (r"\b(?:uzeri|üzeri|ussu|üssü|power|to the power of)\b", " ^ "),
    (r"\b(?:kare\s*k[oö]k[uü]?|karekok[uü]?)\s*", " sqrt "),
    (r"\byuzde\s*(\d+(?:[.,]\d+)?)\b", r" \1 % "),
]


def _normalize(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[=?\s]+$", "", s)
    s = s.replace("−", "-").replace("–", "-").replace("×", "*").replace("÷", "/").replace("·", "*")
    s = s.replace("**", "^")
    for pat, rep in _WORD_OPS:
        s = re.sub(pat, rep, s, flags=re.I)
    # 1.250,50 -> 1250.50   (Turk yazimi)
    s = re.sub(r"(?<![\d.,])\d{1,3}(?:\.\d{3})+,\d+(?![\d.,])",
               lambda m: m.group(0).replace(".", "").replace(",", "."), s)
    # 3,14 -> 3.14  (ondalik virgul; 1,000 gibi uclu bin ayirac oldugu gibi kalir)
    s = re.sub(r"(?<=\d),(?=\d(?!\d\d(?!\d)))", ".", s)
    s = re.sub(r"(?<=\d),(?=\d{1,2}(?!\d))", ".", s)
    return s


def evaluate(text: str):
    """Ifadeyi hesaplar; Fraction / sympy nesnesi dondurur. Cozulemezse ToolError."""
    from .converter import _make_scan, has_sym, parse_full, tokenize, to_sympy  # gec ice aktarim

    s = _normalize(str(text))
    if not s:
        raise ToolError("bos ifade")
    toks = tokenize(_make_scan(s))
    node = parse_full(toks, allow_syms=False)
    if node is not None and not has_sym(node):
        return run(node)
    node = parse_full(toks, allow_syms=True) if node is None else node
    if node is not None:
        return sympy.simplify(to_sympy(node))
    raise ToolError(f"ifade anlasilamadi: {text!r}")


def calculate(text: str, trace: bool = False, lang: str = None) -> str:
    """'4 + 5' -> '9'.  trace=True: <arac_cagrisi>topla(4, 5)</arac_cagrisi><arac_sonucu>9</arac_sonucu>"""
    lang = lang or _P.LANG
    with _P.use_language(lang):
        value = evaluate(text)
        res = to_text(value)
        if not trace:
            return res
        from .converter import _make_scan, parse_full, render, tokenize
        node = parse_full(tokenize(_make_scan(_normalize(str(text)))), allow_syms=True)
        call = render(node) if node is not None and not isinstance(node, Fraction) else f'hesapla("{text}")'
        out = f"{_P.CALL_OPEN}{call}{_P.CALL_CLOSE}{_P.RES_OPEN}{res}{_P.RES_CLOSE}"
    return _P.localize(out, lang)
