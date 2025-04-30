import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-me-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///fitness_coach.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration Amazon Bedrock
    AWS_REGION = os.environ.get('AWS_REGION') or 'us-east-1'
    
    # ID du modèle Claude 3.7 Sonnet
    BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID') or 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
