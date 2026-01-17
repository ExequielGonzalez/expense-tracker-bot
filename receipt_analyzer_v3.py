"""
Receipt Analyzer V3 - Ollama Vision LLM Integration

Uses qwen3-vl:4b-instruct (or configurable model) via Ollama API to analyze
receipt images and extract structured data as JSON.

Features:
- Vision LLM for intelligent receipt understanding
- Deterministic JSON output (temperature=0)
- Automatic VRAM release after each analysis (keep_alive=0)
- Strict validation of output schema and categories
- Compatible with V2 output format for bot/CSV integration
"""

import os
import re
import json
import base64
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration via environment variables
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3-vl:4b-instruct')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '120'))
STORE_RAW_TEXT = os.getenv('STORE_RAW_TEXT', '0') == '1'

# Valid categories (must match bot.py and V2)
VALID_CATEGORIES = ['Comida', 'Transporte', 'Compras', 'Entretenimiento', 'Otros']

# System prompt for deterministic JSON extraction
SYSTEM_PROMPT = """Eres un asistente especializado en analizar imágenes de tickets/recibos de compra.
Tu tarea es extraer información estructurada del ticket y devolverla ÚNICAMENTE como JSON válido.

REGLAS ESTRICTAS:
1. Responde SOLO con un objeto JSON válido, sin texto adicional antes o después.
2. NO incluyas explicaciones, comentarios ni markdown.
3. NO uses bloques de código (```).
4. El JSON debe tener exactamente estos campos:

{
  "amount": <número decimal con el monto total pagado>,
  "date": "<fecha en formato YYYY-MM-DD>",
  "title": "<nombre del comercio/establecimiento>",
  "category": "<una de las categorías permitidas>",
  "confidence": <número entero 0-100 indicando tu confianza en la extracción>
}

CATEGORÍAS PERMITIDAS (elige la más apropiada según el tipo de gasto):
- "Comida": supermercados, restaurantes, cafeterías, panaderías, carnicerías
- "Transporte": gasolina, parking, taxi, transporte público, peajes
- "Compras": tiendas de ropa, electrónica, ópticas, muebles, deportes
- "Entretenimiento": cine, teatro, conciertos, museos, gimnasios
- "Otros": cualquier gasto que no encaje en las anteriores

INSTRUCCIONES DE EXTRACCIÓN:
- amount: Busca el TOTAL final pagado (no subtotales). Si hay varios, usa el mayor.
- date: Extrae la fecha del ticket. Si no es visible, usa "1900-01-01".
- title: Nombre del comercio, generalmente en las primeras líneas del ticket.
- category: Clasifica según el tipo de establecimiento y productos comprados.
- confidence: Tu nivel de seguridad (0-100) en la precisión de los datos extraídos.

IMPORTANTE: Si no puedes leer el ticket o está muy borroso, devuelve:
{"amount": 0, "date": "1900-01-01", "title": "Ilegible", "category": "Otros", "confidence": 0}"""

USER_PROMPT = """Analiza esta imagen de ticket/recibo y extrae la información solicitada.
Responde ÚNICAMENTE con el JSON, sin ningún texto adicional."""


