import io
import base64
from PIL import Image
from io import BytesIO

def resize_image(image_data, max_width=800, max_height=800, quality=85):
    """
    Redimensionne une image pour réduire sa taille tout en maintenant les proportions
    
    Args:
        image_data (bytes): Données binaires de l'image
        max_width (int): Largeur maximale
        max_height (int): Hauteur maximale
        quality (int): Qualité JPEG (1-100)
        
    Returns:
        bytes: Données de l'image redimensionnée
    """
    # Ouvrir l'image
    img = Image.open(BytesIO(image_data))
    
    # Obtenir les dimensions d'origine
    width, height = img.size
    
    # Calculer les nouvelles dimensions en maintenant le ratio
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # Redimensionner
        img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Enregistrer dans un buffer avec la qualité spécifiée
    buffer = BytesIO()
    
    # Préserver le format d'origine si possible
    format = img.format if img.format else 'JPEG'
    
    if format == 'JPEG' or format == 'JPG':
        img.save(buffer, format=format, quality=quality)
    elif format == 'PNG':
        img.save(buffer, format=format, optimize=True)
    else:
        # Convertir en JPEG pour les autres formats
        if img.mode == 'RGBA':
            # Convertir avec un fond blanc pour les images avec transparence
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # 3 est le canal alpha
            background.save(buffer, 'JPEG', quality=quality)
        else:
            img.convert('RGB').save(buffer, 'JPEG', quality=quality)
    
    # Retourner les données binaires
    buffer.seek(0)
    return buffer.getvalue()

def get_base64_image(image_data):
    """
    Convertit les données binaires d'une image en chaîne base64
    
    Args:
        image_data (bytes): Données binaires de l'image
        
    Returns:
        str: Chaîne base64 encodée
    """
    return base64.b64encode(image_data).decode('utf-8')

def get_image_format(image_data):
    """
    Détermine le format d'une image à partir de ses données binaires
    
    Args:
        image_data (bytes): Données binaires de l'image
        
    Returns:
        str: Format de l'image ('JPEG', 'PNG', etc.)
    """
    img = Image.open(BytesIO(image_data))
    return img.format

def get_media_type(image_data):
    """
    Détermine le type MIME d'une image à partir de ses données binaires
    
    Args:
        image_data (bytes): Données binaires de l'image
        
    Returns:
        str: Type MIME de l'image ('image/jpeg', 'image/png', etc.)
    """
    format = get_image_format(image_data)
    format_to_mime = {
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
        "PNG": "image/png",
        "GIF": "image/gif",
        "WEBP": "image/webp",
        "BMP": "image/bmp",
        "TIFF": "image/tiff"
    }
    
    return format_to_mime.get(format, f"image/{format.lower()}")

def decode_base64_image(base64_string):
    """
    Décode une chaîne base64 en données binaires d'image
    
    Args:
        base64_string (str): Chaîne base64 encodée
        
    Returns:
        bytes: Données binaires de l'image
    """
    # Enlever le préfixe data:image/...;base64, si présent
    if "," in base64_string:
        base64_string = base64_string.split(",", 1)[1]
    
    return base64.b64decode(base64_string)

def resize_base64_image(base64_string, max_width=800, max_height=800, quality=85):
    """
    Redimensionne une image encodée en base64
    
    Args:
        base64_string (str): Chaîne base64 encodée
        max_width (int): Largeur maximale
        max_height (int): Hauteur maximale
        quality (int): Qualité JPEG (1-100)
        
    Returns:
        str: Chaîne base64 encodée de l'image redimensionnée
    """
    # Extraire le préfixe si présent
    prefix = ""
    if "base64," in base64_string:
        parts = base64_string.split("base64,", 1)
        prefix = parts[0] + "base64,"
        base64_string = parts[1]
    
    # Décoder l'image
    image_data = base64.b64decode(base64_string)
    
    # Redimensionner l'image
    resized_data = resize_image(image_data, max_width, max_height, quality)
    
    # Encoder en base64
    resized_base64 = base64.b64encode(resized_data).decode('utf-8')
    
    # Retourner avec le préfixe
    return prefix + resized_base64

def resize_base64_image_with_size_limit(base64_string, max_size_mb=5, quality_start=85, min_quality=20):
    """
    Redimensionne une image base64 pour s'assurer qu'elle est sous la limite de taille spécifiée
    
    Args:
        base64_string (str): Chaîne base64 encodée
        max_size_mb (float): Taille maximale en MB
        quality_start (int): Qualité JPEG initiale (1-100)
        min_quality (int): Qualité JPEG minimale acceptable
        
    Returns:
        str: Chaîne base64 encodée de l'image redimensionnée
    """
    # Convertir MB en octets
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # Extraire le préfixe si présent
    if "base64," in base64_string:
        prefix = base64_string.split("base64,")[0] + "base64,"
        base64_string = base64_string.split("base64,")[1]
    else:
        prefix = ""
        
    # Décoder la chaîne base64
    image_data = base64.b64decode(base64_string)
    
    # Vérifier si déjà sous la limite de taille
    if len(image_data) <= max_size_bytes:
        return prefix + base64_string
    
    # Ouvrir l'image
    img = Image.open(BytesIO(image_data))
    
    # Obtenir le format d'origine
    original_format = img.format if img.format else 'JPEG'
    
    # Stratégie 1 : Réduire la qualité d'abord (pour JPEG/JPG)
    if original_format in ['JPEG', 'JPG']:
        quality = quality_start
        while quality >= min_quality:
            buffer = BytesIO()
            img.save(buffer, format=original_format, quality=quality)
            if buffer.tell() <= max_size_bytes:
                # Succès - retourner l'image redimensionnée
                buffer.seek(0)
                return prefix + base64.b64encode(buffer.getvalue()).decode('utf-8')
            quality -= 5
    
    # Stratégie 2 : Réduire les dimensions proportionnellement
    width, height = img.size
    scale_factor = 1.0
    
    while scale_factor > 0.1:
        # Calculer les nouvelles dimensions
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # Redimensionner l'image
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Essayer avec différents paramètres de qualité
        for quality in range(quality_start, min_quality - 1, -5):
            buffer = BytesIO()
            
            if original_format in ['JPEG', 'JPG']:
                resized_img.save(buffer, format=original_format, quality=quality)
            elif original_format == 'PNG':
                resized_img.save(buffer, format=original_format, optimize=True)
            else:
                resized_img.save(buffer, format=original_format)
            
            if buffer.tell() <= max_size_bytes:
                # Succès - retourner l'image redimensionnée
                buffer.seek(0)
                return prefix + base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Réduire le facteur d'échelle pour la prochaine itération
        scale_factor *= 0.8
    
    # Si toutes les stratégies échouent, retourner la plus petite version possible
    buffer = BytesIO()
    img.resize((int(width * 0.1), int(height * 0.1)), Image.LANCZOS).save(
        buffer, 
        format=original_format, 
        quality=min_quality if original_format in ['JPEG', 'JPG'] else None
    )
    
    return prefix + base64.b64encode(buffer.getvalue()).decode('utf-8')
