import os
import sys
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath("/app"))
sys.path.insert(0, os.path.abspath("/app/backend"))
# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery("omega_rag_worker")
celery.conf.broker_url = REDIS_URL
celery.conf.result_backend = REDIS_URL

# Explicitly discover tasks
celery.autodiscover_tasks(['worker.tasks'])

# Import Celery tasks
from worker.tasks import document_processing, rag_tasks

if __name__ == "__main__":
    celery.start()