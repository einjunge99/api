from fastapi import FastAPI
from api.v1.endpoints import lectures, users
from middlewares.cors import add_cors_middleware
from core.firebase import initialize_firebase

app = FastAPI()

initialize_firebase()


add_cors_middleware(app)

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(lectures.router, prefix="/api/v1/lectures", tags=["lectures"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8080, host="0.0.0.0")
