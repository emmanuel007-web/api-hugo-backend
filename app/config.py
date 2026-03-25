"""
=============================================================================
Configuración y variables de entorno
=============================================================================
Carga la API Key de NYTimes desde el archivo .env usando python-dotenv.
La API Key NUNCA se expone al frontend - permanece solo en el servidor.
=============================================================================
"""

import os
from dotenv import load_dotenv
from functools import lru_cache

# Cargar variables del archivo .env al inicio
load_dotenv()


class Settings:
    """
    Clase de configuración centralizada.
    Lee variables de entorno y provee valores por defecto seguros.
    """

    # API Key de NYTimes - se lee desde .env (NUNCA hardcodeada)
    NYT_API_KEY: str = os.getenv("NYTIMES_API_KEY", "")

    # URL base de la Books API
    NYT_BOOKS_BASE_URL: str = "https://api.nytimes.com/svc/books/v3"

    # URL base de la Article Search API (para reseñas literarias)
    NYT_SEARCH_BASE_URL: str = "https://api.nytimes.com/svc/search/v2"

    # Tiempo máximo de espera para peticiones HTTP al NYT (segundos)
    HTTP_TIMEOUT: float = 15.0

    # Máximo de resultados por página en búsquedas
    MAX_RESULTS: int = 20

    def validate(self) -> None:
        """Valida que la API Key esté configurada."""
        if not self.NYT_API_KEY:
            raise ValueError(
                "❌ NYTIMES_API_KEY no encontrada. "
                "Crea un archivo .env con: NYTIMES_API_KEY=tu_clave_aquí"
            )


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instancia cacheada de Settings.
    Usa lru_cache para no recargar el archivo .env en cada request.
    """
    settings = Settings()
    return settings
