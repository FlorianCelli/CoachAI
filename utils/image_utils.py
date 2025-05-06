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
