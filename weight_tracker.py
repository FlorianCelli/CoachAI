# weight_tracker.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Pour le rendu sans serveur X
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np

# Ne pas importer les modèles directement ici
weight_tracker = Blueprint('weight_tracker', __name__)

# Les modèles seront importés dans chaque fonction pour éviter l'importation circulaire

@weight_tracker.route('/weight-tracker')
@login_required
def index():
    from models.weight_entry import WeightEntry  # Import depuis le chemin absolu
    entries = WeightEntry.query.filter_by(user_id=current_user.id).order_by(WeightEntry.date.desc()).all()
    return render_template('weight_tracker.html', entries=entries)

@weight_tracker.route('/weight-tracker/add', methods=['POST'])
@login_required
def add_entry():
    from models import db, WeightEntry  # Import à l'intérieur de la fonction
    try:
        weight = float(request.form.get('weight'))
        date_str = request.form.get('date')
        notes = request.form.get('notes', '')
        
        if not date_str:
            date = datetime.utcnow().date()
        else:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Vérifier si une entrée existe déjà pour cette date
        existing_entry = WeightEntry.query.filter_by(
            user_id=current_user.id, 
            date=date
        ).first()
        
        if existing_entry:
            existing_entry.weight = weight
            existing_entry.notes = notes
            flash('Entrée de poids mise à jour avec succès.', 'success')
        else:
            entry = WeightEntry(
                user_id=current_user.id,
                weight=weight,
                date=date,
                notes=notes
            )
            db.session.add(entry)
            flash('Entrée de poids ajoutée avec succès.', 'success')
            
        db.session.commit()
        
    except ValueError:
        flash('Veuillez entrer un poids valide.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Une erreur est survenue: {str(e)}', 'error')
    
    return redirect(url_for('weight_tracker.index'))

@weight_tracker.route('/weight-tracker/data')
@login_required
def get_data():
    from models import WeightEntry  # Import à l'intérieur de la fonction
    entries = WeightEntry.query.filter_by(user_id=current_user.id).order_by(WeightEntry.date.asc()).all()
    data = [entry.to_dict() for entry in entries]
    return jsonify(data)

@weight_tracker.route('/weight-tracker/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    from models import db, WeightEntry  # Import à l'intérieur de la fonction
    entry = WeightEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(entry)
    db.session.commit()
    
    flash('Entrée de poids supprimée avec succès.', 'success')
    return redirect(url_for('weight_tracker.index'))

@weight_tracker.route('/weight-tracker/chart-image')
@login_required
def get_chart_image():
    from models import WeightEntry  # Import à l'intérieur de la fonction
    entries = WeightEntry.query.filter_by(user_id=current_user.id).order_by(WeightEntry.date.asc()).all()
    
    if not entries:
        return jsonify({'error': 'Pas de données disponibles'}), 404
    
    # Créer le graphique avec matplotlib
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(1, 1, 1)
    
    dates = [entry.date for entry in entries]
    weights = [entry.weight for entry in entries]
    
    # Calculer la tendance
    if len(entries) > 2:
        x = mdates.date2num(dates)
        z = np.polyfit(x, weights, 1)
        p = np.poly1d(z)
        ax.plot(dates, p(x), "r--", alpha=0.8, label="Tendance")
    
    ax.plot(dates, weights, 'o-', color='#3498db', linewidth=2, markersize=8)
    
    # Calculer les statistiques
    weight_diff = 0
    weight_per_week = 0
    if len(entries) > 1:
        weight_start = entries[0].weight
        weight_current = entries[-1].weight
        weight_diff = weight_current - weight_start
        days_diff = (entries[-1].date - entries[0].date).days
        
        if days_diff > 0:
            weight_per_week = (weight_diff / days_diff) * 7
            ax.text(0.05, 0.95, 
                   f'Début: {weight_start:.1f} kg\nDernier: {weight_current:.1f} kg\n'
                   f'Variation: {weight_diff:+.1f} kg\n'
                   f'Rythme: {weight_per_week:+.1f} kg/semaine',
                   transform=ax.transAxes, fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_title('Évolution du Poids', fontsize=16)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Poids (kg)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Formater les dates sur l'axe x
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    fig.autofmt_xdate()
    
    # Convertir le graphique en image
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    
    # Encodage en base64 pour les données d'image
    image_data = base64.b64encode(output.getvalue()).decode('utf-8')
    
    return jsonify({
        'image_data': f'data:image/png;base64,{image_data}',
        'statistics': {
            'entries_count': len(entries),
            'first_date': dates[0].isoformat() if dates else None,
            'last_date': dates[-1].isoformat() if dates else None,
            'first_weight': weights[0] if weights else None,
            'last_weight': weights[-1] if weights else None,
            'weight_diff': round(weight_diff, 2) if len(entries) > 1 else None,
            'weight_per_week': round(weight_per_week, 2) if len(entries) > 1 and days_diff > 0 else None
        }
    })
