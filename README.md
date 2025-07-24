# Recommendations Places API

Sistema de recomendaciones de lugares basado en embeddings de OpenAI y búsqueda vectorial con Qdrant.

## 📋 Descripción

Esta API proporciona recomendaciones de lugares utilizando procesamiento de lenguaje natural. El sistema convierte descripciones de texto en embeddings vectoriales usando OpenAI, almacena estos vectores en Qdrant para búsqueda eficiente, y devuelve lugares similares desde una base de datos PostgreSQL.

## 🏗️ Arquitectura

- **FastAPI**: API REST
- **PostgreSQL**: Base de datos principal de lugares
- **Qdrant**: Base de datos vectorial para embeddings
- **OpenAI**: Generación de embeddings de texto
- **SQLAlchemy**: ORM para PostgreSQL
- **Loguru**: Sistema de logging mejorado

## 🚀 Instalación

### Prerrequisitos

- Python 3.12+
- Docker y Docker Compose
- OpenAI API Key

### Configuración

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd recommendations-places
```

2. **Instalar dependencias**
```bash
# Con poetry (recomendado)
poetry install

# O con pip
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
# Crear archivo .env
cp .envs/.env.example .env

# Editar las variables necesarias:
OPENAI_API_KEY=tu_api_key_de_openai
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=places_embeddings
POSTGRESQL_URL=postgresql://roni:roni123@localhost:9999/places
```

4. **Levantar servicios con Docker**
```bash
docker-compose up -d postgres qdrant
```

5. **Ejecutar migraciones y crear embeddings**
```bash
# Crear embeddings en Qdrant
python src/create_embedings_qdrant.py
```

6. **Iniciar la API**
```bash
python serve.py
```

## 🔍 Diagnóstico y Troubleshooting

### Sistema de Logging Mejorado

La aplicación cuenta con un sistema de logging detallado que proporciona información completa sobre:

#### 🔌 Conexión con Qdrant
- ✅ Estado de conexión en tiempo real
- ⏱️ Tiempos de respuesta detallados
- 🔧 Información de configuración
- 💡 Recomendaciones específicas para errores

#### 📊 Operaciones de Base de Datos
- 🗄️ Logs de consultas PostgreSQL
- 🎯 Resultados de búsqueda vectorial
- 📈 Métricas de rendimiento
- 🔍 Trazabilidad completa de operaciones

### Herramientas de Diagnóstico

#### 1. Script de Diagnóstico Completo
```bash
# Diagnóstico completo
python src/qdrant_diagnostic.py

# Verificación rápida
python src/qdrant_diagnostic.py --quick

# Modo verbose
python src/qdrant_diagnostic.py --verbose
```

El script verifica:
- ✅ Conectividad básica con Qdrant
- 📊 Estado de colecciones
- ⚡ Rendimiento del sistema
- 🔧 Configuración actual

#### 2. Endpoint de Health Check
```bash
# Verificar estado de Qdrant
curl http://localhost:8000/v1/places/health/qdrant
```

#### 3. Script de Verificación de Conexión
```bash
# Verificar conexión con Qdrant
python src/check_qdrant_connection.py

# Verificar conexión con PostgreSQL
python src/check_database_connection.py
```

### Errores Comunes y Soluciones

#### 🚫 "Connection refused" - Qdrant no disponible

**Logs mejorados muestran:**
```
🚫 Error de conexión con Qdrant:
   📍 URL intentada: http://localhost:6333
   🔥 Error: ConnectionError: [Errno 111] Connection refused
   💡 Solución: Verifica que Qdrant esté ejecutándose en http://localhost:6333
   🐳 Docker: docker-compose up qdrant
```

**Solución:**
```bash
# Verificar estado de Docker
docker-compose ps

# Levantar Qdrant
docker-compose up -d qdrant

# Verificar logs
docker-compose logs qdrant
```

#### 📊 Colección no existe

**Logs mejorados muestran:**
```
❌ La colección 'places_embeddings' no encontrada
💡 Crea la colección 'places_embeddings'
🔧 Ejecuta: python src/create_embedings_qdrant.py
```

**Solución:**
```bash
python src/create_embedings_qdrant.py
```

#### ⚡ Rendimiento lento

**Logs mejorados muestran:**
```
⚡ Búsqueda completada en 2.45s
🔴 get_collections: 1.234s
⚠️ Rendimiento lento detectado
```

**Solución:**
- Verificar recursos del sistema
- Revisar configuración de Qdrant
- Considerar optimización de colección

## 📡 API Endpoints

### Recomendaciones
```http
POST /v1/places/recommendations
Content-Type: application/json

{
  "description": "cafeterías para estudiar",
  "limit": 5
}
```

### Health Check
```http
GET /v1/places/health/qdrant
```

### Estado General
```http
GET /health
```

## 📝 Logs Detallados

### Formato de Logs
Los logs incluyen:
- 🔍 **Trazabilidad**: ID de request y operación
- ⏱️ **Tiempos**: Duración de cada operación
- 📊 **Métricas**: Scores de similitud, cantidad de resultados
- 💡 **Contexto**: Recomendaciones específicas para errores

### Ejemplo de Log de Recomendación Exitosa
```
🔍 Generando recomendaciones para: 'cafeterías para estudiar'
   🎯 Límite solicitado: 5
🏥 Verificando estado de Qdrant...
✅ Qdrant disponible (0.023s)
🧠 Generando embedding con OpenAI...
✅ Embedding generado (0.456s)
   📏 Dimensiones: 1536
🎯 Buscando lugares similares en Qdrant...
🚀 Ejecutando búsqueda vectorial...
⚡ Búsqueda completada en 0.089s
📊 Qdrant encontró 5 lugares similares
   🎯 #1: ID=abc123, Score=0.8934
   🎯 #2: ID=def456, Score=0.8712
🗄️ Consultando datos completos en PostgreSQL...
✅ PostgreSQL consultado (0.034s)
📋 Obtenidos 5 lugares de PostgreSQL
✅ Recomendaciones generadas exitosamente!
   ⏱️  Tiempo total: 0.612s
   📊 Resultados: 5
   🎯 Score rango: 0.765 - 0.893
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_api_key
QDRANT_COLLECTION_NAME=places_embeddings

# OpenAI
OPENAI_API_KEY=sk-...

# PostgreSQL
POSTGRESQL_URL=postgresql://user:pass@host:port/db

# Logging
LOG_LEVEL=INFO
LOG_COLORIZE=true
```

### Configuración de Logging
```python
# En settings.py
LOG: LogSettings = LogSettings(
    DEBUG=False,
    COLORIZE=True,
    SERIALIZE=False,
    ENQUEUE=False
)
```

## 📈 Monitoreo

### Métricas Clave
- ⏱️ Tiempo de respuesta de embeddings
- 🔍 Tiempo de búsqueda vectorial
- 📊 Precisión de recomendaciones
- 🔌 Disponibilidad de servicios

### Alertas Recomendadas
- Qdrant no disponible
- Tiempos de respuesta > 2s
- Errores de OpenAI API
- Colecciones vacías

## 🤝 Contribución

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a branch (`git push origin feature/amazing-feature`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

Para soporte técnico:
1. Ejecuta el diagnóstico: `python src/qdrant_diagnostic.py`
2. Revisa los logs de la aplicación
3. Verifica el health check: `/v1/places/health/qdrant`
4. Crea un issue con los logs relevantes 