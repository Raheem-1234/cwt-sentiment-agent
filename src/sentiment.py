"""Sentiment scoring: VADER if installed, else a built-in finance lexicon.
Score range: -1 (very negative) .. +1 (very positive). No heavy downloads."""
import re

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER = SentimentIntensityAnalyzer()
except Exception:
    _VADER = None

POS = {
    "surge":2,"soar":2,"rally":2,"bullish":2,"beat":1.5,"beats":1.5,"upgrade":1.5,"upgraded":1.5,
    "growth":1,"gains":1,"gain":1,"profit":1,"profits":1,"strong":1,"record":1.5,"buy":1,
    "outperform":1.5,"raises":1,"raised":1,"dividend":1,"expansion":1,"wins":1,"win":1,
    "positive":1,"optimistic":1,"breakthrough":1.5,"innovation":1,"demand":0.5,"rise":1,"rises":1,
    "rose":1,"higher":0.5,"jump":1.5,"jumps":1.5,"good":1,"great":1.5,"excellent":2,"boom":1.5,
    "recovery":1,"rebound":1.5,"upside":1,"momentum":0.5,"leader":0.5,"partnership":1,
}
NEG = {
    "crash":-2,"plunge":-2,"plunges":-2,"bearish":-2,"miss":-1.5,"misses":-1.5,"downgrade":-1.5,
    "downgraded":-1.5,"loss":-1,"losses":-1,"weak":-1,"lawsuit":-1.5,"sue":-1.5,"sues":-1.5,
    "fine":-1,"penalty":-1,"ban":-1.5,"fraud":-2,"scandal":-2,"sell":-1,"underperform":-1.5,
    "cuts":-1,"cut":-0.5,"decline":-1,"declines":-1,"fall":-1,"falls":-1,"drop":-1,"drops":-1,
    "lower":-0.5,"negative":-1,"concern":-1,"concerns":-1,"risk":-0.5,"risks":-0.5,"warning":-1,
    "slowdown":-1,"layoff":-1.5,"layoffs":-1.5,"bad":-1,"poor":-1,"worst":-2,"crisis":-2,
    "tumble":-1.5,"slump":-1.5,"pressure":-0.5,"probe":-1,"investigation":-1,
}
NEGATORS = {"not","no","never","isn't","isnt","don't","dont","won't","wont"}

def score_text(text: str) -> float:
    if not text:
        return 0.0
    if _VADER is not None:
        return float(_VADER.polarity_scores(text)["compound"])
    tokens = re.findall(r"[a-z']+", text.lower())
    total, hits = 0.0, 0
    for i, tok in enumerate(tokens):
        w = None
        if tok in POS: w = POS[tok]
        elif tok in NEG: w = NEG[tok]
        if w is not None:
            if i > 0 and tokens[i-1] in NEGATORS:
                w = -w * 0.8
            total += w; hits += 1
    if hits == 0:
        return 0.0
    # squash to [-1, 1]
    import math
    return float(math.tanh(total / 2.0))

def label(score: float) -> str:
    if score >= 0.15: return "Positive"
    if score <= -0.15: return "Negative"
    return "Neutral"
