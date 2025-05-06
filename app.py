from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
import markdown
import re

from werkzeug.utils import secure_filename
import os
from io import BytesIO
from PIL import Image
import base64

from models import init_app, User, Conversation, Message, WorkoutPlan, NutritionPlan, WorkoutLog
from utils.bedrock_client import BedrockClient
from utils.fitness_prompts import (
    SYSTEM_PROMPT, INITIAL_ASSESSMENT_PROMPT, WORKOUT_PLAN_PROMPT,
    NUTRITION_PLAN_PROMPT, PROGRESS_ASSESSMENT_PROMPT, MOTIVATION_PROMPT,
    EXERCISE_FORM_PROMPT
)
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialisation des extensions
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

# Initialisation de la base de données
init_app(app)

# Initialisation du client Bedrock
bedrock_client = BedrockClient(app.config['AWS_REGION'], app.config['BEDROCK_MODEL_ID'])

# Définir les extensions d'images autorisées
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configuration du système de login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Filtre pour le Markdown
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text)

# Context processor pour les variables globales
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Fonction pour personnaliser le prompt système avec les infos du profil
def get_customized_system_prompt():
    customized_system_prompt = SYSTEM_PROMPT

    # Ajouter des instructions de formatage et de structure
    formatting_instructions = """
Pour toutes tes réponses, suis ces règles de formatage et de communication :
1. Utilise des paragraphes courts et bien espacés pour une meilleure lisibilité
2. Pose maximum 1-2 questions à la fois, jamais plus
3. Utilise des émojis avec parcimonie pour ajouter de la chaleur à la conversation
4. Structure tes messages avec des sauts de ligne clairs entre les sections
5. Préfère un ton conversationnel, naturel et bienveillant
6. Évite les blocs de texte trop denses ou les listes de questions
7. N'utilise PAS de symboles comme ** ou ## pour la mise en forme - ils ne s'affichent pas correctement
8. Pour mettre en évidence une partie du texte, utilise plutôt des tirets, des émojis ou des phrases claires comme "Important : " ou "À retenir : "
9. Utilise des phrases complètes et évite les énumérations avec points/numéros
10. Sépare clairement les différentes sections de ton message
"""

    customized_system_prompt += formatting_instructions

    if not current_user.is_authenticated:
        return customized_system_prompt

    # Ajouter les informations du profil si disponibles
    profile_info = []
    if current_user.username:
        profile_info.append(f"Nom d'utilisateur: {current_user.username}")
    if current_user.age:
        profile_info.append(f"Âge: {current_user.age} ans")
    if current_user.gender:
        profile_info.append(f"Genre: {current_user.gender}")
    if current_user.height and current_user.weight:
        profile_info.append(f"Taille: {current_user.height} cm, Poids: {current_user.weight} kg")
    if current_user.fitness_goal:
        # Mapper les codes vers des descriptions plus lisibles
        goal_map = {
            'perte_de_poids': 'Perte de poids',
            'prise_de_muscle': 'Prise de muscle/musculation',
            'endurance': 'Amélioration de l\'endurance',
            'force': 'Développement de la force',
            'sante': 'Santé générale et bien-être',
            'mobilite': 'Amélioration de la mobilité et flexibilité'
        }
        goal_desc = goal_map.get(current_user.fitness_goal, current_user.fitness_goal)
        profile_info.append(f"Objectif fitness: {goal_desc}")

    if current_user.fitness_level:
        level_map = {
            'debutant': 'Débutant',
            'intermediaire': 'Intermédiaire',
            'avance': 'Avancé'
        }
        level_desc = level_map.get(current_user.fitness_level, current_user.fitness_level)
        profile_info.append(f"Niveau d'expérience: {level_desc}")

    if current_user.activity_level:
        activity_map = {
            'sedentaire': 'Sédentaire (peu ou pas d\'exercice)',
            'leger': 'Légèrement actif (exercice léger 1-3 fois/semaine)',
            'modere': 'Modérément actif (exercice modéré 3-5 fois/semaine)',
            'actif': 'Actif (exercice intense 6-7 fois/semaine)',
            'tres_actif': 'Très actif (exercice intense quotidien ou athlète)'
        }
        activity_desc = activity_map.get(current_user.activity_level, current_user.activity_level)
        profile_info.append(f"Niveau d'activité quotidienne: {activity_desc}")

    if current_user.equipment_access:
        equipment_map = {
            'aucun': 'Aucun équipement (poids du corps uniquement)',
            'leger': 'Équipement léger à domicile (haltères, bandes élastiques)',
            'maison': 'Salle à domicile (haltères, banc, barre)',
            'salle': 'Accès à une salle de sport complète'
        }
        equipment_desc = equipment_map.get(current_user.equipment_access, current_user.equipment_access)
        profile_info.append(f"Équipement disponible: {equipment_desc}")

    if current_user.medical_conditions:
        profile_info.append(f"Conditions médicales ou blessures: {current_user.medical_conditions}")

    if current_user.dietary_restrictions:
        profile_info.append(f"Restrictions alimentaires: {current_user.dietary_restrictions}")

    if profile_info:
        profile_section = "\n\nInformations sur l'utilisateur:\n" + "\n".join(profile_info)
        customized_system_prompt += profile_section
        customized_system_prompt += "\n\nUtilise ces informations pour personnaliser tes réponses sans demander ces détails à nouveau, sauf si tu as besoin de précisions supplémentaires. Si certaines informations manquent pour donner un conseil personnalisé, tu peux poser des questions spécifiques sur ces points manquants, mais limite-toi à 1-2 questions par message."

    return customized_system_prompt

