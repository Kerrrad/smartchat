# Przegląd API

## 1. Endpointy publiczne

### `GET /api/v1/health`

- healthcheck aplikacji,
- zwraca podstawowe informacje o środowisku.

### `POST /api/v1/auth/register`

- rejestracja konta,
- tworzy użytkownika z rolą `user`.

### `POST /api/v1/auth/login`

- logowanie po e-mailu lub nazwie użytkownika,
- zwraca token JWT.

## 2. Endpointy użytkownika

### `POST /api/v1/auth/logout`

- zapisuje zdarzenie wylogowania,
- faktyczne usunięcie tokena odbywa się po stronie klienta.

### `GET /api/v1/users/me`

- pobiera profil aktualnego użytkownika.

### `PATCH /api/v1/users/me`

- aktualizuje nazwę, bio, avatar, status i ustawienia.

### `GET /api/v1/users/search?q=...`

- wyszukiwanie użytkowników po nazwie lub e-mailu.

### `GET /api/v1/users/{user_id}`

- podgląd profilu wybranego użytkownika.

## 3. Konwersacje i wiadomości

### `GET /api/v1/conversations`

- lista konwersacji użytkownika.

### `POST /api/v1/conversations`

- utworzenie rozmowy prywatnej lub grupowej.

### `GET /api/v1/conversations/{conversation_id}`

- szczegóły konwersacji z historią wiadomości.

### `GET /api/v1/conversations/{conversation_id}/messages`

- historia wiadomości,
- obsługa filtrów: treść, kategoria, nadawca, status.

### `POST /api/v1/conversations/{conversation_id}/messages`

- wysyłanie wiadomości,
- klasyfikacja i spam detection wykonywane automatycznie.

### `PATCH /api/v1/conversations/messages/{message_id}`

- edycja własnej wiadomości.

### `DELETE /api/v1/conversations/messages/{message_id}`

- logiczne usunięcie wiadomości.

### `POST /api/v1/conversations/{conversation_id}/read`

- oznaczenie wiadomości w rozmowie jako przeczytanych.

### `GET /api/v1/conversations/messages/search?q=...`

- globalne wyszukiwanie wiadomości w konwersacjach użytkownika.

### `POST /api/v1/conversations/messages/analyze`

- analiza wiadomości bez jej wysyłania,
- endpoint używany przez panel testowy.

## 4. Powiadomienia

### `GET /api/v1/notifications`

- lista powiadomień użytkownika.

### `POST /api/v1/notifications/{notification_id}/read`

- oznaczenie powiadomienia jako przeczytanego.

## 5. Automatyzacje

### `GET /api/v1/automation/rules`

- lista reguł autorespondera.

### `POST /api/v1/automation/rules`

- dodanie nowej reguły.

### `PATCH /api/v1/automation/rules/{rule_id}`

- aktualizacja reguły.

### `DELETE /api/v1/automation/rules/{rule_id}`

- usunięcie reguły.

### `GET /api/v1/automation/history`

- historia wykonanych automatycznych akcji.

## 6. Panel administratora

### `GET /api/v1/admin/stats`

- statystyki systemu.

### `GET /api/v1/admin/users`

- lista wszystkich użytkowników.

### `POST /api/v1/admin/users/{user_id}/block`

- blokowanie i odblokowywanie użytkownika.

### `GET /api/v1/admin/spam`

- wiadomości oznaczone jako spam.

### `GET /api/v1/admin/audit-logs`

- logi systemowe i zdarzenia audytowe.

### `GET /api/v1/admin/automation-logs`

- logi automatycznych działań.

### `GET /api/v1/admin/diagnostics`

- podstawowe testy stanu systemu.

## 7. WebSocket

### `GET /ws?token=<jwt>`

Kanał realtime dla:

- nowych wiadomości,
- statusów `read`,
- typing indicator,
- presence online/offline,
- powiadomień systemowych.

### Obsługiwane eventy wejściowe

- `typing`
- `mark_read`

### Obsługiwane eventy wyjściowe

- `message.new`
- `message.updated`
- `message.deleted`
- `message.status`
- `conversation.typing`
- `presence.changed`

