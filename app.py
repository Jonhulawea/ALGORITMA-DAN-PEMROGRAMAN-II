from flask import Flask, render_template, request, redirect, session
import json
import os

app = Flask(__name__)
app.secret_key = "simti"

FILE_MHS = "mahasiswa.json"
FILE_USER = "user.json"

# =========================
# DATABASE
# =========================

def load_mhs():
    if os.path.exists(FILE_MHS):
        with open(FILE_MHS,"r") as f:
            return json.load(f)
    return []

def save_mhs(data):
    with open(FILE_MHS,"w") as f:
        json.dump(data,f,indent=4)

def load_user():
    if os.path.exists(FILE_USER):
        with open(FILE_USER,"r") as f:
            return json.load(f)
    return []

def save_user(data):
    with open(FILE_USER,"w") as f:
        json.dump(data,f,indent=4)
        
# =========================
# HELPER
# =========================

def get_mahasiswa(nim):

    data = load_mhs()

    for mhs in data:

        if mhs["nim"] == nim:
            return mhs

    return None

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if "percobaan" not in session:
        session["percobaan"] = 0

    if "blokir" not in session:
        session["blokir"] = False

    if session["blokir"]:
        return render_template(
            "login.html",
            error="Akun dikunci setelah 3 kali percobaan login."
        )

    error = ""

    if request.method == "POST":

        nim = request.form["nim"]
        password = request.form["password"]

        users = load_user()

        for user in users:

            if user["nim"] == nim and user["password"] == password:

                session["login"] = True
                session["nama"] = user["nama"]
                session["nim"] = user["nim"]
                session["role"] = user["role"]

                session["percobaan"] = 0

                return redirect("/")

        session["percobaan"] += 1

        sisa = 3 - session["percobaan"]

        if session["percobaan"] >= 3:

            session["blokir"] = True

            error = "Akun dikunci setelah 3 kali percobaan login."

        else:

            error = f"Login gagal! Sisa percobaan {sisa} kali."

    return render_template(
        "login.html",
        error=error
    )
    
# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():

    session.clear()
    return redirect("/login")

# =========================
# DASHBOARD
# =========================
@app.route("/")
def dashboard():

    if "login" not in session:
        return redirect("/login")

    mahasiswa = load_mhs()

    total_mahasiswa = len(mahasiswa)

    total_matkul = sum(
        len(m["matakuliah"])
        for m in mahasiswa
    )

    return render_template(
        "index.html",
        mahasiswa=mahasiswa,
        total_mahasiswa=total_mahasiswa,
        total_matkul=total_matkul
    )
    
# =========================
# DATA MAHASISWA
# =========================
@app.route("/mahasiswa")
def data_mahasiswa():

    data = load_mhs()

    q = request.args.get("q", "").lower()

    if q:

        data = [

            mhs for mhs in data

            if (
                q in mhs["nama"].lower()
                or q in mhs["nim"].lower()
            )

        ]

    return render_template(
        "data_mahasiswa.html",
        mahasiswa=data
    )
    
# =========================
# TAMBAH MAHASISWA
# =========================
@app.route("/tambah", methods=["GET", "POST"])
def tambah():

    error = ""

    if request.method == "POST":

        data = load_mhs()

        nim = request.form["nim"]

        # Cek NIM sudah ada atau belum
        for mhs in data:
            if mhs["nim"] == nim:

                error = f"NIM {nim} sudah terdaftar!"

                return render_template(
                    "tambah_mahasiswa.html",
                    error=error
                )

        mahasiswa_baru = {

            "nim": nim,
            "nama": request.form["nama"],
            "jurusan": request.form["jurusan"],
            "semester": request.form["semester"],
            "ipk": request.form["ipk"],

            "absensi": {
                "hadir": 0,
                "izin": 0,
                "sakit": 0,
                "alpa": 0
            },

            "matakuliah": []

        }

        data.append(mahasiswa_baru)

        save_mhs(data)

        return redirect("/mahasiswa")

    return render_template(
        "tambah_mahasiswa.html",
        error=error
    )
    
