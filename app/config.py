import logging
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Sin valores por defecto para forzar el uso del .env
    mp_ticket: str
    mp_base_url: str
    
    # Solr Configuration
    solr_base_url: str
    solr_core: str
    solr_username: str
    solr_password: str
    
    # Deprecated/Legacy (keeping for compatibility if needed, or we can migrate)
    # solr_url: str  <-- I will remove this if I update all usages.
    # Let's see where solr_url is used. It's used in dependencies.py. 
    # I will replace solr_url with solr_base_url and solr_core in dependencies.py later.
    # For now, let's just add the new ones and remove solr_url if I'm confident. 
    # The existing solr_url was just the base URL anyway?
    # View file app/dependencies.py at step 152: 
    # return IngestionService(mp_client=real_client, solr_url=settings.solr_url)
    
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

# Instancia única de configuración
try:
    settings = Settings()
except Exception as e:
    # Esto fallará si falta MP_TICKET en el .env
    print(f"Error cargando configuración: {e}")
    raise

# Configuración de logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger("licitaciones")
