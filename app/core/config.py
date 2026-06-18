from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    DATABASE_URL:str
    
    ALEMBIC_DATABASE_URL: str

    JWT_SECRET:str

    ACCESS_TOKEN_EXPIRE_MINUTES:int

    MAX_UPLOAD_SIZE_MB:int

    CHUNK_ROW_THRESHOLD:int

    DEFAULT_COUNTRY:str
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = ""
    
    # S3 folder prefixes
    S3_UPLOADS_PREFIX: str = "uploads"
    S3_OUTPUTS_PREFIX: str = "outputs"
    S3_CHUNKS_PREFIX: str = "chunks"
    
    # Presigned URL expiration (in seconds)
    S3_PRESIGNED_URL_EXPIRATION: int = 3600

    class Config:
        env_file=".env"

settings=Settings()