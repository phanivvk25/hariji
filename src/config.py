"""Central configuration management for the AI Agent system.
Supports multi-provider configuration (Google, OpenAI, Microsoft Azure, AWS Bedrock).
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from project root if present
load_dotenv()


class ProviderType(str, Enum):
    GOOGLE = "google"
    OPENAI = "openai"
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"
    CUSTOM = "custom"


class Settings:
    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    VECTOR_DB_DIR: Path = Path(os.getenv("VECTOR_DB_DIR", str(BASE_DIR / "data" / "vectordb")))
    DOCS_RAW_DIR: Path = Path(os.getenv("DOCS_RAW_DIR", str(BASE_DIR / "data" / "raw")))

    # Default Providers
    DEFAULT_LLM_PROVIDER: ProviderType = ProviderType(
        os.getenv("DEFAULT_LLM_PROVIDER", "google").lower()
    )
    DEFAULT_EMBEDDING_PROVIDER: ProviderType = ProviderType(
        os.getenv("DEFAULT_EMBEDDING_PROVIDER", "google").lower()
    )

    # 1. Google Gemini Config
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")

    # 2. OpenAI Config (Supports OpenAI or compatible local/cloud endpoints)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")

    # 3. Microsoft Azure OpenAI Config
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    # 4. Amazon AWS Bedrock Config
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_BEDROCK_MODEL_ID: str = os.getenv("AWS_BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    AWS_BEDROCK_EMBEDDING_MODEL_ID: str = os.getenv("AWS_BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")

    # General Agent Parameters
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))


# Global singleton settings
settings = Settings()

# Ensure directories exist
settings.VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
settings.DOCS_RAW_DIR.mkdir(parents=True, exist_ok=True)
