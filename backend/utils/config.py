import os
import dotenv
from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_ENV: str
    SEC_CIK: str = "789019"  # Microsoft default

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
