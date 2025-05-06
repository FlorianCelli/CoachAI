from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Ajout de l'attribut coach
    coach = db.Column(db.String(20))  # 'maxence' ou 'sofia'
    
    # Informations de profil fitness
    age = db.Column(db.Integer)
    height = db.Column(db.Float)  # en cm
    weight = db.Column(db.Float)  # en kg
    gender = db.Column(db.String(20))
    fitness_level = db.Column(db.String(20))  # débutant, intermédiaire, avancé
    fitness_goal = db.Column(db.String(100))
    activity_level = db.Column(db.String(20))  # sédentaire, modéré, actif, très actif
    equipment_access = db.Column(db.String(100))
    medical_conditions = db.Column(db.Text)
    dietary_restrictions = db.Column(db.Text)
    
    # Relations
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic')
    workout_plans = db.relationship('WorkoutPlan', backref='user', lazy='dynamic')
    nutrition_plans = db.relationship('NutritionPlan', backref='user', lazy='dynamic')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
