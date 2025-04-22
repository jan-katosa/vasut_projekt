from flask import Flask, render_template, request, g
import getpass
import oracledb

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session


def execute_sql(sql_file, db_cursor):
    with open(sql_file, "r", encoding="utf-8") as f:
        statement_parts = []
        for line in f:
            if line.startswith("--"):
                continue
            if line.strip() == "/":
                statement = "".join(statement_parts).strip()
                if statement:
                    try:
                        db_cursor.execute(statement)
                    except Exception as e:
                        print("Failed to execute SQL:", statement)
                        raise e
                statement_parts = []
            else:
                statement_parts.append(line)


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
        execute_sql("tabla_letrehozo.sql", g.cursor)
        g.db.commit()
    return g.db, g.cursor


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


app = Flask(__name__, template_folder="views")
app.teardown_appcontext(close_db)

vonat_adatok = [
    {"id": 0, "elsoosztaly": 10, "masodosztaly": 60},
    {"id": 1, "elsoosztaly": 20, "masodosztaly": 50},
    {"id": 2, "elsoosztaly": 15, "masodosztaly": 100},
    {"id": 3, "elsoosztaly": 25, "masodosztaly": 200},
]

allomas_adatok = [
    {"id": 0, "nev": "állomás 1", "varos": "Szeged"},
    {"id": 1, "nev": "állomás 2", "varos": "Szeged"},
    {"id": 2, "nev": "állomás 3", "varos": "Szeged 2"},
    {"id": 3, "nev": "állomás 4", "varos": "Szeged 3"},
]

jegy_adatok = [
    {"id": 0, "nev": "jegy 1", "ar": 2000, "felhasznalhato": 3},
    {"id": 1, "nev": "jegy 2", "ar": 1000, "felhasznalhato": 1},
    {"id": 2, "nev": "jegy 3", "ar": 4000, "felhasznalhato": 7},
    {"id": 3, "nev": "jegy 4", "ar": 5500, "felhasznalhato": 6},
]

csatlakozas_adatok = [
    {"id": 0, "idotartam": 30, "hossz": 12.0, "elso_id": 0, "masodik_id": 1, "jarat_id": 0},
    {"id": 1, "idotartam": 20, "hossz": 14.0, "elso_id": 1, "masodik_id": 2, "jarat_id": 0},
    {"id": 2, "idotartam": 15, "hossz": 10.0, "elso_id": 0, "masodik_id": 2, "jarat_id": 1},
    {"id": 3, "idotartam": 20, "hossz": 15.0, "elso_id": 0, "masodik_id": 1, "jarat_id": 2},
    {"id": 4, "idotartam": 40, "hossz": 25.0, "elso_id": 1, "masodik_id": 3, "jarat_id": 2},
    {"id": 5, "idotartam": 30, "hossz": 30.0, "elso_id": 2, "masodik_id": 3, "jarat_id": 3},
]

jarat_adatok = [
    {"id": 0, "indulas": 1000, "vonat": 0, "utvonal": 0},
    {"id": 1, "indulas": 2000, "vonat": 0, "utvonal": 2},
    {"id": 2, "indulas": 3000, "vonat": 1, "utvonal": 3},
    {"id": 3, "indulas": 4000, "vonat": 2, "utvonal": 5},
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/vonatok", methods=['POST', 'GET'])
def vonatok():
    db, cursor = get_db()
    global vonat_adatok
    if request.method == 'POST':
        data = request.get_json()
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
                        cursor.execute("""
                            UPDATE vonatok SET elsoosztaly = :1, masodosztaly = :2 WHERE id = :3
                        """, [d["elsoosztaly"], d["masodosztaly"], d["id"]])
                        db.commit()
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
                newData.append(d)
                vonat_adatok.append(d)
                cursor.execute("""
                    INSERT INTO vonatok (id, elsoosztaly, masodosztaly) VALUES (:1, :2, :3)
                """, [d["id"], d["elsoosztaly"], d["masodosztaly"]])
                db.commit()

    return render_template("vonatok.html", vonat_adatok=vonat_adatok)


@app.route("/jaratok")
def jaratok():
    global csatlakozas_adatok, jarat_adatok
    max_csatlakozas_id = max(c["id"] for c in csatlakozas_adatok)
    return render_template("jaratok.html", jarat_adatok=jarat_adatok,
                           vonat_adatok=vonat_adatok,
                           csatlakozas_adatok=csatlakozas_adatok,
                           max_csatlakozas_id=max_csatlakozas_id)


@app.route("/allomasok", methods=['POST', 'GET'])
def allomasok():
    db, cursor = get_db()
    global allomas_adatok
    if request.method == 'POST':
        data = request.get_json()
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
                        cursor.execute("""
                            UPDATE allomasok SET nev = :1, varos = :2 WHERE id = :3
                        """, [d["nev"], d["varos"], d["id"]])
                        db.commit()
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
                newData.append(d)
                allomas_adatok.append(d)
                cursor.execute("""
                    INSERT INTO allomasok (id, nev, varos) VALUES (:1, :2, :3)
                """, [d["id"], d["nev"], d["varos"]])
                db.commit()

    return render_template("allomasok.html", allomas_adatok=allomas_adatok)


@app.route("/jegyek", methods=['POST', 'GET'])
def jegyek():
    db, cursor = get_db()
    global jegy_adatok
    if request.method == 'POST':
        data = request.get_json()
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
                        cursor.execute("""
                            UPDATE jegyek 
                            SET nev = :1, ar = :2, felhasznalhato = :3 
                            WHERE id = :4
                        """, [d["nev"], d["ar"], d["felhasznalhato"], d["id"]])
                        db.commit()
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
                newData.append(d)
                jegy_adatok.append(d)
                cursor.execute("""
                    INSERT INTO jegyek (id, nev, ar, felhasznalhato) 
                    VALUES (:1, :2, :3, :4)
                """, [d["id"], d["nev"], d["ar"], d["felhasznalhato"]])
                db.commit()

    return render_template("jegyek.html", jegy_adatok=jegy_adatok)



app = Flask(__name__, template_folder="views")
app.secret_key = "nagyontitkoskod"  # titkos kulcs a session-höz

# Használunk szerver-oldali session tárolást
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Átmeneti felhasználói adatbázis (normál esetben ez adatbázis lenne)
felhasznalok = {}  # {username: {"email": email, "password": hashed_pw}}


@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("bejelentkezes"))
    return render_template("index.html", user=session["user"])


