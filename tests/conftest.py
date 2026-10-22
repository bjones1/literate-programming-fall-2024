# `conftest.py` -- Pytest configuration
# =====================================
#
# Register the autouse fixture which isolates every test's Git environment.
from git_test_tools import git_setup

__all__ = ["git_setup"]
