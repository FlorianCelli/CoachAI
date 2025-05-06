# Script pour ajouter la colonne coach à la table user
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

with app.app_context():
    try:
        # Vérifier si la colonne existe déjà
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'coach' not in columns:
            # Ajouter la colonne coach à la table user
            db.engine.execute('ALTER TABLE user ADD COLUMN coach VARCHAR(20)')
            print("Colonne 'coach' ajoutée avec succès à la table 'user'")
        else:
            print("La colonne 'coach' existe déjà dans la table 'user'")
            
    except Exception as e:
        print(f"Erreur lors de la mise à jour de la base de données: {e}")
