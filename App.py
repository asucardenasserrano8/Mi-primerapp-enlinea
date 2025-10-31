# App.py
import streamlit as st
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import time
import google.generativeai as genai
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import numpy as np
import io
import base64
import random
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import os
import pycountry
from geopy.geocoders import Nominatim
import requests


# Cargar variables de entorno
load_dotenv()

# Configuración de la página (debe ser lo primero)
st.set_page_config(page_title="Análisis de Acciones", layout="wide")

GOOGLE_KEY = os.getenv("AP")

genai.configure(api_key=GOOGLE_KEY)

currencyapi = os.getenv("AP1")

# CSS personalizado mejorado
st.markdown("""
<style>
    /* Estilos para botones seleccionados */
    .stButton > button {
        border: 2px solid #cccccc;
        background-color: white;
        color: black;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        border-color: #adb5bd;
        background-color: #f8f9fa;
    }
    
    /* Botón seleccionado */
    .stButton > button.selected {
        border: 3px solid #28a745 !important;
        background-color: #d4edda !important;
        color: #155724 !important;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
    }
    
    /* Indicadores de métricas */
    .metric-positive {
        color: #28a745;
        font-weight: bold;
    }
    
    .metric-negative {
        color: #dc3545;
        font-weight: bold;
    }
    
    .metric-neutral {
        color: #ffc107;
        font-weight: bold;
    }
    
    /* Tarjetas de información */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    
    /* Estilos para educación financiera */
    .concept-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        border-left: 5px solid #ff6b6b;
    }
    
    .macro-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización de session_state
if 'seccion_actual' not in st.session_state:
    st.session_state.seccion_actual = "info"

if 'favoritas' not in st.session_state:
    st.session_state.favoritas = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]

if 'portafolio' not in st.session_state:
    st.session_state.portafolio = {}

if 'historial_busquedas' not in st.session_state:
    st.session_state.historial_busquedas = []

# FUNCIONES NUEVAS CACHED
@st.cache_data(ttl=3600)
def obtener_datos_accion(ticker):
    try:
        return yf.download(ticker, period="1y")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def obtener_info_completa(ticker):
    try:
        return yf.Ticker(ticker).info
    except:
        return {}

# FUNCIÓN CON API DE WIKIPEDIA - CONTENIDO COMPLETO MEJORADO
@st.cache_data(ttl=3600)
def obtener_info_wikipedia(ticker, nombre_empresa):
    """
    Obtiene información de Wikipedia usando la API oficial - CONTENIDO COMPLETO MEJORADO
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # PRIMERO: Usar la API de búsqueda de Wikipedia para encontrar la página correcta
        search_url = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={nombre_empresa}&format=json&srlimit=5"
        
        search_response = requests.get(search_url, headers=headers, timeout=10)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            
            if search_data['query']['search']:
                # Tomar el primer resultado que parezca relevante
                for result in search_data['query']['search']:
                    title = result['title']
                    
                    # Verificar que el título sea relevante (contenga palabras clave de la empresa)
                    if any(keyword in title.lower() for keyword in ['inc', 'corp', 'company', 'corporation', nombre_empresa.split()[0].lower()]):
                        # Obtener el contenido COMPLETO de la página usando la API
                        content_url = f"https://es.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=true&titles={title}&format=json"
                        content_response = requests.get(content_url, headers=headers, timeout=10)
                        
                        if content_response.status_code == 200:
                            content_data = content_response.json()
                            pages = content_data['query']['pages']
                            
                            for page_id, page_data in pages.items():
                                if 'extract' in page_data and page_data['extract']:
                                    contenido = page_data['extract']
                                    
                                    # LIMPIAR EL FORMATO DE TÍTULOS
                                    contenido_limpio = limpiar_formato_wikipedia(contenido)
                                    
                                    return {
                                        'encontrado': True,
                                        'contenido': contenido_limpio,
                                        'url': f"https://es.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                        'termino_busqueda': title,
                                        'fuente': 'API Wikipedia'
                                    }
        
        # SEGUNDO: Intentar con búsqueda en inglés
        search_url_english = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={nombre_empresa}&format=json&srlimit=5"
        
        search_response_english = requests.get(search_url_english, headers=headers, timeout=10)
        
        if search_response_english.status_code == 200:
            search_data_english = search_response_english.json()
            
            if search_data_english['query']['search']:
                for result in search_data_english['query']['search']:
                    title = result['title']
                    
                    if any(keyword in title.lower() for keyword in ['inc', 'corp', 'company', 'corporation', nombre_empresa.split()[0].lower()]):
                        content_url_english = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=true&titles={title}&format=json"
                        content_response_english = requests.get(content_url_english, headers=headers, timeout=10)
                        
                        if content_response_english.status_code == 200:
                            content_data_english = content_response_english.json()
                            pages_english = content_data_english['query']['pages']
                            
                            for page_id, page_data in pages_english.items():
                                if 'extract' in page_data and page_data['extract']:
                                    contenido_ingles = page_data['extract']
                                    
                                    # LIMPIAR EL FORMATO PRIMERO
                                    contenido_ingles_limpio = limpiar_formato_wikipedia(contenido_ingles)
                                    
                                    # Traducir con Gemini - CONTENIDO COMPLETO
                                    try:
                                        prompt_traduccion = f"""
                                        Traduce al español el siguiente texto sobre una empresa manteniendo un tono formal.
                                        Conserva términos técnicos y financieros sin cambios.
                                        Traduce TODO el texto completo sin omitir nada.
                                        
                                        Texto: {contenido_ingles_limpio}
                                        """
                                        
                                        response_traduccion = genai.models.generate_content(
                                            model="gemini-2.5-flash",
                                            contents=prompt_traduccion
                                        )
                                        
                                        contenido_traducido = response_traduccion.text
                                        
                                        return {
                                            'encontrado': True,
                                            'contenido': contenido_traducido,
                                            'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                            'termino_busqueda': title,
                                            'fuente': 'API Wikipedia Inglés (Traducido)'
                                        }
                                    except:
                                        # Si falla la traducción, devolver en inglés COMPLETO
                                        return {
                                            'encontrado': True,
                                            'contenido': contenido_ingles_limpio,
                                            'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                            'termino_busqueda': title,
                                            'fuente': 'API Wikipedia Inglés'
                                        }
        
        return {'encontrado': False, 'error': 'No se encontró información en Wikipedia'}
            
    except Exception as e:
        return {'encontrado': False, 'error': f'Error: {str(e)}'}

# NUEVA FUNCIÓN PARA LIMPIAR Y FORMATEAR EL CONTENIDO DE WIKIPEDIA
def limpiar_formato_wikipedia(texto):
    """
    Limpia el formato de markdown de Wikipedia y convierte los títulos a formato Markdown
    """
    if not texto:
        return texto
    
    lineas = texto.split('\n')
    lineas_limpias = []
    
    for linea in lineas:
        linea_limpia = linea.strip()
        if not linea_limpia:
            continue
            
        # Detectar títulos con === Título ===
        if linea_limpia.startswith('===') and linea_limpia.endswith('==='):
            # Es un título principal (### en Markdown)
            titulo = linea_limpia.replace('===', '').strip()
            if titulo:
                lineas_limpias.append(f"### {titulo}")
                
        # Detectar subtítulos con == Título ==
        elif linea_limpia.startswith('==') and linea_limpia.endswith('=='):
            # Es un subtítulo (## en Markdown)
            subtitulo = linea_limpia.replace('==', '').strip()
            if subtitulo:
                lineas_limpias.append(f"## {subtitulo}")
                
        else:
            # Texto normal
            lineas_limpias.append(linea_limpia)
    
    return '\n\n'.join(lineas_limpias)

# FUNCIÓN PARA OBTENER RATING DE ANALISTAS
def obtener_rating_analistas(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        ratings = {
            'recommendationMean': info.get('recommendationMean', 'N/A'),
            'recommendationKey': info.get('recommendationKey', 'N/A'),
            'targetMeanPrice': info.get('targetMeanPrice', 'N/A'),
            'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions', 'N/A')
        }
        return ratings
    except:
        return {}

# FUNCIÓN PARA ANÁLISIS TÉCNICO CORREGIDA
def calcular_indicadores_tecnicos(data):
    if data.empty:
        return data
    
    # Crear una copia para no modificar el original
    data_tech = data.copy()
    
    # Asegurarnos de que tenemos la columna Close
    if 'Close' not in data_tech.columns:
        st.error("No se encuentra la columna 'Close' en los datos")
        return data_tech
    
    try:
        # RSI
        delta = data_tech['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data_tech['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = data_tech['Close'].ewm(span=12, adjust=False).mean()
        exp26 = data_tech['Close'].ewm(span=26, adjust=False).mean()
        data_tech['MACD'] = exp12 - exp26
        data_tech['MACD_Signal'] = data_tech['MACD'].ewm(span=9, adjust=False).mean()
        data_tech['MACD_Histogram'] = data_tech['MACD'] - data_tech['MACD_Signal']
        
        # Bandas de Bollinger
        data_tech['BB_Middle'] = data_tech['Close'].rolling(window=20).mean()
        bb_std = data_tech['Close'].rolling(window=20).std()
        data_tech['BB_Upper'] = data_tech['BB_Middle'] + (bb_std * 2)
        data_tech['BB_Lower'] = data_tech['BB_Middle'] - (bb_std * 2)
        
        # Medias Móviles
        data_tech['SMA_20'] = data_tech['Close'].rolling(window=20).mean()
        data_tech['SMA_50'] = data_tech['Close'].rolling(window=50).mean()
        data_tech['SMA_200'] = data_tech['Close'].rolling(window=200).mean()
        
        return data_tech
        
    except Exception as e:
        st.error(f"Error calculando indicadores: {str(e)}")
        return data_tech

# FUNCIÓN PARA SCORING AUTOMÁTICO
def calcular_scoring_fundamental(info):
    score = 0
    max_score = 100
    metricas = {}
    
    # P/E Ratio (15 puntos)
    pe = info.get('trailingPE', 0)
    if pe and pe > 0:
        if pe < 15:
            score += 15
            metricas['P/E'] = '🟢 Excelente'
        elif pe < 25:
            score += 10
            metricas['P/E'] = '🟡 Bueno'
        else:
            score += 5
            metricas['P/E'] = '🔴 Alto'
    
    # ROE (15 puntos)
    roe = info.get('returnOnEquity', 0)
    if roe and roe > 0:
        if roe > 0.15:
            score += 15
            metricas['ROE'] = '🟢 Excelente'
        elif roe > 0.08:
            score += 10
            metricas['ROE'] = '🟡 Bueno'
        else:
            score += 5
            metricas['ROE'] = '🔴 Bajo'
    
    # Deuda/Equity (15 puntos)
    deuda_eq = info.get('debtToEquity', 0)
    if deuda_eq and deuda_eq > 0:
        if deuda_eq < 0.5:
            score += 15
            metricas['Deuda/Equity'] = '🟢 Excelente'
        elif deuda_eq < 1.0:
            score += 10
            metricas['Deuda/Equity'] = '🟡 Bueno'
        else:
            score += 5
            metricas['Deuda/Equity'] = '🔴 Alto'
    
    # Margen Beneficio (15 puntos)
    margen = info.get('profitMargins', 0)
    if margen and margen > 0:
        if margen > 0.2:
            score += 15
            metricas['Margen Beneficio'] = '🟢 Excelente'
        elif margen > 0.1:
            score += 10
            metricas['Margen Beneficio'] = '🟡 Bueno'
        else:
            score += 5
            metricas['Margen Beneficio'] = '🔴 Bajo'
    
    # Crecimiento Ingresos (20 puntos)
    crecimiento = info.get('revenueGrowth', 0)
    if crecimiento and crecimiento > 0:
        if crecimiento > 0.15:
            score += 20
            metricas['Crecimiento Ingresos'] = '🟢 Excelente'
        elif crecimiento > 0.08:
            score += 15
            metricas['Crecimiento Ingresos'] = '🟡 Bueno'
        else:
            score += 8
            metricas['Crecimiento Ingresos'] = '🔴 Bajo'
    
    # Rating Analistas (20 puntos)
    rating_mean = info.get('recommendationMean', 3)
    if rating_mean and rating_mean > 0:
        if rating_mean < 2:
            score += 20
            metricas['Rating Analistas'] = '🟢 Fuerte Compra'
        elif rating_mean < 3:
            score += 15
            metricas['Rating Analistas'] = '🟡 Compra'
        else:
            score += 8
            metricas['Rating Analistas'] = '🔴 Neutral/Venta'
    
    return min(score, max_score), metricas

# FUNCIÓN PARA GENERAR REPORTE SIMPLIFICADO (SIN PDF)
def generar_reporte_texto(ticker, info, datos, scoring, metricas):
    reporte = f"""
    REPORTE DE ANÁLISIS: {ticker}
    Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    INFORMACIÓN BÁSICA:
    - Nombre: {info.get('longName', 'N/A')}
    - Sector: {info.get('sector', 'N/A')}
    - Industria: {info.get('industry', 'N/A')}
    
    SCORING FUNDAMENTAL: {scoring}/100
    
    MÉTRICAS:
    """
    
    for metrica, valor in metricas.items():
        reporte += f"- {metrica}: {valor}\n"
    
    if not datos.empty:
        precio_actual = datos['Close'].iloc[-1]
        precio_min = datos['Close'].min()
        precio_max = datos['Close'].max()
        reporte += f"""
    DATOS DE PRECIO:
    - Precio Actual: ${precio_actual:.2f}
    - Precio Mínimo (1 año): ${precio_min:.2f}
    - Precio Máximo (1 año): ${precio_max:.2f}
        """
    
    return reporte

# FUNCIÓN PARA DETECTOR DE TENDENCIAS
def analizar_tendencias(data):
    if data.empty or 'Close' not in data.columns:
        return {"tendencia": "No disponible", "confianza": 0, "detalles": {}}
    
    try:
        # Calcular medias móviles
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        # Obtener últimos valores
        precio_actual = data['Close'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]
        sma_200 = data['SMA_200'].iloc[-1]
        
        # Calcular RSI para momentum
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_actual = rsi.iloc[-1]
        
        # Análisis de tendencia
        tendencia_alcista = 0
        tendencia_bajista = 0
        
        # 1. Análisis de medias móviles (40%)
        if precio_actual > sma_20 > sma_50 > sma_200:
            tendencia_alcista += 40
        elif precio_actual < sma_20 < sma_50 < sma_200:
            tendencia_bajista += 40
        
        # 2. Posición respecto a medias (30%)
        if precio_actual > sma_20:
            tendencia_alcista += 15
        else:
            tendencia_bajista += 15
            
        if precio_actual > sma_50:
            tendencia_alcista += 10
        else:
            tendencia_bajista += 10
            
        if precio_actual > sma_200:
            tendencia_alcista += 5
        else:
            tendencia_bajista += 5
        
        # 3. Momentum RSI (30%)
        if rsi_actual > 50:
            tendencia_alcista += 30
        else:
            tendencia_bajista += 30
        
        # Determinar tendencia principal
        if tendencia_alcista > tendencia_bajista:
            tendencia = "ALCISTA"
            confianza = min(100, tendencia_alcista)
        elif tendencia_bajista > tendencia_alcista:
            tendencia = "BAJISTA"
            confianza = min(100, tendencia_bajista)
        else:
            tendencia = "LATERAL"
            confianza = 50
        
        detalles = {
            "precio_actual": precio_actual,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "rsi": rsi_actual,
            "puntos_alcista": tendencia_alcista,
            "puntos_bajista": tendencia_bajista
        }
        
        return {
            "tendencia": tendencia,
            "confianza": confianza,
            "detalles": detalles
        }
        
    except Exception as e:
        return {"tendencia": "Error en análisis", "confianza": 0, "detalles": {}}

# FUNCIÓN PARA OBTENER DATOS MACROECONÓMICOS
def obtener_datos_macro():
    # Datos macroeconómicos simulados (en una app real, esto vendría de APIs)
    datos_macro = {
        "indicadores_usa": {
            "Inflación (CPI)": "3.2%",
            "Tasa de Desempleo": "3.8%",
            "Crecimiento PIB": "2.1%",
            "Tasa de Interés Fed": "5.25%-5.50%",
            "Confianza del Consumidor": "64.9"
        },
        "mercados_globales": {
            "S&P 500": "+15% YTD",
            "NASDAQ": "+22% YTD",
            "Dow Jones": "+12% YTD",
            "Euro Stoxx 50": "+8% YTD",
            "Nikkei 225": "+18% YTD"
        },
        "materias_primas": {
            "Petróleo (WTI)": "$78.50",
            "Oro": "$1,950.00",
            "Plata": "$23.15",
            "Cobre": "$3.85",
            "Bitcoin": "$42,000"
        },
        "divisas": {
            "EUR/USD": "1.0850",
            "USD/JPY": "148.50",
            "GBP/USD": "1.2650",
            "USD/MXN": "17.20",
            "DXY (Índice Dólar)": "103.50"
        }
    }
    return datos_macro

# INTERFAZ PRINCIPAL
stonk = st.text_input("Ingrese el nombre del símbolo de la acción", value="MSFT")

# Agregar a historial de búsquedas
if stonk and stonk not in st.session_state.historial_busquedas:
    st.session_state.historial_busquedas.append(stonk)
    if len(st.session_state.historial_busquedas) > 10:
        st.session_state.historial_busquedas.pop(0)

end_date = datetime.today()
start_date = end_date - timedelta(days=5 * 365)

# Yahoo finanzas trae los datos del Ticker
try:
    ticker = yf.Ticker(stonk)
    info = ticker.info
    nombre = info.get("longName", "Ese nombre no existe")
    descripcion = info.get("longBusinessSummary", "No hay datos")
except Exception as e:
    st.error(f"❌ Error al cargar datos de {stonk}: {str(e)}")
    st.stop()

# BOTONES MEJORADOS CON NUEVA DISTRIBUCIÓN
st.write("### 📊 Selecciona qué información quieres ver:")

# Primera fila: 5 botones
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🏢 Información", use_container_width=True, key="btn_info", 
                type="primary" if st.session_state.seccion_actual == "info" else "secondary"):
        st.session_state.seccion_actual = "info"

with col2:    
    if st.button("📈 Variación del precio", use_container_width=True, key="btn_datos", 
                type="primary" if st.session_state.seccion_actual == "datos" else "secondary"):
        st.session_state.seccion_actual = "datos"

with col3:
    if st.button("💰 Datos fundamentales", use_container_width=True, key="btn_fundamentales", 
                type="primary" if st.session_state.seccion_actual == "fundamentales" else "secondary"):
        st.session_state.seccion_actual = "fundamentales"

with col4:
    if st.button("📊 Análisis técnico", use_container_width=True, key="btn_tecnico", 
                type="primary" if st.session_state.seccion_actual == "tecnico" else "secondary"):
        st.session_state.seccion_actual = "tecnico"

with col5:
    if st.button("🤖 Análisis IA", use_container_width=True, key="btn_ia", 
                type="primary" if st.session_state.seccion_actual == "ia" else "secondary"):
        st.session_state.seccion_actual = "ia"

# Segunda fila: 4 botones
col6, col7, col8, col9 = st.columns(4)

with col6:
    if st.button("📊 Comparación", use_container_width=True, key="btn_comparar", 
                type="primary" if st.session_state.seccion_actual == "comparar" else "secondary"):
        st.session_state.seccion_actual = "comparar"

with col7:
    if st.button("📰 Noticias", use_container_width=True, key="btn_noticias", 
                type="primary" if st.session_state.seccion_actual == "noticias" else "secondary"):
        st.session_state.seccion_actual = "noticias"

with col8:
    if st.button("🔍 Buscador", use_container_width=True, key="btn_screener", 
                type="primary" if st.session_state.seccion_actual == "screener" else "secondary"):
        st.session_state.seccion_actual = "screener"

# En la sección de botones (después del botón de Macroeconomía), agrega:
with col9:
    if st.button("🌍 Macroeconomía", use_container_width=True, key="btn_macro", 
                type="primary" if st.session_state.seccion_actual == "macro" else "secondary"):
        st.session_state.seccion_actual = "macro"

# Agrega un décimo botón para Mercados Globales
col10 = st.columns(1)[0]  # Crear una nueva columna
with col10:
    if st.button("📈 Mercados Globales", use_container_width=True, key="btn_global", 
                type="primary" if st.session_state.seccion_actual == "global" else "secondary"):
        st.session_state.seccion_actual = "global"

# Línea separadora
st.markdown("---")

# SECCIÓN DE INFORMACIÓN PRINCIPAL
if st.session_state.seccion_actual == "info":
    st.header(f"🏢 Información de {nombre}")
    
    # Rating de analistas
    ratings = obtener_rating_analistas(stonk)
    if ratings:
        st.subheader("🎯 Rating de Analistas")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            reco_key = ratings.get('recommendationKey', 'N/A')
            if isinstance(reco_key, str):
                reco_display = reco_key.upper().replace("_", " ")
            else:
                reco_display = "N/A"
            
            st.metric("Recomendación", reco_display)
        
        with col2:
            target_price = ratings.get('targetMeanPrice', 'N/A')
            current_price = info.get('currentPrice', 0)
            if target_price != 'N/A' and current_price and target_price > current_price:
                st.metric("Target Price", f"${target_price:.2f}", f"+{((target_price/current_price)-1)*100:.1f}%")
            elif target_price != 'N/A':
                st.metric("Target Price", f"${target_price:.2f}")
            else:
                st.metric("Target Price", "N/A")
        
        with col3:
            st.metric("Rating Medio", f"{ratings.get('recommendationMean', 'N/A')}/5")
        
        with col4:
            st.metric("# Analistas", ratings.get('numberOfAnalystOpinions', 'N/A'))
    
    # Descripción traducida
    prompt = f"""
    Te voy a dar la descripción en inglés de una empresa que cotiza en bolsa, necesito que traduzcas la descripción a español financiero formal,
    quiero que la traducción sea lo más apegado posible a la descripción original y que me entregues el texto en exactamente 500 caracteres, te paso la
    descripción de la empresa: {descripcion}
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        texto_traducido = response.text

    except Exception as e:
        texto_traducido = "Traducción no disponible por el momento."
    
    st.subheader("📋 Descripción de la Empresa")
    st.write(texto_traducido)
    
    # INFORMACIÓN DE WIKIPEDIA PARA CUALQUIER ACCIÓN
    st.subheader("📚 Información Corporativa")

    # Obtener información de Wikipedia
    with st.spinner('Buscando información en Wikipedia...'):
        info_wikipedia = obtener_info_wikipedia(stonk, nombre)

        if info_wikipedia.get('encontrado', False):
            # MOSTRAR DIRECTAMENTE CON MARKDOWN SIN EL CUADRO HTML
            st.markdown(info_wikipedia['contenido'])
            
            # Mostrar fuente
            st.caption(f"📖 Fuente: {info_wikipedia['fuente']} - [Enlace a Wikipedia]({info_wikipedia['url']})")
            
        else:
            st.info("""
            ℹ️ **Información de Wikipedia no disponible**
                
            No se pudo encontrar información específica de Wikipedia para esta empresa. 
            Esto puede deberse a:
            - La empresa tiene un nombre diferente en Wikipedia
            - La empresa es muy nueva o poco conocida
            - Problemas de conexión temporal
                
            **La información financiera y de análisis sigue disponible en las demás secciones.**
            """)
    
    # Información adicional básica
    st.subheader("📊 Información Básica")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sector = info.get("sector", "N/A")
        st.metric("Sector", sector)
        employees = info.get("fullTimeEmployees", "N/A")
        if employees != "N/A":
            st.metric("Empleados", f"{employees:,}")
        else:
            st.metric("Empleados", "N/A")
    
    with col2:
        industry = info.get("industry", "N/A")
        st.metric("Industria", industry)
        country = info.get("country", "N/A")
        st.metric("País", country)
    
    with col3:
        market_cap = info.get("marketCap", "N/A")
        if market_cap != "N/A":
            st.metric("Market Cap", f"${market_cap/1e9:.2f}B")
        else:
            st.metric("Market Cap", "N/A")
        
        currency = info.get("currency", "N/A")
        st.metric("Moneda", currency)
    
    with col4:
        pe_ratio = info.get("trailingPE", "N/A")
        if pe_ratio != "N/A":
            st.metric("P/E Ratio", f"{pe_ratio:.2f}")
        else:
            st.metric("P/E Ratio", "N/A")
        
        dividend_yield = info.get("dividendYield", "N/A")
        if dividend_yield and dividend_yield != "N/A":
            st.metric("Dividend Yield", f"{dividend_yield*100:.2f}%")
        else:
            st.metric("Dividend Yield", "N/A")
            
    # Línea separadora
    st.markdown("---")

    # INFORMACIÓN DE WIKIPEDIA (AHORA AL FINAL)
    st.subheader("📚 Información Corporativa")

    # Obtener información de Wikipedia
    with st.spinner('Buscando información en Wikipedia...'):
        info_wikipedia = obtener_info_wikipedia(stonk, nombre)

        if info_wikipedia.get('encontrado', False):
            # MOSTRAR DIRECTAMENTE CON MARKDOWN SIN EL CUADRO HTML
            st.markdown(info_wikipedia['contenido'])
            
            # Mostrar fuente
            st.caption(f"📖 Fuente: {info_wikipedia['fuente']} - [Enlace a Wikipedia]({info_wikipedia['url']})")
            
        else:
            st.info("""
            ℹ️ **Información no disponible**
                
            No se pudo encontrar información específica de esta empresa. 
            """)

# SECCIÓN DE DATOS CON DETECTOR DE TENDENCIAS (MODIFICADA)
elif st.session_state.seccion_actual == "datos":
    st.header(f"📊 Variación del Precio y Gráfica de Velas de {nombre}")
    
    # MÉTRICAS DE PRECIO
    st.subheader(f"📊 Métricas de Precio - Período Actual")
    
    try:
        # Descargar datos de yfinance (por defecto 5 años para las métricas iniciales)
        start_date_default = end_date - timedelta(days=5 * 365)
        data = yf.download(stonk, start=start_date_default.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval='1d')
        
        if data.empty:
            st.warning("No se encontraron datos para este símbolo")
        else:
            # Organizar datos
            data = data.reset_index()
            
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in data.columns.values]
            
            data.columns = [col.replace(f'_{stonk}', '') for col in data.columns]
            
            # MÉTRICAS VISUALES
            if 'Close' in data.columns:
                precio_actual = data['Close'].iloc[-1]
                precio_inicial = data['Close'].iloc[0]
                variacion_total = ((precio_actual - precio_inicial) / precio_inicial) * 100
                
                # Calcular variación del último día
                if len(data) > 1:
                    precio_anterior = data['Close'].iloc[-2]
                    variacion_diaria = ((precio_actual - precio_anterior) / precio_anterior) * 100
                else:
                    variacion_diaria = 0
                
                # Calcular máximo y mínimo del período
                precio_maximo = data['Close'].max()
                precio_minimo = data['Close'].min()
                
                # Calcular volatilidad (desviación estándar de los retornos diarios)
                retornos_diarios = data['Close'].pct_change().dropna()
                volatilidad = retornos_diarios.std() * 100  # En porcentaje
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Precio Inicial", f"${precio_inicial:.2f}")
                    st.metric("Precio Mínimo", f"${precio_minimo:.2f}")
                with col2:
                    st.metric("Precio Actual", f"${precio_actual:.2f}", f"{variacion_diaria:.2f}%")
                    st.metric("Precio Máximo", f"${precio_maximo:.2f}")
                with col3:
                    st.metric("Variación Total", f"{variacion_total:.2f}%")
                    st.metric("Volatilidad Anual", f"{volatilidad:.2f}%")
                with col4:
                    st.metric("Período", "5 Años")
                    st.metric("Días Analizados", len(data))
            
            # Selector de período
            st.subheader("📅 Selecciona el período de análisis")
            
            periodo_opciones = {
                "1 Mes": 30,
                "3 Meses": 90,
                "6 Meses": 180,
                "1 Año": 365,
                "3 Años": 3 * 365,
                "5 Años": 5 * 365,
                "Máximo": None  # Para datos máximos disponibles
            }
            
            periodo_seleccionado = st.selectbox(
                "Período:",
                options=list(periodo_opciones.keys()),
                index=5,  # 5 Años por defecto
                key="selector_periodo"
            )
            
            # Calcular fecha de inicio según el período seleccionado
            if periodo_opciones[periodo_seleccionado] is None:
                # Para período máximo, usar una fecha muy antigua
                start_date = datetime(2000, 1, 1)
                periodo_texto = "Máximo"
            else:
                start_date = end_date - timedelta(days=periodo_opciones[periodo_seleccionado])
                periodo_texto = periodo_seleccionado
            
            # Descargar datos de yfinance
            data_periodo = yf.download(stonk, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval='1d')
            
            if not data_periodo.empty:
                data_periodo = data_periodo.reset_index()
                if isinstance(data_periodo.columns, pd.MultiIndex):
                    data_periodo.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in data_periodo.columns.values]
                data_periodo.columns = [col.replace(f'_{stonk}', '') for col in data_periodo.columns]
            
            # Línea separadora entre métricas y gráfica
            st.markdown("---")
            
            # GRÁFICA DE VELAS
            st.subheader(f"📈 Gráfica de Velas - Período: {periodo_texto}")
            
            # Función para obtener nombres de columnas dinámicamente
            def get_column_name(data, prefix):
                for col in data.columns:
                    if col.startswith(prefix):
                        return col
                return None
            
            if not data_periodo.empty:
                # Obtener los nombres dinámicos de las columnas
                open_col = get_column_name(data_periodo, 'Open')
                high_col = get_column_name(data_periodo, 'High') 
                low_col = get_column_name(data_periodo, 'Low')
                close_col = get_column_name(data_periodo, 'Close')
                date_col = get_column_name(data_periodo, 'Date')
                
                # Gráfica de velas
                if all(col is not None for col in [open_col, high_col, low_col, close_col, date_col]):
                    fig = go.Figure(data=[go.Candlestick(
                        x=data_periodo[date_col],
                        open=data_periodo[open_col],
                        high=data_periodo[high_col],
                        low=data_periodo[low_col],
                        close=data_periodo[close_col],
                        increasing_line_color='green',
                        decreasing_line_color='red',
                        name=stonk
                    )])
                    
                    fig.update_layout(
                        title=f'Gráfica de velas de {stonk}',
                        xaxis_title='Fecha',
                        yaxis_title='Precio (USD)',
                        xaxis_rangeslider_visible=False,
                        height=600
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.warning("No se pudieron cargar los datos para la gráfica de velas")
            
                # DETECTOR DE TENDENCIAS (NUEVO)
                st.markdown("---")
                st.subheader("🔍 Detector de Tendencias")
                
                # Analizar tendencias
                analisis_tendencia = analizar_tendencias(data_periodo)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if analisis_tendencia["tendencia"] == "ALCISTA":
                        st.success(f"📈 Tendencia: {analisis_tendencia['tendencia']}")
                    elif analisis_tendencia["tendencia"] == "BAJISTA":
                        st.error(f"📉 Tendencia: {analisis_tendencia['tendencia']}")
                    else:
                        st.warning(f"➡️ Tendencia: {analisis_tendencia['tendencia']}")
                    
                    st.metric("Confianza", f"{analisis_tendencia['confianza']}%")
                
                with col2:
                    if 'detalles' in analisis_tendencia:
                        detalles = analisis_tendencia['detalles']
                        if 'precio_actual' in detalles:
                            st.metric("Precio Actual", f"${detalles['precio_actual']:.2f}")
                        if 'rsi' in detalles:
                            rsi_color = "green" if detalles['rsi'] < 30 else "red" if detalles['rsi'] > 70 else "orange"
                            st.metric("RSI", f"{detalles['rsi']:.1f}")
                
                with col3:
                    if 'detalles' in analisis_tendencia:
                        detalles = analisis_tendencia['detalles']
                        if all(key in detalles for key in ['sma_20', 'sma_50', 'sma_200']):
                            st.write("**Medias Móviles:**")
                            st.write(f"SMA 20: ${detalles['sma_20']:.2f}")
                            st.write(f"SMA 50: ${detalles['sma_50']:.2f}")
                            st.write(f"SMA 200: ${detalles['sma_200']:.2f}")
                
                # Explicación de la tendencia
                with st.expander("📖 Explicación del Análisis de Tendencia"):
                    st.write("""
                    **Cómo se determina la tendencia:**
                    - **Medias Móviles (40%):** Analiza la posición del precio respecto a las medias de 20, 50 y 200 días
                    - **Posición Precio/Medias (30%):** Evalúa si el precio está por encima o debajo de las medias clave
                    - **Momentum RSI (30%):** Considera si el RSI indica fuerza compradora o vendedora
                    
                    **Interpretación:**
                    - 🟢 **ALCISTA:** Precio por encima de medias, RSI >50, medias alineadas ascendente
                    - 🔴 **BAJISTA:** Precio por debajo de medias, RSI <50, medias alineadas descendente  
                    - 🟡 **LATERAL:** Señales mixtas o sin dirección clara
                    """)
                
                # Línea separadora entre gráfica y tabla
                st.markdown("---")
                
                # TABLA DE DATOS HISTÓRICOS
                st.subheader(f"📋 Datos Históricos Del Período: {periodo_texto}")
                
                # Mostrar información resumida sobre los datos
                st.write(f"**Total de registros:** {len(data_periodo)} días")
                if date_col:
                    st.write(f"**Período:** {data_periodo[date_col].iloc[0].strftime('%d/%m/%Y')} - {data_periodo[date_col].iloc[-1].strftime('%d/%m/%Y')}")
                
                st.dataframe(data_periodo, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error al generar la gráfica: {str(e)}")

# SECCIÓN FUNDAMENTALES COMPLETA (UNIFICADA)
elif st.session_state.seccion_actual == "fundamentales":
    st.header(f"💰 Datos Fundamentales Completos - {nombre}")
    
    # Pestañas para Fundamentales
    tab1, tab2 = st.tabs(["📊 Análisis Fundamental", "🎓 Educación Financiera"])

    with tab1:
        # FUNCIONES PARA EXTRACCIÓN DE DATOS FUNDAMENTALES
        def extraer_tabla_finviz(ticker):
            url = f"https://finviz.com/quote.ashx?t={ticker}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extraer TODOS los datos de la tabla snapshot de Finviz
                    tabla_snapshot = soup.find('table', class_='snapshot-table2')
                    
                    if tabla_snapshot:
                        datos = {}
                        
                        # Extraer en el formato exacto de Finviz (pares clave-valor)
                        filas = tabla_snapshot.find_all('tr')
                        
                        for fila in filas:
                            celdas = fila.find_all('td')
                            for i in range(0, len(celdas) - 1, 2):
                                if i + 1 < len(celdas):
                                    clave = celdas[i].get_text(strip=True)
                                    valor = celdas[i + 1].get_text(strip=True)
                                    if clave and valor:
                                        datos[clave] = valor
                        
                        return datos
                    else:
                        return {}
                else:
                    return {}
                    
            except Exception as e:
                return {}

        # FUNCIÓN PARA CALCULAR SKEWNESS Y KURTOSIS
        def calcular_skewness_kurtosis(returns):
            """
            Calcula skewness y kurtosis de una serie de retornos
            """
            try:
                n = len(returns)
                if n < 4:
                    return 0, 0
                
                mean = np.mean(returns)
                std = np.std(returns)
                
                if std == 0:
                    return 0, 0
                
                # Skewness
                skew = np.sum((returns - mean) ** 3) / (n * std ** 3)
                
                # Kurtosis (Fisher's definition, excess kurtosis)
                kurt = np.sum((returns - mean) ** 4) / (n * std ** 4) - 3
                
                return skew, kurt
                
            except Exception as e:
                return 0, 0

        # FUNCIONES PARA CÁLCULOS DE RIESGO AVANZADOS
        def calcular_metricas_riesgo_avanzadas(ticker_symbol, periodo_años=5):
            """
            Calcula métricas avanzadas de riesgo MEJORADAS para una acción
            """
            try:
                # Descargar datos históricos
                end_date = datetime.today()
                start_date = end_date - timedelta(days=periodo_años * 365)
                
                # Datos de la acción
                stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
                if stock_data.empty or len(stock_data) == 0:
                    return None
                    
                # Datos del mercado (S&P500 como benchmark)
                market_data = yf.download('^GSPC', start=start_date, end=end_date, interval='1d')
                if market_data.empty or len(market_data) == 0:
                    return None
                
                # Asegurarnos de que tenemos columnas de cierre
                if 'Close' not in stock_data.columns or 'Close' not in market_data.columns:
                    return None
                
                # Calcular rendimientos diarios - manejar MultiIndex
                if isinstance(stock_data.columns, pd.MultiIndex):
                    stock_close = stock_data[('Close', ticker_symbol)]
                else:
                    stock_close = stock_data['Close']
                    
                if isinstance(market_data.columns, pd.MultiIndex):
                    market_close = market_data[('Close', '^GSPC')]
                else:
                    market_close = market_data['Close']
                
                stock_returns = stock_close.pct_change().dropna()
                market_returns = market_close.pct_change().dropna()
                
                # Alinear las fechas
                common_dates = stock_returns.index.intersection(market_returns.index)
                if len(common_dates) == 0:
                    return None
                    
                stock_returns = stock_returns.loc[common_dates]
                market_returns = market_returns.loc[common_dates]
                
                if len(stock_returns) < 30:  # Mínimo de datos
                    return None
                
                # Convertir a arrays numpy para evitar problemas con Series
                stock_returns_array = stock_returns.values
                market_returns_array = market_returns.values
                
                # 1. CALCULAR BETA
                covariance = np.cov(stock_returns_array, market_returns_array)[0, 1]
                market_variance = np.var(market_returns_array)
                beta = covariance / market_variance if market_variance != 0 else 0
                
                # 2. CALCULAR ALPHA
                stock_total_return = (stock_close.iloc[-1] / stock_close.iloc[0] - 1)
                market_total_return = (market_close.iloc[-1] / market_close.iloc[0] - 1)
                alpha = stock_total_return - (beta * market_total_return)
                
                # 3. CALCULAR SHARPE RATIO
                risk_free_rate = 0.02 / 252  # Tasa diaria
                excess_returns = stock_returns_array - risk_free_rate
                sharpe_ratio = (np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) 
                              if np.std(excess_returns) != 0 else 0)
                
                # 4. CALCULAR SORTINO RATIO
                downside_returns = stock_returns_array[stock_returns_array < 0]
                downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
                sortino_ratio = (np.mean(excess_returns) / downside_std * np.sqrt(252) 
                               if downside_std != 0 else 0)
                
                # 5. CALCULAR TREYNOR RATIO
                treynor_ratio = (stock_total_return - 0.02) / beta if beta != 0 else 0
                
                # 6. CALCULAR INFORMATION RATIO
                active_returns = stock_returns_array - market_returns_array
                tracking_error = np.std(active_returns) * np.sqrt(252) if len(active_returns) > 0 else 0
                information_ratio = (stock_total_return - market_total_return) / tracking_error if tracking_error != 0 else 0
                
                # 7. CALCULAR VALUE AT RISK (VaR)
                var_95 = np.percentile(stock_returns_array, 5)
                var_95_annual = var_95 * np.sqrt(252)
                var_99 = np.percentile(stock_returns_array, 1)
                var_99_annual = var_99 * np.sqrt(252)
                
                # 8. CALCULAR EXPECTED SHORTFALL (CVaR)
                cvar_95 = stock_returns_array[stock_returns_array <= var_95].mean()
                cvar_95_annual = cvar_95 * np.sqrt(252) if not np.isnan(cvar_95) else 0
                
                # 9. CALCULAR DRAWDOWN MÁXIMO
                cumulative_returns = (1 + stock_returns).cumprod()
                rolling_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - rolling_max) / rolling_max
                max_drawdown = drawdown.min()
                
                # Calcular duración del drawdown máximo
                max_dd_idx = drawdown.idxmin()
                max_dd_start = drawdown[drawdown == 0].last_valid_index()
                if max_dd_start is not None:
                    max_dd_duration = (max_dd_idx - max_dd_start).days
                else:
                    max_dd_duration = 0
                
                # 10. CALCULAR VOLATILIDAD ANUALIZADA
                volatility_annual = np.std(stock_returns_array) * np.sqrt(252)
                
                # 11. CALCULAR CORRELACIONES CON MÚLTIPLES ÍNDICES 
                correlation_sp500 = np.corrcoef(stock_returns_array, market_returns_array)[0, 1]
                
                # 12. CALCULAR MÁXIMO GANANCIA/PÉRDIDA CONSECUTIVA 
                positive_streak = 0
                negative_streak = 0
                max_positive_streak = 0
                max_negative_streak = 0
                
                for ret in stock_returns_array:
                    if ret > 0:
                        positive_streak += 1
                        negative_streak = 0
                        max_positive_streak = max(max_positive_streak, positive_streak)
                    elif ret < 0:
                        negative_streak += 1
                        positive_streak = 0
                        max_negative_streak = max(max_negative_streak, negative_streak)
                
                # 13. CALCULAR SKEWNESS Y KURTOSIS
                skewness, kurtosis = calcular_skewness_kurtosis(stock_returns_array)
                
                # 14. CALCULAR PROBABILIDAD DE PÉRDIDA
                prob_loss = np.mean(stock_returns_array < 0) * 100
                
                return {
                    # Métricas básicas
                    'Beta': round(beta, 4),
                    'Alpha': round(alpha, 4),
                    'Sharpe Ratio': round(sharpe_ratio, 4),
                    'Sortino Ratio': round(sortino_ratio, 4),
                    'Treynor Ratio': round(treynor_ratio, 4),
                    'Information Ratio': round(information_ratio, 4),
                    
                    # Métricas de riesgo
                    'VaR 95% Diario': round(var_95, 4),
                    'VaR 95% Anual': round(var_95_annual, 4),
                    'VaR 99% Diario': round(var_99, 4),
                    'VaR 99% Anual': round(var_99_annual, 4),
                    'Expected Shortfall 95%': round(cvar_95_annual, 4),
                    'Drawdown Máximo': round(max_drawdown, 4),
                    'Duración Drawdown (días)': max_dd_duration,
                    'Volatilidad Anual': round(volatility_annual, 4),
                    
                    # Correlaciones
                    'Correlación S&P500': round(correlation_sp500, 4),
                    
                    # Estadísticas avanzadas
                    'Máxima Ganancia Consecutiva': max_positive_streak,
                    'Máxima Pérdida Consecutiva': max_negative_streak,
                    'Skewness': round(skewness, 4),
                    'Kurtosis': round(kurtosis, 4),
                    'Probabilidad de Pérdida (%)': round(prob_loss, 2),
                    
                    # Rendimientos
                    'Rendimiento Total': round(stock_total_return, 4),
                    'Rendimiento Mercado': round(market_total_return, 4),
                    'Días Analizados': len(stock_returns),
                    'Período': f"{periodo_años} años"
                }
                
            except Exception as e:
                st.error(f"Error calculando métricas de riesgo: {str(e)}")
                return None

        def crear_grafica_drawdown_mejorada(ticker_symbol, periodo_años=5):
            """
            Crea gráfica de drawdown MEJORADA para visualizar pérdidas máximas
            """
            try:
                # Descargar datos
                end_date = datetime.today()
                start_date = end_date - timedelta(days=periodo_años * 365)
                
                stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
                if stock_data.empty:
                    return None
                
                # Manejar MultiIndex columns
                if isinstance(stock_data.columns, pd.MultiIndex):
                    stock_close = stock_data[('Close', ticker_symbol)]
                else:
                    stock_close = stock_data['Close']
                
                # Calcular drawdown
                returns = stock_close.pct_change().dropna()
                cumulative_returns = (1 + returns).cumprod()
                rolling_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - rolling_max) / rolling_max
                
                # Crear gráfica
                fig = go.Figure()
                
                # Área de drawdown
                fig.add_trace(go.Scatter(
                    x=drawdown.index,
                    y=drawdown * 100,
                    fill='tozeroy',
                    fillcolor='rgba(255, 0, 0, 0.3)',
                    line=dict(color='red', width=2),
                    name='Drawdown',
                    hovertemplate='<b>Drawdown</b><br>Fecha: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>'
                ))
                
                # Línea de máximo anterior
                fig.add_hline(y=0, line_dash="dash", line_color="green", annotation_text="Máximo Anterior")
                
                # Encontrar los 3 mayores drawdowns
                drawdown_sorted = drawdown.sort_values()
                top_drawdowns = drawdown_sorted.head(3)
                
                # Anotar los mayores drawdowns
                for i, (fecha, valor) in enumerate(top_drawdowns.items()):
                    fig.add_annotation(
                        x=fecha,
                        y=valor * 100,
                        text=f"DD {i+1}: {valor*100:.1f}%",
                        showarrow=True,
                        arrowhead=2,
                        bgcolor="red",
                        font=dict(color="white", size=10),
                        yshift=10 if i == 0 else (-20 if i == 1 else 30)
                    )
                
                fig.update_layout(
                    title=f'Análisis de Drawdown - {ticker_symbol}',
                    xaxis_title='Fecha',
                    yaxis_title='Drawdown (%)',
                    height=500,
                    showlegend=True,
                    hovermode='x unified'
                )
                
                return fig
                
            except Exception as e:
                st.error(f"Error creando gráfica de drawdown: {str(e)}")
                return None

        def crear_grafica_distribucion_retornos(ticker_symbol, periodo_años=5):
            """
            Crea gráfica de distribución de retornos
            """
            try:
                # Descargar datos
                end_date = datetime.today()
                start_date = end_date - timedelta(days=periodo_años * 365)
                
                stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
                if stock_data.empty:
                    return None
                
                # Manejar MultiIndex columns
                if isinstance(stock_data.columns, pd.MultiIndex):
                    stock_close = stock_data[('Close', ticker_symbol)]
                else:
                    stock_close = stock_data['Close']
                
                # Calcular retornos
                returns = stock_close.pct_change().dropna() * 100  # En porcentaje
                
                # Crear histograma con curva normal
                fig = go.Figure()
                
                # Histograma
                fig.add_trace(go.Histogram(
                    x=returns,
                    nbinsx=50,
                    name='Frecuencia',
                    opacity=0.7,
                    marker_color='lightblue'
                ))
                
                # Calcular distribución normal (aproximación)
                if len(returns) > 0:
                    x_norm = np.linspace(returns.min(), returns.max(), 100)
                    # Aproximación manual de distribución normal
                    mean = np.mean(returns)
                    std = np.std(returns)
                    if std > 0:
                        y_norm = (1/(std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean)/std) ** 2)
                        y_norm = y_norm * len(returns) * (returns.max() - returns.min()) / 50  # Escalar
                        
                        # Curva normal
                        fig.add_trace(go.Scatter(
                            x=x_norm,
                            y=y_norm,
                            mode='lines',
                            name='Distribución Normal',
                            line=dict(color='red', width=2)
                        ))
                
                # Línea en cero
                fig.add_vline(x=0, line_dash="dash", line_color="green")
                
                fig.update_layout(
                    title=f'Distribución de Retornos Diarios - {ticker_symbol}',
                    xaxis_title='Retorno Diario (%)',
                    yaxis_title='Frecuencia',
                    height=400,
                    showlegend=True
                )
                
                return fig
                
            except Exception as e:
                st.error(f"Error creando gráfica de distribución: {str(e)}")
                return None

        # Mostrar spinner mientras se cargan los datos
        with st.spinner('Cargando datos fundamentales y calculando métricas de riesgo avanzadas...'):
            datos_finviz = extraer_tabla_finviz(stonk)
            metricas_riesgo = calcular_metricas_riesgo_avanzadas(stonk)
            
            if datos_finviz:
                st.success(f"✅ Se cargaron {len(datos_finviz)} métricas fundamentales")
                
                # FUNCIÓN INTELIGENTE PARA BUSCAR MÉTRICAS
                def buscar_metrica(datos, posibles_claves):
                    for clave in posibles_claves:
                        if clave in datos:
                            return datos[clave]
                    return "N/A"
                
                # DEFINIR LAS MÉTRICAS QUE QUEREMOS MOSTRAR
                metricas_principales = {
                    # Valoración y Mercado
                    "Market Cap": ["Market Cap", "Mkt Cap"],
                    "P/E": ["P/E", "PE", "P/E Ratio"],
                    "Forward P/E": ["Forward P/E", "Fwd P/E", "Forward PE"],
                    "PEG": ["PEG", "PEG Ratio"],
                    "P/FCF": ["P/FCF", "Price/FCF"],
                    "EV/EBITDA": ["EV/EBITDA", "Enterprise Value/EBITDA"],
                    "EV/SALES": ["EV/Sales", "Enterprise Value/Sales", "EV/S"],
                    
                    # Ingresos y Rentabilidad
                    "Income": ["Income", "Net Income"],
                    "Sales": ["Sales", "Revenue", "Sales Q/Q"],
                    "Gross Margin": ["Gross Margin", "Gross Mgn"],
                    "Oper. Margin": ["Oper. Margin", "Operating Margin", "Oper Mgn"],
                    "Profit Margin": ["Profit Margin", "Profit Mgn", "Net Margin"],
                    
                    # Efectivo y Deuda
                    "Cash/Share": ["Cash/sh", "Cash/Share", "Cash per Share"],
                    "Debt/Eq": ["Debt/Eq", "Debt/Equity", "Total Debt/Equity"],
                    "LT Debt/Eq": ["LT Debt/Eq", "Long Term Debt/Equity"],
                    
                    # Rentabilidad (MANTENEMOS ROIC)
                    "ROA": ["ROA", "Return on Assets"],
                    "ROE": ["ROE", "Return on Equity"],
                    "ROIC": ["ROI", "ROIC", "Return on Investment", "Return on Capital"],
                    
                    # Indicadores Técnicos
                    "Volatility": ["Volatility", "Volatility W", "Volatility M"],
                    "RSI": ["RSI (14)", "RSI", "Relative Strength Index"],
                    "Beta": ["Beta", "Beta"],
                    "Volume": ["Volume", "Avg Volume", "Volume Today"]
                }
                
                # =============================================
                # 1. MÉTRICAS FUNDAMENTALES PRINCIPALES
                # =============================================
                st.subheader("🏢 Métricas Fundamentales Principales")
                
                # Valoración y Mercado
                st.write("#### 💰 Valoración y Mercado")
                cols = st.columns(4)
                valoracion_keys = ["Market Cap", "P/E", "Forward P/E", "PEG", "P/FCF", "EV/EBITDA", "EV/SALES"]
                for i, key in enumerate(valoracion_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                # Ingresos y Rentabilidad
                st.write("#### 📈 Ingresos y Rentabilidad")
                cols = st.columns(4)
                ingresos_keys = ["Income", "Sales", "Gross Margin", "Oper. Margin", "Profit Margin"]
                for i, key in enumerate(ingresos_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                # Deuda y Efectivo
                st.write("#### 🏦 Deuda y Efectivo")
                cols = st.columns(4)
                deuda_keys = ["Cash/Share", "Debt/Eq", "LT Debt/Eq"]
                for i, key in enumerate(deuda_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                # Rentabilidad (CON ROIC)
                st.write("#### 📊 Rentabilidad")
                cols = st.columns(4)
                rentabilidad_keys = ["ROA", "ROE", "ROIC"]
                for i, key in enumerate(rentabilidad_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                # Indicadores Técnicos
                st.write("#### 📈 Indicadores Técnicos")
                cols = st.columns(4)
                tecnicos_keys = ["Volatility", "RSI", "Beta", "Volume"]
                for i, key in enumerate(tecnicos_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                st.markdown("---")
                
                # =============================================
                # 2. MÉTRICAS AVANZADAS DE RIESGO Y RENDIMIENTO
                # =============================================
                if metricas_riesgo:
                    st.subheader("🎯 Métricas Avanzadas de Riesgo y Rendimiento")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Beta con interpretación 
                        beta = metricas_riesgo['Beta']
                        if beta < 0.8:
                            interpretacion = "Defensivo"
                            color = "green"
                        elif beta < 1.2:
                            interpretacion = "Neutro"
                            color = "orange"
                        else:
                            interpretacion = "Agresivo"
                            color = "red"
                        
                        st.metric("📊 Beta (Riesgo Sistemático)", f"{beta:.4f}")
                        st.caption(f"*Interpretación: {interpretacion}*")
                        
                        # Alpha 
                        alpha = metricas_riesgo['Alpha']
                        st.metric("α Alpha", f"{alpha:.2%}")
                        st.caption("*Rendimiento vs esperado*")
                    
                    with col2:
                        # Sharpe Ratio 
                        sharpe = metricas_riesgo['Sharpe Ratio']
                        if sharpe > 1.0:
                            color_sharpe = "green"
                        elif sharpe > 0.5:
                            color_sharpe = "orange"
                        else:
                            color_sharpe = "red"
                        
                        st.metric("⚡ Sharpe Ratio", f"{sharpe:.4f}")
                        st.caption("*Rendimiento/riesgo total*")
                        
                        # Sortino Ratio 
                        sortino = metricas_riesgo['Sortino Ratio']
                        st.metric("🎯 Sortino Ratio", f"{sortino:.4f}")
                        st.caption("*Rendimiento/riesgo bajista*")
                    
                    with col3:
                        # Nuevos ratios
                        treynor = metricas_riesgo['Treynor Ratio']
                        st.metric("📈 Treynor Ratio", f"{treynor:.4f}")
                        st.caption("*Rendimiento/riesgo sistemático*")
                        
                        information = metricas_riesgo['Information Ratio']
                        st.metric("ℹ️ Information Ratio", f"{information:.4f}")
                        st.caption("*Rendimiento activo*")
                    
                    with col4:
                        # Rendimiento vs Mercado 
                        rend_stock = metricas_riesgo['Rendimiento Total']
                        rend_mercado = metricas_riesgo['Rendimiento Mercado']
                        diferencia = rend_stock - rend_mercado
                        
                        st.metric("📊 Vs S&P500", f"{diferencia:.2%}")
                        st.caption("*Exceso vs mercado*")
                        
                        # Probabilidad de pérdida
                        prob_loss = metricas_riesgo['Probabilidad de Pérdida (%)']
                        st.metric("📉 Prob. Pérdida", f"{prob_loss:.1f}%")
                        st.caption("*Frecuencia días negativos*")
                    
                    st.markdown("---")
                    
                    # =============================================
                    # 3. MÉTRICAS DE RENDIMIENTO AJUSTADO AL RIESGO
                    # =============================================
                    st.subheader("📈 Métricas de Rendimiento Ajustado al Riesgo")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # VaR 
                        var_95 = metricas_riesgo['VaR 95% Anual']
                        var_99 = metricas_riesgo['VaR 99% Anual']
                        
                        st.metric("📉 VaR 95% Anual", f"{var_95:.2%}")
                        st.caption("*Pérdida máxima esperada*")
                        st.metric("📉 VaR 99% Anual", f"{var_99:.2%}")
                        st.caption("*Pérdida extrema esperada*")
                    
                    with col2:
                        # Drawdown 
                        max_dd = metricas_riesgo['Drawdown Máximo']
                        dd_duration = metricas_riesgo['Duración Drawdown (días)']
                        
                        st.metric("🔻 Drawdown Máximo", f"{max_dd:.2%}")
                        st.caption("*Peor pérdida histórica*")
                        st.metric("⏱️ Duración DD", f"{dd_duration} días")
                        st.caption("*Tiempo recuperación*")
                    
                    with col3:
                        # Volatilidad y Correlación
                        volatilidad = metricas_riesgo['Volatilidad Anual']
                        correlacion = metricas_riesgo['Correlación S&P500']
                        
                        st.metric("📈 Volatilidad Anual", f"{volatilidad:.2%}")
                        st.caption("*Riesgo total anualizado*")
                        st.metric("🔗 Correlación S&P500", f"{correlacion:.2%}")
                        st.caption("*Movimiento vs mercado*")
                    
                    with col4:
                        # Estadísticas avanzadas
                        cvar = metricas_riesgo['Expected Shortfall 95%']
                        skew = metricas_riesgo['Skewness']
                        
                        st.metric("💀 Expected Shortfall", f"{cvar:.2%}")
                        st.caption("*Pérdida promedio en colas*")
                        st.metric("📊 Skewness", f"{skew:.4f}")
                        st.caption("*Asimetría distribución*")
                    
                    st.markdown("---")
                    
                    # =============================================
                    # 4. ALERTAS DE RIESGO
                    # =============================================
                    st.subheader("🚨 Alertas de Riesgo")
                    
                    alertas = []
                    
                    # Verificar condiciones de riesgo
                    if metricas_riesgo['Drawdown Máximo'] < -0.20:
                        alertas.append("🔴 ALTO RIESGO: Drawdown máximo > 20%")
                    elif metricas_riesgo['Drawdown Máximo'] < -0.10:
                        alertas.append("🟡 RIESGO MODERADO: Drawdown máximo > 10%")
                    
                    if metricas_riesgo['VaR 95% Anual'] < -0.25:
                        alertas.append("🔴 ALTO RIESGO: VaR anual > 25%")
                    
                    if metricas_riesgo['Volatilidad Anual'] > 0.40:
                        alertas.append("🟡 VOLATILIDAD ALTA: > 40% anual")
                    
                    if metricas_riesgo['Probabilidad de Pérdida (%)'] > 50:
                        alertas.append("🔴 ALTA PROBABILIDAD DE PÉRDIDA: > 50%")
                    
                    if alertas:
                        for alerta in alertas:
                            st.warning(alerta)
                    else:
                        st.success("✅ Perfil de riesgo dentro de parámetros normales")
                    
                    st.markdown("---")
                    
                    # =============================================
                    # 5. ANÁLISIS GRÁFICO DE RIESGO
                    # =============================================
                    st.subheader("📈 Análisis Gráfico de Riesgo")

                    col1, col2 = st.columns(2)

                    with col1:
                        # Gráfica de drawdown 
                        st.markdown("**📉 Drawdown - Pérdidas Máximas Históricas**")
                        
                        grafica_drawdown = crear_grafica_drawdown_mejorada(stonk)
                        if grafica_drawdown:
                            st.plotly_chart(grafica_drawdown, use_container_width=True)
                            st.caption("*Visualiza las mayores caídas desde máximos históricos. Áreas rojas indican períodos de pérdidas.*")
                        else:
                            st.warning("No se pudo generar la gráfica de drawdown")

                    with col2:
                        # Gráfica de distribución de retornos
                        st.markdown("**📊 Distribución de Retornos Diarios**")
                        
                        grafica_distribucion = crear_grafica_distribucion_retornos(stonk)
                        if grafica_distribucion:
                            st.plotly_chart(grafica_distribucion, use_container_width=True)
                            st.caption("*Muestra la frecuencia y distribución de ganancias/pérdidas diarias. Línea roja = distribución normal teórica.*")
                        else:
                            st.warning("No se pudo generar la gráfica de distribución")

                    st.markdown("---")

                # =============================================
                # 6. MODELO CAPM - COSTO DE CAPITAL
                # =============================================
                st.subheader("📊 Modelo CAPM - Costo de Capital")

                # Configuración de parámetros CAPM
                col_params1, col_params2, col_params3 = st.columns(3)

                with col_params1:
                    tasa_libre_riesgo = st.number_input(
                        "Tasa Libre de Riesgo (%)", 
                        min_value=0.0, 
                        max_value=10.0, 
                        value=2.0, 
                        step=0.1,
                        help="Rendimiento de bonos gubernamentales (10 años)"
                    ) / 100

                with col_params2:
                    prima_riesgo_mercado = st.number_input(
                        "Prima de Riesgo de Mercado (%)", 
                        min_value=0.0, 
                        max_value=15.0, 
                        value=6.0, 
                        step=0.1,
                        help="Rendimiento esperado del mercado sobre tasa libre de riesgo"
                    ) / 100

                with col_params3:
                    # Obtener Beta de Yahoo Finance o usar valor por defecto
                    beta_actual = info.get('beta', 1.0)
                    beta = st.number_input(
                        "Beta (β) de la Acción", 
                        min_value=0.0, 
                        max_value=5.0, 
                        value=float(beta_actual), 
                        step=0.1,
                        help="Riesgo sistemático vs mercado"
                    )

                # Calcular CAPM
                costo_capital = tasa_libre_riesgo + beta * prima_riesgo_mercado

                # Mostrar métricas CAPM
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Tasa Libre Riesgo", 
                        f"{tasa_libre_riesgo*100:.1f}%",
                        "Rf"
                    )

                with col2:
                    st.metric(
                        "Beta (β)", 
                        f"{beta:.2f}",
                        "Riesgo Sistemático"
                    )

                with col3:
                    st.metric(
                        "Prima Riesgo Mercado", 
                        f"{prima_riesgo_mercado*100:.1f}%",
                        "E(Rm) - Rf"
                    )

                with col4:
                    st.metric(
                        "**Costo Capital (CAPM)**", 
                        f"**{costo_capital*100:.1f}%**",
                        "**E(R) = Rf + β×(Rm-Rf)**",
                        delta_color="off"
                    )

                # Gráfica del CAPM - Scatter Plot con datos históricos
                st.subheader("📈 Análisis CAPM - Datos Históricos")

                # SELECTOR DE PERÍODO PARA DATOS HISTÓRICOS
                st.markdown("**🕐 Selecciona el período de análisis:**")

                col_periodo, col_frecuencia = st.columns(2)

                with col_periodo:
                    periodo_capm = st.selectbox(
                        "Período de datos:",
                        options=["1 mes", "3 meses", "6 meses", "1 año", "2 años", "3 años", "5 años", "10 años"],
                        index=3,  # 1 año por defecto
                        key="periodo_capm"
                    )

                with col_frecuencia:
                    frecuencia_capm = st.selectbox(
                        "Frecuencia de datos:",
                        options=["Diario", "Semanal", "Mensual"],
                        index=0,  # Diario por defecto para períodos cortos
                        key="frecuencia_capm"
                    )

                # Mapear selecciones a parámetros
                periodo_map = {
                    "1 mes": 30,
                    "3 meses": 90,
                    "6 meses": 180,
                    "1 año": 365,
                    "2 años": 730,
                    "3 años": 1095,
                    "5 años": 1825,
                    "10 años": 3650
                }

                frecuencia_map = {
                    "Diario": "1d",
                    "Semanal": "1wk", 
                    "Mensual": "1mo"
                }

                dias_periodo = periodo_map[periodo_capm]
                intervalo = frecuencia_map[frecuencia_capm]

                # Ajustar frecuencia automáticamente para períodos muy cortos
                if dias_periodo <= 90 and frecuencia_capm == "Mensual":  # 3 meses o menos
                    st.warning("⚠️ Para períodos cortos (≤ 3 meses) se recomienda frecuencia Diaria o Semanal para mejor análisis")
                    intervalo = "1d"  # Forzar diario para períodos cortos

                st.info(f"**📊 Configuración:** {periodo_capm} | {frecuencia_capm} | {stonk} vs S&P500")

                # Obtener datos históricos según la selección
                try:
                    start_date = datetime.today() - timedelta(days=dias_periodo)
                    end_date = datetime.today()
                    
                    # Descargar datos
                    with st.spinner(f'Cargando datos {frecuencia_capm.lower()} para {periodo_capm}...'):
                        stock_data = yf.download(stonk, start=start_date, end=end_date, interval=intervalo)
                        market_data = yf.download('^GSPC', start=start_date, end=end_date, interval=intervalo)
                    
                    if not stock_data.empty and not market_data.empty:
                        # Obtener precios de cierre
                        if isinstance(stock_data.columns, pd.MultiIndex):
                            stock_close = stock_data[('Close', stonk)]
                        else:
                            stock_close = stock_data['Close']
                            
                        if isinstance(market_data.columns, pd.MultiIndex):
                            market_close = market_data[('Close', '^GSPC')]
                        else:
                            market_close = market_data['Close']
                        
                        # Calcular rendimientos
                        stock_returns = stock_close.pct_change().dropna()
                        market_returns = market_close.pct_change().dropna()
                        
                        # Alinear fechas
                        common_dates = stock_returns.index.intersection(market_returns.index)
                        stock_returns = stock_returns.loc[common_dates]
                        market_returns = market_returns.loc[common_dates]
                        
                        if len(stock_returns) > 5:  # Mínimo reducido para períodos cortos
                            # Crear scatter plot
                            fig_capm = go.Figure()
                            
                            # Determinar color de los puntos basado en la tendencia reciente
                            color_points = 'blue'
                            if len(stock_returns) > 10:
                                # Calcular tendencia reciente para colorear puntos
                                tendencia_reciente = stock_returns.tail(min(10, len(stock_returns))).mean()
                                if tendencia_reciente > 0:
                                    color_points = 'green'
                                else:
                                    color_points = 'red'
                            
                            # Puntos de datos históricos
                            fig_capm.add_trace(go.Scatter(
                                x=market_returns * 100,
                                y=stock_returns * 100,
                                mode='markers',
                                name=f'Datos {frecuencia_capm} ({len(stock_returns)} puntos)',
                                marker=dict(
                                    size=8,
                                    color=color_points,
                                    opacity=0.7,
                                    line=dict(width=1, color='darkgray')
                                ),
                                hovertemplate=(
                                    'Fecha: %{text}<br>' +
                                    'Rendimiento Mercado: %{x:.2f}%<br>' +
                                    'Rendimiento Acción: %{y:.2f}%<br>' +
                                    '<extra></extra>'
                                ),
                                text=[date.strftime('%d/%m/%Y') for date in common_dates]
                            ))
                            
                            # Calcular línea de regresión (Beta histórico)
                            if len(market_returns) > 1:
                                beta_real, intercepto = np.polyfit(market_returns, stock_returns, 1)
                                r_squared = np.corrcoef(market_returns, stock_returns)[0, 1] ** 2
                                
                                # Línea de regresión
                                x_line = np.linspace(market_returns.min(), market_returns.max(), 50)
                                y_line = intercepto + beta_real * x_line
                                
                                fig_capm.add_trace(go.Scatter(
                                    x=x_line * 100,
                                    y=y_line * 100,
                                    mode='lines',
                                    name=f'Beta Histórico = {beta_real:.2f}',
                                    line=dict(color='red', width=3, dash='dash'),
                                    hovertemplate='Beta histórico: {:.2f}<extra></extra>'.format(beta_real)
                                ))
                            
                            # Línea CAPM teórica
                            # Ajustar tasa libre de riesgo según frecuencia
                            if frecuencia_capm == "Diario":
                                rf_ajustado = tasa_libre_riesgo / 252
                            elif frecuencia_capm == "Semanal":
                                rf_ajustado = tasa_libre_riesgo / 52
                            else:  # Mensual
                                rf_ajustado = tasa_libre_riesgo / 12
                                
                            x_capm = np.linspace(market_returns.min(), market_returns.max(), 50)
                            y_capm = rf_ajustado + beta * (x_capm - rf_ajustado)
                            
                            fig_capm.add_trace(go.Scatter(
                                x=x_capm * 100,
                                y=y_capm * 100,
                                mode='lines',
                                name=f'CAPM Teórico (β = {beta:.2f})',
                                line=dict(color='blue', width=3),
                                hovertemplate='CAPM teórico<extra></extra>'
                            ))
                            
                            # Punto de rendimiento esperado actual
                            fig_capm.add_trace(go.Scatter(
                                x=[0],  # Centrado en el origen para mejor visualización
                                y=[costo_capital * 100],
                                mode='markers+text',
                                name='Rendimiento Esperado Anual',
                                marker=dict(size=12, color='orange', symbol='star', line=dict(width=2, color='darkorange')),
                                text=['ESPERADO'],
                                textposition="top center",
                                hovertemplate=f'Rendimiento esperado anual: {costo_capital*100:.1f}%<extra></extra>'
                            ))
                            
                            fig_capm.update_layout(
                                title=f'CAPM - {stonk} vs S&P500 ({periodo_capm}, {frecuencia_capm})',
                                xaxis_title='Rendimiento del Mercado (S&P500) (%)',
                                yaxis_title=f'Rendimiento de {stonk} (%)',
                                height=600,
                                showlegend=True,
                                hovermode='closest',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                ),
                                xaxis=dict(
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='lightgray',
                                    zeroline=True,
                                    zerolinewidth=2,
                                    zerolinecolor='black'
                                ),
                                yaxis=dict(
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='lightgray',
                                    zeroline=True,
                                    zerolinewidth=2,
                                    zerolinecolor='black'
                                )
                            )
                            
                            st.plotly_chart(fig_capm, use_container_width=True)
                            
                            # Análisis de la regresión
                            st.subheader("📊 Análisis de Regresión")
                            
                            col_reg1, col_reg2, col_reg3, col_reg4 = st.columns(4)
                            
                            with col_reg1:
                                st.metric("Beta Histórico", f"{beta_real:.2f}")
                                st.caption(f"Calculado con {len(stock_returns)} puntos")
                                
                            with col_reg2:
                                st.metric("Beta Teórico", f"{beta:.2f}")
                                st.caption("Valor de Yahoo Finance")
                                
                            with col_reg3:
                                diferencia_beta = beta_real - beta
                                st.metric(
                                    "Diferencia Beta", 
                                    f"{diferencia_beta:.2f}",
                                    f"{'↑' if beta_real > beta else '↓'} histórico vs teórico"
                                )
                                st.caption("Consistencia del beta")
                                
                            with col_reg4:
                                st.metric("R² (Coef. Determinación)", f"{r_squared:.3f}")
                                st.caption("Ajuste del modelo")
                            
                            # Interpretación específica por período
                            st.markdown("---")
                            st.subheader("💡 Interpretación por Período")
                            
                            col_interp1, col_interp2 = st.columns(2)
                            
                            with col_interp1:
                                st.markdown(f"""
                                **📈 Análisis del Período {periodo_capm}:**
                                
                                • **Beta histórico**: **{beta_real:.2f}**
                                • **Puntos analizados**: **{len(stock_returns)}**
                                • **Período**: {periodo_capm}
                                • **Frecuencia**: {frecuencia_capm}
                                
                                **🎯 Significado del Beta:**
                                - **Beta > 1**: Más volátil que el mercado
                                - **Beta = 1**: Misma volatilidad  
                                - **Beta < 1**: Menos volátil
                                """)
                            
                            with col_interp2:
                                # Interpretación específica del período
                                if "mes" in periodo_capm:
                                    interpretacion_periodo = "**🔄 Análisis de Corto Plazo** - Muestra el comportamiento reciente y puede ser más volátil"
                                elif periodo_capm == "1 año":
                                    interpretacion_periodo = "**📊 Análisis de Mediano Plazo** - Balance entre estabilidad y actualidad"
                                else:
                                    interpretacion_periodo = "**📈 Análisis de Largo Plazo** - Muestra tendencias estables y comportamiento histórico"
                                
                                st.markdown(f"""
                                **🔍 Contexto del Período:**
                                
                                {interpretacion_periodo}
                                
                                **📋 Recomendaciones:**
                                - Períodos cortos: Útiles para trading
                                - Períodos largos: Mejores para inversión
                                - Combine períodos para análisis completo
                                """)
                            
                            # Recomendaciones específicas basadas en el período
                            st.markdown("---")
                            st.subheader("🎯 Recomendaciones Específicas")
                            
                            if "mes" in periodo_capm:
                                if r_squared > 0.6:
                                    st.success("""
                                    **✅ BUEN AJUSTE EN CORTO PLAZO - Para Trading:**
                                    - Relación mercado-acción consistente recientemente
                                    - Estrategias de momentum pueden ser efectivas
                                    - Monitorea cambios diarios en la relación
                                    """)
                                else:
                                    st.warning("""
                                    **🟡 AJUSTE VARIABLE EN CORTO PLAZO - Precauciones:**
                                    - La acción tiene comportamiento independiente reciente
                                    - Considera noticias y eventos específicos de la empresa
                                    - Usa stops más ajustados
                                    """)
                            else:
                                if r_squared > 0.7:
                                    st.success("""
                                    **✅ ALTO AJUSTE - Para Inversión:**
                                    - Comportamiento predecible vs mercado
                                    - Estrategias basadas en Beta son confiables
                                    - Buena para diversificación de cartera
                                    """)
                                elif r_squared > 0.4:
                                    st.info("""
                                    **🟡 AJUSTE MODERADO - Enfoque Balanceado:**
                                    - Combine análisis CAPM con otros métodos
                                    - Considere factores específicos de la empresa
                                    - Monitoree cambios en la relación
                                    """)
                                else:
                                    st.warning("""
                                    **🔴 BAJO AJUSTE - Análisis Cauteloso:**
                                    - La acción se mueve independientemente del mercado
                                    - Enfóquese en análisis fundamental y técnico
                                    - El Beta puede no ser indicador confiable
                                    """)
                        
                        else:
                            st.warning(f"⚠️ No hay suficientes datos {frecuencia_capm.lower()} para {periodo_capm}. Intenta con una frecuencia diferente.")
                            
                    else:
                        st.warning("❌ No se pudieron cargar los datos para el análisis CAPM")
                        
                except Exception as e:
                    st.error(f"Error en el análisis CAPM: {str(e)}")

                # Consejos para usar diferentes períodos
                st.markdown("---")
                st.subheader("💡 Consejos para Usar Diferentes Períodos")

                consejos_periodos = [
                    "**📅 1-3 meses**: Ideal para traders - muestra comportamiento reciente",
                    "**📊 6 meses - 1 año**: Balanceado - buen para swing trading",
                    "**📈 2-3 años**: Estabilidad media - recomendado para mayoría de inversores", 
                    "**🏛️ 5-10 años**: Largo plazo - muestra tendencias estables",
                    "**🔄 Combine períodos**: Use corto + largo plazo para análisis completo",
                    "**📉 Períodos cortos**: Más volátiles pero más actualizados",
                    "**📈 Períodos largos**: Más estables pero pueden omitir cambios recientes"
                ]

                for consejo in consejos_periodos:
                    st.write(f"• {consejo}")

                st.markdown("---")

                # =============================================
                # 7. SNAPSHOT FINANCIERO COMPLETO
                # =============================================
                st.subheader(f"📊 Snapshot Financiero Completo - {stonk}")
                
                # Crear una tabla de 2 columnas replicando Finviz
                num_datos = len(datos_finviz)
                mitad = (num_datos + 1) // 2
                
                # Dividir los datos en dos columnas
                items = list(datos_finviz.items())
                col1_items = items[:mitad]
                col2_items = items[mitad:]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    for clave, valor in col1_items:
                        st.markdown(f"""
                        <div style="border-bottom: 1px solid #444; padding: 10px 0;">
                            <div style="font-weight: bold; color: white; font-size: 14px; margin-bottom: 2px;">{clave}</div>
                            <div style="color: #f0f0f0; font-size: 14px; text-align: right; font-weight: 500;">{valor}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    for clave, valor in col2_items:
                        st.markdown(f"""
                        <div style="border-bottom: 1px solid #444; padding: 10px 0;">
                            <div style="font-weight: bold; color: white; font-size: 14px; margin-bottom: 2px;">{clave}</div>
                            <div style="color: #f0f0f0; font-size: 14px; text-align: right; font-weight: 500;">{valor}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # BOTÓN DE DESCARGA
                st.markdown("---")
                st.subheader("💾 Exportar Datos")
                
                # Crear DataFrame combinado con todas las métricas
                df_completo = pd.DataFrame(list(datos_finviz.items()), columns=['Métrica', 'Valor'])
                
                # Agregar métricas de riesgo si están disponibles
                if metricas_riesgo:
                    df_riesgo = pd.DataFrame(list(metricas_riesgo.items()), columns=['Métrica', 'Valor'])
                    df_completo = pd.concat([df_completo, df_riesgo], ignore_index=True)
                
                csv = df_completo.to_csv(index=False)
                
                st.download_button(
                    label="📥 Descargar datos fundamentales y de riesgo como CSV",
                    data=csv,
                    file_name=f"{stonk}_datos_completos.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                    
            else:
                st.error("""
                ❌ No se pudieron cargar los datos fundamentales. Posibles causas:
                
                • **Problemas de conexión** con Finviz
                • **Bloqueo temporal** por demasiadas solicitudes
                • **El símbolo no existe** o no está disponible
                
                💡 **Sugerencias:**
                • Verifica el símbolo (ej: AAPL, MSFT, TSLA, GOOGL)
                • Espera 1-2 minutos e intenta nuevamente  
                • Verifica directamente en [Finviz](https://finviz.com/quote.ashx?t={stonk})
                """)
                
                if st.button("🔄 Intentar nuevamente", use_container_width=True, key="reintentar_fundamentales"):
                    st.rerun()
    
        with tab2:
            st.header("🎓 Educación Financiera - Guía Completa de Métricas")
            st.write("Aprende el significado e interpretación de todas las métricas financieras y de riesgo")
            
            # Selector de categoría ampliado
            categorias = [
                "📊 Métricas Fundamentales (82 métricas)",
                "⚡ Métricas Avanzadas de Riesgo y Rendimiento", 
                "📈 Métricas de Rendimiento Ajustado al Riesgo",
                "📉 Métricas de Riesgo Avanzadas",
                "📊 Análisis Gráfico de Riesgo",
                "💡 Consejos Prácticos de Inversión"
            ]
            
            categoria = st.selectbox("Selecciona una categoría:", categorias)
            
            st.markdown("---")
            
            if categoria == "📊 Métricas Fundamentales (82 métricas)":
                st.subheader("📊 Guía Completa de Métricas Fundamentales")
                st.write("**Explicación de las 82 métricas fundamentales más importantes**")
                
                metricas_fundamentales = {
                    "💰 VALORACIÓN Y MERCADO": {
                        "Market Cap": "**Capitalización de mercado**: Valor total de la empresa en bolsa = Precio por acción × Acciones en circulación. Empresas grandes (>$10B) suelen ser más estables.",
                        "P/E": "**Ratio Precio-Beneficio**: Cuánto pagan los inversores por cada $1 de ganancias. P/E alto = expectativas de crecimiento altas.",
                        "Forward P/E": "**P/E Forward**: Basado en ganancias estimadas futuras. Mejor indicador que P/E histórico.",
                        "PEG": "**Ratio P/E sobre Crecimiento**: P/E dividido por tasa crecimiento anual. PEG < 1 puede indicar subvaloración.",
                        "P/S": "**Ratio Precio-Ventas**: Precio sobre ventas anuales. Útil para empresas sin ganancias.",
                        "P/B": "**Ratio Precio-Valor Contable**: Precio sobre valor en libros. <1 puede indicar subvaloración.",
                        "P/FCF": "**Precio sobre Flujo de Caja Libre**: Cuánto pagas por el flujo de caja operativo. Muy importante para valoración.",
                        "P/C": "**Precio sobre Efectivo**: Valoración respecto al efectivo en balance.",
                        "EV/EBITDA": "**Enterprise Value/EBITDA**: Valor empresa sobre ganancias operativas. Útil para comparar empresas con diferente deuda.",
                        "EV/SALES": "**Enterprise Value/Ventas**: Similar a P/S pero considera deuda y efectivo.",
                        "EV/FCF": "**Enterprise Value/Flujo Caja Libre**: Valoración completa sobre flujo de caja libre."
                    },
                    "📈 INGRESOS Y RENTABILIDAD": {
                        "Revenue": "**Ingresos/Ventas**: Dinero total generado por ventas. Crecimiento constante es positivo.",
                        "Sales Q/Q": "**Crecimiento Ventas Trimestral**: % cambio ventas vs trimestre anterior. >5% es bueno.",
                        "EPS": "**Ganancias por Acción**: Beneficio neto dividido por acciones. Crecimiento constante es clave.",
                        "EPS Q/Q": "**Crecimiento EPS Trimestral**: % cambio ganancias vs trimestre anterior.",
                        "EPS this Y": "**EPS Este Año**: Ganancias actuales vs año anterior.",
                        "EPS next Y": "**EPS Próximo Año**: Estimaciones de ganancias futuras.",
                        "EPS past 5Y": "**Crecimiento EPS 5 Años**: Tasa crecimiento anualizada histórica.",
                        "EPS next 5Y": "**Crecimiento EPS Próximos 5 Años**: Estimaciones crecimiento futuro.",
                        "Gross Margin": "**Margen Bruto**: (Ventas - Costo bienes) / Ventas. Eficiencia producción.",
                        "Oper. Margin": "**Margen Operativo**: Ganancias operativas / Ventas. Eficiencia operativa.",
                        "Profit Margin": "**Margen de Beneficio Neto**: Beneficio neto / Ventas. Rentabilidad final.",
                        "ROA": "**Return on Assets**: Beneficio neto / Activos totales. Eficiencia uso activos.",
                        "ROE": "**Return on Equity**: Beneficio neto / Patrimonio neto. Rentabilidad para accionistas.",
                        "ROI": "**Return on Investment**: Ganancia / Inversión. Eficiencia inversiones.",
                        "EBITDA": "**Ganancias antes de Intereses, Impuestos, Depreciación**: Flujo operativo bruto.",
                        "EBIT": "**Ganancias antes de Intereses e Impuestos**: Resultado operativo."
                    },
                    "🏦 DEUDA Y EFECTIVO": {
                        "Total Debt": "**Deuda Total**: Suma deuda corto + largo plazo.",
                        "Debt/Eq": "**Ratio Deuda/Patrimonio**: Deuda total / Patrimonio neto. >2 puede ser riesgoso.",
                        "LT Debt/Eq": "**Deuda Largo Plazo/Patrimonio**: Deuda a largo plazo sobre patrimonio.",
                        "Current Ratio": "**Ratio Corriente**: Activos corrientes / Pasivos corrientes. Liquidez corto plazo.",
                        "Quick Ratio": "**Ratio Rápido**: (Activos corrientes - Inventario) / Pasivos corrientes. Liquidez inmediata.",
                        "Cash/Share": "**Efectivo por Acción**: Efectivo total / Acciones. Reservas de seguridad.",
                        "Cash Flow/Share": "**Flujo Caja por Acción**: Flujo caja operativo por acción.",
                        "Total Cash": "**Efectivo Total**: Dinero disponible en caja y equivalentes.",
                        "Total Cash/Share": "**Efectivo Total por Acción**: Similar a Cash/Share pero incluye equivalentes."
                    },
                    "📊 INDICADORES TÉCNICOS": {
                        "Beta": "**Volatilidad vs Mercado**: 1 = igual volatilidad que mercado. <1 = menos volátil, >1 = más volátil.",
                        "RSI": "**Índice Fuerza Relativa**: Oscilador 0-100. >70 = sobrecomprado, <30 = sobrevendido.",
                        "Volatility": "**Volatilidad**: Desviación estándar retornos. Mide riesgo precio.",
                        "ATR": "**Average True Range**: Volatilidad basada en rangos de trading.",
                        "SMA 20": "**Media Móvil Simple 20 días**: Tendencia precio corto plazo.",
                        "SMA 50": "**Media Móvil Simple 50 días**: Tendencia precio medio plazo.",
                        "SMA 200": "**Media Móvil Simple 200 días**: Tendencia precio largo plazo.",
                        "Volume": "**Volumen**: Acciones negociadas. Alto volumen confirma tendencias.",
                        "Avg Volume": "**Volumen Promedio**: Volumen medio histórico para comparar.",
                        "Rel Volume": "**Volumen Relativo**: Volumen actual / Volumen promedio."
                    },
                    "📋 DATOS CORPORATIVOS": {
                        "Shares Out": "**Acciones en Circulación**: Número total acciones emitidas.",
                        "Float": "**Acciones Flotantes**: Acciones disponibles para trading público.",
                        "Insider Own": "**Propiedad Insider**: % acciones poseídas por directivos.",
                        "Insider Trans": "**Transacciones Insider**: Compras/ventas de directivos.",
                        "Inst Own": "**Propiedad Institucional**: % acciones poseídas por fondos.",
                        "Inst Trans": "**Transacciones Institucionales**: Compras/ventas de fondos.",
                        "Short Float": "**Short Interest**: % acciones vendidas en corto. Alto = pesimismo.",
                        "Short Ratio": "**Ratio Corto**: Días para cubrir posiciones cortas.",
                        "Dividend": "**Dividendo**: Pago por acción a accionistas.",
                        "Dividend %": "**Rendimiento por Dividendo**: Dividendo anual / Precio acción.",
                        "Payout Ratio": "**Ratio de Pago**: % ganancias pagado como dividendo."
                    },
                    "🌎 MACRO Y SECTOR": {
                        "Sector": "**Sector Empresarial**: Clasificación industria (Tech, Health, Finance, etc.).",
                        "Industry": "**Industria Específica**: Subclasificación sector.",
                        "Country": "**País de Origen**: Donde opera principalmente la empresa.",
                        "Index": "**Índice de Referencia**: DJIA, S&P500, Nasdaq, etc.",
                        "Employees": "**Número de Empleados**: Tamaño empresa por personal."
                    }
                }
                
                for grupo, metricas in metricas_fundamentales.items():
                    st.markdown(f"### {grupo}")
                    for metrica, explicacion in metricas.items():
                        with st.expander(f"**{metrica}**"):
                            st.write(explicacion)
                            # Agregar interpretación práctica
                            if "P/E" in metrica:
                                st.info("**Interpretación práctica**: P/E < 15 puede ser barato, 15-25 razonable, >25 caro (depende del sector)")
                            elif "ROE" in metrica:
                                st.info("**Interpretación práctica**: ROE > 15% generalmente bueno, >20% excelente")
                            elif "Debt/Eq" in metrica:
                                st.info("**Interpretación práctica**: Debt/Eq < 0.5 conservador, 0.5-1 moderado, >1 agresivo")
                    
                    st.markdown("---")
                    
            elif categoria == "⚡ Métricas Avanzadas de Riesgo y Rendimiento":
                st.subheader("⚡ Métricas Avanzadas de Riesgo y Rendimiento")
                st.write("**Métricas sofisticadas para análisis profesional**")
                
                metricas_avanzadas = {
                    "Beta (Riesgo Sistemático)": {
                        "definicion": "Mide la volatilidad de una acción en relación con el mercado completo.",
                        "formula": "Covarianza(Acción, Mercado) / Varianza(Mercado)",
                        "interpretacion": "**<0.8**: Defensivo | **0.8-1.2**: Neutral | **>1.2**: Agresivo",
                        "uso": "Para determinar qué tan sensible es una acción a los movimientos del mercado."
                    },
                    "Alpha": {
                        "definicion": "Rendimiento excedente sobre lo esperado dado su nivel de riesgo (Beta).",
                        "formula": "Rendimiento Real - (Beta × Rendimiento Mercado)",
                        "interpretacion": "**Alpha > 0**: Supera expectativas | **Alpha < 0**: No alcanza expectativas",
                        "uso": "Medir la habilidad del gestor o el desempeño anormal."
                    },
                    "Sharpe Ratio": {
                        "definicion": "Rendimiento excedente por unidad de riesgo total.",
                        "formula": "(Rendimiento - Tasa Libre Riesgo) / Volatilidad",
                        "interpretacion": "**>1.0**: Excelente | **0.5-1.0**: Bueno | **<0.5**: Pobre",
                        "uso": "Comparar fondos o estrategias ajustando por riesgo total."
                    },
                    "Sortino Ratio": {
                        "definicion": "Similar a Sharpe pero solo considera riesgo bajista (desviación negativa).",
                        "formula": "(Rendimiento - Tasa Libre Riesgo) / Volatilidad Bajista",
                        "interpretacion": "**>2.0**: Excelente | **1.0-2.0**: Bueno | **<1.0**: Mejorable",
                        "uso": "Mejor métrica cuando preocupa más las pérdidas que la volatilidad general."
                    },
                    "Treynor Ratio": {
                        "definicion": "Rendimiento excedente por unidad de riesgo sistemático (Beta).",
                        "formula": "(Rendimiento - Tasa Libre Riesgo) / Beta",
                        "interpretacion": "Cuanto mayor mejor. Comparar con benchmark del sector.",
                        "uso": "Para carteras diversificadas donde el riesgo no sistemático es mínimo."
                    },
                    "Information Ratio": {
                        "definicion": "Rendimiento activo por unidad de riesgo activo (tracking error).",
                        "formula": "(Rendimiento Cartera - Rendimiento Benchmark) / Tracking Error",
                        "interpretacion": "**>0.5**: Buen gestor activo | **>0.75**: Excelente gestor",
                        "uso": "Evaluar gestión activa vs benchmark."
                    }
                }
                
                for metrica, detalles in metricas_avanzadas.items():
                    st.markdown(f"### {metrica}")
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.write(f"**📖 Definición**: {detalles['definicion']}")
                        st.write(f"**🧮 Fórmula**: {detalles['formula']}")
                    
                    with col2:
                        st.write(f"**📊 Interpretación**: {detalles['interpretacion']}")
                        st.write(f"**🎯 Uso Práctico**: {detalles['uso']}")
                    
                    # Ejemplos prácticos
                    if "Beta" in metrica:
                        st.info("**Ejemplo**: Una acción con Beta 1.5 subirá 15% si el mercado sube 10%, pero caerá 15% si el mercado cae 10%")
                    elif "Sharpe" in metrica:
                        st.info("**Ejemplo**: Sharpe 1.2 significa que por cada 1% de riesgo, genera 1.2% de rendimiento excedente")
                    elif "Alpha" in metrica:
                        st.info("**Ejemplo**: Alpha 0.05 significa que superó en 5% al rendimiento esperado dado su riesgo")
                    
                    st.markdown("---")
                    
            elif categoria == "📈 Métricas de Rendimiento Ajustado al Riesgo":
                st.subheader("📈 Métricas de Rendimiento Ajustado al Riesgo")
                st.write("**Cómo evaluar si el rendimiento compensa el riesgo asumido**")
                
                metricas_rendimiento = {
                    "Rendimiento Total vs S&P500": {
                        "concepto": "Comparación directa del rendimiento de la acción vs el índice de referencia.",
                        "importancia": "¿Supera al mercado? Rendimientos consistentemente superiores indican ventaja competitiva.",
                        "interpretacion": "**>0**: Supera mercado | **<0**: No alcanza mercado | Consistencia > Magnitud"
                    },
                    "Probabilidad de Pérdida (%)": {
                        "concepto": "Porcentaje de días con rendimientos negativos en el período analizado.",
                        "importancia": "Frecuencia de pérdidas. Menos del 50% es deseable.",
                        "interpretacion": "**<45%**: Buena consistencia | **45-55%**: Neutral | **>55%**: Alta frecuencia pérdidas"
                    },
                    "Máxima Ganancia Consecutiva": {
                        "concepto": "Máximo número de días consecutivos con rendimientos positivos.",
                        "importancia": "Mide la persistencia de tendencias alcistas.",
                        "interpretacion": "Valores altos indican momentum positivo sostenido"
                    },
                    "Máxima Pérdida Consecutiva": {
                        "concepto": "Máximo número de días consecutivos con rendimientos negativos.",
                        "importancia": "Mide la persistencia de tendencias bajistas.",
                        "interpretacion": "Valores altos indican rachas bajistas prolongadas"
                    }
                }
                
                for metrica, detalles in metricas_rendimiento.items():
                    st.markdown(f"#### {metrica}")
                    st.write(f"**🎯 Concepto**: {detalles['concepto']}")
                    st.write(f"**📊 Importancia**: {detalles['importancia']}")
                    st.write(f"**🔍 Interpretación**: {detalles['interpretacion']}")
                    
                    # Consejos específicos
                    if "Probabilidad" in metrica:
                        st.warning("⚠️ **Atención**: Una probabilidad de pérdida muy baja puede indicar falta de volatilidad (y por tanto de oportunidad)")
                    elif "Consecutiva" in metrica:
                        st.success("💡 **Tip**: Las rachas extremas (muy largas) pueden indicar mercados anormales")
                    
                    st.markdown("---")
                    
            elif categoria == "📉 Métricas de Riesgo Avanzadas":
                st.subheader("📉 Métricas de Riesgo Avanzadas")
                st.write("**Medidas sofisticadas de riesgo para inversores profesionales**")
                
                metricas_riesgo = {
                    "Value at Risk (VaR) 95%": {
                        "definicion": "Pérdida máxima esperada en condiciones normales de mercado (nivel 95% confianza).",
                        "interpretacion": "**VaR 95% = -15%**: Hay 5% probabilidad de perder más del 15% en el período",
                        "limitaciones": "No captura eventos extremos (colas de distribución)",
                        "uso": "Gestión de riesgo diario, establecimiento de límites"
                    },
                    "Value at Risk (VaR) 99%": {
                        "definicion": "Pérdida máxima esperada en escenarios más extremos (nivel 99% confianza).",
                        "interpretacion": "**VaR 99% = -25%**: Hay 1% probabilidad de perder más del 25%",
                        "limitaciones": "Basado en supuestos de distribución normal",
                        "uso": "Preparación para escenarios adversos"
                    },
                    "Expected Shortfall (CVaR)": {
                        "definicion": "Pérdida promedio en los peores casos (más allá del VaR).",
                        "interpretacion": "**ES = -30%**: En el 5% peor de casos, la pérdida promedio es 30%",
                        "ventajas": "Captura mejor el riesgo de cola que VaR",
                        "uso": "Análisis de escenarios catastróficos"
                    },
                    "Drawdown Máximo": {
                        "definicion": "Mayor caída desde pico a valle en el período histórico.",
                        "interpretacion": "**-35%**: La peor caída histórica fue del 35% desde un máximo",
                        "importancia": "Mide el peor escenario pasado que podría repetirse",
                        "uso": "Preparación psicológica y gestión de capital"
                    },
                    "Duración del Drawdown": {
                        "definicion": "Tiempo que tomó recuperar el pico anterior después de la máxima caída.",
                        "interpretacion": "**180 días**: Tomó 6 meses recuperarse de la peor caída",
                        "importancia": "Mide la persistencia del dolor en pérdidas",
                        "uso": "Evaluar tolerancia temporal a pérdidas"
                    },
                    "Volatilidad Anualizada": {
                        "definicion": "Desviación estándar de rendimientos anualizada.",
                        "interpretacion": "**40%**: Movimientos típicos de ±40% anuales",
                        "escalas": "**<20%**: Baja vol | **20-40%**: Media | **>40%**: Alta volatilidad",
                        "uso": "Dimensionamiento de posición y expectativas de movimiento"
                    },
                    "Correlación S&P500": {
                        "definicion": "Grado de relación lineal con el mercado estadounidense.",
                        "interpretacion": "**0.8**: Fuertemente correlacionado | **0.2**: Baja correlación",
                        "importancia": "Para diversificación: baja correlación = mejor diversificación",
                        "uso": "Construcción de carteras y hedge"
                    },
                    "Skewness": {
                        "definicion": "Asimetría de la distribución de rendimientos.",
                        "interpretacion": "**>0**: Sesgo positivo (más ganancias extremas) | **<0**: Sesgo negativo (más pérdidas extremas)",
                        "preferencia": "Skewness positivo generalmente preferible",
                        "uso": "Evaluar perfil de retornos asimétricos"
                    },
                    "Kurtosis": {
                        "definicion": "Medida de 'grosor' de las colas de la distribución.",
                        "interpretacion": "**>3**: Colas pesadas (más eventos extremos) | **<3**: Colas livianas",
                        "importancia": "Kurtosis alta = mayor probabilidad de eventos black swan",
                        "uso": "Evaluar riesgo de eventos extremos"
                    }
                }
                
                for metrica, detalles in metricas_riesgo.items():
                    st.markdown(f"#### {metrica}")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**📖 Definición**: {detalles['definicion']}")
                        st.write(f"**🔍 Interpretación**: {detalles['interpretacion']}")
                    
                    with col2:
                        if 'limitaciones' in detalles:
                            st.write(f"**⚠️ Limitaciones**: {detalles['limitaciones']}")
                        if 'ventajas' in detalles:
                            st.write(f"**✅ Ventajas**: {detalles['ventajas']}")
                        st.write(f"**🎯 Uso Práctico**: {detalles['uso']}")
                    
                    # Alertas específicas
                    if "VaR" in metrica:
                        st.error("**Cuidado**: VaR subestima riesgo en crisis reales")
                    if "Drawdown" in metrica:
                        st.warning("**Importante**: Drawdown histórico ≠ Drawdown futuro")
                    
                    st.markdown("---")
                    
            elif categoria == "📊 Análisis Gráfico de Riesgo":
                st.subheader("📊 Análisis Gráfico de Riesgo")
                st.write("**Interpretación de gráficas y visualizaciones de riesgo**")
                
                analisis_grafico = {
                    "Gráfica de Drawdown": {
                        "que_muestra": "Evolución temporal de las caídas desde máximos históricos.",
                        "como_interpretar": "**Áreas rojas profundas** = períodos de grandes pérdidas | **Recuperación rápida** = resiliencia",
                        "señales_alerta": "Drawdowns > 20%, duración > 1 año, múltiples drawdowns profundos",
                        "uso_practico": "Identificar períodos de stress histórico y patrones de recuperación"
                    },
                    "Distribución de Retornos": {
                        "que_muestra": "Frecuencia y distribución de los rendimientos diarios.",
                        "como_interpretar": "**Campana centrada en positivo** = buenos retornos | **Colas anchas** = alta probabilidad eventos extremos",
                        "señales_alerta": "Sesgo negativo, colas muy pesadas, múltiples picos anormales",
                        "uso_practico": "Entender el perfil estadístico de los retornos y probabilidades"
                    },
                    "Análisis de Rachas": {
                        "que_muestra": "Patrones de rendimientos consecutivos positivos/negativos.",
                        "como_interpretar": "**Rachas largas positivas** = momentum fuerte | **Rachas largas negativas** = tendencia bajista persistente",
                        "señales_alerta": "Rachas extremadamente largas (pueden indicar mercados anormales)",
                        "uso_practico": "Identificar persistencia en tendencias y posibles reversiones"
                    }
                }
                
                for grafica, detalles in analisis_grafico.items():
                    st.markdown(f"#### {grafica}")
                    
                    st.write(f"**📈 Qué muestra**: {detalles['que_muestra']}")
                    st.write(f"**🔍 Cómo interpretar**: {detalles['como_interpretar']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**🚨 Señales de alerta**: {detalles['señales_alerta']}")
                    with col2:
                        st.write(f"**💡 Uso práctico**: {detalles['uso_practico']}")
                    
                    # Ejemplos visuales conceptuales
                    if "Drawdown" in grafica:
                        st.info("**Ejemplo visual**: Una gráfica que muestra caídas del 30% en 2008 y 15% en 2020 ayuda a entender resiliencia histórica")
                    elif "Distribución" in grafica:
                        st.info("**Ejemplo visual**: Una distribución con cola izquierda larga indica mayor probabilidad de grandes pérdidas que ganancias")
                    
                    st.markdown("---")
                
                # Consejos generales de interpretación gráfica
                st.markdown("### 🎯 Consejos para Interpretación Gráfica")
                consejos_graficos = [
                    "**Contexto temporal**: Siempre considera el período analizado. 5 años vs 10 años puede cambiar completamente la perspectiva.",
                    "**Escalas engañosas**: Verifica las escalas de los ejes. Cambios pequeños en escala pueden exagerar o minimizar movimientos.",
                    "**Comparativa**: Siempre compara con un benchmark relevante (S&P500 para acciones US).",
                    "**Múltiples timeframes**: Analiza diferentes períodos: corto (1 año), medio (3-5 años), largo (10+ años).",
                    "**Eventos específicos**: Identifica eventos macro (COVID, crisis 2008) que distorsionan datos históricos."
                ]
                
                for consejo in consejos_graficos:
                    st.write(f"• {consejo}")
                    
            else:  # Consejos Prácticos de Inversión
                st.subheader("💡 Consejos Prácticos de Inversión")
                st.write("**Sabiduría probada para tomar mejores decisiones**")
                
                # Consejos organizados por categoría
                categorias_consejos = {
                    "🔍 Investigación y Análisis": [
                        "**Conoce el negocio**: Invierte solo en empresas que entiendas completamente",
                        "**Análisis competitivo**: Evalúa ventajas competitivas duraderas (moats)",
                        "**Sector y tendencias**: Invierte en sectores con tailwinds, no headwinds",
                        "**Calidad management**: Investiga el track record del equipo directivo",
                        "**Múltiples métricas**: Nunca bases decisiones en una sola métrica"
                    ],
                    "📈 Gestión de Riesgo": [
                        "**Diversificación inteligente**: No sobre-diversifiques, pero tampoco pongas todos los huevos en una canasta",
                        "**Tamaño de posición**: Nunca arriesgues más del 5% de tu cartera en una sola idea",
                        "**Stop losses mentales**: Define tu precio de venta antes de comprar",
                        "**Riesgo asimétrico**: Busca oportunidades con upside potencial > downside risk",
                        "**Liquidez**: Considera siempre cuán fácil puedes salir de la inversión"
                    ],
                    "⏳ Psicología y Disciplina": [
                        "**Paciencia**: El tiempo en el mercado > timing del mercado",
                        "**Control emocional**: El miedo y la codicia son tus peores enemigos",
                        "**Independencia**: Piensa por ti mismo, no sigas la manada",
                        "**Humildad**: Reconoce cuando te equivocas y ajusta",
                        "**Consistencia**: Sigue tu proceso invariablemente"
                    ],
                    "💰 Valoración y Timing": [
                        "**Margen de seguridad**: Compra con descuento al valor intrínseco",
                        "**Ciclos de mercado**: Entiende en qué fase del ciclo estás",
                        "**Valoración relativa**: Compara siempre con alternativas",
                        "**Catalizadores**: Identifica eventos que puedan mover el precio",
                        "**Patience**: Mejor oportunidad perdida que mala inversión"
                    ],
                    "📚 Educación Continua": [
                        "**Aprendizaje constante**: Los mercados evolucionan, tú también debes hacerlo",
                        "**Historia financiera**: Estudia burbujas y cracks pasados",
                        "**Mentes brillantes**: Lee a Buffett, Munger, Lynch, Graham",
                        "**Pensamiento crítico**: Cuestiona todo, especialmente tus propias ideas",
                        "**Red de conocimiento**: Rodéate de personas más inteligentes que tú"
                    ]
                }
                
                for categoria, consejos in categorias_consejos.items():
                    st.markdown(f"### {categoria}")
                    for consejo in consejos:
                        st.write(f"• {consejo}")
                    st.markdown("---")
                
                # Frases célebres de inversión
                st.markdown("### 💬 Sabiduría de los Grandes Inversores")
                frases = [
                    "**Warren Buffett**: 'Sé temeroso cuando otros son codiciosos, y codicioso cuando otros son temerosos.'",
                    "**Charlie Munger**: 'La inversión no es fácil. Cualquiera que crea que es fácil es un tonto.'",
                    "**Peter Lynch**: 'Detrás de cada acción hay una empresa. Descubre qué está haciendo esa empresa.'",
                    "**Benjamin Graham**: 'En el corto plazo, el mercado es una máquina de votación. En el largo plazo, es una máquina de ponderación.'",
                    "**Philip Fisher**: 'El stock market está lleno de individuos que saben el precio de todo, pero el valor de nada.'",
                    "**John Bogle**: 'No busques la aguja en el pajar. Simplemente compra el pajar.'"
                ]
                
                for frase in frases:
                    st.success(frase)

# SECCIÓN NOTICIAS ORIGINAL (COMPLETA)
elif st.session_state.seccion_actual == "noticias":
    st.header(f"📰 Noticias de {nombre}")
    
    # Función para obtener noticias de Finviz
    def obtener_noticias_finviz(ticker):
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar la tabla de noticias
                news_table = soup.find('table', {'class': 'fullview-news-outer'})
                
                if news_table:
                    noticias = []
                    rows = news_table.find_all('tr')
                    
                    for row in rows:
                        try:
                            # Extraer fecha/hora
                            fecha_td = row.find('td', {'align': 'right', 'width': '130'})
                            fecha = fecha_td.get_text(strip=True) if fecha_td else "Fecha no disponible"
                            
                            # Extraer enlace y título
                            link_container = row.find('div', {'class': 'news-link-left'})
                            if link_container:
                                link = link_container.find('a')
                                if link:
                                    titulo = link.get_text(strip=True)
                                    href = link.get('href', '')
                                    
                                    # Si el enlace es relativo, convertirlo a absoluto
                                    if href.startswith('/'):
                                        href = f"https://finviz.com{href}"
                                    
                                    # Extraer fuente
                                    fuente_container = row.find('div', {'class': 'news-link-right'})
                                    fuente = fuente_container.get_text(strip=True).strip('()') if fuente_container else "Fuente no disponible"
                                    
                                    noticias.append({
                                        'fecha': fecha,
                                        'titulo': titulo,
                                        'enlace': href,
                                        'fuente': fuente
                                    })
                        except Exception as e:
                            continue
                    
                    return noticias
                else:
                    st.error("No se pudo encontrar la tabla de noticias en Finviz")
                    return []
            else:
                st.error(f"Error al acceder a Finviz: {response.status_code}")
                return []
                
        except Exception as e:
            st.error(f"Error al obtener noticias: {str(e)}")
            return []

    # Obtener y mostrar noticias
    with st.spinner('Cargando noticias recientes...'):
        noticias = obtener_noticias_finviz(stonk)
        
        if noticias:
            st.success(f"✅ Se encontraron {len(noticias)} noticias recientes")
            
            # Mostrar estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Noticias", len(noticias))
            with col2:
                fuentes_unicas = len(set(noticia['fuente'] for noticia in noticias))
                st.metric("Fuentes Diferentes", fuentes_unicas)
            with col3:
                st.metric("Última Actualización", datetime.now().strftime("%H:%M"))
            
            st.markdown("---")
            
            # Mostrar noticias
            st.subheader("📋 Noticias Recientes")
            
            for i, noticia in enumerate(noticias[:100], 1):  # Mostrar solo las primeras 20
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        st.write(f"**{noticia['fecha']}**")
                        st.write(f"*{noticia['fuente']}*")
                    
                    with col2:
                        # Crear un enlace clickeable
                        st.markdown(f"**[{noticia['titulo']}]({noticia['enlace']})**")
                    
                    # Separador entre noticias (excepto la última)
                    if i < min(100, len(noticias)):
                        st.markdown("---")
            
            # Información adicional si hay más noticias
            if len(noticias) > 100:
                st.info(f"💡 Mostrando las 100 noticias más recientes de {len(noticias)} totales")
                
        else:
            st.warning("No se pudieron cargar las noticias. Esto puede deberse a:")
            st.write("• Problemas de conexión con Finviz")
            st.write("• Cambios en la estructura del sitio web")
            st.write("• Restricciones de acceso temporales")
            
            # Sugerencia alternativa
            st.info("💡 **Alternativa:** Puedes visitar directamente [Finviz](https://finviz.com) para ver las noticias más recientes")

# SECCIÓN DE COMPARACIÓN DE ACCIONES (COMPLETA)
elif st.session_state.seccion_actual == "comparar":
    st.header(f"📈 Comparar {nombre} con Otras Acciones")
    
    # INPUTS MEJORADOS PARA LAS ACCIONES A COMPARAR
    st.subheader("🔍 Selecciona las acciones para comparar")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        accion1 = st.text_input("Acción 1", value="AAPL", key="accion1")
    with col2:
        accion2 = st.text_input("Acción 2", value="GOOGL", key="accion2")
    with col3:
        accion3 = st.text_input("Acción 3", value="AMZN", key="accion3")
    with col4:
        accion4 = st.text_input("Acción 4", value="TSLA", key="accion4")
    with col5:
        # MÚLTIPLES ÍNDICES DE REFERENCIA
        indice_referencia = st.selectbox(
            "Índice de Referencia:",
            options=["S&P500", "NASDAQ", "DOW JONES", "RUSSELL 2000"],
            index=0,
            help="Selecciona el índice de mercado para comparación"
        )
    
    # SELECTOR DE PERÍODO
    st.subheader("📅 Configuración de Análisis")
    
    col_periodo, col_metricas = st.columns(2)
    
    with col_periodo:
        periodo_opciones = {
            "1 Mes": 30,
            "3 Meses": 90,
            "6 Meses": 180,
            "1 Año": 365,
            "3 Años": 3 * 365,
            "5 Años": 5 * 365,
            "10 Años": 10 * 365
        }
        
        periodo_seleccionado = st.selectbox(
            "Período de Comparación:",
            options=list(periodo_opciones.keys()),
            index=4,  # 3 Años por defecto
            key="selector_periodo_comparacion"
        )
    
    with col_metricas:
        # MÉTRICAS ADICIONALES PARA COMPARACIÓN
        metricas_adicionales = st.multiselect(
            "Métricas Adicionales:",
            options=["Volatilidad", "Sharpe Ratio", "Drawdown Máximo", "Beta", "Correlación"],
            default=["Volatilidad", "Sharpe Ratio"],
            help="Selecciona métricas adicionales para comparar"
        )
    
    # MAPA DE ÍNDICES
    indices_map = {
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC", 
        "DOW JONES": "^DJI",
        "RUSSELL 2000": "^RUT"
    }
    
    indice_symbol = indices_map[indice_referencia]
    
    # Calcular fecha de inicio
    start_date_comparacion = end_date - timedelta(days=periodo_opciones[periodo_seleccionado])
    
    # BOTÓN PARA EJECUTAR LA COMPARACIÓN
    if st.button("🔄 Ejecutar Análisis Comparativo Avanzado", use_container_width=True):
        with st.spinner('Cargando datos y calculando métricas comparativas...'):
            # LISTA DE TODAS LAS ACCIONES A COMPARAR
            acciones_comparar = [stonk, accion1, accion2, accion3, accion4]
            acciones_comparar = [accion for accion in acciones_comparar if accion.strip()]
            
            # Agregar índice seleccionado
            acciones_comparar.append(indice_symbol)
            
            nombres_acciones = {}
            datos_comparacion = {}
            metricas_detalladas = {}
            datos_originales = {}  # Para guardar los datos originales para las métricas de riesgo
            
            # OBTENER NOMBRES Y DATOS DE CADA ACCIÓN
            for accion in acciones_comparar:
                if accion.strip():
                    try:
                        # Obtener nombre de la acción
                        if accion in indices_map.values():
                            # Es un índice
                            nombre_idx = [k for k, v in indices_map.items() if v == accion][0]
                            nombres_acciones[accion] = f"📊 {nombre_idx}"
                        else:
                            # Es una acción
                            ticker_temp = yf.Ticker(accion)
                            info_temp = ticker_temp.info
                            nombre_accion = info_temp.get("longName", accion)
                            nombres_acciones[accion] = nombre_accion
                        
                        # Descargar datos históricos
                        data_temp = yf.download(accion, 
                                              start=start_date_comparacion.strftime('%Y-%m-%d'), 
                                              end=end_date.strftime('%Y-%m-%d'),
                                              progress=False)
                        
                        if not data_temp.empty:
                            # Guardar datos originales para métricas de riesgo
                            datos_originales[accion] = data_temp.copy()
                            
                            # Manejar MultiIndex columns
                            if isinstance(data_temp.columns, pd.MultiIndex):
                                close_columns = [col for col in data_temp.columns if 'Close' in col]
                                if close_columns:
                                    precios = data_temp[close_columns[0]]
                                else:
                                    continue
                            else:
                                if 'Close' in data_temp.columns:
                                    precios = data_temp['Close']
                                else:
                                    continue

                            if len(precios) > 0 and not precios.isna().all():
                                # Normalizar los precios a porcentaje de cambio
                                precio_inicial = precios.iloc[0]
                                if precio_inicial > 0:
                                    datos_comparacion[accion] = (precios / precio_inicial - 1) * 100
                                    
                                    # CALCULAR MÉTRICAS ADICIONALES
                                    returns = precios.pct_change().dropna()
                                    
                                    # Función para calcular drawdown máximo
                                    def calcular_drawdown_maximo(precios):
                                        try:
                                            rolling_max = precios.expanding().max()
                                            drawdown = (precios - rolling_max) / rolling_max
                                            return drawdown.min() * 100
                                        except:
                                            return 0
                                    
                                    # Función para calcular Sharpe ratio simplificado
                                    def calcular_sharpe_simple(returns, risk_free_rate=0.02):
                                        try:
                                            if len(returns) == 0:
                                                return 0
                                            excess_returns = returns - (risk_free_rate / 252)
                                            sharpe = (excess_returns.mean() / returns.std()) * np.sqrt(252)
                                            return sharpe if not np.isnan(sharpe) else 0
                                        except:
                                            return 0
                                    
                                    metricas_accion = {
                                        'Rendimiento Total': (precios.iloc[-1] / precio_inicial - 1) * 100,
                                        'Volatilidad Anual': returns.std() * np.sqrt(252) * 100,
                                        'Drawdown Máximo': calcular_drawdown_maximo(precios),
                                        'Sharpe Ratio': calcular_sharpe_simple(returns),
                                        'Beta': 0,
                                        'Correlación': 0
                                    }
                                    metricas_detalladas[accion] = metricas_accion
                                    
                            else:
                                st.warning(f"⚠️ No hay datos válidos para {accion}")
                        else:
                            st.warning(f"⚠️ No se encontraron datos para {accion}")
                                                        
                    except Exception as e:
                        st.error(f"❌ Error al cargar datos de {accion}: {str(e)}")

            # CALCULAR BETA Y CORRELACIONES
            if indice_symbol in datos_comparacion:
                for accion in [a for a in acciones_comparar if a != indice_symbol]:
                    if accion in datos_comparacion:
                        try:
                            # Calcular Beta
                            stock_returns = datos_comparacion[accion].pct_change().dropna()
                            index_returns = datos_comparacion[indice_symbol].pct_change().dropna()
                            
                            common_dates = stock_returns.index.intersection(index_returns.index)
                            if len(common_dates) > 0:
                                stock_returns = stock_returns.loc[common_dates]
                                index_returns = index_returns.loc[common_dates]
                                
                                covariance = np.cov(stock_returns, index_returns)[0, 1]
                                index_variance = np.var(index_returns)
                                beta = covariance / index_variance if index_variance != 0 else 0
                                correlation = np.corrcoef(stock_returns, index_returns)[0, 1]
                                
                                metricas_detalladas[accion]['Beta'] = beta
                                metricas_detalladas[accion]['Correlación'] = correlation
                        except:
                            pass

            # VERIFICAR QUE HAYA DATOS PARA COMPARAR
            if len(datos_comparacion) > 1:
                st.success(f"✅ Comparando {len([a for a in acciones_comparar if a in datos_comparacion])} instrumentos")
                
                # GUARDAR DATOS EN SESSION_STATE PARA USAR EN CAPM
                st.session_state.datos_comparacion = datos_comparacion
                st.session_state.nombres_acciones = nombres_acciones
                st.session_state.metricas_detalladas = metricas_detalladas
                st.session_state.acciones_comparar = acciones_comparar
                st.session_state.indice_symbol = indice_symbol
                st.session_state.indice_referencia = indice_referencia
                st.session_state.comparacion_realizada = True

    # MOSTRAR RESULTADOS DE COMPARACIÓN SI EXISTEN
    if hasattr(st.session_state, 'comparacion_realizada') and st.session_state.comparacion_realizada:
        datos_comparacion = st.session_state.datos_comparacion
        nombres_acciones = st.session_state.nombres_acciones
        metricas_detalladas = st.session_state.metricas_detalladas
        acciones_comparar = st.session_state.acciones_comparar
        indice_symbol = st.session_state.indice_symbol
        indice_referencia = st.session_state.indice_referencia
        
        # GRÁFICA DE LÍNEAS COMPARATIVA
        st.subheader("📊 Gráfica de Comparación - Rendimiento Relativo")
        
        fig = go.Figure()
        
        colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', "#ffffff", '#e377c2']
        
        for i, (accion, datos) in enumerate(datos_comparacion.items()):
            if len(datos) > 0:
                nombre_display = nombres_acciones.get(accion, accion)
                color = colores[i % len(colores)]
                
                # Configuración especial para índices
                if accion in indices_map.values():
                    line_width = 4
                    line_dash = "dash"
                    nombre_display = f"📊 {nombre_display}"
                else:
                    line_width = 3
                    line_dash = "solid"
                
                fig.add_trace(go.Scatter(
                    x=datos.index,
                    y=datos.values,
                    mode='lines',
                    name=nombre_display,
                    line=dict(
                        color=color, 
                        width=line_width,
                        dash=line_dash
                    ),
                    hovertemplate=(
                        f"<b>{nombre_display}</b><br>" +
                        "Fecha: %{x}<br>" +
                        "Rendimiento: %{y:.2f}%<br>" +
                        "<extra></extra>"
                    )
                ))
         
        if len(fig.data) > 0:
            fig.update_layout(
                title=f'Comparación de Rendimiento vs {indice_referencia} - Período: {periodo_seleccionado}',
                xaxis_title='Fecha',
                yaxis_title='Rendimiento (%)',
                height=600,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # ANÁLISIS COMPARATIVO
            st.subheader("📈 Análisis de Performance vs Índice")
            
            if indice_symbol in datos_comparacion:
                index_data = datos_comparacion[indice_symbol]
                index_final = index_data.iloc[-1] if len(index_data) > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    mejor_performer = None
                    mejor_rendimiento = -float('inf')
                    
                    for accion, datos in datos_comparacion.items():
                        if accion != indice_symbol:
                            rendimiento_final = datos.iloc[-1] if len(datos) > 0 else 0
                            if rendimiento_final > mejor_rendimiento:
                                mejor_rendimiento = rendimiento_final
                                mejor_performer = accion
                    
                    if mejor_performer:
                        vs_index = mejor_rendimiento - index_final
                        st.metric(
                            "🏆 Mejor Performer", 
                            f"{nombres_acciones.get(mejor_performer, mejor_performer)}",
                            f"{vs_index:+.2f}% vs índice"
                        )
                
                with col2:
                    st.metric(
                        f"📊 Rendimiento {indice_referencia}", 
                        f"{index_final:.2f}%",
                        "Referencia mercado"
                    )
                
                with col3:
                    # Contar acciones que superaron al índice
                    acciones_superiores = 0
                    total_acciones = 0
                    
                    for accion, datos in datos_comparacion.items():
                        if accion != indice_symbol:
                            total_acciones += 1
                            rendimiento_final = datos.iloc[-1] if len(datos) > 0 else 0
                            if rendimiento_final > index_final:
                                acciones_superiores += 1
                    
                    if total_acciones > 0:
                        porcentaje_superiores = (acciones_superiores / total_acciones) * 100
                        st.metric(
                            "📈 Superan Índice", 
                            f"{acciones_superiores}/{total_acciones}",
                            f"{porcentaje_superiores:.1f}%"
                        )
                
                with col4:
                    # Volatilidad promedio vs índice
                    if indice_symbol in metricas_detalladas:
                        vol_index = metricas_detalladas[indice_symbol]['Volatilidad Anual']
                        vol_promedio = np.mean([m['Volatilidad Anual'] for a, m in metricas_detalladas.items() 
                                               if a != indice_symbol])
                        diff_vol = vol_promedio - vol_index
                        
                        st.metric(
                            "📉 Volatilidad Promedio", 
                            f"{vol_promedio:.1f}%",
                            f"{diff_vol:+.1f}% vs índice"
                        )

        # TABLA DE MÉTRICAS COMPARATIVAS
        st.subheader("📋 Métricas Comparativas Detalladas")
        
        # Crear tabla de métricas
        metricas_tabla = []
        for accion in [a for a in acciones_comparar if a in metricas_detalladas]:
            metricas = metricas_detalladas[accion]
            es_indice = accion in indices_map.values()
            
            metricas_tabla.append({
                'Instrumento': nombres_acciones.get(accion, accion),
                'Tipo': 'Índice' if es_indice else 'Acción',
                'Rendimiento (%)': f"{metricas['Rendimiento Total']:.2f}%",
                'Volatilidad (%)': f"{metricas['Volatilidad Anual']:.1f}%",
                'Sharpe Ratio': f"{metricas['Sharpe Ratio']:.2f}",
                'Drawdown Máx (%)': f"{metricas['Drawdown Máximo']:.1f}%",
                'Beta': f"{metricas['Beta']:.2f}" if not es_indice else "N/A",
                'Correlación': f"{metricas['Correlación']:.2f}" if not es_indice else "N/A"
            })
        
        if metricas_tabla:
            df_metricas = pd.DataFrame(metricas_tabla)
            st.dataframe(df_metricas, use_container_width=True)
            
        # ANÁLISIS DE CORRELACIÓN
        st.subheader("🔗 Análisis de Correlación")

        if len([a for a in acciones_comparar if a != indice_symbol and a in datos_comparacion]) > 1:
            acciones_validas = [a for a in acciones_comparar if a != indice_symbol and a in datos_comparacion]
            
            if len(acciones_validas) > 1:
                precios_originales = {}
                
                for accion in acciones_validas:
                    try:
                        # Descargar datos frescos para obtener precios originales
                        data_temp = yf.download(accion, 
                                            start=start_date_comparacion.strftime('%Y-%m-%d'), 
                                            end=end_date.strftime('%Y-%m-%d'),
                                            progress=False)
                        
                        if not data_temp.empty:
                            # Obtener precios de cierre originales
                            if isinstance(data_temp.columns, pd.MultiIndex):
                                close_columns = [col for col in data_temp.columns if 'Close' in col]
                                if close_columns:
                                    precios = data_temp[close_columns[0]]
                                else:
                                    continue
                            else:
                                if 'Close' in data_temp.columns:
                                    precios = data_temp['Close']
                                else:
                                    continue
                            
                            precios_originales[accion] = precios
                    except Exception as e:
                        st.warning(f"Error obteniendo precios para {accion}: {str(e)}")
                
                # Calcular matriz de correlación con precios originales
                corr_matrix = np.zeros((len(acciones_validas), len(acciones_validas)))
                nombres_display = [nombres_acciones.get(a, a) for a in acciones_validas]
                
                for i, accion1 in enumerate(acciones_validas):
                    for j, accion2 in enumerate(acciones_validas):
                        if i == j:
                            corr_matrix[i, j] = 1.0
                        else:
                            try:
                                if accion1 in precios_originales and accion2 in precios_originales:
                                    precios1 = precios_originales[accion1]
                                    precios2 = precios_originales[accion2]
                                    
                                    # Alinear fechas
                                    common_dates = precios1.index.intersection(precios2.index)
                                    if len(common_dates) > 10:
                                        precios1_aligned = precios1.loc[common_dates]
                                        precios2_aligned = precios2.loc[common_dates]
                                        
                                        # Calcular rendimientos logarítmicos diarios para mejor correlación
                                        returns1 = np.log(precios1_aligned / precios1_aligned.shift(1)).dropna()
                                        returns2 = np.log(precios2_aligned / precios2_aligned.shift(1)).dropna()
                                        
                                        # Alinear después del cálculo
                                        common_returns = returns1.index.intersection(returns2.index)
                                        if len(common_returns) > 0:
                                            returns1_final = returns1.loc[common_returns]
                                            returns2_final = returns2.loc[common_returns]
                                            
                                            # Calcular correlación de Pearson
                                            corr = returns1_final.corr(returns2_final)
                                            corr_matrix[i, j] = corr if not np.isnan(corr) else 0
                                else:
                                    corr_matrix[i, j] = 0
                            except Exception as e:
                                corr_matrix[i, j] = 0
                
                # Solo mostrar la gráfica si hay correlaciones no cero
                if not np.all(corr_matrix == 0):
                    # GRÁFICA DE CORRELACIÓN
                    fig_corr = go.Figure()
                    
                    fig_corr.add_trace(go.Heatmap(
                        z=corr_matrix,
                        x=nombres_display,
                        y=nombres_display,
                        colorscale='RdBu_r',
                        zmin=-1,
                        zmax=1,
                        hoverongaps=False,
                        hovertemplate=(
                            '<b>%{y}</b> vs <b>%{x}</b><br>' +
                            'Correlación: %{z:.3f}<extra></extra>'
                        ),
                        colorbar=dict(title="Correlación")
                    ))
                    
                    # Agregar anotaciones con valores
                    for i in range(len(acciones_validas)):
                        for j in range(len(acciones_validas)):
                            color = 'white' if abs(corr_matrix[i, j]) > 0.5 else 'black'
                            fig_corr.add_annotation(
                                x=j,
                                y=i,
                                text=f"{corr_matrix[i, j]:.2f}",
                                showarrow=False,
                                font=dict(color=color, size=10)
                            )
                    
                    fig_corr.update_layout(
                        title='Matriz de Correlación entre Acciones (Rendimientos Diarios)',
                        xaxis_title='',
                        yaxis_title='',
                        height=500,
                        width=600,
                        xaxis=dict(tickangle=45),
                        yaxis=dict(tickangle=0)
                    )
                    
                    st.plotly_chart(fig_corr, use_container_width=True)
                    
                    # RESUMEN DE CORRELACIONES
                    st.subheader("📊 Resumen de Correlaciones")
                    
                    correlaciones_positivas = []
                    correlaciones_negativas = []
                    todas_correlaciones = []
                    
                    for i in range(len(acciones_validas)):
                        for j in range(i+1, len(acciones_validas)):
                            corr_val = corr_matrix[i, j]
                            todas_correlaciones.append(corr_val)
                            if corr_val > 0:
                                correlaciones_positivas.append(corr_val)
                            elif corr_val < 0:
                                correlaciones_negativas.append(corr_val)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if todas_correlaciones:
                            st.metric(
                                "📊 Correlación Promedio",
                                f"{np.mean(todas_correlaciones):.3f}",
                                f"Rango: {min(todas_correlaciones):.3f} a {max(todas_correlaciones):.3f}"
                            )
                    
                    with col2:
                        if correlaciones_positivas:
                            st.metric(
                                "📈 Correlaciones Positivas",
                                f"{len(correlaciones_positivas)}",
                                f"Promedio: {np.mean(correlaciones_positivas):.3f}"
                            )
                        else:
                            st.metric("📈 Correlaciones Positivas", "0", "Sin correlaciones positivas")
                    
                    with col3:
                        if correlaciones_negativas:
                            st.metric(
                                "📉 Correlaciones Negativas",
                                f"{len(correlaciones_negativas)}",
                                f"Promedio: {np.mean(correlaciones_negativas):.3f}"
                            )
                        else:
                            st.metric("📉 Correlaciones Negativas", "0", "Sin correlaciones negativas")
                    
                    # INTERPRETACIÓN
                    st.info("""
                    **💡 Interpretación de Correlaciones:**
                    - **+1.0**: Movimientos idénticos
                    - **+0.7 a +1.0**: Fuerte correlación positiva
                    - **+0.3 a +0.7**: Correlación moderada positiva  
                    - **-0.3 a +0.3**: Correlación débil o nula
                    - **-0.7 a -0.3**: Correlación moderada negativa
                    - **-1.0 a -0.7**: Fuerte correlación negativa
                    """)
                else:
                    st.warning("⚠️ No se pudieron calcular correlaciones significativas")
            else:
                st.info("ℹ️ Se necesitan al menos 2 acciones válidas para calcular correlaciones")
                    
        # ANÁLISIS DE RIESGO-RENDIMIENTO
        st.subheader("🎯 Análisis Riesgo-Rendimiento")
        
        # Crear gráfica de riesgo-rendimiento
        fig_scatter = go.Figure()
        
        # Definir colores según tipo de instrumento
        for accion in [a for a in acciones_comparar if a in metricas_detalladas]:
            metricas = metricas_detalladas[accion]
            es_indice = accion in indices_map.values()
            
            # Configurar propiedades según tipo
            if es_indice:
                color = 'red'
                simbolo = 'star'
                tamaño = 20
                nombre = nombres_acciones.get(accion, accion)
            else:
                color = 'blue'
                simbolo = 'circle'
                tamaño = 15
                nombre = nombres_acciones.get(accion, accion)
            
            fig_scatter.add_trace(go.Scatter(
                x=[metricas['Volatilidad Anual']],
                y=[metricas['Rendimiento Total']],
                mode='markers+text',
                name=nombre,
                marker=dict(
                    size=tamaño,
                    color=color,
                    symbol=simbolo,
                    line=dict(width=2, color='darkgray')
                ),
                text=nombre,
                textposition="top center",
                hovertemplate=(
                    f"<b>{nombre}</b><br>" +
                    "Volatilidad: %{x:.1f}%<br>" +
                    "Rendimiento: %{y:.2f}%<br>" +
                    "Sharpe: " + f"{metricas['Sharpe Ratio']:.2f}" + "<br>" +
                    "<extra></extra>"
                )
            ))
        
        # Agregar línea de eficiencia teórica
        if len([a for a in acciones_comparar if a not in indices_map.values() and a in metricas_detalladas]) > 1:
            # Calcular línea de tendencia para acciones (excluyendo índices)
            acciones_no_indices = [a for a in acciones_comparar if a not in indices_map.values() and a in metricas_detalladas]
            volatilidades = [metricas_detalladas[a]['Volatilidad Anual'] for a in acciones_no_indices]
            rendimientos = [metricas_detalladas[a]['Rendimiento Total'] for a in acciones_no_indices]
            
            if len(volatilidades) > 1:
                # Calcular línea de tendencia
                z = np.polyfit(volatilidades, rendimientos, 1)
                p = np.poly1d(z)
                
                x_line = np.linspace(min(volatilidades), max(volatilidades), 50)
                y_line = p(x_line)
                
                fig_scatter.add_trace(go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode='lines',
                    name='Línea de Tendencia',
                    line=dict(color='gray', dash='dash', width=1),
                    hovertemplate="Línea de tendencia<extra></extra>"
                ))
        
        fig_scatter.update_layout(
            title='Análisis Riesgo-Rendimiento',
            xaxis_title='Volatilidad Anual (%)',
            yaxis_title='Rendimiento Total (%)',
            height=500,
            showlegend=True,
            hovermode='closest'
        )
        
        # Agregar cuadrantes de referencia
        fig_scatter.add_hline(y=0, line_dash="dot", line_color="green", 
                            annotation_text="Break Even", annotation_position="left")
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # INTERPRETACIÓN DEL ANÁLISIS RIESGO-RENDIMIENTO
        st.info("""
        **💡 Interpretación del Gráfico Riesgo-Rendimiento:**
        - **Arriba a la izquierda**: Alto rendimiento con bajo riesgo (Ideal)
        - **Arriba a la derecha**: Alto rendimiento con alto riesgo 
        - **Abajo a la izquierda**: Bajo rendimiento con bajo riesgo (Conservador)
        - **Abajo a la derecha**: Bajo rendimiento con alto riesgo (Evitar)
        - **Estrella roja**: Índice de referencia del mercado
        """)

        # BOTÓN DE DESCARGA
        st.markdown("---")
        st.subheader("💾 Exportar Análisis Comparativo")
        
        # Crear DataFrame para exportación
        df_export = pd.DataFrame()
        for accion, datos in datos_comparacion.items():
            temp_df = pd.DataFrame({
                'Fecha': datos.index,
                nombres_acciones.get(accion, accion): datos.values
            })
            
            if df_export.empty:
                df_export = temp_df
            else:
                df_export = pd.merge(df_export, temp_df, on='Fecha', how='outer')
        
        if not df_export.empty:
            df_export = df_export.sort_values('Fecha').reset_index(drop=True)
            
            csv_comparacion = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos de comparación como CSV",
                data=csv_comparacion,
                file_name=f"comparacion_{stonk}_vs_{indice_referencia.lower()}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # =============================================
        # NUEVA SECCIÓN: ANÁLISIS CAPM COMPARATIVO
        # =============================================
        st.markdown("---")
        st.subheader("📊 Análisis CAPM Comparativo")

        # Selectores para CAPM comparativo - CON STATE MANAGEMENT
        st.markdown("**🕐 Configuración del Análisis CAPM:**")

        col_capm1, col_capm2, col_capm3 = st.columns(3)

        with col_capm1:
            # Inicializar en session_state si no existe
            if 'periodo_capm_comp' not in st.session_state:
                st.session_state.periodo_capm_comp = "1 año"
                
            periodo_capm_comp = st.selectbox(
                "Período de datos CAPM:",
                options=["1 mes", "3 meses", "6 meses", "1 año", "2 años", "3 años", "5 años", "10 años"],
                index=3,
                key="periodo_capm_comparar"
            )
            st.session_state.periodo_capm_comp = periodo_capm_comp

        with col_capm2:
            if 'frecuencia_capm_comp' not in st.session_state:
                st.session_state.frecuencia_capm_comp = "Diario"
                
            frecuencia_capm_comp = st.selectbox(
                "Frecuencia de datos CAPM:",
                options=["Diario", "Semanal", "Mensual"],
                index=0,
                key="frecuencia_capm_comparar"
            )
            st.session_state.frecuencia_capm_comp = frecuencia_capm_comp

        with col_capm3:
            if 'tasa_libre_riesgo_comp' not in st.session_state:
                st.session_state.tasa_libre_riesgo_comp = 2.0
            if 'prima_riesgo_mercado_comp' not in st.session_state:
                st.session_state.prima_riesgo_mercado_comp = 6.0
                
            tasa_libre_riesgo_comp = st.number_input(
                "Tasa Libre Riesgo (%)", 
                min_value=0.0, 
                max_value=10.0, 
                value=st.session_state.tasa_libre_riesgo_comp, 
                step=0.1,
                help="Para cálculo CAPM comparativo",
                key="tasa_libre_comp"
            ) / 100
            st.session_state.tasa_libre_riesgo_comp = tasa_libre_riesgo_comp * 100
            
            prima_riesgo_mercado_comp = st.number_input(
                "Prima Riesgo Mercado (%)", 
                min_value=0.0, 
                max_value=15.0, 
                value=st.session_state.prima_riesgo_mercado_comp, 
                step=0.1,
                help="Para cálculo CAPM comparativo",
                key="prima_riesgo_comp"
            ) / 100
            st.session_state.prima_riesgo_mercado_comp = prima_riesgo_mercado_comp * 100

        # BOTÓN PARA CALCULAR CAPM - SEPARADO DEL BOTÓN PRINCIPAL
        if st.button("🧮 Calcular CAPM Comparativo", type="secondary", use_container_width=True):
            with st.spinner('Calculando CAPM comparativo...'):
                # Mapear selecciones a parámetros
                periodo_map = {
                    "1 mes": 30,
                    "3 meses": 90,
                    "6 meses": 180,
                    "1 año": 365,
                    "2 años": 730,
                    "3 años": 1095,
                    "5 años": 1825,
                    "10 años": 3650
                }

                frecuencia_map = {
                    "Diario": "1d",
                    "Semanal": "1wk", 
                    "Mensual": "1mo"
                }

                dias_periodo_comp = periodo_map[st.session_state.periodo_capm_comp]
                intervalo_comp = frecuencia_map[st.session_state.frecuencia_capm_comp]

                # Función para calcular CAPM comparativo
                def calcular_capm_comparativo(simbolo, indice_symbol, dias_periodo, intervalo):
                    """Calcula métricas CAPM para comparación"""
                    try:
                        start_date = datetime.today() - timedelta(days=dias_periodo)
                        end_date = datetime.today()
                        
                        # Descargar datos
                        stock_data = yf.download(simbolo, start=start_date, end=end_date, interval=intervalo)
                        market_data = yf.download(indice_symbol, start=start_date, end=end_date, interval=intervalo)
                        
                        if stock_data.empty or market_data.empty:
                            return None
                        
                        # Obtener precios de cierre
                        if isinstance(stock_data.columns, pd.MultiIndex):
                            stock_close = stock_data[('Close', simbolo)]
                        else:
                            stock_close = stock_data['Close']
                            
                        if isinstance(market_data.columns, pd.MultiIndex):
                            market_close = market_data[('Close', indice_symbol)]
                        else:
                            market_close = market_data['Close']
                        
                        # Calcular rendimientos
                        stock_returns = stock_close.pct_change().dropna()
                        market_returns = market_close.pct_change().dropna()
                        
                        # Alinear fechas
                        common_dates = stock_returns.index.intersection(market_returns.index)
                        stock_returns = stock_returns.loc[common_dates]
                        market_returns = market_returns.loc[common_dates]
                        
                        if len(stock_returns) < 5:
                            return None
                        
                        # Calcular Beta histórico
                        if len(market_returns) > 1:
                            beta_real, intercepto = np.polyfit(market_returns, stock_returns, 1)
                            r_squared = np.corrcoef(market_returns, stock_returns)[0, 1] ** 2
                        else:
                            beta_real = 1.0
                            r_squared = 0
                        
                        # Calcular CAPM
                        costo_capital = st.session_state.tasa_libre_riesgo_comp/100 + beta_real * st.session_state.prima_riesgo_mercado_comp/100
                        
                        return {
                            'beta_historico': beta_real,
                            'r_squared': r_squared,
                            'costo_capital': costo_capital,
                            'puntos_datos': len(stock_returns),
                            'rendimiento_promedio': stock_returns.mean() * 100,
                            'volatilidad': stock_returns.std() * 100,
                            'stock_returns': stock_returns,
                            'market_returns': market_returns,
                            'fechas': common_dates
                        }
                        
                    except Exception as e:
                        st.error(f"Error calculando CAPM para {simbolo}: {str(e)}")
                        return None

                # Calcular CAPM para todas las acciones
                datos_capm_comparativo = {}
                
                for accion in [a for a in acciones_comparar if a not in indices_map.values()]:
                    if accion in datos_comparacion:  # Solo acciones con datos válidos
                        datos_capm = calcular_capm_comparativo(accion, indice_symbol, dias_periodo_comp, intervalo_comp)
                        if datos_capm:
                            datos_capm_comparativo[accion] = datos_capm

                # GUARDAR RESULTADOS CAPM EN SESSION_STATE
                st.session_state.datos_capm_comparativo = datos_capm_comparativo
                st.session_state.capm_calculado = True

        # MOSTRAR RESULTADOS CAPM SI EXISTEN
        if hasattr(st.session_state, 'capm_calculado') and st.session_state.capm_calculado:
            datos_capm_comparativo = st.session_state.datos_capm_comparativo
            
            if len(datos_capm_comparativo) > 1:
                st.success(f"✅ CAPM calculado para {len(datos_capm_comparativo)} acciones")

                # =============================================
                # GRÁFICA SCATTER PLOT CAPM COMPARATIVO
                # =============================================
                st.subheader("📈 Gráfica CAPM - Scatter Plot Comparativo")
                
                # Crear gráfica scatter plot comparativa
                fig_scatter_capm = go.Figure()
                
                colores = ["#C25327", "#4EBD38", '#45B7D1', "#912727", "#AD8C20", '#DDA0DD', "#721FAA"]
                
                # Agregar puntos de datos para cada acción
                for i, (accion, datos) in enumerate(datos_capm_comparativo.items()):
                    color = colores[i % len(colores)]
                    
                    # Agregar scatter plot con todos los puntos históricos
                    fig_scatter_capm.add_trace(go.Scatter(
                        x=datos['market_returns'] * 100,  # Rendimiento del mercado
                        y=datos['stock_returns'] * 100,   # Rendimiento de la acción
                        mode='markers',
                        name=f"{nombres_acciones.get(accion, accion)} ({len(datos['stock_returns'])} pts)",
                        marker=dict(
                            size=6,
                            color=color,
                            opacity=0.6,
                            line=dict(width=1, color='darkgray')
                        ),
                        hovertemplate=(
                            f'<b>{nombres_acciones.get(accion, accion)}</b><br>' +
                            'Fecha: %{text}<br>' +
                            'Rend. Mercado: %{x:.2f}%<br>' +
                            'Rend. Acción: %{y:.2f}%<br>' +
                            '<extra></extra>'
                        ),
                        text=[date.strftime('%d/%m/%Y') for date in datos['fechas']],
                        showlegend=True
                    ))
                    
                    # Agregar línea de regresión para cada acción
                    if len(datos['market_returns']) > 1:
                        beta_real = datos['beta_historico']
                        intercepto = np.polyfit(datos['market_returns'], datos['stock_returns'], 1)[1]
                        
                        x_line = np.linspace(datos['market_returns'].min(), datos['market_returns'].max(), 50)
                        y_line = intercepto + beta_real * x_line
                        
                        fig_scatter_capm.add_trace(go.Scatter(
                            x=x_line * 100,
                            y=y_line * 100,
                            mode='lines',
                            name=f"Regresión {nombres_acciones.get(accion, accion)} (β={beta_real:.2f})",
                            line=dict(color=color, width=2, dash='dash'),
                            showlegend=True,
                            hovertemplate=f'Beta: {beta_real:.2f}<extra></extra>'
                        ))

                # Agregar línea CAPM teórica general
                x_capm = np.linspace(-0.2, 0.2, 50)  # Rango razonable para rendimientos
                y_capm = st.session_state.tasa_libre_riesgo_comp/100/252 + 1.0 * (x_capm - st.session_state.tasa_libre_riesgo_comp/100/252)  # Beta = 1 para mercado
                
                fig_scatter_capm.add_trace(go.Scatter(
                    x=x_capm * 100,
                    y=y_capm * 100,
                    mode='lines',
                    name='Línea Mercado (β=1.0)',
                    line=dict(color='black', width=3),
                    hovertemplate='Mercado teórico<extra></extra>'
                ))

                # Línea de referencia en cero
                fig_scatter_capm.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
                fig_scatter_capm.add_vline(x=0, line_dash="dot", line_color="gray", opacity=0.5)

                fig_scatter_capm.update_layout(
                    title=f'CAPM Comparativo - {st.session_state.periodo_capm_comp} ({st.session_state.frecuencia_capm_comp})',
                    xaxis_title=f'Rendimiento del Mercado ({indice_referencia}) (%)',
                    yaxis_title='Rendimiento de las Acciones (%)',
                    height=600,
                    showlegend=True,
                    hovermode='closest',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    xaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='lightgray',
                        zeroline=True,
                        zerolinewidth=2,
                        zerolinecolor='black'
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='lightgray',
                        zeroline=True,
                        zerolinewidth=2,
                        zerolinecolor='black'
                    )
                )

                st.plotly_chart(fig_scatter_capm, use_container_width=True)

                # Interpretación de la gráfica scatter
                st.info("""
                **💡 Interpretación del Scatter Plot CAPM:**
                
                - **🔵 Puntos**: Cada punto representa un período (día/semana/mes) histórico
                - **📈 Eje X**: Rendimiento del mercado en ese período
                - **📈 Eje Y**: Rendimiento de la acción en ese período  
                - **📊 Líneas punteadas**: Líneas de regresión (Beta histórico de cada acción)
                - **⚫ Línea negra**: Comportamiento teórico del mercado (Beta = 1.0)
                
                **Patrones a observar:**
                - **Puntos alineados con pendiente positiva**: Acción que sigue al mercado
                - **Puntos dispersos**: Acción con comportamiento independiente
                - **Pendiente > 1**: Acción más volátil que el mercado
                - **Pendiente < 1**: Acción menos volátil que el mercado
                """)

                # =============================================
                # TABLA COMPARATIVA CAPM
                # =============================================
                st.subheader("📋 Tabla Comparativa CAPM")
                
                # Crear tabla comparativa
                tabla_comparativa = []
                for accion, datos in datos_capm_comparativo.items():
                    # Obtener Beta de Yahoo Finance para comparación
                    try:
                        ticker_temp = yf.Ticker(accion)
                        info_temp = ticker_temp.info
                        beta_yahoo = info_temp.get('beta', datos['beta_historico'])
                        diferencia_beta = datos['beta_historico'] - beta_yahoo
                    except:
                        beta_yahoo = datos['beta_historico']
                        diferencia_beta = 0
                    
                    # Determinar categoría de riesgo
                    if datos['beta_historico'] < 0.8:
                        categoria_riesgo = "🛡️ Defensiva"
                    elif datos['beta_historico'] < 1.2:
                        categoria_riesgo = "⚖️ Moderada"
                    else:
                        categoria_riesgo = "🚀 Agresiva"
                    
                    # Determinar calidad del ajuste
                    if datos['r_squared'] > 0.7:
                        calidad_ajuste = "✅ Alto"
                    elif datos['r_squared'] > 0.4:
                        calidad_ajuste = "⚠️ Moderado"
                    else:
                        calidad_ajuste = "❌ Bajo"
                    
                    tabla_comparativa.append({
                        'Acción': nombres_acciones.get(accion, accion),
                        'Beta Histórico': f"{datos['beta_historico']:.2f}",
                        'Beta Yahoo': f"{beta_yahoo:.2f}",
                        'Diferencia β': f"{diferencia_beta:+.2f}",
                        'Costo Capital': f"{datos['costo_capital']*100:.1f}%",
                        'R²': f"{datos['r_squared']:.3f}",
                        'Calidad Ajuste': calidad_ajuste,
                        'Categoría Riesgo': categoria_riesgo,
                        'Rend. Promedio': f"{datos['rendimiento_promedio']:.2f}%",
                        'Puntos Datos': datos['puntos_datos']
                    })
                
                # Mostrar tabla
                df_comparativo = pd.DataFrame(tabla_comparativa)
                st.dataframe(df_comparativo, use_container_width=True)

                # =============================================
                # ANÁLISIS COMPARATIVO
                # =============================================
                st.subheader("🎯 Análisis Comparativo CAPM")
                
                col_anal1, col_anal2 = st.columns(2)
                
                with col_anal1:
                    # Encontrar acciones con mejor relación riesgo/retorno
                    st.markdown("**🏆 Mejores Relaciones Riesgo/Retorno:**")
                    
                    # Calcular ratio Sharpe simplificado (retorno/volatilidad)
                    acciones_ratio = []
                    for accion, datos in datos_capm_comparativo.items():
                        if datos['volatilidad'] > 0:
                            ratio = abs(datos['rendimiento_promedio'] / datos['volatilidad'])
                            acciones_ratio.append((accion, ratio, datos['rendimiento_promedio']))
                    
                    # Ordenar por mejor ratio
                    acciones_ratio.sort(key=lambda x: x[1], reverse=True)
                    
                    for i, (accion, ratio, rendimiento) in enumerate(acciones_ratio[:3]):
                        st.write(f"{i+1}. **{nombres_acciones.get(accion, accion)}**")
                        st.write(f"   Ratio: {ratio:.2f} | Rendimiento: {rendimiento:.2f}%")
                
                with col_anal2:
                    # Análisis de consistencia Beta
                    st.markdown("**📊 Consistencia del Beta:**")
                    
                    acciones_consistentes = []
                    for accion, datos in datos_capm_comparativo.items():
                        try:
                            ticker_temp = yf.Ticker(accion)
                            info_temp = ticker_temp.info
                            beta_yahoo = info_temp.get('beta', datos['beta_historico'])
                            diferencia = abs(datos['beta_historico'] - beta_yahoo)
                            acciones_consistentes.append((accion, diferencia, datos['r_squared']))
                        except:
                            continue
                    
                    # Ordenar por menor diferencia (más consistentes)
                    acciones_consistentes.sort(key=lambda x: x[1])
                    
                    for i, (accion, diferencia, r2) in enumerate(acciones_consistentes[:3]):
                        st.write(f"{i+1}. **{nombres_acciones.get(accion, accion)}**")
                        st.write(f"   Dif. β: {diferencia:.2f} | R²: {r2:.3f}")

                # =============================================
                # COMPARATIVA DE BETAS
                # =============================================
                st.subheader("📈 Comparativa de Betas")
                
                fig_betas = go.Figure()
                
                colores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
                
                for i, (accion, datos) in enumerate(datos_capm_comparativo.items()):
                    color = colores[i % len(colores)]
                    
                    # Obtener Beta Yahoo
                    try:
                        ticker_temp = yf.Ticker(accion)
                        info_temp = ticker_temp.info
                        beta_yahoo = info_temp.get('beta', datos['beta_historico'])
                    except:
                        beta_yahoo = datos['beta_historico']
                    
                    fig_betas.add_trace(go.Bar(
                        name=nombres_acciones.get(accion, accion),
                        x=['Beta Histórico', 'Beta Yahoo'],
                        y=[datos['beta_historico'], beta_yahoo],
                        marker_color=[color, color],
                        hovertemplate='%{x}: %{y:.2f}<extra></extra>'
                    ))
                
                fig_betas.update_layout(
                    title='Comparativa Beta Histórico vs Beta Yahoo Finance',
                    yaxis_title='Valor Beta (β)',
                    height=500,
                    showlegend=True,
                    barmode='group'
                )
                
                st.plotly_chart(fig_betas, use_container_width=True)

                # =============================================
                # RECOMENDACIONES FINALES CAPM
                # =============================================
                st.markdown("---")
                st.subheader("💡 Recomendaciones de Inversión CAPM")
                
                # Encontrar la acción con mejor perfil riesgo/retorno
                mejor_accion = None
                mejor_puntaje = -float('inf')
                
                for accion, datos in datos_capm_comparativo.items():
                    # Puntaje basado en R², rendimiento y consistencia Beta
                    puntaje = (datos['r_squared'] * 100 + 
                            min(datos['rendimiento_promedio'], 20) +  # Cap rendimiento en 20%
                            (1 - min(abs(datos['beta_historico'] - 1), 1)) * 20)  # Preferir Beta cerca de 1
                    
                    if puntaje > mejor_puntaje:
                        mejor_puntaje = puntaje
                        mejor_accion = accion
                
                if mejor_accion:
                    datos_mejor = datos_capm_comparativo[mejor_accion]
                    st.success(f"""
                    **🏅 MEJOR PERFIL CAPM: {nombres_acciones.get(mejor_accion, mejor_accion)}**
                    
                    • **Costo de capital**: {datos_mejor['costo_capital']*100:.1f}%
                    • **Beta histórico**: {datos_mejor['beta_historico']:.2f}
                    • **Calidad ajuste**: {datos_mejor['r_squared']:.3f}
                    • **Rendimiento promedio**: {datos_mejor['rendimiento_promedio']:.2f}%
                    
                    **Recomendación**: Esta acción muestra la mejor combinación de relación riesgo-retorno y consistencia con el modelo CAPM.
                    """)

                # Exportar datos CAPM
                st.markdown("---")
                st.subheader("💾 Exportar Análisis CAPM Comparativo")
                
                df_export_capm = pd.DataFrame([
                    {
                        'Acción': nombres_acciones.get(accion, accion),
                        'Beta_Historico': datos['beta_historico'],
                        'Costo_Capital_%': datos['costo_capital'] * 100,
                        'R_Cuadrado': datos['r_squared'],
                        'Rendimiento_Promedio_%': datos['rendimiento_promedio'],
                        'Volatilidad_%': datos['volatilidad'],
                        'Puntos_Datos': datos['puntos_datos'],
                        'Periodo': st.session_state.periodo_capm_comp,
                        'Frecuencia': st.session_state.frecuencia_capm_comp
                    }
                    for accion, datos in datos_capm_comparativo.items()
                ])
                
                csv_capm = df_export_capm.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar datos CAPM comparativo (CSV)",
                    data=csv_capm,
                    file_name=f"capm_comparativo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            else:
                st.warning("No hay suficientes datos CAPM para realizar la comparación")

# SECCIÓN DE ANÁLISIS TÉCNICO (COMPLETA)
elif st.session_state.seccion_actual == "tecnico":
    st.header(f"📈 Análisis Técnico - {nombre}")
    
    try:
        # Obtener datos
        data = yf.download(stonk, period="1y", interval="1d")
        
        if data.empty:
            st.warning("No se encontraron datos para análisis técnico")
        else:
            # Verificar la estructura de los datos
            st.write(f"📊 Estructura de datos: {data.shape[0]} filas, {data.shape[1]} columnas")
            
            # Si los datos tienen MultiIndex, simplificarlos
            if isinstance(data.columns, pd.MultiIndex):
                # Tomar solo la primera columna de cada tipo si hay múltiples
                simple_data = pd.DataFrame()
                for col_type in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    cols = [col for col in data.columns if col_type in col]
                    if cols:
                        simple_data[col_type] = data[cols[0]]
                data = simple_data
            
            # Calcular indicadores
            data_tech = calcular_indicadores_tecnicos(data)
            
            if data_tech.empty:
                st.error("No se pudieron calcular los indicadores técnicos")
            else:
                # Selector de indicadores
                st.subheader("🔧 Indicadores Técnicos")
                indicadores = st.multiselect(
                    "Selecciona los indicadores a mostrar:",
                    ["RSI", "MACD", "Bandas Bollinger", "Medias Móviles"],
                    default=["RSI", "MACD"]
                )
                
                # Crear gráfica principal
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.1,
                    subplot_titles=('Precio e Indicadores', 'RSI y MACD'),
                    row_heights=[0.6, 0.4]
                )
                
                # Gráfica de velas (fila 1)
                fig.add_trace(go.Candlestick(
                    x=data_tech.index,
                    open=data_tech['Open'],
                    high=data_tech['High'],
                    low=data_tech['Low'],
                    close=data_tech['Close'],
                    name='Precio'
                ), row=1, col=1)
                
                # Bandas de Bollinger
                if "Bandas Bollinger" in indicadores and all(col in data_tech.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
                    fig.add_trace(go.Scatter(
                        x=data_tech.index, y=data_tech['BB_Upper'],
                        line=dict(color='rgba(255,0,0,0.5)', width=1),
                        name='BB Superior',
                        legendgroup="bollinger"
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=data_tech.index, y=data_tech['BB_Middle'],
                        line=dict(color='rgba(0,255,0,0.5)', width=1),
                        name='BB Media',
                        legendgroup="bollinger"
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=data_tech.index, y=data_tech['BB_Lower'],
                        line=dict(color='rgba(0,0,255,0.5)', width=1),
                        name='BB Inferior',
                        fill='tonexty',
                        fillcolor='rgba(0,100,80,0.1)',
                        legendgroup="bollinger"
                    ), row=1, col=1)
                
                # Medias Móviles
                if "Medias Móviles" in indicadores:
                    if 'SMA_20' in data_tech.columns:
                        fig.add_trace(go.Scatter(
                            x=data_tech.index, y=data_tech['SMA_20'],
                            line=dict(color='orange', width=2),
                            name='SMA 20'
                        ), row=1, col=1)
                    
                    if 'SMA_50' in data_tech.columns:
                        fig.add_trace(go.Scatter(
                            x=data_tech.index, y=data_tech['SMA_50'],
                            line=dict(color='red', width=2),
                            name='SMA 50'
                        ), row=1, col=1)
                    
                    if 'SMA_200' in data_tech.columns:
                        fig.add_trace(go.Scatter(
                            x=data_tech.index, y=data_tech['SMA_200'],
                            line=dict(color='purple', width=2),
                            name='SMA 200'
                        ), row=1, col=1)
                
                # RSI (fila 2)
                if "RSI" in indicadores and 'RSI' in data_tech.columns:
                    fig.add_trace(go.Scatter(
                        x=data_tech.index, y=data_tech['RSI'],
                        line=dict(color='blue', width=2),
                        name='RSI'
                    ), row=2, col=1)
                    
                    # Líneas de sobrecompra/sobreventa
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                    fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
                
                # MACD (fila 2, segundo eje Y)
                if "MACD" in indicadores and all(col in data_tech.columns for col in ['MACD', 'MACD_Signal']):
                    fig.add_trace(go.Scatter(
                        x=data_tech.index, y=data_tech['MACD'],
                        line=dict(color='red', width=2),
                        name='MACD',
                        yaxis='y2'
                    ), row=2, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=data_tech.index, y=data_tech['MACD_Signal'],
                        line=dict(color='blue', width=2),
                        name='Señal MACD',
                        yaxis='y2'
                    ), row=2, col=1)
                    
                    # Configurar segundo eje Y para MACD
                    fig.update_layout(
                        yaxis2=dict(
                            title='MACD',
                            overlaying='y',
                            side='right'
                        )
                    )
                
                fig.update_layout(
                    height=800, 
                    showlegend=True, 
                    xaxis_rangeslider_visible=False,
                    title=f"Análisis Técnico de {stonk}"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # REDUCIR ESPACIO ENTRE GRÁFICA Y SEÑALES
                st.markdown("<br>", unsafe_allow_html=True)  # Solo un pequeño espacio

                # SEÑALES TÉCNICAS
                st.subheader("📊 Señales Técnicas Actuales")
                
                if not data_tech.empty:
                    # Obtener el último dato
                    ultimo = data_tech.iloc[-1]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if 'RSI' in data_tech.columns:
                            rsi_actual = ultimo['RSI']
                            st.metric("RSI", f"{rsi_actual:.2f}")
                            if rsi_actual > 70:
                                st.error("SOBRECOMPRA 🔴")
                            elif rsi_actual < 30:
                                st.success("SOBREVENTA 🟢")
                            else:
                                st.info("NEUTRAL 🟡")
                    
                    with col2:
                        if all(col in data_tech.columns for col in ['MACD', 'MACD_Signal']):
                            macd_actual = ultimo['MACD']
                            signal_actual = ultimo['MACD_Signal']
                            st.metric("MACD", f"{macd_actual:.4f}")
                            if macd_actual > signal_actual:
                                st.success("ALCISTA 🟢")
                            else:
                                st.error("BAJISTA 🔴")
                    
                    with col3:
                        if 'Close' in data_tech.columns and 'SMA_50' in data_tech.columns:
                            precio_actual = ultimo['Close']
                            sma_50 = ultimo['SMA_50']
                            st.metric("Precio vs SMA50", f"${precio_actual:.2f}")
                            if precio_actual > sma_50:
                                st.success("POR ENCIMA 🟢")
                            else:
                                st.error("POR DEBAJO 🔴")
                    
                    with col4:
                        if all(col in data_tech.columns for col in ['BB_Upper', 'BB_Lower', 'Close']):
                            precio_actual = ultimo['Close']
                            bb_upper = ultimo['BB_Upper']
                            bb_lower = ultimo['BB_Lower']
                            st.metric("Bandas Bollinger", f"${precio_actual:.2f}")
                            if precio_actual > bb_upper:
                                st.error("SOBRE SUPERIOR 🔴")
                            elif precio_actual < bb_lower:
                                st.success("BAJO INFERIOR 🟢")
                            else:
                                st.info("DENTRO BANDAS 🟡")
                 # PEQUEÑO ESPACIO ANTES DEL RESUMEN
                st.markdown("<br>", unsafe_allow_html=True)

                # RESUMEN DE INDICADORES
                st.subheader("📈 Resumen de Indicadores")
                
                # Crear DataFrame resumen
                resumen_data = []
                if 'RSI' in data_tech.columns:
                    rsi_actual = data_tech['RSI'].iloc[-1]
                    rsi_señal = "SOBRECOMPRA" if rsi_actual > 70 else "SOBREVENTA" if rsi_actual < 30 else "NEUTRAL"
                    resumen_data.append({'Indicador': 'RSI', 'Valor': f"{rsi_actual:.2f}", 'Señal': rsi_señal})
                
                if all(col in data_tech.columns for col in ['MACD', 'MACD_Signal']):
                    macd_actual = data_tech['MACD'].iloc[-1]
                    signal_actual = data_tech['MACD_Signal'].iloc[-1]
                    macd_señal = "ALCISTA" if macd_actual > signal_actual else "BAJISTA"
                    resumen_data.append({'Indicador': 'MACD', 'Valor': f"{macd_actual:.4f}", 'Señal': macd_señal})
                
                if all(col in data_tech.columns for col in ['Close', 'SMA_20', 'SMA_50', 'SMA_200']):
                    precio_actual = data_tech['Close'].iloc[-1]
                    sma_20 = data_tech['SMA_20'].iloc[-1]
                    sma_50 = data_tech['SMA_50'].iloc[-1]
                    sma_200 = data_tech['SMA_200'].iloc[-1]
                    
                    # Señal de tendencia basada en medias
                    if precio_actual > sma_20 > sma_50 > sma_200:
                        tendencia = "FUERTE ALCISTA 🟢"
                    elif precio_actual < sma_20 < sma_50 < sma_200:
                        tendencia = "FUERTE BAJISTA 🔴"
                    else:
                        tendencia = "LATERAL 🟡"
                    
                    resumen_data.append({'Indicador': 'Tendencia Medias', 'Valor': f"${precio_actual:.2f}", 'Señal': tendencia})
                
                if resumen_data:
                    df_resumen = pd.DataFrame(resumen_data)
                    st.dataframe(df_resumen, use_container_width=True)
                
                # PEQUEÑO ESPACIO ANTES DE LA SECCIÓN EDUCATIVA
                st.markdown("<br>", unsafe_allow_html=True)

                # SECCIÓN EDUCATIVA SOBRE INDICADORES
                st.subheader("📚 ¿Qué son los Indicadores Técnicos?")
                
                st.markdown("""
                Los **indicadores técnicos** son herramientas matemáticas que se aplican a los precios y volúmenes 
                históricos de un activo para analizar tendencias, identificar posibles puntos de entrada y salida, 
                y predecir movimientos futuros del precio. Se dividen principalmente en:
                
                - **Indicadores de tendencia**: Ayudan a identificar la dirección del mercado
                - **Indicadores de momentum**: Miden la velocidad de los movimientos de precios
                - **Indicadores de volatilidad**: Miden la magnitud de las fluctuaciones del precio
                - **Indicadores de volumen**: Analizan la fuerza detrás de los movimientos de precios
                """)
                
                # EXPANDERS PARA CADA INDICADOR
                st.subheader("🔍 Explicación de Cada Indicador")
                
                with st.expander("📊 RSI (Relative Strength Index)", expanded=False):
                    st.markdown("""
                    **¿Qué es?**
                    - El RSI es un oscilador de momentum que mide la velocidad y el cambio de los movimientos de precios
                    - Oscila entre 0 y 100
                    
                    **¿Para qué sirve?**
                    - Identificar condiciones de **sobrecompra** (RSI > 70) y **sobreventa** (RSI < 30)
                    - Detectar divergencias que pueden indicar cambios de tendencia
                    - Confirmar la fuerza de una tendencia
                    
                    **Interpretación:**
                    - **RSI > 70**: Posible sobrecompra - considerar venta
                    - **RSI < 30**: Posible sobreventa - considerar compra
                    - **RSI = 50**: Punto de equilibrio
                    """)
                
                with st.expander("📈 MACD (Moving Average Convergence Divergence)", expanded=False):
                    st.markdown("""
                    **¿Qué es?**
                    - Indicador de tendencia que muestra la relación entre dos medias móviles exponenciales
                    - Se compone de:
                      - **Línea MACD**: Diferencia entre EMA 12 y EMA 26
                      - **Línea de Señal**: EMA 9 del MACD
                      - **Histograma**: Diferencia entre MACD y su línea de señal
                    
                    **¿Para qué sirve?**
                    - Identificar cambios en la dirección y fuerza de la tendencia
                    - Generar señales de compra y venta
                    - Detectar momentum alcista o bajista
                    
                    **Señales principales:**
                    - **Cruce alcista**: MACD cruza por encima de la línea de señal → COMPRA
                    - **Cruce bajista**: MACD cruza por debajo de la línea de señal → VENTA
                    - **Divergencias**: Cuando el precio y el MACD no coinciden
                    """)
                
                with st.expander("📉 Bandas de Bollinger", expanded=False):
                    st.markdown("""
                    **¿Qué es?**
                    - Indicador de volatilidad que consiste en tres líneas:
                      - **Banda media**: SMA 20 (Media Móvil Simple de 20 periodos)
                      - **Banda superior**: SMA 20 + (2 × Desviación Estándar)
                      - **Banda inferior**: SMA 20 - (2 × Desviación Estándar)
                    
                    **¿Para qué sirve?**
                    - Medir la volatilidad del mercado
                    - Identificar niveles de soporte y resistencia dinámicos
                    - Detectar condiciones de mercado extremas
                    
                    **Interpretación:**
                    - **Bandas estrechas**: Baja volatilidad (posible breakout próximo)
                    - **Bandas anchas**: Alta volatilidad
                    - **Precio toca banda superior**: Posible resistencia
                    - **Precio toca banda inferior**: Posible soporte
                    - **Walk the band**: El precio se mantiene en una banda indicando tendencia fuerte
                    """)
                
                with st.expander("📊 Medias Móviles", expanded=False):
                    st.markdown("""
                    **¿Qué es?**
                    - Indicadores que suavizan los datos de precio para identificar la dirección de la tendencia
                    - Tipos principales:
                      - **SMA (Simple Moving Average)**: Media aritmética simple
                      - **EMA (Exponential Moving Average)**: Da más peso a los precios recientes
                    
                    **¿Para qué sirve?**
                    - Identificar la dirección de la tendencia
                    - Generar señales de compra y venta mediante cruces
                    - Actuar como niveles de soporte y resistencia dinámicos
                    
                    **Configuraciones comunes:**
                    - **SMA 20**: Tendencia a corto plazo
                    - **SMA 50**: Tendencia a medio plazo
                    - **SMA 200**: Tendencia a largo plazo (tendencia principal)
                    
                    **Señales importantes:**
                    - **Cruce dorado**: SMA 50 cruza por encima de SMA 200 → FUERTE ALCISTA
                    - **Cruce de la muerte**: SMA 50 cruza por debajo de SMA 200 → FUERTE BAJISTA
                    - **Precio sobre medias**: Tendencia alcista
                    - **Precio bajo medias**: Tendencia bajista
                    """)
                
                # CONSEJOS DE USO
                st.info("""
                **💡 Consejos Prácticos:**
                - Nunca uses un solo indicador para tomar decisiones
                - Combina múltiples indicadores para confirmar señales
                - Considera el contexto del mercado y las noticias relevantes
                - Los indicadores son herramientas, no garantías de éxito
                """)
                
                # DESCARGAR DATOS TÉCNICOS
                st.subheader("💾 Exportar Datos Técnicos")
                
                # Preparar datos para descarga
                columnas_descarga = ['Open', 'High', 'Low', 'Close', 'Volume']
                if 'RSI' in data_tech.columns:
                    columnas_descarga.append('RSI')
                if 'MACD' in data_tech.columns:
                    columnas_descarga.extend(['MACD', 'MACD_Signal', 'MACD_Histogram'])
                if 'BB_Middle' in data_tech.columns:
                    columnas_descarga.extend(['BB_Upper', 'BB_Middle', 'BB_Lower'])
                if 'SMA_20' in data_tech.columns:
                    columnas_descarga.extend(['SMA_20', 'SMA_50', 'SMA_200'])
                
                datos_descarga = data_tech[columnas_descarga].copy()
                datos_descarga = datos_descarga.reset_index()
                
                csv = datos_descarga.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar datos técnicos como CSV",
                    data=csv,
                    file_name=f"{stonk}_datos_tecnicos.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
    except Exception as e:
        st.error(f"Error en análisis técnico: {str(e)}")
        st.write("Detalles del error:", str(e))

# SECCIÓN DE ANÁLISIS IA (COMPLETA)
elif st.session_state.seccion_actual == "ia":
    st.header(f"🤖 Análisis IA - {nombre}")
    
    # Obtener datos para el análisis
    try:
        current_price = info.get('currentPrice', 0)
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 0)
        revenue_growth = info.get('revenueGrowth', 0)
        
        # Prompt para análisis IA
        prompt_analisis = f"""
        Analiza la acción {stonk} ({nombre}) como un experto financiero. Considera:
        
        Precio actual: ${current_price}
        Market Cap: ${market_cap/1e9:.2f}B
        P/E Ratio: {pe_ratio}
        Crecimiento de ingresos: {revenue_growth*100 if revenue_growth else 0:.1f}%
        
        Proporciona un análisis conciso que incluya:
        1. Valoración actual (sobrevalorada/subvalorada)
        2. Fortalezas clave
        3. Riesgos principales  
        4. Recomendación (Comprar/Mantener/Vender)
        5. Perspectiva a 12 meses
        
        Máximo 400 palabras, en español.
        """
        
        with st.spinner("🤖 Analizando con IA..."):
            try:
                response_ia = genai.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_analisis
                )
                
                st.success("✅ Análisis completado")
                st.write(response_ia.text)
                
            except Exception as e:
                st.warning("⚠️ El modelo de IA está temporalmente saturado")
        
        # Análisis de sentimiento de noticias
        st.subheader("😊 Análisis de Sentimiento")
        
        def analizar_sentimiento_noticias(ticker):
            # Simulación de análisis de sentimiento
            sentimientos = ["POSITIVO", "NEUTRAL", "NEGATIVO"]
            return random.choice(sentimientos)
        
        sentimiento = analizar_sentimiento_noticias(stonk)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if sentimiento == "POSITIVO":
                st.success("😊 Sentimiento: POSITIVO")
            elif sentimiento == "NEGATIVO":
                st.error("😞 Sentimiento: NEGATIVO")
            else:
                st.info("😐 Sentimiento: NEUTRAL")
        
        with col2:
            # Scoring fundamental
            scoring, metricas_scoring = calcular_scoring_fundamental(info)
            st.metric("Scoring Fundamental", f"{scoring}/100")
        
        with col3:
            # Recomendación IA
            if scoring >= 70:
                st.success("🎯 Recomendación: COMPRAR")
            elif scoring >= 50:
                st.warning("🎯 Recomendación: MANTENER")
            else:
                st.error("🎯 Recomendación: VENDER")
        
        # Métricas de scoring
        st.subheader("📊 Métricas de Scoring")
        for metrica, valor in metricas_scoring.items():
            st.write(f"{metrica}: {valor}")
            
    except Exception as e:
        st.error(f"Error en análisis IA: {str(e)}")

# SECCIÓN DE SCREENER Y FILTROS (COMPLETAMENTE DINÁMICO CON YFINANCE)

elif st.session_state.seccion_actual == "screener":
    st.header("🔍 Screener S&P 500 - Filtros Avanzados")
    st.write("Busca acciones del S&P 500 que cumplan con tus criterios de inversión")
    
    # LISTA COMPLETA DEL S&P 500 (actualizada 2024)
    SP500_SYMBOLS = [
        # Technology (120+ stocks)
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'AVGO', 'TSLA', 'ADBE',
        'CRM', 'CSCO', 'ACN', 'ORCL', 'IBM', 'INTC', 'AMD', 'QCOM', 'TXN', 'NOW',
        'SNOW', 'NET', 'PANW', 'CRWD', 'ZS', 'FTNT', 'OKTA', 'TEAM', 'PLTR', 'DDOG',
        'MDB', 'SPLK', 'HUBS', 'ESTC', 'PD', 'TWLO', 'DOCU', 'RBLX', 'UBER', 'LYFT',
        'SHOP', 'SQ', 'PYPL', 'COIN', 'HOOD', 'ROKU', 'NFLX', 'DIS', 'CMCSA', 'CHTR',
        'T', 'VZ', 'TMUS', 'EA', 'ATVI', 'TTWO', 'ZNGA', 'RIVN', 'LCID', 'FSLR',
        'ENPH', 'SEDG', 'RUN', 'PLUG', 'BE', 'NIO', 'LI', 'XPEV', 'F', 'GM',
        'TSM', 'ASML', 'LRCX', 'AMAT', 'KLAC', 'NXPI', 'MRVL', 'SWKS', 'QRVO', 'MCHP',
        'CDNS', 'ANSS', 'ADSK', 'TTD', 'TTWO', 'EA', 'ATVI', 'ZG', 'Z', 'RDFN',
        'OPEN', 'COMP', 'U', 'CLSK', 'MSTR', 'RIOT', 'MARA', 'HUT', 'BITF', 'COIN',
        
        # Healthcare (60+ stocks)
        'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'TMO', 'LLY', 'DHR', 'ABT', 'BMY',
        'AMGN', 'GILD', 'VRTX', 'REGN', 'BIIB', 'ISRG', 'SYK', 'BDX', 'ZTS', 'EW',
        'HCA', 'IDXX', 'DXCM', 'ILMN', 'MTD', 'WAT', 'PKI', 'TECH', 'RGEN', 'ICLR',
        'STE', 'WST', 'BRKR', 'PODD', 'ALGN', 'COO', 'HSIC', 'XRAY', 'BAX', 'HOLX',
        'LH', 'DGX', 'A', 'ABC', 'CAH', 'MCK', 'CVS', 'WBA', 'CI', 'HUM',
        'ELV', 'CNC', 'MOH', 'OGN', 'BHC', 'JAZZ', 'INCY', 'EXAS', 'NTRA', 'TXG',
        
        # Financials (70+ stocks)
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'SCHW', 'BLK', 'AXP', 'V', 'MA',
        'PYPL', 'SQ', 'COF', 'DFS', 'TFC', 'PNC', 'USB', 'KEY', 'CFG', 'MTB',
        'RF', 'HBAN', 'FITB', 'ALLY', 'CMA', 'ZION', 'EWBC', 'C', 'BK', 'STT',
        'NTRS', 'TROW', 'AMP', 'BEN', 'IVZ', 'JEF', 'PGR', 'ALL', 'TRV', 'AIG',
        'HIG', 'PFG', 'L', 'AON', 'MMC', 'WTW', 'AJG', 'BRO', 'ERIE', 'CINF',
        'RE', 'RGA', 'MET', 'PRU', 'LNC', 'UNM', 'AFL', 'BHF', 'NMRK', 'RJF',
        'ICE', 'MCO', 'SPGI', 'MSCI', 'NDAQ', 'CBOE', 'FDS', 'FIS', 'FISV', 'GPN',
        
        # Consumer Discretionary (60+ stocks)
        'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'TGT', 'BKNG',
        'ORLY', 'AZO', 'MGM', 'WYNN', 'LVS', 'RCL', 'CCL', 'NCLH', 'MAR', 'HLT',
        'EXPE', 'ABNB', 'TRIP', 'BKNG', 'YUM', 'CMG', 'DPZ', 'WING', 'DRI', 'BLMN',
        'EBAY', 'ETSY', 'ROST', 'BURL', 'DLTR', 'FIVE', 'BIG', 'DKS', 'ASO', 'ANF',
        'GPS', 'URBN', 'LEVI', 'NKE', 'LULU', 'VFC', 'TPR', 'CPRI', 'RL', 'PVH',
        'F', 'GM', 'STLA', 'HMC', 'TM', 'RACE', 'TSLA', 'LCID', 'RIVN', 'NKLA',
        
        # Consumer Staples (30+ stocks)
        'PG', 'KO', 'PEP', 'WMT', 'COST', 'TGT', 'KR', 'SYY', 'ADM', 'BG',
        'MDLZ', 'K', 'GIS', 'HSY', 'SJM', 'CAG', 'CPB', 'KMB', 'CL', 'EL',
        'NWL', 'CLX', 'CHD', 'EPD', 'MO', 'PM', 'BTI', 'IMB', 'STZ', 'BUD',
        'TAP', 'SAM', 'MNST', 'KDP', 'FIZZ', 'COKE', 'PEP', 'KO', 'WMT', 'COST',
        
        # Industrials (70+ stocks)
        'UPS', 'FDX', 'RTX', 'BA', 'LMT', 'NOC', 'GD', 'HII', 'LHX', 'CW',
        'TDG', 'HEI', 'COL', 'TXT', 'DE', 'CAT', 'CNHI', 'AGCO', 'CMI', 'PCAR',
        'ALLE', 'ALGN', 'CSX', 'UNP', 'NSC', 'CP', 'KSU', 'JBHT', 'LSTR', 'ODFL',
        'EXPD', 'CHRW', 'XPO', 'GWW', 'FAST', 'MSM', 'SNA', 'ITW', 'EMR', 'ROK',
        'DOV', 'PNR', 'IEX', 'FLS', 'FLR', 'J', 'PWR', 'QUAD', 'VMC', 'MLM',
        'SUM', 'EXP', 'ASH', 'ECL', 'IFF', 'PPG', 'SHW', 'ALB', 'LTHM', 'SLB',
        'HAL', 'BKR', 'NOV', 'FTI', 'OII', 'RIG', 'DO', 'LBRT', 'WHD', 'NBR',
        
        # Energy (30+ stocks)
        'XOM', 'CVX', 'COP', 'EOG', 'MPC', 'PSX', 'VLO', 'DVN', 'PXD', 'OXY',
        'HES', 'MRO', 'FANG', 'APA', 'NOV', 'SLB', 'HAL', 'BKR', 'WMB', 'KMI',
        'ET', 'EPD', 'OKE', 'TRGP', 'LNG', 'CHK', 'RRC', 'SWN', 'AR', 'MGY',
        
        # Materials (20+ stocks)
        'LIN', 'APD', 'SHW', 'ECL', 'PPG', 'ALB', 'NEM', 'GOLD', 'FCX', 'SCCO',
        'AA', 'CLF', 'STLD', 'NUE', 'X', 'MOS', 'CF', 'NTR', 'FMC', 'AVY',
        'IP', 'PKG', 'WRK', 'SEE', 'BALL', 'ATI', 'CMC', 'RS', 'CRS', 'WOR',
        
        # Real Estate (30+ stocks)
        'AMT', 'CCI', 'PLD', 'EQIX', 'PSA', 'SPG', 'O', 'AVB', 'EQR', 'ESS',
        'UDR', 'MAA', 'CPT', 'ARE', 'BXP', 'SLG', 'VNO', 'KIM', 'FRT', 'REG',
        'DLR', 'IRM', 'EXR', 'PSA', 'WPC', 'NSA', 'LAMR', 'CUBE', 'REXR', 'PLD',
        
        # Utilities (30+ stocks)
        'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'WEC', 'ES',
        'PEG', 'ETR', 'FE', 'AES', 'AWK', 'CNP', 'DTE', 'LNT', 'PPL', 'EIX',
        'ED', 'CMS', 'NRG', 'VST', 'ALE', 'OTTR', 'SWX', 'NI', 'OGE', 'POR'
    ]

    # FUNCIÓN PARA CALCULAR MÉTRICAS DE RIESGO CON YFINANCE
    def calcular_metricas_riesgo_yfinance(simbolo, periodo_dias=365):
        """
        Calcula métricas de riesgo sofisticadas usando yfinance con datos históricos reales
        """
        try:
            # Descargar datos históricos
            end_date = datetime.today()
            start_date = end_date - timedelta(days=periodo_dias)
            
            # Descargar datos de la acción
            datos_accion = yf.download(
                simbolo, 
                start=start_date.strftime('%Y-%m-%d'), 
                end=end_date.strftime('%Y-%m-%d'),
                progress=False,
                auto_adjust=False
            )
            
            if datos_accion.empty:
                return None
            
            # Verificar que tenemos la columna Close
            if 'Close' not in datos_accion.columns:
                if 'Adj Close' in datos_accion.columns:
                    precios = datos_accion['Adj Close']
                else:
                    return None
            else:
                precios = datos_accion['Close']
            
            if len(precios) < 30:
                return None
            
            precios = precios.dropna()
            if len(precios) < 30:
                return None
            
            retornos = precios.pct_change().dropna()
            if len(retornos) < 20:
                return None
            
            precio_actual = precios.iloc[-1]
            
            # 1. Value at Risk (VaR)
            var_95 = retornos.quantile(0.05)
            var_95_porcentaje = abs(var_95 * 100)
            var_95_dinero = abs(precio_actual * var_95)
            
            # 2. Sharpe Ratio
            tasa_libre_riesgo_anual = 0.02
            retorno_medio_anual = retornos.mean() * 252
            volatilidad_anual = retornos.std() * np.sqrt(252)
            
            if volatilidad_anual > 0:
                sharpe_ratio = (retorno_medio_anual - tasa_libre_riesgo_anual) / volatilidad_anual
            else:
                sharpe_ratio = 0
            
            # 3. Sortino Ratio
            retornos_negativos = retornos[retornos < 0]
            if len(retornos_negativos) > 1:
                volatilidad_negativa = retornos_negativos.std() * np.sqrt(252)
                if volatilidad_negativa > 0:
                    sortino_ratio = (retorno_medio_anual - tasa_libre_riesgo_anual) / volatilidad_negativa
                else:
                    sortino_ratio = sharpe_ratio
            else:
                sortino_ratio = sharpe_ratio
            
            # 4. Drawdown Analysis
            rolling_max = precios.expanding().max()
            drawdown = (precios - rolling_max) / rolling_max
            max_drawdown = abs(drawdown.min() * 100)
            
            # 5. Beta y Correlación con S&P 500
            beta = 1.0
            correlacion = 0.5
            
            try:
                sp500_data = yf.download('^GSPC', 
                                       start=start_date.strftime('%Y-%m-%d'), 
                                       end=end_date.strftime('%Y-%m-%d'),
                                       progress=False,
                                       auto_adjust=False)
                
                if not sp500_data.empty and 'Close' in sp500_data.columns:
                    sp500_precios = sp500_data['Close'].dropna()
                    
                    fechas_comunes = precios.index.intersection(sp500_precios.index)
                    if len(fechas_comunes) > 30:
                        precios_aligned = precios.reindex(fechas_comunes)
                        sp500_aligned = sp500_precios.reindex(fechas_comunes)
                        
                        retornos_accion = precios_aligned.pct_change().dropna()
                        retornos_sp500 = sp500_aligned.pct_change().dropna()
                        
                        fechas_retornos = retornos_accion.index.intersection(retornos_sp500.index)
                        if len(fechas_retornos) > 20:
                            retornos_accion_aligned = retornos_accion.reindex(fechas_retornos)
                            retornos_sp500_aligned = retornos_sp500.reindex(fechas_retornos)
                            
                            correlacion = retornos_accion_aligned.corr(retornos_sp500_aligned)
                            
                            covarianza = retornos_accion_aligned.cov(retornos_sp500_aligned)
                            varianza_mercado = retornos_sp500_aligned.var()
                            if varianza_mercado > 0:
                                beta = covarianza / varianza_mercado
            except:
                pass
            
            # 6. Calcular RSI
            rsi_actual = 50
            try:
                delta = precios.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_actual = rsi.iloc[-1] if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50
            except:
                pass
            
            return {
                'var_95': var_95_porcentaje,
                'var_95_dinero': var_95_dinero,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'max_drawdown': max_drawdown,
                'correlacion_sp500': correlacion,
                'beta': beta,
                'volatilidad_anual': volatilidad_anual * 100,
                'retorno_anual': retorno_medio_anual * 100,
                'rsi': rsi_actual,
                'precio_actual': precio_actual,
            }
            
        except Exception as e:
            return None

    def obtener_datos_completos_yfinance(simbolo):
        """Obtiene datos fundamentales y técnicos de yFinance para cualquier símbolo"""
        try:
            ticker = yf.Ticker(simbolo)
            info = ticker.info
            
            # Verificar que el símbolo es válido
            if not info or 'currentPrice' not in info or info.get('currentPrice') is None:
                return None
            
            # Obtener datos históricos para calcular RSI
            datos_historicos = yf.download(simbolo, period="6mo", interval="1d", progress=False)
            
            # Calcular RSI si hay datos históricos
            rsi = 50
            if not datos_historicos.empty and 'Close' in datos_historicos.columns:
                try:
                    delta = datos_historicos['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi_calculado = 100 - (100 / (1 + rs))
                    rsi = rsi_calculado.iloc[-1] if not rsi_calculado.empty and not pd.isna(rsi_calculado.iloc[-1]) else 50
                except:
                    rsi = 50
            
            # Datos completos
            datos = {
                'Símbolo': simbolo,
                'Nombre': info.get('longName', simbolo),
                'Sector': info.get('sector', 'N/A'),
                'Industria': info.get('industry', 'N/A'),
                'Market Cap': info.get('marketCap', 0),
                'P/E': info.get('trailingPE', 0),
                'Precio Actual': info.get('currentPrice', 0),
                'Cambio %': info.get('regularMarketChangePercent', 0),
                'Volumen': info.get('volume', 0),
                'ROE': info.get('returnOnEquity', 0),
                'Margen Beneficio': info.get('profitMargins', 0),
                'Deuda/Equity': info.get('debtToEquity', 0),
                'Crecimiento Ingresos': info.get('revenueGrowth', 0),
                'Beta': info.get('beta', 1),
                'RSI': rsi,
                'Empresa Valida': True
            }
            
            return datos
            
        except Exception as e:
            return None

    def calcular_scoring_dinamico(datos):
        """Calcula scoring basado en datos fundamentales"""
        if not datos:
            return 0
        
        score = 0
        max_score = 100
        
        try:
            # P/E Ratio (20 puntos) - MÁS FLEXIBLE
            pe = datos.get('P/E', 0)
            if pe and pe > 0:
                if pe < 15:
                    score += 20
                elif pe < 25:
                    score += 15
                elif pe < 35:
                    score += 10
                else:
                    score += 5
            
            # ROE (20 puntos) - MÁS FLEXIBLE
            roe = datos.get('ROE', 0)
            if roe and roe > 0:
                if roe > 0.20:
                    score += 20
                elif roe > 0.15:
                    score += 16
                elif roe > 0.10:
                    score += 12
                elif roe > 0.05:
                    score += 8
                else:
                    score += 4
            
            # Margen Beneficio (15 puntos) - MÁS FLEXIBLE
            margen = datos.get('Margen Beneficio', 0)
            if margen and margen > 0:
                if margen > 0.20:
                    score += 15
                elif margen > 0.15:
                    score += 12
                elif margen > 0.10:
                    score += 9
                elif margen > 0.05:
                    score += 6
                else:
                    score += 3
            
            # Deuda/Equity (15 puntos) - MÁS FLEXIBLE
            deuda_eq = datos.get('Deuda/Equity', 0)
            if deuda_eq and deuda_eq >= 0:
                if deuda_eq < 0.5:
                    score += 15
                elif deuda_eq < 1.0:
                    score += 12
                elif deuda_eq < 1.5:
                    score += 9
                elif deuda_eq < 2.0:
                    score += 6
                else:
                    score += 3
            
            # Crecimiento Ingresos (20 puntos) - MÁS FLEXIBLE
            crecimiento = datos.get('Crecimiento Ingresos', 0)
            if crecimiento:
                if crecimiento > 0.20:
                    score += 20
                elif crecimiento > 0.15:
                    score += 16
                elif crecimiento > 0.10:
                    score += 12
                elif crecimiento > 0.05:
                    score += 8
                elif crecimiento > 0:
                    score += 4
            
            # Beta (10 puntos) - MÁS FLEXIBLE
            beta = datos.get('Beta', 1)
            if beta and beta > 0:
                if beta < 0.8:
                    score += 10
                elif beta < 1.2:
                    score += 8
                elif beta < 1.5:
                    score += 6
                elif beta < 2.0:
                    score += 4
                else:
                    score += 2
            
            return min(score, max_score)
            
        except Exception as e:
            return 0

    def buscar_simbolos_sp500_por_criterios(filtros, max_acciones=100):
        """Busca símbolos del S&P 500 que cumplan los criterios"""
        st.info(f"🔍 Escaneando {len(SP500_SYMBOLS)} acciones del S&P 500...")
        
        acciones_encontradas = []
        total_procesadas = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Crear contenedor para logs en tiempo real
        log_container = st.empty()
        
        for i, simbolo in enumerate(SP500_SYMBOLS):
            if len(acciones_encontradas) >= max_acciones:
                break
                
            total_procesadas += 1
            progress_percent = (i + 1) / len(SP500_SYMBOLS)
            progress_bar.progress(progress_percent)
            
            # Actualizar status cada 10 acciones para no sobrecargar
            if i % 10 == 0:
                status_text.text(f"Procesadas: {i}/{len(SP500_SYMBOLS)} | Encontradas: {len(acciones_encontradas)}")
            
            try:
                datos = obtener_datos_completos_yfinance(simbolo)
                if datos and datos.get('Empresa Valida'):
                    # Aplicar filtros - MÁS FLEXIBLES
                    cumple_filtros = True
                    
                    # Filtro P/E - MÁS FLEXIBLE
                    pe = datos.get('P/E', 0)
                    if filtros['pe_min'] > 0 and (pe == 0 or pe < filtros['pe_min']):
                        cumple_filtros = False
                    if filtros['pe_max'] < 1000 and pe > filtros['pe_max']:
                        cumple_filtros = False
                    
                    # Filtro ROE - MÁS FLEXIBLE
                    roe = datos.get('ROE', 0)
                    if filtros['roe_min'] > 0 and roe < (filtros['roe_min'] / 100):
                        cumple_filtros = False
                    
                    # Filtro Margen Beneficio - MÁS FLEXIBLE
                    margen = datos.get('Margen Beneficio', 0)
                    if filtros['profit_margin_min'] > 0 and margen < (filtros['profit_margin_min'] / 100):
                        cumple_filtros = False
                    
                    # Filtro Deuda/Equity - MÁS FLEXIBLE
                    deuda_eq = datos.get('Deuda/Equity', 0)
                    if filtros['debt_equity_max'] < 10 and deuda_eq > filtros['debt_equity_max']:
                        cumple_filtros = False
                    
                    # Filtro Beta - MÁS FLEXIBLE
                    beta = datos.get('Beta', 1)
                    if filtros['beta_max'] < 5 and beta > filtros['beta_max']:
                        cumple_filtros = False
                    
                    # Filtro RSI - MÁS FLEXIBLE
                    rsi = datos.get('RSI', 50)
                    if rsi < filtros['rsi_min'] or rsi > filtros['rsi_max']:
                        cumple_filtros = False
                    
                    if cumple_filtros:
                        scoring = calcular_scoring_dinamico(datos)
                        datos['Score'] = scoring
                        acciones_encontradas.append(datos)
                        
            except Exception as e:
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resumen final
        log_container.success(f"""
        ✅ **Búsqueda completada:**
        - Acciones procesadas: {total_procesadas}
        - Acciones encontradas: {len(acciones_encontradas)}
        - Tasa de éxito: {(len(acciones_encontradas)/total_procesadas)*100:.1f}%
        """)
        
        return acciones_encontradas

    # INTERFAZ DE FILTROS MEJORADA - VALORES POR DEFECTO MÁS FLEXIBLES
    st.subheader("🎯 Configura tus Criterios de Búsqueda")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**💰 Valoración:**")
        pe_min = st.number_input("P/E Mínimo", value=0.0, min_value=0.0, max_value=100.0, step=1.0, 
                               help="0 = Sin filtro. Valores típicos: 5-15")
        pe_max = st.number_input("P/E Máximo", value=60.0, min_value=0.0, max_value=1000.0, step=1.0,
                               help="1000 = Sin filtro. Valores típicos: 20-50")
        
        st.write("**📈 Rentabilidad:**")
        roe_min = st.number_input("ROE Mínimo (%)", value=5.0, min_value=0.0, max_value=100.0, step=1.0,
                                help="0 = Sin filtro. Valores típicos: 8-15")
        profit_margin_min = st.number_input("Margen Beneficio Mínimo (%)", value=0.0, min_value=0.0, max_value=100.0, step=1.0,
                                          help="0 = Sin filtro. Valores típicos: 5-12")
    
    with col2:
        st.write("**🏦 Estructura de Capital:**")
        debt_equity_max = st.number_input("Deuda/Equity Máximo", value=3.0, min_value=0.0, max_value=10.0, step=0.1,
                                        help="10 = Sin filtro. Valores típicos: 0.5-2.0")
        
        st.write("**📊 Volatilidad:**")
        beta_max = st.number_input("Beta Máximo", value=2.5, min_value=0.1, max_value=5.0, step=0.1,
                                 help="5 = Sin filtro. Valores típicos: 0.8-1.5")
        
        st.write("**🚀 Crecimiento:**")
        revenue_growth_min = st.number_input("Crecimiento Ingresos Mínimo (%)", value=0.0, min_value=-50.0, max_value=200.0, step=1.0,
                                          help="-50 = Sin filtro. Valores típicos: 5-15")
    
    # Filtros RSI MÁS FLEXIBLES
    st.subheader("📊 Filtro de Momentum (RSI)")
    col_rsi1, col_rsi2 = st.columns(2)
    
    with col_rsi1:
        rsi_min = st.slider("RSI Mínimo", 0, 100, 25, key="rsi_min_screener",
                          help="RSI muy bajo puede indicar sobreventa")
    
    with col_rsi2:
        rsi_max = st.slider("RSI Máximo", 0, 100, 75, key="rsi_max_screener",
                          help="RSI muy alto puede indicar sobrecompra")
    
    st.info(f"💡 **Rango RSI seleccionado:** {rsi_min} - {rsi_max} (Recomendado: 25-75 para más resultados)")

    # BOTÓN DE BÚSQUEDA MEJORADO
    st.markdown("---")
    
    # Selector de límite de resultados
    max_resultados = st.slider("Límite máximo de resultados", 10, 200, 50, 10,
                             help="Número máximo de acciones a mostrar")
    
    if st.button("🚀 Ejecutar Búsqueda en S&P 500", use_container_width=True, type="primary"):
        # Definir filtros
        filtros = {
            'pe_min': pe_min,
            'pe_max': pe_max,
            'roe_min': roe_min,
            'profit_margin_min': profit_margin_min,
            'revenue_growth_min': revenue_growth_min,
            'debt_equity_max': debt_equity_max,
            'beta_max': beta_max,
            'rsi_min': rsi_min,
            'rsi_max': rsi_max
        }
        
        # Ejecutar búsqueda
        with st.spinner(f"Buscando en {len(SP500_SYMBOLS)} acciones del S&P 500..."):
            acciones_encontradas = buscar_simbolos_sp500_por_criterios(filtros, max_resultados)
        
        if acciones_encontradas:
            st.success(f"✅ Se encontraron {len(acciones_encontradas)} acciones que cumplen los criterios")
            
            # Ordenar por score
            acciones_encontradas.sort(key=lambda x: x['Score'], reverse=True)
            
            # Crear DataFrame para mostrar
            df_resultados = pd.DataFrame(acciones_encontradas)
            
            # Formatear columnas para mostrar
            columnas_mostrar = ['Símbolo', 'Nombre', 'Sector', 'P/E', 'Precio Actual', 
                              'ROE', 'Margen Beneficio', 'Deuda/Equity', 'Beta', 'RSI', 'Score']
            
            df_display = df_resultados[columnas_mostrar].copy()
            
            # Formatear valores
            df_display['P/E'] = df_display['P/E'].apply(lambda x: f"{x:.1f}" if x > 0 else "N/A")
            df_display['Precio Actual'] = df_display['Precio Actual'].apply(lambda x: f"${x:.2f}" if x > 0 else "N/A")
            df_display['ROE'] = df_display['ROE'].apply(lambda x: f"{x*100:.1f}%" if x > 0 else "N/A")
            df_display['Margen Beneficio'] = df_display['Margen Beneficio'].apply(lambda x: f"{x*100:.1f}%" if x > 0 else "N/A")
            df_display['Deuda/Equity'] = df_display['Deuda/Equity'].apply(lambda x: f"{x:.2f}" if x >= 0 else "N/A")
            df_display['Beta'] = df_display['Beta'].apply(lambda x: f"{x:.2f}" if x > 0 else "N/A")
            df_display['RSI'] = df_display['RSI'].apply(lambda x: f"{x:.1f}")
            df_display['Score'] = df_display['Score'].apply(lambda x: f"{x:.0f}")
            
            # Mostrar resultados
            st.subheader("📊 Resultados del Screener S&P 500")
            st.dataframe(df_display, use_container_width=True)
            
            # Análisis por sectores
            st.subheader("📈 Análisis por Sectores")
            sector_counts = df_resultados['Sector'].value_counts()
            fig_sectores = px.pie(
                values=sector_counts.values,
                names=sector_counts.index,
                title='Distribución de Acciones por Sector'
            )
            st.plotly_chart(fig_sectores, use_container_width=True)
            
            # Gráfica de scores
            st.subheader("🏆 Distribución de Scores")
            fig_scores = px.bar(
                df_resultados.head(20),  # Mostrar solo top 20 para mejor visualización
                x='Símbolo',
                y='Score',
                color='Score',
                title='Top 20 Acciones por Score',
                color_continuous_scale='viridis'
            )
            fig_scores.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_scores, use_container_width=True)
            
            # ANÁLISIS DE RIESGO PARA LAS MEJORES ACCIONES
            if len(acciones_encontradas) > 0:
                st.markdown("---")
                st.subheader("📊 Métricas de Riesgo Avanzadas (Top 5)")
                
                with st.spinner("Calculando métricas de riesgo..."):
                    metricas_riesgo = []
                    
                    for accion in acciones_encontradas[:5]:
                        simbolo = accion['Símbolo']
                        
                        metricas = calcular_metricas_riesgo_yfinance(simbolo)
                        
                        if metricas:
                            metricas_riesgo.append({
                                'Símbolo': simbolo,
                                **metricas
                            })
                    
                    if metricas_riesgo:
                        # Mostrar métricas detalladas
                        tabs = st.tabs([f"📈 {m['Símbolo']}" for m in metricas_riesgo])
                        
                        for i, (tab, metricas) in enumerate(zip(tabs, metricas_riesgo)):
                            with tab:
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Value at Risk (95%)", 
                                            f"${metricas['var_95_dinero']:.2f}", 
                                            f"{metricas['var_95']:.1f}%")
                                    st.metric("Sharpe Ratio", f"{metricas['sharpe_ratio']:.2f}")
                                    st.metric("Retorno Anual", f"{metricas['retorno_anual']:.1f}%")
                                
                                with col2:
                                    st.metric("Sortino Ratio", f"{metricas['sortino_ratio']:.2f}")
                                    st.metric("Drawdown Máximo", f"{metricas['max_drawdown']:.1f}%")
                                    st.metric("Volatilidad Anual", f"{metricas['volatilidad_anual']:.1f}%")
                                
                                with col3:
                                    st.metric("Beta vs S&P 500", f"{metricas['beta']:.2f}")
                                    st.metric("Correlación S&P 500", f"{metricas['correlacion_sp500']:.2f}")
                                    st.metric("Precio Actual", f"${metricas['precio_actual']:.2f}")
            
            # BOTÓN DE DESCARGA
            st.markdown("---")
            st.subheader("💾 Exportar Resultados")
            
            csv_resultados = df_resultados.to_csv(index=False)
            st.download_button(
                label="📥 Descargar resultados completos (CSV)",
                data=csv_resultados,
                file_name=f"screener_sp500_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        else:
            st.warning("""
            ❌ No se encontraron acciones que cumplan todos los criterios.
            
            **💡 Sugerencias para obtener más resultados:**
            • **Relaja los filtros** - especialmente P/E Máximo (prueba 60-80) y ROE Mínimo (5-8%)
            • **Amplía el rango RSI** - prueba 20-80 en lugar de 30-70
            • **Reduce Deuda/Equity Máximo** - prueba 3.0-4.0
            • **Aumenta Beta Máximo** - prueba 2.5-3.0
            • **Establece algunos filtros en 0** para desactivarlos completamente
            """)

    # CONSEJOS PARA FILTROS MÁS EFECTIVOS
    with st.expander("💡 Consejos para Configurar Filtros en S&P 500"):
        st.markdown("""
        **Configuraciones recomendadas para S&P 500:**
        
        | Filtro | Valor Conservador | Valor Balanceado | Valor Agresivo | Resultados |
        |--------|------------------|------------------|----------------|------------|
        | P/E Máximo | 25 | 40-50 | 60-80 | 🟢 Más resultados |
        | ROE Mínimo | 15% | 8-12% | 5-8% | 🟢 Más resultados |
        | RSI Mínimo | 30 | 25-30 | 20-25 | 🟢 Más resultados |
        | RSI Máximo | 70 | 70-75 | 75-80 | 🟢 Más resultados |
        | Deuda/Equity | 1.0 | 2.0-2.5 | 3.0-4.0 | 🟢 Más resultados |
        | Beta Máximo | 1.2 | 1.8-2.2 | 2.5-3.0 | 🟢 Más resultados |
        
        **Para empezar (Balanceado):**
        - P/E Mínimo: 0
        - P/E Máximo: 50
        - ROE Mínimo: 8%
        - RSI: 25-75
        - Deuda/Equity: 2.5
        - Beta: 2.0
        
        Esto debería darte **20-60 acciones** del S&P 500.
        
        **Sectores con mejores resultados:**
        - 🏦 **Financieras:** Suelen tener P/E bajos
        - 🛢️ **Energía:** Crecimiento variable pero oportunidades
        - 🏭 **Industriales:** Estables con buenos dividendos
        - 🛒 **Consumo:** Defensivas con crecimiento constante
        """)

    # ESTADÍSTICAS DEL S&P 500
    with st.expander("📊 Estadísticas del S&P 500"):
        st.markdown(f"""
        **Información del Universo de Búsqueda:**
        - 📈 **Total de acciones:** {len(SP500_SYMBOLS)} empresas
        - 🏢 **Sectores representados:** Tecnología, Salud, Finanzas, Consumo, Industrial, Energía, Materiales, Bienes Raíces, Servicios
        - 🌎 **Diversificación:** Empresas líderes de EE.UU. y globales
        - 💰 **Market Cap:** Desde ~$10B hasta +$2T
        
        **Características típicas del S&P 500:**
        - P/E promedio: 20-25
        - ROE promedio: 12-18%
        - Beta promedio: 1.0-1.2
        - Dividend yield: 1.5-2.5%
        
        **💡 Tip:** El S&P 500 es más estable que el mercado general, por lo que los filtros muy estrictos pueden dejar fuera buenas oportunidades.
        """)

# SECCIÓN DE MACROECONOMÍA - CON DATOS REALES DEL WORLD BANK (SIN MAPEO)
elif st.session_state.seccion_actual == "macro":
    st.header("🌍 Panorama Macroeconómico Global")
    
    st.markdown("""
    **Contexto macroeconómico actual** que puede afectar tus inversiones.
    Los indicadores económicos influyen en los mercados bursátiles y en las decisiones de los inversores.
    """)

    # FUNCIONES AUXILIARES
    def mostrar_indicadores_en_columnas(indicadores_dict):
        """Muestra indicadores organizados en columnas"""
        cols = st.columns(2)
        current_col = 0
        
        for indicador, valor in indicadores_dict.items():
            if "---" in valor or "**" in indicador:
                # Es un separador o título
                st.markdown(f"**{indicador}**")
                continue
                
            with cols[current_col]:
                color_borde, color_texto = determinar_colores_indicador(indicador, valor)
                    
                st.markdown(f"""
                <div style='padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid {color_borde}; background-color: #1e1e1e; border: 1px solid #444;'>
                    <strong style='color: #ffffff; font-size: 13px;'>{indicador}</strong><br>
                    <span style='color: {color_texto}; font-weight: bold; font-size: 14px;'>{valor}</span>
                </div>
                """, unsafe_allow_html=True)
            
            current_col = (current_col + 1) % 2

    def determinar_colores_indicador(indicador, valor):
        """Determina colores apropiados para cada tipo de indicador"""
        indicador_lower = indicador.lower()
        
        # Indicadores donde alto es malo
        if any(x in indicador_lower for x in ['inflación', 'desempleo', 'interés', 'déficit', 'deuda', 'pobreza', 'corrupción', 'riesgo', 'emisiones']):
            try:
                valor_limpio = ''.join(c for c in str(valor) if c.isdigit() or c == '.' or c == '-')
                if valor_limpio:
                    valor_num = float(valor_limpio)
                    if valor_num > 10:
                        return "#ff4444", "#ff6666"  # Rojo - Muy malo
                    elif valor_num > 5:
                        return "#ffaa00", "#ffbb33"  # Naranja - Malo
                    else:
                        return "#4CAF50", "#66bb6a"  # Verde - Bueno
            except:
                pass
            return "#2196F3", "#64b5f6"  # Azul - Neutral
        
        # Indicadores donde alto es bueno
        elif any(x in indicador_lower for x in ['crecimiento', 'confianza', 'producción', 'ventas', 'consumo', 'inversión', 'salarios', 'productividad', 'innovación', 'competitividad', 'facilidad', 'esperanza']):
            try:
                valor_limpio = ''.join(c for c in str(valor) if c.isdigit() or c == '.' or c == '-')
                if valor_limpio:
                    valor_num = float(valor_limpio)
                    if valor_num > 5:
                        return "#4CAF50", "#66bb6a"  # Verde - Muy bueno
                    elif valor_num > 0:
                        return "#ffaa00", "#ffbb33"  # Naranja - Regular
                    else:
                        return "#ff4444", "#ff6666"  # Rojo - Malo
            except:
                pass
            return "#2196F3", "#64b5f6"  # Azul - Neutral
        
        # Indicadores de igualdad (Gini)
        elif 'gini' in indicador_lower:
            try:
                valor_limpio = ''.join(c for c in str(valor) if c.isdigit() or c == '.' or c == '-')
                if valor_limpio:
                    valor_num = float(valor_limpio)
                    if valor_num > 0.4:
                        return "#ff4444", "#ff6666"  # Rojo - Alta desigualdad
                    elif valor_num > 0.3:
                        return "#ffaa00", "#ffbb33"  # Naranja - Media desigualdad
                    else:
                        return "#4CAF50", "#66bb6a"  # Verde - Baja desigualdad
            except:
                pass
        
        return "#2196F3", "#64b5f6"  # Azul por defecto

    # FUNCIONES PARA OBTENER DATOS DEL WORLD BANK (SIN MAPEO)
    def buscar_codigo_pais_world_bank(nombre_pais):
        """Busca el código de país directamente en la API del World Bank"""
        try:
            # Primero intentamos obtener la lista de países
            url = f"http://api.worldbank.org/v2/country?format=json&per_page=300"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    # Buscar el país por nombre (búsqueda flexible)
                    nombre_buscar = nombre_pais.lower().strip()
                    for pais in data[1]:
                        nombre_pais_wb = pais['name'].lower()
                        
                        # Búsqueda exacta o parcial
                        if (nombre_buscar == nombre_pais_wb or 
                            nombre_buscar in nombre_pais_wb or 
                            nombre_pais_wb in nombre_buscar):
                            return pais['id']
                    
                    # Si no se encuentra, intentar con pycountry para nombres alternativos
                    try:
                        pais_pycountry = pycountry.countries.search_fuzzy(nombre_pais)
                        if pais_pycountry:
                            nombre_oficial = pais_pycountry[0].name
                            # Buscar nuevamente con el nombre oficial
                            for pais in data[1]:
                                if nombre_oficial.lower() == pais['name'].lower():
                                    return pais['id']
                    except:
                        pass
            return None
        except Exception as e:
            return None

    def obtener_datos_world_bank(pais_codigo, indicadores):
        """Obtiene datos del World Bank usando la API"""
        try:
            datos = {}
            for indicador in indicadores:
                try:
                    # Usar la API principal del World Bank
                    url = f"http://api.worldbank.org/v2/country/{pais_codigo}/indicator/{indicador}?format=json"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if len(data) > 1 and data[1]:
                            # Ordenar por año y obtener el más reciente
                            datos_ordenados = sorted(data[1], key=lambda x: x['date'], reverse=True)
                            for dato in datos_ordenados:
                                if dato['value'] is not None:
                                    datos[indicador] = {
                                        'valor': dato['value'],
                                        'año': dato['date'],
                                        'nombre': dato['indicator']['value']
                                    }
                                    break
                except Exception as e:
                    continue
            
            return datos
        except Exception as e:
            return {}

    def obtener_datos_pais_world_bank(nombre_pais):
        """Obtiene datos económicos completos del World Bank para cualquier país"""
        try:
            # Buscar código del país
            with st.spinner(f"🔍 Buscando {nombre_pais} en World Bank Group..."):
                pais_codigo = buscar_codigo_pais_world_bank(nombre_pais)
            
            if not pais_codigo:
                return {
                    "nombre": nombre_pais.title(),
                    "poblacion": "País no encontrado",
                    "pib_per_capita": "N/A",
                    "pib_nominal": "N/A",
                    "indicadores": {
                        "Error": f"No se pudo encontrar '{nombre_pais}' en la base de datos del World Bank",
                        "Sugerencia": "Intenta con el nombre en inglés o verifica la ortografía"
                    }
                }
            
            # Lista de indicadores clave del World Bank
            indicadores_wb = {
                # Población y demografía
                'SP.POP.TOTL': 'Población total',
                'SP.POP.GROW': 'Crecimiento poblacional anual %',
                'SP.DYN.LE00.IN': 'Esperanza de vida al nacer',
                'SP.URB.TOTL.IN.ZS': 'Población urbana %',
                'SM.POP.NETM': 'Migración neta',
                
                # Economía y PIB
                'NY.GDP.MKTP.CD': 'PIB nominal (US$)',
                'NY.GDP.MKTP.KD.ZG': 'Crecimiento del PIB anual %',
                'NY.GDP.PCAP.CD': 'PIB per cápita (US$)',
                'NY.GDP.PCAP.PP.CD': 'PIB per cápita PPA (US$)',
                'NY.GDP.MKTP.KD': 'PIB real (US$ constantes)',
                
                # Inflación y precios
                'FP.CPI.TOTL.ZG': 'Inflación anual %',
                'FP.CPI.TOTL': 'Índice de precios al consumidor',
                
                # Empleo
                'SL.UEM.TOTL.ZS': 'Tasa de desempleo %',
                'SL.TLF.TOTL.IN': 'Fuerza laboral total',
                'SL.EMP.TOTL.SP.ZS': 'Empleo total',
                
                # Comercio exterior
                'NE.EXP.GNFS.CD': 'Exportaciones de bienes y servicios (US$)',
                'NE.IMP.GNFS.CD': 'Importaciones de bienes y servicios (US$)',
                'NE.RSB.GNFS.CD': 'Balanza comercial (US$)',
                'NE.EXP.GNFS.ZS': 'Exportaciones % PIB',
                'NE.IMP.GNFS.ZS': 'Importaciones % PIB',
                
                # Finanzas públicas
                'GC.DOD.TOTL.GD.ZS': 'Deuda pública % PIB',
                'GC.REV.XGRT.GD.ZS': 'Ingresos del gobierno % PIB',
                'GC.XPN.TOTL.GD.ZS': 'Gasto del gobierno % PIB',
                'GC.BAL.CASH.GD.ZS': 'Balance fiscal % PIB',
                
                # Salud
                'SH.XPD.CHEX.GD.ZS': 'Gasto en salud % PIB',
                'SH.DYN.MORT': 'Tasa de mortalidad menores de 5 años',
                'SH.DYN.AIDS.ZS': 'Prevalencia de VIH %',
                'SH.STA.OWGH.ZS': 'Obesidad adulta %',
                
                # Educación
                'SE.XPD.TOTL.GD.ZS': 'Gasto en educación % PIB',
                'SE.ADT.LITR.ZS': 'Tasa de alfabetización adultos %',
                'SE.PRM.ENRR': 'Tasa de matrícula primaria',
                'SE.SEC.ENRR': 'Tasa de matrícula secundaria',
                
                # Pobreza y desigualdad
                'SI.POV.DDAY': 'Pobreza $3.20/día % población',
                'SI.POV.GINI': 'Coeficiente Gini',
                'SI.POV.NAHC': 'Pobreza nacional %',
                
                # Infraestructura
                'EG.ELC.ACCS.ZS': 'Acceso a electricidad % población',
                'IT.NET.USER.ZS': 'Usuarios de internet % población',
                'IS.RRS.TOTL.KM': 'Red ferroviaria total (km)',
                
                # Medio ambiente
                'EN.ATM.CO2E.PC': 'Emisiones CO2 per cápita',
                'AG.LND.FRST.ZS': 'Área forestal % territorio',
                'ER.H2O.FWTL.ZS': 'Estrés hídrico %',
                
                # Negocios y competitividad
                'IC.BUS.EASE.XQ': 'Facilidad para hacer negocios',
                'IC.TAX.TOTL.CP.ZS': 'Carga tributaria total %',
                'IC.FRM.CORR.ZS': 'Empresas que experimentan soborno %'
            }
            
            # Obtener datos del World Bank
            with st.spinner(f"📊 Obteniendo datos de {nombre_pais.title()} desde World Bank Group..."):
                datos_wb = obtener_datos_world_bank(pais_codigo, list(indicadores_wb.keys()))
            
            # Obtener nombre oficial del país
            nombre_oficial = nombre_pais.title()
            for pais_info in datos_wb.values():
                if 'nombre' in pais_info:
                    # El nombre viene en el formato "Indicador - País", extraer el país
                    if ' - ' in pais_info['nombre']:
                        nombre_oficial = pais_info['nombre'].split(' - ')[-1]
                        break
            
            # Procesar y formatear los datos
            indicadores_formateados = {}
            
            # Información básica del país
            poblacion = datos_wb.get('SP.POP.TOTL', {}).get('valor', 'N/A')
            pib_nominal = datos_wb.get('NY.GDP.MKTP.CD', {}).get('valor', 'N/A')
            pib_per_capita = datos_wb.get('NY.GDP.PCAP.CD', {}).get('valor', 'N/A')
            pib_ppa = datos_wb.get('NY.GDP.PCAP.PP.CD', {}).get('valor', 'N/A')
            
            # Formatear valores grandes
            def formatear_numero_grande(valor):
                if isinstance(valor, (int, float)):
                    if valor > 1e12:
                        return f"{valor/1e12:.2f}T"
                    elif valor > 1e9:
                        return f"{valor/1e9:.2f}B"
                    elif valor > 1e6:
                        return f"{valor/1e6:.2f}M"
                    else:
                        return f"{valor:,.0f}"
                return str(valor)
            
            def formatear_moneda(valor):
                if isinstance(valor, (int, float)):
                    if valor > 1e12:
                        return f"${valor/1e12:.2f}T"
                    elif valor > 1e9:
                        return f"${valor/1e9:.2f}B"
                    elif valor > 1e6:
                        return f"${valor/1e6:.2f}M"
                    else:
                        return f"${valor:,.0f}"
                return str(valor)
            
            poblacion_str = formatear_numero_grande(poblacion)
            pib_nominal_str = formatear_moneda(pib_nominal)
            pib_per_capita_str = formatear_moneda(pib_per_capita)
            pib_ppa_str = formatear_moneda(pib_ppa)
            
            # Construir diccionario de indicadores
            for codigo, nombre in indicadores_wb.items():
                if codigo in datos_wb:
                    dato = datos_wb[codigo]
                    valor = dato['valor']
                    año = dato['año']
                    
                    # Formatear valores según el tipo de indicador
                    if isinstance(valor, (int, float)):
                        if 'US$' in nombre or codigo in ['NY.GDP.MKTP.CD', 'NY.GDP.PCAP.CD', 'NY.GDP.PCAP.PP.CD', 'NE.EXP.GNFS.CD', 'NE.IMP.GNFS.CD']:
                            valor_str = formatear_moneda(valor)
                        elif any(x in nombre for x in ['%', 'tasa', 'crecimiento', 'ratio']):
                            valor_str = f"{valor:.2f}%"
                        elif 'coeficiente' in nombre.lower() or 'índice' in nombre.lower():
                            valor_str = f"{valor:.3f}"
                        else:
                            valor_str = formatear_numero_grande(valor)
                    else:
                        valor_str = str(valor)
                    
                    indicadores_formateados[f"{nombre} ({año})"] = valor_str
            
            return {
                "nombre": nombre_oficial,
                "poblacion": poblacion_str,
                "pib_per_capita": pib_per_capita_str,
                "pib_nominal": pib_nominal_str,
                "pib_ppa": pib_ppa_str,
                "codigo": pais_codigo,
                "indicadores": indicadores_formateados
            }
            
        except Exception as e:
            return {
                "nombre": nombre_pais.title(),
                "poblacion": "Error en consulta",
                "pib_per_capita": "Error en consulta",
                "pib_nominal": "Error en consulta",
                "pib_ppa": "Error en consulta",
                "indicadores": {
                    "Error": f"No se pudieron obtener datos: {str(e)}",
                    "Recomendación": "Intenta nuevamente en unos momentos"
                }
            }

    # Inicializar session_state para el país seleccionado
    if 'pais_seleccionado_macro' not in st.session_state:
        st.session_state.pais_seleccionado_macro = None
    
    # BUSCADOR Y MAPA
    st.subheader("🔍 Buscar y Seleccionar País")
    
    # Buscador de países
    col_buscador, col_limpiar = st.columns([3, 1])
    with col_buscador:
        pais_buscador = st.text_input(
            "Escribe el nombre de cualquier país del mundo:",
            placeholder="Ej: United States, Germany, Japan, Brazil, Mexico, Argentina, Spain, France, China, India...",
            key="buscador_paises_macro"
        )
    with col_limpiar:
        if st.session_state.pais_seleccionado_macro:
            if st.button("🗑️ Limpiar selección", use_container_width=True):
                st.session_state.pais_seleccionado_macro = None
                st.rerun()
    
    # Mapa interactivo con Folium
    st.subheader("🗺️ Mapa Mundial Interactivo - Selecciona cualquier país")
    
    try:
        from streamlit_folium import st_folium
        import folium
        from geopy.geocoders import Nominatim
        
        # Crear mapa global centrado
        m = folium.Map(location=[20, 0], zoom_start=2)
        
        # Mostrar mapa en Streamlit y capturar clic
        mapa_datos = st_folium(m, width=700, height=400, returned_objects=["last_clicked"])
        
        # Detectar clic en el mapa
        if mapa_datos and mapa_datos.get("last_clicked") is not None:
            lat = mapa_datos["last_clicked"]["lat"]
            lon = mapa_datos["last_clicked"]["lng"]
            
            try:
                geolocator = Nominatim(user_agent="macro_app")
                location = geolocator.reverse((lat, lon), language="en", exactly_one=True)
                
                if location and 'address' in location.raw and 'country' in location.raw['address']:
                    pais_click = location.raw['address']['country']
                    st.session_state.pais_seleccionado_macro = pais_click
                    st.success(f"🌍 País seleccionado desde el mapa: **{pais_click}**")
                    
            except Exception as e:
                st.warning("⚠️ No se pudo identificar el país. Intenta hacer clic más cerca del centro del país.")
                
    except ImportError:
        st.error("""
        ❌ **Faltan dependencias para el mapa interactivo**
        
        Para usar el mapa interactivo, instala las dependencias necesarias:
        ```bash
        pip install streamlit-folium folium geopy
        ```
        
        Mientras tanto, usa el buscador de texto arriba.
        """)
    
    # Determinar qué país mostrar (del buscador O del mapa)
    pais_actual = None
    if pais_buscador and pais_buscador.strip():
        pais_actual = pais_buscador.strip()
        st.session_state.pais_seleccionado_macro = pais_actual
    elif st.session_state.pais_seleccionado_macro:
        pais_actual = st.session_state.pais_seleccionado_macro
    
    # Indicador del país seleccionado
    if pais_actual:
        st.success(f"**País seleccionado:** {pais_actual}")
    else:
        st.info("💡 **Escribe el nombre de un país en el buscador o haz clic en el mapa**")
    
    # MOSTRAR INFORMACIÓN DEL PAÍS SELECCIONADO
    st.markdown("---")
    
    if pais_actual:
        # Mostrar vista específica del país
        datos_pais = obtener_datos_pais_world_bank(pais_actual)
        
        st.header(f"📊 Información Económica Completa de {datos_pais['nombre']}")
        
        # Mostrar código del país si se encontró
        if datos_pais.get('codigo'):
            st.caption(f"**World Bank Group:** {datos_pais['codigo']}")
        
        # Métricas principales
        st.subheader("📈 Métricas Principales")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Población", datos_pais.get('poblacion', 'N/A'))
        with col2:
            st.metric("💰 PIB Per Cápita", datos_pais.get('pib_per_capita', 'N/A'))
        with col3:
            st.metric("🌍 PIB Nominal", datos_pais.get('pib_nominal', 'N/A'))
        with col4:
            st.metric("⚖️ PIB PPA", datos_pais.get('pib_ppa', 'N/A'))
        
        # Indicadores económicos del país
        st.subheader("📊 Indicadores Económicos del World Bank Group")
        indicadores = datos_pais.get("indicadores", {})
        
        if indicadores and len(indicadores) > 2:  # Más de solo mensajes de error
            # Crear pestañas para diferentes categorías de indicadores
            tab_principales, tab_economia, tab_social, tab_ambiente = st.tabs([
                "🎯 Principales", 
                "💰 Economía", 
                "👥 Social",
                "🌱 Ambiente"
            ])
            
            with tab_principales:
                st.subheader("📈 Indicadores Principales")
                indicadores_principales = {
                    k: v for k, v in indicadores.items() 
                    if any(x in k.lower() for x in ['pib', 'crecimiento', 'inflación', 'desempleo', 'población'])
                }
                if indicadores_principales:
                    mostrar_indicadores_en_columnas(indicadores_principales)
                else:
                    st.info("No hay indicadores principales disponibles")
            
            with tab_economia:
                st.subheader("💰 Indicadores Económicos")
                indicadores_economia = {
                    k: v for k, v in indicadores.items() 
                    if any(x in k.lower() for x in ['exportaciones', 'importaciones', 'balanza', 'deuda', 'gasto', 'ingresos', 'comercio'])
                }
                if indicadores_economia:
                    mostrar_indicadores_en_columnas(indicadores_economia)
                else:
                    st.info("No hay indicadores económicos disponibles")
            
            with tab_social:
                st.subheader("👥 Indicadores Sociales")
                indicadores_social = {
                    k: v for k, v in indicadores.items() 
                    if any(x in k.lower() for x in ['esperanza', 'salud', 'educación', 'pobreza', 'gini', 'alfabetización', 'mortalidad'])
                }
                if indicadores_social:
                    mostrar_indicadores_en_columnas(indicadores_social)
                else:
                    st.info("No hay indicadores sociales disponibles")
            
            with tab_ambiente:
                st.subheader("🌱 Indicadores Ambientales")
                indicadores_ambiente = {
                    k: v for k, v in indicadores.items() 
                    if any(x in k.lower() for x in ['emisiones', 'forestal', 'electricidad', 'internet', 'agua', 'medio ambiente'])
                }
                if indicadores_ambiente:
                    mostrar_indicadores_en_columnas(indicadores_ambiente)
                else:
                    st.info("No hay indicadores ambientales disponibles")
            
            # Botones de control
            col_act1, col_act2, col_act3 = st.columns(3)
            with col_act1:
                if st.button("🔄 Actualizar Datos", use_container_width=True, type="primary"):
                    st.rerun()
            with col_act2:
                if st.button("📥 Exportar Datos", use_container_width=True):
                    st.info("Función de exportación en desarrollo")
            with col_act3:
                st.info("**Fuente:** World Bank Group")
                
        else:
            st.warning("""
            **No se pudieron obtener datos específicos para este país.**
            
            Posibles razones:
            - El país puede no estar en la base de datos del World Bank Group
            - Problemas temporales de conexión con la API
            - El país no tiene datos disponibles para los indicadores solicitados
            
            **Solución:** Intenta con otro país o verifica el nombre.
            """)
                
    else:
        # Vista cuando no hay país seleccionado
        st.info("🌍 **Selecciona un país usando el buscador o el mapa para ver sus datos económicos**")
        
        st.markdown("""
        ### 💡 Cómo usar esta sección:
        
        1. **🔍 Buscar país**: Escribe el nombre de cualquier país
        2. **🗺️ Mapa interactivo**: Haz clic en cualquier país del mapa mundial
        3. **📊 Datos oficiales**: Obtén información económica verificada del World Bank Group
        
        ### 📈 Información disponible:
        - **Métricas principales**: Población, PIB, PIB per cápita
        - **Indicadores económicos**: Crecimiento, inflación, desempleo
        - **Comercio exterior**: Exportaciones, importaciones, balanza comercial
        - **Finanzas públicas**: Deuda pública, gasto gubernamental
        - **Indicadores sociales**: Salud, educación, pobreza, desigualdad
        - **Medio ambiente**: Emisiones, áreas forestales
        
        ### 🌐 Fuente confiable:
        Todos los datos provienen del **World Bank Group**, 
        una fuente oficial y verificada utilizada por gobiernos e instituciones internacionales.
        """)
    
    # INFORMACIÓN SOBRE LA FUENTE
    st.markdown("---")
    st.success("""
    **🌐 Fuente de Datos: World Bank Group**
    
    - **📊 Datos oficiales** de gobiernos e instituciones internacionales
    - **🕐 Actualizaciones periódicas** según disponibilidad de cada indicador
    - **🌍 Cobertura global** de más de 200 países y territorios
    - **📈 Series históricas** desde 1960 para muchos indicadores
    - **🎯 Metodología consistente** entre países y años
    
    **Nota:** Algunos indicadores pueden tener datos con 1-2 años de retraso debido a los procesos de recolección y verificación.
    """)
























# SECCIÓN DE MERCADOS GLOBALES - CON MÚLTIPLES APIS
elif st.session_state.seccion_actual == "global":
    st.header("📈 Mercados Globales EEn Tiempo Real")
    
    # Configuración de APIs (usando variables de entorno)
    API_KEYS = {
        "alpha_vantage": "TU_ALPHA_VANTAGE_KEY",
        "financial_modeling_prep": "TU_FMP_KEY",
        "currency_api": currencyapi,  # ✅ INTEGRADA
    }

    # FUNCIONES PRINCIPALES CON MÚLTIPLES FUENTES
    @st.cache_data(ttl=300)
    def obtener_datos_indices():
        """Obtiene índices bursátiles de múltiples fuentes"""
        indices_data = {}
        
        # Fuente 1: Yahoo Finance (principal) - 7 ÍNDICES
        yf_indices = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC", 
            "Dow Jones": "^DJI",
            "FTSE 100": "^FTSE",
            "DAX": "^GDAXI",
            "CAC 40": "^FCHI",
            "Nikkei 225": "^N225"
        }
        
        for nombre, ticker in yf_indices.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = ((current - previous) / previous) * 100
                    
                    # Calcular YTD
                    ytd_data = stock.history(period="ytd")
                    if not ytd_data.empty:
                        ytd_start = ytd_data['Close'].iloc[0]
                        ytd_change = ((current - ytd_start) / ytd_start) * 100
                        ytd_str = f"{ytd_change:+.1f}%"
                    else:
                        ytd_str = "N/A"
                    
                    indices_data[nombre] = {
                        "precio": f"${current:,.0f}" if current > 1000 else f"${current:.2f}",
                        "cambio": f"{change:+.2f}%",
                        "ytd": ytd_str,
                        "valor": current,
                        "fuente": "Yahoo Finance"
                    }
            except Exception as e:
                continue
        
        return indices_data

    @st.cache_data(ttl=300)
    def obtener_datos_forex():
        """Obtiene datos de divisas de múltiples fuentes"""
        forex_data = {}
        
        # ✅ FUENTE PRINCIPAL: CurrencyAPI
        if API_KEYS["currency_api"] and API_KEYS["currency_api"] != "TU_CURRENCY_API_KEY":
            try:
                url = f"https://api.currencyapi.com/v3/latest?apikey={API_KEYS['currency_api']}&base_currency=USD"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        divisas_objetivo = {
                            "EUR": "EUR/USD",
                            "JPY": "USD/JPY", 
                            "GBP": "GBP/USD",
                            "CHF": "USD/CHF",
                            "CAD": "USD/CAD",
                            "AUD": "AUD/USD",
                            "CNY": "USD/CNY"
                        }
                        
                        for currency_code, par_nombre in divisas_objetivo.items():
                            if currency_code in data["data"]:
                                rate_data = data["data"][currency_code]
                                rate = rate_data["value"]
                                change = 0.0
                                
                                if currency_code == "EUR":
                                    precio_formateado = f"{1/rate:.4f}" if rate != 0 else "0.0000"
                                    forex_data[par_nombre] = {
                                        "precio": precio_formateado,
                                        "cambio": f"{change:+.2f}%",
                                        "valor": 1/rate if rate != 0 else 0,
                                        "fuente": "CurrencyAPI"
                                    }
                                else:
                                    precio_formateado = f"{rate:.4f}"
                                    forex_data[par_nombre] = {
                                        "precio": precio_formateado,
                                        "cambio": f"{change:+.2f}%",
                                        "valor": rate,
                                        "fuente": "CurrencyAPI"
                                    }
            except Exception as e:
                pass
        
        # ✅ FUENTE SECUNDARIA: Yahoo Finance (fallback - 7 pares)
        if not forex_data:
            yf_forex = {
                "EUR/USD": "EURUSD=X",
                "USD/JPY": "JPY=X",
                "GBP/USD": "GBPUSD=X",
                "USD/CHF": "CHF=X",
                "USD/CAD": "CAD=X",
                "AUD/USD": "AUDUSD=X",
                "USD/CNY": "CNY=X"
            }
            
            for par, ticker in yf_forex.items():
                try:
                    fx = yf.Ticker(ticker)
                    hist = fx.history(period="2d")
                    if not hist.empty and len(hist) >= 2:
                        current = hist['Close'].iloc[-1]
                        previous = hist['Close'].iloc[-2]
                        change = ((current - previous) / previous) * 100
                        
                        forex_data[par] = {
                            "precio": f"{current:.4f}",
                            "cambio": f"{change:+.2f}%",
                            "valor": current,
                            "fuente": "Yahoo Finance"
                        }
                except Exception as e:
                    continue
        
        # ✅ FUENTE TERCIARIA: ExchangeRate-API (fallback gratuito)
        if not forex_data:
            try:
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for currency, rate in data["rates"].items():
                        if currency in ["EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY"]:
                            if currency == "EUR":
                                formatted_rate = 1 / rate
                                par = "EUR/USD"
                            else:
                                formatted_rate = rate
                                par = f"USD/{currency}"
                            
                            forex_data[par] = {
                                "precio": f"{formatted_rate:.4f}",
                                "cambio": "0.00%",
                                "valor": formatted_rate,
                                "fuente": "ExchangeRate-API"
                            }
                            if len(forex_data) >= 7:
                                break
            except:
                pass
        
        return forex_data

    @st.cache_data(ttl=300)
    def obtener_datos_cripto():
        """Obtiene datos de criptomonedas de múltiples fuentes"""
        crypto_data = {}
        
        # Fuente 1: Yahoo Finance - 7 CRIPTOS
        yf_crypto = {
            "Bitcoin": "BTC-USD",
            "Ethereum": "ETH-USD",
            "BNB": "BNB-USD",
            "XRP": "XRP-USD",
            "Cardano": "ADA-USD",
            "Solana": "SOL-USD",
            "Dogecoin": "DOGE-USD"
        }
        
        for nombre, ticker in yf_crypto.items():
            try:
                crypto = yf.Ticker(ticker)
                hist = crypto.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = ((current - previous) / previous) * 100
                    
                    crypto_data[nombre] = {
                        "precio": f"${current:,.2f}",
                        "cambio": f"{change:+.2f}%",
                        "valor": current,
                        "fuente": "Yahoo Finance"
                    }
            except Exception as e:
                continue
        
        # Fuente 2: CoinGecko (respaldo) - 7 CRIPTOS
        if len(crypto_data) < 7:
            try:
                coins = ["bitcoin", "ethereum", "binancecoin", "ripple", "cardano", "solana", "dogecoin"]
                coin_names = ["Bitcoin", "Ethereum", "BNB", "XRP", "Cardano", "Solana", "Dogecoin"]
                
                coin_ids = ",".join(coins)
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd&include_24hr_change=true"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for coin_id, coin_name in zip(coins, coin_names):
                        if coin_id in data:
                            price = data[coin_id]["usd"]
                            change_24h = data[coin_id].get("usd_24h_change", 0)
                            
                            crypto_data[coin_name] = {
                                "precio": f"${price:,.2f}",
                                "cambio": f"{change_24h:+.2f}%" if change_24h else "0.00%",
                                "valor": price,
                                "fuente": "CoinGecko"
                            }
            except Exception as e:
                pass
        
        return crypto_data

    @st.cache_data(ttl=300)
    def obtener_datos_commodities():
        """Obtiene datos de materias primas"""
        commodities_data = {}
        
        # Fuente 1: Yahoo Finance - 6 COMMODITIES
        yf_commodities = {
            "Petróleo WTI": "CL=F",
            "Petróleo Brent": "BZ=F", 
            "Oro": "GC=F",
            "Plata": "SI=F",
            "Cobre": "HG=F",
            "Gas Natural": "NG=F"
        }
        
        for nombre, ticker in yf_commodities.items():
            try:
                comm = yf.Ticker(ticker)
                hist = comm.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = ((current - previous) / previous) * 100
                    
                    if nombre in ["Oro", "Plata"]:
                        precio_str = f"${current:,.2f}"
                    elif nombre in ["Petróleo WTI", "Petróleo Brent", "Gas Natural"]:
                        precio_str = f"${current:.2f}"
                    else:
                        precio_str = f"${current:.2f}"
                    
                    commodities_data[nombre] = {
                        "precio": precio_str,
                        "cambio": f"{change:+.2f}%",
                        "valor": current,
                        "fuente": "Yahoo Finance"
                    }
            except Exception as e:
                continue
        
        return commodities_data

    @st.cache_data(ttl=3600)
    def obtener_datos_tasas_reales():
        """Obtiene tasas de interés REALES de múltiples fuentes"""
        tasas_data = {}
        
        try:
            # FUENTE 1: Yahoo Finance para bonos gubernamentales
            bonos_yahoo = {
                "USA 2 años": "^IRX",
                "USA 10 años": "^TNX", 
                "USA 30 años": "^TYX",
                "USA 5 años": "^FVX"
            }
            
            for nombre, ticker in bonos_yahoo.items():
                try:
                    bono = yf.Ticker(ticker)
                    hist = bono.history(period="2d")
                    if not hist.empty:
                        yield_val = hist['Close'].iloc[-1]
                        if 0.1 < yield_val < 20:
                            tasas_data[nombre] = {
                                "valor": f"{yield_val:.2f}%",
                                "fuente": "Yahoo Finance",
                                "categoria": "bonos"
                            }
                except Exception as e:
                    continue

            # FUENTE 2: CoinGecko para tasas de cripto
            try:
                url = "https://api.coingecko.com/api/v3/global"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        market_data = data["data"]
                        total_volume = market_data.get("total_volume", {})
                        market_cap = market_data.get("total_market_cap", {})
                        
                        if "usd" in total_volume:
                            vol_str = f"${total_volume['usd']:,.0f}"
                            tasas_data["Vol Cripto 24h"] = {
                                "valor": vol_str,
                                "fuente": "CoinGecko", 
                                "categoria": "cripto"
                            }
                        
                        if "usd" in market_cap:
                            cap_str = f"${market_cap['usd']:,.0f}"
                            tasas_data["Market Cap Cripto"] = {
                                "valor": cap_str,
                                "fuente": "CoinGecko",
                                "categoria": "cripto"
                            }
            except Exception as e:
                pass

            # FUENTE 3: Yahoo Finance para ETFs de bonos
            etf_bonos = {
                "HYG": "Bono High Yield",
                "LQD": "Bono Investment Grade", 
                "MUB": "Bono Municipal",
                "TLT": "Bono Largo Plazo",
                "IEF": "Bono 7-10 años",
                "SHY": "Bono 1-3 años"
            }
            
            for ticker, nombre in etf_bonos.items():
                try:
                    etf = yf.Ticker(ticker)
                    info = etf.info
                    dividend_yield = info.get('yield', info.get('trailingAnnualDividendYield', 0))
                    if dividend_yield and dividend_yield > 0:
                        tasas_data[nombre] = {
                            "valor": f"{(dividend_yield * 100):.2f}%",
                            "fuente": "ETF Yield",
                            "categoria": "bonos_etf"
                        }
                except Exception as e:
                    continue

            # FUENTE 4: Yahoo Finance para tasas SOFR
            try:
                sofr = yf.Ticker("SOFR")
                hist_sofr = sofr.history(period="1d")
                if not hist_sofr.empty:
                    tasa_sofr = hist_sofr['Close'].iloc[-1]
                    tasas_data["SOFR"] = {
                        "valor": f"{tasa_sofr:.2f}%",
                        "fuente": "Yahoo Finance",
                        "categoria": "tasas_referencia"
                    }
            except:
                pass

            # FUENTE 5: Calcular spreads de curvas de rendimiento
            try:
                bono_2y = yf.Ticker("^IRX")
                bono_10y = yf.Ticker("^TNX")
                
                hist_2y = bono_2y.history(period="1d")
                hist_10y = bono_10y.history(period="1d")
                
                if not hist_2y.empty and not hist_10y.empty:
                    yield_2y = hist_2y['Close'].iloc[-1]
                    yield_10y = hist_10y['Close'].iloc[-1]
                    curve_spread = yield_10y - yield_2y
                    
                    tasas_data["Spread 10y-2y"] = {
                        "valor": f"{curve_spread:+.2f}%",
                        "fuente": "Yahoo Finance", 
                        "categoria": "curva_rendimiento"
                    }
            except:
                pass

        except Exception as e:
            st.error(f"Error obteniendo tasas: {str(e)}")
        
        return tasas_data

    @st.cache_data(ttl=1800)
    def obtener_analisis_completo(indices, forex, crypto, commodities, tasas):
        """Genera análisis con todos los datos disponibles"""
        try:
            # Contar datos disponibles
            stats = {
                "indices": len(indices),
                "forex": len(forex),
                "crypto": len(crypto),
                "commodities": len(commodities),
                "tasas": len(tasas)
            }
            
            total_datos = sum(stats.values())
            
            if total_datos == 0:
                return "🔍 **Estado del Sistema:** Conectando a fuentes de datos...\n\nLos datos se cargarán automáticamente en unos segundos."
            
            # Crear resumen para el prompt
            resumen_datos = {
                "indices": {k: f"{v['precio']} ({v['cambio']})" for k, v in indices.items()},
                "forex": {k: f"{v['precio']} ({v['cambio']})" for k, v in forex.items()},
                "crypto": {k: f"{v['precio']} ({v['cambio']})" for k, v in crypto.items()},
                "commodities": {k: f"{v['precio']} ({v['cambio']})" for k, v in commodities.items()},
                "tasas": {k: v["valor"] for k, v in tasas.items()}
            }

            prompt = f"""
            Analiza los siguientes datos financieros en tiempo real:

            ÍNDICES BURSÁTILES ({stats['indices']} índices):
            {resumen_datos['indices']}

            DIVISAS ({stats['forex']} pares):
            {resumen_datos['forex']}

            CRIPTOMONEDAS ({stats['crypto']} activos):
            {resumen_datos['crypto']}

            MATERIAS PRIMAS ({stats['commodities']} commodities):
            {resumen_datos['commodities']}

            TASAS DE INTERÉS ({stats['tasas']} tasas):
            {resumen_datos['tasas']}

            Proporciona un análisis profesional que incluya:
            1. Tendencias principales del mercado
            2. Movimientos significativos en activos clave
            3. Perspectiva de riesgo y oportunidades
            4. Contexto macroeconómico relevante

            Máximo 200 palabras. Enfoque en insights accionables.
            Basado únicamente en los datos proporcionados.
            """

            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"📊 **Datos Cargados:** {total_datos} activos | Análisis disponible en próxima actualización"

    # OBTENER TODOS LOS DATOS
    with st.spinner('🔄 Conectando con fuentes de datos globales...'):
        indices = obtener_datos_indices()
        forex = obtener_datos_forex()
        crypto = obtener_datos_cripto()
        commodities = obtener_datos_commodities()
        tasas = obtener_datos_tasas_reales()
        analisis = obtener_analisis_completo(indices, forex, crypto, commodities, tasas)

    # DISEÑO DE LA INTERFAZ
    st.markdown("### 🤖 Análisis de Mercados en Tiempo Real")
    with st.container():
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px; margin: 15px 0;'>
        <h4 style='color: white; margin-bottom: 15px;'>ANÁLISIS GLOBAL</h4>
        """, unsafe_allow_html=True)
        st.write(analisis)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ESTADÍSTICAS DE DATOS
    total_activos = len(indices) + len(forex) + len(crypto) + len(commodities)
    st.markdown(f"### 📊 Indicadores del Mercado Global ({total_activos} activos cargados)")

    # INDICADORES PRINCIPALES
    st.markdown("#### 🎯 Indicadores Clave")
    col1, col2, col3, col4 = st.columns(4)
    
    indicadores_principales = [
        ("S&P 500", indices.get("S&P 500")),
        ("EUR/USD", forex.get("EUR/USD")),
        ("Bitcoin", crypto.get("Bitcoin")),
        ("Oro", commodities.get("Oro"))
    ]
    
    for i, (nombre, datos) in enumerate(indicadores_principales):
        with [col1, col2, col3, col4][i]:
            if datos:
                st.metric(
                    label=nombre,
                    value=datos["precio"],
                    delta=datos["cambio"]
                )
                st.caption(f"Fuente: {datos.get('fuente', 'Directo')}")
            else:
                st.metric(label=nombre, value="Cargando...")
                st.caption("Conectando...")

    st.markdown("---")

    # SECCIÓN DE ÍNDICES - CON COLORES PARA FONDO OSCURO
    if indices:
        st.markdown("#### 📈 Índices Bursátiles Globales")
        cols = st.columns(4)
        for i, (nombre, datos) in enumerate(indices.items()):
            with cols[i % 4]:
                with st.container():
                    st.markdown(f"""
                    <div style='background-color: #1E1E1E; padding: 15px; border-radius: 10px; 
                                border-left: 4px solid #2E86AB; margin: 5px 0; border: 1px solid #444;'>
                    <div style='font-weight: bold; color: white;'>{nombre}</div>
                    <div style='font-size: 1.2em; color: white;'>{datos['precio']}</div>
                    <div style='color: {'#4CAF50' if '+' in datos['cambio'] else '#F44336'}; font-weight: bold;'>
                        {datos['cambio']}
                    </div>
                    <div style='font-size: 0.8em; color: #CCCCCC;'>
                        YTD: {datos.get('ytd', 'N/A')} | {datos.get('fuente', 'Directo')}
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # SECCIÓN DE DIVISAS Y CRIPTO - FORMATO FORMAL
    col_divisas, col_cripto = st.columns(2)
    
    with col_divisas:
        if forex:
            st.markdown("#### 💵 Divisas Principales")
            for par, datos in list(forex.items())[:6]:
                st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 12px; border-radius: 8px; 
                            border: 1px solid #444; margin: 8px 0;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='font-weight: bold; color: white; font-size: 14px;'>{par}</div>
                    <div style='display: flex; flex-direction: column; align-items: end;'>
                        <div style='color: white; font-weight: bold; font-size: 14px;'>{datos['precio']}</div>
                        <div style='color: {'#4CAF50' if '+' in datos['cambio'] else '#F44336'}; font-size: 12px;'>
                            {datos['cambio']}
                        </div>
                    </div>
                </div>
                <div style='font-size: 11px; color: #CCCCCC; margin-top: 5px;'>
                    {datos.get('fuente', 'Directo')}
                </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("#### 💵 Divisas")
            st.info("Cargando datos de divisas...")
    
    with col_cripto:
        if crypto:
            st.markdown("#### ₿ Criptomonedas")
            for moneda, datos in list(crypto.items())[:5]:
                st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 12px; border-radius: 8px; 
                            border: 1px solid #444; margin: 8px 0;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='font-weight: bold; color: white; font-size: 14px;'>{moneda}</div>
                    <div style='display: flex; flex-direction: column; align-items: end;'>
                        <div style='color: white; font-weight: bold; font-size: 14px;'>{datos['precio']}</div>
                        <div style='color: {'#4CAF50' if '+' in datos['cambio'] else '#F44336'}; font-size: 12px;'>
                            {datos['cambio']}
                        </div>
                    </div>
                </div>
                <div style='font-size: 11px; color: #CCCCCC; margin-top: 5px;'>
                    {datos.get('fuente', 'Directo')}
                </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("#### ₿ Criptomonedas")
            st.info("Cargando datos cripto...")

    st.markdown("---")

    # SECCIÓN DE COMMODITIES - FORMATO FORMAL
    if commodities:
        st.markdown("#### 🛢️ Materias Primas")
        cols = st.columns(3)
        for i, (producto, datos) in enumerate(commodities.items()):
            with cols[i % 3]:
                st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 15px; border-radius: 10px; 
                            border: 1px solid #444; margin: 8px 0; text-align: center;'>
                <div style='font-weight: bold; color: white; font-size: 14px; margin-bottom: 8px;'>{producto}</div>
                <div style='color: white; font-size: 16px; font-weight: bold; margin-bottom: 5px;'>{datos['precio']}</div>
                <div style='color: {'#4CAF50' if '+' in datos['cambio'] else '#F44336'}; font-size: 13px; font-weight: bold;'>
                    {datos['cambio']}
                </div>
                <div style='font-size: 11px; color: #CCCCCC; margin-top: 8px;'>
                    {datos.get('fuente', 'Directo')}
                </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # SECCIÓN DE TASAS - FORMATO FORMAL
    if tasas:
        st.markdown("#### 🏦 Tasas de Interés y Bonos")
        
        # Organizar en cuadros formales
        cols = st.columns(4)
        tasas_items = list(tasas.items())
        
        for i, (nombre, datos) in enumerate(tasas_items):
            with cols[i % 4]:
                st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 15px; border-radius: 10px; 
                            border: 1px solid #444; margin: 8px 0; text-align: center;'>
                <div style='font-weight: bold; color: white; font-size: 13px; margin-bottom: 10px; 
                            height: 40px; display: flex; align-items: center; justify-content: center;'>
                    {nombre}
                </div>
                <div style='color: white; font-size: 16px; font-weight: bold; margin-bottom: 8px;'>
                    {datos['valor']}
                </div>
                <div style='font-size: 11px; color: #CCCCCC;'>
                    {datos.get('fuente', 'Directo')}
                </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🏦 Cargando datos de tasas y bonos...")

    # PANEL DE CONTROL
    st.markdown("---")
    
    col_stats, col_control = st.columns([2, 1])
    
    with col_stats:
        st.markdown(f"""
        **📈 Estado del Sistema:**
        - Activos cargados: **{total_activos}**
        - Índices: **{len(indices)}**
        - Divisas: **{len(forex)}** 
        - Cripto: **{len(crypto)}**
        - Commodities: **{len(commodities)}**
        - Tasas: **{len(tasas)}**
        - Última actualización: **{datetime.now().strftime('%H:%M:%S')}**
        """)
    
    with col_control:
        if st.button("🔄 Actualizar Datos", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    st.markdown("""
    **💡 Información:** Los datos se actualizan automáticamente cada 5 minutos.
    Durante fines de semana y festivos, algunos mercados pueden mostrar datos del último cierre.
    """)

    # Nota sobre APIs
    st.markdown("""
    **🔧 Configuración de APIs:**
    Para mejor rendimiento, obtén API keys gratuitas en:
    - [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
    - [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs/)
    - [CurrencyAPI](https://currencyapi.com/) ✅ INTEGRADA
    """)



















# BOTONES ADICIONALES EN EL FOOTER
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    # Generar reporte de texto
    if st.button("📄 Generar Reporte", use_container_width=True):
        try:
            datos = yf.download(stonk, period="1y")
            scoring, metricas = calcular_scoring_fundamental(info)
            reporte_texto = generar_reporte_texto(stonk, info, datos, scoring, metricas)
            
            st.download_button(
                label="📥 Descargar Reporte (TXT)",
                data=reporte_texto,
                file_name=f"reporte_{stonk}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generando reporte: {str(e)}")

with col2:
    # Agregar a favoritos
    if stonk not in st.session_state.favoritas:
        if st.button("⭐ Agregar a Favoritos", use_container_width=True):
            st.session_state.favoritas.append(stonk)
            st.success(f"✅ {stonk} agregado a favoritos")
            st.rerun()
    else:
        if st.button("🗑️ Quitar de Favoritos", use_container_width=True):
            st.session_state.favoritas.remove(stonk)
            st.success(f"✅ {stonk} removido de favoritos")
            st.rerun()

with col3:
    # Historial de búsquedas
    if st.session_state.historial_busquedas:
        with st.popover("🔍 Historial Búsquedas"):
            for busqueda in reversed(st.session_state.historial_busquedas):
                if st.button(f"📌 {busqueda}", key=f"hist_{busqueda}"):
                    st.session_state.seccion_actual = "info"
                    st.rerun()

# FAVORITOS RÁPIDOS
if st.session_state.favoritas:
    st.markdown("---")
    st.write("⭐ **Favoritos Rápidos:**")
    cols_fav = st.columns(len(st.session_state.favoritas))
    
    for i, favorita in enumerate(st.session_state.favoritas):
        with cols_fav[i]:
            if st.button(f"📈 {favorita}", use_container_width=True, key=f"fav_{favorita}"):
                st.session_state.seccion_actual = "info"

# --- DISCLAIMER FINAL ---
st.markdown("""
---
<p style='text-align: center; font-size: 13px; color: gray;'>
© 2025 Todos los derechos reservados. Desarrollado por <strong>Jesús Alberto Cárdenas Serrano.</strong>
<br><em>Esta aplicación es con fines educativos. No constituye asesoramiento financiero.</em>
</p>
""", unsafe_allow_html=True)