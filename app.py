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
from prophet import Prophet

app = FastAPI(title="API de Análisis de Tendencias de Mercado Libre")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Categorías para clasificar las keywords
categories = {
    "maquillaje": ["maquillaje", "base", "polvo", "labial", "sombra", "delineador", "rubor", "pestañas", "bb cream", "effaclar bb"],
    
    "cuidado_piel": ["crema", "serum", "aceite", "mascarilla", "facial", "antiarrugas", "hidratante", "protector", "solar", 
                     "vitamina", "exfoliante", "antiedad", "limpieza", "tónico", "agua micelar", "acido hialuronico", 
                     "eucerin", "anti pigmento", "syndet", "vaselina", "neutrogena", "nivea", "olaplex", "clarins"],
    
    "cabello": ["shampoo", "acondicionador", "pelo", "cabello", "cortar", "capilar", "secador", "coloración", "tinte", 
                "spray", "keratina", "rizador", "tratamiento capilar", "recortadora", "wahl", "peluqueria", "peluquero", 
                "banda rizadora", "ondas", "seda"],
    
    "perfume": ["perfume", "fragancia", "colonia", "eau", "tododia", "ekos", "victoria s secret", "body mist", "mist", 
                "seduction", "rouge", "natura"],
    
    "cuidado_corporal": ["aceite para masajes", "jabon", "agua oxigenada", "lip oil", "afeitadora", "afeitadoras", 
                         "masajes", "tododia"],
    
    "farmacia_medicamentos": ["mometasona", "spray nasal", "lomecan", "ovulos", "cremas para hemorroides", "rifocina", 
                             "heridas", "hongos", "ketoconazol", "clotrimazol", "balanitis", "dermexane", "clobetasol", 
                             "piecidex", "antimicotico", "peroxido de benzoilo", "farmacia", "leloir", "gps farma", 
                             "iruxol", "cicatrizante", "farm x"],
    
    "tratamientos_estéticos": ["implante capilar", "plasma rico en plaquetas", "restylane", "verrugas", "lumigan", 
                              "mesoterapia", "sculptra", "ozonoterapia"],
    
    "tiendas_marcas": ["perfumerias juleriaque", "dd2 regalos", "sephora", "elena difusion", "tienda oficial loreal",
                      "natura", "rouge"],
    
    "otros": []  # Categoría por defecto
}

# Función para inicializar la base de datos (sin cambios)
def init_db():
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keywords_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        category TEXT NOT NULL,
        capture_date DATE NOT NULL,
        capture_time TIME NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keyword_rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        count INTEGER NOT NULL,
        last_date DATE NOT NULL,
        last_time TIME NOT NULL
    )
    ''')
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

# Función para categorizar una keyword (sin cambios)
def categorize_keyword(keyword):
    keyword_lower = keyword.lower()
    for category, keywords in categories.items():
        for key in keywords:
            if key in keyword_lower:
                return category
    return "otros"

# Función para capturar y guardar datos (MODIFICADA)
def capture_and_save_data():
    # 1. Leer datos desde un archivo JSON en la carpeta /trend
    try:
        with open('trend/data.json', 'r', encoding='utf-8') as f:
            selected_data = json.load(f)
    except FileNotFoundError:
        raise Exception("El archivo 'trend/data.json' no se encontró")
    except json.JSONDecodeError:
        raise Exception("Error al decodificar el archivo JSON")

    # 3 y 5. Usar una fecha específica (por ahora fija, con today como comentario para futuro)
    current_date = "2025-04-02"  # Fecha específica que tú indiques
    # Para futuro: current_date = datetime.now().strftime("%Y-%m-%d")  # Usar fecha de hoy
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # 2 y 4. Quitamos el random.shuffle y la selección aleatoria de fechas
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

# Todos los endpoints siguientes quedan INTACTOS
@app.get("/")
def read_root():
    return {"message": "API de Análisis de Tendencias de Mercado Libre"}

@app.post("/update-trends")
def update_trends(background_tasks: BackgroundTasks):
    try:
        result = capture_and_save_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar tendencias: {str(e)}")

@app.get("/top-keywords")
def get_top_keywords(limit: int = 10):
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
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT keyword 
        FROM keyword_rankings 
        ORDER BY count DESC, last_date DESC, last_time DESC 
        LIMIT ?
    """, (top_keywords,))
    top_keywords_list = [row[0] for row in cursor.fetchall()]
    result = []
    for keyword in top_keywords_list:
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

@app.get("/top-keywords-list")
def get_top_keywords_list(limit: int = 20):
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
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT capture_date, capture_time
        FROM keywords_data
        ORDER BY capture_date DESC, capture_time DESC
        LIMIT ?
    """, (limit_captures,))
    capture_times = cursor.fetchall()
    result = []
    for capture_date, capture_time in capture_times:
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

@app.get("/prophet-forecast")
def get_prophet_forecast(keyword: str = None, forecast_days: int = 7):
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    if not keyword:
        cursor.execute("""
            SELECT keyword 
            FROM keyword_rankings 
            ORDER BY count DESC 
            LIMIT 1
        """)
        keyword = cursor.fetchone()[0]
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
    data = cursor.fetchall()
    conn.close()
    if len(data) < 2:
        return {
            "status": "error",
            "message": f"No hay suficientes datos históricos para '{keyword}' (mínimo 2 días)"
        }
    df = pd.DataFrame(data, columns=['ds', 'y'])
    df['ds'] = pd.to_datetime(df['ds'])
    model = Prophet(daily_seasonality=True, yearly_seasonality=False, weekly_seasonality=False)
    model.fit(df)
    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)
    forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_days).to_dict(orient='records')
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

@app.get("/category-flow")
def get_category_flow():
    conn = sqlite3.connect('trends.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT keyword, capture_date 
        FROM keywords_data 
        ORDER BY capture_date
    """)
    data = cursor.fetchall()
    conn.close()
    if not data:
        return {"status": "error", "message": "No hay datos para generar el flujo"}
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
    return {
        "status": "not_implemented",
        "message": "El análisis contextual con IA será implementado en futuras versiones"
    }

@app.on_event("startup")
def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)