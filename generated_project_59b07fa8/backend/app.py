# main.py
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints import router as v1_router
from app.auth import create_access_token, authenticate_user, get_current_user
from app.config import settings
from app.database import init_db, get_db
from app.schemas import Token, UserInDB, UserCreate
from app.crud import create_user as crud_create_user

app = FastAPI(
    title="Minimal Conversational Model API",
    description="A highly optimized, resource-efficient conversational model backend.",
    version="1.0.0",
)

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(v1_router, prefix="/api/v1", tags=["v1"])

@app.post("/token", response_model=Token, summary="Obtain JWT access token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user and returns a JWT access token.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserInDB, status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user in the system.
    """
    db_user = await crud_create_user(db, user)
    return db_user

@app.get("/users/me/", response_model=UserInDB, summary="Get current authenticated user")
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Retrieves information about the currently authenticated user.
    """
    return current_user

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

```
```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    SECRET_KEY: str = "super-secret-key" # In production, use a strong, randomly generated key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

```
```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

```
```python
# app/models.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

```