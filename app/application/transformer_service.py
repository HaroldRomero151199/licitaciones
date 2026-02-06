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
            "L1": "Menos de 100 UTM",
            "LE": "De 100 UTM a 1.000 UTM",
            "LP": "De 1.000 UTM a 2.000 UTM",
            "LR": "De 2.000 UTM a 5.000 UTM",
            "LQ": "Más de 5.000 UTM",
            "LS": "Menos de 100 UTM",
        }

        # Si el tipo existe en nuestro mapeo oficial, devolvemos el rango estándar
        if tender_type in type_ranges:
            return type_ranges[tender_type]
            
        return "Monto no especificado"

    @staticmethod
    def _extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
        """Extrae palabras clave relevantes del texto (para indexación)."""
        if not text:
            return []
        
        # Extraer palabras de 4+ letras
        words = re.findall(r"\b\w{4,}\b", text.lower())
        
        # Stop words básicas en español
        stop = {
            "para", "con", "por", "los", "las", "del", "de", "la", "el",
            "en", "y", "a", "que", "un", "una", "este", "esta", "año",
            "tiene", "como", "objeto", "entre", "días", "cabo", "será",
            "debe", "pueden", "todo", "todos", "todas"
        }
        
        # Contar frecuencias
        freq = {}
        for w in words:
            if w not in stop and len(w) > 3:
                freq[w] = freq.get(w, 0) + 1
        
        # Retornar top N por frecuencia
        return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]]
    
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
        
        # Combinar texto para extracción de keywords
        combined_text = f"{lic.nombre} {lic.descripcion}"
        
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
            products_keywords=cls._extract_keywords(combined_text),
            url=f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={lic.codigo_externo}",
        )
