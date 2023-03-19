import pytest
@pytest.fixture(scope="function")
def setup_temporary_directory(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("temporary-dir")
    return tmpdir


