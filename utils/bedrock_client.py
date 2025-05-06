import boto3
import json
import base64
from io import BytesIO
from PIL import Image
from botocore.config import Config

class BedrockClient:
    def __init__(self, aws_region, model_id):
        config = Config(
            read_timeout=120,
            connect_timeout=120,
            retries={'max_attempts': 2}
        )
        self.client = boto3.client('bedrock-runtime', 
                                  region_name=aws_region,
                                  config=config)
        self.model_id = model_id
    
    def invoke_model(self, prompt, system_prompt=None, max_tokens=4096, temperature=0.7, image_data=None):
        """
        Invoquer Claude 3.7 Sonnet via Amazon Bedrock avec ou sans image
        """
        # Préparer le corps de la requête
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Ajouter le prompt système si fourni
        if system_prompt:
            request_body["system"] = system_prompt
        
        # Construire le message utilisateur
        if image_data:
            # Format pour les messages multimodaux (image + texte)
            user_content = []
            
            # Ajouter l'image
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self._get_media_type(image_data),
                    "data": base64.b64encode(image_data).decode('utf-8')
                }
            })
            
            # Ajouter le texte (même vide)
            if prompt and prompt.strip():
                user_content.append({
                    "type": "text",
                    "text": prompt
                })
            else:
                # Si pas de texte, ajouter une question générique
                user_content.append({
                    "type": "text",
                    "text": "Que penses-tu de cette image ?"
                })
            
            # Message final avec contenu multimodal
            request_body["messages"] = [
                {"role": "user", "content": user_content}
            ]
        else:
            # Pour les messages texte uniquement (format correct)
            request_body["messages"] = [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ]
        
        # Debug log
        content_types = [c["type"] for c in request_body["messages"][0]["content"]]
        print(f"INVOKE_MODEL - Requête avec {len(content_types)} éléments: {content_types}")
        
        # Exécuter la requête
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
        except Exception as e:
            print(f"ERREUR invoke_model: {str(e)}")
            raise
    
    def continue_conversation(self, conversation_history, user_message, system_prompt=None, max_tokens=4096, temperature=0.7, image_data=None):
        """
        Continuer une conversation avec l'historique et éventuellement une image
        """
        # Préparer le corps de la requête
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Ajouter le prompt système si fourni
        if system_prompt:
            request_body["system"] = system_prompt
        
        # Construire les messages pour la conversation
        messages = []
        
        # Traiter les messages d'historique - convertir au format correct si nécessaire
        for msg in conversation_history:
            role = msg["role"]
            content = msg["content"]
            
            # Convertir le contenu au format attendu par l'API
            if isinstance(content, str):
                formatted_content = [{"type": "text", "text": content}]
            else:
                # Supposer que le contenu est déjà correctement formaté
                formatted_content = content
            
            # Ajouter le message formaté
            messages.append({"role": role, "content": formatted_content})
        
        # Ajouter le nouveau message utilisateur
        if image_data:
            # Format multimodal pour image + texte
            user_content = []
            
            # Ajouter l'image
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self._get_media_type(image_data),
                    "data": base64.b64encode(image_data).decode('utf-8')
                }
            })
            
            # Ajouter le texte (même vide)
            if user_message and user_message.strip():
                user_content.append({
                    "type": "text",
                    "text": user_message
                })
            else:
                # Si pas de texte, ajouter une question générique
                user_content.append({
                    "type": "text",
                    "text": "Que penses-tu de cette image ?"
                })
            
            # Ajouter le message multimodal
            messages.append({"role": "user", "content": user_content})
        else:
            # Message texte uniquement (format correct)
            messages.append({
                "role": "user", 
                "content": [{"type": "text", "text": user_message}]
            })
        
        # Ajouter les messages à la requête
        request_body["messages"] = messages
        
        # Debug log
        last_message_content_types = [c["type"] for c in messages[-1]["content"]]
        print(f"CONTINUE_CONVERSATION - {len(messages)} messages total, dernier message avec {len(last_message_content_types)} éléments: {last_message_content_types}")
        
        # Exécuter la requête
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
        except Exception as e:
            print(f"ERREUR continue_conversation: {str(e)}")
            raise
    
    def _get_media_type(self, image_data):
        """
        Détermine le type MIME d'une image à partir de ses données binaires
        """
        try:
            img = Image.open(BytesIO(image_data))
            format = img.format or "JPEG"
            
            format_to_mime = {
                "JPEG": "image/jpeg",
                "JPG": "image/jpeg",
                "PNG": "image/png",
                "GIF": "image/gif",
                "WEBP": "image/webp",
                "BMP": "image/bmp",
                "TIFF": "image/tiff"
            }
            
            return format_to_mime.get(format.upper(), f"image/{format.lower()}")
        except Exception as e:
            print(f"Erreur détection type média: {str(e)}")
            return "image/jpeg"  # Par défaut
