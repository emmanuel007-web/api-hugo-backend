"""
=============================================================================
NYTimes Books API - Backend Proxy con FastAPI
=============================================================================
Este servidor actúa como proxy seguro entre el frontend Angular y la API
del New York Times, manteniendo la API Key protegida en el servidor.

Autor: Ejercicio Full-Stack Senior
Stack: Python 3.11+ | FastAPI | Uvicorn | python-dotenv | httpx
=============================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import books, search

# ---------------------------------------------------------------------------
# Inicialización de la aplicación FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="NYTimes Books API Proxy",
    description="""
    Proxy seguro para la API de Libros del New York Times.
    Protege la API Key del cliente y expone endpoints limpios al frontend Angular.
    
    ## Endpoints implementados
    - **Overview**: Todas las listas best-sellers actuales o por fecha
    - **Lista Actual**: Lista específica por nombre (ej. hardcover-fiction)
    - **Lista Histórica**: Lista por nombre y fecha específica
    - **Lista Nonfiction**: Lista actual de no-ficción combinada
    - **Reseñas**: Búsqueda de reseñas literarias (Article Search API)
    - **Best-sellers por Autor/Título**: Búsqueda filtrada en best-sellers
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ---------------------------------------------------------------------------
# Configuración de CORS - permite peticiones desde Angular (localhost:4200)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",   # Angular dev server
        ""
    
        "https://apihugofrontend.vercel.app", # Angular en producción (Vercel)
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Inclusión de routers modulares (libros y búsqueda)
# ---------------------------------------------------------------------------
app.include_router(books.router, prefix="/api/books", tags=["📚 Books API"])
app.include_router(search.router, prefix="/api/search", tags=["🔍 Article Search API"])


# ---------------------------------------------------------------------------
# Endpoint raíz - health check
# ---------------------------------------------------------------------------
@app.get("/", summary="Health Check")
async def root():
    """
    Endpoint de verificación de estado del servidor.
    Confirma que el proxy está corriendo correctamente.
    """
    return {
        "status": "✅ NYTimes Books API Proxy activo",
        "version": "1.0.0",
        "endpoints": {
            "books": "/api/books",
            "search": "/api/search",
            "docs": "/docs"
        }
    }
