
### 📦 Respuesta del endpoint `GET /search`

Este endpoint está pensado para ser consumido por un frontend (SPA o similar) y expone una búsqueda paginada sobre el índice de licitaciones en Solr.

- **Método**: `GET`
- **URL**: `/search`

**Parámetros de query:**

- `q` (**string, requerido**): texto a buscar, se aplica principalmente sobre `title` y `description`.
- `page` (**int, opcional**, por defecto `1`, mínimo `1`): número de página (1-indexado).
- `size` (**int, opcional**, por defecto `20`, mínimo `1`, máximo `100`): cantidad de resultados por página.

Ejemplo:

```http
GET /search?q=convenio&page=2&size=10
```

**Respuesta (`200 OK`):**

```json
{
  "query": "convenio",
  "page": 2,
  "size": 10,
  "total": 137,
  "totalPages": 14,
  "items": [
    {
      "id": "1002-11-LP26",
      "title": "VIGAS METALICAS 30 METROS GALVANIZADAS CON ARRIOSTRAMIENTOS",
      "description": "VIGAS METALICAS 30 METROS GALVANIZADAS CON ARRIOSTRAMIENTOS",
      "entity": "MINISTERIO DE OBRAS PUBLICAS ...",
      "region": "Región de los Lagos",
      "comuna": "Puerto Montt",
      "type": "LP",
      "status": "open",
      "publishDate": "2026-01-29T16:36:00Z",
      "closingDate": "2026-02-16T15:00:00Z",
      "currency": "CLP",
      "amount": 0.0,
      "montoDisplay": "De 1.000 UTM a 2.000 UTM",
      "complaintsLevel": "medio",
      "complaintsCount": 459,
      "productsCount": 1,
      "url": "https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion=1002-11-LP26",
      "score": 3.21
    }
  ]
}
```

**Campos de nivel superior:**

- `query`: texto final de búsqueda que se envió a Solr.
- `page`: página actual (1-indexada).
- `size`: cantidad de elementos por página.
- `total`: número total de resultados que cumplen la búsqueda.
- `totalPages`: número total de páginas (`ceil(total / size)`).
- `items`: arreglo de resultados (`TenderSummaryDTO`).

**Estructura de cada ítem (`TenderSummaryDTO`):**

- `id`: código externo de la licitación (ej. `1002-11-LP26`).
- `title`: título de la licitación.
- `description`: descripción de la licitación.
- `entity`: organismo comprador.
- `region`: región del organismo.
- `comuna`: comuna del organismo.
- `type`: tipo de licitación (L1, LE, LP, etc.).
- `status`: estado normalizado (`open`, `closed`, `deserted`, `awarded`, etc.).
- `publishDate`: fecha de publicación (ISO 8601).
- `closingDate`: fecha de cierre (ISO 8601 o `null`).
- `currency`: moneda (por defecto `CLP`).
- `amount`: monto estimado (si está disponible, sino `0.0`).
- `montoDisplay`: texto legible del rango de monto (por tipo de licitación).
- `complaintsLevel`: nivel de reclamos (`bajo`, `medio`, `alto`).
- `complaintsCount`: número de reclamos.
- `productsCount`: número de productos/ítems de la licitación.
- `url`: enlace directo a la ficha en Mercado Público.
- `score`: puntaje de relevancia entregado por Solr para esa búsqueda.