tu_refresh_token
# 📊 Dashboard de Tendencias - Mercado Libre

Este proyecto es una solución completa para analizar y predecir tendencias de búsqueda de Belleza en Mercado Libre Argentina, utilizando:

- 🔥 **FastAPI** como backend
- 📊 **Streamlit** como frontend interactivo
- 🔮 **Prophet** para predicciones
- 🗃️ **SQLite** para almacenamiento
- 🌐 **API oficial de Mercado Libre**

---

## 🚀 Funcionalidades principales

✅ Captura diaria de tendencias desde la API oficial  
✅ Clasificación automática por categoría  
✅ Visualización de top keywords, evolución, y distribución  
✅ Predicciones por palabra clave con Prophet  
✅ Comparación de múltiples tendencias  
✅ Recomendaciones dinámicas basadas en datos históricos  
✅ Exportación de CSV

---

## 🧰 Requisitos

- Python 3.8+
- Cuenta de desarrollador en [developers.mercadolibre.com.ar](https://developers.mercadolibre.com.ar)

Instalación de paquetes:

```bash
pip install -r requirements.txt
```

---

## 🔐 Configuración del entorno

Crea un archivo `.env` en la raíz del proyecto con:

```env
CLIENT_ID=tu_client_id
CLIENT_SECRET=tu_client_secret
```
Y Crea un archivo `refresh_token.txt` en la raíz del proyecto con:

tu_refresh_token

> ⚠️ **Nunca compartas estos archivos ni lo subas al repositorio.**

También asegurate de que tu archivo `.gitignore` contenga:

```
.env
refresh_token.txt
```

---

## 🧪 Ejecución local

### ▶️ 1. Levantar el backend:

```bash
uvicorn app:app --reload
```

Accede a la documentación de la API en:  
`http://localhost:8000/docs`

---

### 💻 2. Correr el dashboard:

```bash
streamlit run dashboard.py
```

Por defecto se conecta a `http://localhost:8000`, pero podés cambiarlo en el panel lateral.

---

## 🗃️ Base de datos

El backend usa una base SQLite `trends.db` con estas tablas:

- `keywords_data`: registros históricos por palabra y categoría
- `keyword_rankings`: ranking de repeticiones
- `category_rankings`: acumulados por categoría

---

## 📦 Estructura del proyecto

```
📂 proyecto/
├── app.py                  ← Backend FastAPI
├── dashboard.py            ← Frontend Streamlit
├── trends.db               ← Base de datos local
├── trend/data.json         ← Última respuesta de tendencias
├── refresh_token.txt       ← Token que se actualiza solo
├── .env                    ← Credenciales privadas
├── .gitignore              ← Ignorar archivos sensibles
└── README.md               ← Este documento
```

---

## 📈 Sobre Prophet

Se usa Prophet para predecir la evolución futura de palabras clave. El sistema simula crecimiento con una progresión acumulada y proyecta 7 a 90 días hacia adelante.

---

## 🙌 Autor

**Mario Passalia**  
Herrería artesanal, testing afilado, y código con garra.

---

## 📬 Contacto

Para dudas, feedback o nuevas ideas:  
📧 tester.passalia@gmail.com 

---

## 🛑 Licencia

Este proyecto es de uso personal y educativo. No está asociado oficialmente con Mercado Libre.
