Hornchen - Readme

Wstêp
Hornchen to gra w zamyœle roguelike. Jest jeszcze niedokoñczona (w szczególnoœci faktyczna rozgrywka),
ale jej g³ówne elementy s¹ sprawne - generowanie losowej mapy pomieszczeñ, wrogowie, ekwipunek, umiejêtnoœci gracza.
Napisana jest ca³kowicie obiektowo w Pythonie z wykorzystaniem biblioteki pygame.
Silnik gry oparty jest na stanach (states), np. menu g³ówne, ekwipunek gracza, widok poziomu (pomieszczenia).
Notatka: do uruchomienia gry potrzebna jest biblioteka pygame. Do jej zainstalowania mo¿na wykorzystaæ
         wbudowan¹ czêœæ Pythona - pip - za pomoc¹ komendy cmd.exe "pip install pygame". Bibliotekê mo¿na
         te¿ ewentualnie pobraæ z https://www.lfd.uci.edu/~gohlke/pythonlibs/#pygame 

Grê w³¹czamy za pomoc¹ app.py (z widokiem konsoli Pythona - log) lub $launcher.pyw (bez konsoli Pythona)

Menu g³ówne
"Continue" spróbuje wczytaæ zapis gry. Je¿eli nie mo¿e go znaleŸæ, nic siê nie dzieje.
"Start" wygeneruje now¹ mapê i zacznie now¹ grê.
"Settings" to prosty prototyp ustawieñ 
- w trybie z w³¹czon¹ myszk¹ "Use Mouse" efekty przedmiotów s¹ kierowane w kierunku kursora

Widok gry
Pojawia siê po u¿yciu "Continue" lub "Start".
W górnej czeœci ekranu znajduje siê "Topbar", na którym widaæ obecny stan gracza (¿ycie/mana),
u¿ywany przedmiot (pod przyciskiem "Z") i czar (pod "X"). W prawym górnym rogu jest minimapa.
Na pocz¹tku gry gracz zawsze znajdzie siê w pomieszczeniu startowym, w którym znajduje siê
jedna pusta skrzynia, przeciwnik poruszaj¹cy siê w losowych kierunkach oraz przeciwnik
pod¹¿aj¹cy za graczem.

Klawisze
- Gra:
lewo, prawo, góra, dó³ - W/S/A/D, strza³ki
u¿yj przedmiotu - Z, LPM (lewy przycisk myszy)
u¿yj czaru (tzn. umiejêtnoœci) - X, PPM
szybsze poruszanie (sprint) - V
aktywacja czêœci mapy (drzwi, skrzynia) - Spacja

- W menu:
lewo, prawo, góra, dó³ - W/S/A/D, strza³ki
dzia³anie w menu: Z/LPM, X/PPM, Spacja
w widoku minimapy: powrót widoku do pozycji gracza - P
wyjœcie - Escape, Enter

- W³¹czanie menu:
pauza - Escape
ekwipunek - I
widok mapy - M
widok wszystkich czarów (umiejêtnoœci) - T

- Debugging:
konsola (interaktywny REPL Pythona) - F2
widok debug - F3
w³¹cz/wy³¹cz u¿ycie myszki - F6
w³¹cz/wy³¹cz nagrywanie - F9/F10, (uwaga: wymaga biblioteki 3rd-party: numpy)
w³¹cz/wy³¹cz tryb pe³noekranowy - F11
screenshot - F12

- W konsoli:
Mo¿na u¿ywaæ prawie wszystkich znaków na zwyk³ej klawiaturze.
wpisanie linii - Enter
usuñ jeden znak - Backspace
usuñ liniê - Delete
przewijaj widok w górê - Page Up
przewijaj widok w dó³ - Page Down
(historia to poprzednie wpisane komendy)
poprzedni z historii - strza³ka w dó³
nastêpny z historii - strza³ka w górê
pozycja wskaŸnika (gdzie s¹ wpisywane litery) - strza³ka w lewo/prawo


Rozgrywka
- Dzia³anie
W widoku gry mo¿emy u¿ywaæ przedmiotów, by pokonaæ wrogów. Nale¿y siê te¿ poruszaæ by unikaæ ich ataków.
Inaczej tracimy ¿ycie. Aby pokonaæ wrogów mo¿emy u¿ywaæ przedmiotów (tyle, ile chcemy) [Z/LPM] lub czarów [X/PPM],
które zu¿ywaj¹ manê.

- Pomieszczenia
W dowolnym momencie mo¿emy przejœæ do innego pomieszczenia udaj¹c siê przez jedne z drzwi
(obok niego nale¿y nacisn¹æ spacjê lub wyjœæ poza mapê). Znajdziemy siê wtedy w innym pomieszczeniu.
Wszystko, co zrobiliœmy w poprzednim pomieszczeniu jest zapisane i zapamiêtane. Po tym, jak wrócimy
do pomieszczenia przeprowadzana jest "symulacja" tego, co siê dzia³o, gdy znajdowaliœmy siê poza nim.
(np. przeciwnicy nadal siê poruszaj¹).
Wchodz¹c do innego pomieszczenia na minimapie odkrywamy wszystkie do niego s¹siednie. Znaki zapytania
oznaczaj¹ pomieszczenie nieodkryte.

- Ekwipunek [I]
Przedmioty wybieramy kursorem myszki lub u¿ywaj¹c przycisków lewo/prawo/góra dó³. Z/LPM wybieramy nowy
przedmiot do u¿ywania pod przyciskiem u¿ywania przedmiotu. U¿ywaj¹c X/PPM mo¿emy przenosiæ przedmioty
w ekwipunku pomiêdzy dwoma miejscami, co pozwala na ich uporz¹dkowanie. Najechanie na przedmiot
pokazuje jego opis, powiêkszon¹ ikonê i statystyki.

- Czary [T]
Nale¿y najechaæ na czar i u¿ywaj¹c przycisku X odblokowaæ go. Nastêpnie Z mo¿emy go zaznaczyæ do u¿ycia.
Czary:
p³omyczki, promieñ spowalniaj¹cy wrogów, kula ognia, pu³apka

- Minimapa [M]
Mo¿emy j¹ przemieszczaæ u¿ywaj¹c kursora myszy (przytrzymuj¹c i przemieszczaj¹c go) lub przyciskami
lewo/prawo/góra/dó³.

- Pauza [Escape]
W oknie pauzy mo¿na u¿yæ opcji "Save" by zapisaæ w pe³ni stan gry do pliku "save.json" w obecnej œcie¿ce. 

- Konsola [F2]
Przydatne funkcje:
get_player().reveal_all_map_tiles() - odkrycie ca³ej mapy (nale¿y j¹ aktualizowaæ przechodz¹c do innego pomieszczenia)
spawn_enemy(type, col, row, count=1) - np. spawn_enemy(enemies.GrayGoo, 5, 5) - przywo³anie przeciwnika
infmana() - nieskoñczona mana do czarów

Jest to w pe³ni u¿yteczna konsola Pythona, wiêc wyra¿enia tj.
> x = 5
> x + 3
8
Dzia³aj¹ tak jak mo¿na siê spodziewaæ.




Jakub Bachurski © 2017 kbachurski@gmail.com