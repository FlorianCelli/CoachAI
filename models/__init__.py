from models.user import db, User
from models.conversation import Conversation, Message
from models.fitness_plan import WorkoutPlan, NutritionPlan, WorkoutLog

def init_app(app):
    """Initialize database with app"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
