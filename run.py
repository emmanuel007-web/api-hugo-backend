#!/usr/bin/env python3
"""
Script de inicio del backend FastAPI.
Ejecutar desde la carpeta backend/:
  python run.py
O directamente con uvicorn:
  uvicorn app.main:app --reload --port 8000
"""

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()

    # Validar configuración antes de iniciar
    if not settings.NYT_API_KEY:
        print("❌ ERROR: NYTIMES_API_KEY no encontrada en .env")
        print("   1. Copia .env.example a .env")
        print("   2. Reemplaza TU_API_KEY_AQUI con tu clave real")
        print("   3. Obtén tu clave en: https://developer.nytimes.com/accounts/create")
        exit(1)

    print("=" * 60)
    print("🗽 NYTimes Books API Proxy - Backend FastAPI")
    print("=" * 60)
    print(f"✅ API Key configurada: {settings.NYT_API_KEY[:8]}...{settings.NYT_API_KEY[-4:]}")
    print(f"🌐 Servidor: http://localhost:8000")
    print(f"📖 Docs: http://localhost:8000/docs")
    print(f"🔄 Modo: desarrollo (hot-reload activado)")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,      # Hot-reload en desarrollo
        log_level="info"
    )
