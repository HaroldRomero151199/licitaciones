# Mercado Público Ingestor

Este proyecto es un backend robusto escrito en Python 3.11+ diseñado para consumir la API de Mercado Público Chile, procesar licitaciones y prepararlas para ser indexadas en Apache Solr.

## Arquitectura

Se ha seguido una **Clean Architecture** para asegurar la mantenibilidad y desacoplamiento del código:

-   **/app/domain**: Contiene las entidades y modelos de datos (Pydantic V2).
-   **/app/infrastructure**: Implementaciones de clientes externos (API Mercado Público, Solr).
-   **/app/application**: Servicios y casos de uso del negocio.

## Modelos de Datos (DTOs)

Se han implementado modelos Pydantic V2 en `domain/models.py` que:
1.  **Mapean el JSON oficial**: Utilizan `alias` para convertir los nombres de campos en `PascalCase` (propios del JSON de Mercado Público) a `snake_case` (estándar de Python).
2.  **Validación Estricta**: Aseguran que los tipos de datos (fechas, enteros, strings) sean correctos antes de procesarlos.
3.  **Normalización**: Manejan la estructura anidada de `Items` y `Comprador` para facilitar el acceso a la data.

> [!NOTE]
> Aunque el directorio `backend/` contiene modelos con nombres en PascalCase, los modelos en `app/domain/models.py` son los recomendados para este proyecto por seguir las convenciones de Python sin perder la compatibilidad con el JSON original.

## Requisitos Previos

-   Python 3.11 o superior.
-   [Poetry](https://python-poetry.org/) (recomendado) o Pip.

## Instalación y Configuración

1.  **Instalar dependencias**:
    ```bash
    poetry install
    ```
    O usando pip:
    ```bash
    pip install httpx pydantic tenacity pysolr
    ```

2.  **Configuración**:
    Asegúrate de tener un ticket válido de Mercado Público. El ticket de pruebas es: `F8537A18-6766-4DEF-9E59-426B4FEE2844`.

## Cómo Ejecutar

### Verificación de Modelos
Para verificar que los modelos parsean correctamente el JSON de ejemplo proporcionado por la documentación:
```bash
python verify_models.py
```

### Uso del Cliente API
El cliente se encuentra en `infrastructure/mercadopublico/client.py`. Soporta reintentos automáticos y peticiones asíncronas.

```python
from app.infrastructure.mercadopublico.client import MercadoPublicoClient

client = MercadoPublicoClient(ticket="TU_TICKET")
# Uso asíncrono...
```

## Solr (Search Engine)
En `infrastructure/solr/managed-schema.xml` encontrarás la definición sugerida del core para Solr, optimizada para búsquedas en español y facetas por región y categoría.
# licitaciones
