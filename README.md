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
-   **/app/infrastructure**: Adaptadores para servicios externos.
    - `mercadopublico/`: Cliente para la API oficial de Mercado Público.
    - `solr/`: Integración con Apache Solr y definición del esquema (`managed-schema.xml`).
-   **/app/api**: Definición de rutas y controladores FastAPI.

## 🛠️ Instalación y Configuración

1.  **Clonar el repositorio**:
    ```bash
    git clone <url-del-repositorio>
    cd licitaciones
    ```

2.  **Instalar dependencias**:
    ```bash
    poetry install
    ```

3.  **Configurar Variables de Entorno**:
    Copia el archivo de ejemplo y completa tus credenciales:
    ```bash
    cp .env.example .env
    ```
    Asegúrate de configurar tu `MP_TICKET` (puedes usar el de pruebas: `F8537A18-6766-4DEF-9E59-426B4FEE2844`) y la URL de tu instancia de `SOLR_URL`.

## 🚦 Cómo Ejecutar

### Iniciar el Servidor API
```bash
poetry run uvicorn main:app --reload
```
La API estará disponible en `http://localhost:8000`. Puedes acceder a la documentación interactiva en `/docs`.

### Verificación de Modelos
Si deseas validar que los modelos de datos siguen procesando correctamente los JSON de ejemplo:
```bash
python verify_models.py
```

## 🔗 Endpoints Principales

- `GET /test/`: Consulta licitaciones por fecha directamente a la API real.
- `GET /test/status/{estado}`: Consulta licitaciones por estado (activas, publicada, adjudicada, etc.).
- `GET /test/detail`: Consulta el detalle de una licitación específica por código.
- `GET /test/detail/dto`: Obtiene el detalle de una licitación transformado al DTO simplificado.
- `POST /ingest/test`: Dispara un proceso de ingesta de prueba (actualmente mockeado con archivos locales).

## 🔍 Solr (Search Engine)
La configuración del core para Solr se encuentra en `app/infrastructure/solr/managed-schema.xml`. Esta definición está optimizada para búsquedas en español, incluyendo:
- Configuración de filtros `SpanishLightStemmer`.
- Facetas por región, comuna y categoría.
- Búsqueda por palabras clave en descripciones de productos.

---
*Desarrollado con enfoque en calidad de datos y escalabilidad.*