# =========================
# EDIT MAHASISWA
# =========================
@app.route("/edit/<nim>", methods=["GET","POST"])
def edit(nim):

    data = load_mhs()

    mahasiswa = next(
        (m for m in data if m["nim"] == nim),
        None
    )

    if request.method == "POST":

        mahasiswa["nim"] = request.form["nim"]
        mahasiswa["nama"] = request.form["nama"]
        mahasiswa["jurusan"] = request.form["jurusan"]
        mahasiswa["semester"] = request.form["semester"]
        mahasiswa["ipk"] = request.form["ipk"]

        save_mhs(data)

        return redirect("/mahasiswa")

    return render_template(
        "edit_mahasiswa.html",
        mahasiswa=mahasiswa
    )

# =========================
# HAPUS
# =========================

@app.route("/hapus/<nim>")
def hapus(nim):

    data=load_mhs()

    data=[
        x for x in data
        if x["nim"]!=nim
    ]

    save_mhs(data)

    return redirect("/")

# =========================
# AKADEMIK
# =========================
@app.route("/akademik/<nim>")
def akademik(nim):

    data = load_mhs()

    for mhs in data:

        if mhs["nim"] == nim:

            if "absensi" not in mhs:
                mhs["absensi"] = {
                    "hadir": 0,
                    "izin": 0,
                    "sakit": 0,
                    "alpa": 0
                }

                save_mhs(data)

            return render_template(
                "akademik.html",
                mahasiswa=mhs
            )

    return redirect("/")


# =========================
# TAMBAH MATA KULIAH
# =========================
@app.route("/tambah-matkul/<nim>", methods=["GET", "POST"])
def tambah_matkul(nim):

    data = load_mhs()

    for mhs in data:

        if mhs["nim"] == nim:

            if request.method == "POST":

                # ID otomatis
                if mhs["matakuliah"]:

                    next_id = max(
                        mk["id"]
                        for mk in mhs["matakuliah"]
                    ) + 1

                else:

                    next_id = 1

                sks = int(request.form["sks"])

                jumlah = 14 if sks == 2 else 21

                presensi = []

                for i in range(1, jumlah + 1):

                    pola = (i - 1) % 3

                    if pola == 1:
                        metode = "Daring"
                    else:
                        metode = "Tatap Muka"

                    presensi.append({
                        "pertemuan": i,
                        "tanggal": "-",
                        "jam": "-",
                        "metode": metode,
                        "status": "-"
                    })

                mhs["matakuliah"].append({

                    "id": next_id,
                    "kode": request.form["kode"],
                    "nama": request.form["nama"],
                    "dosen": request.form["dosen"],
                    "sks": sks,
                    "nilai": request.form["nilai"],
                    "presensi": presensi

                })

                save_mhs(data)

                return redirect(
                    f"/akademik/{nim}"
                )

            return render_template(
                "tambah_matkul.html",
                mahasiswa=mhs
            )

    return redirect("/")

# =========================
# EDIT MATKUL
# =========================
@app.route("/edit-matkul/<nim>/<int:id>", methods=["GET","POST"])
def edit_matkul(nim, id):
    
    data=load_mhs()

    for mhs in data:

        if mhs["nim"]==nim:

            for mk in mhs["matakuliah"]:

                if mk["id"]==id:

                    if request.method=="POST":

                        mk["kode"]=request.form["kode"]
                        mk["nama"]=request.form["nama"]
                        mk["dosen"]=request.form["dosen"]
                        mk["sks"]=request.form["sks"]
                        mk["nilai"]=request.form["nilai"]

                        save_mhs(data)

                        return redirect(
                            f"/akademik/{nim}"
                        )

                    return render_template(
                        "edit_matkul.html",
                        matkul=mk,
                        mahasiswa=mhs
                    )

