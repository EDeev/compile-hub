from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="CompileHub API", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