# Routes générales
@app.route('/')
def index():
    now = datetime.now()
    return render_template('index.html', now=now)  # Correctement indenté

# Routes d'authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = 'remember_me' in request.form

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember_me)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            flash('Connexion réussie!', 'success')
            return redirect(next_page)
        else:
            flash('Email ou mot de passe incorrect.', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'error')
            return render_template('register.html')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Ce nom d\'utilisateur ou cet email est déjà utilisé.', 'error')
            return render_template('register.html')

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        from models.user import db
        db.session.add(new_user)
        db.session.commit()

        flash('Votre compte a été créé avec succès! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Routes de profil
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user = current_user

    user.username = request.form.get('username')
    user.email = request.form.get('email')

    # Informations personnelles
    user.age = request.form.get('age', type=int)
    user.gender = request.form.get('gender')
    user.height = request.form.get('height', type=float)
    user.weight = request.form.get('weight', type=float)

    # Préférences fitness
    user.fitness_goal = request.form.get('fitness_goal')
    user.fitness_level = request.form.get('fitness_level')
    user.activity_level = request.form.get('activity_level')
    user.equipment_access = request.form.get('equipment_access')
    user.medical_conditions = request.form.get('medical_conditions')
    user.dietary_restrictions = request.form.get('dietary_restrictions')

    from models.user import db
    db.session.commit()

    flash('Votre profil a été mis à jour avec succès!', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_user.check_password(current_password):
        flash('Mot de passe actuel incorrect.', 'error')
        return redirect(url_for('profile'))

    if new_password != confirm_password:
        flash('Les nouveaux mots de passe ne correspondent pas.', 'error')
        return redirect(url_for('profile'))

    current_user.set_password(new_password)

    from models.user import db
    db.session.commit()

    flash('Votre mot de passe a été changé avec succès!', 'success')
    return redirect(url_for('profile'))

# Routes de chat
@app.route('/chat', methods=['GET'])
@login_required
def chat():
    conversation_id = request.args.get('conversation_id', type=int)
    conversation = None

    if conversation_id:
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()

    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()

    # Si une requête prompt est fournie, initialiser le chat avec cette question
    prompt = request.args.get('prompt')
    if prompt and not conversation_id:
        # Créer une nouvelle conversation
        conversation = Conversation(user_id=current_user.id, title="Nouvelle conversation")

        from models.user import db
        db.session.add(conversation)
        db.session.commit()

        # Ajouter le message de l'utilisateur
        message = Message(conversation_id=conversation.id, role="user", content=prompt)
        db.session.add(message)

        # Obtenir le prompt personnalisé avec les infos du profil
        customized_system_prompt = get_customized_system_prompt()

        # Obtenir la réponse du coach IA
        response_content = bedrock_client.invoke_model(prompt, system_prompt=customized_system_prompt)

        # Ajouter la réponse
        assistant_message = Message(conversation_id=conversation.id, role="assistant", content=response_content)
        db.session.add(assistant_message)

        # Mettre à jour le titre de la conversation en fonction du contenu
        conversation.title = generate_conversation_title(prompt)
        db.session.commit()

        # Rafraîchir la conversation pour inclure les messages
        conversation = Conversation.query.get(conversation.id)

        # Mettre à jour la liste des conversations
        conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()

    return render_template('chat.html', conversation=conversation, conversations=conversations)

@app.route('/message-image/<int:message_id>')
@login_required
def get_message_image(message_id):
    message = Message.query.get_or_404(message_id)
    # Vérifier que l'utilisateur a accès à cette image
    conversation = Conversation.query.get_or_404(message.conversation_id)
    if conversation.user_id != current_user.id:
        abort(403)
    
    if not message.image_path:
        abort(404)
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], message.image_path)


