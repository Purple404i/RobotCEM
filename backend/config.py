import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent  # Points to /home/devlord/RobotCEM

CONFIG = {
	# Core Infrastructure
	"csharp_project_path": os.getenv("CSHARP_PROJECT_PATH", str(BASE_DIR / "csharp_runtime" / "RobotCEM")),
	"output_dir": os.getenv("OUTPUT_DIR", str(BASE_DIR / "backend" / "outputs")),
	"template_dir": os.getenv("TEMPLATE_DIR", str(BASE_DIR / "csharp_runtime" / "RobotCEM" / "Templates")),
	
	# Database & Caching (Tool System)
	"database_url": os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'robotcem.db'}"),
	"redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
	"enable_redis_cache": os.getenv("ENABLE_REDIS_CACHE", "false").lower() == "true",
	
	# Cloud Storage
	"s3_bucket": os.getenv("AWS_S3_BUCKET"),
	"aws_region": os.getenv("AWS_REGION", "us-east-1"),
	
	# Tool System Configuration (DuckDuckGo-based, no API keys required)
	"tool_cache_ttl": {
		"product_prices": int(os.getenv("TOOL_CACHE_PRODUCT_TTL", "3600")),  # 1 hour
		"material_prices": int(os.getenv("TOOL_CACHE_MATERIAL_TTL", "7200")),  # 2 hours
		"density_lookup": int(os.getenv("TOOL_CACHE_DENSITY_TTL", "604800")),  # 7 days
		"manufacturing_costs": int(os.getenv("TOOL_CACHE_MFG_TTL", "86400")),  # 1 day
		"exchange_rates": int(os.getenv("TOOL_CACHE_CURRENCY_TTL", "21600")),  # 6 hours
	},
	"tool_search_engine": "duckduckgo",  # No API key required, unlimited queries
	"tool_search_timeout": int(os.getenv("TOOL_SEARCH_TIMEOUT", "30")),
	"tool_max_retries": int(os.getenv("TOOL_MAX_RETRIES", "3")),
}

# Ensure output directory exists
Path(CONFIG["output_dir"]).mkdir(parents=True, exist_ok=True)

