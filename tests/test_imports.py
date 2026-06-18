"""Verify that all required testing and compatibility packages are importable.

These tests will fail if Flask or Hypothesis are missing.
"""

import pytest


@pytest.mark.unit
def test_flask_importable():
    import flask

    assert flask.__version__


@pytest.mark.unit
def test_hypothesis_importable():
    import hypothesis

    assert hypothesis.__version__
