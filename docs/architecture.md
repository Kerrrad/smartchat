# Architektura projektu

## 1. Przeglad

System zostal zaprojektowany w stylu warstwowym:

1. warstwa prezentacji: frontend HTML/CSS/JS,
2. warstwa API: routery FastAPI,
3. warstwa logiki biznesowej: serwisy,
4. warstwa danych: SQLAlchemy + PostgreSQL lub SQLite w trybie developerskim,
5. warstwa asynchroniczna: Celery + Redis,
6. warstwa realtime: WebSocket manager.

Taki uklad upraszcza testowanie, rozbudowe i pozniejsze dolaczenie modeli NLP/ML.

## 2. Glowne moduly

### `backend/app/core`

- konfiguracja srodowiskowa i ustawienia `.env`,
- bezpieczenstwo JWT i haszowanie hasel,
- rate limiting,
- logowanie systemowe.

### `backend/app/models`

- modele ORM uzytkownikow,
- konwersacje, uczestnicy i kategorie widoku konwersacji,
- wiadomosci,
- reguly autorespondera,
- powiadomienia,
- logi audytowe i logi automatyzacji.

### `backend/app/schemas`

- kontrakty wejscia i wyjscia API,
- walidacja danych,
- serializacja obiektow ORM.

### `backend/app/services`

- `auth_service` – rejestracja i logowanie,
- `message_service` – wiadomosci, historia, wyszukiwanie, statusy, grupy i kategorie konwersacji,
- `classification_service` – kategoryzacja wiadomosci,
- `spam_service` – wykrywanie wiadomosci niechcianych,
- `autoresponder_service` – reguly i automatyczne odpowiedzi,
- `admin_service` – statystyki, moderacja, diagnostyka,
- `notification_service` – powiadomienia systemowe i powiadomienia wiadomosci,
- `presence_service` – statusy online i offline.

### `backend/app/api/v1`

- endpointy REST dla wszystkich obszarow systemu,
- autoryzacja przez zaleznosci FastAPI,
- automatyczna dokumentacja Swagger/OpenAPI.

### `backend/app/websocket`

- utrzymywanie aktywnych polaczen,
- broadcasty wiadomosci i zmian konwersacji,
- typing indicator,
- statusy `read`,
- zdarzenia presence.

### `backend/app/workers`

- integracja z Celery,
- asynchroniczne przetwarzanie automatyzacji wiadomosci,
- mozliwosc dalszej rozbudowy o zadania cykliczne.

## 3. Model danych

Najwazniejsze tabele:

- `users`
  przechowuje dane konta, role, status, ustawienia prywatnosci i powiadomien.

- `conversations`
  zawiera metadane rozmow prywatnych i grupowych.

- `conversation_participants`
  wiaze uzytkownikow z konwersacjami i przechowuje:
  - moment dolaczenia,
  - stan odczytu,
  - wyciszenie,
  - prywatna kategorie widoku konwersacji u danego uzytkownika (`private`, `work`, `other`).

- `messages`
  zapisuje tresc, status, kategorie, wynik spamu, metadane analizy i flage automatyzacji.

- `notifications`
  powiadomienia o nowych wiadomosciach i akcjach systemu. Moga byc powiazane z wiadomoscia albo bezposrednio z konwersacja.

- `autoresponder_rules`
  reguly automatycznych odpowiedzi uzytkownikow.

- `audit_logs`
  logi zdarzen biznesowych i administracyjnych.

- `automation_logs`
  historia automatycznie wykonanych dzialan.

## 4. Przeplyw wiadomosci

1. uzytkownik wysyla wiadomosc przez REST API,
2. `message_service` sprawdza dostep do konwersacji,
3. `classification_service` nadaje kategorie podstawowa,
4. `spam_service` oblicza wynik spamu,
5. wiadomosc jest zapisywana w bazie ze statusem `sent`,
6. generowane sa powiadomienia dla odbiorcow,
7. WebSocket broadcast dostarcza wiadomosc online,
8. autoresponder uruchamia sie inline i opcjonalnie przez Celery, ale tylko dla konwersacji prywatnych.

