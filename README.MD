# Vasútmenetrend projekt

## Leírás

A feladat egy olyan alkalmazást foglal magába, amelyen keresztül egy vasúttársaság menetrendjét lehet megtekinteni, illetve jegyet foglalni járataira. Továbbá, a társaság adminisztrátorai az alkalmazásban tudják kezelni az alkalmazottaik (kalauzok, jegypénztárosok) beosztását, és többfajta statisztikát és adatot tudnak lekérdezni (például a jegyárusításról). Regisztrálás és bejelentkezés után lehet jegyet online vásárolni az alkalmazáson keresztül; és a bejelentkezett felhasználók többfajta kedvezményben részesülhetnek. Ezenkívül a felhasználók képesek járatot keresni ár, illetve idő alapján és a csatlakozások figyelembevételével keresni.


## Telepítés

1. Töltsd le a repót
2. Telepítsd a *requirements.txt*-ből a module-okat (pip install -r requirements.txt)
3. Futtasd le a *tabla_letrehozo.sql* szkriptet az SQL Developer alkalmazásban
4. Nyiss SSH csatlakozást az orania2 szerverre
5. Nyisd meg a parancssorban/terminálban a src mappát
6. Futtasd a *flask run* parancsot
7. Add meg az Oracle adatbázis adataidat
8. Előre generált adminisztrátor fiók a teszteléshez
    - felhasználónév: asd
    - jelszó: asd


## Megjegyzések

- Adatok hozzáadásánál/szerkesztésénél először a **"+"** jeles gombra kell nyomni, aztán a **"mentés"** gombra.
- Lehetséges, hogy a html oldalaknál hibákat jelez ha egy IDE-ben van megtekintve, de működik az oldal.