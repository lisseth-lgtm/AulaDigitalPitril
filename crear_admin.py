import sqlite3

# Conexión a la base de datos
conn = sqlite3.connect('data/escuela.db')
c = conn.cursor()

# Crear usuario administrador si no existe
try:
    c.execute("INSERT INTO usuarios (nombre, usuario, clave, tipo, estado) VALUES (?, ?, ?, ?, ?)",
              ('Administrador', 'admin', 'admin123', 'admin', 'aprobado'))
    conn.commit()
    print("✅ Usuario administrador creado correctamente:")
    print("   Usuario: admin")
    print("   Clave: admin123")
except sqlite3.IntegrityError:
    print("⚠️ Ya existe un usuario con ese nombre de usuario.")

conn.close()
