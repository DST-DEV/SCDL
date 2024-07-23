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
               "Free DL", "FreeDL", "exclusive", "|", "preview", "sindex", 
               "motz", "OUTNOW"]        #common obsolete strings
    
    def __init__(self, lib_dir = None, nf_dir = None, 
                 excl_lib_folders=["00_Organization"], **kwargs):
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
                                             "old_filename", "extension", 
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
        """Finds all mp3, wav and aiff files within a directory and its substructure.
        
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
                                 old_filename = [""]*n_files,
                                 exceptions=[""]*n_files,
                                 status=[""]*n_files,
                                 create_missing_dir=[False]*n_files)
        file_df.reindex(columns=["folder", "goal_dir", "filename",
                                 "old_filename", "extension", "exceptions", 
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
    
    def prepare_files (self, df_sel=None,
                       adj_fnames = True,
                       adj_art_tit = True,
                       adj_genre = True):
        """Strips the filename of predefined obsolete strings and inserts the 
        artist and title in the metadata.
        If the file is in the .wav format, then the sample rate is adjusted to 
        44100 Hz if needed
        
        Note: files have to be named in the following form: 'artist - title.mp3'
        
        Parameters:
            df_sel (str or pandas.DataFrame): 
                Dataframe with information on the folder_path, and filename for 
                all tracks to be processed as well as columns for exceptions and the 
                status whether the file has been processed
                Alternatively, 'nf' or 'lib' can be specified. The function will
                then automatically extract the file_df or the lib_df 
            adj_fnames (bool):
                Whether to adjust the filenames
            adj_art_tit (bool):
                Whether to automatically insert the artist and title metadata
            adj_genre (bool):
                Whether to automatically insert the genre  metadata
            
        Returns:
        file_df: updated version of the file_df dataframe
        
        """
        if type(df_sel)==str:
            if df_sel == "nf":
                df = self.file_df.copy(deep=True)
            elif df_sel == "lib":
                df = self.lib_df.copy(deep=True)
            else:
                ValueError("Parameter df_sel must be either a string of value 'nf'",
                           " or 'lib', or a pandas Dataframe")
        if type(df_sel) == pd.core.frame.DataFrame:
            if not df.empty:
                df = df_sel.copy(deep=True)
            else: 
                raise ValueError("Dataframe must be non empty")
        else:
            ValueError("Parameter df_sel must be either a string of value 'nf'",
                       " or 'lib', or a pandas Dataframe")
            
        
        for index, row in df.iterrows():
            #Skip entries, which are already processed or which were chosen
            # explicitly not to be included
            if row.status != "": continue
            if "include" in df.columns and row.include==False: continue
            
            if adj_fnames:
                #standarize filename
                filename, ext = self.adjust_fname (row["filename"] 
                                                   + row["extension"], 
                                                   row["folder"])
                df.loc[index, "old_filename"] = row["filename"]
                df.loc[index, "filename"] = filename
            else:
                filename, ext = row["filename"], row["extension"]
                
            if adj_art_tit or adj_genre:
                #Adjust metadata
                file_path = os.path.join(row["folder"], filename + ext)
                try:
                    self.set_metadata_auto(file_path,
                                           adj_art_tit=adj_art_tit,
                                           adj_genre = adj_genre)
                except Exception as e:
                    self.file_df = self.add_exception(
                        self.file_df, col = "status",
                        msg=f"Metadata error: {e.__class__} : {e}", 
                        index = index)
                    df.loc[index, "status"] = "Metadata error"
                else:
                    df.loc[index, "status"] = "Renamed and Metadata adjusted"
        
        #Save the results
        if type(df_sel) == str:
            if df_sel == "nf":
                self.file_df = df.copy(deep=True)
            elif df_sel == "lib":
                self.lib_df = df.copy(deep=True)
        
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
        
        #Remove all content within square brackets
        new_filename = re.sub(r"\s*\[.*?\]\s*", '', 
                              new_filename)
        
        #Replace square  brackets around "Remix", "Edit", or "Mashup"
        # by round brackets
        # Note: searching for lowercase and uppercase versions of the string is 
        # not necessary, since they were replaced by the title version in a 
        # previous step
        new_filename = re.sub(r"\s*\[(.*?(?:Remix|Edit|Mashup).*?)\]\s*", 
                              lambda match: '(' + match.group(1) + ')', 
                              new_filename)
        
        #Remove all round brackets which contain the words 'ft', 'prod', 'feat', or 'records'
        excl = "|".join(np.array([[x.lower(),x.upper(),x.title()] 
                                  for x in ["ft","prod","feat","records"]]
                                 ).flatten())
        new_filename = re.sub(r"\s*\(.*(?:" + excl + r").*\)\s*", '', 
                              new_filename)
        
        #Convert to title type and remove leading and tailing spaces
        new_filename = new_filename.title().strip()
        
        #Note: os.replace is used instead of os.rename since os.replace 
        #automatically overwrites if a file with the new filename already exists
        os.replace(os.path.join(folder_path, filename), 
                  os.path.join(folder_path, new_filename + extension))
        
        return new_filename, extension
    
    
        
    def adjust_sample_rate(self, tracks=pd.DataFrame(), max_sr=48000, 
                           std_sr=44100, mode="nf", auto_genre=False):
        """Finds all .wav files and checks if their sample_rate is below max_sr. 
        If not so, the respective files are converted to the user specified
        sample rate std_sr
        Note: standard resolution is 16 bit
        
        Parameters:
        tracks (opt. - pd.Dataframe): 
            Dataframe with paths to the tracks to be processed
        max_sr (opt. - int): 
            maximum allowed sample rate (default: 48000 Hz)
        std_sr (opt. - int): 
            standard sample rate to which files with a sample rate higher than 
            max_sr should be converted
        mode (opt. - str): 
            which directory should be considered.
            - "nf": only consider the files in self.base_dir
            - "lib": only consider the files in the track library
        auto_genre (opt.): 
            Whether the genre should be inserted based on the folder path 
            (default: False). Else the old genre value will be kept
            
        Returns:
        doc: documentation of wave files and whether they were changed
        """
        #If tracks is a str but it is empty, the track_df or lib_df are used 
        # (if a mode is specified)
        if type(tracks)==str and tracks=="": 
            if mode =="nf":
                tracks = self.file_df if not self.file_df \
                    else self.read_tracks(self, directory=self.nf_dir, 
                                          mode="independent")
            elif mode == "lib":
                tracks = self.lib_df if not self.lib_df.empty \
                    else self.read_tracks(self, directory=self.lib_dir,
                                          mode="independent")
            else:
                raise ValueError("mode must be either 'new' or 'lib' or "
                                 + "tracks parameter must be a dataframe")
        #If tracks is a dataframe, it is processed. If it is empty, the 
        # track_df or lib_df are used (if a mode is specified)
        elif type(tracks)==pd.core.frame.DataFrame:
            if tracks.empty:
                if mode =="nf":
                    tracks = self.file_df if not self.file_df.empty \
                        else self.read_tracks(self, directory=self.nf_dir, 
                                              mode="independent")
                elif mode == "lib":
                    tracks = self.lib_df if not self.lib_df.empty \
                        else self.read_tracks(self, directory=self.lib_dir,
                                              mode="independent")
                else:
                    raise ValueError("mode must be either 'new' or 'lib' or "
                                     + "tracks parameter must be a dataframe")
        #If tracks is a non-empty string, it is converted to a Path and it is
        # checked whether the Path exists and it is a wav file
        elif type(tracks)==str and not tracks=="":
            filepath = Path(tracks)
            
            if filepath.exists() and filepath.suffix == ".wav":
                self.adjust_sr(filepath, max_sr, std_sr, auto_genre)
                return
            else:
                raise OSError("Filepath doesn't point to a wav file")
        #If tracks is a Path it is checked whether the Path exists and it is a 
        # wav file
        elif type(tracks)== type(Path()):   
            if filepath.exists() and filepath.suffix == ".wav":
                self.adjust_sr(filepath, max_sr, std_sr, auto_genre)
                return
            else:
                raise OSError("Filepath doesn't point to a wav file")
        else:
            raise ValueError("Invalid File Format: tracks must be a pandas "
                             +"Dataframe, a string containing a filepath or a "
                             +"pathlib.WindowsPath object")
        
        #Note: in case of a single file to process, the function automatically
        #processes it and returns. The following code is therefore only executed
        #if tracks is a dataframe with multiple entries 
        for index, row in tracks.loc[tracks.extension ==".wav"].iterrows():
            filepath = Path(row.folder, row.filename + ".wav")
            
            try:
                self.adjust_sr(filepath, max_sr, std_sr, auto_genre)
            except Exception as e:
                self.file_df = self.add_exception(
                    self.file_df, col = "status",
                    msg=f"sample rate adjustment error: {e.__class__} : {e}", 
                    index = index)
                self.file_df.loc[index, "status"] = "Error during sample rate adjustment"
            else:
                self.file_df.loc[index, "status"] = "sample rate checked"
            
    def adjust_sr(self, filepath, max_sr=48000,  std_sr=44100, 
                  auto_genre=False):
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
        auto_genre (opt.): whether the genre should be inserted based on the 
                           folder path (default: False). Else the old genre 
                           value will be kept
            
        Returns:
        None
        """
        
        data, sr = soundfile.read(filepath)
        
        if sr>max_sr:
            # Get the metadata (will be deleted during resampling)
            file = music_tag.load_file(filepath)
            metadata = {"genre":file["genre"].first,
                        "artist":file["artist"].first,
                        "title":file["title"].first}
            
            # Resample the data
            resampled_data = resample(data, int(len(data)*(std_sr/sr)))
            soundfile.write(filepath, resampled_data, std_sr, subtype='PCM_16')
            
            if auto_genre:
                self.set_metadata_auto(filepath, update_genre=True)
            else:
                self.set_metadata (filepath, **metadata)
    
    def set_metadata_auto (self, filepath, genre = "", 
                           adj_genre=False, adj_art_tit=True):
        """Automatically sets the artist, title and genre metadata of the file
        provided via the filepath to the values provided via the filename and 
        folderpath
        
        Paramters:
        filepath (str or pathlib.WindowsPath): absolute path to the file to be 
                                               edited
        genre (str): genre of the file (possible to specify manually)
        adj_genre (bool): Whether the genre should be updated (default: False)
                           Note: if a genre is specified manually via the 'genre'
                           parameter, then the genre is updated according to its 
                           value
        adj_art_tit (bool): Whether The Artist and Title should be updated
        
        Return:
        None"""
        
        if type(filepath)==str:
            filepath=Path(filepath)
        elif type(filepath)!=type(Path()):
            raise ValueError("filepath must be of type str or "
                             + f"pathlib.WindowsPath, not {type(filepath)}")
        
        artist, title = [t.strip() for t in
                         filepath.stem.split(" - ", maxsplit=1)]
        
        if genre or adj_genre:
            if not genre:
                genre = str(filepath.parents[0]).replace(
                    (str(self.lib_dir))+"\\","").replace ("\\"," - ")
            
            if not adj_art_tit:
                self.set_metadata(filepath, genre=genre)
            else:
                self.set_metadata(filepath, artist=artist, 
                                  title=title, genre=genre)
        elif adj_art_tit:
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
        
        
        if filepath.suffix in [".mp3", ".wav", ".aiff"]:
            file = music_tag.load_file(filepath)   
        else: 
            raise ValueError(f"Invalid file format: {filepath.suffix}")
        
        for key in kwargs.keys():
            file[key] = kwargs[key]
        file.save()
    
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
            if mode == "metadata":
                file_path = Path(self.nf_dir, row["folder"], 
                                 row.filename + row["extension"])
                
                #Extract the goal directory from the genre metadata
                try:
                    file = music_tag.load_file(file_path)
                    library_dir = Path(str(file["genre"].first).replace(" - ", 
                                                                        "/"))
                    file_df.loc[index, "goal_dir"]=str(library_dir)
                except Exception as e:
                    file_df = self.add_exception(
                        file_df, col = "status",
                        msg=f"Genre extraction error: {e.__class__} : {e}", 
                        index = index)
                    file_df.loc[index, "status"] = "Error during Genre extraction"            
            elif mode=="namesearch":
                closest_match = difflib.get_close_matches(row.filename, 
                                                          lib_df.filename.tolist(), 
                                                          n=1, cutoff=0.6)
                if closest_match:
                    res = lib_df.loc[lib_df.filename==closest_match[0]]
                    
                    #Only use first match
                    res = res.folder.to_list()[0] + "/"\
                        + res.filename.to_list()[0]\
                        + res.extension.to_list()[0]
                    
                    #Use all matches that were found
                    # if res.shape[0]==1:
                    #     res = res.folder.to_list()[0] + "/"\
                    #         + res.filename.to_list()[0]\
                    #         + res.extension.to_list()[0]
                    # else:
                    #     res = " | ".join([row.folder + "/"
                    #                      + row.filename
                    #                      + row.extension
                    #                      for i,row in res.iterrows()])
                               
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
            if "include" in file_df.columns and row.include==False: continue
            
            #Determine the path to the file
            file_path = Path(self.nf_dir, row["folder"], 
                             row["filename"] + row["extension"])
            
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
                            os.replace(file_path, 
                                       Path(self.lib_dir,
                                            gd.with_suffix(''),
                                            row["extension"])
                                       )
                            
                            #If the old file in the library had a different 
                            # extension than the new file, delete the old file
                            if not gd.suffix == row["extension"]:
                                os.remove(Path(self.lib_dir, gd))
                                
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
                                                file_path.name))
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
    
    def reset_goal_folder(self):
        self.file_df = self.file_df.loc[:,"goal_dir"] = ""
    
    def reset_lib_df(self):
        """Clears the entries in the self.lib_df dataframe
        
        Parameters:
        None
            
        Returns:
        None
        """
        self.lib_df = pd.DataFrame(columns=["folder", "filename", "extension"])
        
    def reset_file_df(self):
        """Clears the entries in the self.file_df dataframe
        
        Parameters:
        None
            
        Returns:
        None
        """
        self.file_df = pd.DataFrame(columns=["folder", "goal_dir", "filename",
                                             "old_filename", "extension", 
                                             "exceptions", "status", 
                                             "create_missing_dir"])    
        
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
    
    # nf_dir = r"C:\Users\davis\Downloads\SCDL test\00_General\new files"
    # lib_dir = r"C:\Users\davis\Downloads\SCDL test"
    # LibMan = LibManager(lib_dir, nf_dir)
    LibMan = LibManager()
    # lib_df = LibMan.read_dir()
    track_df = LibMan.read_tracks(r"C:\Users\davis\Downloads\SC DL", mode="replace")
    # file_df = LibMan.determine_goal_folder(mode="namesearch")
    # 
    # rename_doc = LibManLibMan.process_directory()
    # track_df = LibMan.move_to_library()
    
    
    