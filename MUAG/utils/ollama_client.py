import requests
from config import OLLAMA_URL, OLLAMA_MODEL, TIMEOUT_OLLAMA

class OllamaClient:
    def __init__(self, model=None):
        self.model = model or OLLAMA_MODEL
        self.base_url = OLLAMA_URL
    
    def generate(self, prompt, system_prompt=None, max_tokens=None, temperature=None):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "system": system_prompt,
            "keep_alive": 0,
            "options": {}
        }
        
        # Ajouter options si spécifiées
        if temperature is not None:
            payload["options"]["temperature"] = temperature
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=TIMEOUT_OLLAMA
            )
            return response.json()["response"]
        except Exception as e:
            return f"Erreur Ollama: {e}"
    
    def generate_with_image(self, prompt, image_base64, system_prompt=None):
        """
        Génère une réponse avec un VLM (Vision-Language Model)
        Args:
            prompt: Le prompt textuel
            image_base64: L'image encodée en base64
            system_prompt: Prompt système optionnel
        Returns:
            str: La réponse du VLM
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "images": [image_base64],  # Ollama accepte une liste d'images en base64
            "keep_alive": 0,  # Libère la mémoire immédiatement après
            "options": {
                "temperature": 0.0,  # Déterministe (pas d'aléatoire)
                "seed": 42,          # Reproductibilité
            }
        }

        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=TIMEOUT_OLLAMA * 2  # VLM prend plus de temps
            )
            return response.json()["response"]
        except Exception as e:
            return f"Erreur VLM Ollama: {e}"
    
    # Ajouter à la fin de la classe, après la méthode generate_with_image :

    def unload(self):
        """
        Force le déchargement du modèle de la VRAM
        Envoie une requête vide avec keep_alive=0
        """
        payload = {
            "model": self.model,
            "keep_alive": 0
        }
        
        try:
            requests.post(
                self.base_url,
                json=payload,
                timeout=5
            )
            print(f"[Ollama] Modèle {self.model} déchargé de la VRAM")
        except Exception as e:
            print(f"[Ollama] Erreur déchargement: {e}")