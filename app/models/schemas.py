"""
=============================================================================
Modelos Pydantic para validación de datos
=============================================================================
Define los esquemas de entrada y salida para todos los endpoints.
Pydantic valida automáticamente los tipos y formatos de datos.
=============================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# ---------------------------------------------------------------------------
# Modelos de Respuesta - representan la estructura de datos devuelta al frontend
# ---------------------------------------------------------------------------

class AuthorInfo(BaseModel):
    """Información simplificada de un autor destacado."""
    name: str
    book_count: int
    primary_list: Optional[str] = None


class BookItem(BaseModel):
    """Representa un libro individual dentro de una lista best-seller."""
    rank: Optional[int] = Field(None, description="Posición actual en la lista")
    rank_last_week: Optional[int] = Field(None, description="Posición la semana pasada")
    weeks_on_list: Optional[int] = Field(None, description="Semanas en la lista")
    title: Optional[str] = Field(None, description="Título del libro")
    author: Optional[str] = Field(None, description="Autor del libro")
    description: Optional[str] = Field(None, description="Descripción o sinopsis")
    publisher: Optional[str] = Field(None, description="Editorial")
    book_image: Optional[str] = Field(None, description="URL de la portada del libro")
    amazon_product_url: Optional[str] = Field(None, description="URL en Amazon")
    buy_links: Optional[List[dict]] = Field(None, description="Links de compra")
    primary_isbn13: Optional[str] = Field(None, description="ISBN-13 principal")
    primary_isbn10: Optional[str] = Field(None, description="ISBN-10 principal")
    found_in_lists: Optional[List[str]] = Field(default_factory=list, description="Listas donde aparece")


class BestSellerList(BaseModel):
    """Representa una lista de best-sellers (ej. hardcover-fiction)."""
    list_id: Optional[int] = None
    list_name: Optional[str] = None
    list_name_encoded: Optional[str] = None
    display_name: Optional[str] = None
    bestsellers_date: Optional[str] = None
    published_date: Optional[str] = None
    published_date_description: Optional[str] = None
    updated: Optional[str] = None
    books: Optional[List[BookItem]] = []


class OverviewResponse(BaseModel):
    """Respuesta del endpoint Overview - todas las listas actuales."""
    status: str
    bestsellers_date: Optional[str] = None
    published_date: Optional[str] = None
    num_lists: int
    lists: List[BestSellerList] = []


class ListResponse(BaseModel):
    """Respuesta de una lista específica (actual o histórica)."""
    status: str
    endpoint: str
    list_name: Optional[str] = None
    display_name: Optional[str] = None
    bestsellers_date: Optional[str] = None
    published_date: Optional[str] = None
    num_results: int
    books: List[BookItem] = []


class HistoryBookItem(BaseModel):
    """Representa un libro en el historial de best-sellers."""
    title: str
    author: str
    description: Optional[str] = ""
    publisher: Optional[str] = ""
    isbns: List[dict] = []
    ranks_history: List[dict] = []


class HistoryResponse(BaseModel):
    """Respuesta del endpoint de historial completo (Best Seller History API)."""
    status: str
    query: Optional[str] = None
    page: int
    total_results: int
    total_pages: int
    num_results: int
    books: List[HistoryBookItem] = []


class ReviewArticle(BaseModel):
    """Representa una reseña de libro del NYTimes (Critic Review)."""
    url: str
    publication_dt: Optional[str] = None
    byline: Optional[str] = None
    book_title: Optional[str] = None
    book_author: Optional[str] = None
    summary: Optional[str] = ""
    isbn13: List[str] = []


class ReviewResponse(BaseModel):
    """Respuesta del endpoint de búsqueda de reseñas críticas."""
    status: str
    num_results: int
    query_type: str
    query_value: str
    results: List[ReviewArticle] = []


class BestsellerSearchResponse(BaseModel):
    """Respuesta de búsqueda filtrada en best-sellers actuales."""
    status: str
    query: str
    search_type: str
    num_results: int
    books: List[BookItem] = []
    prominent_authors: List[AuthorInfo] = []


# ---------------------------------------------------------------------------
# Modelos de Request y Errores
# ---------------------------------------------------------------------------

class DateRequest(BaseModel):
    """Parámetros para consultas que requieren fecha."""
    date: str = Field(..., pattern=r"^\d{4}$|^\d{4}-\d{2}-\d{2}$") # Soporta YYYY o YYYY-MM-DD
    list_name: str


class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada."""
    status: str = "error"
    error_code: Optional[str] = None
    message: str
    detail: Optional[str] = None
