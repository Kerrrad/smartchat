# Przeglad API

## 1. Endpointy publiczne

### `GET /api/v1/health`

- healthcheck aplikacji,
- zwraca podstawowe informacje o srodowisku.

### `POST /api/v1/auth/register`

- rejestracja konta,
- tworzy uzytkownika z rola `user`.

### `POST /api/v1/auth/login`

- logowanie po e-mailu lub nazwie uzytkownika,
- zwraca token JWT.

## 2. Endpointy uzytkownika

### `POST /api/v1/auth/logout`

- zapisuje zdarzenie wylogowania,
- faktyczne usuniecie tokena odbywa sie po stronie klienta.

### `GET /api/v1/users/me`

- pobiera profil aktualnego uzytkownika.

### `PATCH /api/v1/users/me`

- aktualizuje nazwe, bio, avatar, status i ustawienia.

### `GET /api/v1/users/search?q=...`

- wyszukiwanie uzytkownikow po nazwie lub e-mailu,
- zwraca tylko profile widoczne dla inicjowania nowych rozmow.

### `GET /api/v1/users/directory`

- katalog uzytkownikow wykorzystywany przez frontend,
- wspiera opcjonalny filtr `q`,
- pomija ukryte profile i biezacego uzytkownika.

### `GET /api/v1/users/{user_id}`

- podglad profilu wybranego uzytkownika.

## 3. Konwersacje i wiadomosci

### `GET /api/v1/conversations`

- lista konwersacji uzytkownika,
- zwraca rowniez prywatna kategorie widoku konwersacji danego uczestnika.

### `POST /api/v1/conversations`

- utworzenie rozmowy prywatnej lub grupowej,
- respektuje ustawienie ukrytego profilu przy inicjowaniu nowych rozmow.

### `PATCH /api/v1/conversations/{conversation_id}`

- zmiana nazwy czatu grupowego,
- dostepne dla wlasciciela grupy lub administratora.

### `PATCH /api/v1/conversations/{conversation_id}/category`

- zmienia prywatna kategorie widoku konwersacji bieżącego użytkownika:
  - `private`
  - `work`
  - `other`

### `POST /api/v1/conversations/{conversation_id}/participants`

- dodaje nowych uczestnikow do grupy,
- dostepne dla wlasciciela grupy lub administratora.

### `DELETE /api/v1/conversations/{conversation_id}/participants/{participant_user_id}`

- usuwa uczestnika z grupy,
- dostepne dla wlasciciela grupy lub administratora.

### `DELETE /api/v1/conversations/{conversation_id}`

- usuwa cala grupe,
- dostepne tylko dla wlasciciela grupy.

### `DELETE /api/v1/conversations/{conversation_id}/leave`

- pozwala opuscic czat grupowy,
- po wyjsciu konwersacja znika z listy uzytkownika,
- jesli wlasciciel opuszcza grupe i sa jeszcze inni uczestnicy, wlasnosc przechodzi na kolejna osobe.

### `GET /api/v1/conversations/{conversation_id}`

- szczegoly konwersacji z historia wiadomosci i uczestnikami.

### `GET /api/v1/conversations/{conversation_id}/messages`

- historia wiadomosci,
- obsluga filtrow: tresc, kategoria, nadawca, status.

### `POST /api/v1/conversations/{conversation_id}/messages`

- wysylanie wiadomosci,
- klasyfikacja i spam detection wykonywane automatycznie.

### `PATCH /api/v1/conversations/messages/{message_id}`

- edycja wlasnej wiadomosci,
- tylko dopoki wiadomosc nie zostala odczytana.

### `DELETE /api/v1/conversations/messages/{message_id}`

- logiczne usuniecie wiadomosci.

### `POST /api/v1/conversations/{conversation_id}/read`

- oznaczenie wiadomosci w rozmowie jako przeczytanych.

### `GET /api/v1/conversations/messages/search?q=...`

- globalne wyszukiwanie wiadomosci w konwersacjach uzytkownika.

### `POST /api/v1/conversations/messages/analyze`

- analiza wiadomosci bez jej wysylania,
- endpoint wykorzystywany przez panel testowy.

## 4. Powiadomienia

### `GET /api/v1/notifications`

- lista powiadomien uzytkownika,
- elementy moga zawierac:
  - `type`,
  - `message_category`,
  - `related_message_id`,
  - `conversation_id`.

### `POST /api/v1/notifications/{notification_id}/read`

- oznaczenie powiadomienia jako przeczytanego.

## 5. Automatyzacje

### `GET /api/v1/automation/rules`

- lista regul autorespondera.

### `POST /api/v1/automation/rules`

- dodanie nowej reguly.

### `PATCH /api/v1/automation/rules/{rule_id}`

- aktualizacja reguly.

### `DELETE /api/v1/automation/rules/{rule_id}`

- usuniecie reguly.

### `GET /api/v1/automation/history`

- historia wykonanych automatycznych akcji.

Wazna uwaga:

- autoresponder jest obecnie aktywny tylko dla rozmow prywatnych,
- nie generuje odpowiedzi w konwersacjach grupowych.

## 6. Panel administratora

### `GET /api/v1/admin/stats`

- statystyki systemu.

### `GET /api/v1/admin/users`

- lista wszystkich uzytkownikow.

### `POST /api/v1/admin/users/{user_id}/block`

- blokowanie i odblokowywanie uzytkownika.

### `GET /api/v1/admin/spam`

- wiadomosci oznaczone jako spam.

### `GET /api/v1/admin/audit-logs`

- logi systemowe i zdarzenia audytowe.

### `GET /api/v1/admin/automation-logs`

- logi automatycznych dzialan.

### `GET /api/v1/admin/diagnostics`

- podstawowe testy stanu systemu.

## 7. WebSocket

### `GET /ws?token=<jwt>`

Kanal realtime dla:

- nowych wiadomosci,
- statusow `read`,
- typing indicator,
- presence online i offline,
- zmian konwersacji.

### Obslugiwane eventy wejsciowe

- `typing`
- `mark_read`

### Obslugiwane eventy wyjsciowe

- `message.new`
- `message.updated`
- `message.deleted`
- `message.status`
- `conversation.typing`
- `presence.changed`
- `conversation.updated`
- `conversation.removed`

## 8. Dokumentacja interaktywna

FastAPI generuje dokumentacje automatycznie:

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
