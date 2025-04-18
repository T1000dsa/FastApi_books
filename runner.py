import uvicorn 

from src.core.main import app


if __name__ == '__main__':
    uvicorn.run(
        'src.core.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
        )