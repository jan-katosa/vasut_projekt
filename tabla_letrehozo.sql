DROP TABLE Felhasznalo;
DROP TABLE Kedvezmeny;
DROP TABLE Jegy;
DROP TABLE Jarat;
DROP TABLE Vonat;
DROP TABLE Csatlakozas;
DROP TABLE Allomas;
DROP TABLE Vasarlas;
DROP TABLE Alkalmazott;
DROP TABLE Munkabeosztas;
DROP TABLE Szabadsag;


-- Felhasználó tábla
CREATE TABLE Felhasznalo (
    felhasznalonev VARCHAR2(50),
    jelszo VARCHAR2(100) NOT NULL,
    szuletesi_ido DATE NOT NULL,
    alkalmazott NUMBER(1) CHECK (alkalmazott IN (0,1)),
    administrator NUMBER(1) CHECK (administrator IN (0,1))
);

-- Kedvezmény tábla
CREATE TABLE Kedvezmeny (
    k_azonosito NUMBER,
    nev VARCHAR2(100) NOT NULL,
    kedvezmeny_szazalek NUMBER(3) CHECK (kedvezmeny_szazalek BETWEEN 0 AND 100)
);

-- Jegy tábla
CREATE TABLE Jegy (
    jegy_azonosito NUMBER,
    nev VARCHAR2(100) NOT NULL,
    ar NUMBER NOT NULL,
    felhasznalhato NUMBER(1) CHECK (felhasznalhato IN (0,1))
);

-- Járat tábla
CREATE TABLE Jarat (
    jarat_azonosito NUMBER,
    indulas DATE NOT NULL,
    cs_azonosito NUMBER,
    vonat_azonosito NUMBER
);

-- Vonat tábla
CREATE TABLE Vonat (
    vonat_azonosito NUMBER,
    elso_osztalyu_helyek NUMBER NOT NULL,
    masod_osztalyu_helyek NUMBER NOT NULL
);

-- Csatlakozás tábla
CREATE TABLE Csatlakozas (
    cs_azonosito NUMBER,
    idotartam NUMBER NOT NULL,
    hossz NUMBER NOT NULL,
    elso_a_azonosito NUMBER,
    masodik_a_azonosito NUMBER,
    jarat_azonosito NUMBER
);

-- Állomás tábla
CREATE TABLE Allomas (
    a_azonosito NUMBER,
    nev VARCHAR2(100) NOT NULL,
    varos VARCHAR2(100) NOT NULL
);

-- Vásárlás tábla
CREATE TABLE Vasarlas (
    vasarlas_azonosito NUMBER,
    idopont DATE NOT NULL,
    felhasznalonev VARCHAR2(50),
    k_azonosito NUMBER,
    jegy_azonosito NUMBER,
    jarat_azonosito NUMBER
);

-- Alkalmazott tábla
CREATE TABLE Alkalmazott (
    a_azonosito NUMBER,
    nev VARCHAR2(100) NOT NULL,
    beosztas VARCHAR2(50) NOT NULL,
    oraber NUMBER NOT NULL
);

-- Szabadság tábla
CREATE TABLE Szabadsag (
    sz_azonosito NUMBER,
    mettol DATE NOT NULL,
    meddig DATE NOT NULL,
    a_azonosito NUMBER
);

-- Munkabeosztás tábla
CREATE TABLE Munkabeosztas (
    m_azonosito NUMBER,
    milyen_nap VARCHAR2(20) NOT NULL,
    kezdet DATE NOT NULL,
    veg DATE NOT NULL,
    a_azonosito NUMBER
);

-- Elsődleges és külső kulcsok hozzáadása
ALTER TABLE Felhasznalo ADD CONSTRAINT pk_felhasznalo PRIMARY KEY (felhasznalonev);
ALTER TABLE Kedvezmeny ADD CONSTRAINT pk_kedvezmeny PRIMARY KEY (k_azonosito);
ALTER TABLE Jegy ADD CONSTRAINT pk_jegy PRIMARY KEY (jegy_azonosito);
ALTER TABLE Jarat ADD CONSTRAINT pk_jarat PRIMARY KEY (jarat_azonosito);
ALTER TABLE Vonat ADD CONSTRAINT pk_vonat PRIMARY KEY (vonat_azonosito);
ALTER TABLE Csatlakozas ADD CONSTRAINT pk_csatlakozas PRIMARY KEY (cs_azonosito);
ALTER TABLE Allomas ADD CONSTRAINT pk_allomas PRIMARY KEY (a_azonosito);
ALTER TABLE Vasarlas ADD CONSTRAINT pk_vasarlas PRIMARY KEY (vasarlas_azonosito);
ALTER TABLE Alkalmazott ADD CONSTRAINT pk_alkalmazott PRIMARY KEY (a_azonosito);
ALTER TABLE Szabadsag ADD CONSTRAINT pk_szabadsag PRIMARY KEY (sz_azonosito);
ALTER TABLE Munkabeosztas ADD CONSTRAINT pk_munkabeosztas PRIMARY KEY (m_azonosito);

