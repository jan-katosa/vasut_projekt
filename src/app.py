from flask import Flask, render_template, request, g, redirect, url_for, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

import datetime

import getpass
import oracledb

def get_db():
    if 'db' not in g:
        un = input("Enter database username: ").strip()
        pw = getpass.getpass("Enter database password for " + un + ": ")
        g.db = oracledb.connect(
            user=un,
            password=pw,
            host="localhost",
            port=1521,
            sid="orania2"
        )
        g.cursor = g.db.cursor()
        print("Successfully connected to Oracle Database")

        # Only on first connection
        #execute_sql("tabla_letrehozo.sql", g.cursor)
        #g.db.commit()
    
    return g.db, g.cursor

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        print("Connection to database is closed")

app = Flask(__name__, template_folder="views")
app.teardown_appcontext(close_db)

app.secret_key = "nagyontitkoskod"  # titkos kulcs a session-höz

app.config["SESSION_TYPE"] = "filesystem"
Session(app)


vonat_adatok = [
    {"id":0, "elsoosztaly":10, "masodosztaly":60},
    {"id":1, "elsoosztaly":20, "masodosztaly":50},
    {"id":2, "elsoosztaly":15, "masodosztaly":100},
    {"id":3, "elsoosztaly":25, "masodosztaly":200},
]

allomas_adatok = [
    {"id":0, "nev":"állomás 1", "varos":"Szeged"},
    {"id":1, "nev":"állomás 2", "varos":"Szeged"},
    {"id":2, "nev":"állomás 3", "varos":"Szeged 2"},
    {"id":3, "nev":"állomás 4", "varos":"Szeged 3"},
]

jegy_adatok = [
    {"id":0, "nev":"jegy 1", "ar":2000, "felhasznalhato":3},
    {"id":1, "nev":"jegy 2", "ar":1000, "felhasznalhato":1},
    {"id":2, "nev":"jegy 3", "ar":4000, "felhasznalhato":7},
    {"id":3, "nev":"jegy 4", "ar":5500, "felhasznalhato":6},
]

csatlakozas_adatok = [
    {"id":0, "idotartam":30, "hossz":12.0, "elso_id":0, "masodik_id":1, "jarat_id":0},
    {"id":1, "idotartam":20, "hossz":14.0, "elso_id":1, "masodik_id":2, "jarat_id":0},
    {"id":2, "idotartam":15, "hossz":10.0, "elso_id":0, "masodik_id":2, "jarat_id":1},
    {"id":3, "idotartam":20, "hossz":15.0, "elso_id":0, "masodik_id":1, "jarat_id":2},
    {"id":4, "idotartam":40, "hossz":25.0, "elso_id":1, "masodik_id":3, "jarat_id":2},
    {"id":5, "idotartam":30, "hossz":30.0, "elso_id":2, "masodik_id":3, "jarat_id":3},
]

jarat_adatok = [
    {"id":0, "indulas":1000, "vonat":0, "utvonal":0},
    {"id":1, "indulas":2000, "vonat":0, "utvonal":2},
    {"id":2, "indulas":3000, "vonat":1, "utvonal":3},
    {"id":3, "indulas":4000, "vonat":2, "utvonal":5},
]

felhasznalok = {}


@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("bejelentkezes"))
    return render_template("index.html", user=session["user"])

