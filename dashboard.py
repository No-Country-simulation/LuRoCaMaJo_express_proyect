import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import json

# Configuración de la página
st.set_page_config(
    page_title="BeautyTrends - Análisis Predictivo de Tendencias",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #ff4b8d;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
    }
    .metric-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .prediction-card {
        background-color: #fff8fa;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #ff4b8d;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Función para cargar datos simulados (en producción conectaríamos con la API)
@st.cache_data
def load_sample_data():
    # Generamos datos de muestra para el prototipo
    today = datetime.now()
    dates = [(today - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(90, 0, -1)]
    
    categories = ["skincare", "makeup", "haircare", "fragrance", "nailcare"]
    platforms = ["tiktok", "instagram", "youtube"]
    
    data = []
    
    for date in dates:
        for category in categories:
            base_trend = np.random.randint(30, 70)
            
            # Añadimos tendencias simuladas
            if category == "skincare":
                trend_factor = 1.2 + 0.005 * dates.index(date)  # Skincare creciendo
            elif category == "makeup":
                trend_factor = 1.0 + 0.002 * dates.index(date)  # Makeup estable con ligero crecimiento
            elif category == "nailcare":
                trend_factor = 1.5 - 0.007 * dates.index(date)  # Nailcare decreciendo
            else:
                trend_factor = 1.0
                
            for platform in platforms:
                platform_factor = 1.2 if platform == "tiktok" else 1.0  # TikTok más relevante
                
                trend_score = base_trend * trend_factor * platform_factor
                trend_score = min(100, max(0, trend_score + np.random.uniform(-5, 5)))
                
                mentions = int(np.random.randint(500, 5000) * trend_factor * platform_factor)
                engagement = np.random.uniform(0.01, 0.20) * trend_factor
                
                data.append({
                    "date": date,
                    "category": category,
                    "platform": platform,
                    "trend_score": trend_score,
                    "mentions": mentions,
                    "engagement_rate": engagement,
                    "search_volume": int(mentions * np.random.uniform(0.8, 1.2))
                })
    
    return pd.DataFrame(data)

# Funciones de conexión a la API (simuladas para el prototipo)
def get_top_trending(category=None, limit=10):
    """Obtiene las tendencias principales desde la API"""
    # En producción, aquí haríamos una llamada real a la API
    # Para el prototipo, devolvemos datos simulados
    
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
        },
        {
            "keyword": "rizador de pestañas con calor",
            "growth_rate": 78.9,
            "category": "makeup",
            "mentions": 35672,
            "top_regions": ["México", "Argentina", "España"]
        },
        {
            "keyword": "aceite de ricino pestañas",
            "growth_rate": 73.2,
            "category": "haircare",
            "mentions": 31245,
            "top_regions": ["Colombia", "Chile", "México"]
        }
    ]
    
    if category:
        trends = [t for t in trends if t["category"] == category]
    
    return trends[:limit]

def predict_trend(category, platform, horizon=30):
    """Realiza una predicción de tendencia a través de la API"""
    # En producción, aquí haríamos una llamada real a la API
    # Para el prototipo, devolvemos datos simulados
    
    trend_values = {
        "skincare": 85.7,
        "makeup": 72.3,
        "haircare": 65.8,
        "fragrance": 58.2,
        "nailcare": 45.6
    }
    
    # Añadimos algo de variabilidad según la plataforma
    platform_multiplier = {
        "tiktok": 1.1,
        "instagram": 1.0,
        "youtube": 0.9
    }
    
    base_score = trend_values.get(category, 50)
    trend_score = base_score * platform_multiplier.get(platform, 1.0)
    trend_score = min(100, max(0, trend_score))
    
    # Generamos una respuesta similar a la que daría nuestra API
    now = datetime.now()
    valid_until = now + timedelta(days=horizon)
    
    prediction = {
        "product_category": category,
        "trend_score": round(trend_score, 2),
        "confidence": 85.5,
        "predicted_at": now.isoformat(),
        "valid_until": valid_until.isoformat()
    }
    
    # Generar recomendación basada en el puntaje
    if trend_score > 75:
        recommendation = f"La categoría {category} muestra un fuerte potencial de crecimiento. Recomendamos aumentar inventario y presupuesto publicitario."
    elif trend_score > 50:
        recommendation = f"La categoría {category} muestra un potencial moderado. Mantener estrategia actual con monitoreo cercano."
    else:
        recommendation = f"La categoría {category} muestra señales de declive. Considerar reducir inventario y diversificar oferta."
    
    return {
        "predictions": [prediction],
        "recommendation": recommendation
    }

