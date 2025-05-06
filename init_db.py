from app import app, db
from sqlalchemy import inspect, text
from models import User, Conversation, Message, WorkoutPlan, NutritionPlan, WorkoutLog

# Initialiser la base de données avec toutes les tables nécessaires
with app.app_context():
    print("Création des tables dans la base de données...")
    db.create_all()
    print("Base de données initialisée avec succès!")
    
    # Vérifier que les tables existent
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables créées: {tables}")
    
    # Si la table user existe, vérifier si la colonne coach existe
    if 'user' in tables:
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'coach' not in columns:
            try:
                print("Ajout de la colonne 'coach' à la table 'user'")
                # Utiliser text() pour déclarer explicitement la requête SQL
                sql = text('ALTER TABLE user ADD COLUMN coach VARCHAR(20)')
                db.session.execute(sql)
                db.session.commit()
                print("Colonne 'coach' ajoutée avec succès à la table 'user'")
            except Exception as e:
                db.session.rollback()
                print(f"Erreur lors de l'ajout de la colonne: {e}")
        else:
            print("La colonne 'coach' existe déjà dans la table 'user'")
    else:
        print("La table 'user' n'existe pas dans la base de données")
