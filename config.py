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
    
    # Configuration pour les images
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite la taille des uploads à 16 Mo
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Configuration pour le redimensionnement des images
    MAX_IMAGE_WIDTH = 1200
    MAX_IMAGE_HEIGHT = 1200
    IMAGE_QUALITY = 85  # Pour les images JPEG
