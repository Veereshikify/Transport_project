from flask import Flask, request, render_template, session, redirect
from datetime import datetime
from reportlab.pdfgen import canvas
from flask import send_file
from io import BytesIO
import mysql.connector

app = Flask(__name__)
app.secret_key = "transport_secret_key"

# ================= DB =================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="9900552764",
    database="transport_system"
)

# ================= ROLE SECURITY =================
def allow(*roles):
    if "user_id" not in session:
        return False
    return session["role"] in roles


# ================= HOME =================
@app.route("/")
def home():
    return "Flask + MySQL Connected Successfully 🚍🔥"


# ================= LOGIN =================
@app.route("/login_page")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()

    if user:
        session["user_id"] = user[0]
        session["name"] = user[1]
        session["role"] = user[4]
        return redirect("/dashboard")
    return "Invalid Login ❌"


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login_page")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login_page")

    role = session["role"]

    if role == "admin":
        return render_template("admin_home.html")

    elif role == "manager":
        return render_template("manager_dashboard.html")

    else:
        return render_template("employee_dashboard.html")


# ================= EMPLOYEES (ADMIN ONLY) =================
@app.route("/employees")
def employees():
    if not allow("admin"):
        return "Access Denied ❌"

    cursor = db.cursor()
    cursor.execute("SELECT * FROM employees")
    data = cursor.fetchall()
    return render_template("employees.html", employees=data)


@app.route("/add_employee", methods=["POST"])
def add_employee():
    if not allow("admin"):
        return "Access Denied ❌"

    name = request.form["name"]
    role = request.form["role"]
    phone = request.form["phone"]
    depot = request.form["depot"]

    cursor = db.cursor()
    cursor.execute("INSERT INTO employees(name, role, phone, depot) VALUES (%s,%s,%s,%s)",
                   (name, role, phone, depot))
    db.commit()
    return redirect("/employees")


@app.route("/delete_employee/<int:id>")
def delete_employee(id):
    if not allow("admin"):
        return "Access Denied ❌"

    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
    db.commit()
    return redirect("/employees")


@app.route("/edit_employee/<int:id>")
def edit_employee(id):
    if not allow("admin"):
        return "Access Denied ❌"

    cursor = db.cursor()
    cursor.execute("SELECT * FROM employees WHERE id=%s", (id,))
    emp = cursor.fetchone()
    return render_template("edit_employee.html", emp=emp)


@app.route("/update_employee/<int:id>", methods=["POST"])
def update_employee(id):
    if not allow("admin"):
        return "Access Denied ❌"

    name = request.form["name"]
    role = request.form["role"]
    phone = request.form["phone"]
    depot = request.form["depot"]

    cursor = db.cursor()
    cursor.execute(
        "UPDATE employees SET name=%s, role=%s, phone=%s, depot=%s WHERE id=%s",
        (name, role, phone, depot, id))
    db.commit()
    return redirect("/employees")


# ================= ATTENDANCE (ALL ROLES) =================
@app.route("/attendance")
def attendance():
    if "user_id" not in session:
        return redirect("/login_page")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM attendance ORDER BY id DESC")
    data = cursor.fetchall()
    return render_template("attendance.html", data=data)


@app.route("/mark_in", methods=["POST"])
def mark_in():
    emp_id = request.form["emp_id"]
    name = request.form["name"]

    cursor = db.cursor()
    cursor.execute("INSERT INTO attendance(employee_id, name, status, time) VALUES (%s,%s,%s,NOW())",
                   (emp_id, name, "IN"))
    db.commit()
    return redirect("/attendance")


@app.route("/mark_out", methods=["POST"])
def mark_out():
    emp_id = request.form["emp_id"]
    name = request.form["name"]

    cursor = db.cursor()
    cursor.execute("INSERT INTO attendance(employee_id, name, status, time) VALUES (%s,%s,%s,NOW())",
                   (emp_id, name, "OUT"))
    db.commit()
    return redirect("/attendance")


# ================= FUEL / CONDUCTOR =================
@app.route("/fuel")
def fuel():
    if "user_id" not in session:
        return redirect("/login_page")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM fuel_collection ORDER BY id DESC")
    data = cursor.fetchall()
    return render_template("fuel.html", data=data)


@app.route("/check_role", methods=["POST"])
def check_role():
    emp_id = request.form["emp_id"]

    cursor = db.cursor()
    cursor.execute("SELECT name, role FROM employees WHERE id=%s", (emp_id,))
    emp = cursor.fetchone()

    if not emp:
        return "Employee Not Found"
    role = emp[1]

    if role.lower() == "driver":
        return redirect(f"/driver_fuel/{emp_id}")
    return redirect(f"/conductor_money/{emp_id}")


