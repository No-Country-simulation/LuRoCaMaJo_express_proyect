# app.py (FastAPI)
from fastapi import FastAPI, BackgroundTasks, HTTPException
import requests
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import json
import httpx
from typing import List, Dict
from collections import Counter
from fastapi.middleware.cors import CORSMiddleware
import random
from prophet import Prophet  # Añadir esta importación al inicio de app.py
# import openai  # lo usaremos más adelante si volvemos a integrar IA

app = FastAPI(title="API de Análisis de Tendencias de Mercado Libre")
# Justo después de app = FastAPI(...) añade:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)
# Datos de ejemplo hardcodeados
mock_data = [
    {"keyword": "tododia", "url": "https://listado.mercadolibre.com.ar/tododia"},
    {"keyword": "maquillaje", "url": "https://listado.mercadolibre.com.ar/maquillaje"},
    {"keyword": "perfume", "url": "https://listado.mercadolibre.com.ar/perfume"},
    {"keyword": "crema facial", "url": "https://listado.mercadolibre.com.ar/crema-facial"},
    {"keyword": "labial", "url": "https://listado.mercadolibre.com.ar/labial"},
    {"keyword": "shampoo", "url": "https://listado.mercadolibre.com.ar/shampoo"},
    {"keyword": "acondicionador", "url": "https://listado.mercadolibre.com.ar/acondicionador"},
    {"keyword": "base maquillaje", "url": "https://listado.mercadolibre.com.ar/base-maquillaje"},
    {"keyword": "serum", "url": "https://listado.mercadolibre.com.ar/serum"},
    {"keyword": "mascarilla facial", "url": "https://listado.mercadolibre.com.ar/mascarilla-facial"},
    {"keyword": "delineador ojos", "url": "https://listado.mercadolibre.com.ar/delineador-ojos"},
    {"keyword": "polvo compacto", "url": "https://listado.mercadolibre.com.ar/polvo-compacto"},
    {"keyword": "ekos", "url": "https://listado.mercadolibre.com.ar/ekos"},
    {"keyword": "aceite corporal", "url": "https://listado.mercadolibre.com.ar/aceite-corporal"},
    {"keyword": "antiarrugas", "url": "https://listado.mercadolibre.com.ar/antiarrugas"},
    {"keyword": "fragancia femenina", "url": "https://listado.mercadolibre.com.ar/fragancia-femenina"},
    {"keyword": "secador pelo", "url": "https://listado.mercadolibre.com.ar/secador-pelo"},
    {"keyword": "coloración cabello", "url": "https://listado.mercadolibre.com.ar/coloracion-cabello"},
    {"keyword": "colonia", "url": "https://listado.mercadolibre.com.ar/colonia"},
    {"keyword": "sombra ojos", "url": "https://listado.mercadolibre.com.ar/sombra-ojos"},
    {"keyword": "capilar", "url": "https://listado.mercadolibre.com.ar/capilar"},
    {"keyword": "crema corporal", "url": "https://listado.mercadolibre.com.ar/crema-corporal"},
    {"keyword": "perfume importado", "url": "https://listado.mercadolibre.com.ar/perfume-importado"},
    {"keyword": "eau de toilette", "url": "https://listado.mercadolibre.com.ar/eau-de-toilette"},
    {"keyword": "limpieza facial", "url": "https://listado.mercadolibre.com.ar/limpieza-facial"},
    {"keyword": "corte pelo", "url": "https://listado.mercadolibre.com.ar/corte-pelo"},
    {"keyword": "tinte cabello", "url": "https://listado.mercadolibre.com.ar/tinte-cabello"},
    {"keyword": "crema hidratante", "url": "https://listado.mercadolibre.com.ar/crema-hidratante"},
    {"keyword": "protector solar", "url": "https://listado.mercadolibre.com.ar/protector-solar"},
    {"keyword": "máscara pestañas", "url": "https://listado.mercadolibre.com.ar/mascara-pestanas"},
    {"keyword": "vitamina c", "url": "https://listado.mercadolibre.com.ar/vitamina-c"},
    {"keyword": "exfoliante", "url": "https://listado.mercadolibre.com.ar/exfoliante"},
    {"keyword": "rubor", "url": "https://listado.mercadolibre.com.ar/rubor"},
    {"keyword": "crema antiedad", "url": "https://listado.mercadolibre.com.ar/crema-antiedad"},
    {"keyword": "spray cabello", "url": "https://listado.mercadolibre.com.ar/spray-cabello"},
    {"keyword": "maquillaje profesional", "url": "https://listado.mercadolibre.com.ar/maquillaje-profesional"},
    {"keyword": "shampoo anticaspa", "url": "https://listado.mercadolibre.com.ar/shampoo-anticaspa"},
    {"keyword": "crema antiarrugas", "url": "https://listado.mercadolibre.com.ar/crema-antiarrugas"},
    {"keyword": "suero facial", "url": "https://listado.mercadolibre.com.ar/suero-facial"},
    {"keyword": "keratina", "url": "https://listado.mercadolibre.com.ar/keratina"},
    {"keyword": "fragancia masculina", "url": "https://listado.mercadolibre.com.ar/fragancia-masculina"},
    {"keyword": "rizador cabello", "url": "https://listado.mercadolibre.com.ar/rizador-cabello"},
    {"keyword": "limpieza facial profunda", "url": "https://listado.mercadolibre.com.ar/limpieza-facial-profunda"},
    {"keyword": "tonico facial", "url": "https://listado.mercadolibre.com.ar/tonico-facial"},
    {"keyword": "tratamiento capilar", "url": "https://listado.mercadolibre.com.ar/tratamiento-capilar"},
    {"keyword": "base líquida", "url": "https://listado.mercadolibre.com.ar/base-liquida"},
    {"keyword": "aceite para barba", "url": "https://listado.mercadolibre.com.ar/aceite-para-barba"},
    {"keyword": "agua micelar", "url": "https://listado.mercadolibre.com.ar/agua-micelar"},
    {"keyword": "regalo belleza", "url": "https://listado.mercadolibre.com.ar/regalo-belleza"},
    {"keyword": "maquina afeitar", "url": "https://listado.mercadolibre.com.ar/maquina-afeitar"}
]

