from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= DB INIT =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS songs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        artist TEXT,
        filename TEXT,
        lyrics TEXT,
        views INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================
@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM songs ORDER BY views DESC")
    songs = c.fetchall()
    conn.close()
    return render_template("index.html", songs=songs)

# ================= SEARCH =================
@app.route("/search")
def search():
    q = request.args.get("q", "")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM songs WHERE title LIKE ? OR artist LIKE ?",
              ('%'+q+'%', '%'+q+'%'))
    songs = c.fetchall()
    conn.close()
    return render_template("index.html", songs=songs)

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users(username,password) VALUES(?,?)",
                      (username,password))
            conn.commit()
        except:
            return "Username already exists!"
        conn.close()
        return redirect("/login")

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/")
        return "Invalid Login"

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ================= UPLOAD =================
@app.route("/upload", methods=["GET","POST"])
def upload():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        artist = request.form["artist"]
        lyrics = request.form["lyrics"]
        file = request.files["file"]

        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
        INSERT INTO songs(title,artist,filename,lyrics)
        VALUES(?,?,?,?)
        """,(title,artist,filename,lyrics))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("upload.html")

# ================= SONG =================
@app.route("/song/<int:id>")
def song(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE songs SET views=views+1 WHERE id=?", (id,))
    conn.commit()

    c.execute("SELECT * FROM songs WHERE id=?", (id,))
    song = c.fetchone()
    conn.close()

    return render_template("song.html", song=song)

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM songs")
    songs = c.fetchone()[0]

    conn.close()

    return render_template("admin.html", users=users, songs=songs)

# ================= FILE =================
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ================= RUN (IMPORTANT) =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
