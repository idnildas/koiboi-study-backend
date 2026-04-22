"""Authentication endpoints for sign-up, sign-in, and password management."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.user import ChangePasswordRequest, UserCreate, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthData(BaseModel):
    """Response data containing JWT token and user profile."""

    token: str
    user: UserResponse


class SignInRequest(BaseModel):
    """Request body for sign-in."""

    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    """Request body for forgot-password."""

    email: str


class ResetPasswordRequest(BaseModel):
    """Request body for reset-password."""

    email: str
    token: str
    new_password: str


@router.post(
    "/sign-up",
    response_model=SuccessResponse[AuthData],
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        400: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def sign_up(
    body: UserCreate,
    db: AsyncSession = Depends(get_session),
):
    """
    Register a new user account.

    Accepts name, email, password, avatar_style_id, and avatar_color_id.
    Returns a JWT token and user profile on success.

    **Validates: Requirements 1, 20, 21**
    """
    try:
        user, token = await AuthService.sign_up(
            db=db,
            name=body.name,
            email=body.email,
            password=body.password,
            avatar_style_id=body.avatar_style_id,
            avatar_color_id=body.avatar_color_id,
        )
        await db.commit()
    except ValueError as exc:
        msg = str(exc)
        if "Email already registered" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "error": "EMAIL_CONFLICT",
                    "message": msg,
                },
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": msg,
            },
        )

    return SuccessResponse(
        data=AuthData(
            token=token,
            user=UserResponse.model_validate(user),
        ),
        message="Account created successfully",
    )


@router.post(
    "/sign-in",
    response_model=SuccessResponse[AuthData],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def sign_in(
    body: SignInRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    """
    Authenticate user with email and password.

    Returns a JWT token and user profile on success.
    Creates a session record with token, expiration, IP address, and user agent.

    **Validates: Requirements 2, 20, 21**
    """
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    try:
        user, token = await AuthService.sign_in(
            db=db,
            email=body.email,
            password=body.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "INVALID_CREDENTIALS",
                "message": str(exc),
            },
        )

    return SuccessResponse(
        data=AuthData(
            token=token,
            user=UserResponse.model_validate(user),
        ),
        message="Signed in successfully",
    )


@router.post(
    "/sign-out",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def sign_out(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Sign out the current user by deleting their session.

    **Validates: Requirements 2, 20**
    """
    token = authorization.split()[1] if authorization else ""

    try:
        await AuthService.sign_out(db=db, user_id=current_user.id, token=token)
        await db.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "SESSION_NOT_FOUND",
                "message": str(exc),
            },
        )

    return SuccessResponse(data=None, message="Signed out successfully")


@router.post(
    "/forgot-password",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Request a password reset token.

    Always returns 200 OK regardless of whether the email exists (security best practice).
    If the email exists, a cryptographically secure reset token is generated with a 1-hour expiration.

    **Validates: Requirements 3, 20, 21, 28**
    """
    await AuthService.forgot_password(db=db, email=body.email)
    await db.commit()

    return SuccessResponse(
        data=None,
        message="If that email is registered, a reset link has been sent",
    )


@router.post(
    "/reset-password",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Reset user password using a reset token.

    Validates the token, updates the password, marks the token as used,
    and invalidates all existing sessions.

    **Validates: Requirements 3, 4, 20, 21, 28**
    """
    try:
        await AuthService.reset_password(
            db=db,
            email=body.email,
            token=body.token,
            new_password=body.new_password,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "RESET_TOKEN_INVALID",
                "message": str(exc),
            },
        )

    return SuccessResponse(data=None, message="Password reset successfully")


@router.post(
    "/change-password",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Current password incorrect"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def change_password(
    body: ChangePasswordRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Change the current user's password.

    Verifies the current password before updating to the new password.

    **Validates: Requirements 4, 20, 21, 28**
    """
    try:
        await AuthService.change_password(
            db=db,
            user_id=current_user.id,
            current_password=body.current_password,
            new_password=body.new_password,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "PASSWORD_CHANGE_FAILED",
                "message": str(exc),
            },
        )

    return SuccessResponse(data=None, message="Password changed successfully")
