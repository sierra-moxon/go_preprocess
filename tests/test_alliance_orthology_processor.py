"""Test the Alliance Ortholog processor."""
import os
import unittest
from pathlib import Path


class TestOrthoProcessor(unittest.TestCase):

    """Test the Alliance Ortholog processor."""

    def test_parse_gpi(self):
        """Test the files exist."""
        data_path = os.path.expanduser("tests/resources")
        file_path = Path(os.path.join(data_path, "test_ortho.json"))
        self.assertTrue(file_path.exists())


if __name__ == "__main__":
    """
    Run the unit tests

    """
    unittest.main()