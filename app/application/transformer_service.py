from typing import Any, Dict, Optional
from app.domain.schemas import Licitacion, TenderSummaryDTO, TenderIndexDoc


class TenderTransformer:
    """Transforms domain models into DTOs and Solr index documents."""
    
    @staticmethod
    def _map_status(code: int) -> str:
        """Maps MercadoPublico status codes into a stable string."""
        return {
            5: "open",
            6: "closed",
            7: "deserted",
            8: "awarded",
            15: "revoked",
            16: "suspended",
        }.get(code, "unknown")
    
    @staticmethod
    def _complaints_level(count: int) -> str:
        """Computes complaints level from a numeric count."""
        if count >= 500:
            return "alto"
        if count >= 100:
            return "medio"
        return "bajo"
    
    @staticmethod
    def _monto_display(amount: Optional[float], tender_type: str = "") -> str:
        """Builds a human-friendly amount label, mostly derived from tender type."""
        # Standard mapping of tender types to UTM ranges in Chile
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

        # If the type exists in our official mapping, return the standard range label
        if tender_type in type_ranges:
            return type_ranges[tender_type]
            
        return "Monto no especificado"


    
    @classmethod
    def to_summary_dto(cls, lic: Licitacion, complaints_count: Optional[int] = None) -> TenderSummaryDTO:
        """
        Transforms a `Licitacion` into a compact DTO for API responses.
        
        Args:
            lic: Domain `Licitacion` instance
            complaints_count: Optional override for complaints count
            
        Returns:
            TenderSummaryDTO: DTO for list view
        """
        # Use the tender value unless explicitly overridden
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
        Transforms a `Licitacion` into a document ready to be indexed in Solr.
        
        Args:
            lic: Domain `Licitacion` instance
            complaints_count: Optional override for complaints count
            
        Returns:
            TenderIndexDoc: Index document
        """
        # Use the tender value unless explicitly overridden
        count = complaints_count if complaints_count is not None else lic.cantidad_reclamos

        # Extract category from the first item
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
            status_code=lic.codigo_estado,
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

    # --- Helpers for Solr search results ---

    @staticmethod
    def _first_or_empty(value: Any) -> str:
        """Normalizes Solr fields that may be returned as a list or a scalar."""
        if isinstance(value, list):
            return value[0] if value else ""
        return value or ""

    @staticmethod
    def _first_or_none(value: Any) -> Any:
        """Returns the first element of a list or the value itself; allows None."""
        if isinstance(value, list):
            return value[0] if value else None
        return value

    @staticmethod
    def _first_number_or_default(value: Any, default: float | int = 0) -> float | int:
        """Normalizes numeric fields that may arrive as a single value or list."""
        if isinstance(value, list):
            if not value:
                return default
            return value[0]
        if value is None:
            return default
        return value

    @classmethod
    def solr_doc_to_summary_dto(cls, doc: Dict[str, Any]) -> TenderSummaryDTO:
        """
        Converts a raw Solr document (dict) into a `TenderSummaryDTO`
        ready for frontend consumption.
        """
        return TenderSummaryDTO(
            id=doc.get("id", ""),
            title=cls._first_or_empty(doc.get("title")),
            description=cls._first_or_empty(doc.get("description")),
            entity=cls._first_or_empty(doc.get("entity")),
            region=cls._first_or_empty(doc.get("region")),
            comuna=cls._first_or_empty(doc.get("comuna")),
            type=cls._first_or_empty(doc.get("type")),
            status=cls._map_status(int(cls._first_number_or_default(doc.get("status_code"), 0))),
            publishDate=cls._first_or_none(doc.get("publish_date")),
            closingDate=cls._first_or_none(doc.get("closing_date")),
            currency=cls._first_or_empty(doc.get("currency")) or "CLP",
            amount=cls._first_number_or_default(doc.get("amount"), 0.0),
            montoDisplay=cls._monto_display(
                cls._first_number_or_default(doc.get("amount"), 0.0),
                cls._first_or_empty(doc.get("type")),
            ),
            complaintsLevel=cls._first_or_empty(doc.get("complaints_level")),
            complaintsCount=cls._first_number_or_default(doc.get("complaints_count"), 0),
            productsCount=cls._first_number_or_default(doc.get("products_count"), 0),
            url=cls._first_or_empty(doc.get("url")),
            score=doc.get("score", 0.0),
        )