# Categorías para clasificar las keywords
categories = {
    "maquillaje": ["maquillaje", "base", "polvo", "labial", "sombra", "delineador", "rubor", "pestañas"],
    "cuidado_piel": ["crema", "serum", "aceite", "mascarilla", "facial", "antiarrugas", "hidratante", "protector", "solar", "vitamina", "exfoliante", "antiedad", "limpieza", "tónico", "agua micelar"],
    "cabello": ["shampoo", "acondicionador", "pelo", "cabello", "cortar", "capilar", "secador", "coloración", "tinte", "spray", "keratina", "rizador", "tratamiento capilar"],
    "perfume": ["perfume", "fragancia", "colonia", "eau", "tododia", "ekos"],
    "otros": []  # Categoría por defecto
}

# Fechas de ejemplo hardcodeadas para simular diferentes días
mock_dates = [
    "2025-04-01",
    "2025-04-02",
    "2025-04-03",
    "2025-04-04",
    "2025-04-05"
]

# Función para inicializar la base de datos
def init_db():
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    # Tabla para almacenar las keywords individuales
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keywords_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        category TEXT NOT NULL,
        capture_date DATE NOT NULL,
        capture_time TIME NOT NULL
    )
    ''')
    
    # Tabla para almacenar el ranking de keywords
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keyword_rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        count INTEGER NOT NULL,
        last_date DATE NOT NULL,
        last_time TIME NOT NULL
    )
    ''')
    
    # Tabla para almacenar el ranking de categorías
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS category_rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        count INTEGER NOT NULL,
        last_date DATE NOT NULL,
        last_time TIME NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Función para categorizar una keyword
def categorize_keyword(keyword):
    keyword_lower = keyword.lower()
    
    for category, keywords in categories.items():
        for key in keywords:
            if key in keyword_lower:
                return category
    
    return "otros"

# Función para capturar y guardar datos

