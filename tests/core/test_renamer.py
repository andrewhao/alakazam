"""Tests for Alakazam core renamer."""

import pytest
from alakazam.core.renamer import AlakazamConfig, Alakazam


class TestAlakazamConfig:
    """Test AlakazamConfig dataclass (verifies typo fix)."""

    def test_config_instantiation(self):
        """Test that AlakazamConfig can be instantiated with correct name."""
        config = AlakazamConfig()
        assert config.batch_size == 5
        assert config.dry_run is False
        assert config.safe_mode is False
        assert config.max_batches == 1000
        assert config.verbose is False

    def test_config_with_custom_values(self):
        """Test AlakazamConfig with custom values."""
        config = AlakazamConfig(
            batch_size=10,
            dry_run=True,
            safe_mode=True,
            max_batches=100,
            verbose=True
        )
        assert config.batch_size == 10
        assert config.dry_run is True
        assert config.safe_mode is True
        assert config.max_batches == 100
        assert config.verbose is True

    def test_config_class_name_spelling(self):
        """Verify the class name is spelled correctly (Alakazam not Alazazam)."""
        # This test verifies the typo fix
        assert AlakazamConfig.__name__ == "AlakazamConfig"
        assert "Alakazam" in AlakazamConfig.__name__
        assert "Alazazam" not in AlakazamConfig.__name__
