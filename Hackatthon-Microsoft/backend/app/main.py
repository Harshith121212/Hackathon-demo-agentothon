import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.api.routes import router as api_router, dispatcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run baseline fleet evaluation
    print(f"[{settings.PROJECT_NAME}] Starting up...")
    await dispatcher.run_full_fleet_evaluation()
    print(f"[{settings.PROJECT_NAME}] Initial fleet state evaluated successfully.")
    yield
    print(f"[{settings.PROJECT_NAME}] Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")


# WebSocket Endpoint
@app.websocket("/ws/fleet-stream")
async def websocket_endpoint(websocket: WebSocket):
    await dispatcher.connect(websocket)
    try:
        # Send immediate initial state
        assessments_list = [a.model_dump(mode="json") for a in dispatcher.assessments.values()]
        stats = {
            "total": len(assessments_list),
            "critical": sum(1 for a in assessments_list if a["risk_tier"] == "CRITICAL"),
            "high": sum(1 for a in assessments_list if a["risk_tier"] == "HIGH"),
            "watch": sum(1 for a in assessments_list if a["risk_tier"] == "WATCH"),
            "normal": sum(1 for a in assessments_list if a["risk_tier"] == "NORMAL"),
        }
        await websocket.send_json({
            "event": "INITIAL_STATE",
            "data": {
                "assessments": assessments_list,
                "stats": stats,
                "storms": dispatcher.weather_provider.fetch_active_storms_summary(),
                "incidents": [inc.model_dump(mode="json") for inc in dispatcher.incident_provider.get_all_active_incidents()],
                "metrics": dispatcher.metrics,
            }
        })
        while True:
            # Keep alive and receive incoming client commands
            data = await websocket.receive_text()
            # Respond to ping or client queries
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        dispatcher.disconnect(websocket)


# Mount Static Frontend
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir / "static")), name="static")

    @app.get("/")
    async def serve_spa_index():
        return FileResponse(str(frontend_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