@app.route("/driver_fuel/<emp_id>")
def driver_fuel(emp_id):
    cursor = db.cursor()
    cursor.execute("SELECT name FROM employees WHERE id=%s", (emp_id,))
    name = cursor.fetchone()[0]

    return f"""
        <h1>Driver Fuel Entry</h1>
        <h3>Name: {name}</h3>
        <form action='/save_fuel' method='post'>
            <input type='hidden' name='emp_id' value='{emp_id}'>
            <input type='hidden' name='name' value='{name}'>
            Bus No: <input name='bus'><br><br>
            Diesel Used: <input name='diesel'><br><br>
            <button type='submit'>Save</button>
        </form>
        <a href='/fuel'>Back</a>
    """


@app.route("/conductor_money/<emp_id>")
def conductor_money(emp_id):
    cursor = db.cursor()
    cursor.execute("SELECT name FROM employees WHERE id=%s", (emp_id,))
    name = cursor.fetchone()[0]

    return f"""
        <h1>Conductor Collection Entry</h1>
        <h3>Name: {name}</h3>
        <form action='/save_fuel' method='post'>
            <input type='hidden' name='emp_id' value='{emp_id}'>
            <input type='hidden' name='name' value='{name}'>
            Bus No: <input name='bus'><br><br>
            Money Collected ₹: <input name='money'><br><br>
            <button type='submit'>Save</button>
        </form>
        <a href='/fuel'>Back</a>
    """


@app.route("/save_fuel", methods=["POST"])
def save_fuel():
    emp_id = request.form["emp_id"]
    name = request.form["name"]
    bus = request.form["bus"]

    diesel = request.form.get("diesel") or 0
    money = request.form.get("money") or 0

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO fuel_collection(employee_id, name, bus_no, diesel_used, money_collected, date_time) "
        "VALUES (%s,%s,%s,%s,%s,NOW())",
        (emp_id, name, bus, diesel, money))
    db.commit()
    return redirect("/fuel")


# ================= LOST ITEMS (ALL ROLES) =================
@app.route("/lost")
def lost():
    if "user_id" not in session:
        return redirect("/login_page")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM lost_items ORDER BY id DESC")
    data = cursor.fetchall()
    return render_template("lost.html", data=data)


@app.route("/save_lost", methods=["POST"])
def save_lost():
    passenger = request.form["passenger"]
    contact = request.form["contact"]
    item = request.form["item"]
    bus = request.form["bus"]
    details = request.form["details"]

    reported_by = session["name"]

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO lost_items(passenger_name, contact, item, bus_no, details, reported_by, date_time) "
        "VALUES (%s,%s,%s,%s,%s,%s,NOW())",
        (passenger, contact, item, bus, details, reported_by))
    db.commit()
    return redirect("/lost")


# ================= TRIPS (ADMIN + MANAGER) =================
@app.route("/trips")
def trips():
    if not allow("admin","manager"):
        return "Access Denied ❌"

    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM trips ORDER BY id DESC")
    data = cursor.fetchall()

    cursor.execute("SELECT bus_no FROM buses")
    buses = cursor.fetchall()

    return render_template("trips.html", data=data, buses=buses)



@app.route("/save_trip", methods=["POST"])
def save_trip():
    if not allow("admin", "manager"):
        return "Access Denied ❌"

    bus = request.form["bus"]
    route = request.form["route"]
    driver = request.form["driver"]
    conductor = request.form["conductor"]
    passengers = request.form["passengers"]
    collection = request.form["collection"]

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO trips(bus_no, route, driver, conductor, passengers, collection, date_time) "
        "VALUES (%s,%s,%s,%s,%s,%s,NOW())",
        (bus, route, driver, conductor, passengers, collection))
    db.commit()
    return redirect("/trips")


# ================= PERFORMANCE (ADMIN + MANAGER) =================
@app.route("/performance", methods=["GET", "POST"])
def performance():
    if not allow("admin", "manager"):
        return "Access Denied ❌"

    data = None
    if request.method == "POST":
        emp_id = request.form["emp_id"]
        cursor = db.cursor()

        cursor.execute("SELECT name, role FROM employees WHERE id=%s", (emp_id,))
        emp = cursor.fetchone()
        if not emp:
            return "Employee Not Found"

        name, role = emp
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE employee_id=%s", (emp_id,))
        attendance = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*), IFNULL(SUM(passengers),0), IFNULL(SUM(collection),0) "
            "FROM trips WHERE driver=%s", (name,))
        trip_data = cursor.fetchone()

        data = {
            "emp_id": emp_id,
            "name": name,
            "role": role,
            "attendance": trip_data[0],
            "trips": trip_data[0],
            "passengers": trip_data[1],
            "collection": trip_data[2]
        }

    return render_template("performance.html", data=data)


