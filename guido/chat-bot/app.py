from flask import Flask, render_template, request, jsonify
from datetime import datetime
import google.generativeai as genai
import requests
import os
import re
from dotenv import load_dotenv
from googletrans import Translator 
from openai import OpenAI 
# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)
translator = Translator()  

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

print(f"🔑 GEMINI_API_KEY cargada: {bool(GEMINI_API_KEY)}")
print(f"🔑 DEEPSEEK_API_KEY cargada: {bool(DEEPSEEK_API_KEY)}")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini configurado correctamente")
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")

responses = {
    "hola": "¡Hola! ¿En qué puedo ayudarte?",
    "qué puedes hacer": "Puedo responder preguntas con la ayuda de IA avanzada",
    "qué hora es": f"Son las {datetime.now().strftime('%H:%M')}",
    "cuéntame un chiste": "¿Qué dice un semáforo a otro? ¡No me mires, me estoy cambiando! 😆",
    "adiós": "¡Hasta luego! 💻",
    "default": "No entendí. ¿Puedes reformular tu pregunta?"
}

# ✅ FUNCIÓN MEJORADA PARA TRADUCIR TEXTO
def traducir_a_espanol(texto):
    """Traduce texto al español si está en inglés - DETECCIÓN MEJORADA"""
    try:
        if not texto or not isinstance(texto, str):
            return texto
        
        # Detección más agresiva de inglés
        palabras_ingles = [
            'the', 'is', 'are', 'and', 'of', 'in', 'to', 'for', 'with', 'that', 'this',
            'you', 'your', 'it', 'its', 'he', 'she', 'they', 'them', 'their', 'our', 'we',
            'what', 'when', 'where', 'why', 'how', 'which', 'who', 'whom', 'whose',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'can', 'may', 'might', 'must', 'shall', 'about', 'above', 'after', 'before',
            'between', 'into', 'through', 'during', 'including', 'until', 'upon', 'within'
        ]
        
        # Contar palabras en inglés de manera más precisa
        palabras_texto = re.findall(r'\b[a-z]+\b', texto.lower())
        total_palabras = len(palabras_texto)
        
        if total_palabras == 0:
            return texto
        
        count_ingles = sum(1 for palabra in palabras_texto if palabra in palabras_ingles)
        porcentaje_ingles = count_ingles / total_palabras
        
        print(f"🔍 Detección idioma: {count_ingles}/{total_palabras} palabras en inglés ({porcentaje_ingles:.2%})")
        
        # Si más del 30% son palabras en inglés, traducir
        if porcentaje_ingles > 0.1:
            print("🌍 Traduciendo de inglés a español...")
            traduccion = translator.translate(texto, dest='es')
            return traduccion.text
        
        return texto
        
    except Exception as e:
        print(f"⚠️ Error en traducción: {e}")
        return texto

# ✅ FUNCIÓN PARA LIMPIAR TEXTO
def limpiar_texto(texto):
    """Elimina caracteres especiales y formato no deseado"""
    if not texto or not isinstance(texto, str):
        return texto
    
    # 1. Eliminar markdown y caracteres especiales
    texto = re.sub(r'[\*\#\_\`\~\-\=]', ' ', texto)  # Elimina * # _ ` ~ - =
    texto = re.sub(r'\[.*?\]\(.*?\)', '', texto)     # Elimina [enlaces](url)
    
    # 2. Eliminar frases típicas de IAs
    frases_a_eliminar = [
        'as an ai', 'as a language model', 'i am an ai', 
        'please note that', 'keep in mind that', 'according to',
        'based on my knowledge', 'i should note', 'it\'s important to note',
        'here is', 'here are', 'for example', 'in summary',
        'in conclusion', 'additionally', 'furthermore', 'moreover'
    ]
    
    for frase in frases_a_eliminar:
        texto = re.sub(frase, '', texto, flags=re.IGNORECASE)
    
    # 3. Normalizar espacios y saltos de línea
    texto = re.sub(r'\s+', ' ', texto)  # Reemplazar múltiples espacios por uno
    texto = re.sub(r'\n\s*\n', '\n', texto)  # Reemplazar múltiples saltos de línea
    texto = texto.strip()
    
    # 4. Capitalizar primera letra
    if texto and texto[0].islower():
        texto = texto[0].upper() + texto[1:]
    
    # 5. Eliminar espacios alrededor de puntuación
    texto = re.sub(r'\s+([.,!?;:])', r'\1', texto)
    texto = re.sub(r'([.,!?;:])\s+', r'\1 ', texto)
    
    return texto

def ask_gemini(user_message):
    """Consulta real a Gemini con traducción y limpieza"""
    if not GEMINI_API_KEY:
        return "Gemini API Key no configurada."
    try:
        response = gemini_model.generate_content(user_message)
        text = response.text if hasattr(response, "text") else str(response)
        
        # ✅ Aplicar traducción y limpieza
        text = text.replace('[IA: gemini]', '').strip()
        text = traducir_a_espanol(text)
        text = limpiar_texto(text)
        
        return text
    except Exception as e:
        print(f"❌ Error consultando Gemini: {e}")
        return "Error consultando Gemini"

def ask_deepseek(user_message):
    """Consulta real a DeepSeek con traducción y limpieza"""
    if not DEEPSEEK_API_KEY:
        return "DeepSeek API Key no configurada."
    try:
        url = "https://openrouter.ai/api/v1"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        text = result["choices"][0]["message"]["content"]
        
        # ✅ Aplicar traducción y limpieza
        text = traducir_a_espanol(text)
        text = limpiar_texto(text)
        
        return text
    except Exception as e:
        print(f"❌ Error consultando DeepSeek: {e}")
        return "Error consultando DeepSeek"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    try:
        user_message = request.form['message'].lower()
        ai_selected = request.form.get('ai_type', 'auto')
        
        print(f"📩 Mensaje recibido: '{user_message}'")
        print(f"🎯 IA seleccionada: '{ai_selected}'")
       
        for key in responses:
            if key in user_message:
                print(f"✅ Usando respuesta predefinida para: {key}")
                return jsonify({'response': responses[key]})
        
        bot_response = None
        
        if ai_selected == 'predefinido':
            print("🔧 Modo predefinido seleccionado")
            bot_response = responses['default']
        
        elif ai_selected == 'gemini':
            print("🔧 Solicitando Gemini...")
            bot_response = ask_gemini(user_message)
        
        elif ai_selected == 'deepseek':
            print("🔧 Solicitando DeepSeek...")
            bot_response = ask_deepseek(user_message)
        
        else:  # Modo automático
            print("🔧 Modo automático... usando Gemini")
            bot_response = ask_gemini(user_message)
        
        print(f"📤 Enviando respuesta: {bot_response}")
        return jsonify({'response': bot_response})
        
    except Exception as e:
        print(f"💥 Error grave: {e}")
        return jsonify({'response': "Error interno del servidor"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)