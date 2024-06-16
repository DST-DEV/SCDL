#General imports
import re
import numpy as np
import pandas as pd

#Soundfile adjustment imports
import music_tag
import soundfile
import unicodedata
from scipy.signal import resample

#File Handling imports
import os
import shutil
import difflib
import pathlib
from pathlib import Path

#%%
class LibManager:
    ob_strs = ["premiere", "P R E M I E R E", "free download", "free dl", 
               "Free DL", "FreeDL", "exclusive", "|", "preview"]        #common obsolete strings
    
    def __init__(self, lib_dir = None, nf_dir = None, 
                 excl_lib_folders=["00_General"]):
        #set the standard directory for the code to work in (if none is provided
        # by the user, use the downloads folder)
        if type(lib_dir)==str:
            self.lib_dir = Path(lib_dir) 
        elif type(lib_dir)==type(None) or type(lib_dir)==type(Path()):
            self.lib_dir = lib_dir or Path("C:/Users/davis/00_data/04_Track_Library")
        
        if type(nf_dir)==str:
            self.nf_dir = Path(nf_dir) 
        elif type(nf_dir)==type(None) or type(nf_dir)==type(Path()):
            self.nf_dir = nf_dir or Path(self.lib_dir, 
                                           "00_Organization/00_New_files")
        
        self.excl_lib_folders = excl_lib_folders
        
        self.file_df = pd.DataFrame(columns=["folder", "goal_dir", "filename",
                                             "new_filename", "extension", 
                                             "exceptions", "status", 
                                             "create_missing_dir"])
        self.lib_df = pd.DataFrame(columns=["folder", "filename", "extension"])


    def read_dir (self):
        """Finds all mp3 & wav files within the library directory and its 
        substructure.
        
        Parameters:
        None
        
        Returns:
        self.lib_df: Dataframe with information on the filename, file extension and 
                     folder of all found files
        """
        self.lib_df = self.read_files(self.lib_dir)
        return self.lib_df
    
    
    def read_files(self, directory, excluded_folders = []):
        """Finds all mp3 & wav files within a directory and its substructure.
        
        Parameters:
        directory: top-level directory for the code to work in
        excluded_folders [list of str]: folders to exclude (default: '00_General')
        
        Returns:
        doc: Dataframe with information on the filename, file extension and 
             folder of all found files
        """
        
        #Check inputs:
        if type (excluded_folders) == str:
            excluded_folders = [excluded_folders]
        elif type(excluded_folders) == list:
            if len(excluded_folders)==0:
                excluded_folders = self.excl_lib_folders
        else:
            excluded_folders = self.excl_lib_folders
        
        doc = pd.DataFrame(columns=["folder", "filename", "extension"])
        
        #Search for all mp3 & wav files in the directory, including subdirectories
        for root, _, files in os.walk(directory):
            #Exclude the excluded folders:
            if not any(excl in root for excl in excluded_folders if excl!=""):        
                music_files = np.array([[Path(f).stem, Path(f).suffix] 
                                        for f in files 
                                        if f.endswith(".mp3") 
                                        or f.endswith(".wav")])
                
                if music_files.shape[0]>0:            #check if there are files
                    doc = pd.concat([doc,
                               pd.DataFrame(
                                   dict(folder=[root]*len(music_files), 
                                        filename = music_files[:,0],
                                        extension = music_files[:,1]
                                        )
                                   )
                               ])
        return doc.reset_index(drop=True)    
    
    def read_tracks(self, directory=None, mode="replace"):
        """Finds all mp3 files within a directory and its substructure. The 
        files are then striped of obsolete strings and their artist and title
        are inserted into the metadata information
        
        Parameters:
        directory (opt): top-level directory for the code to work in. If
                         no directory is provided, then the standard_directory 
                         (cf. self.nf_dir) is used
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
        
        if mode not in ["replace", "append", "independent"]:
            raise ValueError ("Invalid value for parameter 'mode'. " 
                              + "Must be either 'replace', 'append' or "
                              + "'independent'")
        
        #read the files (if no directory is provided, use the standard one)
        
        file_df = self.read_files(directory = directory or self.nf_dir,
                                  excluded_folders = [""])
        
        #add additional columns for later
        n_files = len(file_df.index)
        file_df = file_df.assign(goal_dir=[""]*n_files,
                                 new_filename = [""]*n_files,
                                 exceptions=[""]*n_files,
                                 status=[""]*n_files,
                                 create_missing_dir=[False]*n_files)
        file_df.reindex(columns=["folder", "goal_dir", "filename",
                                 "new_filename", "extension", "exceptions", 
                                 "status", "create_missing_dir"])
        
        if mode == "append":
            self.file_df = pd.concat([self.file_df, file_df])
            return self.file_df
        elif mode== "replace":
            self.file_df = file_df
            return self.file_df
        elif mode=="independent":
            return file_df
    
    def prepare_new_files(self):
        "Runs the prepare files function for the new files dataframe"
        
        self.file_df = self.prepare_files(self.file_df.copy(deep=True))
        return self.file_df
    
    def prepare_lib_files (self):
        "Runs the prepare files function for the library files dataframe"
        
        self.lib_df = self.prepare_files(self.lib_df.copy(deep=True))
        return self.lib_df
    
    def prepare_files (self, df=None):
        """Strips the filename of predefined obsolete strings and inserts the 
        artist and title in the metadata.
        If the file is in the .wav format, then the sample rate is adjusted to 
        44100 Hz if needed
        
        Note: files have to be named in the following form: 'artist - title.mp3'
        
        Parameters:
        file_df: Dataframe with information on the folder_path, and filename for 
        all tracks to be processed as well as columns for exceptions and the 
        status whether the file has been processed
            
        Returns:
        file_df: updated version of the file_df dataframe
        
        """
        if type(df) != pd.core.frame.DataFrame or df.empty:
            raise ValueError("Dataframe must be non empty")
        
        for index, row in df.loc[df.status == ""].iterrows():
            #standarize filename
            filename, ext = self.adjust_fname (row["filename"], row["folder"])
            df.loc[index, "new_filename"] = filename + ext

            #Adjust metadata
            file_path = os.path.join(row["folder"], filename + ext)
            try:
                self.set_metadata_auto(file_path)
            except Exception as e:
                self.file_df = self.add_exception(
                    self.file_df, col = "status",
                    msg=f"Metadata error: {e.__class__} : {e}", 
                    index = index)
                df.loc[index, "status"] = "Metadata error"
            else:
                df.loc[index, "status"] = "Renamed and Metadata adjusted"
        
        return df
      
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
    
    def determine_goal_folder (self, mode, file_df=None):
        """Finds the goal subfolder for the files in the file_df depending on 
        the selected mode
        
        Parameters:
        file_df (pd.DataFrame, optional): 
            Dataframe containing information on the folder and filename of all 
            files to be processed
        mode (str):
            Whether the genre metadata or the filename should be used to 
            determine the goal directory for the file
            Choices:
                - 'metadata': Genre metadata is used as the goal folder 
                - 'namesearch': Closest match of filename in the library is used
                for the goal path
            
        Returns:
        file_df: updated version of the dataframe with information on occured 
                 exceptions and the goal folder
        """
        
        if type(file_df) != pd.core.frame.DataFrame or file_df.empty:
            file_df = self.file_df if not self.file_df.empty else self.read_tracks()
        else:
            self.file_df = file_df
            
        if mode=="namesearch":
            lib_df = self.lib_df if not self.lib_df.empty else self.read_dir()
            
        for index, row in file_df.iterrows():
            
            #Determine the path to the file
            if row.new_filename:
                fname = row.new_filename
            else:
                fname = row.filename
            
            if mode == "metadata":
                file_path = Path(self.nf_dir, row["folder"], 
                                 fname + row["extension"])
                
                #Extract the goal directory from the genre metadata
                try:
                    audio = music_tag.load_file(file_path)
                    library_dir = Path(str(audio["genre"]).replace(" - ", "/"))
                    file_df.loc[index, "goal_dir"]=str(library_dir)
                except Exception as e:
                    file_df = self.add_exception(
                        file_df, col = "status",
                        msg=f"Genre extraction error: {e.__class__} : {e}", 
                        index = index)
                    file_df.loc[index, "status"] = "Error during Genre extraction"            
            elif mode=="namesearch":
                closest_match = difflib.get_close_matches(fname, 
                                                          lib_df.filename.tolist(), 
                                                          n=1, cutoff=0.6)
                if closest_match:
                    res = lib_df.loc[lib_df.filename==closest_match[0]]
                    
                    if res.shape[0]==1:
                        res = res.folder.to_list()[0] + "/"\
                            + res.filename.to_list()[0]\
                            + res.extension.to_list()[0]
                    else:
                        res = " | ".join(res.folder.to_list() + "/"
                                         + res.filename.to_list()
                                         + res.extension.to_list())
                    file_df.loc[index, "goal_dir"] = res
            else:
                raise ValueError("mode must me either 'metadata' or 'namesearch,"
                                 f" not {mode}")
        
        self.file_df = file_df
        return file_df
    
    def move_to_library(self, file_df=None):
        """Moves the Tracks in the file_df in their respective folder based on 
        the entries in the goal folder column of the file_df
        
        Parameters:
        file_df (pd.DataFrame, optional): 
            Dataframe containing information on the folder and filename of all 
            files to be processed as well as the goal directory
            
        Returns:
        file_df: updated version of the dataframe with information on occured 
                 exceptions
        """
        
        #Check inputs
        if type(file_df) != pd.core.frame.DataFrame or file_df.empty:
            file_df = self.file_df if not self.file_df.empty else self.read_tracks()
        
        lib_df = self.lib_df if not self.lib_df.empty else self.read_dir()
        
        #Iterate over all tracks
        for index, row in file_df.iterrows():
            
            #Determine the path to the file
            if row.new_filename:
                fname = row.new_filename
            else:
                fname = row.filename
            file_path = Path(self.nf_dir, row["folder"], fname + row["extension"])
            
            #If a goal directory is specified
            if file_df.loc[index, "goal_dir"]:
                #Retrieve all goal directories (there might be multiple)
                goal_dir = file_df.loc[index, "goal_dir"].split(" | ")
                 
                for gd in goal_dir:
                    gd = Path(gd)
                    
                    if gd.suffix:
                        #If the goal directory is a file, replace the file with 
                        #the new file
                        try:
                            os.replace(file_path, Path(self.lib_dir, gd))
                        except Exception as e:
                            self.file_df = self.add_exception(
                                self.file_df, col = "exceptions",
                                msg=f"Copying error for goal directory {gd}: "
                                    + f"{e.__class__} : {e}", 
                                index = index)
                        else:
                            self.file_df = self.add_exception(
                                self.file_df, col = "status",
                                msg=f"Moved to {gd}", 
                                index = index)
                    else:
                        #If the goal directory is a folder, then move the file 
                        # to this folder (Note: if there is already a file with
                        #the same name in the goal folder, then it is replaced)
                        
                        #Check if goal directory exists and whether it should be 
                        #created if it doesn't exist
                        if (row.create_missing_dir 
                            or os.path.isdir (Path(self.lib_dir, gd))):
                            
                            try:
                                if not os.path.isdir (Path(self.lib_dir, gd)):
                                    os.mkdir(self.lib_dir, gd)
                                
                                os.replace(file_path, 
                                           Path(self.lib_dir, 
                                                gd, 
                                                fname + row["extension"]))
                            except Exception as e:
                                self.file_df = self.add_exception(
                                    self.file_df, col = "exceptions",
                                    msg=f"Copying error for goal directory {gd}: "
                                        + f"{e.__class__} : {e}", 
                                    index = index)
                            else:
                                self.file_df = self.add_exception(
                                    self.file_df, col = "status",
                                    msg=f"Moved to {gd}", 
                                    index = index)
                        else:
                            self.file_df.loc[index, "status"] = "Goal directory not found"
            else:
                self.file_df = self.add_exception(
                    self.file_df, col = "exceptions",
                    msg="No goal directory specified", 
                    index = index)
                
        return self.file_df
    
    def process_directory(self, directory=None):
        """Calls the read_tracks and the change_MP3 function on the specified
        directory
        
        Attributes:
        directory (optional): top-level directory for the code to work in. If
        no directory is provided, then the standard_directory is used
        
        Return:
        file_df: Dataframe with information on the folder_path, and filename for 
        all tracks to be processed as well as columns for exceptions and the 
        status whether the file has been processed
        """
        
        file_df = self.read_tracks(directory)
        return self.change_MP3(file_df)
    
    def reset_goal_folder(self):
        self.file_df = self.file_df.loc[:,"goal_dir"] = ""
    
    def reset_file_df(self):
        """Clears the entries in the self.file_df dataframe
        
        Parameters:
        None
            
        Returns:
        None
        """
        self.file_df = pd.DataFrame(columns=["folder", "goal_dir", "filename",
                                             "new_filename", "extension", 
                                             "exceptions", "status", 
                                             "create_missing_dir"])
    def reset_file_df(self):
        """Clears the entries in the self.file_df dataframe
        
        Parameters:
        None
            
        Returns:
        None
        """
        self.file_df = pd.DataFrame(columns=["folder", "goal_dir", "filename",
                                             "new_filename", "extension", 
                                             "exceptions", "status", 
                                             "create_missing_dir"])
        
    def adjust_sample_rate(self, tracks=pd.DataFrame(), max_sr=48000, 
                           std_sr=44100, mode="new", insert_genre=True):
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
        insert_genre (opt.): whether the genre should be inserted based on the 
                             folder path (default: true)
            
        Returns:
        doc: documentation of wave files and whether they were changed
        """
        if type(tracks)==pd.core.frame.DataFrame:
            if mode =="new":
                tracks = tracks if not tracks.empty else self.read_tracks(self, 
                                                                       directory=self.nf_dir, 
                                                                       mode="independent")
            elif mode == "lib":
                tracks = tracks if not tracks.empty else self.read_tracks(self, 
                                                                       directory=self.lib_dir, 
                                                                       mode="independent")
            else:
                raise ValueError("mode must be either 'new' or 'lib'")
        
            for index, row in tracks.loc[tracks.extension ==".wav"].iterrows():
                filepath = Path(row.folder, row.filename + ".wav")
                
                try:
                    self.adjust_sr(filepath, max_sr, std_sr, insert_genre)
                except Exception as e:
                    self.file_df = self.add_exception(
                        self.file_df, col = "status",
                        msg=f"sample rate adjustment error: {e.__class__} : {e}", 
                        index = index)
                    self.file_df.loc[index, "status"] = "Error during sample rate adjustment"
                else:
                    self.file_df.loc[index, "status"] = "sample rate checked"
        elif type(tracks)==str:
            filepath = Path(tracks)
            self.adjust_sr(filepath, max_sr, std_sr, insert_genre)
        elif type(tracks)== type(Path()):
            self.adjust_sr(filepath, max_sr, std_sr, insert_genre)
        else:
            raise ValueError("Invalid File Format: tracks must be a pandas "
                             +"Dataframe, a string containing a filepath or a "
                             +"pathlib.WindowsPath object")
            
    def adjust_sr(self, filepath, max_sr=48000, 
                           std_sr=44100, insert_genre=True):
        """Checks if their sample_rate of the file specified by the filepath
        is below max_sr. 
        If not so, the respective files are converted to the user specified
        sample rate std_sr
        Note: standard resolution is 16 bit
        
        Parameters:
        filepath (str or pathlib.WindowsPath): filepath to the track to be processed
        max_sr (opt. - int): maximum allowed sample rate (default: 48000 Hz)
        std_sr (opt. - int): standard sample rate to which files with a sample
                             rate higher than max_sr should be converted
        insert_genre (opt.): whether the genre should be inserted based on the 
                             folder path (default: true)
            
        Returns:
        None
        """
        
        data, sr = soundfile.read(filepath)
        
        if sr>max_sr:
            # Resample the data
            resampled_data = resample(data, int(len(data)*(std_sr/sr)))
            soundfile.write(filepath, resampled_data, std_sr, subtype='PCM_16')
            
            if insert_genre:
                self.set_metadata_auto(filepath, update_genre=True)
            else:
                self.set_metadata_auto(filepath, update_genre=False)
    
    def set_metadata_auto (self, filepath, genre = "", 
                           update_genre=False, only_genre=False):
        """Automatically sets the artist, title and genre metadata of the file
        provided via the filepath to the values provided via the filename and 
        folderpath
        
        Paramters:
        filepath (str or pathlib.WindowsPath): absolute path to the file to be 
                                               edited
        genre (str): genre of the file (possible to specify manually)
        update_genre (bool): Whether the genre should be updated (default: False)
                           Note: if a genre is specified manually via the 'genre'
                           parameter, then the genre is updated according to its 
                           value
        only_genre (bool): Whether only the genre should be adjusted
        
        Return:
        None"""
        
        if type(filepath)==str:
            filepath=Path(filepath)
        elif type(filepath)!=type(Path()):
            raise ValueError("filepath must be of type str or "
                             + f"pathlib.WindowsPath, not {type(filepath)}")
        
        artist, title = filepath.stem.split(" - ", maxsplit=1).strip()
        
        if genre or update_genre or only_genre:
            if not genre:
                genre = str(filepath.parents[0]).replace(
                    (str(self.lib_dir))+"\\","").replace ("\\"," - ")
            
            if only_genre:
                self.set_metadata(filepath, genre=genre)
            else:
                self.set_metadata(filepath, artist=artist, 
                                  title=title, genre=genre)
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
        elif type(filepath)!=type(Path()):
            raise ValueError("filepath must be of type str or "
                             + f"pathlib.WindowsPath, not {type(filepath)}")
        
        
        if filepath.suffix == [".mp3", ".wav", ".aiff"]:
            file = music_tag.load_file(filepath)   
        else: 
            raise ValueError(f"Invalid file format: {filepath.suffix}")
        
        for key in kwargs.keys():
            file[key] = kwargs[key]
        file.save()
        
        
    def add_exception(self, df, col, msg="", index = -1, key = "", search_col=" "):
        if index >=0 & index<len(df):
            if df.loc[index, col]:
                df.loc[index, col] += " | " + msg
            else:
                df.loc[index, col] =  msg
        elif key and (search_col in df.columns):
            if key in df[search_col].values:
                index = df.loc[df[search_col] == key].index.values[0]
                df.loc[index, col] += " | " +  msg
            else:
                df.loc[-1] = [""]*len(df.column)
                df.loc[-1, col]=msg
                df.loc[-1, search_col]=key
                df = df.reset_index(drop=True)
        else:
            raise ValueError("no valid index or search key and search column provided")
            
        return df
if __name__ == '__main__':
    # nf_dir = Path("C:/Users", os.environ.get("USERNAME"), "Downloads", "music")
    # path = Path("C:/Users/davis/00_data/04_Track_Library/00_Organization/00_New_files")
    
    nf_dir = r"C:\Users\davis\Downloads\SCDL test\00_General\new files"
    lib_dir = r"C:\Users\davis\Downloads\SCDL test"
    MP3r = LibManager(lib_dir, nf_dir)
    lib_df = MP3r.read_dir()
    track_df = MP3r.read_tracks()
    file_df = MP3r.determine_goal_folder(mode="metadata")
    # 
    # rename_doc = MP3r.process_directory()
    # track_df = MP3r.move_to_library()
    
    
    