import psycopg2
from flask import Flask, render_template, request, redirect, url_for

# import psycopg2.extras

common_dict = {}

app = Flask(__name__)


def build_connection_with_database():
    conn = psycopg2.connect(database="medapp", host="localhost", port="5432", user="postgres", password="123")
    return conn


def close_connection_with_database(cur, conn):
    conn.commit()
    cur.close()
    conn.close()


@app.route("/")
def home_page():
    return render_template("home_page.html")


@app.route('/doctor_registration', methods=["POST", "GET"])
def doctor_registration():
    if request.method == "POST":
        name = request.form["name"]
        name = name.replace(".", "_").lower()
        specialty = request.form["specialty"].lower()
        reg_no = request.form["reg_no"]
        city = request.form["city"].lower()
        town = request.form["town"].lower()
        area_code = request.form["area_code"]
        meeting_link = request.form["meeting_link"]
        conn = build_connection_with_database()
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO doctor_info(name, speciality, reg_no, city, town, area_code, meeting_link) VALUES ('{name}','{specialty}','{reg_no}','{city}','{town}','{area_code}','{meeting_link}')")
        cur.execute(f"CREATE TABLE {name} (patient varchar, mobile_no varchar, app_type varchar)")
        close_connection_with_database(cur, conn)
        return redirect(url_for("doctor_login"))
    return render_template("doctor_registration.html")


@app.route('/doctor_login', methods=["POST", "GET"])
def doctor_login():
    if request.method == "POST":
        name = request.form["name"]
        name = name.replace(".", "_").lower()
        common_dict["login_dr"] = name
        reg_no = request.form["reg_no"]
        conn = build_connection_with_database()
        cur = conn.cursor()
        cur.execute("SELECT reg_no FROM doctor_info WHERE name = %s", (name,))
        fetched_reg_no = cur.fetchone()
        if reg_no == fetched_reg_no[0]:
            cur.execute("INSERT INTO live_dr(dr_name) VALUES (%s)", (name,))
            close_connection_with_database(cur, conn)
            return redirect(url_for("doctor_dashboard"))
    return render_template("doctor_login.html")


@app.route('/doctor_dashboard')
def doctor_dashboard():
    conn = build_connection_with_database()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {common_dict["login_dr"]}')
    data = cur.fetchall()
    cur.execute(f"SELECT meeting_link FROM doctor_info WHERE name = '{common_dict['login_dr']}'")
    meetlink = cur.fetchone()
    close_connection_with_database(cur, conn)
    # print(data)
    return render_template("doctor_dashboard.html", data=data, meetlink=meetlink)


@app.route("/doctor_logout", methods=["POST", "GET"])
def doctor_logout():
    # print("enter log")
    if request.method == "POST":
        val_ = request.form["logout"]
        # print(val_)
        if val_ == "logout":
            conn = build_connection_with_database()
            cur = conn.cursor()
            cur.execute("DELETE FROM live_dr WHERE dr_name = %s", (common_dict["login_dr"],))
            close_connection_with_database(cur, conn)
    return render_template("home_page.html")


@app.route("/delete", methods=["POST", 'GET'])
def delete():
    if request.method == "POST":
        patient_name = request.form["name"]
        conn = build_connection_with_database()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {common_dict['login_dr']} WHERE patient = '{patient_name}'")
        close_connection_with_database(cur, conn)
        return redirect(url_for("doctor_dashboard"))


@app.route("/update", methods=["POST", 'GET'])
def update():
    if request.method == "POST":
        new_meeting_link = request.form["meetlink"]
        conn = build_connection_with_database()
        cur = conn.cursor()
        cur.execute(
            f"UPDATE doctor_info SET meeting_link = '{new_meeting_link}' WHERE name = '{common_dict['login_dr']}'")
        close_connection_with_database(cur, conn)
        return redirect(url_for("doctor_dashboard"))


@app.route('/user_registration', methods=["POST", "GET"])
def user_registration():
    if request.method == "POST":
        name = request.form["name"].lower()
        mobile_no = request.form["mobile"]
        city = request.form["city"].lower()
        town = request.form["town"].lower()
        area_code = request.form["area_code"]
        password = request.form["password"]
        conn = build_connection_with_database()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_info (name, mobile_no, city, town, area_code, password) VALUES (%s,%s,%s,%s,%s,%s)",
            (name, mobile_no, city, town, area_code, password))
        close_connection_with_database(cur, conn)
        return redirect(url_for("user_login"))
    return render_template("user_register.html")


@app.route('/user_login', methods=["POST", "GET"])
def user_login():
    if request.method == "POST":
        name = request.form["name"].lower()
        common_dict["login_user"] = name
        password = request.form["password"]
        conn = build_connection_with_database()
        cur = conn.cursor()
        cur.execute("SELECT password FROM user_info WHERE name = %s", (name,))
        fetched_password = cur.fetchone()
        close_connection_with_database(cur, conn)
        if password == fetched_password[0]:
            return redirect(url_for("user_dashboard"))
        else:
            print("Wrong Password")
    return render_template("user_login.html")


@app.route("/user_dashboard", methods=["POST", "GET"])
def user_dashboard():
    conn = build_connection_with_database()
    cur = conn.cursor()
    cur.execute("SELECT * FROM live_dr")
    live_dr = cur.fetchall()
    close_connection_with_database(cur, conn)
    if request.method == "POST":
        dr_name = request.form["dr_name"]
        conn = build_connection_with_database()
        cur = conn.cursor()
        cur.execute("SELECT mobile_no FROM user_info WHERE name = %s ", (common_dict["login_user"],))
        fetched_mobile_no = cur.fetchone()
        app_type = "now"
        cur.execute(f"INSERT INTO {dr_name}(patient, mobile_no, app_type) VALUES (%s,%s,%s)",
                    (common_dict["login_user"], fetched_mobile_no[0], app_type))
        cur.execute(f"INSERT INTO user_appointment(name, dr_name) VALUES (%s,%s)", (common_dict["login_user"], dr_name))
        close_connection_with_database(cur, conn)
        return redirect(url_for("user_appointment"))
    return render_template("user_dashboard.html", live_dr=live_dr)


@app.route("/user_appointment")
def user_appointment():
    conn = build_connection_with_database()
    cur = conn.cursor()
    cur.execute("SELECT dr_name FROM user_appointment WHERE name = %s", (common_dict["login_user"],))
    fetched_dr_name = cur.fetchone()
    cur.execute(F"SELECT app_type FROM {fetched_dr_name[0]} WHERE patient = %s", (common_dict["login_user"],))
    fetched_app_type = cur.fetchone()
    if fetched_app_type is not None:
        if fetched_app_type[0] == "now":
            cur.execute("SELECT meeting_link FROM doctor_info WHERE name = %s", (fetched_dr_name[0],))
            fetched_meeting_link = cur.fetchone()
    else:
        return "No Appointments"
    close_connection_with_database(cur, conn)
    return render_template("user_appointment.html", dr_name=fetched_dr_name, meeting_link=fetched_meeting_link)


if "__main__" == __name__:
    app.run(debug=True)
