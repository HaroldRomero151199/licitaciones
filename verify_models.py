import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.domain.models import LicitacionResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_models():
    # Example JSON based on the user request
    example_json = {
        "Cantidad": 1,
        "Listado": [
            {
                "CodigoExterno": "4494-3-LP26",
                "Nombre": "ADQUISICIÓN DE DOS CAMIONETAS...",
                "CodigoEstado": 6,
                "Descripcion": "La presente licitación...",
                "Estado": "Cerrada",
                "Comprador": {
                    "CodigoOrganismo": "142575",
                    "NombreOrganismo": "I MUNICIPALIDAD DE PENCO",
                    "RutUnidad": "69.150.500-6",
                    "RegionUnidad": "Región del Biobío "
                },
                "Fechas": {
                    "FechaCreacion": "2026-01-22T00:00:00",
                    "FechaCierre": "2026-02-02T15:00:00"
                },
                "Items": {
                    "Listado": [
                        {
                            "Correlativo": 1,
                            "CodigoProducto": 25101503,
                            "NombreProducto": "Automóviles",
                            "Descripcion": "Camioneta doble cabina...",
                            "Categoria": "Vehículos y equipamiento en general..."
                        }
                    ]
                }
            }
        ]
    }

    try:
        logger.info("Verifying LicitacionResponse model...")
        response = LicitacionResponse(**example_json)
        logger.info("✅ Model verification passed successfully!")
        
        # Verify access to nested fields
        licitacion = response.listado[0]
        logger.info(f"Verified Licitacion: {licitacion.codigo_externo}")
        logger.info(f"Verified Comprador Region: {licitacion.comprador.region_unidad}")
        logger.info(f"Verified Item Category: {licitacion.items_flat[0].categoria}")
        
    except Exception as e:
        logger.error(f"❌ Model verification failed: {e}")
        raise

if __name__ == "__main__":
    verify_models()
