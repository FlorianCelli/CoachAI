import boto3
import json
import base64
from io import BytesIO
from PIL import Image

class BedrockClient:
    def __init__(self, aws_region, model_id):
        config = boto3.session.Config(
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
        if image_data:
            return self._invoke_with_image(prompt, system_prompt, max_tokens, temperature, image_data)
        else:
            # Traitement sans image (texte uniquement)
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            if system_prompt:
                request_body["system"] = system_prompt
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
    
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
            
            return format_to_mime.get(format, f"image/{format.lower()}")
        except Exception as e:
            print(f"Error determining media type: {e}")
            return "image/jpeg"  # Default fallback
    
    def _invoke_with_image(self, prompt, system_prompt=None, max_tokens=4096, temperature=0.7, image_data=None):
        """
        Méthode privée pour invoquer Claude avec une image
        """
        try:
            # Déterminer le type MIME de l'image
            media_type = self._get_media_type(image_data)
            
            # Encoder l'image en base64
            b64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Construire le message avec image
            content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64_image
                    }
                }
            ]
            
            # Ajouter le texte s'il existe
            if prompt:
                content.append({
                    "type": "text",
                    "text": prompt
                })
            else:
                # S'assurer qu'il y a toujours un texte
                content.append({
                    "type": "text",
                    "text": "Veuillez analyser cette image."
                })
            
            # Construire le corps de la requête
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }
            
            if system_prompt:
                request_body["system"] = system_prompt
            
            # Debug logging
            print(f"Requesting with image. Media type: {media_type}, Prompt: {prompt}")
            
            # Invoquer le modèle
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
        except Exception as e:
            print(f"Error invoking model with image: {e}")
            raise e
    
    def continue_conversation(self, conversation_history, user_message, system_prompt=None, max_tokens=4096, temperature=0.7, image_data=None):
        """
        Continuer une conversation avec l'historique et éventuellement une image
        """
        # Construire les messages précédents de la conversation
        messages = []
        for message in conversation_history:
            # Pour la compatibilité avec les messages d'historique qui pourraient être sous forme de chaîne
            if isinstance(message.get("content"), str):
                messages.append({
                    "role": message["role"],
                    "content": message["content"]
                })
            else:
                # Si le contenu est déjà au bon format (liste), le conserver tel quel
                messages.append(message)
        
        # Construire le nouveau message utilisateur
        if image_data:
            try:
                # Déterminer le type MIME de l'image
                media_type = self._get_media_type(image_data)
                
                # Encoder l'image en base64
                b64_image = base64.b64encode(image_data).decode('utf-8')
                
                # Construire le contenu du message avec image
                content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_image
                        }
                    }
                ]
                
                # Ajouter le texte s'il existe
                if user_message:
                    content.append({
                        "type": "text",
                        "text": user_message
                    })
                else:
                    # S'assurer qu'il y a toujours un texte
                    content.append({
                        "type": "text",
                        "text": "Veuillez analyser cette image."
                    })
                
                # Ajouter le message à la liste des messages
                messages.append({
                    "role": "user",
                    "content": content
                })
                
                # Debug logging
                print(f"Adding message with image. Media type: {media_type}, Message: {user_message}")
            except Exception as e:
                print(f"Error preparing image for conversation: {e}")
                # En cas d'erreur, ajouter un message texte normal
                messages.append({
                    "role": "user",
                    "content": user_message or "Erreur lors du traitement de l'image."
                })
        else:
            # Ajouter un message texte normal
            messages.append({
                "role": "user",
                "content": user_message
            })
        
        # Construire le corps de la requête
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        # Invoquer le modèle
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text']