-- Külső kulcsok beállítása
ALTER TABLE Jarat ADD CONSTRAINT fk_jarat_csatlakozas FOREIGN KEY (cs_azonosito) REFERENCES Csatlakozas(cs_azonosito) ON DELETE SET NULL;
ALTER TABLE Jarat ADD CONSTRAINT fk_jarat_vonat FOREIGN KEY (vonat_azonosito) REFERENCES Vonat(vonat_azonosito) ON DELETE CASCADE;
ALTER TABLE Csatlakozas ADD CONSTRAINT fk_csatlakozas_allomas1 FOREIGN KEY (elso_a_azonosito) REFERENCES Allomas(a_azonosito) ON DELETE CASCADE;
ALTER TABLE Csatlakozas ADD CONSTRAINT fk_csatlakozas_allomas2 FOREIGN KEY (masodik_a_azonosito) REFERENCES Allomas(a_azonosito) ON DELETE CASCADE;
ALTER TABLE Vasarlas ADD CONSTRAINT fk_vasarlas_felhasznalo FOREIGN KEY (felhasznalonev) REFERENCES Felhasznalo(felhasznalonev) ON DELETE CASCADE;
ALTER TABLE Vasarlas ADD CONSTRAINT fk_vasarlas_kedvezmeny FOREIGN KEY (k_azonosito) REFERENCES Kedvezmeny(k_azonosito) ON DELETE SET NULL;
ALTER TABLE Vasarlas ADD CONSTRAINT fk_vasarlas_jegy FOREIGN KEY (jegy_azonosito) REFERENCES Jegy(jegy_azonosito) ON DELETE CASCADE;
ALTER TABLE Vasarlas ADD CONSTRAINT fk_vasarlas_jarat FOREIGN KEY (jarat_azonosito) REFERENCES Jarat(jarat_azonosito) ON DELETE CASCADE;
ALTER TABLE Szabadsag ADD CONSTRAINT fk_szabadsag_alkalmazott FOREIGN KEY (a_azonosito) REFERENCES Alkalmazott(a_azonosito) ON DELETE CASCADE;
ALTER TABLE Munkabeosztas ADD CONSTRAINT fk_munkabeosztas_alkalmazott FOREIGN KEY (a_azonosito) REFERENCES Alkalmazott(a_azonosito) ON DELETE CASCADE;

COMMIT;

INSERT INTO Felhasznalo VALUES ('Kis Béla', 'kisbela1', TO_DATE('1990-01-01', 'YYYY-MM-DD'), 1, 0);
INSERT INTO Felhasznalo VALUES ('Adminisztrátor Ármin', 'Adminvagyok', TO_DATE('1985-05-15', 'YYYY-MM-DD'), 1, 1);
INSERT INTO Felhasznalo VALUES ('Hát Izsák', 'Vicces00', TO_DATE('1995-07-20', 'YYYY-MM-DD'), 1, 0);
INSERT INTO Felhasznalo VALUES ('Vevő Evelin', 'VE12345', TO_DATE('2000-12-10', 'YYYY-MM-DD'), 0, 0);
INSERT INTO Felhasznalo VALUES ('Adminisztrátor Ádám', 'Testvér2', TO_DATE('1988-04-25', 'YYYY-MM-DD'), 1, 1);

INSERT INTO Kedvezmeny VALUES (1, 'Diák', 50);
INSERT INTO Kedvezmeny VALUES (2, 'Nyugdíjas', 50);
INSERT INTO Kedvezmeny VALUES (3, 'Családi', 70);
INSERT INTO Kedvezmeny VALUES (4, 'Hétvégi', 70);
INSERT INTO Kedvezmeny VALUES (5, 'MÁK-ONYF', 10);

INSERT INTO Jegy VALUES (1, 'Másodosztály', 1000, 1);
INSERT INTO Jegy VALUES (2, 'Elsőosztály', 2000, 1);
INSERT INTO Jegy VALUES (3, 'Diák', 500, 1);
INSERT INTO Jegy VALUES (4, 'Nyugdíjas', 500, 1);
INSERT INTO Jegy VALUES (5, 'MÁK-ONYF', 100, 1);

