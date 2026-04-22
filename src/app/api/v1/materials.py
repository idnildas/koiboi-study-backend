"""Material management endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.material import Material
from app.models.subject import Subject
from app.models.user import User
from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.material import MaterialResponse, MaterialUpdate
from app.services.material import MaterialService
from app.services.storage import StorageService

router = APIRouter(tags=["materials"])

# Maximum allowed file size: 100 MB
MAX_FILE_SIZE = 100 * 1024 * 1024


# ---------------------------------------------------------------------------
# Nested routes: /subjects/{subjectId}/materials
# ---------------------------------------------------------------------------

@router.post(
    "/subjects/{subject_id}/materials",
    response_model=SuccessResponse[MaterialResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Subject not found"},
        413: {"model": ErrorResponse, "description": "Payload too large"},
        422: {"model": ErrorResponse, "description": "Unprocessable entity"},
    },
)
async def upload_material(
    subject_id: UUID,
    title: str = Form(..., min_length=1, max_length=255),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Upload a PDF material to a subject.

    Accepts multipart/form-data with a title field and a PDF file.
    Validates subject ownership, file type (PDF), and file size (≤ 100 MB).

    **Validates: Requirements 14, 24, 20, 21**
    """
    # Validate title is not blank
    if not title or not title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": "Title cannot be empty",
            },
        )

    # Validate subject exists
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Subject with id {subject_id} not found",
            },
        )

    # Validate ownership
    if subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to upload materials to this subject",
            },
        )

    # Validate MIME type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": "Only PDF files are accepted (application/pdf)",
            },
        )

    # Read file content and validate size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "success": False,
                "error": "PAYLOAD_TOO_LARGE",
                "message": "File size exceeds the maximum allowed size of 100 MB",
            },
        )

    file_name = file.filename or "upload.pdf"

    material = await MaterialService.create_material(
        db=db,
        subject_id=subject_id,
        user_id=current_user.id,
        title=title.strip(),
        file_name=file_name,
        file_content=file_content,
        mime_type="application/pdf",
    )
    await db.commit()

    return SuccessResponse(
        data=MaterialResponse.model_validate(material),
        message="Material uploaded successfully",
    )


@router.get(
    "/subjects/{subject_id}/materials",
    response_model=SuccessResponse[List[MaterialResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Subject not found"},
    },
)
async def list_materials(
    subject_id: UUID,
    limit: int = Query(default=50, ge=1, le=50, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    List all materials for a subject with pagination.

    **Validates: Requirements 15, 20, 21, 22**
    """
    # Validate subject exists
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Subject with id {subject_id} not found",
            },
        )

    # Validate ownership
    if subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to view materials for this subject",
            },
        )

    materials, total = await MaterialService.list_materials(
        db=db,
        subject_id=subject_id,
        limit=limit,
        offset=offset,
    )

    return SuccessResponse(
        data=[MaterialResponse.model_validate(m) for m in materials],
        total=total,
        message="Materials retrieved successfully",
    )


# ---------------------------------------------------------------------------
# Flat routes: /materials/{id}
# ---------------------------------------------------------------------------

@router.patch(
    "/materials/{material_id}",
    response_model=SuccessResponse[MaterialResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def update_material(
    material_id: UUID,
    body: MaterialUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update material metadata (title and/or page_count).

    Verifies ownership via material → subject chain.

    **Validates: Requirements 15, 20, 21, 22**
    """
    material = await MaterialService.get_material(db=db, material_id=material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Material with id {material_id} not found",
            },
        )

    # Verify ownership via subject
    result = await db.execute(select(Subject).where(Subject.id == material.subject_id))
    subject = result.scalar_one_or_none()
    if subject is None or subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to update this material",
            },
        )

    material = await MaterialService.update_material(
        db=db,
        material=material,
        title=body.title,
        page_count=body.page_count,
    )
    await db.commit()

    return SuccessResponse(
        data=MaterialResponse.model_validate(material),
        message="Material updated successfully",
    )


@router.get(
    "/materials/{material_id}/download",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def download_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Download a material PDF file.

    Returns the file with Content-Type: application/pdf and
    Content-Disposition: attachment headers.

    **Validates: Requirements 14, 24, 20**
    """
    material = await MaterialService.get_material(db=db, material_id=material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Material with id {material_id} not found",
            },
        )

    # Verify ownership via subject
    result = await db.execute(select(Subject).where(Subject.id == material.subject_id))
    subject = result.scalar_one_or_none()
    if subject is None or subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to download this material",
            },
        )

    try:
        file_content = StorageService.get_file(material.storage_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": "File not found in storage",
            },
        )

    return Response(
        content=file_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{material.file_name}"',
        },
    )


@router.delete(
    "/materials/{material_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
async def delete_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a material and its associated file from storage.

    **Validates: Requirements 14, 24, 20**
    """
    material = await MaterialService.get_material(db=db, material_id=material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Material with id {material_id} not found",
            },
        )

    # Verify ownership via subject
    result = await db.execute(select(Subject).where(Subject.id == material.subject_id))
    subject = result.scalar_one_or_none()
    if subject is None or subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "FORBIDDEN",
                "message": "You do not have permission to delete this material",
            },
        )

    await MaterialService.delete_material(db=db, material=material)
    await db.commit()

    return SuccessResponse(data=None, message="Material deleted successfully")
