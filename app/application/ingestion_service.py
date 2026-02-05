import logging
from datetime import date
from typing import List
from app.domain.ports import MercadoPublicoClientPort
from app.domain.solr_models import SolrDocument
from app.domain.models import Licitacion

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self, mp_client: MercadoPublicoClientPort, solr_url: str):
        self.mp_client = mp_client
        self.solr_url = solr_url

    async def ingest_by_date(self, target_date: date):
        logger.info(f"Starting ingestion for date: {target_date}")
        
        # 1. Obtener lista
        licitaciones_list = await self.mp_client.get_daily_list(target_date)
        logger.info(f"Found {len(licitaciones_list)} licitaciones in list")
        
        documents = []
        for summary in licitaciones_list[:5]:  # Limitamos a 5 para el test mock
            try:
                # 2. Obtener detalle
                detail = await self.mp_client.get_detail(summary.codigo_externo)
                
                # 3. Transformar
                doc = self._map_to_solr(detail)
                documents.append(doc.model_dump(by_alias=True))
                
                logger.info(f"Processed: {detail.codigo_externo}")
            except Exception as e:
                logger.error(f"Error processing {summary.codigo_externo}: {e}")

        # 4. Enviar a Solr (Mockeamos el envío por ahora si no hay URL)
        logger.info(f"Indexable documents: {len(documents)}")
        if self.solr_url:
            logger.info(f"Sending data to Solr at {self.solr_url}...")
            # Aquí iría la lógica de pysolr
        else:
            logger.warning("No Solr URL provided, skipping indexing.")
            
        return documents

    def _map_to_solr(self, lic: Licitacion) -> SolrDocument:
        # Aplanamiento y concatenación para full_text
        items_text = " ".join([f"{i.nombre_producto} {i.descripcion}" for i in lic.items_flat if i.descripcion])
        full_text = f"{lic.nombre} {lic.descripcion} {items_text}"
        
        keywords = [i.nombre_producto for i in lic.items_flat if i.nombre_producto]
        
        return SolrDocument(
            id=lic.codigo_externo,
            nombre=lic.nombre,
            descripcion=lic.descripcion,
            nombre_organismo=lic.comprador.nombre_organismo,
            region_unidad=lic.comprador.region_unidad,
            comuna_unidad=lic.comprador.comuna_unidad,
            estado=lic.estado,
            fecha_publicacion=lic.fechas.fecha_publicacion.isoformat() if lic.fechas.fecha_publicacion else None,
            fecha_cierre=lic.fechas.fecha_cierre.isoformat() if lic.fechas.fecha_cierre else None,
            monto_estimado=lic.monto_estimado or 0.0,
            moneda=lic.moneda or "CLP",
            full_text=full_text,
            products_keywords=keywords,
            products_count=len(lic.items_flat),
            url=f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={lic.codigo_externo}"
        )
