import os
import pytest

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TEST_DIRECTORY = os.path.join(root_dir, 'tests')
def test():
    pytest.main([TEST_DIRECTORY])