def capture_and_save_data():
    current_date = random.choice(mock_dates)
    current_time = datetime.now().strftime("%H:%M:%S")
    random.shuffle(mock_data)
    selected_data = mock_data[:20]
    
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    try:
        for item in selected_data:
            keyword = item["keyword"]
            category = categorize_keyword(keyword)
            
            cursor.execute(
                "INSERT INTO keywords_data (keyword, category, capture_date, capture_time) VALUES (?, ?, ?, ?)",
                (keyword, category, current_date, current_time)
            )
            
            cursor.execute(
                "SELECT count, last_date, last_time FROM keyword_rankings WHERE keyword = ?",
                (keyword,)
            )
            result = cursor.fetchone()
            
            if result:
                count, last_date, last_time = result
                cursor.execute(
                    "UPDATE keyword_rankings SET count = ?, last_date = ?, last_time = ? WHERE keyword = ?",
                    (count + 1, current_date, current_time, keyword)
                )
            else:
                cursor.execute(
                    "INSERT INTO keyword_rankings (keyword, count, last_date, last_time) VALUES (?, ?, ?, ?)",
                    (keyword, 1, current_date, current_time)
                )
            
            cursor.execute(
                "SELECT count, last_date, last_time FROM category_rankings WHERE category = ?",
                (category,)
            )
            result = cursor.fetchone()
            
            if result:
                count, last_date, last_time = result
                cursor.execute(
                    "UPDATE category_rankings SET count = ?, last_date = ?, last_time = ? WHERE category = ?",
                    (count + 1, current_date, current_time, category)
                )
            else:
                cursor.execute(
                    "INSERT INTO category_rankings (category, count, last_date, last_time) VALUES (?, ?, ?, ?)",
                    (category, 1, current_date, current_time)
                )
        
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        conn.close()
    
    return {
        "status": "success",
        "message": f"Datos capturados y guardados correctamente en la fecha {current_date} a las {current_time}",
        "captured_keywords": len(selected_data)
    }

# Endpoints para el dashboard

@app.get("/")
def read_root():
    return {"message": "API de Análisis de Tendencias de Mercado Libre"}

@app.post("/update-trends")
def update_trends(background_tasks: BackgroundTasks):
    """Endpoint para actualizar las tendencias (se activa con el botón del dashboard)"""
    try:
        result = capture_and_save_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar tendencias: {str(e)}")

