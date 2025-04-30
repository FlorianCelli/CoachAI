from datetime import datetime
from models.user import db

class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    objective = db.Column(db.String(100))
    days_per_week = db.Column(db.Integer)
    duration_minutes = db.Column(db.Integer)
    difficulty_level = db.Column(db.String(20))
    
    plan_content = db.Column(db.Text, nullable=False)  # Le plan complet généré par Claude
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WorkoutPlan {self.id}: {self.title}>'

class NutritionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    objective = db.Column(db.String(100))
    daily_calories = db.Column(db.Integer)
    protein_percentage = db.Column(db.Integer)
    carbs_percentage = db.Column(db.Integer)
    fat_percentage = db.Column(db.Integer)
    
    plan_content = db.Column(db.Text, nullable=False)  # Le plan complet généré par Claude
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NutritionPlan {self.id}: {self.title}>'

class WorkoutLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    workout_plan_id = db.Column(db.Integer, db.ForeignKey('workout_plan.id'), nullable=True)
    
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    duration_minutes = db.Column(db.Integer)
    perceived_effort = db.Column(db.Integer)  # 1-10
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WorkoutLog {self.id}: {self.date}>'
