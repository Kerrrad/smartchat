# Architektura projektu

## 1. Przegląd

System został zaprojektowany w stylu warstwowym:

1. warstwa prezentacji: frontend HTML/CSS/JS,
2. warstwa API: routery FastAPI,
3. warstwa logiki biznesowej: serwisy,
4. warstwa danych: SQLAlchemy + PostgreSQL,
5. warstwa asynchroniczna: Celery + Redis,
6. warstwa realtime: WebSocket manager.

Taki układ upraszcza testowanie, rozbudowę i późniejsze dołączenie modeli NLP/ML.

## 2. Główne moduły

### `backend/app/core`

- konfiguracja środowiskowa,
- bezpieczeństwo JWT i haszowanie haseł,
- rate limiting,
- logowanie systemowe.

### `backend/app/models`

- modele ORM użytkowników,
- konwersacje i uczestnicy,
- wiadomości,
- reguły autorespondera,
- powiadomienia,
- logi audytowe i logi automatyzacji.

### `backend/app/schemas`

- kontrakty wejścia/wyjścia API,
- walidacja danych,
- serializacja obiektów ORM.

### `backend/app/services`

- `auth_service` – rejestracja i logowanie,
- `message_service` – wiadomości, historia, wyszukiwanie, statusy,
- `classification_service` – kategoryzacja wiadomości,
- `spam_service` – wykrywanie wiadomości niechcianych,
- `autoresponder_service` – reguły i automatyczne odpowiedzi,
- `admin_service` – statystyki, moderacja, diagnostyka,
- `notification_service` – powiadomienia systemowe,
- `presence_service` – statusy online/offline.

### `backend/app/api/v1`

- endpointy REST dla wszystkich obszarów systemu,
- autoryzacja przez zależności FastAPI,
- automatyczna dokumentacja Swagger/OpenAPI.

### `backend/app/websocket`

- utrzymywanie aktywnych połączeń,
- broadcasty wiadomości,
- typing indicator,
- statusy `read`,
- zdarzenia presence.

### `backend/app/workers`

- integracja z Celery,
- asynchroniczne przetwarzanie automatyzacji wiadomości,
- możliwość dalszej rozbudowy o zadania cykliczne.

## 3. Model danych

Najważniejsze tabele:

- `users`
  przechowuje dane konta, role, status, ustawienia prywatności i powiadomień.

- `conversations`
  zawiera metadane rozmów prywatnych i grupowych.

- `conversation_participants`
  wiąże użytkowników z konwersacjami i przechowuje stan odczytu.

- `messages`
  zapisuje treść, status, kategorię, wynik spamu, metadane analizy i flagę automatyzacji.

- `notifications`
  powiadomienia o nowych wiadomościach i akcjach systemu.

- `autoresponder_rules`
  reguły automatycznych odpowiedzi użytkowników.

- `audit_logs`
  logi zdarzeń biznesowych i administracyjnych.

- `automation_logs`
  historia automatycznie wykonanych działań.

## 4. Przepływ wiadomości

1. użytkownik wysyła wiadomość przez REST API,
2. `message_service` sprawdza dostęp do konwersacji,
3. `classification_service` nadaje kategorię,
4. `spam_service` oblicza wynik spamu,
5. wiadomość jest zapisywana w bazie,
6. generowane są powiadomienia dla odbiorców,
7. WebSocket broadcast dostarcza wiadomość online,
8. autoresponder uruchamia się inline i opcjonalnie przez Celery.

## 5. Mechanizm klasyfikacji wiadomości

Pierwsza wersja opiera się na regułach i słowach kluczowych:

- `urgent` – słowa typu `pilne`, `asap`, `awaria`,
- `announcement` – `ogłoszenie`, `komunikat`, `informacja`,
- `offer` – `oferta`, `promocja`, `rabat`,
- `question` – znak `?` lub forma pytająca,
- `private` – kategoria domyślna,
- `spam` – nadpisuje kategorię, jeśli spam detector przekroczy próg.

Ważne: klasyfikator został celowo odizolowany w osobnym serwisie, aby można było go łatwo zastąpić:

- klasyfikatorem `scikit-learn`,
- modelem `transformers`,
- usługą LLM lub modelem hybrydowym.

## 6. Mechanizm wykrywania spamu

Zastosowana logika wykorzystuje heurystyki:

- liczba linków,
- podejrzane słowa kluczowe,
- nadmiar wielkich liter,
- powtarzające się znaki,
- duża liczba wykrzykników.

Wynik to `spam_score` z przedziału `0.0-1.0`. Po przekroczeniu progu wiadomość:

- zostaje oznaczona jako spam,
- otrzymuje kategorię `spam`,
- może być przeglądana w panelu administratora.

## 7. Mechanizm automatycznej odpowiedzi

Obsługiwane typy reguł:

- `question` – odpowiedź na wiadomości sklasyfikowane jako pytania,
- `keyword` – odpowiedź na podstawie słów kluczowych,
- `off_hours` – odpowiedź poza wybranymi godzinami aktywności.

Zapis historii odpowiedzi realizowany jest w `automation_logs`, a same odpowiedzi trafiają do tabeli `messages` z flagą `is_automated=True`.

## 8. Bezpieczeństwo

W projekcie uwzględniono:

- haszowanie haseł `bcrypt`,
- ochronę endpointów JWT,
- walidację wejścia przez Pydantic,
- podstawowy rate limiting dla logowania, rejestracji i wysyłania wiadomości,
- rozdzielenie ról `user` / `admin`,
- obsługę kont zablokowanych,
- logi audytowe dla działań wrażliwych.

## 9. Obsługa błędów i logowanie

- logowanie aplikacyjne jest skonfigurowane centralnie,
- zdarzenia biznesowe są zapisywane do `audit_logs`,
- automatyzacje zapisują własną historię,
- błędy walidacji są zwracane przez FastAPI,
- logika biznesowa używa wyjątków HTTP tam, gdzie ma to sens.

## 10. Rozbudowa systemu

Projekt przygotowano tak, aby łatwo dodać:

- załączniki i multimedia,
- szyfrowanie end-to-end na poziomie treści,
- harmonogramy automatyzacji,
- ranking spamu oparty o model ML,
- moderację treści w grupach,
- osobny frontend SPA w React.

