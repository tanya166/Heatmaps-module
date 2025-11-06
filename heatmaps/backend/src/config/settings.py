from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "heatmap_db"
    port: int = 8000
    detector_model_path: str = "models/person-detection-retail-0013.xml"
    reid_model_path: str = "models/person-reidentification-retail-0287.xml"
    
    class Config:
        env_file = ".env"

settings = Settings()