# Cargar datos
df = load_sample_data()

# Sidebar para filtros
st.sidebar.image("https://res.cloudinary.com/dloaaxni6/image/upload/v1743649127/image_5_yogy8f.jpg", width=150)
st.sidebar.markdown("### Filtros")

selected_category = st.sidebar.selectbox(
    "Categoría de Producto", 
    ["Todos"] + sorted(df["category"].unique().tolist()),
    format_func=lambda x: x.capitalize() if x != "Todos" else x
)

selected_platform = st.sidebar.selectbox(
    "Plataforma", 
    ["Todas"] + sorted(df["platform"].unique().tolist()),
    format_func=lambda x: x.capitalize() if x != "Todas" else x
)

date_range = st.sidebar.slider(
    "Período de Análisis (días)",
    min_value=7,
    max_value=90,
    value=30
)

# Filtrar datos según selecciones
filtered_df = df.copy()
if selected_category != "Todos":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]
if selected_platform != "Todas":
    filtered_df = filtered_df[filtered_df["platform"] == selected_platform]

# Limitar a rango de fechas seleccionado
filtered_df = filtered_df.sort_values("date").iloc[-date_range:]

# Panel principal
st.markdown("<h1 class='main-header'>Dashboard de Tendencias en Belleza</h1>", unsafe_allow_html=True)

# Métricas principales
col1, col2, col3, col4 = st.columns(4)

# Calcular métricas generales
avg_trend_score = filtered_df["trend_score"].mean()
total_mentions = filtered_df["mentions"].sum()
avg_engagement = filtered_df["engagement_rate"].mean() * 100
total_search = filtered_df["search_volume"].sum()

with col1:
    st.metric("Puntuación Media", f"{avg_trend_score:.1f}")
with col2:
    st.metric("Total Menciones", f"{total_mentions:,}")
with col3:
    st.metric("Engagement Medio", f"{avg_engagement:.1f}%")
with col4:
    st.metric("Volumen de Búsqueda", f"{total_search:,}")

# Gráficos de tendencias
st.markdown("<h2 class='sub-header'>Evolución de Tendencias</h2>", unsafe_allow_html=True)

# Gráfico de evolución temporal
pivot_df = filtered_df.pivot_table(
    index="date", 
    columns="category" if selected_category == "Todos" else "platform",
    values="trend_score",
    aggfunc="mean"
).reset_index()

fig = px.line(
    pivot_df, 
    x="date", 
    y=pivot_df.columns[1:],
    title="Evolución del Índice de Tendencia",
    labels={"value": "Índice de Tendencia", "date": "Fecha", "variable": "Categoría" if selected_category == "Todos" else "Plataforma"},
    color_discrete_sequence=px.colors.qualitative.Bold
)

fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Índice de Tendencia (0-100)",
    legend_title="Categoría" if selected_category == "Todos" else "Plataforma",
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# Gráficos secundarios en 2 columnas
col1, col2 = st.columns(2)

