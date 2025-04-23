# Vasútmenetrend projekt

## Leírás

A feladat egy olyan alkalmazást foglal magába, amelyen keresztül egy vasúttársaság menetrendjét lehet megtekinteni, illetve jegyet foglalni járataira. Továbbá, a társaság adminisztrátorai az alkalmazásban tudják kezelni az alkalmazottaik (kalauzok, jegypénztárosok) beosztását, és többfajta statisztikát és adatot tudnak lekérdezni (például a jegyárusításról). Regisztrálás és bejelentkezés után lehet jegyet online vásárolni az alkalmazáson keresztül; és a bejelentkezett felhasználók többfajta kedvezményben részesülhetnek. Ezenkívül a felhasználók képesek járatot keresni ár, illetve idő alapján és a csatlakozások figyelembevételével keresni.


## Telepítés

1. Töltsd le a repót
2. Telepítsd a *requirements.txt*-ből a module-okat (pip install -r requirements.txt)
3. Futtasd le a *tabla_letrehozo.sql* szkriptet
4. Nyiss SSH csatlakozást az orania2 szerverre
5. Nyisd meg parancssorban a src mappát
6. Futtasd a *flask run* parancsot
7. Add meg az Oracle adatbázis adataidat
8. Előre generált adminisztrátor fiók a teszteléshez
    - felhasználónév: asd
    - jelszó: asd


## Megjegyzések

- Adatok hozzáadásánál/szerkesztésénél először a **"+"** jeles gombra kell nyomni, aztán a **"mentés"** gombra.
- Lehetséges, hogy a html oldalaknál hibákat jelez ha egy IDE-ben van megtekintve, de működik az oldal.
- Jelenleg az app lekéri az Oracle adatbázis adatokat amikor az indexről másik oldalra lépünk. Ha az **"app.py"** fájlban a **"get_db"** függvényben (fájl teteje fele) az **"un"** változót a felhasználónévre, a **"pw"** változót a jelszóra átírjuk amíg teszteljük az appot, akkor csak az oldal indításakor kéri le.