from flask import Flask, render_template, request, g, redirect, url_for, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

import datetime

import getpass
import oracledb

un = input("Enter database username: ").strip()
pw = getpass.getpass("Enter database password for " + un + ": ")

def get_db():
    if 'db' not in g:
        global un
        global pw
        
        g.db = oracledb.connect(
            user=un,
            password=pw,
            host="localhost",
            port=1521,
            sid="orania2"
        )
        g.cursor = g.db.cursor()
        print("Successfully connected to Oracle Database")
    
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


vonat_adatok = []

allomas_adatok = []

jegy_adatok = []

csatlakozas_adatok = []

jarat_adatok = []

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

    felhasznalok = {}
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

    felhasznalok = {}
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

        cursor.execute("insert into Felhasznalo values (:un, :pw, :szi, :alk, :admin)", [username, hashed_pw, datetime.datetime(2020, 5, 17), 0, 0])
        connection.commit()

        felhasznalok = {}
        for row in cursor.execute("select * from Felhasznalo"):
            felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

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

    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("select * from Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

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


@app.route("/jaratok", methods=['POST', 'GET'])
def jaratok():
    global csatlakozas_adatok
    global jarat_adatok
    global felhasznalok
    global allomas_adatok
    global vonat_adatok

    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("select * from Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    vonat_adatok = []
    for row in cursor.execute("select * from Vonat"):
        vonat_adatok.append({"id":row[0], "elsoosztaly":row[1], "masodosztaly":row[2]})

    csatlakozas_adatok = []
    for row in cursor.execute("select * from Csatlakozas"):
        csatlakozas_adatok.append({"id":row[0], "idotartam":row[1], "hossz":row[2], "elso_id":row[3], "masodik_id":row[4], "jarat_id":row[5]})

    allomas_adatok = []
    for row in cursor.execute("select * from Allomas"):
        allomas_adatok.append({"id":row[0], "nev":row[1], "varos":row[2]})

    jarat_adatok = []
    for row in cursor.execute("select * from Jarat"):
        jarat_adatok.append({"id":row[0], "indulas":row[1], "vonat":row[3], "utvonal":row[2]})

    max_csatlakozas_id = 0
    for csatlakozas in csatlakozas_adatok:
        if csatlakozas["id"] > max_csatlakozas_id:
            max_csatlakozas_id = csatlakozas["id"]

    if request.method == 'POST':
        data = request.get_json()
        #app.logger.info(data)
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(jarat_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if datetime.datetime.strptime(d["indulas"], "%a, %d %b %Y %H:%M:%S %Z") != adat["indulas"] or d["vonat"] != adat["vonat"] or d["utvonal"] != adat["utvonal"]:
                        jarat_adatok[i]["indulas"] = datetime.datetime.strptime(d["indulas"], "%a, %d %b %Y %H:%M:%S %Z")
                        jarat_adatok[i]["vonat"] = d["vonat"]
                        jarat_adatok[i]["utvonal"] = d["utvonal"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)
        
        newData = []
        for d in data:
            found = False
            for adat in jarat_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                cursor.execute("insert into Csatlakozas (idotartam, hossz, elso_a_azonosito, masodik_a_azonosito, jarat_azonosito) values (:it, :hossz, :ea, :ma, :ja)", [20, 40, allomas_adatok[0]["id"], allomas_adatok[1]["id"], -1])
                connection.commit()
                uj_csatlakozas_id = -1
                for row in cursor.execute("select * from Csatlakozas where jarat_azonosito = -1"):
                    uj_csatlakozas_id = row[0]
                    break
                newData.append({"indulas":datetime.datetime.strptime(d["indulas"], "%a, %d %b %Y %H:%M:%S %Z"), "vonat":d["vonat"], "utvonal":uj_csatlakozas_id})
        
        for ind in updatedInds:
            cursor.execute("update Jarat set indulas = :indulas, cs_azonosito = :csa, vonat_azonosito = :va where jarat_azonosito = :ja", [jarat_adatok[ind]["indulas"], jarat_adatok[ind]["utvonal"], jarat_adatok[ind]["vonat"], jarat_adatok[ind]["id"]])

        for ind in deletedInds:
            cursor.execute("delete from Jarat where jarat_azonosito = :ja", [jarat_adatok[ind]["id"]])
            cursor.execute("delete from Csatlakozas where jarat_azonosito = :ja", [jarat_adatok[ind]["id"]])
        
        for d in newData:
            cursor.execute("insert into Jarat (indulas, cs_azonosito, vonat_azonosito) values (:indulas, :utvonal, :vonat)", d)
            connection.commit()
            uj_jarat_id = -1
            for row in cursor.execute("select * from Jarat where cs_azonosito = :csa", [d["utvonal"]]):
                uj_jarat_id = row[0]
                break
            cursor.execute("update Csatlakozas set jarat_azonosito = :ja where cs_azonosito = :csa", [uj_jarat_id, d["utvonal"]])

        connection.commit()

        jarat_adatok = []
        for row in cursor.execute("select * from Jarat"):
            jarat_adatok.append({"id":row[0], "indulas":row[1], "vonat":row[3], "utvonal":row[2]})

        return redirect(url_for("jaratok"))

    return render_template("jaratok.html", jarat_adatok=jarat_adatok, vonat_adatok=vonat_adatok, max_csatlakozas_id=max_csatlakozas_id)


@app.route("/utvonal/<jarat_id>", methods=['POST', 'GET'])
def utvonal(jarat_id):
    global allomas_adatok
    global csatlakozas_adatok

    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("select * from Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    jarat_csatlakozas_adatok = []
    for row in cursor.execute("select * from Csatlakozas where jarat_azonosito = :ja order by cs_azonosito", [jarat_id]):
        jarat_csatlakozas_adatok.append({"id":row[0], "idotartam":row[1], "hossz":row[2], "elso_id":row[3], "masodik_id":row[4], "jarat_id":row[5]})

    allomas_adatok = []
    for row in cursor.execute("select * from Allomas"):
        allomas_adatok.append({"id":row[0], "nev":row[1], "varos":row[2]})

    if request.method == 'POST':
        data = request.get_json()
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(jarat_csatlakozas_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if d["idotartam"] != adat["idotartam"] or d["hossz"] != adat["hossz"] or d["elso_id"] != adat["elso_id"] or d["masodik_id"] != adat["masodik_id"]:
                        jarat_csatlakozas_adatok[i]["idotartam"] = d["idotartam"]
                        jarat_csatlakozas_adatok[i]["hossz"] = d["hossz"]
                        jarat_csatlakozas_adatok[i]["elso_id"] = d["elso_id"]
                        jarat_csatlakozas_adatok[i]["masodik_id"] = d["masodik_id"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)
        
        newData = []
        for d in data:
            found = False
            for adat in jarat_csatlakozas_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                newData.append({"idotartam":d["idotartam"], "hossz":d["hossz"], "elso_id":d["elso_id"], "masodik_id":d["masodik_id"], "jarat_id":jarat_id})
        
        for ind in updatedInds:
            cursor.execute("update Csatlakozas set idotartam = :ido, hossz = :hossz, elso_a_azonosito = :ea, masodik_a_azonosito = :ma where cs_azonosito = :csa", [jarat_csatlakozas_adatok[ind]["idotartam"], jarat_csatlakozas_adatok[ind]["hossz"], jarat_csatlakozas_adatok[ind]["elso_id"], jarat_csatlakozas_adatok[ind]["masodik_id"], jarat_csatlakozas_adatok[ind]["id"]])

        for ind in deletedInds:
            cursor.execute("delete from Csatlakozas where cs_azonosito = :csa", [jarat_csatlakozas_adatok[ind]["id"]])
        
        if len(newData) > 0:
            cursor.executemany("insert into Csatlakozas (idotartam, hossz, elso_a_azonosito, masodik_a_azonosito, jarat_azonosito) values (:idotartam, :hossz, :elso_id, :masodik_id, :jarat_id)", newData)

        connection.commit()

        csatlakozas_adatok = []
        for row in cursor.execute("select * from Csatlakozas"):
            csatlakozas_adatok.append({"id":row[0], "idotartam":row[1], "hossz":row[2], "elso_id":row[3], "masodik_id":row[4], "jarat_id":row[5]})

        jarat_csatlakozas_adatok = []
        for row in cursor.execute("select * from Csatlakozas where jarat_azonosito = :ja", [jarat_id]):
            jarat_csatlakozas_adatok.append({"id":row[0], "idotartam":row[1], "hossz":row[2], "elso_id":row[3], "masodik_id":row[4], "jarat_id":row[5]})

        return redirect(url_for("utvonal", jarat_id=jarat_id))

    return render_template("utvonal.html", csatlakozas_adatok = jarat_csatlakozas_adatok, allomas_adatok = allomas_adatok, jarat_id=jarat_id)


@app.route("/allomasok", methods=['POST', 'GET'])
def allomasok():
    global allomas_adatok
    global felhasznalok

    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("select * from Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

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

    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("select * from Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

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


@app.route("/felhasznalok", methods=['POST', 'GET'])
def felhasznalok():
    global felhasznalok

    connection, cursor = get_db()
    

    # Checking if administrator is in session
    felhasznalok = {}
    for row in cursor.execute("select * from Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator":row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))
    

    # Loading in users from database
    # (biztos vagyok benne, hogy ezt lehetne a dictbol is megoldani, de nincs agyi erom ra most)
    felhasznalo_adatok = []

    for row in cursor.execute("select * from Jegy"):
        felhasznalo_adatok.append({"nev":row[0], "datum":row[2], "alkalmazott":row[3], "adminisztrator":row[4]})


#@app.route("/kedvezmenyek", methods=['POST', 'GET'])
def kedvezmenyek():
    pass


#@app.route("/alkalmazottak", methods=['POST', 'GET'])
def alkalmazottak():
    pass


#@app.route("/szabadsagok", methods=['POST', 'GET'])
def szabadsagok():
    pass


#@app.route("/munkabeosztas", methods=['POST', 'GET'])
def munkabeosztas():
    pass