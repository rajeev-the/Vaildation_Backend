from fastapi import FastAPI
from app.db.database import SessionLocal
from app.routers.upload import router as upload_router
from app.routers.chunk import router as chunk_router
from app.routers.validation_rule import router as rule_router
from app.routers.report import router as report_router

app = FastAPI()

@app.get("/")
async def root():
    
    return {"message": "Server Running"}
from fastapi import FastAPI

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    upload_router,
    prefix="/api/v1"
)

app.include_router(
    chunk_router,
    prefix="/api/v1"
)

app.include_router(
    rule_router,
    prefix="/api/v1"
)

app.include_router(
    report_router,
    prefix="/api/v1/reports"
)
