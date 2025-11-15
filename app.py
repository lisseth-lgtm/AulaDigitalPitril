from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)
app.secret_key = "EP1180"

DB_PATH = "data/escuela.db"

# ----------------- Helpers -----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = get_db_connection()
    c = conn.cursor()

    # usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        usuario TEXT UNIQUE NOT NULL,
        clave TEXT NOT NULL,
        tipo TEXT NOT NULL,
        estado TEXT DEFAULT 'pendiente'
    )''')

    # alumnos
    c.execute('''CREATE TABLE IF NOT EXISTS alumnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        curso TEXT NOT NULL,
        estado TEXT DEFAULT 'activo'
    )''')

    # asistencia
    c.execute('''CREATE TABLE IF NOT EXISTS asistencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        fecha TEXT,
        estado TEXT,
        FOREIGN KEY(alumno_id) REFERENCES alumnos(id)
    )''')

    # calificaciones
    c.execute('''CREATE TABLE IF NOT EXISTS calificaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        asignatura TEXT,
        nota REAL,
        fecha TEXT,
        FOREIGN KEY(alumno_id) REFERENCES alumnos(id)
    )''')

    # asignaturas
    c.execute('''CREATE TABLE IF NOT EXISTS asignaturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL
    )''')

    # horarios
    c.execute('''CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profesor TEXT,
        curso TEXT,
        dia TEXT,
        bloque TEXT,
        asignatura TEXT
    )''')

    # leccionario
    c.execute('''CREATE TABLE IF NOT EXISTS leccionario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso TEXT,
        asignatura TEXT,
        descripcion TEXT,
        fecha TEXT
    )''')

    # Crear admin por defecto si no existe
    c.execute("SELECT * FROM usuarios WHERE tipo='admin'")
    if not c.fetchone():
        hashed = generate_password_hash("EP1180")
        c.execute("INSERT INTO usuarios (nombre, usuario, clave, tipo, estado) VALUES (?, ?, ?, ?, ?)",
                  ('Administrador', 'admin', hashed, 'admin', 'aprobado'))

    # Insertar asignaturas ejemplo si no hay
    c.execute("SELECT COUNT(*) as cnt FROM asignaturas")
    if c.fetchone()['cnt'] == 0:
        asigns = ['Matemáticas', 'Lenguaje', 'Ciencias', 'Historia', 'Inglés', 'Religión', 'Ed. Física']
        for a in asigns:
            try:
                c.execute("INSERT INTO asignaturas (nombre) VALUES (?)", (a,))
            except:
                pass

    conn.commit()
    conn.close()

# ----------------- RUTAS AUTH -----------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user['clave'], clave):
            if user['estado'] == 'pendiente':
                flash('Tu cuenta está pendiente de aprobación.', 'warning')
                return redirect(url_for('login'))
            if user['estado'] == 'rechazado':
                flash('Tu cuenta fue rechazada.', 'danger')
                return redirect(url_for('login'))
            session['user_id'] = user['id']
            session['usuario'] = user['usuario']
            session['tipo'] = user['tipo']
            flash(f'Bienvenido {user["nombre"]}', 'success')
            return redirect(url_for('panel'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('login'))

# ----------------- REGISTRO -----------------
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        clave = request.form['clave']
        hashed = generate_password_hash(clave)
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO usuarios (nombre, usuario, clave, tipo, estado) VALUES (?, ?, ?, ?, ?)",
                      (nombre, usuario, hashed, 'profesor', 'pendiente'))
            conn.commit()
            flash('Cuenta registrada. Espera aprobación del administrador.', 'info')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario ya existe.', 'danger')
        finally:
            conn.close()
    return render_template('registro.html')

# ----------------- PANEL -----------------
@app.route('/panel')
def panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT nombre FROM asignaturas")
    asignaturas = [r['nombre'] for r in c.fetchall()]
    c.execute("SELECT * FROM horarios")
    horarios = c.fetchall()
    conn.close()
    return render_template('panel.html', usuario=session.get('usuario'), asignaturas=asignaturas, horarios=horarios)

@app.route('/guardar_horario', methods=['POST'])
def guardar_horario():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    profesor = request.form.get('profesor')
    curso = request.form.get('curso')
    dia = request.form.get('dia')
    bloque = request.form.get('bloque')
    asignatura = request.form.get('asignatura')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO horarios (profesor, curso, dia, bloque, asignatura) VALUES (?, ?, ?, ?, ?)",
              (profesor, curso, dia, bloque, asignatura))
    conn.commit()
    conn.close()
    flash('Horario guardado correctamente', 'success')
    return redirect(url_for('panel'))

# ----------------- ADMIN USUARIOS -----------------
@app.route('/admin/usuarios')
def admin_usuarios():
    if session.get('tipo') != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('login'))
    conn = get_db_connection()
    usuarios = conn.execute("SELECT * FROM usuarios WHERE tipo='profesor'").fetchall()
    conn.close()
    return render_template('admin_usuarios.html', usuarios=usuarios)

@app.route('/admin/actualizar_estado/<int:id>/<estado>')
def actualizar_estado(id, estado):
    if session.get('tipo') != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute("UPDATE usuarios SET estado=? WHERE id=?", (estado, id))
    conn.commit()
    conn.close()
    flash('Estado actualizado', 'success')
    return redirect(url_for('admin_usuarios'))

# ----------------- ALUMNOS CRUD -----------------
@app.route('/estudiantes')
def estudiantes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    alumnos = conn.execute("SELECT * FROM alumnos").fetchall()
    conn.close()
    return render_template('estudiantes.html', alumnos=alumnos)

@app.route('/estudiantes/crear', methods=['GET', 'POST'])
def crear_estudiante():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        curso = request.form['curso']
        conn = get_db_connection()
        conn.execute("INSERT INTO alumnos (nombre, curso) VALUES (?, ?)", (nombre, curso))
        conn.commit()
        conn.close()
        flash('Alumno creado', 'success')
        return redirect(url_for('estudiantes'))
    return render_template('estudiante_form.html')

@app.route('/estudiantes/editar/<int:id>', methods=['GET', 'POST'])
def editar_estudiante(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if request.method == 'POST':
        nombre = request.form['nombre']
        curso = request.form['curso']
        conn.execute("UPDATE alumnos SET nombre=?, curso=? WHERE id=?", (nombre, curso, id))
        conn.commit()
        conn.close()
        flash('Alumno actualizado', 'success')
        return redirect(url_for('estudiantes'))
    alumno = conn.execute("SELECT * FROM alumnos WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('estudiante_form.html', alumno=alumno)

@app.route('/estudiantes/eliminar/<int:id>')
def eliminar_estudiante(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM alumnos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash('Alumno eliminado', 'info')
    return redirect(url_for('estudiantes'))

# ----------------- ASISTENCIA -----------------
@app.route('/asistencia', methods=['GET', 'POST'])
def asistencia():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursos = [r['curso'] for r in conn.execute("SELECT DISTINCT curso FROM alumnos").fetchall()]
    alumnos = []
    selected_curso = None
    if request.method == 'POST' and 'curso' in request.form and 'fecha' not in request.form:
        selected_curso = request.form['curso']
        alumnos = conn.execute("SELECT * FROM alumnos WHERE curso=?", (selected_curso,)).fetchall()
    elif request.method == 'POST' and 'fecha' in request.form:
        # guardar asistencia
        fecha = request.form['fecha']
        for key, value in request.form.items():
            if key.startswith('estado_'):
                alumno_id = int(key.split('_')[1])
                estado = value
                conn.execute("INSERT INTO asistencia (alumno_id, fecha, estado) VALUES (?, ?, ?)",
                             (alumno_id, fecha, estado))
        conn.commit()
        flash('Asistencia registrada', 'success')
        conn.close()
        return redirect(url_for('asistencia'))
    conn.close()
    return render_template('asistencia.html', cursos=cursos, alumnos=alumnos, selected_curso=selected_curso)

@app.route('/asistencia/historial/<int:alumno_id>')
def asistencia_historial(alumno_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    rows = conn.execute("SELECT fecha, estado FROM asistencia WHERE alumno_id=? ORDER BY fecha DESC", (alumno_id,)).fetchall()
    alumno = conn.execute("SELECT * FROM alumnos WHERE id=?", (alumno_id,)).fetchone()
    conn.close()
    return render_template('asistencia_historial.html', rows=rows, alumno=alumno)

# ----------------- CALIFICACIONES -----------------
@app.route('/calificaciones', methods=['GET', 'POST'])
def calificaciones():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    alumnos = conn.execute("SELECT * FROM alumnos").fetchall()
    asignaturas = conn.execute("SELECT nombre FROM asignaturas").fetchall()
    if request.method == 'POST':
        alumno_id = request.form['alumno_id']
        asignatura = request.form['asignatura']
        nota = request.form['nota']
        fecha = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO calificaciones (alumno_id, asignatura, nota, fecha) VALUES (?, ?, ?, ?)",
                     (alumno_id, asignatura, nota, fecha))
        conn.commit()
        flash('Nota registrada', 'success')
        conn.close()
        return redirect(url_for('calificaciones'))
    conn.close()
    return render_template('calificaciones.html', alumnos=alumnos, asignaturas=asignaturas)

@app.route('/calificaciones/boleta/<int:alumno_id>')
def boleta(alumno_id):
    if 'user_id' not in session():
        return redirect(url_for('login'))
    conn = get_db_connection()
    alumno = conn.execute("SELECT * FROM alumnos WHERE id=?", (alumno_id,)).fetchone()
    notas = conn.execute("SELECT asignatura, nota FROM calificaciones WHERE alumno_id=?", (alumno_id,)).fetchall()
    conn.close()
    return render_template('boleta.html', alumno=alumno, notas=notas)

# ----------------- INFORMES PDF (simple) -----------------
@app.route('/informes/estudiante/<int:alumno_id>/pdf')
def informe_pdf(alumno_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    alumno = conn.execute("SELECT * FROM alumnos WHERE id=?", (alumno_id,)).fetchone()
    notas = conn.execute("SELECT asignatura, nota, fecha FROM calificaciones WHERE alumno_id=?", (alumno_id,)).fetchall()
    asistencias = conn.execute("SELECT fecha, estado FROM asistencia WHERE alumno_id=?", (alumno_id,)).fetchall()
    conn.close()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 750, f"Informe - {alumno['nombre']}")
    p.setFont("Helvetica", 11)
    y = 720
    p.drawString(50, y, "Calificaciones:")
    y -= 20
    for n in notas:
        p.drawString(60, y, f"{n['asignatura']}: {n['nota']}  ({n['fecha']})")
        y -= 16
    y -= 10
    p.drawString(50, y, "Asistencias:")
    y -= 20
    for a in asistencias:
        p.drawString(60, y, f"{a['fecha']}: {a['estado']}")
        y -= 16
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"informe_{alumno['nombre']}.pdf", mimetype='application/pdf')

# ----------------- INICIO -----------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
