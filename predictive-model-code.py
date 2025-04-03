import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

class BeautyTrendPredictor:
    def __init__(self):
        self.pipeline = None
        self.model_path = "models/beauty_trend_predictor.pkl"
        
    def preprocess_data(self, df):
        """Preprocesa los datos para el modelado"""
        # Separar características numéricas y categóricas
        numeric_features = ['views_count', 'engagement_rate', 'search_volume', 'mentions_count']
        categorical_features = ['product_category', 'season', 'platform']
        
        # Crear transformadores para cada tipo de característica
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        # Combinar los transformadores
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])
        
        return preprocessor
    
    def build_model(self):
        """Construye el pipeline completo de modelado"""
        preprocessor = self.preprocess_data(None)
        
        # Crear pipeline con preprocesador y modelo
        self.pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', RandomForestRegressor(random_state=42))
        ])
        
        return self.pipeline
    
    def tune_hyperparameters(self, X, y):
        """Optimiza hiperparámetros del modelo"""
        if self.pipeline is None:
            self.build_model()
        
        # Definir espacio de búsqueda de hiperparámetros
        param_grid = {
            'regressor__n_estimators': [50, 100, 200],
            'regressor__max_depth': [None, 10, 20],
            'regressor__min_samples_split': [2, 5, 10]
        }
        
        # Realizar búsqueda de grid con validación cruzada
        grid_search = GridSearchCV(
            self.pipeline, param_grid, cv=5, 
            scoring='neg_mean_squared_error', n_jobs=-1
        )
        
        grid_search.fit(X, y)
        
        print(f"Mejores parámetros: {grid_search.best_params_}")
        self.pipeline = grid_search.best_estimator_
        
        return self.pipeline
    
    def fit(self, X, y):
        """Entrena el modelo con los datos proporcionados"""
        if self.pipeline is None:
            self.build_model()
        
        # Dividir datos en entrenamiento y validación
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Entrenar modelo
        self.pipeline.fit(X_train, y_train)
        
        # Evaluar en conjunto de validación
        y_pred = self.pipeline.predict(X_val)
        mse = mean_squared_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        print(f"MSE de validación: {mse:.4f}")
        print(f"R² de validación: {r2:.4f}")
        
        return self
    
    def predict(self, X):
        """Realiza predicciones con el modelo entrenado"""
        if self.pipeline is None:
            raise ValueError("El modelo no ha sido entrenado. Ejecute fit() primero.")
        
        return self.pipeline.predict(X)
    
    def save_model(self):
        """Guarda el modelo entrenado en disco"""
        if self.pipeline is None:
            raise ValueError("No hay modelo para guardar. Ejecute fit() primero.")
        
        joblib.dump(self.pipeline, self.model_path)
        print(f"Modelo guardado en {self.model_path}")
    
    def load_model(self):
        """Carga un modelo previamente guardado"""
        self.pipeline = joblib.load(self.model_path)
        return self

# Implementación de ejemplo:
if __name__ == "__main__":
    # Simulamos datos de entrenamiento para ejemplificar
    # En un caso real, estos datos vendrían de tu pipeline ETL
    data = {
        'views_count': np.random.randint(1000, 100000, 1000),
        'engagement_rate': np.random.uniform(0.01, 0.25, 1000),
        'search_volume': np.random.randint(500, 50000, 1000),
        'mentions_count': np.random.randint(10, 5000, 1000),
        'product_category': np.random.choice(['skincare', 'makeup', 'haircare', 'fragrance'], 1000),
        'season': np.random.choice(['spring', 'summer', 'fall', 'winter'], 1000),
        'platform': np.random.choice(['tiktok', 'instagram', 'youtube'], 1000),
        'trend_score': np.random.uniform(0, 100, 1000)  # Variable objetivo
    }
    
    df = pd.DataFrame(data)
    
    # Separar características y variable objetivo
    X = df.drop('trend_score', axis=1)
    y = df['trend_score']
    
    # Crear y entrenar el modelo
    predictor = BeautyTrendPredictor()
    predictor.build_model()
    predictor.fit(X, y)
    
    # Opcional: optimizar hiperparámetros
    # predictor.tune_hyperparameters(X, y)
    
    # Guardar el modelo
    predictor.save_model()
