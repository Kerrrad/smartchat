# Materiały do pracy dyplomowej

## 1. Cel pracy

Celem pracy jest zaprojektowanie i implementacja webowego systemu komunikacyjnego umożliwiającego wymianę wiadomości między użytkownikami z dodatkowymi funkcjami automatyzującymi konwersacje, w szczególności:

- wstępną klasyfikacją wiadomości,
- wykrywaniem treści niechcianych,
- automatycznym generowaniem odpowiedzi,
- wsparciem moderacji i analizy zdarzeń.

## 2. Zakres pracy

Zakres zrealizowanego projektu obejmuje:

1. implementację backendu w Pythonie z użyciem FastAPI,
2. przygotowanie bazy danych i modeli SQLAlchemy,
3. autoryzację użytkowników z użyciem JWT,
4. obsługę konwersacji prywatnych i grupowych,
5. komunikację czasu rzeczywistego przez WebSocket,
6. klasyfikację wiadomości na podstawie reguł,
7. wykrywanie spamu z użyciem heurystyk,
8. moduł autorespondera,
9. panel administratora,
10. testy jednostkowe i integracyjne,
11. dokumentację techniczną oraz porównawczą.

## 3. Uzasadnienie wyboru technologii

### Python

Został wybrany ze względu na:

- czytelność,
- szybkość prototypowania,
- dostępność bibliotek backendowych i ML,
- łatwość integracji z narzędziami NLP.

### FastAPI

Wybrano ze względu na:

- wysoką wydajność,
- natywną obsługę asynchroniczności,
- automatyczną dokumentację OpenAPI,
- wygodną walidację modeli.

### SQLAlchemy + PostgreSQL

Zestaw zapewnia:

- dojrzałe ORM,
- dobrą skalowalność,
- możliwość stosowania relacyjnego modelu danych,
- łatwe migracje i raportowanie.

### WebSocket

Technologia ta pozwala realizować:

- czat w czasie rzeczywistym,
- typing indicator,
- statusy online/offline,
- dynamiczne aktualizacje interfejsu.

### Celery + Redis

Rozwiązanie zostało wybrane do obsługi zadań asynchronicznych, ponieważ:

- dobrze współpracuje z Pythonem,
- upraszcza delegowanie czasochłonnych operacji,
- umożliwia dalszy rozwój o zadania okresowe.

## 4. Scenariusze testowe do opisania w pracy

### Scenariusz 1: rejestracja i logowanie

1. użytkownik zakłada konto,
2. loguje się do systemu,
3. otrzymuje token JWT,
4. uzyskuje dostęp do chronionych endpointów.

### Scenariusz 2: wysłanie wiadomości prywatnej

1. użytkownik wyszukuje odbiorcę,
2. tworzy rozmowę prywatną,
3. wysyła wiadomość,
4. odbiorca otrzymuje ją w czasie rzeczywistym.

### Scenariusz 3: klasyfikacja wiadomości

1. nadawca wpisuje wiadomość,
2. system przypisuje kategorię,
3. wynik klasyfikacji jest zapisywany w bazie,
4. użytkownik może przeanalizować wynik w panelu testowym.

### Scenariusz 4: wykrycie spamu

1. użytkownik wysyła wiadomość zawierającą podejrzane cechy,
2. system oznacza ją jako potencjalny spam,
3. administrator widzi ją w panelu spam review.

### Scenariusz 5: autoresponder

1. użytkownik konfiguruje regułę,
2. otrzymuje wiadomość spełniającą warunek,
3. system generuje odpowiedź automatyczną,
4. wpis pojawia się w historii automatyzacji.

### Scenariusz 6: WebSocket i status odczytu

1. użytkownik otwiera rozmowę,
2. oznacza wiadomości jako przeczytane,
3. status `read` trafia do klientów przez WebSocket.

## 5. Kryteria porównania z innymi systemami

W pracy można zastosować następujące kryteria:

- obsługa komunikacji prywatnej,
- obsługa komunikacji grupowej,
- mechanizmy automatyzacji wiadomości,
- wykrywanie spamu i moderacja,
- rozszerzalność architektury,
- bezpieczeństwo i prywatność,
- możliwość wykorzystania w środowisku prywatnym i biznesowym.

## 6. Możliwe kierunki rozwoju aplikacji

- dołączenie modelu NLP opartego na `transformers`,
- klasyfikacja nadzorowana z użyciem `scikit-learn`,
- analiza sentymentu wiadomości,
- boty asystujące w konwersacjach grupowych,
- obsługa załączników, plików i obrazów,
- powiadomienia e-mail oraz web push,
- integracja z systemami zewnętrznymi,
- dashboard analityczny z metrykami aktywności,
- rozbudowana polityka moderacji,
- deployment chmurowy i CI/CD.

## 7. Propozycja tezy

„Możliwe jest zaprojektowanie modularnego komunikatora webowego w architekturze opartej o FastAPI, który dzięki zastosowaniu prostych heurystyk klasyfikacyjnych i mechanizmów automatyzacji konwersacji zapewnia funkcjonalność wystarczającą do dalszej rozbudowy o modele sztucznej inteligencji.”

