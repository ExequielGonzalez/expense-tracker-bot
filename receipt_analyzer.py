import re
import pytesseract
from PIL import Image
from datetime import datetime
import os

class ReceiptAnalyzer:
    def __init__(self):
        pass
    
    def preprocess_image(self, image_path):
        img = Image.open(image_path)
        
        img = img.convert('L')
        
        img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
        
        return img
    
    def extract_text(self, image_path):
        try:
            img = self.preprocess_image(image_path)
            text = pytesseract.image_to_string(img, lang='spa+eng')
            print(f"[DEBUG] Longitud del texto extraído: {len(text)} caracteres")
            print(f"[DEBUG] Texto extraído (primeros 1000): {text[:1000]}...")
            return text
        except Exception as e:
            print(f"[DEBUG] Error extracting text: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def extract_amount(self, text):
        patterns_priority = [
            r'IMPORTE\s*TARJETA[^\d]*(\d+[.,]\d{2})',
            r'IMPORTE\s*PAGADO[^\d]*(\d+[.,]\d{2})',
            r'TOTAL\s*A\s*PAGAR[^\d€]*(\d+[.,]\d{2})',
        ]
        
        patterns_secondary = [
            r'TOTAL\s*(?:DE\s*COMPRA|COMPRA)[^\d€]*(\d+[.,]\d{2})',
            r'TOTAL[^\d€]*(\d+[.,]\d{2})',
            r'IMPORTE[^\d€]*(\d+[.,]\d{2})',
        ]
        
        print(f"[DEBUG] Buscando montos en el texto...")
        
        for pattern in patterns_priority:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            print(f"[DEBUG] Patrón prioridad {pattern}: {matches}")
            if matches:
                for match in matches:
                    clean_amount = match.replace('.', '').replace(',', '.')
                    try:
                        amount = float(clean_amount)
                        if amount > 0 and amount < 10000:
                            print(f"[DEBUG] Monto detectado (prioridad): {amount}")
                            return amount
                    except ValueError:
                        continue
        
        amounts = []
        for pattern in patterns_secondary:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            print(f"[DEBUG] Patrón secundario {pattern}: {matches}")
            for match in matches:
                clean_amount = match.replace('.', '').replace(',', '.')
                try:
                    amount = float(clean_amount)
                    if amount > 0 and amount < 10000:
                        amounts.append(amount)
                except ValueError:
                    continue
        
        print(f"[DEBUG] Montos válidos encontrados: {amounts}")
        if amounts:
            return max(amounts)
        
        return None
    
    def extract_date(self, text):
        today = datetime.now()
        min_year = 2020
        max_year = 2030
        
        patterns_priority = [
            (r'(?:fecha|date|dia|ticket|operation)[^\d]*(20[2-4][0-9](?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01]))', 'code'),
            (r'(?:fecha|date|dia)[^\d]*(\d{1,2})[/-](\d{1,2})[/-](20[2-4][0-9])', 'dmy'),
            (r'(?:fecha|date|dia)[^\d]*(20[2-4][0-9])[/-](\d{1,2})[/-](\d{1,2})', 'ymd'),
        ]
        
        patterns_secondary = [
            (r'(20[2-4][0-9])[/-](\d{1,2})[/-](\d{1,2})', 'ymd'),
            (r'(\d{1,2})[/-](\d{1,2})[/-](20[2-4][0-9])', 'dmy'),
            (r'(\d{1,2})[/-](\d{1,2})[/-](2[0-9])', 'dmy'),
            (r'20[2-4][0-9](?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])', 'code'),
        ]
        
        print(f"[DEBUG] Buscando fecha en el texto (año válido: {min_year}-{max_year})...")
        
        for pattern, ptype in patterns_priority:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"[DEBUG] Patrón prioridad fecha: {matches[:3]}")
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
                        print(f"[DEBUG] Fecha detectada (prioridad): {date_str}")
                        return date_str
                except:
                    continue
        
        for pattern, ptype in patterns_secondary:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"[DEBUG] Patrón secundario fecha: {matches[:3]}")
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
                            print(f"[DEBUG] Fecha detectada (secundario): {date_str}")
                            return date_str
                    except:
                        continue
        
        print(f"[DEBUG] No se pudo detectar fecha válida (año {min_year}-{max_year}), marcando sin fecha")
        return '1900-01-01'
    
    def extract_title(self, text):
        lines = text.split('\n')
        title = lines[0].strip() if lines else 'Ticket sin título'
        
        title = re.sub(r'\d+', '', title)
        title = ' '.join(title.split())
        
        if len(title) > 50:
            title = title[:50]
        
        print(f"[DEBUG] Título detectado: {title}")
        return title
    
    def analyze_receipt(self, image_path):
        text = self.extract_text(image_path)
        
        if not text.strip():
            return None
        
        amount = self.extract_amount(text)
        date = self.extract_date(text)
        title = self.extract_title(text)
        
        if amount:
            return {
                'amount': round(amount, 2),
                'date': date,
                'title': title,
                'raw_text': text
            }
        
        return None