@app.get("/top-keywords")
def get_top_keywords(limit: int = 10):
    """Obtener las top palabras clave"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT keyword, count 
        FROM keyword_rankings 
        ORDER BY count DESC, last_date DESC, last_time DESC 
        LIMIT ?
    """, (limit,))
    
    result = [{"keyword": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return result

@app.get("/category-distribution")
def get_category_distribution():
    """Obtener la distribución por categorías para el gráfico de anillo"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category, count 
        FROM category_rankings 
        ORDER BY count DESC
    """)
    
    result = [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return result

@app.get("/trend-evolution")
def get_trend_evolution(top_keywords: int = 5):
    """Obtener la evolución de tendencias para las top palabras clave (acumulado)"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    # Obtener las top keywords
    cursor.execute("""
        SELECT keyword 
        FROM keyword_rankings 
        ORDER BY count DESC, last_date DESC, last_time DESC 
        LIMIT ?
    """, (top_keywords,))
    
    top_keywords_list = [row[0] for row in cursor.fetchall()]
    
    result = []
    
    for keyword in top_keywords_list:
        # Calcular el conteo acumulado hasta cada fecha
        cursor.execute("""
            SELECT capture_date, 
                   (SELECT COUNT(*) 
                    FROM keywords_data sub 
                    WHERE sub.keyword = ? 
                    AND sub.capture_date <= main.capture_date) as cumulative_count
            FROM keywords_data main
            WHERE keyword = ?
            GROUP BY capture_date
            ORDER BY capture_date
        """, (keyword, keyword))
        
        for row in cursor.fetchall():
            result.append({
                "keyword": keyword,
                "date": row[0],
                "count": row[1]
            })
    
    conn.close()
    
    return result

    """Obtener la evolución de tendencias para las top palabras clave"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    # Obtener las top keywords
    cursor.execute("""
        SELECT keyword 
        FROM keyword_rankings 
        ORDER BY count DESC, last_date DESC, last_time DESC 
        LIMIT ?
    """, (top_keywords,))
    
    top_keywords_list = [row[0] for row in cursor.fetchall()]
    
    # Inicializar como lista vacía
    result = []
    
    # Para cada keyword, obtener su evolución en el tiempo
    for keyword in top_keywords_list:
        cursor.execute("""
            SELECT capture_date, COUNT(*) as daily_count 
            FROM keywords_data 
            WHERE keyword = ? 
            GROUP BY capture_date 
            ORDER BY capture_date
        """, (keyword,))
        
        for row in cursor.fetchall():
            result.append({
                "keyword": keyword,
                "date": row[0],
                "count": row[1]
            })
    
    conn.close()
    
    return result
@app.get("/top-keywords-list")
def get_top_keywords_list(limit: int = 20):
    """Obtener listado de top keywords con número de repeticiones"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT keyword, count 
        FROM keyword_rankings 
        ORDER BY count DESC, last_date DESC, last_time DESC 
        LIMIT ?
    """, (limit,))
    
    result = [{"keyword": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return result

@app.get("/most-searched-keyword")
def get_most_searched_keyword():
    """Obtener la palabra más buscada con su cantidad de repeticiones"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT keyword, count 
        FROM keyword_rankings 
        ORDER BY count DESC, last_date DESC, last_time DESC 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"keyword": result[0], "count": result[1]}
    else:
        return {"keyword": "No hay datos", "count": 0}
    
@app.get("/capture-history")
def get_capture_history(limit_captures: int = 10):
    """Obtener el histórico de capturas agrupado por fecha y hora"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    # Obtener las combinaciones únicas de capture_date y capture_time, limitadas a las más recientes
    cursor.execute("""
        SELECT DISTINCT capture_date, capture_time
        FROM keywords_data
        ORDER BY capture_date DESC, capture_time DESC
        LIMIT ?
    """, (limit_captures,))
    
    capture_times = cursor.fetchall()
    
    result = []
    for capture_date, capture_time in capture_times:
        # Obtener todas las palabras clave para esta captura
        cursor.execute("""
            SELECT keyword
            FROM keywords_data
            WHERE capture_date = ? AND capture_time = ?
            ORDER BY keyword
        """, (capture_date, capture_time))
        
        keywords = [row[0] for row in cursor.fetchall()]
        result.append({
            "date": capture_date,
            "time": capture_time,
            "keywords": keywords
        })
    
    conn.close()
    
    return result

    """Obtener el histórico de capturas de datos con las palabras clave"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT capture_date, capture_time, keyword 
        FROM keywords_data 
        ORDER BY capture_date DESC, capture_time DESC
        LIMIT 20
    """)
    
    result = [{"date": row[0], "time": row[1], "keyword": row[2]} for row in cursor.fetchall()]
    conn.close()
    
    return result

# Rutas para escalabilidad futura  PROPHETTTTTTTTTTTT

 # Corrige la indentación del método get_prophet_forecast
# Actualmente está indentado incorrectamente
# Debe estar al mismo nivel que los otros endpoints

@app.get("/prophet-forecast")
def get_prophet_forecast(keyword: str = None, forecast_days: int = 7):
    """Endpoint para análisis de tendencias con Prophet"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    # Si no se proporciona una keyword, usar la más buscada
    if not keyword:
        cursor.execute("""
            SELECT keyword 
            FROM keyword_rankings 
            ORDER BY count DESC 
            LIMIT 1
        """)
        keyword = cursor.fetchone()[0]
    
    # Obtener datos históricos para la keyword seleccionada
    cursor.execute("""
        SELECT capture_date, COUNT(*) as daily_count 
        FROM keywords_data 
        WHERE keyword = ? 
        GROUP BY capture_date 
        ORDER BY capture_date
    """, (keyword,))
    
    data = cursor.fetchall()
    conn.close()
    
    if len(data) < 2:
        return {
            "status": "error",
            "message": f"No hay suficientes datos históricos para '{keyword}' (mínimo 2 días)"
        }
    
    # Preparar datos para Prophet (necesita columnas 'ds' y 'y')
    df = pd.DataFrame(data, columns=['ds', 'y'])
    df['ds'] = pd.to_datetime(df['ds'])
    
    # Crear y entrenar el modelo Prophet
    model = Prophet(daily_seasonality=True, yearly_seasonality=False, weekly_seasonality=False)
    model.fit(df)
    
    # Hacer predicciones para los próximos 'forecast_days'
    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)
    
    # Seleccionar columnas relevantes para la respuesta
    forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_days).to_dict(orient='records')
    
    # Formatear la respuesta
    result = {
        "status": "success",
        "keyword": keyword,
        "historical_data": df.to_dict(orient='records'),
        "forecast_data": [
            {
                "date": row['ds'].strftime('%Y-%m-%d'),
                "predicted_count": round(row['yhat'], 2),
                "lower_bound": round(row['yhat_lower'], 2),
                "upper_bound": round(row['yhat_upper'], 2)
            } for row in forecast_data
        ]
    }
    
    return result

@app.get("/prophet-forecast-compare")
def get_prophet_forecast_compare(keywords: str = None, forecast_days: int = 7):
    """Endpoint para comparar tendencias de múltiples keywords con Prophet"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    if not keywords:
        cursor.execute("SELECT keyword FROM keyword_rankings ORDER BY count DESC LIMIT 1")
        keyword_list = [cursor.fetchone()[0]]
    else:
        keyword_list = [k.strip() for k in keywords.split(",")]
    
    result = {"status": "success", "forecasts": {}}
    
    for keyword in keyword_list:
        cursor.execute("""
            SELECT capture_date, COUNT(*) as daily_count 
            FROM keywords_data 
            WHERE keyword = ? 
            GROUP BY capture_date 
            ORDER BY capture_date
        """, (keyword,))
        data = cursor.fetchall()
        
        if len(data) < 2:
            result["forecasts"][keyword] = {"status": "error", "message": f"No hay suficientes datos para '{keyword}'"}
            continue
        
        df = pd.DataFrame(data, columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'])
        
        model = Prophet(daily_seasonality=True, yearly_seasonality=False, weekly_seasonality=False)
        model.fit(df)
        
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)
        forecast_data = forecast[['ds', 'yhat']].tail(forecast_days).to_dict(orient='records')
        
        result["forecasts"][keyword] = {
            "historical_data": df.to_dict(orient='records'),
            "forecast_data": [{"date": row['ds'].strftime('%Y-%m-%d'), "predicted_count": round(row['yhat'], 2)} for row in forecast_data]
        }
    
    conn.close()
    return result

    # Rutas para escalabilidad futura  PROPHETTTTTTTTTTTT
@app.get("/category-flow")
def get_category_flow():
    """Endpoint para obtener transiciones entre categorías"""
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    
    # Obtener palabras clave ordenadas por fecha
    cursor.execute("""
        SELECT keyword, capture_date 
        FROM keywords_data 
        ORDER BY capture_date
    """)
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        return {"status": "error", "message": "No hay datos para generar el flujo"}
    
    # Crear transiciones entre categorías consecutivas
    nodes = set()
    links = {}
    for i in range(len(data) - 1):
        current_keyword = data[i][0]
        next_keyword = data[i + 1][0]
        current_category = categorize_keyword(current_keyword)
        next_category = categorize_keyword(next_keyword)
        if current_category and next_category and current_category != next_category:
            nodes.add(current_category)
            nodes.add(next_category)
            link_key = (current_category, next_category)
            links[link_key] = links.get(link_key, 0) + 1
    
    # Preparar datos para Sankey
    node_list = list(nodes)
    source = [node_list.index(k[0]) for k in links.keys()]
    target = [node_list.index(k[1]) for k in links.keys()]
    value = list(links.values())
    
    return {
        "status": "success",
        "nodes": node_list,
        "links": {
            "source": source,
            "target": target,
            "value": value
        }
    }

@app.get("/contextual-analysis")
def get_contextual_analysis():
    """Endpoint para análisis contextual con IA (a implementar)"""
    return {
        "status": "not_implemented",
        "message": "El análisis contextual con IA será implementado en futuras versiones"
    }

# Inicializar la base de datos al inicio
@app.on_event("startup")
def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)