import pytest
import sys
sys.path.append(r"C:\Users\davis\00_data\01_Projects\Personal\SCDL\_01_main\_00_scripts")
from Link_Extractor import PlaylistNotFoundError

def test_open_pl (LinkExt):

    with pytest.raises(PlaylistNotFoundError):
        LinkExt.open_pl(LinkExt.playlists.loc[0],
                        0)