@app.route("/bejelentkezes", methods=["GET", "POST"])
def bejelentkezes():
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
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if username in felhasznalok:
            return "Ez a felhasználónév már foglalt!", 400

        hashed_pw = generate_password_hash(password)
        felhasznalok[username] = {"email": email, "password": hashed_pw}
        session["user"] = username
        return redirect(url_for("index"))

    return render_template("regisztracio.html")


@app.route("/kijelentkezes")
def kijelentkezes():
    session.pop("user", None)
    return redirect(url_for("bejelentkezes"))


# Innen kezdve minden funkcióhoz belépés szükséges
@app.route("/vonatok", methods=["GET", "POST"])
def vonatok():
    if "user" not in session:
        return redirect(url_for("bejelentkezes"))
    # példa adat
    vonatok = [{"id": 0, "elsoosztaly": 20, "masodosztaly": 60}]
    return render_template("vonatok.html", vonat_adatok=vonatok)


@app.route("/allomasok", methods=["GET", "POST"])
def allomasok():
    if "user" not in session:
        return redirect(url_for("bejelentkezes"))
    allomasok = [{"id": 0, "nev": "állomás 1", "varos": "Szeged"}]
    return render_template("allomasok.html", allomas_adatok=allomasok)


@app.route("/jegyek", methods=["GET", "POST"])
def jegyek():
    if "user" not in session:
        return redirect(url_for("bejelentkezes"))
    jegyek = [{"id": 0, "nev": "jegy 1", "ar": 2000, "felhasznalhato": 3}]
    return render_template("jegyek.html", jegy_adatok=jegyek)





@app.route("/jaratok")
def jaratok():
    if "user" not in session:
        return redirect(url_for("bejelentkezes"))

    jarat_adatok = [
        {"id": 0, "indulas": 1000, "vonat": 0, "utvonal": 0},
        {"id": 1, "indulas": 2000, "vonat": 0, "utvonal": 2},
        {"id": 2, "indulas": 3000, "vonat": 1, "utvonal": 3},
        {"id": 3, "indulas": 4000, "vonat": 2, "utvonal": 5},
    ]

    csatlakozas_adatok = [
        {"id": 0, "idotartam": 30, "hossz": 12.0, "elso_id": 0, "masodik_id": 1, "jarat_id": 0},
        {"id": 1, "idotartam": 20, "hossz": 14.0, "elso_id": 1, "masodik_id": 2, "jarat_id": 0},
        {"id": 2, "idotartam": 15, "hossz": 10.0, "elso_id": 0, "masodik_id": 2, "jarat_id": 1},
        {"id": 3, "idotartam": 20, "hossz": 15.0, "elso_id": 0, "masodik_id": 1, "jarat_id": 2},
        {"id": 4, "idotartam": 40, "hossz": 25.0, "elso_id": 1, "masodik_id": 3, "jarat_id": 2},
        {"id": 5, "idotartam": 30, "hossz": 30.0, "elso_id": 2, "masodik_id": 3, "jarat_id": 3},
    ]

    vonat_adatok = [
        {"id": 0, "elsoosztaly": 10, "masodosztaly": 60},
        {"id": 1, "elsoosztaly": 20, "masodosztaly": 50},
        {"id": 2, "elsoosztaly": 15, "masodosztaly": 100},
    ]

    max_csatlakozas_id = max(c["id"] for c in csatlakozas_adatok)

    return render_template("jaratok.html",
                           jarat_adatok=jarat_adatok,
                           csatlakozas_adatok=csatlakozas_adatok,
                           vonat_adatok=vonat_adatok,
                           max_csatlakozas_id=max_csatlakozas_id)





if __name__ == "__main__":
    app.run(debug=True)
