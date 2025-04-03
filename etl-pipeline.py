import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
import json
import re
from typing import List, Dict, Any, Union, Optional
import logging
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import requests
from pytrends.request import TrendReq
from concurrent.futures import ThreadPoolExecutor
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('beauty_etl')

class BeautyTrendsETL:
    def __init__(self, data_dir='data', output_dir='processed_data'):
        """
        Inicializa el pipeline ETL para datos de tendencias de belleza.
        
        Args:
            data_dir: Directorio donde se encuentran los datos crudos
            output_dir: Directorio donde se guardarán los datos procesados
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Crear directorios si no existen
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Descargar recursos de NLTK si es necesario
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        # Inicializar stop words en español
        self.stop_words = set(stopwords.words('spanish'))
        
        # Añadir palabras específicas del dominio a las stop words
        domain_stops = ['belleza', 'producto', 'productos', 'usar', 'mejor', 'mejores', 'nuevo', 'nueva', 'rt']
        self.stop_words.update(domain_stops)
        
        # Inicializar PyTrends para Google Trends
        self.pytrends = TrendReq(hl='es-ES', tz=360)
        
        # Inicializar categorías de productos de belleza para monitoreo
        self.beauty_categories = [
            'maquillaje', 'skincare', 'cabello', 'uñas', 'fragancias', 
            'cuidado facial', 'cuidado corporal', 'cosmética natural'
        ]
        
        logger.info("Pipeline ETL inicializado correctamente")
    
    def extract_tiktok_data(self, api_key: str, days_back: int = 30) -> pd.DataFrame:
        """
        Extrae datos de tendencias de TikTok API
        
        Args:
            api_key: Clave de API para TikTok
            days_back: Cantidad de días hacia atrás para extraer datos
            
        Returns:
            DataFrame con datos de tendencias de TikTok
        """
        logger.info(f"Iniciando extracción de datos de TikTok de los últimos {days_back} días")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Formatear fechas según requisitos de API TikTok
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        tiktok_data = []
        
        # Iterar por cada categoría de belleza
        for category in self.beauty_categories:
            try:
                # URL ejemplo - ajustar según documentación actual de TikTok API
                url = f"https://api.tiktok.com/v1/insights/hashtag/trending?category=beauty&query={category}&start_date={start_date_str}&end_date={end_date_str}"
                
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Procesar respuesta según estructura actual de TikTok API
                    if 'data' in data and 'hashtags' in data['data']:
                        for hashtag_item in data['data']['hashtags']:
                            tiktok_data.append({
                                'category': category,
                                'hashtag': hashtag_item.get('hashtag_name', ''),
                                'view_count': hashtag_item.get('view_count', 0),
                                'video_count': hashtag_item.get('video_count', 0),
                                'engagement_rate': hashtag_item.get('engagement_rate', 0.0),
                                'date': datetime.now().strftime("%Y-%m-%d"),
                                'source': 'tiktok'
                            })
                    
                    logger.info(f"Extraídos {len(tiktok_data)} registros de TikTok para la categoría {category}")
                else:
                    logger.error(f"Error al extraer datos de TikTok para {category}. Código: {response.status_code}, Mensaje: {response.text}")
                    
                # Pausa para respetar límites de tasa de API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error al procesar datos de TikTok para {category}: {str(e)}")
        
        # Crear DataFrame con los datos recopilados
        if tiktok_data:
            df_tiktok = pd.DataFrame(tiktok_data)
            
            # Guardar datos crudos
            raw_filepath = os.path.join(self.data_dir, f"tiktok_raw_{datetime.now().strftime('%Y%m%d')}.csv")
            df_tiktok.to_csv(raw_filepath, index=False)
            logger.info(f"Datos crudos de TikTok guardados en {raw_filepath}")
            
            return df_tiktok
        else:
            logger.warning("No se obtuvieron datos de TikTok")
            return pd.DataFrame()
    
    def extract_google_trends(self, days_back: int = 90) -> pd.DataFrame:
        """
        Extrae datos de Google Trends para términos relacionados con belleza
        
        Args:
            days_back: Cantidad de días hacia atrás para extraer datos
            
        Returns:
            DataFrame con datos de tendencias de Google
        """
        logger.info(f"Iniciando extracción de datos de Google Trends de los últimos {days_back} días")
        
        # Convertir days_back a formato timeframe para PyTrends
        if days_back <= 7:
            timeframe = 'now 7-d'
        elif days_back <= 30:
            timeframe = 'today 1-m'
        elif days_back <= 90:
            timeframe = 'today 3-m'
        else:
            timeframe = 'today 12-m'
            
        all_trends_data = []
        
        # Extraer tendencias para cada categoría de belleza
        for category in self.beauty_categories:
            try:
                # Configurar la consulta de PyTrends
                self.pytrends.build_payload([f"{category}"], cat=0, timeframe=timeframe, geo='MX', gprop='')
                
                # Obtener datos de interés a lo largo del tiempo
                interest_over_time_df = self.pytrends.interest_over_time()
                
                if not interest_over_time_df.empty:
                    # Reformatear datos
                    interest_over_time_df = interest_over_time_df.reset_index()
                    interest_over_time_df['category'] = category
                    interest_over_time_df['source'] = 'google_trends'
                    
                    # Renombrar columnas
                    interest_over_time_df.rename(columns={category: 'interest_score'}, inplace=True)
                    
                    all_trends_data.append(interest_over_time_df)
                    
                    # Obtener términos relacionados
                    related_queries = self.pytrends.related_queries()
                    
                    if related_queries and category in related_queries:
                        top_queries = related_queries[category]['top']
                        rising_queries = related_queries[category]['rising']
                        
                        # Procesar consultas top si existen
                        if top_queries is not None and not top_queries.empty:
                            top_queries['category'] = category
                            top_queries['type'] = 'top'
                            top_queries['source'] = 'google_trends'
                            top_queries['date'] = datetime.now().strftime("%Y-%m-%d")
                            all_trends_data.append(top_queries)
                        
                        # Procesar consultas rising si existen
                        if rising_queries is not None and not rising_queries.empty:
                            rising_queries['category'] = category
                            rising_queries['type'] = 'rising'
                            rising_queries['source'] = 'google_trends'
                            rising_queries['date'] = datetime.now().strftime("%Y-%m-%d")
                            all_trends_data.append(rising_queries)
                
                # Respetar límites de tasa de Google Trends
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error al procesar datos de Google Trends para {category}: {str(e)}")
        
        # Combinar todos los DataFrames recopilados
        if all_trends_data:
            # Puede que tengamos que manejar diferentes estructuras
            try:
                df_trends = pd.concat(all_trends_data, ignore_index=True)
                
                # Guardar datos crudos
                raw_filepath = os.path.join(self.data_dir, f"google_trends_raw_{datetime.now().strftime('%Y%m%d')}.csv")
                df_trends.to_csv(raw_filepath, index=False)
                logger.info(f"Datos crudos de Google Trends guardados en {raw_filepath}")
                
                return df_trends
            except Exception as e:
                logger.error(f"Error al combinar datos de Google Trends: {str(e)}")
                return pd.DataFrame()
        else:
            logger.warning("No se obtuvieron datos de Google Trends")
            return pd.DataFrame()
    
    def transform_data(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Transforma y limpia los datos según la fuente
        
        Args:
            df: DataFrame con datos crudos
            source: Fuente de los datos ('tiktok', 'google_trends', etc.)
            
        Returns:
            DataFrame con datos transformados
        """
        if df.empty:
            logger.warning(f"DataFrame vacío para transformación de {source}")
            return df
            
        logger.info(f"Iniciando transformación de datos de {source}")
        
        # Copia para evitar modificar el original
        transformed_df = df.copy()
        
        # Transformaciones comunes para todas las fuentes
        if 'date' in transformed_df.columns:
            # Asegurar formato consistente de fecha
            transformed_df['date'] = pd.to_datetime(transformed_df['date'])
        
        # Transformaciones específicas según fuente
        if source == 'tiktok':
            # Convertir columnas numéricas al tipo adecuado
            numeric_cols = ['view_count', 'video_count', 'engagement_rate']
            for col in numeric_cols:
                if col in transformed_df.columns:
                    transformed_df[col] = pd.to_numeric(transformed_df[col], errors='coerce')
            
            # Calcular métricas adicionales
            if 'view_count' in transformed_df.columns and 'video_count' in transformed_df.columns:
                transformed_df['views_per_video'] = transformed_df['view_count'] / transformed_df['video_count'].replace(0, np.nan)
            
            # Extraer términos clave de hashtags
            if 'hashtag' in transformed_df.columns:
                transformed_df['terms'] = transformed_df['hashtag'].apply(self._extract_keywords)
                
        elif source == 'google_trends':
            # Asegurar que interest_score es numérico
            if 'interest_score' in transformed_df.columns:
                transformed_df['interest_score'] = pd.to_numeric(transformed_df['interest_score'], errors='coerce')
            
            # Procesar consultas relacionadas
            if 'query' in transformed_df.columns:
                transformed_df['terms'] = transformed_df['query'].apply(self._extract_keywords)
        
        logger.info(f"Transformación de datos de {source} completada. Filas resultantes: {len(transformed_df)}")
        return transformed_df
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrae palabras clave de un texto eliminando stop words
        
        Args:
            text: Texto del cual extraer palabras clave
            
        Returns:
            Lista de palabras clave
        """
        if not isinstance(text, str) or not text.strip():
            return []
            
        # Tokenizar y limpiar
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = word_tokenize(text)
        
        # Eliminar stop words
        keywords = [token for token in tokens if token not in self.stop_words and len(token) > 2]
        
        return keywords
    
    def analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analiza las tendencias en los datos procesados
        
        Args:
            df: DataFrame con datos procesados
            
        Returns:
            Diccionario con resultados del análisis
        """
        logger.info("Iniciando análisis de tendencias")
        
        results = {}
        
        if df.empty:
            logger.warning("DataFrame vacío para análisis de tendencias")
            return results
            
        try:
            # Agrupar por categoría y calcular métricas
            if 'category' in df.columns:
                category_summary = df.groupby('category').agg({
                    'view_count': 'sum',
                    'video_count': 'sum',
                    'engagement_rate': 'mean'
                }).reset_index()
                
                results['category_summary'] = category_summary.to_dict(orient='records')
            
            # Análisis de términos y keywords
            if 'terms' in df.columns:
                # Aplanar lista de términos
                all_terms = []
                for terms_list in df['terms'].dropna():
                    all_terms.extend(terms_list)
                
                # Contar frecuencia de términos
                term_counts = pd.Series(all_terms).value_counts().head(20)
                results['top_terms'] = term_counts.to_dict()
                
            # Tendencias temporales si hay datos de fecha
            if 'date' in df.columns and 'category' in df.columns:
                if 'interest_score' in df.columns:
                    # Para Google Trends
                    time_trends = df.groupby(['date', 'category'])['interest_score'].mean().reset_index()
                    results['time_trends'] = time_trends.to_dict(orient='records')
                elif 'view_count' in df.columns:
                    # Para TikTok
                    time_trends = df.groupby(['date', 'category'])['view_count'].sum().reset_index()
                    results['time_trends'] = time_trends.to_dict(orient='records')
            
            logger.info("Análisis de tendencias completado")
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis de tendencias: {str(e)}")
            return {"error": str(e)}
    
    def load_data(self, df: pd.DataFrame, name: str) -> str:
        """
        Carga los datos procesados en archivos
        
        Args:
            df: DataFrame con datos procesados
            name: Nombre base para el archivo
            
        Returns:
            Ruta del archivo guardado
        """
        if df.empty:
            logger.warning(f"No hay datos para cargar en {name}")
            return ""
            
        try:
            # Crear nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{name}_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # Guardar como CSV
            df.to_csv(filepath, index=False)
            logger.info(f"Datos guardados exitosamente en {filepath}")
            
            # También guardar como JSON para API
            json_filepath = os.path.join(self.output_dir, f"{name}_{timestamp}.json")
            df.to_json(json_filepath, orient='records', date_format='iso')
            logger.info(f"Datos JSON guardados en {json_filepath}")
            
            return filepath
        except Exception as e:
            logger.error(f"Error al guardar datos {name}: {str(e)}")
            return ""
    
    def run_pipeline(self, tiktok_api_key: str = None) -> Dict[str, Any]:
        """
        Ejecuta el pipeline ETL completo
        
        Args:
            tiktok_api_key: Clave API para TikTok
            
        Returns:
            Diccionario con resultados del pipeline
        """
        logger.info("Iniciando ejecución del pipeline ETL completo")
        results = {}
        
        try:
            # 1. Extracción
            if tiktok_api_key:
                df_tiktok = self.extract_tiktok_data(tiktok_api_key)
                results['extracted_tiktok'] = len(df_tiktok) if not df_tiktok.empty else 0
            else:
                logger.warning("No se proporcionó API key de TikTok, omitiendo extracción")
                df_tiktok = pd.DataFrame()
            
            df_google = self.extract_google_trends()
            results['extracted_google'] = len(df_google) if not df_google.empty else 0
            
            # 2. Transformación
            transformed_tiktok = self.transform_data(df_tiktok, 'tiktok')
            transformed_google = self.transform_data(df_google, 'google_trends')
            
            results['transformed_tiktok'] = len(transformed_tiktok) if not transformed_tiktok.empty else 0
            results['transformed_google'] = len(transformed_google) if not transformed_google.empty else 0
            
            # 3. Análisis
            tiktok_analysis = self.analyze_trends(transformed_tiktok)
            google_analysis = self.analyze_trends(transformed_google)
            
            results['analysis'] = {
                'tiktok': tiktok_analysis,
                'google_trends': google_analysis
            }
            
            # 4. Carga
            if not transformed_tiktok.empty:
                tiktok_path = self.load_data(transformed_tiktok, 'tiktok_trends')
                results['tiktok_data_path'] = tiktok_path
            
            if not transformed_google.empty:
                google_path = self.load_data(transformed_google, 'google_trends')
                results['google_data_path'] = google_path
            
            # 5. Combinar datasets si ambos tienen datos
            if not transformed_tiktok.empty and not transformed_google.empty:
                # Identificar columnas comunes para combinar
                common_cols = ['category', 'date']
                
                # Preparar datasets para combinación
                tiktok_for_merge = transformed_tiktok[['category', 'date', 'view_count']].copy()
                tiktok_for_merge.rename(columns={'view_count': 'tiktok_popularity'}, inplace=True)
                
                google_for_merge = transformed_google[['category', 'date', 'interest_score']].copy()
                google_for_merge.rename(columns={'interest_score': 'google_popularity'}, inplace=True)
                
                # Combinar por categoría y fecha
                combined_df = pd.merge(
                    tiktok_for_merge, 
                    google_for_merge, 
                    on=common_cols, 
                    how='outer'
                )
                
                # Guardar dataset combinado
                if not combined_df.empty:
                    combined_path = self.load_data(combined_df, 'combined_trends')
                    results['combined_data_path'] = combined_path
            
            logger.info("Pipeline ETL ejecutado exitosamente")
            return results
            
        except Exception as e:
            error_msg = f"Error en ejecución del pipeline ETL: {str(e)}"
            logger.error(error_msg)
            results['error'] = error_msg
            return results
