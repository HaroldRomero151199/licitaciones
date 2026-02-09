import logging
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Sin valores por defecto para forzar el uso del .env
    mp_ticket: str
    mp_base_url: str
    solr_url: str
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
