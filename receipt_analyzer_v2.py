import re
import pytesseract
from PIL import Image
from datetime import datetime
import cv2
import numpy as np
from skimage import filters
import warnings
warnings.filterwarnings('ignore')

class ReceiptAnalyzerV2:
    """
    Multi-engine OCR analyzer with confidence scoring and fallback support.
    Supports: Tesseract, EasyOCR, PaddleOCR
    """
    
    def __init__(self, engines=['tesseract', 'easyocr', 'paddleocr']):
        self.engines = engines
        self.easyocr_reader = None
        self.paddleocr_reader = None
        
        # Category keywords for automatic classification
        self.category_keywords = {
            'Comida': ['supermerc', 'alimenta', 'restaur', 'cafe', 'bar', 'comida', 
                      'mercado', 'carniceria', 'panaderia', 'dia', 'mercadona', 'carrefour'],
            'Transporte': ['gasolina', 'combustible', 'parking', 'taxi', 'uber', 
                          'metro', 'bus', 'tren', 'peaje', 'autopista'],
            'Compras': ['optic', 'ropa', 'zapato', 'moda', 'tienda', 'store', 
                       'electronica', 'mueble', 'decathlon'],
            'Entretenimiento': ['cine', 'teatro', 'concert', 'museo', 'parque', 
                               'juego', 'deporte', 'gym'],
            'Otros': []
        }
    
    def _init_easyocr(self):
        """Lazy load EasyOCR"""
        if self.easyocr_reader is None and 'easyocr' in self.engines:
            try:
                import easyocr
                # Detect CUDA availability via PyTorch if possible
                have_cuda = False
                try:
                    import torch
                    have_cuda = torch.cuda.is_available()
                except Exception:
                    have_cuda = False

                self.easyocr_reader = easyocr.Reader(['es', 'en'], gpu=have_cuda, verbose=False)
                print(f"[DEBUG] EasyOCR initialized (gpu={have_cuda})")
            except Exception as e:
                print(f"[DEBUG] Could not initialize EasyOCR: {e}")
        return self.easyocr_reader
    
    def _init_paddleocr(self):
        """Lazy load PaddleOCR"""
        if self.paddleocr_reader is None and 'paddleocr' in self.engines:
            try:
                from paddleocr import PaddleOCR
                # Detect Paddle (GPU) support if possible
                have_cuda = False
                try:
                    import paddle
                    have_cuda = paddle.is_compiled_with_cuda()
                except Exception:
                    have_cuda = False

                # Try multiple possible PaddleOCR constructor signatures to support different versions
                tried = []
                def try_ctor(**kwargs):
                    tried.append(list(kwargs.keys()))
                    return PaddleOCR(**kwargs)

                init_attempts = [
                    dict(use_angle_cls=True, lang='es', show_log=False, use_gpu=have_cuda),
                    dict(use_angle_cls=True, lang='es', use_gpu=have_cuda),
                    dict(use_angle_cls=True, lang='es', show_log=False),
                    dict(lang='es'),
                    {},
                ]

                for params in init_attempts:
                    try:
                        self.paddleocr_reader = try_ctor(**params)
                        print(f"[DEBUG] PaddleOCR initialized with params: {params}")
                        break
                    except TypeError as te:
                        # Constructor doesn't accept these params, try next
                        continue
                    except Exception as e:
                        msg = str(e)
                        # If error mentions unknown/unexpected argument, try next signature
                        if any(substr in msg.lower() for substr in ['unknown argument', 'unexpected keyword', 'got an unexpected keyword']):
                            continue
                        # Otherwise it's likely a different failure (models, runtime); log and stop
                        print(f"[DEBUG] Could not initialize PaddleOCR with params {params}: {e}")
                        self.paddleocr_reader = None
                        break
                else:
                    print(f"[DEBUG] PaddleOCR initialization failed for tried signatures: {tried}")
            except Exception as e:
                print(f"[DEBUG] Could not initialize PaddleOCR: {e}")
        return self.paddleocr_reader
    
    def preprocess_image_basic(self, image_path):
        """Basic preprocessing: grayscale + resize"""
        img = Image.open(image_path)
        img = img.convert('L')
        img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
        return img
    
    def preprocess_image_advanced(self, image_path):
        """Advanced preprocessing: denoise, binarize, deskew"""
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Resize 2x for better OCR
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Adaptive thresholding for binarization
        binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        # Convert to PIL Image
        return Image.fromarray(binary)
    
    def extract_text_tesseract(self, image_path):
        """Extract text using Tesseract OCR"""
        try:
            # Try both raw and preprocessed to get best results
            results = []
            
            # Method 1: Raw image (better for clear text)
            img_raw = Image.open(image_path)
            text_raw = pytesseract.image_to_string(img_raw, lang='spa+eng')
            data_raw = pytesseract.image_to_data(img_raw, lang='spa+eng', output_type=pytesseract.Output.DICT)
            conf_raw = [int(c) for c in data_raw['conf'] if int(c) > 0]
            avg_conf_raw = sum(conf_raw) / len(conf_raw) if conf_raw else 0
            results.append(('raw', text_raw, avg_conf_raw, len(text_raw)))
            
            # Method 2: Advanced preprocessing (better for poor quality)
            img_adv = self.preprocess_image_advanced(image_path)
            text_adv = pytesseract.image_to_string(img_adv, lang='spa+eng')
            data_adv = pytesseract.image_to_data(img_adv, lang='spa+eng', output_type=pytesseract.Output.DICT)
            conf_adv = [int(c) for c in data_adv['conf'] if int(c) > 0]
            avg_conf_adv = sum(conf_adv) / len(conf_adv) if conf_adv else 0
            results.append(('advanced', text_adv, avg_conf_adv, len(text_adv)))
            
            # Choose best method: prefer raw if text length is significantly better
            # or if confidence is similar
            raw_score = results[0][3] * (results[0][2] / 100)
            adv_score = results[1][3] * (results[1][2] / 100)
            
            # Prefer raw if it has more text and decent confidence
            if results[0][3] > results[1][3] * 1.2 and results[0][2] > 50:
                best = results[0]
            else:
                best = max(results, key=lambda x: x[3] * (x[2] / 100))
            
            method, text, confidence, _ = best
            
            print(f"[DEBUG] Tesseract ({method}): {len(text)} chars, confidence: {confidence:.1f}%")
            return {
                'text': text,
                'confidence': confidence,
                'engine': 'tesseract'
            }
        except Exception as e:
            print(f"[DEBUG] Tesseract error: {e}")
            return {'text': '', 'confidence': 0, 'engine': 'tesseract'}
    
    def extract_text_easyocr(self, image_path):
        """Extract text using EasyOCR"""
        try:
            reader = self._init_easyocr()
            if reader is None:
                return {'text': '', 'confidence': 0, 'engine': 'easyocr'}
            
            img = cv2.imread(image_path)
            results = reader.readtext(img)
            
            text_parts = []
            confidences = []
            
            for bbox, text, conf in results:
                text_parts.append(text)
                confidences.append(conf * 100)  # Convert to percentage
            
            text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            print(f"[DEBUG] EasyOCR: {len(text)} chars, confidence: {avg_confidence:.1f}%")
            return {
                'text': text,
                'confidence': avg_confidence,
                'engine': 'easyocr'
            }
        except Exception as e:
            print(f"[DEBUG] EasyOCR error: {e}")
            return {'text': '', 'confidence': 0, 'engine': 'easyocr'}
    
    def extract_text_paddleocr(self, image_path):
        """Extract text using PaddleOCR"""
        try:
            reader = self._init_paddleocr()
            if reader is None:
                return {'text': '', 'confidence': 0, 'engine': 'paddleocr'}
            # Try common call signature; fall back if API differs
            try:
                results = reader.ocr(image_path, cls=True)
            except Exception:
                try:
                    results = reader.ocr(image_path)
                except Exception as e:
                    print(f"[DEBUG] PaddleOCR error during ocr call: {e}")
                    return {'text': '', 'confidence': 0, 'engine': 'paddleocr'}

            text_parts = []
            confidences = []

            # Parse several possible return formats
            if results:
                # Case A: results is nested and text entries are in results[0]
                if isinstance(results, (list, tuple)) and len(results) > 0 and isinstance(results[0], (list, tuple)):
                    # Try the common nested format
                    try:
                        for line in results[0]:
                            try:
                                t = line[1][0]
                                c = line[1][1]
                                text_parts.append(t)
                                confidences.append(c * 100)
                            except Exception:
                                continue
                    except Exception:
                        pass

                # Case B: results is a flat list of (box, (text, score)) or similar
                if not text_parts:
                    try:
                        for entry in results:
                            try:
                                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                                    second = entry[1]
                                    if isinstance(second, (list, tuple)) and len(second) >= 2 and isinstance(second[0], str):
                                        text_parts.append(second[0])
                                        confidences.append(second[1] * 100 if isinstance(second[1], float) else float(second[1]))
                                        continue
                                    # Some formats use entry = (box, text, score)
                                    if isinstance(second, str) and len(entry) >= 3:
                                        text_parts.append(second)
                                        try:
                                            confval = entry[2]
                                            confidences.append(confval * 100 if isinstance(confval, float) else float(confval))
                                        except Exception:
                                            pass
                            except Exception:
                                continue
                    except Exception:
                        pass
            
            text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            print(f"[DEBUG] PaddleOCR: {len(text)} chars, confidence: {avg_confidence:.1f}%")
            return {
                'text': text,
                'confidence': avg_confidence,
                'engine': 'paddleocr'
            }
        except Exception as e:
            print(f"[DEBUG] PaddleOCR error: {e}")
            return {'text': '', 'confidence': 0, 'engine': 'paddleocr'}
    
    def extract_text_multi_engine(self, image_path):
        """
        Extract text using multiple OCR engines with fallback.
        Returns the best result based on confidence and text length.
        """
        results = []
        
        # Try all engines
        if 'tesseract' in self.engines:
            results.append(self.extract_text_tesseract(image_path))
        
        if 'easyocr' in self.engines:
            results.append(self.extract_text_easyocr(image_path))
        
        if 'paddleocr' in self.engines:
            results.append(self.extract_text_paddleocr(image_path))
        
        # Filter out failed results
        valid_results = [r for r in results if r['text'].strip() and r['confidence'] > 0]
        
        if not valid_results:
            print("[DEBUG] No valid OCR results from any engine")
            return {'text': '', 'confidence': 0, 'engine': 'none'}
        
        # Score results: confidence * text_length_factor
        for result in valid_results:
            text_len = len(result['text'])
            length_score = min(text_len / 500, 1.0)  # Normalize to 0-1
            result['score'] = result['confidence'] * (0.7 + 0.3 * length_score)
        
        # Select best result
        best = max(valid_results, key=lambda x: x['score'])
        print(f"[DEBUG] Best engine: {best['engine']} (score: {best['score']:.1f})")
        
        return best
    
    def extract_amount(self, text):
        """Extract amount with confidence scoring"""
        patterns_priority = [
            (r'IMPORTE\s*TARJETA[^\d]*(\d+[.,]\d{2})', 95),
            (r'IMPORTE\s*PAGADO[^\d]*(\d+[.,]\d{2})', 95),
            (r'TOTAL\s*A\s*PAGAR[^\d€]*(\d+[.,]\d{2})', 90),
            (r'A\s*PAGAR[^\d€]*(\d+[.,]\d{2})\s*EUR', 90),
        ]
        
        patterns_secondary = [
            (r'(\d+[.,]\d{2})\s*EUR', 85),
            (r'TOTAL\s*(?:DE\s*COMPRA|COMPRA)[^\d€]*(\d+[.,]\d{2})', 80),
            (r'TOTAL[^\d€]*(\d+[.,]\d{2})', 70),
            (r'IMPORTE[^\d€]*(\d+[.,]\d{2})', 60),
        ]
        
        # Try priority patterns first
        for pattern, base_conf in patterns_priority:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                for match in matches:
                    clean_amount = match.replace('.', '').replace(',', '.')
                    try:
                        amount = float(clean_amount)
                        if 0 < amount < 10000:
                            print(f"[DEBUG] Amount found (priority): {amount} (confidence: {base_conf}%)")
                            return {'value': round(amount, 2), 'confidence': base_conf}
                    except ValueError:
                        continue
        
        # Try secondary patterns
        amounts = []
        for pattern, base_conf in patterns_secondary:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                clean_amount = match.replace('.', '').replace(',', '.')
                try:
                    amount = float(clean_amount)
                    if 0 < amount < 10000:
                        amounts.append({'value': round(amount, 2), 'confidence': base_conf})
                except ValueError:
                    continue
        
        if amounts:
            # Return largest amount with its confidence
            best = max(amounts, key=lambda x: x['value'])
            print(f"[DEBUG] Amount found (secondary): {best['value']} (confidence: {best['confidence']}%)")
            return best
        
        print("[DEBUG] No amount found")
        return {'value': None, 'confidence': 0}
    
    def extract_date(self, text):
        """Extract date with confidence scoring"""
        today = datetime.now()
        min_year = 2020
        max_year = 2030
        
        patterns_priority = [
            (r'(?:fecha|date|dia|ticket|operation)[^\d]*(20[2-4][0-9](?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01]))', 'code', 90),
            (r'(?:fecha|date|dia)[^\d]*(\d{1,2})[/-](\d{1,2})[/-](20[2-4][0-9])', 'dmy', 90),
            (r'(?:fecha|date|dia)[^\d]*(20[2-4][0-9])[/-](\d{1,2})[/-](\d{1,2})', 'ymd', 90),
        ]
        
        patterns_secondary = [
            (r'(20[2-4][0-9])[/-](\d{1,2})[/-](\d{1,2})', 'ymd', 70),
            (r'(\d{1,2})[/-](\d{1,2})[/-](20[2-4][0-9])', 'dmy', 70),
            (r'(\d{1,2})[/-](\d{1,2})[/-](2[0-9])', 'dmy', 60),
            (r'20[2-4][0-9](?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])', 'code', 50),
        ]
        
        # Try priority patterns
        for pattern, ptype, base_conf in patterns_priority:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if ptype == 'code':
                        date_str = matches[0]
                        date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    elif ptype == 'dmy':
                        day, month, year = matches[0]
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        year, month, day = matches[0]
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                    year_num = int(date_str[:4])
                    
                    if min_year <= year_num <= max_year and parsed_date <= today:
                        print(f"[DEBUG] Date found (priority): {date_str} (confidence: {base_conf}%)")
                        return {'value': date_str, 'confidence': base_conf}
                except:
                    continue
        
        # Try secondary patterns
        for pattern, ptype, base_conf in patterns_secondary:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if ptype == 'code':
                        date_str = match
                        date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    elif ptype == 'dmy':
                        day, month, year = match
                        if len(year) == 2:
                            year = '20' + year
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        year, month, day = match
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                    year_num = int(date_str[:4])
                    
                    if min_year <= year_num <= max_year and parsed_date <= today:
                        print(f"[DEBUG] Date found (secondary): {date_str} (confidence: {base_conf}%)")
                        return {'value': date_str, 'confidence': base_conf}
                except:
                    continue
        
        print("[DEBUG] No date found")
        return {'value': '1900-01-01', 'confidence': 0}
    
    def extract_title(self, text):
        """Extract title (merchant name) with confidence scoring"""
        lines = text.split('\n')
        
        # Try first 3 lines
        for i in range(min(3, len(lines))):
            line = lines[i].strip()
            if not line:
                continue
            
            # Clean line: remove numbers, special chars
            title = re.sub(r'\d+', '', line)
            title = re.sub(r'[^\w\s-]', '', title)
            title = ' '.join(title.split())
            
            # Valid title should have at least 3 chars
            if len(title) >= 3:
                confidence = 85 if i == 0 else (70 if i == 1 else 50)
                
                if len(title) > 50:
                    title = title[:50]
                
                print(f"[DEBUG] Title found: '{title}' (confidence: {confidence}%)")
                return {'value': title, 'confidence': confidence}
        
        print("[DEBUG] No title found")
        return {'value': 'Sin título', 'confidence': 0}
    
    def extract_category(self, text, title):
        """Extract/predict category based on keywords"""
        text_lower = (text + ' ' + title).lower()
        
        scores = {}
        for category, keywords in self.category_keywords.items():
            if category == 'Otros':
                continue
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            confidence = min(scores[best_category] * 30, 85)  # Scale confidence
            print(f"[DEBUG] Category predicted: {best_category} (confidence: {confidence}%)")
            return {'value': best_category, 'confidence': confidence}
        
        print("[DEBUG] No category predicted")
        return {'value': 'Otros', 'confidence': 30}
    
    def analyze_receipt(self, image_path):
        """
        Analyze receipt with multi-engine OCR and confidence scoring.
        Returns extracted fields with individual confidence scores.
        """
        print(f"\n[DEBUG] ========== Analyzing: {image_path} ==========")
        
        # Extract text using best OCR engine
        ocr_result = self.extract_text_multi_engine(image_path)
        
        if not ocr_result['text'].strip():
            print("[DEBUG] No text extracted from image")
            return None
        
        text = ocr_result['text']
        print(f"[DEBUG] Text length: {len(text)} chars")
        print(f"[DEBUG] Text preview: {text[:200]}...")
        
        # Extract all fields with confidence
        amount_data = self.extract_amount(text)
        date_data = self.extract_date(text)
        title_data = self.extract_title(text)
        category_data = self.extract_category(text, title_data['value'])
        
        if not amount_data['value']:
            print("[DEBUG] Could not extract amount - analysis failed")
            return None
        
        # Calculate overall confidence (weighted average)
        weights = {'amount': 0.4, 'date': 0.2, 'title': 0.2, 'category': 0.2}
        overall_confidence = (
            amount_data['confidence'] * weights['amount'] +
            date_data['confidence'] * weights['date'] +
            title_data['confidence'] * weights['title'] +
            category_data['confidence'] * weights['category']
        )
        
        result = {
            'amount': amount_data['value'],
            'amount_confidence': amount_data['confidence'],
            'date': date_data['value'],
            'date_confidence': date_data['confidence'],
            'title': title_data['value'],
            'title_confidence': title_data['confidence'],
            'category': category_data['value'],
            'category_confidence': category_data['confidence'],
            'overall_confidence': round(overall_confidence, 1),
            'ocr_engine': ocr_result['engine'],
            'ocr_confidence': round(ocr_result['confidence'], 1),
            'raw_text': text
        }
        
        print(f"[DEBUG] ========== Analysis Complete (Overall: {result['overall_confidence']}%) ==========\n")
        
        return result
