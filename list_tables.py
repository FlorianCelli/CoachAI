import sqlite3

conn = sqlite3.connect('fitness_coach.db')
cursor = conn.cursor()

# Obtenir la liste des tables existantes
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables dans la base de données:")
for table in tables:
    print(table[0])

conn.close()
