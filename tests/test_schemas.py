"""Unit tests for Pydantic schemas."""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserUpdate, UserResponse, ChangePasswordRequest
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.schemas.topic import TopicCreate, TopicUpdate, TopicResponse
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, ScribbleStroke, Point
from app.schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse
from app.schemas.snippet import SnippetCreate, SnippetUpdate, SnippetResponse
from app.schemas.master_data import AvatarStyleResponse, AvatarColorResponse, TintPaletteResponse


class TestUserSchemas:
    """Tests for user schemas."""

    def test_user_create_valid(self):
        """Test valid user creation schema."""
        user_id = uuid4()
        color_id = uuid4()
        user = UserCreate(
            name="John Doe",
            email="john@example.com",
            password="secure_password_123",
            avatar_style_id=user_id,
            avatar_color_id=color_id,
        )
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.password == "secure_password_123"

    def test_user_create_email_lowercase(self):
        """Test email is converted to lowercase."""
        user_id = uuid4()
        color_id = uuid4()
        user = UserCreate(
            name="John Doe",
            email="JOHN@EXAMPLE.COM",
            password="secure_password_123",
            avatar_style_id=user_id,
            avatar_color_id=color_id,
        )
        assert user.email == "john@example.com"

    def test_user_create_invalid_email(self):
        """Test invalid email format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                name="John Doe",
                email="invalid-email",
                password="secure_password_123",
                avatar_style_id=uuid4(),
                avatar_color_id=uuid4(),
            )
        assert "Invalid email format" in str(exc_info.value)

    def test_user_create_name_too_short(self):
        """Test name too short raises error."""
        with pytest.raises(ValidationError):
            UserCreate(
                name="J",
                email="john@example.com",
                password="secure_password_123",
                avatar_style_id=uuid4(),
                avatar_color_id=uuid4(),
            )

    def test_user_create_name_too_long(self):
        """Test name too long raises error."""
        with pytest.raises(ValidationError):
            UserCreate(
                name="J" * 101,
                email="john@example.com",
                password="secure_password_123",
                avatar_style_id=uuid4(),
                avatar_color_id=uuid4(),
            )

    def test_user_create_password_too_short(self):
        """Test password too short raises error."""
        with pytest.raises(ValidationError):
            UserCreate(
                name="John Doe",
                email="john@example.com",
                password="short",
                avatar_style_id=uuid4(),
                avatar_color_id=uuid4(),
            )

    def test_user_create_password_too_long(self):
        """Test password too long raises error."""
        with pytest.raises(ValidationError):
            UserCreate(
                name="John Doe",
                email="john@example.com",
                password="p" * 129,
                avatar_style_id=uuid4(),
                avatar_color_id=uuid4(),
            )

    def test_user_create_empty_name(self):
        """Test empty name raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                name="   ",
                email="john@example.com",
                password="secure_password_123",
                avatar_style_id=uuid4(),
                avatar_color_id=uuid4(),
            )
        assert "Name cannot be empty" in str(exc_info.value)

    def test_user_update_valid(self):
        """Test valid user update schema."""
        user = UserUpdate(name="Jane Doe")
        assert user.name == "Jane Doe"

    def test_user_update_partial(self):
        """Test partial user update."""
        user = UserUpdate(avatar_style_id=uuid4())
        assert user.avatar_style_id is not None
        assert user.name is None

    def test_change_password_request_valid(self):
        """Test valid change password request."""
        req = ChangePasswordRequest(
            current_password="old_password",
            new_password="new_password_123",
        )
        assert req.current_password == "old_password"
        assert req.new_password == "new_password_123"

    def test_change_password_new_password_too_short(self):
        """Test new password too short raises error."""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                current_password="old_password",
                new_password="short",
            )


