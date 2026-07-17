import pytest
import sys
import os

os.environ.setdefault("DEMO_MODE", "true")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent_medic"))
