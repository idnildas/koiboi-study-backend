"""Note management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.topic import Topic
from app.models.user import User
from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.note import NoteCreate, NoteResponse, NoteUpdate
from app.services.note import NoteService

router = APIRouter(tags=["notes"])


# ---------------------------------------------------------------------------
# Nested routes: /topics/{topicId}/notes
# ---------------------------------------------------------------------------

@router.post(
    "/topics/{topic_id}/notes",
    response_model=SuccessResponse[NoteResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Topic not found"},
    },
)
async def create_note(
    topic_id: UUID,
    body: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new note under a topic.

    Validates topic exists and is owned by the authenticated user.
    Assigns a random tint if tint_id is not provided.

    **Validates: Requirements 12, 20, 21, 22**
    """
    topic = await NoteService.get_topic_for_user(
        db=db, topic_id=topic_id, user_id=current_user.id
    )
    if topic is None:
        # Distinguish between not found and forbidden
        result = await db.execute(select(Topic).where(Topic.id == topic_id))
        exists = result.scalar_one_or_none()
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": "RESOURCE_NOT_FOUND",
                    "message": f"Topic with id {topic_id} not found",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to create notes in this topic",
            },
        )

    try:
        note = await NoteService.create_note(
            db=db,
            topic_id=topic_id,
            title=body.title,
            body=body.body,
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
        data=NoteResponse.model_validate(note),
        message="Note created successfully",
    )


@router.get(
    "/topics/{topic_id}/notes",
    response_model=SuccessResponse[List[NoteResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Topic not found"},
    },
)
async def list_notes(
    topic_id: UUID,
    limit: int = Query(default=50, ge=1, le=50, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    sort: str = Query(
        default="created_at",
        description="Sort field: created_at or updated_at",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    List all notes for a topic with pagination and sorting.

    **Validates: Requirements 12, 20, 21, 22**
    """
    topic = await NoteService.get_topic_for_user(
        db=db, topic_id=topic_id, user_id=current_user.id
    )
    if topic is None:
        result = await db.execute(select(Topic).where(Topic.id == topic_id))
        exists = result.scalar_one_or_none()
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": "RESOURCE_NOT_FOUND",
                    "message": f"Topic with id {topic_id} not found",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to view notes in this topic",
            },
        )

    if sort not in ("created_at", "updated_at"):
        sort = "created_at"

    notes, total = await NoteService.list_notes(
        db=db,
        topic_id=topic_id,
        limit=limit,
        offset=offset,
        sort=sort,
    )

    return SuccessResponse(
        data=[NoteResponse.model_validate(n) for n in notes],
        total=total,
        message="Notes retrieved successfully",
    )


# ---------------------------------------------------------------------------
# Flat routes: /notes/{id}
# ---------------------------------------------------------------------------

@router.get(
    "/notes/{note_id}",
    response_model=SuccessResponse[NoteResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def get_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get a note by ID including scribbles.

    Verifies ownership via note → topic → subject chain.

    **Validates: Requirements 13, 19, 20**
    """
    note = await NoteService.get_note(db=db, note_id=note_id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Note with id {note_id} not found",
            },
        )

    # Verify ownership via topic → subject chain
    topic = await NoteService.get_topic_for_user(
        db=db, topic_id=note.topic_id, user_id=current_user.id
    )
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to access this note",
            },
        )

    return SuccessResponse(
        data=NoteResponse.model_validate(note),
        message="Note retrieved successfully",
    )


@router.patch(
    "/notes/{note_id}",
    response_model=SuccessResponse[NoteResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def update_note(
    note_id: UUID,
    body: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update a note by ID.

    Validates scribbles array structure. Verifies ownership via note → topic → subject chain.

    **Validates: Requirements 13, 19, 20, 21**
    """
    note = await NoteService.get_note(db=db, note_id=note_id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Note with id {note_id} not found",
            },
        )

    topic = await NoteService.get_topic_for_user(
        db=db, topic_id=note.topic_id, user_id=current_user.id
    )
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to update this note",
            },
        )

    # Serialize scribbles to plain dicts for JSONB storage
    scribbles_data: Optional[list] = None
    if body.scribbles is not None:
        scribbles_data = [s.model_dump() for s in body.scribbles]

    try:
        note = await NoteService.update_note(
            db=db,
            note=note,
            title=body.title,
            body=body.body,
            tint_id=body.tint_id,
            scribbles=scribbles_data,
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
        data=NoteResponse.model_validate(note),
        message="Note updated successfully",
    )


@router.delete(
    "/notes/{note_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def delete_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a note by ID.

    Associated snippets have note_id set to NULL via DB constraint (SET NULL).
    Verifies ownership via note → topic → subject chain.

    **Validates: Requirements 13, 19, 20**
    """
    note = await NoteService.get_note(db=db, note_id=note_id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Note with id {note_id} not found",
            },
        )

    topic = await NoteService.get_topic_for_user(
        db=db, topic_id=note.topic_id, user_id=current_user.id
    )
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to delete this note",
            },
        )

    await NoteService.delete_note(db=db, note=note)
    await db.commit()

    return SuccessResponse(data=None, message="Note deleted successfully")
