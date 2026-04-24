# SmartChat Automation

Nowoczesny komunikator webowy zbudowany w Pythonie z użyciem FastAPI, WebSocketów, SQLAlchemy, JWT, Celery i Redis. Projekt został przygotowany tak, aby był jednocześnie:

- prosty do uruchomienia lokalnie,
- czytelny i modularny,
- gotowy do dalszego rozwoju,
- użyteczny jako baza do pracy inżynierskiej, licencjackiej lub magisterskiej.

## Najważniejsze funkcje

- rejestracja, logowanie i autoryzacja JWT,
- role `user` i `admin`,
- profile użytkowników z ustawieniami prywatności i powiadomień,
- konwersacje prywatne i grupowe,
- wiadomości realtime przez WebSocket,
- statusy wiadomości: `sent`, `delivered`, `read`, `deleted`,
- edycja i usuwanie własnych wiadomości,
- klasyfikacja wiadomości do kategorii,
- wykrywanie spamu na bazie reguł i heurystyk,
- autoresponder z regułami użytkownika,
- panel administratora ze statystykami, moderacją i logami,
- panel testowy do analiz i scenariuszy demonstracyjnych,
- dokumentacja techniczna i materiały do pracy dyplomowej.

## Stack technologiczny

- Backend: FastAPI
- Realtime: WebSocket
- ORM: SQLAlchemy 2.0
- Walidacja: Pydantic 2
- Baza danych produkcyjna: PostgreSQL
- Cache / broker: Redis
- Automatyzacje: Celery
- Frontend: HTML + CSS + JavaScript
- Migracje: Alembic
- Testy: pytest + httpx + TestClient
- Konteneryzacja: Docker + docker-compose

## Dlaczego frontend bez React?

Zastosowano lekki frontend w czystym HTML/CSS/JS, ponieważ:

- upraszcza to uruchomienie projektu bez dodatkowego toolchainu Node.js,
- lepiej wspiera szybkie wdrożenie akademickie,
- pozwala skupić się na Pythonowym backendzie i logice systemu,
- nadal umożliwia pełną obsługę realtime, panelu admina i testów.

W dokumentacji opisano, jak łatwo zastąpić ten frontend aplikacją React lub Vue w kolejnych etapach rozwoju.

## Architektura i struktura katalogów

```text
.
├── backend/
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   └── app/
│       ├── api/
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       ├── websocket/
│       ├── workers/
│       ├── main.py
│       └── seed.py
├── docs/
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
├── tests/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── pyproject.toml
```

Szczegółowy opis architektury znajduje się w [docs/architecture.md](/Users/darek/Documents/New%20project/docs/architecture.md).

## Szybki start

### Wariant 1: Docker

Najprostsza ścieżka uruchomienia:

```bash
docker-compose up --build
```

Po starcie aplikacja będzie dostępna pod adresem [http://localhost:8000](http://localhost:8000).

### Wariant 2: lokalnie bez Dockera

Projekt uruchomi się także lokalnie z SQLite jako domyślną bazą developerską i z wyłączonym dispatchingiem Celery.

```bash
pip install -e .[dev]
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Jeżeli chcesz przełączyć się na PostgreSQL + Redis, skopiuj `.env.example` do `.env` i ustaw odpowiednie wartości środowiskowe.

## Konta demonstracyjne

Po wykonaniu `python -m app.seed` dostępne są przykładowe konta:

- `admin@smartchat.local` / `Admin123!`
- `alice@smartchat.local` / `Password123!`
- `bob@smartchat.local` / `Password123!`
- `carol@smartchat.local` / `Password123!`

W samym UI można też zalogować się loginem `admin`.

## Najważniejsze pliki

- [backend/app/main.py](/Users/darek/Documents/New%20project/backend/app/main.py)  
  Punkt wejścia aplikacji, konfiguracja FastAPI, CORS, frontend i WebSocket.

- [backend/app/services/message_service.py](/Users/darek/Documents/New%20project/backend/app/services/message_service.py)  
  Główna logika wiadomości, konwersacji, statusów i wyszukiwania.

- [backend/app/services/classification_service.py](/Users/darek/Documents/New%20project/backend/app/services/classification_service.py)  
  Moduł kategoryzacji wiadomości przygotowany pod późniejszą podmianę na ML/NLP.

- [backend/app/services/spam_service.py](/Users/darek/Documents/New%20project/backend/app/services/spam_service.py)  
  Regułowy moduł wykrywania spamu i treści podejrzanych.

- [backend/app/services/autoresponder_service.py](/Users/darek/Documents/New%20project/backend/app/services/autoresponder_service.py)  
  CRUD reguł autorespondera i generowanie automatycznych odpowiedzi.

- [frontend/templates/index.html](/Users/darek/Documents/New%20project/frontend/templates/index.html)  
  Główny interfejs aplikacji.

- [frontend/static/js/app.js](/Users/darek/Documents/New%20project/frontend/static/js/app.js)  
  Logika SPA, API client, WebSockety, panel admina i panel testów.

## Testy

Uruchomienie pełnego zestawu:

```bash
pytest
```

Zakres testów:

- logowanie i rejestracja,
- wysyłanie wiadomości i wyszukiwanie,
- klasyfikacja i spam detection,
- automatyczne odpowiedzi,
- działanie WebSocketów.

## Dokumentacja dodatkowa

- [docs/architecture.md](/Users/darek/Documents/New%20project/docs/architecture.md) – architektura, moduły, baza danych, bezpieczeństwo
- [docs/api-overview.md](/Users/darek/Documents/New%20project/docs/api-overview.md) – przegląd endpointów REST i WebSocket
- [docs/comparison.md](/Users/darek/Documents/New%20project/docs/comparison.md) – porównanie z Messengerem, WhatsAppem, Discordem i Slackiem
- [docs/thesis-materials.md](/Users/darek/Documents/New%20project/docs/thesis-materials.md) – gotowe materiały do pracy dyplomowej

## Dalszy rozwój

Najbardziej naturalne kierunki rozbudowy:

- dodanie modelu ML do klasyfikacji i spamu,
- rozbudowa o załączniki i media,
- zaawansowany system grup i kanałów,
- powiadomienia e-mail / push,
- deployment na chmurę z reverse proxy i obserwowalnością,
- frontend React/Vue jako osobna aplikacja.

