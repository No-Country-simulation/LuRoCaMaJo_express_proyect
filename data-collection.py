# google_trends_collector.py
import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime, timedelta
import os
import json

class GoogleTrendsCollector:
    def __init__(self, timeframe='today 3-m', geo=''):
        """
        Inicializa el colector de Google Trends.
        
        Args:
            timeframe: Período de tiempo para los datos ('today 3-m', 'today 12-m', etc.)
            geo: Código de país para filtrar los datos ('ES', 'MX', 'CO', etc.) o vacío para global
        """
        self.pytrends = TrendReq(hl='es')
        self.timeframe = timeframe
        self.geo = geo
        self.output_dir = 'data/google_trends'
        
        # Crear directorio de salida si no existe
        os.makedirs(self.output_dir, exist_ok=True)
    
    def collect_data(self, keywords_list):
        """
        Recolecta datos de tendencias para las palabras clave especificadas.
        
        Args:
            keywords_list: Lista de listas de palabras clave. Cada lista debe contener máximo 5 keywords.
        
        Returns:
            Dictionary con DataFrames de resultados para cada conjunto de keywords
        """
        results = {}
        
        for i, keywords in enumerate(keywords_list):
            if len(keywords) > 5:
                print(f"Advertencia: Google Trends permite máximo 5 keywords por consulta. Truncando lista {i}.")
                keywords = keywords[:5]
            
            try:
                # Construir consulta
                self.pytrends.build_payload(keywords, 
                                           cat=0,  # Categoría 0 = Todas
                                           timeframe=self.timeframe, 
                                           geo=self.geo)
                
                # Obtener datos de interés a lo largo del tiempo
                interest_over_time = self.pytrends.interest_over_time()
                
                # Obtener datos de interés por región
                interest_by_region = self.pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
                
                # Obtener temas relacionados
                related_topics = self.pytrends.related_topics()
                
                # Obtener consultas relacionadas
                related_queries = self.pytrends.related_queries()
                
                # Almacenar resultados
                results[f"keywords_set_{i}"] = {
                    'keywords': keywords,
                    'interest_over_time': interest_over_time,
                    'interest_by_region': interest_by_region,
                    'related_topics': related_topics,
                    'related_queries': related_queries
                }
                
                # Guardar resultados en archivos CSV
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                keywords_str = '_'.join(keywords).replace(' ', '_')
                
                # Guardar interés a lo largo del tiempo
                if not interest_over_time.empty:
                    interest_over_time.to_csv(f"{self.output_dir}/{timestamp}_{keywords_str}_time.csv")
                
                # Guardar interés por región
                if not interest_by_region.empty:
                    interest_by_region.to_csv(f"{self.output_dir}/{timestamp}_{keywords_str}_region.csv")
                
                # Esperar para evitar límites de tasa
                time.sleep(1)
                
            except Exception as e:
                print(f"Error al recolectar datos para {keywords}: {str(e)}")
        
        return results

    def beauty_keywords_generator(self):
        """
        Genera listas de palabras clave relacionadas con belleza por categorías.
        
        Returns:
            List de listas de palabras clave agrupadas por categoría
        """
        beauty_keywords = {
            'skincare': [
                ['serum vitamina c', 'crema hidratante', 'ácido hialurónico', 'retinol', 'protector solar'],
                ['mascarilla facial', 'limpiador facial', 'tónico facial', 'contorno de ojos', 'exfoliante'],
                ['antiarrugas', 'tratamiento acné', 'piel grasa', 'piel seca', 'rutina facial']
            ],
            'makeup': [
                ['base maquillaje', 'corrector ojeras', 'bronceador', 'iluminador', 'colorete'],
                ['sombra ojos', 'máscara pestañas', 'delineador ojos', 'labial mate', 'labial hidratante'],
                ['cejas perfectas', 'maquillaje natural', 'contouring', 'primer maquillaje', 'fijador maquillaje']
            ],
            'haircare': [
                ['champú sin sulfatos', 'acondicionador pelo', 'mascarilla capilar', 'aceite pelo', 'serum cabello'],
                ['rizos definidos', 'protector térmico', 'tinte pelo', 'pelo dañado', 'anticaída'],
                ['peinados tendencia', 'cortes pelo', 'alisado permanente', 'ondas surferas', 'coleta alta']
            ],
            'nailcare': [
                ['esmalte uñas', 'manicura semipermanente', 'uñas acrílicas', 'nail art', 'lima uñas'],
                ['uñas gel', 'removedor esmalte', 'fortalecedor uñas', 'top coat', 'base coat']
            ],
            'fragrance': [
                ['perfume mujer', 'perfume hombre', 'fragancia unisex', 'perfume dulce', 'perfume cítrico'],
                ['eau de parfum', 'eau de toilette', 'colonia', 'perfume duradero', 'perfume verano']
            ]
        }
        
        # Aplanar la estructura en una lista de listas
        keywords_list = []
        for category, keyword_sets in beauty_keywords.items():
            for keyword_set in keyword_sets:
                keywords_list.append(keyword_set)
        
        return keywords_list

# Ejemplo de uso
if __name__ == "__main__":
    collector = GoogleTrendsCollector(timeframe='today 3-m', geo='ES')
    keywords = collector.beauty_keywords_generator()
    results = collector.collect_data(keywords[:3])  # Recolectar solo los primeros 3 conjuntos como ejemplo
    print(f"Se han recolectado datos para {len(results)} conjuntos de palabras clave.")

# social_media_collector.py
import tweepy
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import time
import requests

