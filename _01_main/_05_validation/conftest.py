import pytest
import pandas as pd

import sys
sys.path.append(r"C:\Users\davis\00_data\01_Projects\Personal\SCDL\_01_main\_00_scripts")
from Library_Manager import LibManager
from Link_Extractor import PlaylistLinkExtractor

@pytest.fixture
def LibMan():
    return LibManager()

@pytest.fixture
def LinkExt():
    ple = PlaylistLinkExtractor()
    ple.playlists = pd.DataFrame(
        columns=["name", "link", "last_track", "status"],
        data=[["Not Existing",
               "https://soundcloud.com/sillyphus/sets/not_existing_playlist",
               "https://soundcloud.com/no_track",
               ""],
              ["Hardstyle",
               "https://soundcloud.com/sillyphus/sets/hardstyle",
               "https://soundcloud.com/user-483951846/davay-rasskazhem",
               ""],
              ["Trance - Other - Low Energy - Vocal",
               "https://soundcloud.com/sillyphus/sets/hardstyle",
               "https://soundcloud.com/syndikaet/kh38-lehmann-fuccbois",
               ""],
              ])

    return ple