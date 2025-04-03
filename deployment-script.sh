#!/bin/bash

# Script para desplegar el prototipo en la nube
# Este script asume que tienes instalado Google Cloud SDK

# Variables de configuración
PROJECT_ID="beauty-trends-analyzer"
REGION="us-central1"
SERVICE_NAME="beauty-trends-api"
CONTAINER_NAME="beauty-trends-api"

echo "Configurando el proyecto en Google Cloud..."
gcloud config set project $PROJECT_ID

echo "Construyendo la imagen Docker..."
# Crear Dockerfile para la API
cat > Dockerfile << EOF
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Crear archivo de requerimientos
cat > requirements.txt << EOF
fastapi==0.95.0
uvicorn==0.21.1
pandas==1.5.3
scikit-learn==1.2.2
numpy==1.24.2
joblib==1.2.0
plotly==5.14.1
streamlit==1.22.0
requests==2.28.2
python-dotenv==1.0.0
EOF

# Construir la imagen Docker
docker build -t $CONTAINER_NAME .

# Taggear la imagen para Google Container Registry
docker tag $CONTAINER_NAME gcr.io/$PROJECT_ID/$CONTAINER_NAME

# Subir la imagen a Google Container Registry
echo "Subiendo la imagen a Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$CONTAINER_NAME

# Desplegar en Cloud Run
echo "Desplegando en Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$CONTAINER_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80

# Desplegar Streamlit en App Engine
echo "Preparando despliegue de Streamlit en App Engine..."

# Crear app.yaml para App Engine
cat > app.yaml << EOF
runtime: python39
entrypoint: streamlit run dashboard/app.py --server.port=\$PORT --server.enableCORS=false
instance_class: F2
automatic_scaling:
  min_instances: 0
  max_instances: 1
EOF

# Desplegar en App Engine
echo "Desplegando Streamlit en App Engine..."
gcloud app deploy --quiet

echo "¡Despliegue completado!"
echo "API disponible en: https://$SERVICE_NAME-$REGION-$PROJECT_ID.a.run.app"
echo "Dashboard disponible en: https://$PROJECT_ID.appspot.com"