class SocialMediaCollector:
    def __init__(self, platform, credentials):
        """
        Inicializa el colector de datos de redes sociales.
        
        Args:
            platform: Plataforma a utilizar ('twitter', 'instagram', etc.)
            credentials: Diccionario con credenciales de API
        """
        self.platform = platform.lower()
        self.credentials = credentials
        self.output_dir = f'data/{self.platform}'
        
        # Crear directorio de salida si no existe
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Inicializar cliente según la plataforma
        if self.platform == 'twitter':
            self._init_twitter_client()
    
    def _init_twitter_client(self):
        """Inicializa el cliente de Twitter API v2"""
        try:
            self.client = tweepy.Client(
                bearer_token=self.credentials.get('bearer_token'),
                consumer_key=self.credentials.get('consumer_key'),
                consumer_secret=self.credentials.get('consumer_secret'),
                access_token=self.credentials.get('access_token'),
                access_token_secret=self.credentials.get('access_token_secret')
            )
        except Exception as e:
            print(f"Error al inicializar cliente de Twitter: {str(e)}")
            self.client = None
    
    def collect_twitter_data(self, query, max_results=100):
        """
        Recolecta tweets relacionados con la consulta especificada.
        
        Args:
            query: String con la consulta de búsqueda
            max_results: Número máximo de tweets a recolectar
        
        Returns:
            DataFrame con los tweets recolectados
        """
        if not self.client:
            print("Cliente de Twitter no inicializado correctamente.")
            return pd.DataFrame()
        
        try:
            # Realizar búsqueda
            tweets = self.client.search_recent_tweets(
                query=query,
                tweet_fields=['created_at', 'lang', 'public_metrics', 'context_annotations'],
                max_results=max_results
            )
            
            if not tweets.data:
                print(f"No se encontraron tweets para la consulta: {query}")
                return pd.DataFrame()
            
            # Procesar resultados
            tweets_data = []
            for tweet in tweets.data:
                tweet_dict = tweet.data
                # Extraer métricas
                metrics = tweet_dict.get('public_metrics', {})
                # Añadir datos al listado
                tweets_data.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'lang': tweet.lang,
                    'retweet_count': metrics.get('retweet_count', 0),
                    'reply_count': metrics.get('reply_count', 0),
                    'like_count': metrics.get('like_count', 0),
                    'quote_count': metrics.get('quote_count', 0)
                })
            
            # Crear DataFrame
            df = pd.DataFrame(tweets_data)
            
            # Guardar resultados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            query_str = query.replace(' ', '_').replace('#', '').replace('@', '')[:30]
            filename = f"{self.output_dir}/{timestamp}_{query_str}.csv"
            df.to_csv(filename, index=False)
            
            print(f"Se han guardado {len(df)} tweets en {filename}")
            
            return df
            
        except Exception as e:
            print(f"Error al recolectar tweets para {query}: {str(e)}")
            return pd.DataFrame()
    
    def collect_instagram_data_mockup(self, hashtag, max_results=100):
        """
        Simulación de recolección de datos de Instagram.
        En un escenario real, aquí conectaríamos con la API de Instagram.
        
        Args:
            hashtag: Hashtag a buscar sin el símbolo #
            max_results: Número máximo de publicaciones a recolectar
        
        Returns:
            DataFrame con las publicaciones simuladas
        """
        # Simular datos de Instagram
        posts_data = []
        
        # En un escenario real, aquí haríamos las llamadas a la API de Instagram
        # Como es una simulación, generamos datos aleatorios
        import numpy as np
        
        for i in range(min(max_results, 30)):  # Simular máximo 30 posts
            posts_data.append({
                'id': f"post_{hashtag}_{i}",
                'caption': f"Post sobre #{hashtag} con contenido relacionado a belleza #{hashtag}",
                'created_at': (datetime.now() - timedelta(hours=np.random.randint(1, 72))).isoformat(),
                'like_count': np.random.randint(10, 1000),
                'comment_count': np.random.randint(0, 100),
                'hashtags': [hashtag, 'belleza', 'tendencias', np.random.choice(['makeup', 'skincare', 'haircare'])]
            })
        
        # Crear DataFrame
        df = pd.DataFrame(posts_data)
        
        # Guardar resultados simulados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.output_dir}/{timestamp}_{hashtag}_mockup.csv"
        df.to_csv(filename, index=False)
        
        print(f"Se han guardado {len(df)} posts simulados de Instagram en {filename}")
        
        return df

# Ejemplo de uso
if __name__ == "__main__":
    # Credenciales de Twitter (reemplazar con las propias en un escenario real)
    twitter_credentials = {
        'bearer_token': 'YOUR_BEARER_TOKEN',
        'consumer_key': 'YOUR_CONSUMER_KEY',
        'consumer_secret': 'YOUR_CONSUMER_SECRET',
        'access_token': 'YOUR_ACCESS_TOKEN',
        'access_token_secret': 'YOUR_ACCESS_TOKEN_SECRET'
    }
    
    # Inicializar colector
    twitter_collector = SocialMediaCollector('twitter', twitter_credentials)
    
    # Recolectar datos (comentado para evitar llamadas a la API sin credenciales válidas)
    # tweets_df = twitter_collector.collect_twitter_data('skincare OR "cuidado piel" lang:es', max_results=50)
    
    # Inicializar colector de Instagram (simulado)
    instagram_collector = SocialMediaCollector('instagram', {})
    
    # Recolectar datos simulados
    posts_df = instagram_collector.collect_instagram_data_mockup('skincare', max_results=20)
