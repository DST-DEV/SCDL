import os, re
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import pandas as pd
import unicodedata
import shutil

class MP3Renamer:
    ob_strs = ["premiere", "P R E M I E R E", "free download", "free dl", 
               "Free DL", "FreeDL", "exclusive", "|", "preview"]        #common obsolete strings
    
    def __init__(self, std_dir = None, lib_path = None):
        #set the standard directory for the code to work in (if none is provided
        # by the user, use the downloads folder)
        self.std_dir = std_dir or Path("C:/Users/davis/00_data/04_Track_Library/00_Organization/00_New_files")
        self.lib_path = lib_path or Path("C:/Users/davis/00_data/04_Track_Library")
        
        self.file_df = pd.DataFrame(columns=["folder", "filename", "new_filename",
                                             "exceptions", "processed"])

    def read_dir(self, directory=None):
        """Finds all mp3 files within a directory and its substructure. The 
        files are then striped of obsolete strings and their artist and title
        are inserted into the metadata information
        
        Parameters:
        directory (optional): top-level directory for the code to work in. If
        no directory is provided, then the standard_directory is used
        
        Returns:
        file_dict: dictionary with the foulders found to contain mp3 files as 
        keys and a list of the filenames as the value
        """
        
        #if no directory is provided, use the standard one
        directory = directory or self.std_dir
        
        #Search for all mp3 files in the directory, including subdirectories
        for root, _, files in os.walk(directory):
            music_files = [f for f in files if f.endswith(".mp3") | f.endswith(".wav")]
            if music_files:                       #check if there are files
               self.file_df = pd.concat([self.file_df,
                   pd.DataFrame(dict(folder=[root]*len(music_files),
                                     filename = music_files,
                                     new_filename = [""]*len(music_files),
                                     exceptions=[""]*len(music_files),
                                     processed=[False]*len(music_files)
                                     )
                                )
                   ])
               
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
        
        for index, row in file_df.loc[file_df.processed == False].iterrows():
            filename, ext = self.adjust_fname (row["filename"], row["folder"])
            
            self.file_df.loc[index, "new_filename"] = filename + ext
            
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
                self.file_df.loc[index, "processed"] = False
            else:
                self.file_df.loc[index, "processed"] = True
        
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
            file_df = self.read_dir()
        
        for index, row in file_df.iterrows():
            file_path = os.path.join(row["folder"], row["filename"])
            try:
                audio = MP3(file_path, ID3=EasyID3)
                library_dir = Path(audio["genre"].replace(" - ", "/"))
            except Exception as e:
                self.file_df.loc[index, "exceptions"] = f"{e.__class__} : {e}"
                self.file_df.loc[index, "processed"] = False
            else:
                try:
                    shutil.copy2(file_path,
                                 Path(self.lib_path, library_dir)
                                )
                except Exception as e:
                    self.file_df.loc[index, "exceptions"] = f"{e.__class__} : {e}"
                    self.file_df.loc[index, "processed"] = False
                else:
                    self.file_df.loc[index, "processed"] = True
        
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
        
if __name__ == '__main__':
    # std_dir = Path("C:/Users", os.environ.get("USERNAME"), "Downloads", "music")
    path = Path("C:/Users/davis/00_data/04_Track_Library/00_Organization/00_New_files")
    MP3r = MP3Renamer(path)
    
    rename_doc = MP3r.process_directory()
    
    
    