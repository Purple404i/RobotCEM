import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

CONFIG = {
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    "octopart_api_key": os.getenv("OCTOPART_API_KEY"),
    "digikey_client_id": os.getenv("DIGIKEY_CLIENT_ID"),
    "digikey_client_secret": os.getenv("DIGIKEY_CLIENT_SECRET"),
    "csharp_project_path": os.getenv("CSHARP_PROJECT_PATH", "../csharp_runtime/RobotCEM"),
    "output_dir": os.getenv("OUTPUT_DIR", str(BASE_DIR / "outputs")),
    "template_dir": os.getenv("TEMPLATE_DIR", "../csharp_runtime/RobotCEM/Templates"),
    "database_url": os.getenv("DATABASE_URL", "sqlite:///./robotcem.db"),
    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "s3_bucket": os.getenv("AWS_S3_BUCKET"),
    "aws_region": os.getenv("AWS_REGION", "us-east-1"),
}

# Ensure output directory exists
Path(CONFIG["output_dir"]).mkdir(parents=True, exist_ok=True)
