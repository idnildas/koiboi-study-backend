"""Playground snippet endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.snippet import SnippetCreate, SnippetResponse, SnippetUpdate
from app.services.snippet import SnippetService

router = APIRouter(prefix="/snippets", tags=["snippets"])


@router.post(
    "",
    response_model=SuccessResponse[SnippetResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    },
)
async def create_snippet(
    body: SnippetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new playground snippet.

    Validates language and code are not empty. If note_id is provided,
    validates the note exists and the user owns it.

    **Validates: Requirements 16, 20, 21, 22**
    """
    try:
        snippet = await SnippetService.create_snippet(
            db=db,
            user_id=current_user.id,
            language=body.language,
            code=body.code,
            note_id=body.note_id,
        )
        await db.commit()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": "Note not found",
            },
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to associate this note",
            },
        )

    return SuccessResponse(
        data=SnippetResponse.model_validate(snippet),
        message="Snippet created successfully",
    )


@router.get(
    "",
    response_model=SuccessResponse[List[SnippetResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def list_snippets(
    limit: int = Query(default=50, ge=1, le=50, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    language: Optional[str] = Query(default=None, description="Filter by language"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    List all snippets owned by the authenticated user.

    Supports pagination and optional language filter. Sorted by created_at descending.

    **Validates: Requirements 16, 20, 21, 22**
    """
    snippets, total = await SnippetService.list_snippets(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        language=language,
    )

    return SuccessResponse(
        data=[SnippetResponse.model_validate(s) for s in snippets],
        total=total,
        message="Snippets retrieved successfully",
    )


@router.patch(
    "/{snippet_id}",
    response_model=SuccessResponse[SnippetResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def update_snippet(
    snippet_id: UUID,
    body: SnippetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update a snippet's code and/or output.

    Verifies the authenticated user owns the snippet.

    **Validates: Requirements 17, 19, 20**
    """
    snippet = await SnippetService.get_snippet(db=db, snippet_id=snippet_id)
    if snippet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Snippet with id {snippet_id} not found",
            },
        )

    if snippet.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to update this snippet",
            },
        )

    snippet = await SnippetService.update_snippet(
        db=db,
        snippet=snippet,
        code=body.code,
        output=body.output,
    )
    await db.commit()

    return SuccessResponse(
        data=SnippetResponse.model_validate(snippet),
        message="Snippet updated successfully",
    )


@router.delete(
    "/{snippet_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def delete_snippet(
    snippet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a snippet by ID.

    Verifies the authenticated user owns the snippet.

    **Validates: Requirements 17, 19, 20**
    """
    snippet = await SnippetService.get_snippet(db=db, snippet_id=snippet_id)
    if snippet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Snippet with id {snippet_id} not found",
            },
        )

    if snippet.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to delete this snippet",
            },
        )

    await SnippetService.delete_snippet(db=db, snippet=snippet)
    await db.commit()

    return SuccessResponse(data=None, message="Snippet deleted successfully")