## 5. Mechanizm klasyfikacji wiadomosci

Pierwsza wersja opiera sie na regulach i slowach kluczowych:

- `urgent` – slowa typu `pilne`, `asap`, `awaria`,
- `announcement` – `ogloszenie`, `komunikat`, `informacja`,
- `offer` – `oferta`, `promocja`, `rabat`,
- `question` – znak `?` lub forma pytajaca,
- `private` – kategoria domyslna,
- `spam` – nadpisuje kategorie, jesli spam detector przekroczy prog.

Wazne: klasyfikator zostal celowo odizolowany w osobnym serwisie, aby mozna bylo go latwo zastapic:

- klasyfikatorem `scikit-learn`,
- modelem `transformers`,
- usluga LLM lub modelem hybrydowym.

## 6. Mechanizm wykrywania spamu

Zastosowana logika wykorzystuje heurystyki:

- liczba linkow,
- podejrzane slowa kluczowe,
- nadmiar wielkich liter,
- powtarzajace sie znaki,
- duza liczba wykrzyknikow.

Wynik to `spam_score` z przedzialu `0.0-1.0`. Po przekroczeniu progu wiadomosc:

- zostaje oznaczona jako spam,
- otrzymuje kategorie `spam`,
- moze byc przegladana w panelu administratora.

## 7. Mechanizm automatycznej odpowiedzi

Obslugiwane typy regul:

- `question` – odpowiedz na wiadomosci sklasyfikowane jako pytania,
- `keyword` – odpowiedz na podstawie slow kluczowych,
- `off_hours` – odpowiedz poza wybranymi godzinami aktywnosci.

Aktualne zasady dzialania:

- autoresponder dziala tylko w konwersacjach prywatnych,
- dla jednego odbiorcy wybierana jest pierwsza pasujaca regula,
- reguly `off_hours` bez godzin sa traktowane jako stale aktywne,
- odpowiedzi sa zapisywane w `messages` z flaga `is_automated = true`,
- historia odpowiedzi trafia do `automation_logs`.

## 8. Powiadomienia

System zapisuje trzy glowne typy powiadomien:

- `message` – nowe wiadomosci,
- `system` – zdarzenia systemowe, np. dodanie do grupy,
- `automation` – informacje o wykonaniu automatyzacji.

Dodatkowo powiadomienia:

- przechowuja kategorie wiadomosci przez pole pochodne `message_category`,
- przechowuja identyfikator konwersacji,
- sa deduplikowane per konwersacja, aby dla jednego czatu zostawic tylko najnowsze nieprzeczytane powiadomienie.

## 9. Bezpieczenstwo

W projekcie uwzgledniono:

- haszowanie hasel `bcrypt`,
- ochrone endpointow JWT,
- walidacje wejscia przez Pydantic,
- podstawowy rate limiting dla logowania, rejestracji i wysylania wiadomosci,
- rozdzielenie rol `user` i `admin`,
- obsluge kont zablokowanych,
- logi audytowe dla dzialan wrazliwych,
- ustawienie prywatnosci profilu blokujace inicjowanie nowych rozmow i dodawanie do grup, jesli profil jest ukryty.

## 10. Obsluga bledow i logowanie

- logowanie aplikacyjne jest skonfigurowane centralnie,
- zdarzenia biznesowe sa zapisywane do `audit_logs`,
- automatyzacje zapisuje wlasna historie,
- bledy walidacji sa zwracane przez FastAPI,
- logika biznesowa uzywa wyjatkow HTTP tam, gdzie ma to sens.

## 11. Rozbudowa systemu

Projekt przygotowano tak, aby latwo dodac:

- zalaczniki i multimedia,
- szyfrowanie end-to-end na poziomie tresci,
- harmonogramy automatyzacji,
- ranking spamu oparty o model ML,
- moderacje tresci w grupach,
- osobny frontend SPA w React,
- bardziej zaawansowane kategorie konwersacji i reguly workflow.
