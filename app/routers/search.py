"""
Router: NYTimes Article Search API - Endpoints 5-6
FIXES: example->examples, regex->pattern, null safety con `or`
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.config import get_settings
from app.http_client import fetch_nyt
from app.routers.books import _normalize_books

router = APIRouter()
settings = get_settings()

BOOKS_BASE = settings.NYT_BOOKS_BASE_URL
SEARCH_BASE = settings.NYT_SEARCH_BASE_URL


# ---------------------------------------------------------------------------
# ENDPOINT 5: Búsqueda en el HISTORIAL completo de Best-Sellers
# URL NYT: /svc/books/v3/lists/best-sellers/history.json
# ---------------------------------------------------------------------------
@router.get("/history", summary="🔍 Endpoint 5: Búsqueda en el historial completo de Best-Sellers")
async def search_best_seller_history(
    query: Optional[str] = Query(None, description="Título o autor a buscar"),
    author: Optional[str] = Query(None, description="Nombre del autor"),
    title: Optional[str] = Query(None, description="Título del libro"),
    page: int = Query(0, description="Página de resultados (offset = page * 20)", ge=0)
):
    """
    Endpoint 5: Búsqueda en todo el historial de libros que han sido best-sellers.
    Soporta búsqueda por título, autor o texto genérico.
    """
    params = {
        "offset": page * 20
    }
    if query:
        # Si hay query genérico, lo enviamos como 'author' o 'title'
        # Nota: La API del NYT prefiere campos específicos, pero aceptamos query por simplicidad
        params["author"] = query
    if author:
        params["author"] = author
    if title:
        params["title"] = title

    url = f"{BOOKS_BASE}/lists/best-sellers/history.json"
    data = await fetch_nyt(url, params)

    results = data.get("results") or []
    total_hits = data.get("num_results", 0)

    books = []
    for item in results:
        books.append({
            "title": item.get("title", "Sin título"),
            "author": item.get("author", "Autor desconocido"),
            "description": item.get("description", ""),
            "publisher": item.get("publisher", ""),
            "isbns": item.get("isbns") or [],
            "ranks_history": item.get("ranks_history") or []
        })

    return {
        "status": "success",
        "endpoint": "bestseller_history",
        "query": query or f"{author} {title}".strip(),
        "page": page,
        "total_results": total_hits,
        "total_pages": (total_hits - 1) // 20 + 1 if total_hits > 0 else 0,
        "num_results": len(books),
        "books": books
    }


# ---------------------------------------------------------------------------
# ENDPOINT 6: Búsqueda de BEST-SELLERS por autor o título + Autores Destacados
# ---------------------------------------------------------------------------
@router.get("/bestsellers", summary="🏆 Endpoint 6: Autores Populares No Ficción")
async def search_popular_nonfiction_authors(
    query: Optional[str] = Query(None, description="Filtrar autor por nombre")
):
    """
    Endpoint 6: Obtiene los autores más populares de la categoría Hardcover Nonfiction.
    Si se provee un 'query' con el nombre de autor, busca en el historial completo
    del NYT (history API) todos los libros de ese autor.
    """
    # 1. Obtener SIEMPRE la lista actual de hardcover-nonfiction para el ranking de autores
    url_current = f"{BOOKS_BASE}/lists/current/hardcover-nonfiction.json"
    data_current = await fetch_nyt(url_current, {})

    results_raw = data_current.get("results") or {}
    books_raw = results_raw.get("books") or []

    # Extraer autores y su popularidad (weeks_on_list)
    author_map = {}
    for book in books_raw:
        author = book.get("author", "Autor desconocido")
        weeks = book.get("weeks_on_list", 0)
        
        # Guardar el máximo de semanas visto para este autor
        if author not in author_map or weeks > author_map[author]:
            author_map[author] = weeks
            
    # Convertir mapa a lista y ordenar por semanas (popularidad)
    all_authors = []
    for auth, wks in author_map.items():
        all_authors.append({
            "name": auth,
            "book_count": wks, # Usamos book_count para representar "popularidad" en la interfaz
            "primary_list": "Hardcover Nonfiction"
        })
            
    # Ordenar autores por "popularidad" (semanas en lista)
    all_authors.sort(key=lambda x: x["book_count"], reverse=True)

    matched_books = []
    
    # 2. Si hay un query (nombre de autor), buscar sus libros en la misma lista actual
    query_lower = query.strip().lower() if query else None

    # Iterar de nuevo sobre la lista actual para extraer los libros del autor seleccionado
    if query_lower:
        for book in books_raw:
            author = book.get("author", "Autor desconocido")
            if query_lower in author.lower():
                matched_books.append({
                    "rank": book.get("rank"),
                    "title": book.get("title", "Sin título"),
                    "author": author,
                    "description": book.get("description", ""),
                    "publisher": book.get("publisher", ""),
                    "primary_isbn13": book.get("primary_isbn13", ""),
                    "book_image": book.get("book_image", ""),
                    "weeks_on_list": book.get("weeks_on_list", 0),
                    # Para compatibilidad con frontend
                    "found_in_lists": ["Hardcover Nonfiction"]
                })

    return {
        "status": "success",
        "endpoint": "popular_authors_nonfiction",
        "query": query,
        "num_results": len(matched_books),
        "books": matched_books,
        "prominent_authors": all_authors # Estos aparecerán en la sección "Autores destacados"
    }


# ---------------------------------------------------------------------------
# ENDPOINT 7: Búsqueda de Reseñas Críticas (NYT Critic Reviews)
# URL NYT: /svc/books/v3/reviews.json
# ---------------------------------------------------------------------------
@router.get("/reviews", summary="🗞️ Endpoint 7: Búsqueda de reseñas críticas")
async def search_critic_reviews(
    title: Optional[str] = Query(None, description="Título del libro"),
    author: Optional[str] = Query(None, description="Autor del libro"),
    isbn: Optional[str] = Query(None, description="ISBN-13 o ISBN-10"),
):
    """
    Endpoint 7: Obtiene reseñas críticas oficiales escritas por el NYTimes.
    Requiere al menos uno de los parámetros: title, author o isbn.
    """
    if not any([title, author, isbn]):
        raise HTTPException(
            status_code=400,
            detail={"error_code": "MISSING_PARAMS", "message": "Debes proveer al menos: título, autor o isbn"}
        )

    params = {}
    if isbn: params["isbn"] = isbn
    if title: params["title"] = title
    if author: params["author"] = author

    url = f"{BOOKS_BASE}/reviews.json"
    data = await fetch_nyt(url, params)

    results_raw = data.get("results") or []
    
    # Normalizar resultados
    processed_reviews = []
    for r in results_raw:
        processed_reviews.append({
            "url": r.get("url", ""),
            "publication_dt": r.get("publication_dt"),
            "byline": r.get("byline", ""),
            "book_title": r.get("book_title", ""),
            "book_author": r.get("book_author", ""),
            "summary": r.get("summary", ""),
            "isbn13": r.get("isbn13") or []
        })

    return {
        "status": "success",
        "num_results": data.get("num_results", len(processed_reviews)),
        "query_type": "isbn" if isbn else ("title" if title else "author"),
        "query_value": isbn or title or author,
        "results": processed_reviews
    }
