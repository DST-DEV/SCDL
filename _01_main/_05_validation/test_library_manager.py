import pytest
import pandas as pd


def test_auto_renaming (LibMan):
    fpath = r"C:\Users\davis\00_data\01_Projects\Personal\SCDL\_01_main" \
        + r"\_05_validation\LibMan_renaming_test_names.xlsx"
    names = pd.read_excel(fpath)

    for i, name in names.iterrows():
        original_name = name["original_filename"] + ".mp3"
        renamed,_ = LibMan.adjust_fname(original_name)

        assert renamed == names.loc[i,"correct_filename"], \
            f"Renaming failed for {name.original_filename}"


if __name__ == "__main__":
    import sys
    sys.path.append(r"C:\Users\davis\00_data\01_Projects\Personal\SCDL\_01_main\_00_scripts")
    from Library_Manager import LibManager

    test_auto_renaming(LibManager())