"""Ethosoft-Math: matematik cozumlerini dogrulanmis tool-use izlerine ceviren kutuphane.

    >>> import ethosoft_math as em
    >>> em.convert("Toplam 3 + 4 = 7 elma.")
    'Toplam <arac_cagrisi>topla(3, 4)</arac_cagrisi><arac_sonucu>7</arac_sonucu> elma.'
    >>> em.execute("topla(3, 4)")
    '7'
    >>> em.calculate("4 + 5")
    '9'
"""
from .protocol import (  # noqa: F401
    CALL_OPEN, CALL_CLOSE, RES_OPEN, RES_CLOSE, REG, ToolError, TR_NAMES, EN_NAMES,
    execute, parse_call, run, render_protocol_md, localize, delocalize, set_language,
)
from .calc import calculate, evaluate  # noqa: F401
from .converter import convert_text, verify_converted  # noqa: F401

__version__ = "0.2.0"


def convert(text: str, aggressive: bool = False, lang: str = None) -> str:
    """Metindeki dogrulanabilir hesaplari arac cagrilarina cevirir; sadece metni dondurur.
    lang: 'tr' (varsayilan, <arac_cagrisi>/topla) veya 'en' (<tool_call>/add)."""
    return convert_text(text, aggressive=aggressive, lang=lang)[0]


def verify(text: str):
    """Metindeki her arac cagrisini yeniden calistirir; (toplam, hatali) dondurur."""
    return verify_converted(text)


def functions():
    """Protokoldeki fonksiyonlar: {ad: {cat, sig, doc}}"""
    return {k: {"cat": v["cat"], "sig": v["sig"], "doc": v["doc"]} for k, v in REG.items()}
