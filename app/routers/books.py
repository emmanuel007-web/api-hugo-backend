"""
Router: NYTimes Books API - Endpoints 1-4
FIXES: null safety (or {} / or []), example->examples, regex->pattern
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.config import get_settings
from app.http_client import fetch_nyt

router = APIRouter()
settings = get_settings()
BASE = settings.NYT_BOOKS_BASE_URL


@router.get("/overview", summary="📋 Endpoint 1: Overview de todas las listas")
async def get_overview(
    published_date: Optional[str] = Query(
        None,
        description="Fecha de publicación (YYYY-MM-DD). Si se omite, devuelve la semana actual.",
        examples=["2024-01-07"]
    )
):
    """
    Endpoint 1: Overview completo de todas las listas best-sellers.
    El NYTimes tiene datos históricos desde aproximadamente 2008.
    Fechas anteriores devolverán un error con mensaje amigable.
    """
    params = {}
    if published_date:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", published_date):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_DATE",
                    "message": "Formato de fecha inválido",
                    "detail": "Usa el formato YYYY-MM-DD (ej. 2024-01-07)"
                }
            )
        params["published_date"] = published_date

    url = f"{BASE}/lists/overview.json"
    data = await fetch_nyt(url, params)

    # FIX clave: usar `or {}` y `or []` — el NYT puede devolver None
    # para fechas sin datos (muy antiguas o fuera de rango)
    results = data.get("results") or {}
    lists_raw = results.get("lists") or []

    if not lists_raw and published_date:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NO_DATA_FOR_DATE",
                "message": f"No hay datos de best-sellers para la fecha '{published_date}'",
                "detail": (
                    "El NYTimes solo tiene datos históricos desde aproximadamente 2008. "
                    "Prueba con una fecha más reciente, por ejemplo: 2020-01-05 o 2023-06-11"
                )
            }
        )

    lists_normalized = []
    for lst in lists_raw:
        books = []
        for book in (lst.get("books") or []):
            books.append({
                "rank": book.get("rank"),
                "title": book.get("title"),
                "author": book.get("author"),
                "description": book.get("description"),
                "publisher": book.get("publisher"),
                "book_image": book.get("book_image"),
                "amazon_product_url": book.get("amazon_product_url"),
                "primary_isbn13": book.get("primary_isbn13"),
                "weeks_on_list": book.get("weeks_on_list", 0),
                "rank_last_week": book.get("rank_last_week", 0),
            })
        lists_normalized.append({
            "list_id": lst.get("list_id"),
            "list_name": lst.get("list_name"),
            "list_name_encoded": lst.get("list_name_encoded"),
            "display_name": lst.get("display_name"),
            "updated": lst.get("updated"),
            "books": books
        })

    return {
        "status": "success",
        "endpoint": "overview",
        "bestsellers_date": results.get("bestsellers_date"),
        "published_date": results.get("published_date"),
        "published_date_description": results.get("published_date_description"),
        "num_lists": len(lists_normalized),
        "lists": lists_normalized
    }


@router.get("/current/{list_name}", summary="📗 Endpoint 2: Lista específica actual")
async def get_current_list(
    list_name: str,
    offset: Optional[int] = Query(None, description="Offset para paginación (múltiplo de 20)", ge=0)
):
    """Endpoint 2: Lista específica actual por nombre (ej. hardcover-fiction)."""
    list_name_clean = list_name.strip().lower().replace(" ", "-")
    params = {}
    if offset is not None:
        params["offset"] = offset

    url = f"{BASE}/lists/current/{list_name_clean}.json"
    data = await fetch_nyt(url, params)

    results = data.get("results") or {}
    books_raw = results.get("books") or []
    books = _normalize_books(books_raw)

    return {
        "status": "success",
        "endpoint": "current_list",
        "list_name": results.get("list_name"),
        "display_name": results.get("display_name"),
        "list_name_encoded": results.get("list_name_encoded"),
        "bestsellers_date": results.get("bestsellers_date"),
        "published_date": results.get("published_date"),
        "published_date_description": results.get("published_date_description"),
        "updated": results.get("updated"),
        "num_results": data.get("num_results", len(books)),
        "books": books
    }


@router.get("/history/{date}/{list_name}", summary="📅 Endpoint 3: Lista histórica por fecha o año")
async def get_historical_list(
    date: str,
    list_name: str,
    offset: Optional[int] = Query(None, description="Offset para paginación", ge=0)
):
    """
    Endpoint 3: Lista histórica por nombre y fecha (YYYY-MM-DD) o Año (YYYY).
    Si se provee solo un año, busca el primer domingo de ese año.
    """
    import re
    from datetime import datetime, timedelta

    target_date = date
    # Si es solo un año (4 dígitos)
    if re.match(r"^\d{4}$", date):
        year = int(date)
        # Encontrar el primer domingo de enero de ese año
        # 1 de enero
        d = datetime(year, 1, 1)
        # weekday(): Monday=0, Sunday=6.
        # Queremos llegar al primer domingo (6).
        days_to_sunday = (6 - d.weekday()) % 7
        first_sunday = d + timedelta(days=days_to_sunday)
        target_date = first_sunday.strftime("%Y-%m-%d")
    elif not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_DATE_FORMAT",
                "message": "Formato de fecha inválido. Usa YYYY o YYYY-MM-DD",
                "detail": f"Recibido: '{date}'"
            }
        )

    list_name_clean = list_name.strip().lower().replace(" ", "-")
    params = {}
    if offset is not None:
        params["offset"] = offset

    url = f"{BASE}/lists/{target_date}/{list_name_clean}.json"
    data = await fetch_nyt(url, params)

    results = data.get("results") or {}
    books_raw = results.get("books") or []
    books = _normalize_books(books_raw)

    return {
        "status": "success",
        "endpoint": "historical_list",
        "requested_date": date,
        "effective_date": target_date,
        "list_name": results.get("list_name"),
        "display_name": results.get("display_name"),
        "bestsellers_date": results.get("bestsellers_date"),
        "published_date": results.get("published_date"),
        "num_results": data.get("num_results", len(books)),
        "books": books
    }


@router.get("/nonfiction", summary="📘 Endpoint 4: Nonfiction combinada (impreso + ebook)")
async def get_nonfiction_combined():
    """Endpoint 4: Lista fija combined-print-and-e-book-nonfiction. Sin parámetros."""
    list_name = "combined-print-and-e-book-nonfiction"
    url = f"{BASE}/lists/current/{list_name}.json"
    data = await fetch_nyt(url, {})

    results = data.get("results") or {}
    books_raw = results.get("books") or []
    books = _normalize_books(books_raw)

    return {
        "status": "success",
        "endpoint": "nonfiction_combined",
        "description": "Lista combinada impreso + ebook de No Ficción",
        "list_name": results.get("list_name"),
        "display_name": results.get("display_name"),
        "bestsellers_date": results.get("bestsellers_date"),
        "published_date": results.get("published_date"),
        "num_results": data.get("num_results", len(books)),
        "books": books
    }


@router.get("/names", summary="📋 Listado de todos los nombres de listas")
async def get_list_names():
    """Obtiene todos los nombres de las listas de best-sellers disponibles."""
    url = f"{BASE}/lists/names.json"
    data = await fetch_nyt(url, {})
    return {
        "status": "success",
        "endpoint": "list_names",
        "num_results": data.get("num_results", 0),
        "results": data.get("results") or []
    }


def _normalize_books(books_raw: list) -> list:
    """Normaliza la estructura de libros. Usa `or []` para evitar TypeError con None."""
    books = []
    for book in (books_raw or []):
        buy_links = book.get("buy_links") or []
        books.append({
            "rank": book.get("rank"),
            "rank_last_week": book.get("rank_last_week", 0),
            "weeks_on_list": book.get("weeks_on_list", 0),
            "title": book.get("title", "Sin título"),
            "author": book.get("author", "Autor desconocido"),
            "description": book.get("description", ""),
            "publisher": book.get("publisher", ""),
            "book_image": book.get("book_image", ""),
            "book_image_width": book.get("book_image_width"),
            "book_image_height": book.get("book_image_height"),
            "amazon_product_url": book.get("amazon_product_url", ""),
            "primary_isbn13": book.get("primary_isbn13", ""),
            "primary_isbn10": book.get("primary_isbn10", ""),
            "buy_links": buy_links[:3],
            "sunday_review_link": book.get("sunday_review_link", ""),
            "article_chapter_link": book.get("article_chapter_link", ""),
        })
    return books