with col1:
    # Gráfico de menciones por categoría/plataforma
    group_by = "category" if selected_category == "Todos" else "platform" if selected_platform == "Todas" else "date"
    mentions_df = filtered_df.groupby(group_by)["mentions"].sum().reset_index().sort_values("mentions", ascending=False)
    
    fig = px.bar(
        mentions_df, 
        x=group_by, 
        y="mentions",
        title="Total de Menciones",
        labels={"mentions": "Número de Menciones"},
        color_discrete_sequence=[px.colors.qualitative.Bold[0]]
    )
    
    fig.update_layout(
        xaxis_title="Categoría" if group_by == "category" else "Plataforma" if group_by == "platform" else "Fecha",
        yaxis_title="Menciones",
        height=350
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Gráfico de engagement por categoría/plataforma
    engagement_df = filtered_df.groupby(group_by)["engagement_rate"].mean().reset_index().sort_values("engagement_rate", ascending=False)
    engagement_df["engagement_rate"] = engagement_df["engagement_rate"] * 100  # Convertir a porcentaje
    
    fig = px.bar(
        engagement_df, 
        x=group_by, 
        y="engagement_rate",
        title="Tasa de Engagement Medio",
        labels={"engagement_rate": "Engagement (%)"},
        color_discrete_sequence=[px.colors.qualitative.Bold[1]]
    )
    
    fig.update_layout(
        xaxis_title="Categoría" if group_by == "category" else "Plataforma" if group_by == "platform" else "Fecha",
        yaxis_title="Tasa de Engagement (%)",
        height=350
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Sección de tendencias principales
st.markdown("<h2 class='sub-header'>Tendencias Destacadas</h2>", unsafe_allow_html=True)

top_trends = get_top_trending(
    category=None if selected_category == "Todos" else selected_category,
    limit=5
)

## Mostrar las tendencias principales en una tabla
trends_df = pd.DataFrame(top_trends)
if not trends_df.empty:
    # Convertir la lista de regiones a string para mostrar en la tabla
    trends_df['top_regions'] = trends_df['top_regions'].apply(lambda x: ', '.join(x))
    
    # Aplicar formato a las columnas numéricas
    trends_df['growth_rate'] = trends_df['growth_rate'].apply(lambda x: f"{x:.1f}%")
    trends_df['mentions'] = trends_df['mentions'].apply(lambda x: f"{x:,}")
    
    # Renombrar columnas para mejor presentación
    trends_df = trends_df.rename(columns={
        'keyword': 'Palabra Clave',
        'growth_rate': 'Tasa de Crecimiento',
        'category': 'Categoría',
        'mentions': 'Menciones',
        'top_regions': 'Regiones Principales'
    })
    
    st.dataframe(trends_df, use_container_width=True)
else:
    st.info("No hay tendencias disponibles para los filtros seleccionados.")

# Sección de predicción de tendencias
st.markdown("<h2 class='sub-header'>Predicción de Tendencias</h2>", unsafe_allow_html=True)

# Formulario para la predicción
with st.form("prediction_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pred_category = st.selectbox(
            "Categoría de Producto",
            options=sorted(df["category"].unique().tolist()),
            format_func=lambda x: x.capitalize()
        )
    
    with col2:
        pred_platform = st.selectbox(
            "Plataforma",
            options=sorted(df["platform"].unique().tolist()),
            format_func=lambda x: x.capitalize()
        )
    
    with col3:
        pred_horizon = st.slider(
            "Horizonte de Predicción (días)",
            min_value=7,
            max_value=90,
            value=30
        )
    
    predict_button = st.form_submit_button("Predecir Tendencia")

# Mostrar resultados de predicción si se hace clic en el botón
if predict_button:
    with st.spinner("Realizando predicción..."):
        prediction_result = predict_trend(pred_category, pred_platform, pred_horizon)
        
        # Extraer datos de la predicción
        prediction = prediction_result["predictions"][0]
        recommendation = prediction_result["recommendation"]
        
        # Mostrar resultados en una tarjeta estilizada
        st.markdown("<div class='prediction-card'>", unsafe_allow_html=True)
        
        # Título y puntuación
        st.subheader(f"Predicción para {pred_category.capitalize()} en {pred_platform.capitalize()}")
        
        # Visualizar puntuación como un medidor
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prediction["trend_score"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Índice de Tendencia"},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "#FF4B8D"},
                'steps': [
                    {'range': [0, 33], 'color': "#FFECF2"},
                    {'range': [33, 66], 'color': "#FFCFE0"},
                    {'range': [66, 100], 'color': "#FFADD0"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        
        fig.update_layout(height=250)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Información adicional
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Confianza", f"{prediction['confidence']}%")
            st.text(f"Predicción realizada: {prediction['predicted_at'][:10]}")
        
        with col2:
            # Determinar el color según el puntaje
            if prediction["trend_score"] > 75:
                icon = "🚀"
                status = "En ascenso"
            elif prediction["trend_score"] > 50:
                icon = "📈"
                status = "Estable con potencial"
            else:
                icon = "📉"
                status = "En declive"
                
            st.metric("Estado", f"{icon} {status}")
            st.text(f"Válido hasta: {prediction['valid_until'][:10]}")
        
        # Recomendación
        st.markdown("### Recomendación")
        st.info(recommendation)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Sección de análisis comparativo
st.markdown("<h2 class='sub-header'>Análisis Comparativo</h2>", unsafe_allow_html=True)

# Comparativa entre plataformas si hay una categoría seleccionada
if selected_category != "Todos":
    platform_comp = df[df["category"] == selected_category].groupby("platform")[["trend_score", "mentions", "engagement_rate"]].mean().reset_index()
    platform_comp["engagement_rate"] = platform_comp["engagement_rate"] * 100  # Convertir a porcentaje
    
    # Gráfico de radar para comparar plataformas
    fig = go.Figure()
    
    for i, platform in enumerate(platform_comp["platform"]):
        fig.add_trace(go.Scatterpolar(
            r=[
                platform_comp.loc[i, "trend_score"],
                platform_comp.loc[i, "engagement_rate"] * 5,  # Escalamos para visualización
                platform_comp.loc[i, "mentions"] / 1000  # Escalamos para visualización
            ],
            theta=["Índice de Tendencia", "Engagement", "Menciones"],
            fill='toself',
            name=platform.capitalize()
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
            )
        ),
        title="Comparativa entre Plataformas",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Análisis histórico
st.markdown("<h2 class='sub-header'>Análisis Histórico</h2>", unsafe_allow_html=True)

# Mostrar un gráfico de calor mensual
# Primero preparamos los datos
df['month'] = pd.to_datetime(df['date']).dt.month_name()
df['month_num'] = pd.to_datetime(df['date']).dt.month
df['year_month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')

# Filtramos según las selecciones
heat_df = df.copy()
if selected_category != "Todos":
    heat_df = heat_df[heat_df["category"] == selected_category]
if selected_platform != "Todas":
    heat_df = heat_df[heat_df["platform"] == selected_platform]

# Creamos el heatmap por categoría y mes
heatmap_data = heat_df.pivot_table(
    index="category" if selected_category == "Todos" else "platform",
    columns="month",
    values="trend_score",
    aggfunc="mean"
).reindex(columns=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])

# Mostrar el heatmap solo si hay datos
if not heatmap_data.empty and not heatmap_data.isna().all().all():
    fig = px.imshow(
        heatmap_data,
        labels=dict(
            x="Mes", 
            y="Categoría" if selected_category == "Todos" else "Plataforma", 
            color="Índice de Tendencia"
        ),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale="Reds",
        title="Mapa de Calor de Tendencias por Mes"
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Datos insuficientes para generar el mapa de calor.")

# Sección final con notas metodológicas
st.markdown("<h2 class='sub-header'>Notas Metodológicas</h2>", unsafe_allow_html=True)

with st.expander("Ver detalles sobre la metodología"):
    st.markdown("""
    ### Metodología de Análisis de Tendencias
    
    El índice de tendencia se calcula utilizando una combinación de los siguientes factores:
    
    * **Menciones en redes sociales**: Volumen y frecuencia de menciones relacionadas con productos o categorías
    * **Engagement**: Interacciones como likes, comentarios, compartidos, etc.
    * **Búsquedas**: Volumen de búsquedas en motores de búsqueda
    * **Estacionalidad**: Ajustes basados en patrones históricos para cada temporada
    * **Viralidad**: Velocidad de crecimiento de las menciones en un período corto
    
    Los modelos predictivos utilizan algoritmos de aprendizaje automático (Random Forest y Gradient Boosting) 
    entrenados con datos históricos de los últimos 3 años para proyectar tendencias futuras.
    
    **Nivel de confianza**: El nivel de confianza se basa en la estabilidad histórica de la categoría y 
    la cantidad de datos disponibles para el entrenamiento del modelo.
    """)

# Pie de página
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 0.8em;'>
        BeautyTrends Analytics | Dashboard Prototipo | Datos actualizados: {}
    </div>
    """.format(datetime.now().strftime("%d-%m-%Y")),
    unsafe_allow_html=True
)
