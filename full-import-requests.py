# import_requests.py
import os
import json
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import backoff

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/import_requests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('beauty_trends_import')

class BeautyTrendsDataCollector:
    """Clase para recolectar datos de diferentes APIs relacionadas con tendencias de belleza"""
    
    def __init__(self, output_dir: str = 'data/raw'):
        """
        Inicializa el recolector de datos
        
        Args:
            output_dir: Directorio donde se guardarán los datos recolectados
        """
        self.output_dir = output_dir
        
        # Crear directorio si no existe
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Cargar credenciales desde variables de entorno
        self.tiktok_api_key = os.getenv('TIKTOK_API_KEY')
        self.tiktok_api_secret = os.getenv('TIKTOK_API_SECRET')
        self.ecommerce_api_key = os.getenv('ECOMMERCE_API_KEY')
        
        # Definir categorías y términos de interés
        self.beauty_categories = [
            'maquillaje', 'skincare', 'cabello', 'uñas', 'fragancias', 
            'cuidado facial', 'cuidado corporal', 'cosmética natural'
        ]
        
        # Marcas populares de belleza para seguimiento
        self.beauty_brands = [
            'loreal', 'maybelline', 'mac', 'clinique', 'esteelauder', 
            'cerave', 'neutrogena', 'theordinary', 'fenty', 'glossier'
        ]
        
        # Límites y configuración para solicitudes API
        self.max_requests_per_minute = 30
        self.request_timestamps = []
        
        logger.info("Inicializado recolector de datos de tendencias de belleza")
    
    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, requests.exceptions.HTTPError),
                         max_tries=5)
    def _make_api_request(self, url: str, headers: Dict, params: Optional[Dict] = None) -> Dict:
        """
        Realiza una solicitud API con manejo de límites de tasa
        
        Args:
            url: URL endpoint
            headers: Cabeceras de la solicitud
            params: Parámetros de la solicitud
            
        Returns:
            Respuesta de la API en formato diccionario
        """
        # Control de límites de tasa
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Eliminar timestamps antiguos
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > minute_ago]
        
        # Verificar si estamos cerca del límite
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_timestamps[0])
            if sleep_time > 0:
                logger.info(f"Límite de tasa alcanzado, esperando {sleep_time:.2f} segundos")
                time.sleep(sleep_time)
        
        # Realizar solicitud
        response = requests.get(url, headers=headers, params=params)
        
        # Registrar timestamp
        self.request_timestamps.append(time.time())
        
        # Verificar respuesta
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error en API: {response.status_code} - {response.text}")
            response.raise_for_status()
    
    def collect_tiktok_data(self, days_back: int = 30) -> pd.DataFrame:
        """
        Recolecta datos de la API de TikTok
        
        Args:
            days_back: Número de días hacia atrás para recolectar datos
            
        Returns:
            DataFrame con datos recolectados
        """
        if not self.tiktok_api_key or not self.tiktok_api_secret:
            logger.error("No se encontraron credenciales para TikTok API")
            return pd.DataFrame()
        
        logger.info(f"Iniciando recolección de datos de TikTok para los últimos {days_back} días")
        
        # Crear headers de autenticación
        headers = {
            "Authorization": f"Bearer {self.tiktok_api_key}",
            "Content-Type": "application/json"
        }
        
        # Calcular rango de fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        all_data = []
        
        # Recolectar datos para cada categoría
        for category in self.beauty_categories:
            try:
                logger.info(f"Consultando TikTok API para categoría: {category}")
                
                # Endpoint para hashtags de tendencias
                url = "https://open.tiktokapis.com/v2/research/hashtag/trending/"
                params = {
                    "keywords": f"beauty {category}",
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "region_code": "MX"  # México, ajustar según necesidades
                }
                
                response_data = self._make_api_request(url, headers, params)
                
                if response_data and 'data' in response_data:
                    # Procesar datos según estructura de la API
                    for hashtag in response_data['data'].get('hashtags', []):
                        hashtag_data = {
                            'category': category,
                            'hashtag': hashtag.get('display_name', ''),
                            'view_count': hashtag.get('view_count', 0),
                            'video_count': hashtag.get('video_count', 0),
                            'source': 'tiktok',
                            'date_collected': datetime.now().strftime("%Y-%m-%d"),
                            'period_start': start_date_str,
                            'period_end': end_date_str
                        }
                        all_data.append(hashtag_data)
                
                # Añadir datos de búsqueda de marcas populares
                for brand in self.beauty_brands:
                    brand_url = "https://open.tiktokapis.com/v2/research/video/search/"
                    brand_params = {
                        "keywords": f"{brand} {category}",
                        "start_date": start_date_str,
                        "end_date": end_date_str,
                        "region_code": "MX",
                        "max_count": 50,
                        "sort_type": "likes"
                    }
                    
                    brand_data = self._make_api_request(brand_url, headers, brand_params)
                    
                    if brand_data and 'data' in brand_data:
                        for video in brand_data['data'].get('videos', []):
                            video_data = {
                                'category': category,
                                'brand': brand,
                                'video_id': video.get('id', ''),
                                'likes': video.get('like_count', 0),
                                'comments': video.get('comment_count', 0),
                                'shares': video.get('share_count', 0),
                                'views': video.get('view_count', 0),
                                'created_at': video.get('create_time', ''),
                                'source': 'tiktok_video',
                                'date_collected': datetime.now().strftime("%Y-%m-%d")
                            }
                            all_data.append(video_data)
                
                # Pausa para respetar límites de la API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error al recolectar datos de TikTok para {category}: {str(e)}")
        
        # Crear DataFrame
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Guardar datos crudos
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.output_dir, f"tiktok_raw_{timestamp}.csv")
            df.to_csv(output_file, index=False)
            
            logger.info(f"Datos de TikTok guardados en {output_file}, {len(df)} registros")
            return df
        else:
            logger.warning("No se recolectaron datos de TikTok")
            return pd.DataFrame()
    
    def collect_ecommerce_data(self) -> pd.DataFrame:
        """
        Recolecta datos de tendencias de productos de APIs de e-commerce
        
        Returns:
            DataFrame con datos de productos tendencia
        """
        if not self.ecommerce_api_key:
            logger.error("No se encontró clave de API para e-commerce")
            return pd.DataFrame()
        
        logger.info("Iniciando recolección de datos de e-commerce")
        
        # Plataformas de e-commerce a consultar
        platforms = ['mercadolibre', 'amazon', 'walmart']
        
        all_product_data = []
        
        for platform in platforms:
            for category in self.beauty_categories:
                try:
                    logger.info(f"Consultando productos de {category} en {platform}")
                    
                    # URL según plataforma (ajustar según documentación real de APIs)
                    if platform == 'mercadolibre':
                        url = "https://api.mercadolibre.com/sites/MLM/search"
                        headers = {"Accept": "application/json"}
                        params = {
                            "q": f"belleza {category}",
                            "sort": "relevance",
                            "limit": 50
                        }
                    elif platform == 'amazon':
                        # Usar un servicio de proxy para Amazon, como RapidAPI
                        url = "https://amazon-product-data.p.rapidapi.com/search"
                        headers = {
                            "X-RapidAPI-Key": self.ecommerce_api_key,
                            "X-RapidAPI-Host": "amazon-product-data.p.rapidapi.com"
                        }
                        params = {
                            "keyword": f"beauty {category}",
                            "country": "mx",
                            "page": "1"
                        }
                    elif platform == 'walmart':
                        url = "https://walmart.p.rapidapi.com/products/search"
                        headers = {
                            "X-RapidAPI-Key": self.ecommerce_api_key,
                            "X-RapidAPI-Host": "walmart.p.rapidapi.com"
                        }
                        params = {
                            "query": f"beauty {category}",
                            "page": "1"
                        }
                    
                    # Realizar solicitud
                    response_data = self._make_api_request(url, headers, params)
                    
                    # Procesar datos según estructura de cada API
                    if platform == 'mercadolibre' and 'results' in response_data:
                        for product in response_data['results']:
                            product_data = {
                                'platform': platform,
                                'category': category,
                                'product_id': product.get('id', ''),
                                'title': product.get('title', ''),
                                'price': product.get('price', 0),
                                'currency': product.get('currency_id', ''),
                                'rating': product.get('seller', {}).get('seller_reputation', {}).get('level_id', ''),
                                'sold_quantity': product.get('sold_quantity', 0),
                                'product_url': product.get('permalink', ''),
                                'source': platform,
                                'date_collected': datetime.now().strftime("%Y-%m-%d")
                            }
                            all_product_data.append(product_data)
                    elif platform == 'amazon' and 'results' in response_data:
                        for product in response_data['results']:
                            product_data = {
                                'platform': platform,
                                'category': category,
                                'product_id': product.get('asin', ''),
                                'title': product.get('title', ''),
                                'price': product.get('price', {}).get('current_price', 0),
                                'currency': product.get('price', {}).get('currency', ''),
                                'rating': product.get('rating', 0),
                                'reviews_count': product.get('reviews_count', 0),
                                'product_url': product.get('url', ''),
                                'source': platform,
                                'date_collected': datetime.now().strftime("%Y-%m-%d")
                            }
                            all_product_data.append(product_data)
                    elif platform == 'walmart' and 'items' in response_data:
                        for product in response_data['items']:
                            product_data = {
                                'platform': platform,
                                'category': category,
                                'product_id': product.get('id', ''),
                                'title': product.get('name', ''),
                                'price': product.get('price', {}).get('currentPrice', 0),
                                'currency': 'MXN',  # Asumiendo MXN para Walmart México
                                'rating': product.get('rating', {}).get('averageRating', 0),
                                'reviews_count': product.get('rating', {}).get('numberOfReviews', 0),
                                'product_url': product.get('productPageUrl', ''),
                                'source': platform,
                                'date_collected': datetime.now().strftime("%Y-%m-%d")
                            }
                            all_product_data.append(product_data)
                    
                    # Pausa para respetar límites
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error al recolectar datos de {platform} para {category}: {str(e)}")
        
        # Crear DataFrame
        if all_product_data:
            df = pd.DataFrame(all_product_data)
            
            # Guardar datos crudos
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.output_dir, f"ecommerce_raw_{timestamp}.csv")
            df.to_csv(output_file, index=False)
            
            logger.info(f"Datos de e-commerce guardados en {output_file}, {len(df)} registros")
            return df
        else:
            logger.warning("No se recolectaron datos de e-commerce")
            return pd.DataFrame()
    
    def collect_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Ejecuta recolección de datos de todas las fuentes
        
        Returns:
            Diccionario con DataFrames para cada fuente
        """
        logger.info("Iniciando recolección de datos de todas las fuentes")
        
        results = {}
        
        # Recolectar datos de TikTok
        tiktok_df = self.collect_tiktok_data()
        if not tiktok_df.empty:
            results['tiktok'] = tiktok_df
        
        # Recolectar datos de e-commerce
        ecommerce_df = self.collect_ecommerce_data()
        if not ecommerce_df.empty:
            results['ecommerce'] = ecommerce_df
        
        # Guardar metadatos de la recolección
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'sources': list(results.keys()),
            'record_counts': {source: len(df) for source, df in results.items()},
            'categories': self.beauty_categories,
            'brands': self.beauty_brands
        }
        
        metadata_file = os.path.join(self.output_dir, f"collection_metadata_{datetime.now().strftime('%Y%m%d')}.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Recolección de datos completada. Fuentes: {list(results.keys())}")
        return results

# Función principal para ejecutar la recolección desde línea de comandos
def main():
    """Función principal para ejecutar el recolector de datos"""
    collector = BeautyTrendsDataCollector()
    results = collector.collect_all_data()
    
    # Mostrar resumen de resultados
    print("\n--- Resumen de Recolección de Datos ---")
    for source, df in results.items():
        print(f"Fuente: {source} - {len(df)} registros recolectados")

if __name__ == "__main__":
    main()
