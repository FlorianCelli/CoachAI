# create_weight_table_direct.py
import sqlite3
import os

# Chemin vers votre base de données SQLite
# Remplacez par le chemin correct de votre base de données
DB_PATH = 'fitness_coach.db'  # Ajustez si nécessaire avec le chemin complet

# Vérifier si le fichier existe
if not os.path.exists(DB_PATH):
    print(f"Erreur: Le fichier de base de données '{DB_PATH}' n'existe pas")
    exit(1)

try:
    # Connexion à la base de données
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si la table existe déjà
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weight_entries'")
    if cursor.fetchone() is None:
        # Créer la table weight_entries
        cursor.execute('''
        CREATE TABLE weight_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            weight FLOAT NOT NULL,
            date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        print("Table 'weight_entries' created successfully")
    else:
        print("Table 'weight_entries' already exists")
    
    # Finaliser la transaction
    conn.commit()
    
except sqlite3.Error as e:
    print(f"SQLite error: {e}")
finally:
    # Fermer la connexion
    if conn:
        conn.close()