class ReceiptAnalyzerV3:
    """
    Vision LLM-based receipt analyzer using Ollama.
    
    Sends receipt images to a local Ollama instance running a vision model
    (default: qwen3-vl:4b-instruct) and extracts structured data.
    """
    
    def __init__(self, 
                 base_url: str | None = None,
                 model: str | None = None,
                 timeout: int | None = None,
                 keep_alive: int = 0):
        """
        Initialize the analyzer.
        
        Args:
            base_url: Ollama API base URL (default: from OLLAMA_BASE_URL env)
            model: Model name (default: from OLLAMA_MODEL env)
            timeout: Request timeout in seconds (default: from OLLAMA_TIMEOUT env)
            keep_alive: Seconds to keep model loaded after request (0 = unload immediately)
        """
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or OLLAMA_MODEL
        self.timeout = timeout or OLLAMA_TIMEOUT
        self.keep_alive = keep_alive
        
        # Ensure base_url doesn't end with /
        self.base_url = self.base_url.rstrip('/')
        
        print(f"[INFO] ReceiptAnalyzerV3 initialized")
        print(f"[INFO]   Ollama URL: {self.base_url}")
        print(f"[INFO]   Model: {self.model}")
        print(f"[INFO]   Timeout: {self.timeout}s")
        print(f"[INFO]   Keep-alive: {self.keep_alive}s (0=unload after each request)")
    
    def _encode_image_base64(self, image_path: str) -> str:
        """Read image file and encode as base64."""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _call_ollama(self, image_base64: str) -> str:
        """
        Call Ollama /api/chat endpoint with the image.
        
        Args:
            image_base64: Base64-encoded image data
            
        Returns:
            Parsed JSON response from the model
            
        Raises:
            requests.RequestException: On network/API errors
            json.JSONDecodeError: If model returns invalid JSON
            ValueError: If response doesn't match expected schema
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": USER_PROMPT,
                    "images": [image_base64]
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 1,
                "seed": 42  # Fixed seed for reproducibility
            },
            "keep_alive": self.keep_alive  # 0 = unload model after response (free VRAM)
        }
        
        print(f"[DEBUG] Calling Ollama API: {url}")
        print(f"[DEBUG] Model: {self.model}, keep_alive: {self.keep_alive}")
        
        response = requests.post(
            url,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()

        result = response.json()

        # Extract the assistant's message content
        if 'message' not in result or 'content' not in result['message']:
            raise ValueError(f"Unexpected Ollama response structure: {result}")

        content = result['message']['content'].strip()
        print(f"[DEBUG] Raw model response: {content[:500]}...")

        return content
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse and validate JSON from model response.
        
        Handles common issues like markdown code blocks or extra text.
        
        Args:
            content: Raw string response from the model
            
        Returns:
            Parsed and validated JSON dict
            
        Raises:
            json.JSONDecodeError: If content is not valid JSON
            ValueError: If JSON doesn't match expected schema
        """
        # Remove potential markdown code blocks
        content = content.strip()
        if content.startswith('```'):
            # Remove opening ```json or ```
            content = re.sub(r'^```(?:json)?\s*', '', content)
            # Remove closing ```
            content = re.sub(r'\s*```$', '', content)
            content = content.strip()
        
        # Try to extract JSON if there's extra text
        # Look for { ... } pattern
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        # Parse JSON
        data = json.loads(content)
        
        # Validate required fields
        required_fields = ['amount', 'date', 'title', 'category', 'confidence']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return data
    
    def _validate_and_normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize extracted data.
        
        Args:
            data: Parsed JSON from model
            
        Returns:
            Normalized data dict with correct types
            
        Raises:
            ValueError: If data fails validation
        """
        # Validate and normalize amount
        try:
            amount = float(data['amount'])
            if amount < 0:
                raise ValueError(f"Invalid amount (negative): {amount}")
            if amount > 100000:
                raise ValueError(f"Invalid amount (too large): {amount}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid amount value: {data['amount']}") from e
        
        # Validate and normalize date
        date_str = str(data['date']).strip()
        if date_str and date_str != '1900-01-01':
            try:
                # Try to parse the date
                parsed = datetime.strptime(date_str, '%Y-%m-%d')
                # Sanity check: date should be between 2020 and now
                if parsed.year < 2020 or parsed > datetime.now():
                    print(f"[WARN] Date out of reasonable range: {date_str}, using as-is")
            except ValueError:
                print(f"[WARN] Could not parse date '{date_str}', setting to 1900-01-01")
                date_str = '1900-01-01'
        else:
            date_str = '1900-01-01'
        
        # Validate category
        category = str(data['category']).strip()
        if category not in VALID_CATEGORIES:
            print(f"[WARN] Invalid category '{category}', mapping to 'Otros'")
            category = 'Otros'
        
        # Validate title
        title = str(data.get('title', 'Sin título')).strip()
        if not title:
            title = 'Sin título'
        if len(title) > 100:
            title = title[:100]
        
        # Validate confidence
        try:
            confidence = int(data.get('confidence', 50))
            confidence = max(0, min(100, confidence))
        except (TypeError, ValueError):
            confidence = 50
        
        return {
            'amount': round(amount, 2),
            'date': date_str,
            'title': title,
            'category': category,
            'model_confidence': confidence
        }
    
    def analyze_receipt(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a receipt image and extract structured data.
        
        This method is compatible with V2's analyze_receipt output format,
        allowing seamless integration with the existing bot and CSV handler.
        
        Args:
            image_path: Path to the receipt image file
            
        Returns:
            Dict with extracted data in V2-compatible format:
            {
                'amount': float,
                'amount_confidence': int,
                'date': str (YYYY-MM-DD),
                'date_confidence': int,
                'title': str,
                'title_confidence': int,
                'category': str,
                'category_confidence': int,
                'overall_confidence': float,
                'ocr_engine': str,
                'ocr_confidence': float,
                'raw_text': str,
                'model': str
            }
            
            Returns None if analysis fails completely.
            
        Raises:
            In strict mode (tests), raises exceptions on failures.
            In normal mode, returns None on failures.
        """
        print(f"\n[DEBUG] ========== Analyzing (V3): {image_path} ==========")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Encode image
        print(f"[DEBUG] Encoding image as base64...")
        image_base64 = self._encode_image_base64(image_path)
        print(f"[DEBUG] Image size: {len(image_base64)} bytes (base64)")
        
        # Call Ollama
        raw_response = self._call_ollama(image_base64)

        # Parse JSON response
        print(f"[DEBUG] Parsing JSON response...")
        parsed_data = self._parse_json_response(str(raw_response))

        print(f"[DEBUG] Parsed data: {parsed_data}")
        
        # Validate and normalize
        print(f"[DEBUG] Validating and normalizing...")
        normalized = self._validate_and_normalize(parsed_data)
        
        # Build V2-compatible result
        # Use model's confidence for all fields (LLM provides holistic confidence)
        model_conf = normalized['model_confidence']
        
        result = {
            'amount': normalized['amount'],
            'amount_confidence': model_conf,
            'date': normalized['date'],
            'date_confidence': model_conf if normalized['date'] != '1900-01-01' else 0,
            'title': normalized['title'],
            'title_confidence': model_conf,
            'category': normalized['category'],
            'category_confidence': model_conf,
            'overall_confidence': float(model_conf),
            'ocr_engine': f'ollama-{self.model}',
            'ocr_confidence': float(model_conf),
            'raw_text': raw_response if STORE_RAW_TEXT else '',
            'model': self.model
        }
        
        print(f"[DEBUG] ========== Analysis Complete (V3) ==========")
        print(f"[DEBUG] Amount: €{result['amount']:.2f}")
        print(f"[DEBUG] Date: {result['date']}")
        print(f"[DEBUG] Title: {result['title']}")
        print(f"[DEBUG] Category: {result['category']}")
        print(f"[DEBUG] Confidence: {result['overall_confidence']}%")
        
        return result
    
    def check_ollama_connection(self) -> bool:
        """
        Check if Ollama is reachable and the model is available.
        
        Returns:
            True if Ollama is accessible and model is loaded/available
        """
        try:
            # Check Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if model is available
            tags = response.json()
            models = [m.get('name', '') for m in tags.get('models', [])]
            
            # Check for exact match or partial match (with :latest suffix)
            model_available = any(
                self.model in m or m.startswith(self.model.split(':')[0])
                for m in models
            )
            
            if not model_available:
                print(f"[WARN] Model '{self.model}' not found. Available: {models}")
                return False
            
            print(f"[INFO] Ollama connection OK, model '{self.model}' available")
            return True
            
        except requests.RequestException as e:
            print(f"[ERROR] Ollama connection failed: {e}")
            return False


# Quick test when run directly
if __name__ == '__main__':
    import sys
    
    analyzer = ReceiptAnalyzerV3()
    
    # Check connection
    if not analyzer.check_ollama_connection():
        print("[ERROR] Cannot connect to Ollama or model not available")
        sys.exit(1)
    
    # Test with a sample image if provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        result = analyzer.analyze_receipt(image_path)
        if result:
            print("\n=== RESULT ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("[ERROR] Analysis failed")
            sys.exit(1)
    else:
        print("[INFO] No image provided. Usage: python receipt_analyzer_v3.py <image_path>")
