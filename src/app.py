from flask import Flask, render_template, request, g, redirect, url_for, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
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







#Innentől Janié, nem tudom hogy jók, ha az egész program beszar akkor töröld vagy commenteld ki


@app.route("/felhasznalok", methods=["POST", "GET"])
def felhasznalok_kezeles():
    global felhasznalok

    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("SELECT * FROM Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator": row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    felhasznalo_adatok = []
    for row in cursor.execute("SELECT * FROM Felhasznalo"):
        felhasznalo_adatok.append({
            "nev": row[0],
            "password": row[1],
            "szul_ido": row[2],
            "alkalmazott": row[3],
            "administrator": row[4]
        })

    if request.method == "POST":
        data = request.get_json()
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(felhasznalo_adatok):
            found = False
            for d in data:
                if d["nev"] == adat["nev"]:
                    if (d["password"] != adat["password"] or d["szul_ido"] != str(adat["szul_ido"]) or
                        d["alkalmazott"] != adat["alkalmazott"] or d["administrator"] != adat["administrator"]):
                        felhasznalo_adatok[i]["password"] = d["password"]
                        felhasznalo_adatok[i]["szul_ido"] = datetime.datetime.strptime(d["szul_ido"], "%Y-%m-%d")
                        felhasznalo_adatok[i]["alkalmazott"] = d["alkalmazott"]
                        felhasznalo_adatok[i]["administrator"] = d["administrator"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)

        newData = []
        for d in data:
            found = False
            for adat in felhasznalo_adatok:
                if d["nev"] == adat["nev"]:
                    found = True
                    break
            if not found:
                newData.append({
                    "nev": d["nev"],
                    "password": d["password"],
                    "szul_ido": datetime.datetime.strptime(d["szul_ido"], "%Y-%m-%d"),
                    "alkalmazott": d["alkalmazott"],
                    "administrator": d["administrator"]
                })

        for ind in updatedInds:
            cursor.execute("""
                UPDATE Felhasznalo 
                SET jelszo = :pw, szuletesi_ido = :szul, alkalmazott = :alk, adminisztrator = :adm 
                WHERE felhasznalonev = :nev
            """, [felhasznalo_adatok[ind]["password"], felhasznalo_adatok[ind]["szul_ido"], felhasznalo_adatok[ind]["alkalmazott"], felhasznalo_adatok[ind]["administrator"], felhasznalo_adatok[ind]["nev"]])

        for ind in deletedInds:
            cursor.execute("DELETE FROM Felhasznalo WHERE felhasznalonev = :nev", [felhasznalo_adatok[ind]["nev"]])

        if newData:
            cursor.executemany("""
                INSERT INTO Felhasznalo (felhasznalonev, jelszo, szuletesi_ido, alkalmazott, adminisztrator)
                VALUES (:nev, :password, :szul_ido, :alkalmazott, :administrator)
            """, newData)

        connection.commit()

        return redirect(url_for("felhasznalok_kezeles"))

    return render_template("felhasznalok.html", felhasznalo_adatok=felhasznalo_adatok)


@app.route("/kedvezmenyek", methods=["POST", "GET"])
def kedvezmenyek():
    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("SELECT * FROM Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator": row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    kedvezmeny_adatok = []
    for row in cursor.execute("SELECT * FROM Kedvezmeny"):
        kedvezmeny_adatok.append({"id": row[0], "nev": row[1], "mertek": row[2]})

    if request.method == "POST":
        data = request.get_json()
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(kedvezmeny_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if d["nev"] != adat["nev"] or d["mertek"] != adat["mertek"]:
                        kedvezmeny_adatok[i]["nev"] = d["nev"]
                        kedvezmeny_adatok[i]["mertek"] = d["mertek"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)

        newData = []
        for d in data:
            found = False
            for adat in kedvezmeny_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                newData.append({"nev": d["nev"], "mertek": d["mertek"]})

        for ind in updatedInds:
            cursor.execute("""
                UPDATE Kedvezmeny SET nev = :nev, mertek = :mertek WHERE kedvezmeny_azonosito = :id
            """, [kedvezmeny_adatok[ind]["nev"], kedvezmeny_adatok[ind]["mertek"], kedvezmeny_adatok[ind]["id"]])

        for ind in deletedInds:
            cursor.execute("DELETE FROM Kedvezmeny WHERE kedvezmeny_azonosito = :id", [kedvezmeny_adatok[ind]["id"]])

        if newData:
            cursor.executemany("""
                INSERT INTO Kedvezmeny (nev, mertek) VALUES (:nev, :mertek)
            """, newData)

        connection.commit()

        return redirect(url_for("kedvezmenyek"))

    return render_template("kedvezmenyek.html", kedvezmeny_adatok=kedvezmeny_adatok)


@app.route("/alkalmazottak", methods=["POST", "GET"])
def alkalmazottak():
    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("SELECT * FROM Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator": row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    alkalmazott_adatok = []
    for row in cursor.execute("SELECT * FROM Alkalmazott"):
        alkalmazott_adatok.append({"id": row[0], "nev": row[1]})

    if request.method == "POST":
        data = request.get_json()
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(alkalmazott_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if d["nev"] != adat["nev"]:
                        alkalmazott_adatok[i]["nev"] = d["nev"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)

        newData = []
        for d in data:
            found = False
            for adat in alkalmazott_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                newData.append({"nev": d["nev"]})

        for ind in updatedInds:
            cursor.execute("UPDATE Alkalmazott SET nev = :nev WHERE alkalmazott_azonosito = :id", [alkalmazott_adatok[ind]["nev"], alkalmazott_adatok[ind]["id"]])

        for ind in deletedInds:
            cursor.execute("DELETE FROM Alkalmazott WHERE alkalmazott_azonosito = :id", [alkalmazott_adatok[ind]["id"]])

        if newData:
            cursor.executemany("INSERT INTO Alkalmazott (nev) VALUES (:nev)", newData)

        connection.commit()

        return redirect(url_for("alkalmazottak"))

    return render_template("alkalmazottak.html", alkalmazott_adatok=alkalmazott_adatok)


import oracledb  # cx_Oracle helyett

@app.route("/szabadsagok", methods=["POST", "GET"])
def szabadsagok():
    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("SELECT * FROM Felhasznalo"):
        felhasznalok[row[0]] = {
            "password": row[1],
            "szul_ido": row[2],
            "alkalmazott": row[3],
            "administrator": row[4]
        }

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    szabadsag_adatok = []
    for row in cursor.execute("SELECT * FROM Szabadsag"):
        szabadsag_adatok.append({
            "id": row[0],
            "datum_tol": row[1],
            "datum_ig": row[2],
            "alkalmazott_id": row[3]
        })

    if request.method == "POST":
        data = request.get_json()
        deletedInds = []
        updatedInds = []

        for i, adat in enumerate(szabadsag_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if (d["alkalmazott_id"] != adat["alkalmazott_id"] or
                        d["datum_tol"] != str(adat["datum_tol"]) or
                        d["datum_ig"] != str(adat["datum_ig"])):
                        szabadsag_adatok[i]["alkalmazott_id"] = d["alkalmazott_id"]
                        szabadsag_adatok[i]["datum_tol"] = datetime.datetime.strptime(d["datum_tol"], "%Y-%m-%d")
                        szabadsag_adatok[i]["datum_ig"] = datetime.datetime.strptime(d["datum_ig"], "%Y-%m-%d")
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)

        newData = []
        for d in data:
            found = False
            for adat in szabadsag_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                newData.append({
                    "alkalmazott_id": d["alkalmazott_id"],
                    "datum_tol": datetime.datetime.strptime(d["datum_tol"], "%Y-%m-%d"),
                    "datum_ig": datetime.datetime.strptime(d["datum_ig"], "%Y-%m-%d")
                })

        # MÓDOSÍTÁS
        for ind in updatedInds:
            cursor.execute("""
                UPDATE Szabadsag 
                SET mettol = :dtol, meddig = :dig, a_azonosito = :alk
                WHERE sz_azonosito = :id
            """, [
                szabadsag_adatok[ind]["datum_tol"],
                szabadsag_adatok[ind]["datum_ig"],
                szabadsag_adatok[ind]["alkalmazott_id"],
                szabadsag_adatok[ind]["id"]
            ])

        # TÖRLÉS
        for ind in deletedInds:
            cursor.execute("DELETE FROM Szabadsag WHERE sz_azonosito = :id", [szabadsag_adatok[ind]["id"]])

        # HOZZÁADÁS (tárolt eljárással)
        for d in newData:
            try:
                cursor.callproc("Uj_Szabadsag_Rogzitese", [
                    d["alkalmazott_id"],
                    d["datum_tol"],
                    d["datum_ig"]
                ])
            except oracledb.DatabaseError as e:  # cx_Oracle helyett oracledb
                error_obj, = e.args
                connection.rollback()
                return jsonify({"status": "hiba", "uzenet": error_obj.message}), 400

        connection.commit()
        return redirect(url_for("szabadsagok"))

    return render_template("szabadsagok.html", szabadsag_adatok=szabadsag_adatok)


@app.route("/munkabeosztas", methods=["POST", "GET"])
def munkabeosztas():
    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("SELECT * FROM Felhasznalo"):
        felhasznalok[row[0]] = {"password": row[1], "szul_ido": row[2], "alkalmazott": row[3], "administrator": row[4]}

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    munkabeosztas_adatok = []
    for row in cursor.execute("SELECT * FROM Munkabeosztas"):
        munkabeosztas_adatok.append({"id": row[0], "alkalmazott_id": row[1], "datum": row[2], "muszak": row[3]})

    if request.method == "POST":
        data = request.get_json()
        deletedInds = []
        updatedInds = []
        for i, adat in enumerate(munkabeosztas_adatok):
            found = False
            for d in data:
                if d["id"] == adat["id"]:
                    if (d["alkalmazott_id"] != adat["alkalmazott_id"] or
                        d["datum"] != str(adat["datum"]) or
                        d["muszak"] != adat["muszak"]):
                        munkabeosztas_adatok[i]["alkalmazott_id"] = d["alkalmazott_id"]
                        munkabeosztas_adatok[i]["datum"] = datetime.datetime.strptime(d["datum"], "%Y-%m-%d")
                        munkabeosztas_adatok[i]["muszak"] = d["muszak"]
                        updatedInds.append(i)
                    found = True
                    break
            if not found:
                deletedInds.append(i)

        newData = []
        for d in data:
            found = False
            for adat in munkabeosztas_adatok:
                if d["id"] == adat["id"]:
                    found = True
                    break
            if not found:
                newData.append({
                    "alkalmazott_id": d["alkalmazott_id"],
                    "datum": datetime.datetime.strptime(d["datum"], "%Y-%m-%d"),
                    "muszak": d["muszak"]
                })

        for ind in updatedInds:
            cursor.execute("""
                UPDATE Munkabeosztas 
                SET alkalmazott_azonosito = :alk, datum = :datum, muszak = :muszak
                WHERE munkabeosztas_azonosito = :id
            """, [munkabeosztas_adatok[ind]["alkalmazott_id"], munkabeosztas_adatok[ind]["datum"], munkabeosztas_adatok[ind]["muszak"], munkabeosztas_adatok[ind]["id"]])

        for ind in deletedInds:
            cursor.execute("DELETE FROM Munkabeosztas WHERE munkabeosztas_azonosito = :id", [munkabeosztas_adatok[ind]["id"]])

        if newData:
            cursor.executemany("""
                INSERT INTO Munkabeosztas (alkalmazott_azonosito, datum, muszak) 
                VALUES (:alkalmazott_id, :datum, :muszak)
            """, newData)

        connection.commit()

        return redirect(url_for("munkabeosztas"))

    return render_template("munkabeosztas.html", munkabeosztas_adatok=munkabeosztas_adatok)


@app.route("/alaplekerdezesek", methods=['POST', 'GET'])
def alaplekerdezesek():
    global felhasznalok
    global alapadatok

    connection, cursor = get_db()

    # Felhasználók betöltése
    felhasznalok = {}
    for row in cursor.execute("SELECT azonosito, jelszo, szul_ido, alkalmazott, administrator FROM Felhasznalo"):
        felhasznalok[row[0]] = {
            "password": row[1],
            "szul_ido": row[2],
            "alkalmazott": row[3],
            "administrator": row[4]
        }

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))

    # Alapadatok lekérdezése
    alapadatok = {
        "felhasznalok": [],
        "kedvezmenyek": [],
        "alkalmazottak": [],
        "szabadsagok": [],
        "munkabeosztas": []
    }

    for row in cursor.execute("SELECT azonosito, jelszo, szul_ido, alkalmazott, administrator FROM Felhasznalo"):
        alapadatok["felhasznalok"].append({
            "azonosito": row[0], "jelszo": row[1], "szul_ido": row[2],
            "alkalmazott": row[3], "administrator": row[4]
        })

    for row in cursor.execute("SELECT kedvezmeny_id, leiras, osszeg FROM Kedvezmeny"):
        alapadatok["kedvezmenyek"].append({
            "id": row[0], "leiras": row[1], "osszeg": row[2]
        })

    for row in cursor.execute("SELECT a_azonosito, nev, beosztas FROM Alkalmazott"):
        alapadatok["alkalmazottak"].append({
            "id": row[0], "nev": row[1], "beosztas": row[2]
        })

    for row in cursor.execute("SELECT szabadsag_id, alkalmazott_id, datum FROM Szabadsag"):
        alapadatok["szabadsagok"].append({
            "id": row[0], "alkalmazott_id": row[1], "datum": row[2]
        })

    for row in cursor.execute("SELECT beosztas_id, alkalmazott_id, nap, muszak FROM Munkabeosztas"):
        alapadatok["munkabeosztas"].append({
            "id": row[0], "alkalmazott_id": row[1], "nap": row[2], "muszak": row[3]
        })

    return render_template("alaplekerdezesek.html", alapadatok=alapadatok)









@app.route("/api/felhasznalok")
def api_felhasznalok():
    connection, cursor = get_db()
    eredmeny = []
    for row in cursor.execute("SELECT azonosito, jelszo, szul_ido, alkalmazott, administrator FROM Felhasznalo"):
        eredmeny.append({
            "azonosito": row[0],
            "jelszo": row[1],
            "szul_ido": row[2],
            "alkalmazott": row[3],
            "administrator": row[4]
        })
    return jsonify(eredmeny)


@app.route("/api/kedvezmenyek")
def api_kedvezmenyek():
    connection, cursor = get_db()
    eredmeny = []
    for row in cursor.execute("SELECT k_azonosito, nev, kedvezmeny_szazalek FROM Kedvezmeny"):
        eredmeny.append({
            "id": row[0],
            "nev": row[1],
            "szazalek": row[2]
        })
    return jsonify(eredmeny)


@app.route("/api/alkalmazottak")
def api_alkalmazottak():
    connection, cursor = get_db()
    eredmeny = []
    for row in cursor.execute("SELECT a_azonosito, nev, beosztas FROM Alkalmazott"):
        eredmeny.append({
            "id": row[0],
            "nev": row[1],
            "beosztas": row[2]
        })
    return jsonify(eredmeny)


@app.route("/api/szabadsagok")
def api_szabadsagok():
    connection, cursor = get_db()
    eredmeny = []
    for row in cursor.execute("SELECT sz_azonosito, a_azonosito, mettol, meddig FROM Szabadsag"):
        eredmeny.append({
            "id": row[0],
            "alkalmazott_id": row[1],
            "mettol": row[2],
            "meddig": row[3]
        })
    return jsonify(eredmeny)


@app.route("/api/munkabeosztas")
def api_munkabeosztas():
    connection, cursor = get_db()
    eredmeny = []
    for row in cursor.execute("SELECT mb_azonosito, a_azonosito, nap, muszak FROM Munkabeosztas"):
        eredmeny.append({
            "id": row[0],
            "alkalmazott_id": row[1],
            "nap": row[2],
            "muszak": row[3]
        })
    return jsonify(eredmeny)



# 509. sorba írtam, hogy onnan kezdődik és idáig tart Jani feladata,
# ha rossz, töröld vagy commenteld vagy javítsd ki


@app.route("/osszetett_lekerdezesek", methods=['POST', 'GET'])
def osszetett_lekerdezesek():
    global felhasznalok
    global alapadatok

    connection, cursor = get_db()

    felhasznalok = {}
    for row in cursor.execute("SELECT azonosito, jelszo, szul_ido, alkalmazott, administrator FROM Felhasznalo"):
        felhasznalok[row[0]] = {
            "password": row[1],
            "szul_ido": row[2],
            "alkalmazott": row[3],
            "administrator": row[4]
        }

    if "user" not in session or felhasznalok[session["user"]]["administrator"] == 0:
        return redirect(url_for("bejelentkezes"))
    
    return render_template("osszetett_lekerdezesek.html")


@app.route("/api/osszetett/jaratkereso")
def api_jaratkereso():
    connection, cursor = get_db()
    
    destination_loc = request.form['jaratkereso_hova']

    result = []
    for row in cursor.execute( 
        f"SELECT Jarat.jarat_azonosito, Jarat.nev FROM Jarat, Allomas, Csatlakozas WHERE Jarat.jarat_azonosito = Csatlakozas.jarat_azonosito AND a_azonosito = SELECT a_azonosito FROM Allomas, Csatlakozas WHERE a_azonosito = masodik_a_azonosito AND nev = {destination_loc}"
    ):
        result.append({
            "jarat_azonosito": row[0],
            "nev": row[1]
        })
    return jsonify(result)


@app.route("/api/osszetett/utasszam")
def api_jegyvasarlas():
    connection, cursor = get_db()
    
    year = request.form['utasszam_ev']

    result = []
    for row in cursor.execute( 
        f"SELECT jarat_azonosito SUM(utasszam) as sum, elso_osztalyu_helyek as maxelso, masod_osztalyu_helyek as maxmasod FROM Ut, Vonat WHERE YEAR(datum) = {year} GROUP BY jarat_azonosito HAVING COUNT(utasszam) > 0"

    ):
        result.append({
            "jarat_azonosito": row[0],
            "utasszam": row[1],
            "max_hely": row[2] + row[3]
        })
    return jsonify(result)


@app.route("/api/osszetett/eveskimutatas")
def api_eveskimutatas():
    connection, cursor = get_db()
    
    result = []
    for row in cursor.execute( 
    ):
        result.append({
        })
    return jsonify(result)


@app.route("/api/osszetett/arustat")
def api_arustat():
    connection, cursor = get_db()
    
    result = []
    for row in cursor.execute( 
    ):
        result.append({
        })
    return jsonify(result)


@app.route("/api/osszetett/onlinejegy")
def api_onlinejegy():
    connection, cursor = get_db()
    
    result = []
    for row in cursor.execute( 
    ):
        result.append({
        })
    return jsonify(result)


@app.route("/api/osszetett/berszabszam")
def api_berszabszam():
    connection, cursor = get_db()
    
    result = []
    for row in cursor.execute( 
    ):
        result.append({
        })
    return jsonify(result)


@app.route("/api/osszetett/jegyvasarlas")
def api_utasszam():
    connection, cursor = get_db()
    
    result = []
    for row in cursor.execute( 
    ):
        result.append({
        })
    return jsonify(result)