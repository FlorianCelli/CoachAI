import re
import json
from bs4 import BeautifulSoup
from flask import Markup

class ResponseFormatter:
    """
    Cette classe gère la détection et le formatage des différents types de contenus
    dans les réponses de l'IA pour garantir un affichage correct et attrayant.
    """
    
    @staticmethod
    def detect_content_type(text):
        """
        Détecte le type de contenu dans le texte pour déterminer le formatage approprié.
        
        Args:
            text (str): Texte de la réponse de l'IA
            
        Returns:
            str: Type de contenu détecté ('program', 'nutrition_plan', 'conversation', 'html', 'normal')
        """
        # Détection de programme d'entraînement
        if re.search(r'<h[1-3]>\s*Programme d\'entraînement|JOUR \d+|Circuit HIIT|Échauffement|Récupération', text, re.IGNORECASE):
            return 'program'
        
        # Détection de plan nutritionnel
        if re.search(r'Menu pour la semaine|Plan nutritionnel|Déjeuner:|Dîner:|Petit-déjeuner', text, re.IGNORECASE):
            return 'nutrition_plan'
            
        # Détection de contenu HTML (si déjà en HTML)
        if re.search(r'<html|<body|<div|<p>|<h[1-6]>', text):
            return 'html'
            
        # Par défaut: conversation normale
        return 'normal'
    
    @staticmethod
    def format_program(text):
        """
        Formate un programme d'entraînement pour un affichage attrayant.
        """
        # Gestion des titres et sections
        text = re.sub(r'<h1>(.*?)<\/h1>', r'<h1 class="program-title">\1</h1>', text)
        text = re.sub(r'<h2>(.*?)<\/h2>', r'<h2 class="program-section">\1</h2>', text)
        text = re.sub(r'<h3>(.*?)<\/h3>', r'<h3 class="program-day">\1</h3>', text)
        
        # Gestion des exercices
        text = re.sub(r'(.*?)(\d+)\s*séries de\s*(\d+)', 
                     r'<div class="exercise"><span class="exercise-name">\1</span><span class="exercise-sets">\2 séries de \3</span></div>', 
                     text)
        
        # Mise en évidence des durées
        text = re.sub(r'(\(\d+\s*min\))', r'<span class="duration">\1</span>', text)
        
        # Création d'une structure HTML complète avec CSS intégré
        html = f"""
        <div class="program-container">
            <style>
                .program-container {{
                    font-family: 'Roboto', sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .program-title {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                    font-size: 24px;
                }}
                .program-section {{
                    background: #3498db;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 5px;
                    margin-top: 25px;
                    font-size: 20px;
                }}
                .program-day {{
                    background: #2980b9;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 5px;
                    margin-top: 20px;
                    font-size: 18px;
                }}
                .exercise {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 15px;
                    margin: 5px 0;
                    background: white;
                    border-left: 4px solid #3498db;
                    border-radius: 0 5px 5px 0;
                }}
                .exercise-name {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .exercise-sets {{
                    color: #7f8c8d;
                }}
                .duration {{
                    background: #e74c3c;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 14px;
                }}
                p {{
                    line-height: 1.6;
                    color: #34495e;
                }}
            </style>
            {text}
        </div>
        """
        return html
    
    @staticmethod
    def format_nutrition_plan(text):
        """
        Formate un plan nutritionnel pour un affichage attrayant.
        """
        # Extraire les jours de la semaine
        days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        meal_types = ['Petit-déjeuner', 'Déjeuner', 'Dîner', 'Collation']
        
        # Convertir le texte en HTML structuré
        html_parts = ['<div class="nutrition-plan">']
        
        current_day = None
        
        # Parcourir les lignes pour structurer le contenu
        for line in text.split('\n'):
            # Détecter un jour de la semaine
            day_match = None
            for day in days:
                if re.search(f"{day}\\s*:", line, re.IGNORECASE):
                    day_match = day
                    break
            
            if day_match:
                if current_day:
                    html_parts.append('</div>')  # Fermer le jour précédent
                html_parts.append(f'<div class="day-plan"><h3 class="day-header">{day_match}</h3>')
                current_day = day_match
                continue
            
            # Détecter un type de repas
            meal_match = None
            for meal in meal_types:
                if re.search(f"{meal}\\s*:", line, re.IGNORECASE):
                    meal_match = meal
                    break
            
            if meal_match and current_day:
                # Extraire la description du repas
                meal_content = re.sub(f"{meal_match}\\s*:", '', line, flags=re.IGNORECASE).strip()
                html_parts.append(f'<div class="meal"><div class="meal-type">{meal_match}</div><div class="meal-content">{meal_content}</div></div>')
        
        if current_day:  # Fermer le dernier jour
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        # Ajouter le CSS pour le style
        html = f"""
        <div class="nutrition-container">
            <style>
                .nutrition-container {{
                    font-family: 'Roboto', sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .nutrition-plan {{
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }}
                .day-plan {{
                    background: white;
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: 0 1px 5px rgba(0,0,0,0.05);
                }}
                .day-header {{
                    background: #27ae60;
                    color: white;
                    margin: -15px -15px 15px -15px;
                    padding: 10px 15px;
                    border-radius: 8px 8px 0 0;
                    font-size: 18px;
                }}
                .meal {{
                    display: flex;
                    margin-bottom: 12px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 12px;
                }}
                .meal:last-child {{
                    border-bottom: none;
                    margin-bottom: 0;
                    padding-bottom: 0;
                }}
                .meal-type {{
                    min-width: 120px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .meal-content {{
                    flex: 1;
                    color: #34495e;
                    line-height: 1.5;
                }}
                .suggestions {{
                    background: #f0f7ff;
                    border-left: 4px solid #3498db;
                    padding: 12px;
                    margin-top: 15px;
                    border-radius: 0 5px 5px 0;
                }}
                .suggestions h4 {{
                    margin-top: 0;
                    color: #3498db;
                }}
            </style>
            {' '.join(html_parts)}
        </div>
        """
        return html
    
    @staticmethod
    def ensure_valid_html(html_content):
        """
        S'assure que le contenu HTML est valide et complet.
        Corrige les balises non fermées, etc.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        return str(soup)
    
    @staticmethod
    def format_response(text):
        """
        Point d'entrée principal - détecte et formate le contenu approprié.
        
        Args:
            text (str): Texte brut de la réponse de l'IA
            
        Returns:
            Markup: Contenu formaté sécurisé pour l'affichage HTML
        """
        content_type = ResponseFormatter.detect_content_type(text)
        
        if content_type == 'program':
            formatted = ResponseFormatter.format_program(text)
        elif content_type == 'nutrition_plan':
            formatted = ResponseFormatter.format_nutrition_plan(text)
        elif content_type == 'html':
            # Si c'est déjà du HTML, assurer qu'il est valide
            formatted = ResponseFormatter.ensure_valid_html(text)
        else:
            # Texte normal de conversation - formater les paragraphes simplement
            formatted = f"<div class='conversation-text'>{text}</div>"
        
        # Renvoyer sous forme de Markup pour que Flask ne l'échappe pas
        return Markup(formatted)
