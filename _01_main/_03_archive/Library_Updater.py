import os
import shutil
import soundfile
import difflib
import numpy as np
import pandas as pd
import pathlib
from pathlib import Path
from scipy.signal import resample
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import music_tag


class File_Replacer:
    def __init__(self, lib_dir=None, base_dir=None, tracks=[]):
        
        self.lib_dir = lib_dir or Path("C:/Users/davis/00_data/04_Track_Library")
        self.base_dir = base_dir or Path(self.lib_dir,
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
        directory = directory or self.lib_dir
        
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
        
        self.lib = doc.reset_index(drop=True)        
        return self.lib
    
    def find_tracks(self, tracks=[], base_dir=None, lib_dir=None):
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
            self.read_dir(self.lib_dir)
        
        track_library["filename_lower"] = [fname.lower().strip() for fname in 
                                     track_library["filename"]]
        lib_fnames_lower = track_library["filename_lower"].values
        
        
        track_comparison = pd.DataFrame(columns=["new_file", 
                                                 "library_file", 
                                                 "folder"])
        
        for track in tracks:
            track_striped = str(Path(track.lower()).with_suffix('')).strip()
            
            closest_match = difflib.get_close_matches(track_striped, 
                                                      lib_fnames_lower, 
                                                      n=1, cutoff=0.6)
            if closest_match:
                res = track_library.loc[track_library.filename_lower==closest_match[0]]
                
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
            
            # if str(Path(track.lower()).with_suffix('')).strip() in \
            #     track_library.filename_lower.values:
                    
            #     res = track_library.loc[
            #         track_library.filename_lower==str(Path(track.lower()
            #                                                ).with_suffix('')
            #                                           ).strip()]
                
            #     track_comparison.loc[
            #         len(track_comparison)] = [track, 
            #                                   res.filename.values[0] 
            #                                   + res.extension.values[0], 
            #                                   res.folder.values[0]]
            # else:
            #     track_comparison.loc[
            #         len(track_comparison)] = [track, 
            #                                   "Track not found", 
            #                                   ""]
        
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
                self.read_dir(self.lib_dir) 
        
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
                self.read_dir(self.lib_dir) 
        
        track_library = track_library.loc[
            track_library.extension == ".mp3"].reset_index(drop=True)
        
        for index, row in track_library.iterrows():
            self.set_metadata_auto (os.path.join(row.folder, 
                                                 row.filename + row.extension), 
                                    only_genre=True)
        
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
    
    def adjust_sample_rate(self, tracks=[], max_sr=48000, std_sr=44100, mode="new"):
        """Finds all .wav files and checks if their sample_rate is below max_sr. 
        If not so, the respective files are converted to the user specified
        sample rate std_sr
        Note: standard resolution is 16 bit
        
        Parameters:
        tracks (opt. - list): List of paths to the tracks to be processed
        max_sr (opt. - int): maximum allowed sample rate (default: 48000 Hz)
        std_sr (opt. - int): standard sample rate to which files with a sample
                             rate higher than max_sr should be converted
        mode (opt. - str): which directory should be considered.
                          - "new": only consider the files in self.base_dir
                          - "lib": only consider the files in the track library
            
        Returns:
        doc: documentation of wave files and whether they were changed
        """
        
        if mode =="new":
            tracks = tracks or self.tracks or self.read_tracks(self.base_dir) 
        elif mode == "lib":
            if not tracks:
                tracks = self.lib if not self.lib.empty else \
                    self.read_dir(Path("C:/Users/davis/00_data/04_Track_Library")) 
                tracks = [row.folder + row.filename + row.extension 
                          for index,row in tracks.iterrows()]
        else:
            raise ValueError("mode must be either 'new' or 'lib'")
        
        for wavfile in list(filter(lambda s: s.endswith(".wav"), tracks)):
            #Read the wave file
            data, sr = soundfile.read(wavfile)
            
            if sr>max_sr:
                # Resample the data
                resampled_data = resample(data, int(len(data)*(std_sr/sr)))
                soundfile.write(wavfile, resampled_data, std_sr, subtype='PCM_16')
                
                #Adjust the Metadata (gets deleted when changing the sample rate)
                self.set_metadata_auto(wavfile)
            
    def set_metadata_auto (self, filepath, only_genre=False):
        """Automatically extracts the artist, title and genre information from
        the filepath and adjusts the metadata of the file
        
        Parameters:
        filepath: (str or pathlib.WindowsPath): absolute path to the file to 
                  be edited
        only_genre (bool): Whether only the genre should be adjusted
            
        Returns:
        None
        """
        if type(filepath)==str:
            filepath=Path(filepath)
        elif type(filepath)!=pathlib.WindowsPath:
            raise ValueError("Filepath must be of type str or pathlib.WindowsPath")
        
        genre = str(filepath.parent).replace(str(self.lib_dir)+"\\", 
            "").replace("\\", " - ")
        
        if only_genre:
            self.set_metadata(filepath, genre=genre)
        else:
            artist, title = filepath.stem.split("-", maxsplit=1)
            self.set_metadata(filepath, artist=artist, title=title, genre=genre)
    
    def set_metadata(self, filepath, **kwargs):
        """Writes the metadata provided via the **kwargs parameter into the 
            file provided by the filename
        
        Parameters:
        filepath (str or pathlib.WindowsPath): absolute path to the file to 
                be edited
        **kwargs: metadata to be edited
            
        Returns:
        None
        """
        if type(filepath)==str:
            filepath=Path(filepath)
        elif type(filepath)!=pathlib.WindowsPath:
            raise ValueError("filepath must be of type str or pathlib.WindowsPath")
            
        file = music_tag.load_file(filepath)
        for key in kwargs.keys():
            file[key] = kwargs[key]
        file.save()
    
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

    
    # tc = fp.process_new_tracks()
    # repl_df = fp.replace_tracks()
    