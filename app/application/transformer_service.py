import re
from typing import List, Optional
from app.domain.schemas import Licitacion, TenderSummaryDTO, TenderIndexDoc


class TenderTransformer:
    """Servicio para transformar objetos Licitacion a DTOs y documentos de índice."""
    
    @staticmethod
    def _map_status(code: int) -> str:
        """Mapea código de estado a string legible."""
        return {
            5: "open",
            6: "closed",
            7: "deserted",
            8: "awarded",
            18: "revoked",
            19: "suspended",
        }.get(code, "unknown")
    
    @staticmethod
    def _complaints_level(count: int) -> str:
        """Calcula nivel de reclamos basado en cantidad."""
        if count >= 500:
            return "alto"
        if count >= 100:
            return "medio"
        return "bajo"
    
    @staticmethod
    def _monto_display(amount: Optional[float], tender_type: str = "") -> str:
        """Genera representación legible del monto en rangos UTM o basado en el tipo."""
        # Mapeo estándar de tipos de licitación a rangos de UTM en Chile
        type_ranges = {
            "L1": "Menor a 100 UTM",
            "LE": "De 100 UTM a 1.000 UTM",
            "LP": "De 1.000 UTM a 2.000 UTM",
            "LQ": "De 2.000 UTM a 5.000 UTM",
            "LR": "Mayor a 5.000 UTM",
            "E2": "Menor a 100 UTM",
            "CO": "De 100 UTM a 1.000 UTM",
            "B2": "De 1.000 UTM a 2.000 UTM",
            "H2": "De 2.000 UTM a 5.000 UTM",
            "I2": "Mayor a 5.000 UTM",
            "LS": "Servicios personales especializados",
        }

        # Si el tipo existe en nuestro mapeo oficial, devolvemos el rango estándar
        if tender_type in type_ranges:
            return type_ranges[tender_type]
            
        return "Monto no especificado"


    
    @classmethod
    def to_summary_dto(cls, lic: Licitacion, complaints_count: Optional[int] = None) -> TenderSummaryDTO:
        """
        Transforma Licitacion a DTO mínimo para respuestas de API.
        
        Args:
            lic: Objeto Licitacion del dominio
            complaints_count: Cantidad de reclamos (sobrescribe el valor de la licitación si se provee)
            
        Returns:
            TenderSummaryDTO: DTO mínimo para list view
        """
        # Usar el valor de la licitación si no se pasa uno explícito
        count = complaints_count if complaints_count is not None else lic.cantidad_reclamos

        return TenderSummaryDTO(
            id=lic.codigo_externo,
            title=lic.nombre,
            description=lic.descripcion,
            entity=lic.comprador.nombre_organismo,
            region=lic.comprador.region_unidad,
            comuna=lic.comprador.comuna_unidad or "",
            type=lic.tipo,
            status=cls._map_status(lic.codigo_estado),
            publishDate=lic.fechas.fecha_publicacion,
            closingDate=lic.fechas.fecha_cierre,
            currency=lic.moneda or "CLP",
            amount=lic.monto_estimado or 0.0,
            montoDisplay=cls._monto_display(lic.monto_estimado, lic.tipo),
            complaintsLevel=cls._complaints_level(count),
            complaintsCount=count,
            productsCount=len(lic.items_flat),
            url=f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={lic.codigo_externo}",
            score=0.0,
        )
    
    @classmethod
    def to_index_doc(cls, lic: Licitacion, complaints_count: Optional[int] = None) -> TenderIndexDoc:
        """
        Transforma Licitacion a documento para indexar en Solr.
        
        Args:
            lic: Objeto Licitacion del dominio
            complaints_count: Cantidad de reclamos (sobrescribe el valor de la licitación si se provee)
            
        Returns:
            TenderIndexDoc: Documento listo para indexar en Solr
        """
        # Usar el valor de la licitación si no se pasa uno explícito
        count = complaints_count if complaints_count is not None else lic.cantidad_reclamos

        # Extraer categoría del primer item
        first_category = ""
        if lic.items and lic.items.listado:
            first_category = lic.items.listado[0].categoria or ""
        

        
        return TenderIndexDoc(
            id=lic.codigo_externo,
            title=lic.nombre,
            description=lic.descripcion,
            entity=lic.comprador.nombre_organismo,
            region=lic.comprador.region_unidad,
            comuna=lic.comprador.comuna_unidad or "",
            type=lic.tipo,
            status=cls._map_status(lic.codigo_estado),
            publish_date=lic.fechas.fecha_publicacion,
            closing_date=lic.fechas.fecha_cierre,
            currency=lic.moneda or "CLP",
            amount=lic.monto_estimado or 0.0,
            category=first_category,
            complaints_count=count,
            complaints_level=cls._complaints_level(count),
            products_count=len(lic.items_flat),

            url=f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={lic.codigo_externo}",
        )
