"""Topic management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate
from app.services.topic import TopicService

router = APIRouter(tags=["topics"])


# ---------------------------------------------------------------------------
# Nested routes: /subjects/{subjectId}/topics
# ---------------------------------------------------------------------------

@router.post(
    "/subjects/{subject_id}/topics",
    response_model=SuccessResponse[TopicResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Subject not found"},
    },
)
async def create_topic(
    subject_id: UUID,
    body: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new topic under a subject.

    Validates subject exists and is owned by the authenticated user.
    Assigns a random tint if tint_id is not provided.

    **Validates: Requirements 10, 20, 21, 22**
    """
    subject = await TopicService.get_subject_for_user(
        db=db, subject_id=subject_id, user_id=current_user.id
    )
    if subject is None:
        # Distinguish between not found and forbidden
        from sqlalchemy import select
        from app.models.subject import Subject
        result = await db.execute(select(Subject).where(Subject.id == subject_id))
        exists = result.scalar_one_or_none()
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": "RESOURCE_NOT_FOUND",
                    "message": f"Subject with id {subject_id} not found",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to create topics in this subject",
            },
        )

    try:
        topic = await TopicService.create_topic(
            db=db,
            subject_id=subject_id,
            name=body.name,
            tint_id=body.tint_id,
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
        data=TopicResponse.model_validate(topic),
        message="Topic created successfully",
    )


@router.get(
    "/subjects/{subject_id}/topics",
    response_model=SuccessResponse[List[TopicResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Subject not found"},
    },
)
async def list_topics(
    subject_id: UUID,
    limit: int = Query(default=50, ge=1, le=50, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by status: not-started, in-progress, revising, completed",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    List all topics for a subject with pagination and optional status filter.

    **Validates: Requirements 10, 20, 21, 22**
    """
    subject = await TopicService.get_subject_for_user(
        db=db, subject_id=subject_id, user_id=current_user.id
    )
    if subject is None:
        from sqlalchemy import select
        from app.models.subject import Subject
        result = await db.execute(select(Subject).where(Subject.id == subject_id))
        exists = result.scalar_one_or_none()
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": "RESOURCE_NOT_FOUND",
                    "message": f"Subject with id {subject_id} not found",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to view topics in this subject",
            },
        )

    topics, total = await TopicService.list_topics(
        db=db,
        subject_id=subject_id,
        limit=limit,
        offset=offset,
        status=status_filter,
    )

    return SuccessResponse(
        data=[TopicResponse.model_validate(t) for t in topics],
        total=total,
        message="Topics retrieved successfully",
    )


# ---------------------------------------------------------------------------
# Flat routes: /topics/{id}
# ---------------------------------------------------------------------------

@router.patch(
    "/topics/{topic_id}",
    response_model=SuccessResponse[TopicResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def update_topic(
    topic_id: UUID,
    body: TopicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update a topic by ID.

    Verifies ownership via the parent subject. Returns 403 if not owner.

    **Validates: Requirements 11, 19, 20**
    """
    result = await TopicService.get_topic_with_subject(db=db, topic_id=topic_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Topic with id {topic_id} not found",
            },
        )

    topic, subject = result
    if subject is None or subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to update this topic",
            },
        )

    try:
        topic = await TopicService.update_topic(
            db=db,
            topic=topic,
            name=body.name,
            status=body.status,
            confidence=body.confidence,
            tint_id=body.tint_id,
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
        data=TopicResponse.model_validate(topic),
        message="Topic updated successfully",
    )


@router.delete(
    "/topics/{topic_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def delete_topic(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a topic by ID.

    Verifies ownership via the parent subject. Cascade deletes all notes.

    **Validates: Requirements 11, 19, 20**
    """
    result = await TopicService.get_topic_with_subject(db=db, topic_id=topic_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Topic with id {topic_id} not found",
            },
        )

    topic, subject = result
    if subject is None or subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to delete this topic",
            },
        )

    await TopicService.delete_topic(db=db, topic=topic)
    await db.commit()

    return SuccessResponse(data=None, message="Topic deleted successfully")
