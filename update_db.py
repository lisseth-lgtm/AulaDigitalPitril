import sqlite3

conn = sqlite3.connect('data/escuela.db')
c = conn.cursor()

# Agregar la columna estado si no existe
try:
    c.execute("ALTER TABLE usuarios ADD COLUMN estado TEXT DEFAULT 'pendiente'")
    print("✅ Columna 'estado' agregada correctamente.")
except sqlite3.OperationalError:
    print("⚠️ La columna 'estado' ya existe. No se hicieron cambios.")

conn.commit()
conn.close()