@app.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    message_content = data.get('message', '')
    conversation_id = data.get('conversation_id')
    image_data = data.get('image_data')  # base64 image data

    if not message_content and not image_data:
        return jsonify({'error': 'Message or image must be provided'}), 400

    from models.user import db

    # Si pas de conversation_id, créer une nouvelle conversation
    if not conversation_id:
        conversation = Conversation(user_id=current_user.id, title="Nouvelle conversation")
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
    else:
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()

    # Préparer le contenu HTML pour l'affichage du message utilisateur
    display_content = message_content
    if image_data:
        # Créer une version HTML du message avec l'image pour l'affichage
        image_html = f'<div class="user-image-container"><img src="{image_data}" class="user-image" alt="Image utilisateur"></div>'
        text_html = f'<div class="user-text">{message_content}</div>' if message_content else ''
        display_content = f'{image_html}{text_html}'

    # Ajouter le message de l'utilisateur
    user_message = Message(conversation_id=conversation_id, role="user", content=display_content)
    db.session.add(user_message)
    db.session.commit()

    # Préparer l'historique de conversation pour Claude (sans inclure le message qu'on vient d'ajouter)
    message_history = []
    for message in conversation.messages.filter(Message.id != user_message.id).order_by(Message.created_at).all():
        message_history.append({
            "role": message.role,
            "content": message.content
        })

    # Obtenir le prompt personnalisé avec les infos du profil
    customized_system_prompt = get_customized_system_prompt()

    # Traitement de l'image si présente
    image_binary = None
    if image_data:
        try:
            # Nettoyer l'image data:image base64
            clean_image_data = image_data
            if "," in image_data:
                clean_image_data = image_data.split(",", 1)[1]
            
            # Décoder l'image
            image_binary = base64.b64decode(clean_image_data)
            print(f"Image successfully decoded, size: {len(image_binary)} bytes")
        except Exception as e:
            print(f"Error decoding image: {str(e)}")
            return jsonify({'error': 'Invalid image data'}), 400

    # Obtenir la réponse du coach IA
    try:
        if len(message_history) == 0:
            # Première interaction, utiliser invoke_model
            response_content = bedrock_client.invoke_model(
                message_content, 
                system_prompt=customized_system_prompt,
                image_data=image_binary
            )
        else:
            # Conversation en cours, utiliser continue_conversation
            response_content = bedrock_client.continue_conversation(
                message_history,
                message_content,
                system_prompt=customized_system_prompt,
                image_data=image_binary
            )

        # Ajouter la réponse
        assistant_message = Message(conversation_id=conversation_id, role="assistant", content=response_content)
        db.session.add(assistant_message)

        # Si c'est une nouvelle conversation, générer un titre
        if conversation.title == "Nouvelle conversation":
            conversation.title = generate_conversation_title(message_content)

        # Mettre à jour la date de la conversation
        conversation.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'user_message': {
                'content': user_message.content,
                'time': user_message.created_at.strftime('%H:%M')
            },
            'assistant_message': {
                'content': assistant_message.content,
                'time': assistant_message.created_at.strftime('%H:%M')
            },
            'conversation_id': conversation_id
        })
    except Exception as e:
        print(f"Error getting response from AI: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/chat/new', methods=['POST'])
@login_required
def new_conversation():
    from models.user import db

    conversation = Conversation(user_id=current_user.id, title="Nouvelle conversation")
    db.session.add(conversation)
    db.session.commit()

    return jsonify({
        'conversation_id': conversation.id,
        'redirect_url': url_for('chat', conversation_id=conversation.id)
    })

@app.route('/chat/rename/<int:conversation_id>', methods=['POST'])
@login_required
def rename_conversation(conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()

    data = request.json
    new_title = data.get('title')

    if not new_title:
        return jsonify({'error': 'Title cannot be empty'}), 400

    conversation.title = new_title

    from models.user import db
    db.session.commit()

    return jsonify({'success': True})

@app.route('/chat/delete/<int:conversation_id>', methods=['POST'])
@login_required
def delete_conversation(conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()

    from models.user import db
    db.session.delete(conversation)
    db.session.commit()

    return jsonify({'success': True, 'redirect_url': url_for('chat')})

# Route pour supprimer toutes les conversations
@app.route('/delete-all-conversations', methods=['POST'])
@login_required
def delete_all_conversations():
    from models.user import db

    # Récupérer toutes les conversations de l'utilisateur
    conversations = Conversation.query.filter_by(user_id=current_user.id).all()

    # Supprimer chaque conversation
    for conversation in conversations:
        db.session.delete(conversation)

    # Valider les suppressions
    db.session.commit()

    flash('Toutes vos conversations ont été supprimées avec succès!', 'success')
    return redirect(url_for('chat'))

# Routes de programme d'entraînement
@app.route('/workout-plans')
@login_required
def workout_plans():
    plans = WorkoutPlan.query.filter_by(user_id=current_user.id).order_by(WorkoutPlan.created_at.desc()).all()
    return render_template('workout_plans.html', plans=plans)

@app.route('/workout-plan/<int:plan_id>')
@login_required
def workout_plan(plan_id):
    plan = WorkoutPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    return render_template('workout_plan.html', plan=plan)

@app.route('/workout-plan/new')
@login_required
def new_workout_plan():
    return render_template('workout_plan.html', plan=None)

@app.route('/workout-plan/create', methods=['POST'])
@login_required
def create_workout_plan():
    title = request.form.get('title')
    description = request.form.get('description')
    objective = request.form.get('objective')
    days_per_week = request.form.get('days_per_week', type=int)
    duration_minutes = request.form.get('duration_minutes', type=int)
    difficulty_level = request.form.get('difficulty_level')
    equipment = request.form.get('equipment')
    limitations = request.form.get('limitations')

    # Créer le prompt pour Claude
    prompt = WORKOUT_PLAN_PROMPT.format(
        objective=objective,
        level=difficulty_level,
        availability=days_per_week,
        duration=duration_minutes,
        equipment=equipment,
        limitations=limitations or "Aucune limitation particulière"
    )

    # Obtenir le prompt personnalisé avec les infos du profil
    customized_system_prompt = get_customized_system_prompt()

    # Obtenir le plan d'entraînement de Claude
    plan_content = bedrock_client.invoke_model(prompt, system_prompt=customized_system_prompt)

    # Créer le plan d'entraînement
    workout_plan = WorkoutPlan(
        user_id=current_user.id,
        title=title,
        description=description,
        objective=objective,
        days_per_week=days_per_week,
        duration_minutes=duration_minutes,
        difficulty_level=difficulty_level,
        plan_content=plan_content
    )

    from models.user import db
    db.session.add(workout_plan)
    db.session.commit()

    flash('Votre programme d\'entraînement a été créé avec succès!', 'success')
    return redirect(url_for('workout_plan', plan_id=workout_plan.id))

@app.route('/workout-plan/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit_workout_plan(plan_id):
    plan = WorkoutPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        plan.title = request.form.get('title')
        plan.description = request.form.get('description')
        plan.plan_content = request.form.get('plan_content')

        from models.user import db
        db.session.commit()

        flash('Votre programme d\'entraînement a été mis à jour avec succès!', 'success')
        return redirect(url_for('workout_plan', plan_id=plan.id))

    return render_template('edit_workout_plan.html', plan=plan)

@app.route('/workout-plan/delete/<int:plan_id>', methods=['POST'])
@login_required
def delete_workout_plan(plan_id):
    plan = WorkoutPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()

    from models.user import db
    db.session.delete(plan)
    db.session.commit()

    flash('Votre programme d\'entraînement a été supprimé avec succès!', 'success')
    return redirect(url_for('workout_plans'))

@app.route('/workout-log/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def log_workout(plan_id):
    plan = WorkoutPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        duration_minutes = request.form.get('duration_minutes', type=int)
        perceived_effort = request.form.get('perceived_effort', type=int)
        notes = request.form.get('notes')

        workout_log = WorkoutLog(
            user_id=current_user.id,
            workout_plan_id=plan.id,
            date=date,
            duration_minutes=duration_minutes,
            perceived_effort=perceived_effort,
            notes=notes
        )

        from models.user import db
        db.session.add(workout_log)
        db.session.commit()

        flash('Votre séance d\'entraînement a été enregistrée avec succès!', 'success')
        return redirect(url_for('workout_plan', plan_id=plan.id))

    return render_template('log_workout.html', plan=plan)

# Routes de plan nutritionnel
@app.route('/nutrition-plans')
@login_required
def nutrition_plans():
    plans = NutritionPlan.query.filter_by(user_id=current_user.id).order_by(NutritionPlan.created_at.desc()).all()
    return render_template('nutrition_plans.html', plans=plans)

@app.route('/nutrition-plan/<int:plan_id>')
@login_required
def nutrition_plan(plan_id):
    plan = NutritionPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    return render_template('nutrition_plan.html', plan=plan)

@app.route('/nutrition-plan/new')
@login_required
def new_nutrition_plan():
    return render_template('nutrition_plan.html', plan=None)

@app.route('/nutrition-plan/create', methods=['POST'])
@login_required
def create_nutrition_plan():
    title = request.form.get('title')
    description = request.form.get('description')
    objective = request.form.get('objective')
    food_preferences = request.form.get('food_preferences')
    food_restrictions = request.form.get('food_restrictions')

    # Créer le prompt pour Claude
    prompt = NUTRITION_PLAN_PROMPT.format(
        objective=objective,
        age=current_user.age or 30,
        height=current_user.height or 175,
        weight=current_user.weight or 70,
        gender=current_user.gender or "non spécifié",
        activity_level=current_user.activity_level or "modéré",
        food_preferences=food_preferences or "Pas de préférences particulières",
        food_restrictions=food_restrictions or current_user.dietary_restrictions or "Aucune restriction alimentaire"
    )

    # Obtenir le prompt personnalisé avec les infos du profil
    customized_system_prompt = get_customized_system_prompt()

    # Obtenir le plan nutritionnel de Claude
    plan_content = bedrock_client.invoke_model(prompt, system_prompt=customized_system_prompt)

    # Analyser les macronutriments à partir de la réponse (estimation simple)
    daily_calories = 0
    protein_percentage = 0
    carbs_percentage = 0
    fat_percentage = 0

    try:
        # Tentative d'extraction des valeurs à partir de la réponse
        if "calories" in plan_content.lower():
            calorie_match = re.search(r'(\d{1,4})\s*(?:kcal|calories)', plan_content.lower())
            if calorie_match:
                daily_calories = int(calorie_match.group(1))

            # Estimation des macros en fonction de l'objectif
            if objective == "perte_de_poids":
                protein_percentage = 35
                carbs_percentage = 35
                fat_percentage = 30
            elif objective == "prise_de_muscle":
                protein_percentage = 40
                carbs_percentage = 40
                fat_percentage = 20
            elif objective == "performance":
                protein_percentage = 30
                carbs_percentage = 50
                fat_percentage = 20
            else:
                protein_percentage = 30
                carbs_percentage = 40
                fat_percentage = 30
    except:
        # Valeurs par défaut en cas d'erreur
        daily_calories = 2000
        protein_percentage = 30
        carbs_percentage = 40
        fat_percentage = 30

    # Créer le plan nutritionnel
    nutrition_plan = NutritionPlan(
        user_id=current_user.id,
        title=title,
        description=description,
        objective=objective,
        daily_calories=daily_calories,
        protein_percentage=protein_percentage,
        carbs_percentage=carbs_percentage,
        fat_percentage=fat_percentage,
        plan_content=plan_content
    )

    from models.user import db
    db.session.add(nutrition_plan)
    db.session.commit()

    flash('Votre plan nutritionnel a été créé avec succès!', 'success')
    return redirect(url_for('nutrition_plan', plan_id=nutrition_plan.id))

@app.route('/nutrition-plan/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit_nutrition_plan(plan_id):
    plan = NutritionPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        plan.title = request.form.get('title')
        plan.description = request.form.get('description')
        plan.plan_content = request.form.get('plan_content')

        # Mise à jour des macros si fournies
        daily_calories = request.form.get('daily_calories', type=int)
        protein_percentage = request.form.get('protein_percentage', type=int)
        carbs_percentage = request.form.get('carbs_percentage', type=int)
        fat_percentage = request.form.get('fat_percentage', type=int)

        if daily_calories:
            plan.daily_calories = daily_calories
        if protein_percentage:
            plan.protein_percentage = protein_percentage
        if carbs_percentage:
            plan.carbs_percentage = carbs_percentage
        if fat_percentage:
            plan.fat_percentage = fat_percentage

        from models.user import db
        db.session.commit()

        flash('Votre plan nutritionnel a été mis à jour avec succès!', 'success')
        return redirect(url_for('nutrition_plan', plan_id=plan.id))

    return render_template('edit_nutrition_plan.html', plan=plan)

@app.route('/nutrition-plan/delete/<int:plan_id>', methods=['POST'])
@login_required
def delete_nutrition_plan(plan_id):
    plan = NutritionPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()

    from models.user import db
    db.session.delete(plan)
    db.session.commit()

    flash('Votre plan nutritionnel a été supprimé avec succès!', 'success')
    return redirect(url_for('nutrition_plans'))

@app.route('/nutrition-plan/print/<int:plan_id>')
@login_required
def print_nutrition_plan(plan_id):
    plan = NutritionPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    return render_template('print_nutrition_plan.html', plan=plan)

# Fonction utilitaire pour générer un titre de conversation
def generate_conversation_title(first_message):
    prompt = f"Génère un titre court (5 mots maximum) pour une conversation qui commence par ce message: \"{first_message}\""
    title = bedrock_client.invoke_model(prompt, max_tokens=20)

    # Nettoyer le titre (enlever les guillemets, etc.)
    title = re.sub(r'^["\']+|["\']+$', '', title.strip())

    # Limiter la longueur
    if len(title) > 100:
        title = title[:97] + "..."

    return title

# Lancement de l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
