from datetime import datetime
from . import db                              # ← objet partagé

class WeightEntry(db.Model):
    __tablename__ = 'weight_entries'

    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    weight   = db.Column(db.Float, nullable=False)
    date     = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WeightEntry {self.weight} kg on {self.date:%Y-%m-%d}>'

