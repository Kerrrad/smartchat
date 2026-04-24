from pydantic import BaseModel

from app.models.enums import MessageCategoryEnum


class ClassificationResult(BaseModel):
    category: MessageCategoryEnum
    confidence: float
    labels: list[str]
    reasons: list[str]


class RuleBasedMessageClassifier:
    urgent_keywords = {"pilne", "urgent", "asap", "natychmiast", "awaria"}
    announcement_keywords = {"ogloszenie", "announcement", "komunikat", "informacja"}
    offer_keywords = {"oferta", "promocja", "rabat", "discount", "sale"}
    question_keywords = {"czy", "jak", "kiedy", "dlaczego", "gdzie"}

    def classify(self, content: str) -> ClassificationResult:
        normalized = content.lower().strip()
        labels: list[str] = []
        reasons: list[str] = []
        category = MessageCategoryEnum.PRIVATE
        confidence = 0.55

        if any(keyword in normalized for keyword in self.urgent_keywords):
            category = MessageCategoryEnum.URGENT
            confidence = 0.86
            labels.append("priority")
            reasons.append("W treści znaleziono słowa wskazujące na pilność.")
        elif any(keyword in normalized for keyword in self.announcement_keywords):
            category = MessageCategoryEnum.ANNOUNCEMENT
            confidence = 0.78
            labels.append("broadcast")
            reasons.append("Wiadomość przypomina ogłoszenie lub komunikat.")
        elif any(keyword in normalized for keyword in self.offer_keywords):
            category = MessageCategoryEnum.OFFER
            confidence = 0.8
            labels.append("commercial")
            reasons.append("Wykryto słowa kluczowe związane z ofertą lub promocją.")
        elif "?" in normalized or normalized.split(" ")[0:1] and normalized.split(" ")[0] in self.question_keywords:
            category = MessageCategoryEnum.QUESTION
            confidence = 0.82
            labels.append("query")
            reasons.append("Treść ma formę pytania.")
        else:
            reasons.append("Brak cech szczególnych, klasyfikacja jako wiadomość prywatna.")

        return ClassificationResult(
            category=category,
            confidence=confidence,
            labels=labels,
            reasons=reasons,
        )


classifier = RuleBasedMessageClassifier()

