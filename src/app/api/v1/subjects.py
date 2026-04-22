"""Subject management endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services.subject import SubjectService

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.post(
    "",
    response_model=SuccessResponse[SubjectResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def create_subject(
    body: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new subject for the authenticated user.

    Accepts name, optional color_id, and optional description.
    Returns 201 Created with subject data.

    **Validates: Requirements 8, 20, 21, 22**
    """
    try:
        subject = await SubjectService.create_subject(
            db=db,
            user_id=current_user.id,
            name=body.name,
            color_id=body.color_id,
            description=body.description,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": str(exc),
            },
        )

    return SuccessResponse(
        data=SubjectResponse.model_validate(subject),
        message="Subject created successfully",
    )


@router.get(
    "",
    response_model=SuccessResponse[List[SubjectResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def list_subjects(
    limit: int = Query(default=50, ge=1, le=50, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    sort: str = Query(default="created_at", description="Sort field: created_at or name"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    List all subjects owned by the authenticated user with pagination.

    Supports limit, offset, and sort (created_at, name) parameters.

    **Validates: Requirements 8, 20, 21, 22**
    """
    if sort not in ("created_at", "name"):
        sort = "created_at"

    subjects, total = await SubjectService.list_subjects(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        sort=sort,
    )

    return SuccessResponse(
        data=[SubjectResponse.model_validate(s) for s in subjects],
        total=total,
        message="Subjects retrieved successfully",
    )


@router.patch(
    "/{subject_id}",
    response_model=SuccessResponse[SubjectResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def update_subject(
    subject_id: UUID,
    body: SubjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update a subject by ID.

    Only the owner can update their subject. Returns 403 if not owner.

    **Validates: Requirements 9, 19, 20**
    """
    subject = await SubjectService.get_subject(db=db, subject_id=subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Subject with id {subject_id} not found",
            },
        )

    if subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to update this subject",
            },
        )

    try:
        subject = await SubjectService.update_subject(
            db=db,
            subject=subject,
            name=body.name,
            color_id=body.color_id,
            description=body.description,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": str(exc),
            },
        )

    return SuccessResponse(
        data=SubjectResponse.model_validate(subject),
        message="Subject updated successfully",
    )


@router.delete(
    "/{subject_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def delete_subject(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a subject by ID.

    Only the owner can delete their subject. Returns 403 if not owner.
    Cascade deletes all associated topics, notes, and materials via DB constraints.

    **Validates: Requirements 9, 19, 20**
    """
    subject = await SubjectService.get_subject(db=db, subject_id=subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Subject with id {subject_id} not found",
            },
        )

    if subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to delete this subject",
            },
        )

    await SubjectService.delete_subject(db=db, subject=subject)
    await db.commit()

    return SuccessResponse(data=None, message="Subject deleted successfully")
