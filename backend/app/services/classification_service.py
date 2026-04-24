from pydantic import BaseModel

from app.models.enums import MessageCategoryEnum


class ClassificationResult(BaseModel):
    category: MessageCategoryEnum
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

        if any(keyword in normalized for keyword in self.urgent_keywords):
            category = MessageCategoryEnum.URGENT
            labels.append("priority")
            reasons.append("W tresci znaleziono slowa wskazujace na pilnosc.")
        elif any(keyword in normalized for keyword in self.announcement_keywords):
            category = MessageCategoryEnum.ANNOUNCEMENT
            labels.append("broadcast")
            reasons.append("Wiadomosc przypomina ogloszenie lub komunikat.")
        elif any(keyword in normalized for keyword in self.offer_keywords):
            category = MessageCategoryEnum.OFFER
            labels.append("commercial")
            reasons.append("Wykryto slowa kluczowe zwiazane z oferta lub promocja.")
        elif "?" in normalized or normalized.split(" ")[0:1] and normalized.split(" ")[0] in self.question_keywords:
            category = MessageCategoryEnum.QUESTION
            labels.append("query")
            reasons.append("Tresc ma forme pytania.")
        else:
            reasons.append("Brak cech szczegolnych, klasyfikacja jako wiadomosc prywatna.")

        return ClassificationResult(
            category=category,
            labels=labels,
            reasons=reasons,
        )


classifier = RuleBasedMessageClassifier()
