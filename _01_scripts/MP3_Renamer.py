import os, re 
import music_tag
import soundfile
import numpy as np
import pandas as pd
import pathlib
from pathlib import Path
from scipy.signal import resample
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import unicodedata
import shutil

class MP3Renamer:
    ob_strs = ["premiere", "P R E M I E R E", "free download", "free dl", 
               "Free DL", "FreeDL", "exclusive", "|", "preview"]        #common obsolete strings
    
    def __init__(self, std_dir = None, lib_path = None):
        #set the standard directory for the code to work in (if none is provided
        # by the user, use the downloads folder)
        self.lib_path = lib_path or Path("C:/Users/davis/00_data/04_Track_Library")
        self.std_dir = std_dir or Path(self.lib_path, 
                                       "00_Organization/00_New_files")
        
        
        self.file_df = pd.DataFrame(columns=["folder", "goal_folder", "filename", 
                                             "new_filename","exceptions", "status", 
                                             "create_missing_dir"])

    def read_dir(self, directory=None, mode="replace"):
        """Finds all mp3 files within a directory and its substructure. The 
        files are then striped of obsolete strings and their artist and title
        are inserted into the metadata information
        
        Parameters:
        directory (opt): top-level directory for the code to work in. If
                         no directory is provided, then the standard_directory 
                         (cf. self.std_dir) is used
        mode (opt. - str): Whether to replace or append to existing version of 
                           the self.file_df or dont change the self.file_df at 
                           all (default: replace)
                           -"replace": Replace the current self.file_df
                           - "append": Append to the current self.file_df
                           - "independent": dont interact with the self.file_df
        
        Returns:
        file_df: a Dataframe containing information on the found mp3 and wav 
                 files in the directory and its substructure
        """
        
        #if no directory is provided, use the standard one
        directory = directory or self.std_dir
        
        if mode == "append":
            file_df = self.file_df.copy(deep=True)
        else:
            file_df = pd.DataFrame(columns=["folder", "goal_folder", "filename",
                                            "new_filename","exceptions", "status", 
                                            "create_missing_dir"])
        
        #Search for all mp3 files in the directory, including subdirectories
        for root, _, files in os.walk(directory):
            music_files = [f for f in files if f.endswith(".mp3") | f.endswith(".wav")]
            if music_files:                       #check if there are files
               file_df = pd.concat([file_df,
                   pd.DataFrame(dict(folder=[root]*len(music_files),
                                     goal_folder =[""]*len(music_files),
                                     filename = music_files,
                                     new_filename = [""]*len(music_files),
                                     exceptions=[""]*len(music_files),
                                     status=[""]*len(music_files),
                                     create_missing_dir=[False]*len(music_files)
                                     )
                                )])
        if mode=="independent":
            return file_df
        else:
            self.file_df = file_df
            return self.file_df
    
    def change_MP3 (self, file_df=None):
        """Strips the filename of a list of mp3 files of predefined obsolete 
        strings and inserts the artist and title from the metadata
        
        Note: files have to be named in the following form: 'artist - title.mp3'
        
        Parameters:
        file_df: Dataframe with information on the folder_path, and filename for 
        all tracks to be processed as well as columns for exceptions and the 
        status whether the file has been processed
            
        Returns:
        file_df: updated version of the file_df dataframe
        
        """
        if type(file_df) != pd.core.frame.DataFrame or file_df.empty:
            file_df = self.file_df if not self.file_df.empty else self.read_dir()
        
        for index, row in file_df.loc[file_df.status == ""].iterrows():
            filename, ext = self.adjust_fname (row["filename"], row["folder"])
            
            file_df.loc[index, "new_filename"] = filename + ext
            
            file_path = os.path.join(row["folder"], filename + ext)
            try:
                if ext == ".mp3":
                    audio = MP3(file_path, ID3=EasyID3)
                    
                    name, _ = os.path.splitext(filename)
                    
                    audio['title'] = name.split(" - ")[-1].strip()
                    audio['artist'] = name.split(" - ")[0].strip()
                    
                    audio.save()
            except Exception as e:
                self.file_df.loc[index, "exceptions"] = f"{e.__class__} : {e}"
                self.file_df.loc[index, "status"] = "Metadata error"
            else:
                self.file_df.loc[index, "status"] = "Renamed and Metadata adjusted"
        
        return self.file_df
      
    def adjust_fname (self, filename, folder_path):
        """Removes obsolete strings from a filename and renames the file to the 
        new filename
        
        Parameters: 
        filename: name of the file to be processed
        folder_path: path of the folder in which the file is saved
        
        Returns:
        new_filename: Adjusted filename
        """
        new_filename, extension = os.path.splitext(filename)
        
        for ob_str in self.ob_strs:
            new_filename = new_filename.replace("(" + ob_str + ")", '')
            new_filename = new_filename.replace("(" + ob_str.upper() + ")", '')
            new_filename = new_filename.replace("(" + ob_str.title() + ")", '')
            
            new_filename = new_filename.replace("[" + ob_str + "]", '')
            new_filename = new_filename.replace("[" + ob_str.upper() + "]", '')
            new_filename = new_filename.replace("[" + ob_str.title() + "]", '')
            
            new_filename = new_filename.replace(ob_str, '')
            new_filename = new_filename.replace(ob_str.upper(), '')
            new_filename = new_filename.replace(ob_str.title(), '')
            
        
        #Replace lowercase and uppercase variants of "Remix", "Edit", and 
        # "Mashup" by the title form
        new_filename = re.sub(r"(remix|REMIX|edit|EDIT|mashup|MASHUP)", 
                              lambda match: match.group(1).title(), 
                              new_filename)
        
        #Remove replace square  brackets around "Remix", "Edit", or "Mashup"
        # by round brackets
        new_filename = re.sub(r"\s*\[(.*(?:Remix|Edit|Mashup).*)\]\s*", 
                              lambda match: '(' + match.group(1) + ')', 
                              new_filename)
        
        #Remove all content within square brackets
        new_filename = re.sub(r"\s*\[.*\]\s*", '', 
                              new_filename)
        
        #Remove all round brackets which contain the words 'ft', 'prod' or 'feat'
        new_filename = re.sub(r"\s*\((?:ft|prod|feat).*\)\s*", '', 
                              new_filename)
        
        #Convert to title type and remove leading and tailing spaces
        new_filename = new_filename.title().strip()
        
        #Note: os.replace is used instead of os.rename since os.replace 
        #automatically overwrites if a file with the new filename already exists
        os.replace(os.path.join(folder_path, filename), 
                  os.path.join(folder_path, new_filename + extension))
        
        return new_filename, extension
    
    def convert_to_alphanumeric(self, input_string):
        """Convert an arbitrary string to its closest alphanumeric representation 
        in standard ascii characters (remove non ascii characters and convert 
                                      diacritics to standard characters)
        
        Parameters:
        input_string: the string to be converted
        
        Returns:
        alphanumeric_string: the alphanumeric ascii representation of the string
        """
        
        # Normalize the string to ensure compatibility with ASCII characters
        normalized_string = unicodedata.normalize(
            'NFKD', input_string).encode('ascii', 'ignore').decode('ascii')
        
        # Remove non-alphanumeric characters
        alphanumeric_string = ''.join(char for char in normalized_string 
                                      if char.isalnum() or char.isspace() 
                                      or char =='-' or char =='.')
        
        return alphanumeric_string
    
    def move_to_library(self, file_df=None):
        """Moves the Tracks in the file_df in their respective folder based on 
        the genre metadata
        
        Parameters:
        file_df (optional): Dataframe containing information on the folder 
                            and filename of all files to be processed
            
        Returns:
        file_df: updated version of the dataframe with information on occured 
                 exceptions
        """
        
        if type(file_df) != pd.core.frame.DataFrame or file_df.empty:
            file_df = self.file_df if not self.file_df.empty else self.read_dir()
        else:
            self.file_df = file_df
        
        for index, row in file_df.iterrows():
            
            #Determine the path to the file
            if row.new_filename:
                fname = row.new_filename
            else:
                fname = row.filename
            file_path = Path(row["folder"], fname)
            
            #Extract the goal directory from the genre metadata
            try:
                if file_path.suffix == ".mp3":
                    audio = MP3(file_path, ID3=EasyID3)
                elif file_path.suffix == ".wav":
                    audio = music_tag.load_file(file_path)
                library_dir = Path(audio["genre"][0].replace(" - ", "/"))
                self.file_df.loc[index, "goal_folder"]=str(library_dir)
            except Exception as e:
                self.file_df.loc[index, "exceptions"] = f"{e.__class__} : {e}"
                self.file_df.loc[index, "status"] = "Error during Genre extraction"
            else:
                #Move the file
                if (row.create_missing_dir 
                    or os.path.isdir (Path(self.lib_path, library_dir))):
                    try:
                        if not os.path.isdir (Path(self.lib_path, library_dir)):
                            os.mkdir(self.lib_path, library_dir)
                        
                        os.replace(file_path, 
                                   Path(self.lib_path, library_dir, fname))
                    except Exception as e:
                        self.file_df.loc[index, "exceptions"] = f"{e.__class__} : {e}"
                        self.file_df.loc[index, "status"] = "Error during copying"
                    else:
                        self.file_df.loc[index, "status"] = "Moved to library"
                else:
                    self.file_df.loc[index, "status"] = "Goal directory not found"
        return self.file_df
    
    def process_directory(self, directory=None):
        """Calls the read_dir and the change_MP3 function on the specified
        directory
        
        Attributes:
        directory (optional): top-level directory for the code to work in. If
        no directory is provided, then the standard_directory is used
        
        Return:
        file_df: Dataframe with information on the folder_path, and filename for 
        all tracks to be processed as well as columns for exceptions and the 
        status whether the file has been processed
        """
        
        file_df = self.read_dir(directory)
        return self.change_MP3(file_df)
        
    def reset_search(self):
        """Clears the entries in the self.file_df dataframe
        
        Parameters:
        None
            
        Returns:
        None
        """
        self.file_df = pd.DataFrame(columns=["folder", "filename", 
                                             "exceptions", "processed"])
        
    def adjust_sample_rate(self, tracks=pd.DataFrame(), max_sr=48000, std_sr=44100, mode="new"):
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
            tracks = tracks if not tracks.empty else self.read_dir(self, 
                                                                   directory=self.std_dir, 
                                                                   mode="independent")
        elif mode == "lib":
            tracks = tracks if not tracks.empty else self.read_dir(self, 
                                                                   directory=self.lib_path, 
                                                                   mode="independent")
        else:
            raise ValueError("mode must be either 'new' or 'lib'")
        
        for index, row in tracks.loc[tracks.extension ==".wav"].iterrows():
            #Read the wave file
            filepath = Path(row.folder, row.filename + ".wav")
            data, sr = soundfile.read(filepath)
            
            if sr>max_sr:
                # Resample the data
                resampled_data = resample(data, int(len(data)*(std_sr/sr)))
                soundfile.write(filepath, resampled_data, std_sr, subtype='PCM_16')
        
            self.set_metadata_auto(filepath, update_genre=True)
      
    def set_metadata_auto (self, filepath, update_genre=False):
        """Automatically sets the artist, title and genre metadata of the file
        provided via the filepath to the values provided via the filename and 
        folderpath
        
        Paramters:
        filepath (str or pathlib.WindowsPath): absolute path to the file to be 
                                               edited
       update_genre (bool): Whether the genre should be updated (default: False)
        
        Return:
        None"""
        
        if type(filepath)==str:
            filepath=Path(filepath)
        elif type(filepath)!=pathlib.WindowsPath:
            raise ValueError("filepath must be of type str or "
                             + f"pathlib.WindowsPath, not {type(filepath)}")
        
        artist, title = filepath.stem.split("-", maxsplit=1)
        
        if update_genre:
            genre = str(filepath.parents[0]).replace((str(self.lib_path))+"\\","").replace ("\\"," - ")
            self.set_metadata(filepath, artist=artist, title=title, genre=genre)
        else:
            self.set_metadata(filepath, artist=artist, title=title)
        
    def set_metadata(self, filepath, **kwargs):
        """Writes the metadata provided via the **kwargs parameter into the 
            file provided by the filename
            Note: Supported file formats: .mp3, .wav, .aiff
        
        Parameters:
        filepath (str or pathlib.WindowsPath): absolute path to the file to be edited
        **kwargs: metadata to be edited
            
        Returns:
        None"""
        
        if type(filepath)==str:
            filepath=Path(filepath)
        elif type(filepath)!=pathlib.WindowsPath:
            raise ValueError("filepath must be of type str or "
                             + f"pathlib.WindowsPath, not {type(filepath)}")
        
        if filepath.suffix == ".mp3":
            file = MP3(filepath, ID3=EasyID3)   
        elif filepath.suffix in [".wav", ".aiff"]:
            file = music_tag.load_file(filepath)
        else: 
            raise ValueError(f"Invalid file format: {filepath.suffix}")
        
        for key in kwargs.keys():
            file[key] = kwargs[key]
        file.save()
      
if __name__ == '__main__':
    # std_dir = Path("C:/Users", os.environ.get("USERNAME"), "Downloads", "music")
    path = Path("C:/Users/davis/00_data/04_Track_Library/00_Organization/00_New_files")
    MP3r = MP3Renamer(lib_path=Path("C:/Users/davis/00_data/04_Track_Library"))
    
    # rename_doc = MP3r.process_directory()
    track_df = MP3r.move_to_library()
    
    
    