@app.route("/performance_pdf", methods=["POST"])
def performance_pdf():
    if not allow("admin", "manager"):
        return "Access Denied ❌"

    emp_id = request.form["emp_id"]
    cursor = db.cursor()

    cursor.execute("SELECT name, role FROM employees WHERE id=%s", (emp_id,))
    emp = cursor.fetchone()
    name, role = emp

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE employee_id=%s", (emp_id,))
    attendance = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*), IFNULL(SUM(passengers),0), IFNULL(SUM(collection),0) "
        "FROM trips WHERE driver=%s", (name,))
    trip_data = cursor.fetchone()

    trips, passengers, collection = trip_data

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica", 18)
    pdf.drawString(120, 800, "Transport System Performance Report")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Employee ID : {emp_id}")
    pdf.drawString(50, 740, f"Name : {name}")
    pdf.drawString(50, 720, f"Role : {role}")
    pdf.drawString(50, 680, f"Attendance : {attendance}")
    pdf.drawString(50, 660, f"Trips : {trips}")
    pdf.drawString(50, 640, f"Passengers : {passengers}")
    pdf.drawString(50, 620, f"Collection ₹ : {collection}")
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f"{name}_performance.pdf",
                     mimetype="application/pdf")


# ================= ANALYTICS (ADMIN ONLY) =================
@app.route("/analytics")
def analytics():
    if not allow("admin"):
        return "Access Denied ❌"

    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM employees")
    total_employees = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trips")
    total_trips = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance")
    total_attendance = cursor.fetchone()[0]

    cursor.execute("SELECT IFNULL(SUM(collection),0) FROM trips")
    total_collection = cursor.fetchone()[0]

    cursor.execute("SELECT IFNULL(SUM(diesel_used),0) FROM fuel_collection")
    total_diesel = cursor.fetchone()[0]

    cursor.execute("SELECT bus_no, SUM(collection) FROM trips GROUP BY bus_no")
    trip_data = cursor.fetchall()

    bus_labels = [row[0] for row in trip_data]
    bus_collection = [int(row[1]) for row in trip_data]

    cursor.execute("SELECT bus_no, SUM(diesel_used) FROM fuel_collection GROUP BY bus_no")
    fuel_data = cursor.fetchall()

    bus_diesel = [int(row[1]) for row in fuel_data]

    return render_template(
        "admin_dashboard.html",
        total_employees=total_employees,
        total_trips=total_trips,
        total_attendance=total_attendance,
        total_collection=total_collection,
        total_diesel=total_diesel,
        bus_labels=bus_labels,
        bus_collection=bus_collection,
        bus_diesel=bus_diesel
    )


# ================= COMPLAINTS =================
@app.route("/complaint")
def complaint():
    if "user_id" not in session:
        return redirect("/login_page")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM complaints ORDER BY id DESC")
    data = cursor.fetchall()

    return render_template("complaint.html", data=data)
@app.route("/update_complaint/<int:id>/<status>")
def update_complaint(id, status):
    if not allow("admin","manager"):
        return "Access Denied ❌"

    cursor = db.cursor()
    cursor.execute(
        "UPDATE complaints SET status=%s WHERE id=%s",
        (status, id)
    )
    db.commit()

    return redirect("/complaint")


@app.route("/save_complaint", methods=["POST"])
def save_complaint():
    emp_id = request.form["emp_id"]
    name = request.form["name"]
    issue = request.form["issue"]
    pressure = request.form["pressure"]
    against = request.form["against"]

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO complaints(employee_id, name, issue, pressure_level, against_person, date_time) "
        "VALUES (%s,%s,%s,%s,%s,NOW())",
        (emp_id, name, issue, pressure, against))
    db.commit()
    return redirect("/complaint")
from datetime import date, timedelta

@app.route("/buses")
def buses():
    if "user_id" not in session:
        return redirect("/login_page")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM buses ORDER BY id DESC")
    buses = cursor.fetchall()

    today = date.today()
    week_later = today + timedelta(days=7)

    return render_template(
        "buses.html",
        buses=buses,
        today=today,
        week_later=week_later
    )


@app.route("/add_bus", methods=["POST"])
def add_bus():
    if not allow("admin","manager"):
        return "Access Denied ❌"

    bus_no = request.form["bus_no"]
    bus_type = request.form["type"]
    depot = request.form["depot"]
    fitness = request.form["fitness"]
    insurance = request.form["insurance"]
    last = request.form["last"]
    nexts = request.form["next"]
    status = request.form["status"]

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO buses(bus_no,type,depot,fitness_expiry,insurance_expiry,last_service,next_service,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (bus_no,bus_type,depot,fitness,insurance,last,nexts,status)
    )
    db.commit()

    return redirect("/buses")
