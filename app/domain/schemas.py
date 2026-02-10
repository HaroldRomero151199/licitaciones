from datetime import datetime
from enum import IntEnum
from typing import List, Optional
from pydantic import BaseModel, Field


# --- Modelos de la API de Mercado Público (Raw / Infrastructure) ---

class CodigoEstado(IntEnum):
    PUBLICADA = 5
    CERRADA = 6
    DESIERTA = 7
    ADJUDICADA = 8
    REVOCADA = 18
    SUSPENDIDA = 19


class Comprador(BaseModel):
    codigo_organismo: str = Field(alias="CodigoOrganismo")
    nombre_organismo: str = Field(alias="NombreOrganismo")
    rut_unidad: str = Field(alias="RutUnidad")
    region_unidad: str = Field(alias="RegionUnidad")
    comuna_unidad: Optional[str] = Field(default=None, alias="ComunaUnidad")


class Fechas(BaseModel):
    fecha_creacion: datetime = Field(alias="FechaCreacion")
    fecha_cierre: Optional[datetime] = Field(default=None, alias="FechaCierre")
    fecha_inicio: Optional[datetime] = Field(default=None, alias="FechaInicio")
    fecha_final: Optional[datetime] = Field(default=None, alias="FechaFinal")
    fecha_publicacion: Optional[datetime] = Field(default=None, alias="FechaPublicacion")


class Item(BaseModel):
    correlativo: int = Field(alias="Correlativo")
    codigo_producto: int = Field(alias="CodigoProducto")
    nombre_producto: Optional[str] = Field(default=None, alias="NombreProducto")
    descripcion: Optional[str] = Field(default=None, alias="Descripcion")
    categoria: str = Field(alias="Categoria")
    unidad_medida: Optional[str] = Field(default=None, alias="UnidadMedida")
    cantidad: Optional[float] = Field(default=None, alias="Cantidad")


class ItemsList(BaseModel):
    listado: List[Item] = Field(alias="Listado")


class LicitacionItem(BaseModel):
    """Representa un item en la respuesta de listado de la API."""
    codigo_externo: str = Field(alias="CodigoExterno")
    nombre: str = Field(alias="Nombre")
    codigo_estado: int = Field(alias="CodigoEstado")
    fecha_cierre: Optional[datetime] = Field(default=None, alias="FechaCierre")


class Licitacion(BaseModel):
    """Representa el detalle completo de una licitación en la API."""
    codigo_externo: str = Field(alias="CodigoExterno")
    nombre: str = Field(alias="Nombre")
    codigo_estado: int = Field(alias="CodigoEstado")
    estado: str = Field(alias="Estado")
    descripcion: str = Field(alias="Descripcion")
    comprador: Comprador = Field(alias="Comprador")
    fechas: Fechas = Field(alias="Fechas")
    items: ItemsList = Field(alias="Items")
    moneda: Optional[str] = Field(default=None, alias="Moneda")
    monto_estimado: Optional[float] = Field(default=None, alias="MontoEstimado")
    cantidad_reclamos: int = Field(default=0, alias="CantidadReclamos")
    tipo: str = Field(default="", alias="Tipo")

    @property
    def items_flat(self) -> List[Item]:
        return self.items.listado


class LicitacionListResponse(BaseModel):
    cantidad: int = Field(alias="Cantidad")
    fecha_creacion: datetime = Field(alias="FechaCreacion")
    version: str = Field(alias="Version")
    listado: List[LicitacionItem] = Field(alias="Listado")


class LicitacionDetailResponse(BaseModel):
    cantidad: int = Field(alias="Cantidad")
    fecha_creacion: datetime = Field(alias="FechaCreacion")
    version: str = Field(alias="Version")
    listado: List[Licitacion] = Field(alias="Listado")


class MercadoPublicoError(BaseModel):
    codigo: int = Field(alias="Codigo")
    mensaje: str = Field(alias="Mensaje")


# --- DTOs del Sistema (Clean Architecture) ---

class TenderSummaryDTO(BaseModel):
    """DTO para respuestas de API (UI List View)."""
    id: str
    title: str
    description: str
    entity: str
    region: str
    comuna: str
    type: str
    status: str
    publish_date: datetime = Field(alias="publishDate")
    closing_date: Optional[datetime] = Field(default=None, alias="closingDate")
    currency: str = "CLP"
    amount: float = 0.0
    monto_display: Optional[str] = Field(default=None, alias="montoDisplay")
    complaints_level: Optional[str] = Field(default=None, alias="complaintsLevel")
    complaints_count: int = Field(default=0, alias="complaintsCount")
    products_count: int = Field(default=0, alias="productsCount")
    url: str
    score: Optional[float] = 0.0

    model_config = {"populate_by_name": True}


class TenderIndexDoc(BaseModel):
    """Modelo para indexar en Solr."""
    id: str
    title: str
    description: str
    entity: str
    region: str
    comuna: str
    type: str
    status: str
    publish_date: datetime
    closing_date: Optional[datetime] = None
    currency: str = "CLP"
    amount: float = 0.0
    category: Optional[str] = None
    complaints_count: int = 0
    complaints_level: Optional[str] = None
    products_count: int = 0

    url: str


class ErrorResponse(BaseModel):
    error: str
    detail: MercadoPublicoError
