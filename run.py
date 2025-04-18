import subprocess
import sys
import os
import time
import signal
from app.web import app as flask_app
from config.config import settings

def run_flask():
    flask_app.run(
        host=settings.FLASK_HOST,
        port=settings.FLASK_PORT,
        debug=True
    )

def run_both_services():
    # Запускаем FastAPI в отдельном процессе с помощью subprocess
    fastapi_cmd = f"{sys.executable} -m uvicorn app.api:app --host {settings.FASTAPI_HOST} --port {settings.FASTAPI_PORT}"
    fastapi_process = subprocess.Popen(
        fastapi_cmd, 
        shell=True, 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    print(f"FastAPI server running at http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
    
    # Даем время FastAPI запуститься
    time.sleep(2)
    
    try:
        # Запускаем Flask в текущем процессе
        print(f"Flask server running at http://{settings.FLASK_HOST}:{settings.FLASK_PORT}")
        run_flask()
    finally:
        # Корректно завершаем процесс FastAPI при выходе
        if fastapi_process:
            print("Shutting down FastAPI server...")
            os.killpg(os.getpgid(fastapi_process.pid), signal.SIGTERM)
            fastapi_process.wait()

if __name__ == "__main__":
    run_both_services() 