@app.route("/bejelentkezes", methods=["GET", "POST"])
def bejelentkezes():
    global felhasznalok

    connection, cursor = get_db()

    felhasznalok = []
    for row in cursor.execute("select * from Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = felhasznalok.get(username)
        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return redirect(url_for("index"))
        else:
            return "Hibás felhasználónév vagy jelszó!", 401

    return render_template("bejelentkezes.html")

@app.route("/regisztracio", methods=["GET", "POST"])
def regisztracio():
    global felhasznalok

    connection, cursor = get_db()

    felhasznalok = []
    for row in cursor.execute("select * from Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in felhasznalok:
            return "Ez a felhasználónév már foglalt!", 400

        hashed_pw = generate_password_hash(password)
        felhasznalok[username] = {"password": hashed_pw, "szul_ido":datetime.datetime(2020, 5, 17), "alkalmazott":0, "administrator":0}
        session["user"] = username

        cursor.execute("insert into Felhasznalo values (:un, :pw, :szi, :alk, :admin)", [hashed_pw, datetime.datetime(2020, 5, 17), 0, 0])
        connection.commit()

        return redirect(url_for("index"))

    return render_template("regisztracio.html")


@app.route("/kijelentkezes")
def kijelentkezes():
    session.pop("user", None)
    return redirect(url_for("bejelentkezes"))



@app.route("/vonatok", methods=['POST', 'GET'])
def vonatok():
    global vonat_adatok
    global felhasznalok

    if "user" not in session or felhasznalok["user"]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    connection, cursor = get_db()

    vonat_adatok = []

    for row in cursor.execute("select * from Vonat"):
        vonat_adatok.append({"id":row[0], "elsoosztaly":row[1], "masodosztaly":row[2]})

    if request.method == 'POST':
        data = request.get_json()
        #app.logger.info(data)
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(vonat_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if d["elsoosztaly"] != adat["elsoosztaly"] or d["masodosztaly"] != adat["masodosztaly"]:
                        vonat_adatok[i]["elsoosztaly"] = d["elsoosztaly"]
                        vonat_adatok[i]["masodosztaly"] = d["masodosztaly"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)

        newData = []
        for d in data:
            found = False
            for adat in vonat_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                newData.append({"elsoosztaly":d["elsoosztaly"], "masodosztaly":d["masodosztaly"]})
        
        for ind in updatedInds:
            cursor.execute("update Vonat set elso_osztalyu_helyek = :eo, masod_osztalyu_helyek = :mo where vonat_azonosito = :va", [vonat_adatok[ind]["elsoosztaly"], vonat_adatok[ind]["masodosztaly"], vonat_adatok[ind]["id"]])

        for ind in deletedInds:
            cursor.execute("delete from Vonat where vonat_azonosito = :va", [vonat_adatok[ind]["id"]])
        
        if len(newData) > 0:
            cursor.executemany("insert into Vonat (elso_osztalyu_helyek, masod_osztalyu_helyek) values (:elsoosztaly, :masodosztaly)", newData)

        connection.commit()

        vonat_adatok = []
        for row in cursor.execute("select * from Vonat"):
            vonat_adatok.append({"id":row[0], "elsoosztaly":row[1], "masodosztaly":row[2]})

        return redirect(url_for("vonatok"))

    return render_template("vonatok.html", vonat_adatok=vonat_adatok)


@app.route("/jaratok")
def jaratok():
    global csatlakozas_adatok
    global jarat_adatok
    global felhasznalok

    if "user" not in session or felhasznalok["user"]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    connection, cursor = get_db()

    csatlakozas_adatok = []
    for row in cursor.execute("select * from Csatlakozas"):
        allomas_adatok.append({"id":row[0], "idotartam":row[1], "hossz":row[2], "elso_id":row[3], "masodik_id":row[4], "jarat_id":row[5]})

    jarat_adatok
    for row in cursor.execute("select * from Jarat"):
        allomas_adatok.append({"id":row[0], "indulas":row[1], "vonat":row[3], "utvonal":row[2]})

    max_csatlakozas_id = 0
    for csatlakozas in csatlakozas_adatok:
        if csatlakozas["id"] > max_csatlakozas_id:
            max_csatlakozas_id = csatlakozas["id"]

    return render_template("jaratok.html", jarat_adatok=jarat_adatok, vonat_adatok=vonat_adatok, csatlakozas_adatok=csatlakozas_adatok, max_csatlakozas_id=max_csatlakozas_id)


@app.route("/allomasok", methods=['POST', 'GET'])
def allomasok():
    global allomas_adatok
    global felhasznalok

    if "user" not in session or felhasznalok["user"]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    connection, cursor = get_db()

    allomas_adatok = []

    for row in cursor.execute("select * from Allomas"):
        allomas_adatok.append({"id":row[0], "nev":row[1], "varos":row[2]})

    if request.method == 'POST':
        data = request.get_json()
        #app.logger.info(data)
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(allomas_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if d["nev"] != adat["nev"] or d["varos"] != adat["varos"]:
                        allomas_adatok[i]["nev"] = d["nev"]
                        allomas_adatok[i]["varos"] = d["varos"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)
        
        newData = []
        for d in data:
            found = False
            for adat in allomas_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                newData.append({"nev":d["nev"], "varos":d["varos"]})
        
        for ind in updatedInds:
            cursor.execute("update Allomas set nev = :an, varos = :av where a_azonosito = :aa", [allomas_adatok[ind]["nev"], allomas_adatok[ind]["varos"], allomas_adatok[ind]["id"]])

        for ind in deletedInds:
            cursor.execute("delete from Allomas where a_azonosito = :aa", [allomas_adatok[ind]["id"]])
        
        if len(newData) > 0:
            cursor.executemany("insert into Allomas (nev, varos) values (:nev, :varos)", newData)

        connection.commit()

        allomas_adatok = []
        for row in cursor.execute("select * from Allomas"):
            allomas_adatok.append({"id":row[0], "nev":row[1], "varos":row[2]})

        return redirect(url_for("allomasok"))

    return render_template("allomasok.html", allomas_adatok=allomas_adatok)


@app.route("/jegyek", methods=['POST', 'GET'])
def jegyek():
    global jegy_adatok
    global felhasznalok

    if "user" not in session or felhasznalok["user"]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    connection, cursor = get_db()

    jegy_adatok = []

    for row in cursor.execute("select * from Jegy"):
        jegy_adatok.append({"id":row[0], "nev":row[1], "ar":row[2], "felhasznalhato":row[3]})

    if request.method == 'POST':
        data = request.get_json()
        #app.logger.info(data)
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(jegy_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if d["nev"] != adat["nev"] or d["ar"] != adat["ar"] or d["felhasznalhato"] != adat["felhasznalhato"]:
                        jegy_adatok[i]["nev"] = d["nev"]
                        jegy_adatok[i]["ar"] = d["ar"]
                        jegy_adatok[i]["felhasznalhato"] = d["felhasznalhato"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)
        
        newData = []
        for d in data:
            found = False
            for adat in jegy_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                newData.append({"nev":d["nev"], "ar":d["ar"], "felhasznalhato":d["felhasznalhato"]})

        for ind in updatedInds:
            cursor.execute("update Jegy set nev = :jn, ar = :ja, felhasznalhato = :jf where jegy_azonosito = :jazon", [jegy_adatok[ind]["nev"], jegy_adatok[ind]["ar"], jegy_adatok[ind]["felhasznalhato"], jegy_adatok[ind]["id"]])

        for ind in deletedInds:
            cursor.execute("delete from Jegy where jegy_azonosito = :ja", [jegy_adatok[ind]["id"]])
        
        if len(newData) > 0:
            cursor.executemany("insert into Jegy (nev, ar, felhasznalhato) values (:nev, :ar, felhasznalhato)", newData)

        connection.commit()

        jegy_adatok = []
        for row in cursor.execute("select * from Jegy"):
            jegy_adatok.append({"id":row[0], "nev":row[1], "ar":row[2], "felhasznalhato":row[3]})

        return redirect(url_for("jegyek"))

    return render_template("jegyek.html", jegy_adatok=jegy_adatok)


