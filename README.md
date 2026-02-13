# Mercado Público Ingestor & Search API

Este proyecto es un backend robusto escrito en Python 3.11+ diseñado para consumir la API de Mercado Público Chile, procesar licitaciones y prepararlas para ser indexadas en Apache Solr. 

Utiliza una arquitectura limpia (**Clean Architecture**) para asegurar la mantenibilidad y el desacoplamiento entre la lógica de negocio y las integraciones externas.

## 🚀 Tecnologías Principales

- **Python 3.11+**
- **FastAPI**: Framework web para la API.
- **Pydantic V2**: Modelamiento y validación de datos.
- **Apache Solr**: Motor de búsqueda y persistencia de documentos.
- **Httpx + Tenacity**: Cliente HTTP asíncrono con lógica de reintentos exponenciales.
- **Poetry**: Gestión de dependencias y entornos virtuales.

## 🏗️ Arquitectura del Proyecto

El código está organizado siguiendo principios de Clean Architecture:

-   **/app/domain**: Contiene las entidades, puertos y esquemas de validación.
    - `schemas.py`: Modelos Pydantic para el JSON original y DTOs del sistema.
-   **/app/application**: Casos de uso y lógica de transformación.
    - `ingestion_service.py`: Lógica para coordinar la ingesta desde la API a Solr.
    - `transformer_service.py`: Transformación de datos raw a formatos optimizados (DTO/IndexDoc).
    - `daily_ingestion_runner.py`: Orquestador para ejecuciones secuenciales de ingesta por estado.
-   **/app/infrastructure**: Adaptadores para servicios externos.
    - `mercadopublico/`: Cliente para la API oficial de Mercado Público.
    - `solr/`: Integración con Apache Solr y definición del esquema (`managed-schema.xml`).
-   **/app/api**: Definición de rutas y controladores FastAPI.

## �️ Seguridad (API Key)

**Importante**: Todas las rutas de la API (incluyendo búsqueda y tests) están protegidas por un token de administración. Debe incluirse en los headers de cada petición.

1. Configure la variable de entorno `ADMIN_TOKEN` en su archivo `.env`.
2. En cada petición, incluya el header:
   ```http
   X-ADMIN-TOKEN: <su_token_secreto>
   ```

## � Endpoints Principales

Todos los endpoints requieren el header `X-ADMIN-TOKEN`.

### Búsqueda y Datos (Solr)
- `GET /search`: Búsqueda avanzada paginada. Ver [search.md](./search.md) para más detalles.
- `GET /tenders/{id}`: Obtiene el detalle de una licitación desde el índice local.

### Administración e Ingesta
- `POST /admin/ingestion/delta`: Dispara una sincronización incremental por estado.
- `POST /admin/ingestion/daily/run-now`: Ejecuta la secuencia completa de ingesta diaria (activas -> ... -> suspendidas).

### Integración Real (Directo a Mercado Público)
- `GET /test/?fecha=DDMMYYYY`: Consulta directa por fecha.
- `GET /test/status/{estado}`: Consulta directa por estado.
- `GET /test/detail?codigo=...`: Detalle crudo de la API.

## 🛠️ Instalación y Configuración

1.  **Clonar el repositorio**:
    ```bash
    git clone <url-del-repositorio>
    cd licitaciones
    ```

2.  **Instalar Poetry** (si no lo tienes):
    Sigue las instrucciones en [python-poetry.org](https://python-poetry.org/docs/#installation).

3.  **Instalar dependencias**:
    ```bash
    poetry install
    ```

4.  **Configurar Variables de Entorno**:
    ```bash
    cp .env.example .env
    ```
    Completa los valores en `.env` (especialmente `MP_TICKET`, `ADMIN_TOKEN` y credenciales de Solr).

## 🚦 Cómo Ejecutar Localmente

```bash
poetry run uvicorn main:app --reload
```
La API estará en `http://localhost:8000`. La documentación Swagger en `/docs`.

## ⏰ Ingesta Diaria Automática (Cron Job)

Para mantener los datos de Solr sincronizados, se recomienda configurar un Cron job externo (ej. cron-job.org o EasyPanel) que llame al endpoint de ejecución diaria.

- **Endpoint**: `POST /admin/ingestion/daily/run-now`
- **Seguridad**: Requiere header `X-ADMIN-TOKEN`.
- **Frecuencia**: Diariamente a las 06:00 AM (Hora local Chile).
- **Concurrencia**: El sistema bloquea ejecuciones solapadas (retorna `409 Conflict`).

## 🚀 Despliegue

### Requisitos Previos
1. **Apache Solr**: Una instancia accesible con un Core configurado usando el `managed-schema.xml` provisto en `app/infrastructure/solr/`.
2. **Mercado Público**: Un `ticket` válido de la API.

### Pasos para Producción
1. Definir las variables en el entorno de producción (ej. variables de entorno en VPS o contenedor):
   - `ADMIN_TOKEN`: Token robusto para proteger la API.
   - `MP_TICKET`: Tu clave de Mercado Público.
   - `SOLR_BASE_URL`, `SOLR_CORE`, `SOLR_USERNAME`, `SOLR_PASSWORD`.
2. Ejecutar con un servidor de producción como **Gunicorn**:
   ```bash
   poetry run gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
3. (Opcional) Configurar un proxy inverso (Nginx) para HTTPS.

## 🔍 Solr (Search Engine)

La configuración del core para Solr se encuentra en `app/infrastructure/solr/managed-schema.xml`. Esta definición está optimizada para búsquedas en español, incluyendo:

- **Filtros de Texto**: Uso de `SpanishLightStemmer` y eliminación de *stopwords*.
- **Facetas**: Soporte para facetas por región, comuna y categoría.
- **Búsqueda**: Indexación de `title` y `description` en campos de texto optimizados.
- **Transformación**: El servicio `TenderTransformer` asegura que los tipos de datos (fechas, montos) lleguen a Solr en el formato correcto para ordenamiento y filtrado.

---
*Desarrollado con enfoque en calidad de datos y escalabilidad.*