class TestSubjectSchemas:
    """Tests for subject schemas."""

    def test_subject_create_valid(self):
        """Test valid subject creation schema."""
        subject = SubjectCreate(
            name="Data Structures",
            description="Study materials for DSA",
        )
        assert subject.name == "Data Structures"
        assert subject.description == "Study materials for DSA"

    def test_subject_create_minimal(self):
        """Test minimal subject creation."""
        subject = SubjectCreate(name="Algorithms")
        assert subject.name == "Algorithms"
        assert subject.color_id is None
        assert subject.description is None

    def test_subject_create_name_too_long(self):
        """Test name too long raises error."""
        with pytest.raises(ValidationError):
            SubjectCreate(name="A" * 256)

    def test_subject_create_description_too_long(self):
        """Test description too long raises error."""
        with pytest.raises(ValidationError):
            SubjectCreate(name="Test", description="D" * 1001)

    def test_subject_create_empty_name(self):
        """Test empty name raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SubjectCreate(name="   ")
        assert "Name cannot be empty" in str(exc_info.value)

    def test_subject_update_valid(self):
        """Test valid subject update schema."""
        subject = SubjectUpdate(name="Updated Name")
        assert subject.name == "Updated Name"


class TestTopicSchemas:
    """Tests for topic schemas."""

    def test_topic_create_valid(self):
        """Test valid topic creation schema."""
        topic = TopicCreate(name="Graph Algorithms")
        assert topic.name == "Graph Algorithms"
        assert topic.tint_id is None

    def test_topic_create_with_tint(self):
        """Test topic creation with tint."""
        tint_id = uuid4()
        topic = TopicCreate(name="Graph Algorithms", tint_id=tint_id)
        assert topic.tint_id == tint_id

    def test_topic_create_empty_name(self):
        """Test empty name raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TopicCreate(name="   ")
        assert "Name cannot be empty" in str(exc_info.value)

    def test_topic_update_status_valid(self):
        """Test valid status values in update."""
        for status in ["not-started", "in-progress", "revising", "completed"]:
            topic = TopicUpdate(status=status)
            assert topic.status == status

    def test_topic_update_confidence_valid(self):
        """Test valid confidence values in update."""
        for confidence in [0, 1, 2, 3, 4, 5]:
            topic = TopicUpdate(confidence=confidence)
            assert topic.confidence == confidence

    def test_topic_update_confidence_out_of_range(self):
        """Test confidence out of range raises error."""
        with pytest.raises(ValidationError):
            TopicUpdate(confidence=6)

        with pytest.raises(ValidationError):
            TopicUpdate(confidence=-1)