@app.route("/delete_bus/<int:id>")
def delete_bus(id):
    if not allow("admin","manager"):
        return "Access Denied ❌"

    cursor = db.cursor()
    cursor.execute("DELETE FROM buses WHERE id=%s", (id,))
    db.commit()

    return redirect("/buses")
@app.route("/edit_bus/<int:id>")
def edit_bus(id):
    if not allow("admin","manager"):
        return "Access Denied ❌"

    cursor = db.cursor()
    cursor.execute("SELECT * FROM buses WHERE id=%s", (id,))
    bus = cursor.fetchone()

    return render_template("edit_bus.html", bus=bus)
@app.route("/update_bus/<int:id>", methods=["POST"])
def update_bus(id):
    if not allow("admin","manager"):
        return "Access Denied ❌"

    bus_no = request.form["bus_no"]
    bus_type = request.form["type"]
    depot = request.form["depot"]
    fitness = request.form["fitness"]
    insurance = request.form["insurance"]
    last = request.form["last"]
    nexts = request.form["next"]
    status = request.form["status"]

    cursor = db.cursor()
    cursor.execute("""
        UPDATE buses 
        SET bus_no=%s, type=%s, depot=%s, fitness_expiry=%s, insurance_expiry=%s,
        last_service=%s, next_service=%s, status=%s
        WHERE id=%s
    """,
        (bus_no,bus_type,depot,fitness,insurance,last,nexts,status,id)
    )
    db.commit()

    return redirect("/buses")
@app.route("/ai_support", methods=["GET", "POST"])
def ai_support():
    if "user_id" not in session:
        return redirect("/login_page")

    if "ai_chat" not in session:
        session["ai_chat"] = []

    answer = None

    if request.method == "POST":
        question = request.form["question"].strip()

        # store user message
        session["ai_chat"].append(("user", question))

        # generate AI reply
        answer = ai_reply(session["ai_chat"])

        # store AI message
        session["ai_chat"].append(("ai", answer))

        session.modified = True

    return render_template(
        "ai_support.html",
        chat=session["ai_chat"]
    )
def ai_reply(chat):
    last_user_msg = chat[-1][1].lower()

    # stress / pressure
    if "stress" in last_user_msg or "pressure" in last_user_msg:
        return (
            "I understand this can be difficult.\n"
            "Try taking short breaks, maintain proper sleep, and talk to someone you trust.\n"
            "Avoid making decisions when emotionally exhausted."
        )

    # kmpl
    if "kmpl" in last_user_msg or "mileage" in last_user_msg:
        return (
            "To improve KMPL:\n"
            "- Maintain steady speed\n"
            "- Avoid harsh braking\n"
            "- Reduce unnecessary idling\n"
            "- Ensure proper tyre pressure"
        )

    # night shift
    if "night" in last_user_msg:
        return (
            "During night shifts:\n"
            "- Stay hydrated\n"
            "- Take light meals\n"
            "- Stop driving if drowsy\n"
            "- Inform supervisor if unwell"
        )

    # default fallback
    return (
        "I can help with stress, work pressure, safety, KMPL, and shift guidance.\n"
        "Please ask a transport-related question."
    )
@app.route("/feedback")
def feedback():
    if not allow("employee"):
        return "Access Denied ❌"

    return render_template("feedback.html")
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    if not allow("employee"):
        return "Access Denied ❌"

    pressure = request.form["pressure"]
    manager_pressure = request.form["manager_pressure"]
    comments = request.form["comments"]

    emp_id = session["user_id"]
    name = session["name"]
    role = session["role"]

    cursor = db.cursor()
    cursor.execute(
        "SELECT depot FROM employees WHERE id=%s",
        (emp_id,)
    )
    depot = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO employee_feedback
        (employee_id, name, role, depot, pressure_level, manager_pressure, comments)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (emp_id, name, role, depot, pressure, manager_pressure, comments))

    db.commit()
    return redirect("/dashboard")
@app.route("/risk_dashboard")
def risk_dashboard():
    if not allow("admin"):
        return "Access Denied ❌"

    cursor = db.cursor()
    cursor.execute("""
        SELECT depot,
               COUNT(*) AS total_reports,
               AVG(pressure_level) AS avg_pressure,
               SUM(manager_pressure='Yes') AS forced_cases
        FROM employee_feedback
        GROUP BY depot
    """)
    data = cursor.fetchall()

    return render_template("risk_dashboard.html", data=data)



# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
