# Materialy do pracy dyplomowej

## 1. Cel pracy

Celem pracy jest zaprojektowanie i implementacja webowego systemu komunikacyjnego umozliwiajacego wymiane wiadomosci miedzy uzytkownikami z dodatkowymi funkcjami automatyzujacymi konwersacje, w szczegolnosci:

- wstepna klasyfikacja wiadomosci,
- wykrywanie tresci niechcianych,
- automatyczne generowanie odpowiedzi,
- wsparcie moderacji i analizy zdarzen.

## 2. Zakres pracy

Zakres zrealizowanego projektu obejmuje:

1. implementacje backendu w Pythonie z uzyciem FastAPI,
2. przygotowanie bazy danych i modeli SQLAlchemy,
3. autoryzacje uzytkownikow z uzyciem JWT,
4. obsluge konwersacji prywatnych i grupowych,
5. komunikacje czasu rzeczywistego przez WebSocket,
6. klasyfikacje wiadomosci na podstawie regul,
7. wykrywanie spamu z uzyciem heurystyk,
8. modul autorespondera dla rozmow prywatnych,
9. panel administratora,
10. prywatne kategorie konwersacji uzytkownika,
11. testy jednostkowe i integracyjne,
12. dokumentacje techniczna oraz porownawcza.

## 3. Uzasadnienie wyboru technologii

### Python

Zostal wybrany ze wzgledu na:

- czytelnosc,
- szybkosc prototypowania,
- dostepnosc bibliotek backendowych i ML,
- latwosc integracji z narzedziami NLP.

### FastAPI

Wybrano ze wzgledu na:

- wysoka wydajnosc,
- natywna obsluge asynchronicznosci,
- automatyczna dokumentacje OpenAPI,
- wygodna walidacje modeli.

### SQLAlchemy + PostgreSQL

Zestaw zapewnia:

- dojrzale ORM,
- dobra skalowalnosc,
- mozliwosc stosowania relacyjnego modelu danych,
- latwe migracje i raportowanie.

### WebSocket

Technologia ta pozwala realizowac:

- czat w czasie rzeczywistym,
- typing indicator,
- statusy online i offline,
- dynamiczne aktualizacje interfejsu,
- propagacje zmian w konwersacjach bez odswiezania strony.

### Celery + Redis

Rozwiazanie zostalo wybrane do obslugi zadan asynchronicznych, poniewaz:

- dobrze wspolpracuje z Pythonem,
- upraszcza delegowanie czasochlonnych operacji,
- umozliwia dalszy rozwoj o zadania okresowe.

## 4. Scenariusze testowe do opisania w pracy

### Scenariusz 1: rejestracja i logowanie

1. uzytkownik zaklada konto,
2. loguje sie do systemu,
3. otrzymuje token JWT,
4. uzyskuje dostep do chronionych endpointow.

### Scenariusz 2: wyslanie wiadomosci prywatnej

1. uzytkownik wyszukuje odbiorce,
2. tworzy rozmowe prywatna,
3. wysyla wiadomosc,
4. odbiorca otrzymuje ja w czasie rzeczywistym,
5. po otwarciu rozmowy status zmienia sie z `sent` na `read`.

### Scenariusz 3: klasyfikacja wiadomosci

1. nadawca wpisuje wiadomosc,
2. system przypisuje kategorie,
3. wynik klasyfikacji jest zapisywany w bazie,
4. wynik moze zostac sprawdzony przez panel testowy lub bezposrednio przez API.

### Scenariusz 4: wykrycie spamu

1. uzytkownik wysyla wiadomosc zawierajaca podejrzane cechy,
2. system oznacza ja jako potencjalny spam,
3. administrator widzi ja w panelu spam review.

### Scenariusz 5: autoresponder

1. uzytkownik konfiguruje regule,
2. otrzymuje prywatna wiadomosc spelniajaca warunek,
3. system generuje odpowiedz automatyczna,
4. wpis pojawia sie w historii automatyzacji.

### Scenariusz 6: WebSocket i status odczytu

1. uzytkownik otwiera rozmowe,
2. oznacza wiadomosci jako przeczytane,
3. status `read` trafia do klientow przez WebSocket.

### Scenariusz 7: zarzadzanie grupa

1. wlasciciel tworzy czat grupowy,
2. dodaje uczestnikow,
3. uczestnik moze opuscic grupe,
4. wlasciciel moze usunac grupe,
5. zmiany propagowane sa do pozostalych klientow.

### Scenariusz 8: organizacja konwersacji

1. uzytkownik zmienia kategorie wybranej konwersacji,
2. system zapisuje kategorie tylko dla tego uzytkownika,
3. rozmowa pojawia sie w odpowiedniej sekcji interfejsu.

## 5. Kryteria porownania z innymi systemami

W pracy mozna zastosowac nastepujace kryteria:

- obsluga komunikacji prywatnej,
- obsluga komunikacji grupowej,
- mechanizmy automatyzacji wiadomosci,
- wykrywanie spamu i moderacja,
- rozszerzalnosc architektury,
- bezpieczenstwo i prywatnosc,
- mozliwosc wykorzystania w srodowisku prywatnym i biznesowym.

## 6. Mozliwe kierunki rozwoju aplikacji

- dolaczenie modelu NLP opartego na `transformers`,
- klasyfikacja nadzorowana z uzyciem `scikit-learn`,
- analiza sentymentu wiadomosci,
- boty asystujace w konwersacjach grupowych,
- obsluga zalacznikow, plikow i obrazow,
- powiadomienia e-mail oraz web push,
- integracja z systemami zewnetrznymi,
- dashboard analityczny z metrykami aktywnosci,
- rozbudowana polityka moderacji,
- deployment chmurowy i CI/CD.

## 7. Propozycja tezy

„Mozliwe jest zaprojektowanie modularnego komunikatora webowego w architekturze opartej o FastAPI, ktory dzieki zastosowaniu prostych heurystyk klasyfikacyjnych i mechanizmow automatyzacji konwersacji zapewnia funkcjonalnosc wystarczajaca do dalszej rozbudowy o modele sztucznej inteligencji.”
