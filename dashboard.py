import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Tendencias - Mercado Libre",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Funciones para llamadas a la API
def get_api_url():
    return st.session_state.get("api_url", "http://localhost:8000")

def call_api(endpoint, method="GET", params=None):
    url = f"{get_api_url()}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al comunicarse con la API: {str(e)}")
        return {"error": str(e)}

def update_trends():
    with st.spinner("Actualizando tendencias..."):
        result = call_api("/update-trends", method="POST")
        if "error" not in result:
            st.success("¡Tendencias actualizadas correctamente!")
            for key in list(st.session_state.keys()):
                if key.startswith("data_"):
                    del st.session_state[key]
        else:
            st.error("Error al actualizar tendencias")
        time.sleep(1)

def get_top_keywords(limit=10, force_reload=False):
    cache_key = f"data_top_keywords_{limit}"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando top keywords..."):
            data = call_api("/top-keywords", params={"limit": limit})
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return []
    return st.session_state[cache_key]

def get_category_distribution(force_reload=False):
    cache_key = "data_category_distribution"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando distribución por categorías..."):
            data = call_api("/category-distribution")
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return []
    return st.session_state[cache_key]

def get_trend_evolution(force_reload=False):
    cache_key = "data_trend_evolution"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando evolución de tendencias..."):
            data = call_api("/trend-evolution")
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return []
    return st.session_state[cache_key]

def get_top_keywords_list(force_reload=False):
    cache_key = "data_top_keywords_list"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando lista de palabras clave..."):
            data = call_api("/top-keywords-list")
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return []
    return st.session_state[cache_key]

def get_most_searched_keyword(force_reload=False):
    cache_key = "data_most_searched"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando palabra más buscada..."):
            data = call_api("/most-searched-keyword")
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return {"keyword": "N/A", "count": 0}
    return st.session_state[cache_key]

def get_capture_history(force_reload=False):
    cache_key = "data_capture_history"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando historial de capturas..."):
            data = call_api("/capture-history", params={"limit_captures": 10})
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return []
    return st.session_state[cache_key]

