# Imports
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import select, String, ForeignKey, DateTime, func, Boolean
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, date

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./app.db"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Base model for SQLAlchemy
class Base(DeclarativeBase):
    pass

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending") # e.g., "pending", "completed", "in_progress"
    due_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', user_id={self.user_id})>"

# Pydantic Schemas
# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Task Schemas
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: str = Field("pending", pattern="^(pending|completed|in_progress)$")
    due_date: Optional[date] = None

class TaskCreate(TaskBase):
    user_id: int

class TaskUpdate(TaskBase):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, pattern="^(pending|completed|in_progress)$")
    user_id: Optional[int] = None # Allow changing task owner, though often not desired in real apps

class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# FastAPI app with CORS
app = FastAPI(
    title="Task Management API",
    description="A simple task management API with users and tasks.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection for database sessions
async def get_db():
    """
    Dependency that provides a database session for each request.
    """
    async with AsyncSessionLocal() as session:
        yield session

# Root endpoint
@app.get("/", response_model=dict, summary="API Root")
async def read_root():
    """
    Returns basic information about the API.
    """
    return {"message": "Welcome to the Task Management API!", "version": app.version}

# Health check endpoint
@app.get("/health", response_model=dict, summary="Health Check")
async def health_check():
    """
    Checks the health of the API.
    """
    return {"status": "ok", "timestamp": datetime.now()}

# User CRUD Endpoints

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create a new user")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new user with the provided username and email.
    """
    db_user = User(username=user.username, email=user.email)
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username or email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e}"
        )
    return db_user

@app.get("/users/", response_model=List[UserResponse], summary="Retrieve all users")
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves a list of all users with optional pagination.
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@app.get("/users/{user_id}", response_model=UserResponse, summary="Retrieve a single user by ID")
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a single user by their unique ID.
    """
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserResponse, summary="Update an existing user")
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    """
    Updates an existing user's information. Fields not provided will remain unchanged.
    """
    db_user = await db.get(User, user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    try:
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another user with this username or email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_S_ERROR,
            detail=f"Failed to update user: {e}"
        )
    return db_user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a user by their ID. All associated tasks will also be deleted.
    """
    db_user = await db.get(User, user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(db_user)
    await db.commit()
    return

# Task CRUD Endpoints

@app.post("/tasks/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Create a new task")
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new task associated with a specific user.
    """
    user = await db.get(User, task.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_task = Task(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskResponse], summary="Retrieve all tasks")
async def read_tasks(
    user_id: Optional[int] = Query(None, description="Filter tasks by user ID"),
    status_filter: Optional[str] = Query(None, description="Filter tasks by status (pending, completed, in_progress)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves a list of all tasks with optional filtering by user ID and status, and pagination.
    """
    query = select(Task)
    if user_id:
        query = query.where(Task.user_id == user_id)
    if status_filter:
        if status_filter not in ["pending", "completed", "in_progress"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid status filter. Must be 'pending', 'completed', or 'in_progress'."
            )
        query = query.where(Task.status == status_filter)

    result = await db.execute(query.offset(skip).limit(limit))
    tasks = result.scalars().all()
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskResponse, summary="Retrieve a single task by ID")
async def read_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a single task by its unique ID.
    """
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse, summary="Update an existing task")
async def update_task(task_id: int, task_update: TaskUpdate, db: AsyncSession = Depends(get_db)):
    """
    Updates an existing task's information. Fields not provided will remain unchanged.
    """
    db_task = await db.get(Task, task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)

    if "user_id" in update_data and update_data["user_id"] is not None:
        user = await db.get(User, update_data["user_id"])
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New user_id for task not found")

    for key, value in update_data.items():
        setattr(db_task, key, value)

    await db.commit()
    await db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a task")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a task by its ID.
    """
    db_task = await db.get(Task, task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await db.delete(db_task)
    await db.commit()
    return

# Startup event
@app.on_event("startup")
async def startup():
    """
    Initializes the database by creating all tables defined in Base.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)