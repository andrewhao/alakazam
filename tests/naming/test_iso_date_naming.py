"""Tests for ISO date naming strategy (truncation fix verification)."""

import pytest
from alakazam.naming.iso_date import ISODateNaming


class TestISODateNamingTruncation:
    """Test ISODateNaming truncation logic (verifies off-by-one fix)."""

    def test_truncation_length_calculation(self):
        """Test that truncation correctly calculates available space."""
        naming = ISODateNaming(max_length=40)

        # Test case: 40 char limit
        # Format: "YYYY-MM-DD description.pdf"
        # Date: "2024-01-15" (10 chars)
        # Space: " " (1 char)
        # Extension: ".pdf" (4 chars)
        # Total fixed: 10 + 1 + 4 = 15 chars
        # Available for description: 40 - 15 = 25 chars

        date = "2024-01-15"
        description = "This is a very long description that needs truncation"
        ext = ".pdf"

        result = naming._truncate(date, description, ext)

        # Verify total length is within limit
        assert len(result) <= 40

        # Verify format is correct
        assert result.startswith("2024-01-15 ")
        assert result.endswith(".pdf")

        # Verify the description was truncated
        assert "This is a very long" in result

    def test_truncation_at_word_boundary(self):
        """Test that truncation prefers word boundaries."""
        naming = ISODateNaming(max_length=35)

        date = "2024-01-15"
        description = "Short words here and there"
        ext = ".pdf"

        result = naming._truncate(date, description, ext)

        # Should truncate at a word boundary
        assert not result.endswith("d .pdf")  # Not mid-word
        assert len(result) <= 35

    def test_no_truncation_needed(self):
        """Test that short filenames are not truncated."""
        naming = ISODateNaming(max_length=80)

        analysis = {
            "document_date": "2024-01-15",
            "description": "Short Name"
        }

        result = naming.generate_filename(analysis, "test.pdf")

        assert result == "2024-01-15 Short Name.pdf"
        assert len(result) < 80

    def test_truncation_with_exact_length(self):
        """Test edge case where filename is exactly at max_length."""
        naming = ISODateNaming(max_length=30)

        # Create a filename that's exactly 30 chars: "2024-01-15 " (11) + "Test File" (9) + ".pdf" (4) = 24
        analysis = {
            "document_date": "2024-01-15",
            "description": "Test File Name Desc"
        }

        result = naming.generate_filename(analysis, "test.pdf")

        assert len(result) <= 30

    def test_truncation_minimal_space(self):
        """Test behavior when very little space is available."""
        naming = ISODateNaming(max_length=20)  # Very short

        date = "2024-01-15"
        description = "Long description"
        ext = ".pdf"

        result = naming._truncate(date, description, ext)

        # With max_length=20:
        # Date: 10, Space: 1, Ext: 4 = 15 fixed
        # Available: 20 - 15 = 5 chars, which is < 10
        # So it returns just date+ext (no description)
        assert len(result) <= 20
        assert result == "2024-01-15.pdf"
        assert len(result) == 14

    def test_truncation_insufficient_space(self):
        """Test behavior when there's not enough space for meaningful description."""
        naming = ISODateNaming(max_length=15)  # Too short for description

        date = "2024-01-15"
        description = "Any description"
        ext = ".pdf"

        result = naming._truncate(date, description, ext)

        # Should return just date + extension (no space for description)
        # With max_length=15, available = 15 - 15 = 0, which is < 10
        # Returns date+ext = "2024-01-15.pdf" = 14 chars (not 15)
        assert result == "2024-01-15.pdf"
        assert len(result) == 14

    def test_truncation_max_length_too_small(self):
        """Test that truncation raises error when max_length is impossibly small."""
        naming = ISODateNaming(max_length=10)  # Too small for date+ext

        date = "2024-01-15"
        description = "description"
        ext = ".pdf"

        # date+ext requires 14 chars minimum
        with pytest.raises(ValueError, match="max_length.*too small"):
            naming._truncate(date, description, ext)


class TestISODateNamingValidation:
    """Test validation logic."""

    def test_validate_correct_format(self):
        """Test validation accepts correct format."""
        naming = ISODateNaming()

        assert naming.validate("2024-01-15 Document Name.pdf")
        assert naming.validate("2024-12-31 Test.txt")

    def test_validate_rejects_invalid_format(self):
        """Test validation rejects invalid formats."""
        naming = ISODateNaming()

        assert not naming.validate("Document Name.pdf")  # No date
        assert not naming.validate("2024-01-15.pdf")  # No description
        assert not naming.validate("01-15-2024 Document.pdf")  # Wrong date format

    def test_validate_rejects_invalid_characters(self):
        """Test validation rejects filenames with invalid characters."""
        naming = ISODateNaming()

        assert not naming.validate("2024-01-15 Invalid:Name.pdf")
        assert not naming.validate("2024-01-15 Invalid/Name.pdf")
        assert not naming.validate('2024-01-15 Invalid"Name.pdf')
