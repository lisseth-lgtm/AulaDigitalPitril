import os
import sqlite3

# Crear carpeta 'data' si no existe
if not os.path.exists('data'):
    os.makedirs('data')

def init_db():
    conn = sqlite3.connect('data/escuela.db')
    c = conn.cursor()

    # Crear tabla de usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        usuario TEXT UNIQUE,
        contrasena TEXT,
        tipo TEXT
    )''')

    # Crear tabla de asignaturas
    c.execute('''CREATE TABLE IF NOT EXISTS asignaturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE
    )''')

    # Crear tabla de horarios
    c.execute('''CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profesor TEXT,
        curso TEXT,
        dia TEXT,
        bloque TEXT,
        asignatura TEXT
    )''')

    # Insertar asignaturas base
    asignaturas_base = [
        ('Lenguaje y Comunicación',),
        ('Matemáticas',),
        ('Ciencias Naturales',),
        ('Historia, Geografía y Ciencias Sociales',),
        ('Inglés',),
        ('Religión',),
        ('Educación Física',),
        ('Artes Visuales',),
        ('Música',)
    ]
    c.executemany("INSERT OR IGNORE INTO asignaturas (nombre) VALUES (?)", asignaturas_base)

    # Crear usuario administrador por defecto
    c.execute("SELECT * FROM usuarios WHERE tipo='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (nombre, usuario, contrasena, tipo) VALUES (?, ?, ?, ?)",
                  ('Administrador', 'admin', 'EP1180', 'admin'))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Base de datos 'escuela.db' creada correctamente en la carpeta /data")
