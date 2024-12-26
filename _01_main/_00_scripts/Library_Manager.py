#%% Imports
#General imports
import re
import time
import numpy as np
import pandas as pd

#Soundfile adjustment imports
import music_tag
import wave
import soundfile
import unicodedata
from scipy.signal import resample
import pyaudacity as audacity       #Audacity API

#File Handling imports
import os
import shutil
import difflib
import pathlib
from pathlib import Path
from pathlib import PurePath

#%% LibManager Class
class LibManager:
    ob_strs = ["premiere", "P R E M I E R E", "free download", "free dl", 
               "Free DL", "FreeDL", "exclusive", "|", "preview", "sindex", 
               "motz", "OUTNOW"]        #common obsolete strings
    
    def __init__(self, lib_dir = None, nf_dir = None, music_dir = None,
                 excl_lib_folders=["00_Organization", "Sets"], **kwargs):
        #set the standard directory for the code to work in (if none is provided
        # by the user, use the downloads folder)
        if type(lib_dir)==str:
            self.lib_dir = Path(lib_dir) 
        elif type(lib_dir)==type(None) or type(lib_dir)==type(Path()):
            self.lib_dir = lib_dir or Path("C:/Users/davis/00_data/04_Track_Library")
        
        if (type(music_dir)==str or type(music_dir)==type(Path())) \
            and os.path.exists(Path(music_dir)):
            self.music_dir = Path(music_dir) 
        else:
            self.music_dir = None

        if type(nf_dir)==str:
            self.nf_dir = Path(nf_dir) 
        elif type(nf_dir)==type(None) or type(nf_dir)==type(Path()):
            self.nf_dir = nf_dir or Path(self.lib_dir, 
                                           "00_Organization/00_New_files")
        
        self.excl_lib_folders = excl_lib_folders
        
        self.file_df = pd.DataFrame(columns=["directory", "folder", "filename", 
                                             "old_filename", 
                                             "goal_dir", "goal_fld", "goal_name", 
                                             "extension", 
                                             "exceptions", "status", 
                                             "create_missing_dir"])
        self.lib_df = pd.DataFrame(columns=["folder", "filename", "extension"])
        


    def read_dir (self, update_progress_callback=False, **kwargs):
        """Finds all mp3 & wav files within the library directory and its 
        substructure.
        
        Parameters:
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            self.lib_df (pandas DataFrame): 
                Dataframe with information on the filename, file extension and 
                folder of all found files
        """
        self.lib_df = self.read_files(self.lib_dir,
                                      update_progress_callback 
                                      = update_progress_callback)
        return self.lib_df
            
    def read_files(self, directory, update_progress_callback=False, 
                   excluded_folders = [], **kwargs):
        """Finds all mp3 & wav files within a directory and its substructure.
        
        Parameters:
            directory (folderpath as str or path-like object): 
                top-level directory for the code to work in
            excluded_folders [list of str]: 
                folders to exclude (default: '00_General')
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            doc (pandas DataFrame): 
                Dataframe with information on the filename, file extension and 
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
        
        files_array = np.array(["folder","filename","ext"])[np.newaxis,:]
        
        n_folders = 0
        for root, _, files in os.walk(directory):
            if not any(excluded in root for excluded in excluded_folders 
                   if excluded!=""):
                n_folders+=1
        
        #Search for all mp3 & wav files in the directory, including subdirectories
        i = 0
        prog = 0
        
        results = []

        # Use os.walk with early exclusion of unwanted folders
        for root, _, files in os.walk(directory):
            #Skip the excluded folders:
            if any(excluded in root for excluded in excluded_folders 
                   if excluded!=""):
                continue

            # Filter relevant files and collect their attributes
            for file in files:
                if file.endswith((".mp3", ".wav")):
                    relative_folder = str(Path(root).relative_to(directory))
                    file_stem = Path(file).stem
                    file_ext = Path(file).suffix
                    results.append((relative_folder, file_stem, file_ext))
            
            #Update progress bar
            if callable(update_progress_callback):
                i +=1
                if i>=.0499*n_folders:
                    prog +=round(i/n_folders*100,3)
                    i=0
                    update_progress_callback(int(np.ceil(prog)))
                    
        # Create a DataFrame directly from the results list
        doc = pd.DataFrame(results, columns=["folder", "filename", "extension"])
        doc["directory"] = str(directory)
        doc = doc.loc[:, ["directory", "folder", "filename", "extension"]]
        
        return doc
    
    def read_tracks(self, update_progress_callback=False, 
                    directory=None, mode="replace", **kwargs):
        """Finds all mp3, wav and aiff files within a directory and its substructure.
        
        Parameters:
            directory (opt): 
                top-level directory for the code to work in. If no directory 
                is provided, then the standard_directory (cf. self.nf_dir) is 
                used
            mode (opt. - str): 
                Whether to replace or append to existing version of the 
                self.file_df or dont change the self.file_df at all 
                (default: replace)
                -"replace": Replace the current self.file_df
                - "append": Append to the current self.file_df
                - "independent": dont interact with the self.file_df
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
                           
        
        Returns:
            file_df (pandas DataFrame):  
                a Dataframe containing information on the found mp3 and wav 
                files in the directory and its substructure
        """
        
        if mode not in ["replace", "append", "independent"]:
            raise ValueError ("Invalid value for parameter 'mode'. " 
                              + "Must be either 'replace', 'append' or "
                              + "'independent'")
        
        #read the files (if no directory is provided, use the standard one)
        
        file_df = self.read_files(directory = directory or self.nf_dir,
                                  excluded_folders = [""],
                                  update_progress_callback = 
                                      update_progress_callback)
        
        #add additional columns for later
        n_files = len(file_df.index)
        file_df = file_df.assign(goal_dir=[""]*n_files,
                                 goal_fld=[""]*n_files,
                                 goal_name=[""]*n_files,
                                 old_filename = [""]*n_files,
                                 exceptions=[""]*n_files,
                                 status=[""]*n_files,
                                 create_missing_dir=[False]*n_files)
        file_df.reindex(columns=["directory", "folder", "filename", "old_filename", 
                                 "goal_dir", "goal_fld", "goal_name", "extension", 
                                 "exceptions", "status", "create_missing_dir"])
        
        if mode == "append":
            self.file_df = pd.concat([self.file_df, file_df])
            return self.file_df
        elif mode== "replace":
            self.file_df = file_df
            return self.file_df
        elif mode=="independent":
            return file_df
    
    # def prepare_new_files(self, update_progress_callback=False):
    #     """Runs the prepare files function for the new files dataframe
        
    #     Parameters:
    #         update_progress_callback (function handle - optional):
    #             Function handle to return the progress (Intended for usage in 
    #             conjunction with PyQt6 signals). 
                
    #     Returns:
    #         self.file_df (pandas DataFrame): 
    #             Pandas Dataframe with the updated files
    #     """
        
    #     self.file_df = self.prepare_files(self.file_df.copy(deep=True), 
    #                                       update_progress_callback)
    #     return self.file_df
    
    # def prepare_lib_files (self, update_progress_callback=False):
    #     """Runs the prepare files function for the library files dataframe
        
    #     Parameters:
    #         update_progress_callback (function handle - optional):
    #             Function handle to return the progress (Intended for usage in 
    #             conjunction with PyQt6 signals). 
                
    #     Returns:
    #         self.lib_df (pandas DataFrame): 
    #             Pandas Dataframe with the updated files
    #     """
        
    #     self.lib_df = self.prepare_files(self.lib_df.copy(deep=True), 
    #                                      update_progress_callback)
    #     return self.lib_df
    
    def prepare_files (self, df_sel=None,
                       adj_fnames = True,
                       adj_art_tit = True,
                       adj_genre = True, 
                       update_progress_callback=False,
                       prog_bounds = [0,100], **kwargs):
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
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
            prog_bounds (list or tuple - optional):
                lower and upper bound in which to change the progress bar
            
        Returns:
            file_df (pandas DataFrame):  
                updated version of the file_df dataframe
        
        """
        if  isinstance(df_sel, str) and df_sel in ("nf", "lib"):
            if df_sel == "nf":
                df = self.file_df.copy(deep=True)
            elif df_sel == "lib":
                df = self.lib_df.copy(deep=True)
            if df.empty:
                raise ValueError("Dataframe must be non empty")
        elif isinstance(df_sel, pd.core.frame.DataFrame):
            if not df_sel.empty:
                df = df_sel.copy(deep=True)
            else: 
                raise ValueError("Dataframe must be non empty")
        else:
            ValueError("Parameter df_sel must be either a string of value 'nf'",
                       " or 'lib', or a pandas Dataframe")
        
        if not "status" in df.columns:
            df["status"] = ""
        
        #Prepare Progressbar variables
        if callable(update_progress_callback):
            n_files = len(df.index)
            i=0
            prog=prog_bounds[0]
            update_fac = (prog_bounds[1]-prog_bounds[0])/100
        
        df_incl = df.loc[df.include].copy(deep=True) \
            if "include" in df.columns else df.copy(deep=True)
        
        #Iterate over Dataframe
        for index, row in df_incl.iterrows():
            if adj_fnames:
                #standarize filename
                filename, ext = self.adjust_fname (row["filename"] 
                                                   + row["extension"], 
                                                   Path(row["directory"], 
                                                        row["folder"]))
                df.loc[index, "old_filename"] = row["filename"]
                df.loc[index, "filename"] = filename
            else:
                filename, ext = row["filename"], row["extension"]
                
            if adj_art_tit or adj_genre:
                #Adjust metadata
                file_path = Path(row["directory"], row["folder"], 
                                 filename + ext)
                try:
                    self.set_metadata_auto(file_path,
                                           adj_art_tit=adj_art_tit,
                                           adj_genre = adj_genre,
                                           directory=row.directory)
                except Exception as e:
                    df = self.add_exception(
                        df, col = "status",
                        msg=f"Metadata error: {e.__class__} : {e}", 
                        index = index)
                    df.loc[index, "status"] = "Metadata error"
                else:
                    df.loc[index, "status"] = "Renamed and Metadata adjusted"
            
            #Update progress bar
            if callable(update_progress_callback):
                i +=1
                if i>=.0499*n_files:
                    prog +=round(i/n_files*100,3)*update_fac
                    i=0
                    update_progress_callback(int(np.ceil(prog)))
        
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
            filename (str): 
                Name of the file to be processed
            folder_path (folderpath as str or path-like object): 
                path of the folder in which the file is saved
        
        Returns:
            new_filename (str): 
                Adjusted filename
        """
        new_filename, extension = os.path.splitext(filename)
        
        #Step 1: Remove obsolete strings (both standalone and in round brackets)
        #Note: Obsolete strings within square brackets do not need to be 
        # removed in this step since all square brackets are removed anyways 
        # later
        ob_strs_pattern = "(" +  "|".join(self.ob_strs) + ")"
        new_filename = re.sub(r"\([^)]*" + ob_strs_pattern + "[^)]*\)", "", 
                             new_filename, 
                             flags=re.IGNORECASE)
        new_filename = re.sub(ob_strs_pattern + r"[:_]*", "", 
                             new_filename, 
                             flags=re.IGNORECASE)
        
        #Step 2: Replace lowercase and uppercase variants of "Remix", "Edit",
        #and "Mashup" by the title form
        new_filename = re.sub(r"(remix|edit|mashup|bootleg)", 
                              lambda match: match.group(1).title(), 
                              new_filename,
                              flags=re.IGNORECASE)
        
        #Step 3: Remove all content within square brackets (except for the 
        # ones which include the words 'Remix', 'Edit' or 'Mashup')
        new_filename = re.sub(r'\[(?![^\]]*(Mashup|Edit|Remix|Bootleg)).*?\]', 
                              '', 
                              new_filename,
                              flags=re.IGNORECASE)
        
        #Step 4: Replace square  brackets around "Remix", "Edit", or "Mashup"
        # by round brackets
        # Note: searching for lowercase and uppercase versions of the string is 
        # not necessary, since they were replaced by the title version in a 
        # previous step
        new_filename = re.sub(r"\[(.*?(?:Remix|Edit|Mashup|Bootleg).*?)\]", 
                              lambda match: ' (' + match.group(1) + ')', 
                              new_filename)
        
        #Step 5: Remove all round brackets which contain the words 'ft', 
        # 'feat', 'prod',  or 'records'
        # Note: the matching is case-insensitive
        # Note: the brackets are only removed if the words are either:
        # - At the start of the bracket, followed by a white space
        # - At the end of the bracket, leaded by a white space
        # - Somewhere within the bracket, leaded and followed by a white space
        # Note: The word is also matched if it is followed by a "." (e.g. "ft.")
        excl = "|".join(["ft", "prod","feat", "records"])
        pattern1 = r"\([^)]*\s+(" + excl + r")[.]*\s+[^)]*\)"
        pattern2 = r"\((" + excl + r")[.]*\s+[^)]*\)"
        pattern3 = r"\([^)]*\s+(" + excl + r")[.]*\)"
        pattern = "(" + ")|(".join([pattern1, pattern2, pattern3]) + ")"
        new_filename = re.sub(pattern, '', new_filename, flags=re.IGNORECASE)
        
        #Step 6: Replace the weird long hyphen that is sometimes used in the 
        # track title
        new_filename = new_filename.replace(chr(8211), "-")
        
        #Step 7: Replace double hypens
        new_filename = re.sub(r"-+", " - ", new_filename)
        
        
        #Step 8: Change capitalization
        #Artist:
        # - Single letters are converted to lowercase (e.g. "Artist x Artist")
        # - Words with 3-4 characters are not changed (E.g. "DJ ...", "MC ...")
        # - Words with more than 4 characters are capitalized. 
        #Track title:
        # - Title is Capitalized
        # - Content in round brackets is converted to title form (all words 
        #   capizalized)
        new_filename = re.sub(r"\s+", " ", new_filename)
        if " - " in new_filename:
            artist, *title = new_filename.split(" - ")
            title = " ".join(title).strip()
            
            artist = list(artist.strip().split(" "))
            for i, artist_i in enumerate(artist):
                if len(artist_i)==1:
                    artist[i] = artist_i.lower()
                elif len(artist_i)>=4:
                    artist[i] = artist_i.capitalize()
            artist = " ".join(artist)
        
            title_bracket = re.findall(r"(\([^)]*\))", title)
            if title_bracket:
                for i, title_bracket_i in enumerate(title_bracket):
                    title = title.replace(title_bracket_i, "")
                    
                    title_bracket[i] = title_bracket_i.title()
                title = title.strip().capitalize()
                title += " " + " ".join(title_bracket)
            else:
                title = title.strip().capitalize()

            new_filename = artist + " - " + title 
        
        #Step 9: rename the file
        #Note: os.replace is used instead of os.rename since os.replace 
        #automatically overwrites if a file with the new filename already exists
        os.replace(os.path.join(folder_path, filename), 
                  os.path.join(folder_path, new_filename + extension))
        
        return new_filename, extension
        
    def adjust_sample_rate(self, tracks=pd.DataFrame(), max_sr=48000, 
                           std_sr=44100, mode="nf", 
                           update_progress_callback=False, 
                           prog_bounds = [0,100], **kwargs):
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
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
            prog_bounds (list or tuple - optional):
                lower and upper bound in which to change the progress bar
            
        Returns:
            doc (pandas DataFrame): 
                documentation of wave files and whether they were changed
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
                
            if not "status" in tracks.columns:
                tracks["status"] = ""
                
        #If tracks is a dataframe, it is processed. If it is empty, the 
        # track_df or lib_df are used (if a mode is specified)
        elif type(tracks)==pd.core.frame.DataFrame:
            if tracks.empty:
                if mode =="nf":
                    if self.file_df.empty:
                        tracks = self.read_tracks(self, directory=self.nf_dir, 
                                                  mode="independent")
                        save_mode = "None"
                    else:
                        tracks = self.file_df.copy(deep=True)
                        save_mode = "file_df"
                elif mode == "lib":
                    if self.lib_df.empty:
                        tracks = self.read_tracks(self, directory=self.lib_dir,
                                                  mode="independent")
                        save_mode = "None"
                    else:
                        tracks = self.lib_df.copy(deep=True)
                        save_mode = "lib_df"
                else:
                    raise ValueError("mode must be either 'new' or 'lib' or "
                                     + "tracks parameter must be a dataframe")
            else:
                save_mode = "None"
                
            if not "status" in tracks.columns:
                tracks["status"] = ""
                
        #If tracks is a non-empty string, it is converted to a Path and it is
        # checked whether the Path exists and it is a wav file
        #If tracks is a Path it is checked whether the Path exists and it is a 
        # wav file
        elif (type(tracks)==str and not tracks=="") or \
            type(tracks)== type(Path()):
            filepath = Path(tracks) if type(tracks)== str else tracks
            
            if filepath.exists() and filepath.suffix == ".wav":
                self.adjust_sr(filepath, max_sr, std_sr)
                
                #Update progressbar
                if callable(update_progress_callback):
                    update_progress_callback(prog_bounds[1])
                return
            else:
                raise OSError("Filepath doesn't point to a wav file")
        else:
            raise ValueError("Invalid File Format: tracks must be a pandas "
                             +"Dataframe, a string containing a filepath or a "
                             +"type(Path()) object")
        
        #Note: in case of a single file to process, the function automatically
        #processes it and returns. The following code is therefore only executed
        #if tracks is a dataframe with multiple entries 
        
        #Prepare Progressbar variables
        if callable(update_progress_callback):
            n_files = sum(tracks.extension ==".wav")
            i=0
            prog=prog_bounds[0]
            update_fac = (prog_bounds[1]-prog_bounds[0])/100
        
        #Iterate over files
        for index, row in tracks.loc[tracks.extension ==".wav"].iterrows():
            filepath = Path(row["directory"], row["folder"], 
                            row["filename"] + ".wav")
            
            try:
                self.adjust_sr(filepath, max_sr, std_sr)
            except Exception as e:
                tracks = self.add_exception(
                    tracks, col = "status",
                    msg=f"sample rate adjustment error: {e.__class__} : {e}", 
                    index = index)
                tracks.loc[index, "status"] = "Error during sample rate adjustment"
            else:
                tracks.loc[index, "status"] = "sample rate checked"
            
            #Update progress bar
            if callable(update_progress_callback):
                i +=1
                if i>=.0499*n_files:
                    prog +=round(i/n_files*100,3)*update_fac
                    i=0
                    update_progress_callback(int(np.ceil(prog)))
        
        
        #Update progressbar
        if callable(update_progress_callback):
            update_progress_callback(prog_bounds[1])
        
        #If the tracks were extracted from the class dataframes, then save
        # the tracks df to them. Else return the tracks df
        if save_mode=="file_df": self.track_df = tracks
        elif save_mode=="lib_df": self.lib_df = tracks
        else: return tracks
            
    def adjust_sr(self, filepath, max_sr=48000,  std_sr=44100):
        """Checks if their sample_rate of the file specified by the filepath
        is below max_sr. 
        If not so, the respective files are converted to the user specified
        sample rate std_sr
        Note: standard resolution is 16 bit
        
        Parameters:
            filepath (str or type(Path())): 
                filepath to the track to be processed
            max_sr (opt. - int): 
                maximum allowed sample rate (default: 48000 Hz)
            std_sr (opt. - int): 
                standard sample rate to which files with a sample rate higher 
                than max_sr should be converted
            
        Returns:
            None
        """
        
        #Read the file (Note: rb mode is essential here to not damage the file) 
        with soundfile.SoundFile(filepath, 'rb') as sf:
            bd = sf.subtype.replace("PCM_", "")
            bd = int(bd) if not bd=="FLOAT" else 32 
            sr = sf.samplerate
            metadata = sf.copy_metadata()
            data= sf.read()
            #Note: The bid depth of 32 bit files cant be read correctly 
            # (always returns "FLOAT"). Hence this workaround

        if sr>max_sr:
            # Resample the data
            resampled_data = resample(data, int(len(data)*(std_sr/sr)))
            soundfile.write(filepath, resampled_data, std_sr, subtype='PCM_16')
            self.set_metadata(filepath, **metadata)
        elif bd > 16:   #If the bit depth is larger than 16 bit
            soundfile.write(filepath, data, sr, subtype='PCM_16')
            self.set_metadata(filepath, **metadata)
            
    def set_metadata_auto (self, filepath, directory = "", genre = "", 
                           adj_genre=False, adj_art_tit=True,
                           exp_wav=False):
        """Automatically sets the artist, title and genre metadata of the file
        provided via the filepath to the values provided via the filename and 
        folderpath
        
        Paramters:
            filepath (str or type(Path())): 
                Absolute path to the file to be edited
            directory (str or type(Path())): 
                Absolute path of the parent directory. If no genre is specified
                explicitly, this path is removed from the parent path of the 
                filepath to determine the genre automatically.
            genre (str): 
                genre of the file (possible to specify manually)
            adj_genre (bool): 
                Whether the genre should be updated (default: False)
                Note: if a genre is specified manually via the 'genre'
                parameter, then the genre is updated according to its value
            adj_art_tit (bool): 
                Whether The Artist and Title should be updated
            exp_wav (bool):
                Whether the track should be imported and exported in Audacity.
                This option is only relevant for .wav files as their metadata
                is not correctly displayed in the Windows Explorer and Recordbox
                after the adjustment via the music_tag package.
                
                Note: For this feature, Audacity must be opened and the 
                "mod-script-pipe" option in the Edit->Preferences->Modules must 
                be enabled
        
        Return:
            None
        """
        
        if type(filepath)==str:
            filepath=Path(filepath)
        elif type(filepath)!=type(Path()):
            raise ValueError("filepath must be of type str or "
                             + f"type(Path()), not {type(filepath)}")
        
        artist, title = [t.strip() for t in
                         filepath.stem.split(" - ", maxsplit=1)]
        
        if genre or adj_genre:
            if not genre:
                directory = directory if directory else self.lib_dir
                genre = str(filepath.parents[0]).replace(str(directory),"")
                genre = re.sub(r"^\\", "", genre).replace ("\\"," - ")
            
            if not adj_art_tit:
                self.set_metadata(filepath, genre=genre)
            else:
                self.set_metadata(filepath, artist=artist, 
                                  title=title, genre=genre)
        elif adj_art_tit:
            self.set_metadata(filepath, artist=artist, title=title)

        
    def set_metadata(self, filepath, exp_wav=False, **kwargs):
        """Writes the metadata provided via the **kwargs parameter into the 
            file provided by the filename
            Note: Supported file formats: .mp3, .wav, .aiff
        
        Parameters:
            filepath (str or type(Path())): 
                absolute path to the file to be edited
            exp_wav (bool):
                Whether the track should be imported and exported in Audacity.
                This option is only relevant for .wav files as their metadata
                is not correctly displayed in the Windows Explorer and Recordbox
                after the adjustment via the music_tag package.
                
                Note: For this feature, Audacity must be opened and the 
                "mod-script-pipe" option in the Edit->Preferences->Modules must 
                be enabled
            **kwargs: 
                metadata to be edited. Valid metadata fields are:
                - artist
                - title
                - genre
                - album
            
        Returns:
            None
        """
        valid_keys = ["artist", "title", "genre", "album"]
        
        if type(filepath)==str:
            filepath=Path(filepath)
        elif type(filepath)!=type(Path()):
            raise ValueError("filepath must be of type str or "
                             + f"type(Path()), not {type(filepath)}")
        
        if not filepath.exists():
            raise FileNotFoundError(f"File with path {filepath} doesn't exist")

        if filepath.suffix in ".mp3":
            file = music_tag.load_file(filepath) 
            
            for key, value in kwargs.items():
                if key in valid_keys:
                    file[key] = value
                
            file.save()
        elif filepath.suffix == ".wav":
            #Copy current metadata
            with soundfile.SoundFile(filepath, 'r') as sf:
                meta = sf.copy_metadata()
            
            #Add metadata which isn't updated to the kwargs
            for key in ["genre", "artist", "title"]:
                kwargs.setdefault(key, meta.get(key))
            
            #Open file with wave package and rewrite contents (gets rid of any problematic 
            # header data)
            filepath_str = str(filepath) #wave package needs string path
            with wave.open(filepath_str, 'rb') as f_original:
                # Read the original audio data
                params = f_original.getparams()
                audio_frames = f_original.readframes(params.nframes)

            with wave.open(filepath_str, 'wb') as f_adjusted:
                f_adjusted.setparams(params)
                f_adjusted.writeframes(audio_frames)

            #Insert metadata with soundfile package
            with soundfile.SoundFile(filepath, 'r+') as sf:
                for key, value in kwargs.items():
                    if key in valid_keys:
                        sf.__setattr__(key, value)
        else: 
            raise ValueError(f"Invalid file format: {filepath.suffix}")

    def convert_to_alphanumeric(self, input_string):
        """Convert an arbitrary string to its closest alphanumeric 
        representation  in standard ascii characters (remove non ascii 
        characters and convert diacritics to standard characters)
        
        Parameters:
            input_string (str): 
                the string to be converted
        
        Returns:
            alphanumeric_string (str): 
                the alphanumeric ascii representation of the string
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
                Dataframe containing information on the folder and filename of 
                all  files to be processed
            mode (str):
                Whether the genre metadata or the filename should be used to 
                determine the goal directory for the file
                Choices:
                    - 'metadata': Genre metadata is used as the goal folder 
                    - 'namesearch': Closest match of filename in the library 
                                    is used for the goal path
            
        Returns:
            file_df (pandas DataFrame): 
                updated version of the dataframe with information on occured 
                exceptions and the goal folder
        """
        
        if type(file_df) != pd.core.frame.DataFrame or file_df.empty:
            file_df = self.file_df if not self.file_df.empty \
                        else self.read_tracks()
        else:
            self.file_df = file_df

        if "include" in file_df.columns: 
            files_tbd = file_df.loc[file_df.include==True].copy(deep=True)
        else:
            files_tbd = file_df.copy(deep=True)
        
        if mode=="namesearch":
            lib_df = self.lib_df if not self.lib_df.empty else self.read_dir()
            
        for index, row in files_tbd.iterrows():
            if mode == "metadata":
                filepath = Path(row["directory"], row["folder"], 
                                row.filename + row["extension"])
                
                #Extract the goal directory from the genre metadata
                try:
                    if row["extension"]==".mp3":
                        file = music_tag.load_file(filepath)
                        library_fld = file["genre"].first.replace(" - ", "/")
                    elif row["extension"]==".wav":
                        with soundfile.SoundFile(str(filepath), 'r') as sf:
                            meta = sf.copy_metadata()
                        
                        library_fld = meta.get("genre") 
                        #Note: returns None if no genre data is present
                        library_fld = library_fld.replace(" - ", "/") \
                            if library_fld else ""
                        
                    if library_fld:
                        file_df.loc[index, "goal_dir"]=str(self.lib_dir)
                        file_df.loc[index, "goal_fld"]=library_fld
                    else:
                        file_df.loc[index, "goal_dir"]=""
                        file_df.loc[index, "goal_fld"]=""
                except Exception as e:
                    file_df = self.add_exception(
                        file_df, col = "status",
                        msg=f"Genre extraction error: {e.__class__} : {e}", 
                        index = index)
                    file_df.loc[index, "status"] = "Error during Genre extraction"            
            elif mode=="namesearch":
                closest_match = difflib.get_close_matches(row.filename, 
                                                          lib_df.filename.tolist(), 
                                                          n=1, cutoff=0.9)
                if closest_match:
                    res = lib_df.loc[lib_df.filename==closest_match[0]]
                    
                    #Only use first match
                    file_df.loc[index, "goal_dir"] = res.directory.to_list()[0]
                    file_df.loc[index, "goal_fld"] = res.folder.to_list()[0]
                    file_df.loc[index, "goal_name"] = res.filename.to_list()[0]\
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
                else:
                    file_df.loc[index, "goal_dir"] = ""
                    file_df.loc[index, "goal_fld"] = ""
                    file_df.loc[index, "goal_name"] = ""
            else:
                raise ValueError("mode must me either 'metadata' or "
                                 + f"'namesearch, not {mode}")
        
        self.file_df = file_df
        return file_df
    
    def del_doubles (self, exec_msg, msg_signals, df_sel="nf"):
        """Deletes the files in the file_df for which a corresponding file in 
        the library was found
        
        Parameters:
            df_sel (str or pandas.DataFrame): 
                Selection whether the duplicates should be deleted in the 
                library or the new files directory.
                - "nf": Delete duplicate files from new files 
                - "lib": Delete duplicate files from library
                - "ask": Ask individually for each file 
            exec_msg (PyQt Signal):
                PyQt6 signal to launch a message window
            msg_signals (PyQt Signal):
                Message signals class for further customization of the message 
                window
        
        Returns:
            None
        """
        #Check inputs
        if not (isinstance(df_sel, str) and df_sel in ("nf", "lib", "ask")):
            ValueError("Parameter df_sel must be either a string of value "
                       "'nf','lib', 'ask', or a pandas Dataframe")
        if self.file_df.empty:
            return
        
        #Ensure that user wants to delete double files
        msg = "You are about to delete duplicate files{}.\n"\
              + "Do you want to continue?"
        if df_sel=="nf":
            msg = msg.format(" in the new files directory")
        elif df_sel=="lib":
            msg = msg.format(" in the library directory")
        else:
            msg = msg.format("")
        msg_signals.edit_label_txt.emit(msg)
        response = exec_msg("Track Extraction Warning")
        
        if response:
            #Filter for rows to include
            if "include" in self.file_df.columns: 
                file_df = self.file_df.loc[(self.file_df.goal_name!="") 
                                          & (self.file_df.include==True)
                                          ].copy(deep=True)
            else:
                file_df = self.file_df.loc[(self.file_df.goal_name!="")
                                           ].copy(deep=True)
            
            df_sel_i = df_sel
            for i, row in file_df.iterrows():
                if df_sel == "ask":
                    msg = f"Do you want to delete the file \"{row.filename}\" "\
                          + "from the new files or the library?"
                    msg_signals.edit_label_txt.emit(msg)
                    msg_signals.msg_accept_txt.emit("New files")
                    msg_signals.msg_reject_txt.emit("Library")
                    msg_signals.msg_set_min_width.emit(350)
                    
                    df_sel_response = exec_msg("Track Extraction Warning")

                    df_sel_i = "nf" if df_sel_response else "lib"
                
                if df_sel_i == "nf":
                    filepath = Path(row.directory, row.folder, 
                                    row.filename + row.extension)
                    
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    
                    #Drop file from file_df
                    self.file_df.drop(index=i, inplace=True)
                elif df_sel_i == "lib":
                    filepath = Path(row.goal_dir, row.goal_fld, row.goal_name)
                    
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        
                    #Drop file from lib_df
                    i_lib = self.lib_df.loc[(self.lib_df.directory
                                             + self.lib_df.folder
                                             + self.lib_df.filename
                                             + self.lib_df.extension
                                             ==file_df.goal_dir[i]
                                             +file_df.goal_fld[i]
                                             +file_df.goal_name[i])].index
                    self.lib_df.drop(index=i_lib, inplace=True)
                    
            #Reset indices of class variables        
            if df_sel in ("nf", "ask"):
                self.file_df.reset_index(drop=True, inplace=True)
            if df_sel in ("lib", "ask"):
                self.lib_df.reset_index(drop=True, inplace=True)
        else:
            print("Deleting of duplicate files canceled by user")
    
    def move_to_library(self, file_df=None, replace_doubles = False,
                        exec_msg=False, msg_signals=None, 
                        exec_note=False, note_signals=None,**kwargs):
        """Moves the Tracks in the file_df in their respective folder based on 
        the entries in the goal folder column of the file_df
        
        Parameters:
            file_df (pd.DataFrame, optional): 
                Dataframe containing information on the folder and filename of 
                all files to be processed as well as the goal directory
            replace_doubles (bool):
                Whether new files which already exist in the library should be 
                replaced
            exec_msg (PyQt Signal - optional):
                PyQt6 signal to launch a message window
            msg_signals (PyQt Signal - optional):
                Message signals class for further customization of the message 
                window
            
        Returns:
            file_df (pandas DataFrame):  
                updated version of the dataframe with information on 
                occured exceptions
        """
        
        #Check inputs
        if type(file_df) != pd.core.frame.DataFrame or file_df.empty:
            file_df = self.file_df if not self.file_df.empty \
                        else self.read_tracks()
        file_df = file_df.copy(deep=True)
        lib_df = self.lib_df.copy(deep=True) if not self.lib_df.empty \
            else self.read_dir().copy(deep=True)
        
        #Iterate over all tracks
        if "include" in file_df.columns:
            file_df = file_df.loc[file_df.include==True]
        n_moved = 0
        for index, row in file_df.iterrows():
            # if "include" in file_df.columns and row.include==False: continue
            
            #Determine the path to the file
            filepath = Path(row["directory"], row["folder"], 
                             row["filename"] + row["extension"])
            
            #If a goal directory is specified
            if row.goal_dir:
                if row.goal_name:
                    #If the goal directory is a file, replace the file with 
                    #the new file
                    if not replace_doubles:
                        continue
                    try:
                        #Move the new file to the library
                        os.replace(filepath, 
                                   Path(row.goal_dir,
                                        row.goal_fld,
                                        Path(row.goal_name
                                             ).with_suffix(row["extension"]))
                                   )
                    except Exception as e:
                        self.file_df = self.add_exception(
                            self.file_df, col = "exceptions",
                            msg=f"Copying error for goal directory {row.goal_dir}: "
                                + f"{e.__class__} : {e}", 
                            index = index)
                    else:
                        n_moved +=1
                        self.file_df.drop(index = index, inplace=True)

                        #If the old file in the library had a different 
                        # extension than the new file, delete the old file
                        if not Path(row.goal_name).suffix == row["extension"]:
                            i_lib = self.lib_df.loc[(self.lib_df.directory
                                                    + self.lib_df.folder
                                                    + self.lib_df.filename
                                                    + self.lib_df.extension
                                                     ==row.goal_dir
                                                     + row.goal_fld
                                                     + row.goal_name)].index
                            if len(i_lib)>0:
                                try:
                                    os.remove(Path(row.goal_dir,
                                                   row.goal_fld,
                                                   row.goal_name))
                                except Exception as e:
                                    if not type(note_signals)==type(None) \
                                        and exec_note:
                                        msg = f"The file {row.goal_name} "\
                                              + "could not be removed from "\
                                              + "the library"
                                        note_signals.edit_label_txt.emit(msg)
                                        exec_note("File removal error")
                                else:
                                    #Drop file from lib_df
                                    self.lib_df.drop(index=i_lib, inplace=True)
                else:
                    #If the goal directory is a folder, then move the file 
                    # to this folder (Note: if there is already a file with
                    #the same name in the goal folder, then it is replaced)

                    #Check if goal directory exists and whether it should be 
                    #created if it doesn't exist
                    if not os.path.isdir (Path(row.goal_dir, row.goal_fld)):
                        if not row.create_missing_dir:
                            if not type(msg_signals)==type(None) and exec_msg:
                                msg = f"The folder {row.goal_fld} does not "\
                                    "exist. Should it be created?"
                                msg_signals.edit_label_txt.emit(msg)
                                response = exec_msg("File moving warning")
                            else:
                                response=False
                            
                            if not response:
                                self.file_df.loc[index, "status"] = \
                                    "Goal folder not found"
                                continue #continue with next track
                            
                        os.mkdir(Path(row.goal_dir, row.goal_fld))
                    
                    goal_path = Path(row.goal_dir, row.goal_fld, 
                                     filepath.name)
                    
                    if os.path.isfile(goal_path) and not replace_doubles:
                        self.file_df = self.add_exception(
                            self.file_df, col = "exceptions",
                            msg=f"File already exists in library", 
                            index = index)
                        continue
                    else:
                        try:
                            os.replace(filepath, goal_path)
                        except Exception as e:
                            self.file_df = self.add_exception(
                                self.file_df, col = "exceptions",
                                msg=f"Copying error for goal folder {row.goal_fld}: "
                                    + f"{e.__class__} : {e}", 
                                index = index)
                        else:
                            n_moved +=1
                            self.file_df.drop(index = index, inplace=True)
            else:
                self.file_df = self.add_exception(
                    self.file_df, col = "exceptions",
                    msg="No goal directory specified", 
                    index = index)
        
        self.file_df.reset_index(drop=True, inplace=True)
        
        #Notifiy about successfully moved files
        if not type(note_signals)==type(None) and exec_note:
            msg = f"Moved {n_moved} files"
            note_signals.edit_label_txt.emit(msg)
            exec_note("File moving success")
        
        return self.file_df
    
    def sync_music_lib(self, music_dir=None):
        """Copies all .mp3 files in the track library to a provided directory
        
        Parameters:
            music_dir (folderpath as str or path-like object):
                Folder in which to copy the files
        
        Returns:
            None
        """
        
        if (not music_dir or not os.path.exists(Path(music_dir))):
            if self.music_dir:
                music_dir = self.music_dir
            else:
                return

        files = self.lib_df if not self.lib_df.empty else self.read_dir()
        
        files = files.loc[files.extension==".mp3"]
        
        for i, file in files.iterrows():
            shutil.copy2(Path(file.folder, file.filename + ".mp3"),
                         Path(file.folder, file.filename + ".mp3"))
    
    def reset_goal_folder(self):
        """Resets the found goal directory and goal name
        
        Parameters:
            None
        
        Returns:
            None
        """
        
        self.file_df.loc[:,"goal_dir"] = ""
        self.file_df.loc[:,"goal_name"] = ""
    
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
        
    def add_exception(self, df, col, msg="", 
                      index = -1, key = "", search_col=" "):
        """Inserts an exception into a provided dataframe. The row can be
        specified via the index or a search key in a search column
        
        Parameters:
            df (pandas DataFrame): 
                Dataframe in which to insert the message
            col (str - optional):
                Name of the column in which to insert the exception message
            msg (str - optional):
                exception message
            index (int or Index object):
                Index of the row where to insert the exception
            key (str - optional):
                Key to search for the key for in the search_col for the 
                determination of the row where to insert the exception
            search_col (str - optional):
                In which column to search for the key for the determination of 
                the row where to insert the exception
        
        Returns:
            None
        """
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
                df.loc[-1] = [""]*len(df.columns)
                df.loc[-1, col]=msg
                df.loc[-1, search_col]=key
                df = df.reset_index(drop=True)
        else:
            raise ValueError("no valid index or search key and search column provided")
            
        return df

#%% Main        
if __name__ == '__main__':
    # nf_dir = Path("C:/Users", os.environ.get("USERNAME"), "Downloads", "music")
    # path = Path("C:/Users/davis/00_data/04_Track_Library/00_Organization/00_New_files")
    
    # nf_dir = r"C:\Users\davis\Downloads\SCDL test\00_General\new files"
    # lib_dir = r"C:\Users\davis\Downloads\SCDL test"
    # LibMan = LibManager(lib_dir, nf_dir)
    pass