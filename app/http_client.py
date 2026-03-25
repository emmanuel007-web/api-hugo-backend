"""
=============================================================================
Cliente HTTP para comunicación con la API del NYTimes
=============================================================================
Centraliza todas las peticiones HTTP al NYT, maneja errores de red,
rate limiting y respuestas inesperadas de forma robusta.
=============================================================================
"""

import httpx
from fastapi import HTTPException
from app.config import get_settings

# Instancia de configuración (cacheada)
settings = get_settings()


async def fetch_nyt(url: str, params: dict) -> dict:
    """
    Realiza una petición GET asíncrona a la API del NYTimes.
    
    Args:
        url: URL completa del endpoint NYT
        params: Parámetros de query string (SIN la api-key, se añade aquí)
    
    Returns:
        dict: JSON de respuesta del NYT parseado
    
    Raises:
        HTTPException: Con código y mensaje apropiado según el error
    """

    # Validar que la API Key está configurada
    if not settings.NYT_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "API_KEY_MISSING",
                "message": "API Key no configurada en el servidor",
                "detail": "Verifica el archivo .env con NYTIMES_API_KEY=tu_clave"
            }
        )

    # Añadir la API Key a los parámetros (solo en el backend, nunca expuesta)
    params["api-key"] = settings.NYT_API_KEY

    try:
        # Cliente httpx asíncrono con timeout configurado
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            response = await client.get(url, params=params)

            # ---------------------------------------------------------------
            # Manejo de códigos de error HTTP específicos del NYT
            # ---------------------------------------------------------------

            if response.status_code == 200:
                # Éxito - retornar JSON parseado
                return response.json()

            elif response.status_code == 401:
                # API Key inválida o no proporcionada
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error_code": "INVALID_API_KEY",
                        "message": "API Key del NYTimes inválida o expirada",
                        "detail": "Verifica tu clave en developer.nytimes.com"
                    }
                )

            elif response.status_code == 403:
                # Acceso denegado (API no habilitada en la cuenta)
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error_code": "ACCESS_DENIED",
                        "message": "Acceso denegado. Verifica que Books API está habilitada",
                        "detail": "Ve a developer.nytimes.com > Your Apps > Enable Books API"
                    }
                )

            elif response.status_code == 404:
                # Recurso no encontrado (lista inexistente, fecha sin datos, etc.)
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "NOT_FOUND",
                        "message": "Recurso no encontrado",
                        "detail": f"URL: {url} | Verifica el nombre de la lista o la fecha"
                    }
                )

            elif response.status_code == 429:
                # Rate limit alcanzado (máximo 4000/día en cuenta gratuita)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error_code": "RATE_LIMIT",
                        "message": "Límite de peticiones alcanzado",
                        "detail": "NYTimes permite máximo 4000 peticiones/día y 10/minuto. Espera unos minutos."
                    }
                )

            elif response.status_code >= 500:
                # Error del servidor NYTimes
                raise HTTPException(
                    status_code=502,
                    detail={
                        "error_code": "NYT_SERVER_ERROR",
                        "message": "Error en los servidores del NYTimes",
                        "detail": f"Código HTTP: {response.status_code}. Intenta de nuevo más tarde."
                    }
                )

            else:
                # Código de error no esperado
                raise HTTPException(
                    status_code=response.status_code,
                    detail={
                        "error_code": "UNEXPECTED_ERROR",
                        "message": f"Error inesperado: HTTP {response.status_code}",
                        "detail": response.text[:200]
                    }
                )

    except httpx.TimeoutException:
        # Timeout de red - el NYT no respondió en tiempo
        raise HTTPException(
            status_code=504,
            detail={
                "error_code": "TIMEOUT",
                "message": "Tiempo de espera agotado conectando con NYTimes",
                "detail": f"El servidor no respondió en {settings.HTTP_TIMEOUT} segundos"
            }
        )

    except httpx.ConnectError:
        # Sin conexión a internet
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "CONNECTION_ERROR",
                "message": "No se pudo conectar con la API del NYTimes",
                "detail": "Verifica tu conexión a internet"
            }
        )

    except httpx.RequestError as exc:
        # Cualquier otro error de red
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "NETWORK_ERROR",
                "message": "Error de red al contactar NYTimes",
                "detail": str(exc)
            }
        )
