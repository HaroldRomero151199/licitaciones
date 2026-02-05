from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, Field, RootModel


class CodigoEstado(IntEnum):
    PUBLICADA = 5
    CERRADA = 6
    DESIERTA = 7
    ADJUDICADA = 8
    REVOCADA = 18
    SUSPENDIDA = 19
    # Add other states as needed from documentation


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
    # Add other date fields if present in full response


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


class Licitacion(BaseModel):
    codigo_externo: str = Field(alias="CodigoExterno")
    nombre: str = Field(alias="Nombre")
    codigo_estado: int = Field(alias="CodigoEstado")
    estado: str = Field(alias="Estado")
    descripcion: str = Field(alias="Descripcion")
    comprador: Comprador = Field(alias="Comprador")
    fechas: Fechas = Field(alias="Fechas")
    items: ItemsList = Field(alias="Items")
    
    # Optional fields that might appear in full details
    moneda: Optional[str] = Field(default=None, alias="Moneda")
    monto_estimado: Optional[float] = Field(default=None, alias="MontoEstimado")

    @property
    def items_flat(self) -> List[Item]:
        """Helper to access items directly."""
        return self.items.listado


class LicitacionResponse(BaseModel):
    cantidad: int = Field(alias="Cantidad")
    listado: List[Licitacion] = Field(alias="Listado")
