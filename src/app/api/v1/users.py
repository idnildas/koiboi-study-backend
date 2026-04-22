"""User profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get the current user's profile.

    Returns user profile including name, email, avatar selections, and timestamps.

    **Validates: Requirements 4, 20, 21**
    """
    user = await UserService.get_profile(db=db, user_id=current_user.id)
    return SuccessResponse(
        data=UserResponse.model_validate(user),
        message="Profile retrieved successfully",
    )


@router.patch(
    "/me",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid avatar IDs"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def update_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update the current user's profile.

    Accepts optional name and/or avatar selections. Validates that avatar IDs exist.

    **Validates: Requirements 4, 20, 21**
    """
    try:
        user = await UserService.update_profile(
            db=db,
            user_id=current_user.id,
            name=body.name,
            avatar_style_id=body.avatar_style_id,
            avatar_color_id=body.avatar_color_id,
        )
        await db.commit()
    except ValueError as exc:
        msg = str(exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": msg,
            },
        )

    return SuccessResponse(
        data=UserResponse.model_validate(user),
        message="Profile updated successfully",
    )