# Funciones para visualizaciones
def render_top_keywords_chart(data):
    if not data:
        st.warning("No hay datos disponibles para mostrar")
        return
    df = pd.DataFrame(data)
    fig = px.bar(df, x='keyword', y='count', title='Top 10 Palabras Clave',
                 labels={'keyword': 'Palabra Clave', 'count': 'Número de Búsquedas'},
                 color='count', color_continuous_scale='Blues')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def render_category_distribution(data):
    if not data:
        st.warning("No hay datos disponibles para mostrar")
        return
    df = pd.DataFrame(data)
    fig = px.pie(df, values='count', names='category', title='Distribución por Categorías',
                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

def render_trend_evolution(data):
    if not data:
        st.warning("No hay datos disponibles para mostrar")
        return
    df = pd.DataFrame(data)
    if not all(col in df.columns for col in ['date', 'count', 'keyword']):
        st.error("Formato de datos incorrecto para la evolución de tendencias")
        return
    df['date'] = pd.to_datetime(df['date'])
    fig = px.line(df, x='date', y='count', color='keyword',
                  title='Evolución de Tendencias (Top 5 Keywords)',
                  labels={'date': 'Fecha', 'count': 'Búsquedas', 'keyword': 'Palabra Clave'})
    fig.update_layout(xaxis_title='Fecha', yaxis_title='Número de Búsquedas')
    st.plotly_chart(fig, use_container_width=True)

def render_keywords_table(data):
    if not data:
        st.warning("No hay datos disponibles para mostrar. Intenta actualizar las tendencias.")
        return
    df = pd.DataFrame(data)
    df.columns = ['Palabra Clave', 'Repeticiones']
    df['Repeticiones'] = df['Repeticiones'].astype(int)
    st.dataframe(
        df, use_container_width=True,
        column_config={
            "Palabra Clave": st.column_config.TextColumn("Palabra Clave", help="Palabras clave más buscadas en Mercado Libre"),
            "Repeticiones": st.column_config.ProgressColumn("Repeticiones", help="Número de veces que se buscó esta palabra", format="%d", min_value=0, max_value=int(df["Repeticiones"].max())),
        },
        hide_index=True
    )
    st.write(f"**Mostrando {len(df)} de un total de {len(data)} palabras clave**")

def render_capture_history(data):
    if not data:
        st.warning("No hay capturas registradas")
        return
    
    for capture in data:
        timestamp = pd.to_datetime(f"{capture['date']} {capture['time']}").strftime('%d/%m/%Y %H:%M:%S')
        with st.expander(f"Captura del {timestamp} ({len(capture['keywords'])} palabras)"):
            # Mostrar las palabras clave en una lista o tabla simple
            df = pd.DataFrame(capture['keywords'], columns=["Palabra Clave"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
# ... (importaciones y funciones previas sin cambios, incluyendo render_keywords_table y render_capture_history) ...

def get_prophet_forecast(keyword=None, force_reload=False):
    cache_key = f"data_prophet_forecast_{keyword or 'default'}"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando predicción de tendencias..."):
            params = {"keyword": keyword} if keyword else {}
            data = call_api("/prophet-forecast", params=params)
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return {"status": "error", "message": data.get("message", "Error desconocido")}
    return st.session_state[cache_key]

def get_prophet_forecast_compare(keywords=None, force_reload=False):
    cache_key = f"data_prophet_forecast_compare_{keywords or 'default'}"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando comparación de tendencias..."):
            params = {"keywords": keywords} if keywords else {}
            data = call_api("/prophet-forecast-compare", params=params)
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return {"status": "error", "message": data.get("message", "Error desconocido")}
    return st.session_state[cache_key]

def render_prophet_forecast(data):
    if data.get("status") == "error":
        st.warning(data.get("message", "No se pudo cargar la predicción"))
        return
    
    # Datos históricos
    historical_df = pd.DataFrame(data["historical_data"])
    historical_df['ds'] = pd.to_datetime(historical_df['ds'])
    
    # Datos predichos
    forecast_df = pd.DataFrame(data["forecast_data"])
    forecast_df['date'] = pd.to_datetime(forecast_df['date'])
    
    # Crear gráfico con Plotly
    fig = go.Figure()
    
    # Línea histórica
    fig.add_trace(go.Scatter(
        x=historical_df['ds'], y=historical_df['y'],
        mode='lines+markers', name='Histórico',
        line=dict(color='blue')
    ))
    
    # Línea predicha
    fig.add_trace(go.Scatter(
        x=forecast_df['date'], y=forecast_df['predicted_count'],
        mode='lines+markers', name='Predicción',
        line=dict(color='orange', dash='dash')
    ))
    
    # Intervalo de confianza
    fig.add_trace(go.Scatter(
        x=forecast_df['date'].tolist() + forecast_df['date'].tolist()[::-1],
        y=forecast_df['upper_bound'].tolist() + forecast_df['lower_bound'].tolist()[::-1],
        fill='toself', fillcolor='rgba(255, 153, 0, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Intervalo de confianza',
        showlegend=True
    ))
    
    fig.update_layout(
        title=f"Predicción de Tendencias para '{data['keyword']}'",
        xaxis_title="Fecha",
        yaxis_title="Número de Búsquedas",
        legend=dict(x=0, y=1.1, orientation="h")
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_prophet_comparison(data):
    if data.get("status") == "error":
        st.warning(data.get("message", "No se pudo cargar la predicción"))
        return
    
    fig = go.Figure()
    
    for keyword, forecast_info in data["forecasts"].items():
        if forecast_info.get("status") == "error":
            st.warning(f"{keyword}: {forecast_info['message']}")
            continue
        
        historical_df = pd.DataFrame(forecast_info["historical_data"])
        historical_df['ds'] = pd.to_datetime(historical_df['ds'])
        
        forecast_df = pd.DataFrame(forecast_info["forecast_data"])
        forecast_df['date'] = pd.to_datetime(forecast_df['date'])
        
        fig.add_trace(go.Scatter(
            x=historical_df['ds'], y=historical_df['y'],
            mode='lines+markers', name=f"{keyword} (Histórico)",
            line=dict(width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_df['date'], y=forecast_df['predicted_count'],
            mode='lines+markers', name=f"{keyword} (Predicción)",
            line=dict(dash='dash', width=2)
        ))
    
    fig.update_layout(
        title="Comparación de Predicciones de Tendencias",
        xaxis_title="Fecha",
        yaxis_title="Número de Búsquedas",
        legend=dict(x=0, y=1.1, orientation="h")
    )
    
    st.plotly_chart(fig, use_container_width=True)

def download_forecast_data(data):
    if data.get("status") == "error":
        st.warning("No hay datos válidos para descargar.")
        return
    
    # Combinar datos históricos y predichos
    historical_df = pd.DataFrame(data["historical_data"])
    forecast_df = pd.DataFrame(data["forecast_data"])
    combined_df = pd.concat([
        historical_df.rename(columns={"ds": "Fecha", "y": "Conteo"}),
        forecast_df.rename(columns={"date": "Fecha", "predicted_count": "Conteo Predicho"})
    ])
    
    # Usar punto y coma como separador
    csv = combined_df.to_csv(index=False, sep=";")
    
    st.download_button(
        label="▼ Descargar Datos (CSV)",
        data=csv,
        file_name=f"prediccion_{data['keyword']}.csv",
        mime="text/csv",
        key="download_forecast"
    )

def download_comparison_data(data):
    if data.get("status") == "error":
        st.warning("No hay datos válidos para descargar.")
        return
    
    # Combinar datos de todas las palabras clave
    all_dfs = []
    for keyword, forecast_info in data["forecasts"].items():
        if forecast_info.get("status") == "error":
            continue
        historical_df = pd.DataFrame(forecast_info["historical_data"])
        forecast_df = pd.DataFrame(forecast_info["forecast_data"])
        combined_df = pd.concat([
            historical_df.rename(columns={"ds": "Fecha", "y": "Conteo"}),
            forecast_df.rename(columns={"date": "Fecha", "predicted_count": "Conteo Predicho"})
        ])
        combined_df["Palabra Clave"] = keyword
        all_dfs.append(combined_df)
    
    if not all_dfs:
        st.warning("No hay datos válidos para descargar.")
        return
    
    final_df = pd.concat(all_dfs)
    csv = combined_df.to_csv(index=False, sep=";")
    
    st.download_button(
        label="▼  Descargar Comparación (CSV)",
        data=csv,
        file_name="comparacion_predicciones.csv",
        mime="text/csv",
        key="download_comparison"
    )

def clear_forecast_cache():
    import time
    keys_to_clear = [key for key in st.session_state.keys() if key.startswith("data_prophet_forecast")]
    for key in keys_to_clear:
        del st.session_state[key]
    placeholder = st.empty()
    with placeholder:
        st.markdown(
            '<div style="display: inline-block; padding: 10px; background-color: #00cc00; color: white; border-radius: 5px;">Caché de predicciones borrada.</div>',
            unsafe_allow_html=True
        )
    time.sleep(2)
    placeholder.empty()

def get_category_flow(force_reload=False):
    cache_key = "data_category_flow"
    if cache_key not in st.session_state or force_reload:
        with st.spinner("Cargando flujo de categorías..."):
            data = call_api("/category-flow")
            if "error" not in data:
                st.session_state[cache_key] = data
            else:
                return {"status": "error", "message": data.get("message", "Error desconocido")}
    return st.session_state[cache_key]

# MMMMMMMMMMMMMMMMMAAAAAAAAAAAAAAAAAAAAAAIIIIIIIIIIIIIIINNNNNNNNNNNN

def main():
    if "api_url" not in st.session_state:
        st.session_state["api_url"] = "http://localhost:8000"
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

    # CSS para botones y pestañas
# En el bloque st.markdown del CSS, reemplaza todo el <style> con esto:
    st.markdown("""
        <style>
        button[kind="secondary"] {
            background-color: #D3D3D3;
            color: #333333;
            border: none;
        }
        button[kind="secondary"]:hover {
            background-color: #B0B0B0;
        }
        button[kind="secondary"]:active {
            color: #FFFFFF !important;
        }
        div[data-testid="stTabs"] button {
            background-color: #D3D3D3;
            color: #333333;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
        }
        div[data-testid="stTabs"] button:hover {
            background-color: #B0B0B0;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            background-color: #B0B0B0;
            color: #FFFFFF;
        }
        /* Estilo para opciones seleccionadas en multiselect */
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
            background-color: #FFFFFF;
            color: #333333;  /* Texto gris oscuro para legibilidad */
            border: none;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.title("Configuración")
        dark_mode = st.checkbox("Modo Nocturno", value=st.session_state["dark_mode"])
        if dark_mode != st.session_state["dark_mode"]:
            st.session_state["dark_mode"] = dark_mode
            st.rerun()
        st.subheader("Conexión API")
        api_url = st.text_input("URL de la API", value=st.session_state["api_url"])
        if st.button("Guardar URL"):
            st.session_state["api_url"] = api_url
            st.success(f"URL actualizada: {api_url}")
        st.subheader("Información")
        st.info("Dashboard para análisis de tendencias en Mercado Libre")
        st.write("Desarrollado con Streamlit")

    # Título y actualización
    st.title("📊 Dashboard de Tendencias - Mercado Libre")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("↻ Actualizar Tendencias", use_container_width=True):
            update_trends()
    with col2:
        st.write("Última actualización:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    if st.button("🗑️ Limpiar Caché de Predicciones", key="clear_forecast_cache"):
        clear_forecast_cache()

    # Datos
    most_searched = get_most_searched_keyword()
    top_keywords = get_top_keywords(limit=10)
    top5_keywords = get_top_keywords(limit=5)

    # Métricas destacadas
    st.subheader("Métricas Destacadas")
    if not most_searched.get("keyword") or most_searched.get("count", 0) == 0:
        st.info("No hay datos suficientes. Actualiza las tendencias.")
    else:
        st.metric(
            label="Palabra Más Buscada",
            value=f"{most_searched.get('keyword', 'N/A')} - {most_searched.get('count', 0):,} búsquedas",
            help="Palabra clave con más búsquedas"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        top_cols = st.columns(4)
        for i, kw in enumerate(top5_keywords[1:5]):
            with top_cols[i]:
                st.metric(label=f"Top {i+2}", value=kw.get("keyword", ""), delta=f"{kw.get('count', 0):,} búsquedas")

    # Espacio antes de visualizaciones
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Visualizaciones
    st.subheader("Visualizaciones")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↻ Actualizar Top Keywords", key="refresh_top_keywords"):
            render_top_keywords_chart(get_top_keywords(limit=10, force_reload=True))
        else:
            render_top_keywords_chart(top_keywords)
    with col2:
        if st.button("↻ Actualizar Distribución", key="refresh_category"):
            render_category_distribution(get_category_distribution(force_reload=True))
        else:
            render_category_distribution(get_category_distribution())

    # Evolución y tabla
    st.subheader("Evolución de Tendencias")
    if st.button("↻ Actualizar Evolución", key="refresh_trend_evolution"):
        render_trend_evolution(get_trend_evolution(force_reload=True))
    else:
        render_trend_evolution(get_trend_evolution())

    st.subheader("Top 20 Palabras Clave")
    if st.button("↻ Actualizar Tabla", key="refresh_keywords_table"):
        render_keywords_table(get_top_keywords_list(force_reload=True))
    else:
        render_keywords_table(get_top_keywords_list())

    # Predicción individual
    st.subheader("Predicción de Tendencias (Prophet)")
    keyword_options = [kw["keyword"] for kw in top5_keywords]
    selected_keyword = st.selectbox("Selecciona una palabra clave", keyword_options)
    if st.button("↻ Actualizar Predicción", key="refresh_prophet_forecast"):
        data = get_prophet_forecast(keyword=selected_keyword, force_reload=True)
        render_prophet_forecast(data)
        download_forecast_data(data)
    else:
        data = get_prophet_forecast(keyword=selected_keyword)
        render_prophet_forecast(data)
        download_forecast_data(data)

    # Comparación de predicciones
    st.subheader("Comparación de Predicciones")
    selected_keywords = st.multiselect("Selecciona palabras clave para comparar", keyword_options, default=keyword_options[:2])
    if selected_keywords:
        keywords_str = ",".join(selected_keywords)
        if st.button("↻ Actualizar Comparación", key="refresh_prophet_comparison"):
            data = get_prophet_forecast_compare(keywords=keywords_str, force_reload=True)
            render_prophet_comparison(data)
            download_comparison_data(data)
        else:
            data = get_prophet_forecast_compare(keywords=keywords_str)
            render_prophet_comparison(data)
            download_comparison_data(data)
    else:
        st.info("Selecciona al menos una palabra clave para comparar.")
    # grafico de Staclerrr
    st.header("Flujo entre categorías - Gráfico de Sankey")

    # Botón para limpiar y recargar
    if st.button("↻  Recargar flujo de categorías"):
        data = get_category_flow(force_reload=True)
    else:
        data = get_category_flow()

    if data["status"] == "success":
        nodes = data["nodes"]
        links = data["links"]

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=nodes,
                color="lightblue"
            ),
            link=dict(
                source=links["source"],
                target=links["target"],
                value=links["value"]
            )
        )])

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"⊗ {data['message']}")

    # Historial
    st.subheader("Historial de Capturas")
    if st.button("↻ Actualizar Historial", key="refresh_capture_history"):
        data = get_capture_history(force_reload=True)
    else:
        data = get_capture_history()
    if data:
        tab_names = []
        for c in data:
            timestamp = pd.to_datetime(f"{c['date']} {c['time']}").strftime('%d/%m/%Y %H:%M:%S')
            tab_names.append(f"↻ Captura del {timestamp}")
        tabs = st.tabs(tab_names)
        for tab, capture in zip(tabs, data):
            with tab:
                df = pd.DataFrame(capture['keywords'], columns=["Palabra Clave"])
                st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay capturas registradas")

    st.divider()
    st.caption(f"Dashboard de Tendencias de Mercado Libre © 2025 | Última captura: {get_capture_history()[0]['date'] if get_capture_history() else 'N/A'}")

if __name__ == "__main__":
    main()