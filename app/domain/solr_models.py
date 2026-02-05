from typing import List, Optional
from pydantic import BaseModel, Field

class SolrDocument(BaseModel):
    id: str = Field(..., description="CodigoExterno de la licitación")
    title: str = Field(..., alias="nombre")
    description: str = Field(..., alias="descripcion")
    entity: str = Field(..., alias="nombre_organismo")
    region: str = Field(..., alias="region_unidad")
    comuna: Optional[str] = Field(None, alias="comuna_unidad")
    status: str = Field(..., alias="estado")
    publish_date: Optional[str] = Field(None, alias="fecha_publicacion")
    closing_date: Optional[str] = Field(None, alias="fecha_cierre")
    amount: float = Field(0.0, alias="monto_estimado")
    currency: str = Field("CLP", alias="moneda")
    full_text: str = Field(..., description="Concatenación de nombre, descripción e items")
    products_keywords: List[str] = Field(default_factory=list)
    products_count: int = 0
    url: str

    class Config:
        populate_by_name = True
