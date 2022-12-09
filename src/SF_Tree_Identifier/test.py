import os
import pytest

root_dir = os.path.dirname(__file__)
TEST_DIRECTORY = os.path.join(root_dir, "tests")


def test():
    pytest.main([TEST_DIRECTORY])


if __name__ == "__main__":
    test()
