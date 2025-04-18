from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import SearchRequest, SearchResponse
from services.yandex_search import YandexSearchService
from config.config import settings

app = FastAPI(
    title="Supplier Search API",
    description="API для поиска и валидации поставщиков",
    version="1.0.0"
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yandex_service = YandexSearchService()

@app.get("/")
async def root():
    """
    Корневой маршрут для проверки работоспособности API
    """
    return {
        "status": "ok",
        "message": "Supplier Search API is running",
        "docs_url": "/docs",
        "endpoints": {
            "search": "/search"
        }
    }

@app.post("/search", response_model=SearchResponse)
async def search_companies(request: SearchRequest):
    """
    Поиск компаний по категории и местоположению
    
    - **category**: Категория или тип бизнеса (например, "строительные материалы")
    - **location**: Местоположение (например, "Москва")
    """
    try:
        results = await yandex_service.search_companies(
            category=request.category,
            location=request.location
        )
        return SearchResponse(companies=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT
    ) 