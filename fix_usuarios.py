import sqlite3

conn = sqlite3.connect('data/escuela.db')
c = conn.cursor()

# Verificar si la columna 'clave' ya existe
c.execute("PRAGMA table_info(usuarios)")
columnas = [col[1] for col in c.fetchall()]

if 'clave' not in columnas:
    print("🔧 Agregando columna 'clave' a la tabla usuarios...")
    c.execute("ALTER TABLE usuarios ADD COLUMN clave TEXT DEFAULT ''")
    conn.commit()
    print("✅ Columna 'clave' agregada correctamente.")
else:
    print("✅ La columna 'clave' ya existe, no se realizaron cambios.")

conn.close()
