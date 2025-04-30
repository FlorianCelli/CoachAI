import boto3
import json

class BedrockClient:
    def __init__(self, aws_region, model_id):
        # Augmenter le timeout pour les requêtes à 120 secondes
        config = boto3.session.Config(
            read_timeout=120,
            connect_timeout=120,
            retries={'max_attempts': 2}
        )
        self.client = boto3.client('bedrock-runtime', 
                                  region_name=aws_region,
                                  config=config)
        self.model_id = model_id
    
    def invoke_model(self, prompt, system_prompt=None, max_tokens=4096, temperature=0.7):
        """
        Invoquer Claude 3.7 Sonnet via Amazon Bedrock
        """
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
    
    def continue_conversation(self, conversation_history, user_message, system_prompt=None, max_tokens=4096, temperature=0.7):
        """
        Continuer une conversation avec l'historique
        """
        messages = []
        
        for message in conversation_history:
            messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        # Ajouter le nouveau message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text']
