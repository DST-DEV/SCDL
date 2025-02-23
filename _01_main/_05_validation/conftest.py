import pytest

import sys
sys.path.append(r"C:\Users\davis\00_data\01_Projects\Personal\SCDL\_01_main\_00_scripts")
from Library_Manager import LibManager

@pytest.fixture
def LibMan():
    return LibManager()