class TestNoteSchemas:
    """Tests for note schemas."""

    def test_note_create_valid(self):
        """Test valid note creation schema."""
        note = NoteCreate(
            title="Graph Traversal",
            body="# BFS and DFS algorithms",
        )
        assert note.title == "Graph Traversal"
        assert note.body == "# BFS and DFS algorithms"

    def test_note_create_minimal(self):
        """Test minimal note creation."""
        note = NoteCreate(title="Quick Note")
        assert note.title == "Quick Note"
        assert note.body is None

    def test_note_create_empty_title(self):
        """Test empty title raises error."""
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(title="   ")
        assert "Title cannot be empty" in str(exc_info.value)

    def test_scribble_stroke_valid(self):
        """Test valid scribble stroke."""
        stroke = ScribbleStroke(
            id=str(uuid4()),
            tool="brush",
            color="#FF0000",
            width=2.5,
            opacity=0.8,
            points=[Point(x=100, y=200), Point(x=110, y=210)],
        )
        assert stroke.tool == "brush"
        assert stroke.color == "#FF0000"
        assert stroke.width == 2.5
        assert stroke.opacity == 0.8
        assert len(stroke.points) == 2

    def test_scribble_stroke_invalid_color(self):
        """Test invalid hex color raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ScribbleStroke(
                id=str(uuid4()),
                tool="brush",
                color="invalid",
                width=2.5,
                opacity=0.8,
                points=[Point(x=100, y=200)],
            )
        assert "Invalid hex color format" in str(exc_info.value)

    def test_scribble_stroke_width_out_of_range(self):
        """Test width out of range raises error."""
        with pytest.raises(ValidationError):
            ScribbleStroke(
                id=str(uuid4()),
                tool="brush",
                color="#FF0000",
                width=25,
                opacity=0.8,
                points=[Point(x=100, y=200)],
            )

    def test_scribble_stroke_opacity_out_of_range(self):
        """Test opacity out of range raises error."""
        with pytest.raises(ValidationError):
            ScribbleStroke(
                id=str(uuid4()),
                tool="brush",
                color="#FF0000",
                width=2.5,
                opacity=1.5,
                points=[Point(x=100, y=200)],
            )

    def test_note_update_with_scribbles(self):
        """Test note update with scribbles."""
        stroke = ScribbleStroke(
            id=str(uuid4()),
            tool="brush",
            color="#FF0000",
            width=2.5,
            opacity=0.8,
            points=[Point(x=100, y=200)],
        )
        note = NoteUpdate(title="Updated Title", scribbles=[stroke])
        assert note.scribbles is not None
        assert len(note.scribbles) == 1


class TestMaterialSchemas:
    """Tests for material schemas."""

    def test_material_create_valid(self):
        """Test valid material creation schema."""
        material = MaterialCreate(title="Algorithm Design Manual")
        assert material.title == "Algorithm Design Manual"

    def test_material_create_empty_title(self):
        """Test empty title raises error."""
        with pytest.raises(ValidationError) as exc_info:
            MaterialCreate(title="   ")
        assert "Title cannot be empty" in str(exc_info.value)

    def test_material_update_valid(self):
        """Test valid material update schema."""
        material = MaterialUpdate(title="Updated Title", page_count=350)
        assert material.title == "Updated Title"
        assert material.page_count == 350

    def test_material_update_page_count_invalid(self):
        """Test invalid page count raises error."""
        with pytest.raises(ValidationError):
            MaterialUpdate(page_count=0)


class TestSnippetSchemas:
    """Tests for snippet schemas."""

    def test_snippet_create_valid(self):
        """Test valid snippet creation schema."""
        snippet = SnippetCreate(
            language="python",
            code="def hello():\n    print('Hello')",
        )
        assert snippet.language == "python"
        assert snippet.code == "def hello():\n    print('Hello')"

    def test_snippet_create_with_note(self):
        """Test snippet creation with note reference."""
        note_id = uuid4()
        snippet = SnippetCreate(
            language="python",
            code="print('test')",
            note_id=note_id,
        )
        assert snippet.note_id == note_id

    def test_snippet_create_empty_language(self):
        """Test empty language raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SnippetCreate(language="   ", code="print('test')")
        assert "Language cannot be empty" in str(exc_info.value)

    def test_snippet_create_empty_code(self):
        """Test empty code raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SnippetCreate(language="python", code="   ")
        assert "Code cannot be empty" in str(exc_info.value)

    def test_snippet_update_valid(self):
        """Test valid snippet update schema."""
        snippet = SnippetUpdate(code="updated code", output="result")
        assert snippet.code == "updated code"
        assert snippet.output == "result"


class TestMasterDataSchemas:
    """Tests for master data schemas."""

    def test_avatar_style_response(self):
        """Test avatar style response schema."""
        from decimal import Decimal
        
        style = AvatarStyleResponse(
            id=uuid4(),
            name="Floating Bubble",
            slug="floating-bubble",
            description="A gentle floating animation",
            svg_template="<svg>...</svg>",
            animation_type="float",
            animation_duration=Decimal("3.0"),
            color_customizable=True,
            display_order=1,
            is_active=True,
            created_at=datetime.now(),
        )
        assert style.name == "Floating Bubble"
        assert style.animation_type == "float"

    def test_avatar_color_response(self):
        """Test avatar color response schema."""
        color = AvatarColorResponse(
            id=uuid4(),
            name="Ocean Blue",
            hex_code="#0066CC",
            rgb="rgb(0, 102, 204)",
            hsl="hsl(210, 100%, 40%)",
            display_order=1,
            is_active=True,
            created_at=datetime.now(),
        )
        assert color.name == "Ocean Blue"
        assert color.hex_code == "#0066CC"

    def test_tint_palette_response(self):
        """Test tint palette response schema."""
        tint = TintPaletteResponse(
            id=uuid4(),
            name="Dusty Rose",
            hsl="hsl(350, 60%, 70%)",
            hex_code="#E8A0A0",
            category="warm",
            display_order=1,
            is_active=True,
            created_at=datetime.now(),
        )
        assert tint.name == "Dusty Rose"
        assert tint.category == "warm"