INSERT INTO Jarat VALUES (1, TO_DATE('2024-03-21 08:00', 'YYYY-MM-DD HH24:MI'), 1, 1);
INSERT INTO Jarat VALUES (2, TO_DATE('2024-03-21 12:00', 'YYYY-MM-DD HH24:MI'), 2, 2);
INSERT INTO Jarat VALUES (3, TO_DATE('2024-03-21 16:00', 'YYYY-MM-DD HH24:MI'), 3, 3);
INSERT INTO Jarat VALUES (4, TO_DATE('2024-03-21 20:00', 'YYYY-MM-DD HH24:MI'), 4, 4);
INSERT INTO Jarat VALUES (5, TO_DATE('2024-03-22 08:00', 'YYYY-MM-DD HH24:MI'), 5, 5);


INSERT INTO Vonat VALUES (1, 50, 100);
INSERT INTO Vonat VALUES (2, 60, 120);
INSERT INTO Vonat VALUES (3, 70, 140);
INSERT INTO Vonat VALUES (4, 80, 160);
INSERT INTO Vonat VALUES (5, 90, 180);


INSERT INTO Csatlakozas VALUES (1, 30, 10, 1, 2, 1);
INSERT INTO Csatlakozas VALUES (2, 45, 20, 3, 4, 2);
INSERT INTO Csatlakozas VALUES (3, 60, 30, 5, 1, 3);
INSERT INTO Csatlakozas VALUES (4, 75, 40, 2, 3, 4);
INSERT INTO Csatlakozas VALUES (5, 90, 50, 4, 5, 5);

INSERT INTO Allomas VALUES (1, 'Budapest-Keleti', 'Budapest');
INSERT INTO Allomas VALUES (2, 'Debrecen', 'Debrecen');
INSERT INTO Allomas VALUES (3, 'Szeged', 'Szeged');
INSERT INTO Allomas VALUES (4, 'Győr', 'Győr');
INSERT INTO Allomas VALUES (5, 'Pécs', 'Pécs');


INSERT INTO Vasarlas VALUES (1, TO_DATE('2024-03-20', 'YYYY-MM-DD'), 'user1', 1, 1, 1);



INSERT INTO Alkalmazott VALUES (1, 'Kovács János', 'Jegyellenőr', 2000);
INSERT INTO Alkalmazott VALUES (2, 'Nagy Péter', 'Mozdonyvezető', 3000);
INSERT INTO Alkalmazott VALUES (3, 'Szabó Anna', 'Pénztáros', 1800);
INSERT INTO Alkalmazott VALUES (4, 'Tóth Béla', 'Karbantartó', 2200);
INSERT INTO Alkalmazott VALUES (5, 'Varga Erika', 'Diszpécser', 2500);


INSERT INTO Szabadsag VALUES (1, TO_DATE('2024-04-01', 'YYYY-MM-DD'), TO_DATE('2024-04-10', 'YYYY-MM-DD'), 1);
INSERT INTO Szabadsag VALUES (2, TO_DATE('2024-04-11', 'YYYY-MM-DD'), TO_DATE('2024-04-20', 'YYYY-MM-DD'), 2);
INSERT INTO Szabadsag VALUES (3, TO_DATE('2024-04-21', 'YYYY-MM-DD'), TO_DATE('2024-04-30', 'YYYY-MM-DD'), 3);
INSERT INTO Szabadsag VALUES (4, TO_DATE('2024-05-01', 'YYYY-MM-DD'), TO_DATE('2024-05-10', 'YYYY-MM-DD'), 4);
INSERT INTO Szabadsag VALUES (5, TO_DATE('2024-05-11', 'YYYY-MM-DD'), TO_DATE('2024-05-20', 'YYYY-MM-DD'), 5);


INSERT INTO Munkabeosztas VALUES (1, 'Hétfő', TO_DATE('08:00', 'HH24:MI'), TO_DATE('16:00', 'HH24:MI'), 1);
INSERT INTO Munkabeosztas VALUES (2, 'Kedd', TO_DATE('08:00', 'HH24:MI'), TO_DATE('16:00', 'HH24:MI'), 2);
INSERT INTO Munkabeosztas VALUES (3, 'Szerda', TO_DATE('08:00', 'HH24:MI'), TO_DATE('16:00', 'HH24:MI'), 3);
INSERT INTO Munkabeosztas VALUES (4, 'Csütörtök', TO_DATE('08:00', 'HH24:MI'), TO_DATE('16:00', 'HH24:MI'), 4);
INSERT INTO Munkabeosztas VALUES (5, 'Péntek', TO_DATE('08:00', 'HH24:MI'), TO_DATE('16:00', 'HH24:MI'), 5);



