import re

from pydantic import BaseModel


class SpamDetectionResult(BaseModel):
    is_spam: bool
    score: float
    reasons: list[str]


class RuleBasedSpamDetector:
    suspicious_keywords = {
        "gratis",
        "zarobek",
        "kliknij",
        "crypto",
        "bitcoin",
        "natychmiast zysk",
        "free money",
        "winner",
    }

    def detect(self, content: str) -> SpamDetectionResult:
        text = content.strip()
        normalized = text.lower()
        score = 0.0
        reasons: list[str] = []

        urls = len(re.findall(r"(https?://|www\.)", normalized))
        if urls >= 1:
            score += 0.25 if urls == 1 else 0.4
            reasons.append("Wiadomość zawiera podejrzane odnośniki.")

        matched_keywords = [word for word in self.suspicious_keywords if word in normalized]
        if matched_keywords:
            score += min(0.5, 0.12 * len(matched_keywords))
            reasons.append(f"Wykryto podejrzane słowa kluczowe: {', '.join(matched_keywords)}.")

        if re.search(r"(.)\1{5,}", text):
            score += 0.15
            reasons.append("Wiadomość zawiera nienaturalne powtórzenia znaków.")

        uppercase_ratio = sum(1 for char in text if char.isupper()) / max(len(text), 1)
        if len(text) > 20 and uppercase_ratio > 0.45:
            score += 0.2
            reasons.append("Nadmierna liczba wielkich liter.")

        if text.count("!") >= 4:
            score += 0.15
            reasons.append("Duża liczba wykrzykników sugeruje spam.")

        is_spam = score >= 0.5
        if not reasons:
            reasons.append("Brak wyraźnych oznak spamu.")

        return SpamDetectionResult(is_spam=is_spam, score=min(score, 1.0), reasons=reasons)


spam_detector = RuleBasedSpamDetector()
