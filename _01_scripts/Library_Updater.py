import os
import pandas as pd
from pathlib import Path
import shutil
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3


class File_Replacer:
    def __init__(self, base_dir=None, tracks=[]):
        self.base_dir = base_dir or Path("C:/Users/davis/00_data/04_Track_Library/",
                                         "00_Organization/00_new_files")
        self.tracks = tracks
        self.lib = pd.DataFrame(columns = ["filename", 
                                           "extension", 
                                           "folder"])
        self.track_comparison = pd.DataFrame(columns=["new_file", 
                                                     "library_file", 
                                                     "folder",
                                                     "status"])
        
    def read_tracks(self, directory=None):
        """Finds all mp3 & wav files within the directory (only top level)
        
        Parameters:
        directory (optional): directory for the code to work in. If
        no directory is provided, then the standard_directory is used
        
        Returns:
        tracks: list of the found files
        """
        
        #if no directory is provided, use the standard one
        directory = directory or self.base_dir
        
        #List all mp3 and wav files
        tracks = [f for f in sorted(os.listdir(directory)) 
                  if f.endswith(".mp3") or f.endswith(".wav")]
        
        self.tracks = tracks
        
        return tracks
    
    def read_dir(self, directory=None):
        """Finds all mp3 & wav files within a directory and its substructure. The 
        files are then striped of obsolete strings and their artist and title
        are inserted into the metadata information
        
        Parameters:
        directory (optional): top-level directory for the code to work in. If
        no directory is provided, then the standard_directory is used
        
        Returns:
        doc: Dataframe with information on the filename, file extension and 
             folder of all found files
        """
        
        #if no directory is provided, use the standard one
        directory = directory or Path("C:/Users/davis/00_data/04_Track_Library")
        
        doc = pd.DataFrame(columns=["filename", "extension", "folder"])
        
        #Search for all mp3 & wav files in the directory, including subdirectories
        for root, _, files in os.walk(directory):
            if not "00_Organization" in root:        #Exclude the "00_General" folder from the search
                music_files = [f for f in files 
                               if f.endswith(".mp3") or f.endswith(".wav")]
                
                file_list = []
                
                if music_files:                       #check if there are files
                    for f in music_files:
                        name, ext = os.path.splitext(f)
                        file_list.append([name, ext, root])
                
                    doc = pd.concat([doc,
                                     pd.DataFrame(columns = ["filename", 
                                                             "extension", 
                                                             "folder"], 
                                                  data = file_list)
                                     ])
               
        return doc.reset_index(drop=True)
    
    def find_tracks(self, tracks=[], base_dir=None):
        """Find the music files specified in the parameter tracks in the Track 
        library (C:/Users/davis/00_data/04_Track_Library)
        
        Parameters: 
        tracks (optional): List of the filenames to search for (if none is 
                           provided, the value of self.tracks is used or the 
                           tracks are read from the base_dir)
        base_dir (optional): Windows file path of the folder with the files to 
                             search for in the library
        \n
        Returns:
        track_comparison: Pandas Dataframe with information on the filename of 
                          the new filenames, the filenames of the corresponding
                          files in the library and the folder of the files in 
                          the library
        """
        
        tracks = tracks or self.tracks or self.read_tracks(base_dir)

        track_library = self.lib if not self.lib.empty else \
            self.read_dir(Path("C:/Users/davis/00_data/04_Track_Library"))
        
        track_library["filename_lower"] = [fname.lower().strip() for fname in 
                                     track_library["filename"]]
        
        track_comparison = pd.DataFrame(columns=["new_file", 
                                                 "library_file", 
                                                 "folder"])
        
        for track in tracks:
            if str(Path(track.lower()).with_suffix('')).strip() in \
                track_library.filename_lower.values:
                    
                res = track_library.loc[
                    track_library.filename_lower==str(Path(track.lower()
                                                           ).with_suffix('')
                                                      ).strip()]
                
                track_comparison.loc[
                    len(track_comparison)] = [track, 
                                              res.filename.values[0] 
                                              + res.extension.values[0], 
                                              res.folder.values[0]]
            else:
                track_comparison.loc[
                    len(track_comparison)] = [track, 
                                              "Track not found", 
                                              ""]
        
        self.track_comparison = track_comparison
        self.track_comparison["status"] = [None]*len(track_comparison)
        
        return track_comparison
    
    def replace_tracks(self, file_df=None):
        """Replace the files specified in the 'library_file' column of the 
        file_df with the file in the 'new_file' column
        
        Parameters:
        file_df: Pandas DataFrame with the filenames of the new files, the 
                 filenames of the old files, the folder of the old files and a 
                 column 'status' filled with None as columns
        
        Returns:
        file_df: updated version of the file_df
        """
        
        if type(file_df) != pd.core.frame.DataFrame or file_df.empty:
            file_df = self.track_comparison if not self.track_comparison.empty \
                else self.find_tracks()
        
        
        for index, row in file_df.loc[
                file_df.library_file!="Track not found"].iterrows():
            try:
                shutil.copy2(os.path.join(self.base_dir, row.new_file),
                            os.path.join(row.folder))
            except Exception as e:
                if file_df.loc[index, "status"]:
                    file_df.loc[index, "status"] = file_df.loc[index, "status"] + \
                                                    f" | Copy Error {e.__class__}: {e}"
                else:
                    file_df.loc[index, "status"] = f"Copy Error {e.__class__}: {e}"
            else:
                if row.new_file[-3:]!=row.library_file[-3:]:
                    try:
                        os.remove(os.path.join(row.folder, row.library_file)) 
                    except Exception as e:
                        file_df.loc[index, "status"] = f"Deletion Error {e.__class__}: {e}"
                    else:
                        file_df.loc[index, "status"] = "done"
                        os.remove(os.path.join(self.base_dir, row.new_file))
                else:
                    file_df.loc[index, "status"] = "done"
                    os.remove(os.path.join(self.base_dir, row.new_file))
                
        self.track_comparison = file_df
        
        return file_df
    
    def strip_library_tracks(self, track_library=pd.DataFrame(columns = ["filename", 
                                                                   "extension", 
                                                                   "folder"])):
        """Removes leading and tailing spaces from the file names in the library
        
        Parameters:
        track_library (optional): Dataframe with information on the filename, 
                                  file extension and folder of the library files
            
        Returns:
        track_library: updated track_library
            """
        if track_library.empty:
            track_library = self.lib if not self.lib.empty else \
                self.read_dir(Path("C:/Users/davis/00_data/04_Track_Library")) 
        
        for index, row in track_library.iterrows():
            os.replace(os.path.join(row.folder, row.filename + row.extension), 
                      os.path.join(row.folder, row.filename.strip() + row.extension))
            track_library.loc[index, "filename"] = row.filename.strip()
        
        self.lib = track_library
        
        return track_library
    
    def update_genre(self, track_library=pd.DataFrame(columns = ["filename", 
                                                                   "extension", 
                                                                   "folder"])):
        """Updates the Genre of the mp3 files in the library to match the folder
        structure
        
        Parameters:
        track_library (optional): Dataframe with information on the filename, 
                                  file extension and folder of the library files    
            
        Returns:
        None
            """
        if track_library.empty:
            track_library = self.lib if not self.lib.empty else \
                self.read_dir(Path("C:/Users/davis/00_data/04_Track_Library")) 
        
        track_library = track_library.loc[
            track_library.extension == ".mp3"].reset_index(drop=True)
        
        for index, row in track_library.iterrows():
            audio = MP3(os.path.join(row.folder, row.filename + row.extension), ID3=EasyID3)
            audio ["genre"] = row.folder.replace(
                "C:\\Users\\davis\\00_data\\04_Track_Library\\", 
                "").replace("\\", " - ")
            audio.save()
        
    def copy_to_music_lib(self):
        """Copies the mp3 files in the Music directory on the hard drive 
        
        Parameters:
        None
        
        Returns:
        track_doc: Pandas Dataframe with information on the tracks that were 
                   copied
       """
        
        track_library = self.read_dir(
            Path("C:/Users/davis/00_data/04_Track_Library/Trance")) 
        
        mp3_files = track_library.loc[track_library.extension ==".mp3"]
        
        for index, row in mp3_files.iterrows():
            shutil.copy2(Path(row.folder, row.filename + row.extension), 
                         Path("C:/Users/davis/00_data/03_Music"))
            
    def process_new_tracks(self, base_dir = None, tracks = []):
        
        if base_dir:
            tracks = self.read_tracks(base_dir)
        else:
            tracks = tracks or self.tracks or self.read_tracks()
        
        _ = fp.read_dir()
        track_comparison = fp.find_tracks(tracks=tracks)
        
        return track_comparison
        
if __name__ == '__main__':
    fp = File_Replacer() 
    # lib = fp.strip_library_tracks()
    # fp.update_genre()

    
    tc = fp.process_new_tracks()
    # repl_df = fp.replace_tracks()
    