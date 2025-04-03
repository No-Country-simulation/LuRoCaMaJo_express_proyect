from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import joblib
import os
from datetime import datetime, timedelta

# Importar el predictor
from models.beauty_trend_predictor import BeautyTrendPredictor

app = FastAPI(
    title="Beauty Market Trends API",
    description="API para análisis predictivo de tendencias en el sector belleza",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar el modelo predictivo
predictor = BeautyTrendPredictor()
try:
    predictor.load_model()
    print("Modelo cargado correctamente")
except:
    print("No se encontró modelo guardado. Se creará uno nuevo en la primera solicitud.")

# Modelos de datos
class TrendRequest(BaseModel):
    product_category: str
    platform: str
    time_horizon: int = 30  # Días hacia el futuro para predecir

class TrendPrediction(BaseModel):
    product_category: str
    trend_score: float
    confidence: float
    predicted_at: str
    valid_until: str

class TrendResponse(BaseModel):
    predictions: List[TrendPrediction]
    recommendation: str

# Rutas de la API
@app.get("/")
def read_root():
    return {"status": "online", "message": "Beauty Market Trends API"}

@app.get("/categories")
def get_categories():
    """Retorna las categorías de productos disponibles para análisis"""
    # En un caso real, esto vendría de la base de datos
    categories = [
        {"id": "skincare", "name": "Cuidado de la Piel", "product_count": 1245},
        {"id": "makeup", "name": "Maquillaje", "product_count": 1876},
        {"id": "haircare", "name": "Cuidado del Cabello", "product_count": 945},
        {"id": "fragrance", "name": "Fragancias", "product_count": 512},
        {"id": "nailcare", "name": "Cuidado de Uñas", "product_count": 386}
    ]
    return categories

@app.get("/insights/top-trending")
def get_top_trending(
    category: Optional[str] = Query(None, description="Categoría de producto"),
    limit: int = Query(10, description="Número de tendencias a retornar")
):
    """Retorna las tendencias principales en tiempo real"""
    # Simulamos datos para el prototipo
    # En producción, estos datos vendrían de nuestra base de datos
    
    trends = [
        {
            "keyword": "serum vitamina c",
            "growth_rate": 128.5,
            "category": "skincare",
            "mentions": 45678,
            "top_regions": ["España", "México", "Colombia"]
        },
        {
            "keyword": "mascarilla hidratante overnight",
            "growth_rate": 98.2,
            "category": "skincare",
            "mentions": 38921,
            "top_regions": ["Argentina", "España", "Chile"]
        },
        {
            "keyword": "base matte larga duración",
            "growth_rate": 87.6,
            "category": "makeup",
            "mentions": 42105,
            "top_regions": ["México", "Colombia", "Perú"]
        }
    ]
    
    if category:
        trends = [t for t in trends if t["category"] == category]
    
    return {"trends": trends[:limit]}

@app.post("/predict/trends", response_model=TrendResponse)
def predict_trends(request: TrendRequest):
    """Predice tendencias futuras basadas en los parámetros proporcionados"""
    
    try:
        # En un caso real, aquí consultaríamos los datos actuales desde nuestra BD
        # y prepararíamos las características para el modelo
        
        # Para el prototipo, simulamos datos de entrada
        input_data = pd.DataFrame({
            'product_category': [request.product_category],
            'platform': [request.platform],
            'views_count': [50000],  # Valores simulados
            'engagement_rate': [0.15],
            'search_volume': [25000],
            'mentions_count': [1200],
            'season': [get_current_season()]
        })
        
        # Realizar predicción
        trend_score = float(predictor.predict(input_data)[0])
        
        # Crear respuesta
        now = datetime.now()
        valid_until = now + timedelta(days=request.time_horizon)
        
        prediction = TrendPrediction(
            product_category=request.product_category,
            trend_score=round(trend_score, 2),
            confidence=85.5,  # En un caso real, calcularíamos un intervalo de confianza
            predicted_at=now.isoformat(),
            valid_until=valid_until.isoformat()
        )
        
        # Generar recomendación basada en el puntaje
        if trend_score > 75:
            recommendation = f"La categoría {request.product_category} muestra un fuerte potencial de crecimiento. Recomendamos aumentar inventario y presupuesto publicitario."
        elif trend_score > 50:
            recommendation = f"La categoría {request.product_category} muestra un potencial moderado. Mantener estrategia actual con monitoreo cercano."
        else:
            recommendation = f"La categoría {request.product_category} muestra señales de declive. Considerar reducir inventario y diversificar oferta."
        
        return TrendResponse(
            predictions=[prediction],
            recommendation=recommendation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la predicción: {str(e)}")

def get_current_season():
    """Determina la temporada actual basado en la fecha"""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "fall"
    else:
        return "winter"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