# =========================
# HAPUS MATKUL
# =========================
@app.route("/hapus-matkul/<nim>/<int:id>")
def hapus_matkul(nim,id):

    data=load_mhs()

    for mhs in data:

        if mhs["nim"]==nim:

            mhs["matakuliah"]=[
                mk for mk in mhs["matakuliah"]
                if mk["id"]!=id
            ]

            save_mhs(data)

            return redirect(
                f"/akademik/{nim}"
            )

# =========================
# ABSENSI
# =========================

@app.route("/absensi/<nim>",methods=["GET","POST"])
def absensi(nim):

    data=load_mhs()

    for mhs in data:

        if mhs["nim"]==nim:

            if request.method=="POST":

                mhs["absensi"]["hadir"]=request.form["hadir"]
                mhs["absensi"]["izin"]=request.form["izin"]
                mhs["absensi"]["sakit"]=request.form["sakit"]
                mhs["absensi"]["alpa"]=request.form["alpa"]

                save_mhs(data)

                return redirect(
                    f"/akademik/{nim}"
                )

            return render_template(
                "absensi.html",
                mahasiswa=mhs
            )
# =========================
# DETAIL ABSENSI
# =========================     
@app.route("/set-status/<nim>/<int:id>/<int:pertemuan>/<status>")
def set_status(nim,id,pertemuan,status):

    data = load_mhs()

    for mhs in data:

        if mhs["nim"] == nim:

            for mk in mhs["matakuliah"]:

                if mk["id"] == id:

                    for p in mk["presensi"]:

                        if p["pertemuan"] == pertemuan:

                            p["status"] = status

            hadir = 0
            izin = 0
            sakit = 0
            alpa = 0

            for matkul in mhs["matakuliah"]:

                if "presensi" in matkul:

                    for p in matkul["presensi"]:

                        if p["status"] == "Hadir":
                            hadir += 1

                        elif p["status"] == "Izin":
                            izin += 1

                        elif p["status"] == "Sakit":
                            sakit += 1

                        elif p["status"] == "Alpa":
                            alpa += 1

            mhs["absensi"] = {
                "hadir": hadir,
                "izin": izin,
                "sakit": sakit,
                "alpa": alpa
            }

            save_mhs(data)

            return redirect(
                f"/detail-absensi/{nim}/{id}"
            )

    return redirect("/")

# =========================
# PENCARIAN
# =========================
@app.route("/pencarian", methods=["GET", "POST"])
def pencarian():

    if "login" not in session:
        return redirect("/login")

    hasil = None
    keyword = ""

    if request.method == "POST":

        keyword = request.form["keyword"].lower()

        data = load_mhs()

        hasil = []

        for mhs in data:

            if (
                keyword in mhs["nim"].lower()
                or keyword in mhs["nama"].lower()
                or keyword in mhs["jurusan"].lower()
            ):
                hasil.append(mhs)

    return render_template(
        "pencarian.html",
        hasil=hasil,
        keyword=keyword
    )
    
# =========================
# PENGURUTAN
# =========================
@app.route("/pengurutan", methods=["GET","POST"])
def pengurutan():

    hasil = None
    algoritma = ""
    field = ""

    if request.method == "POST":

        data = load_mhs()

        algoritma = request.form["algoritma"]
        field = request.form["field"]

        if field == "nama":
            data.sort(
                key=lambda x: x["nama"].lower()
            )

        elif field == "nim":
            data.sort(
                key=lambda x: x["nim"]
            )

        hasil = data

    return render_template(
        "pengurutan.html",
        hasil=hasil,
        algoritma=algoritma,
        field=field
    )

# =========================
# ABOUT
# =========================

@app.route("/about")
def about():
    return render_template("about.html")

# =========================

if __name__=="__main__":
    app.run(debug=True)