from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.security import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin123")


class LoginResponse(BaseModel):
    success: bool
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    tags=["Authentication"],
)
async def login(request: LoginRequest):
    """
    Authenticate user and issue JWT bearer token.
    Supports Enterprise Admin and Employee roles from environment configuration.
    """
    if request.username == settings.ADMIN_USERNAME and request.password == settings.ADMIN_PASSWORD:
        role = "Admin"
    elif request.username == settings.EMPLOYEE_USERNAME and request.password == settings.EMPLOYEE_PASSWORD:
        role = "Employee"
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password credentials."
        )

    token = create_access_token(user_id=request.username, role=role)


    return LoginResponse(
        success=True,
        access_token=token,
        token_type="bearer",
        user={
            "username": request.username,
            "email": f"{request.username}@queryreform.ai",
            "role": role,
        },
    )
