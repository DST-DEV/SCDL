from fuzzywuzzy import process
import textdistance
import difflib
import os
import pandas as pd
from pathlib import Path



def read_dir(directory=None):
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

def find_closest_match(query, choices):
    """
    Find the closest match of a query string in a list of choices.
    
    Args:
        query (str): The query string to find a match for.
        choices (list of str): The list of strings to search for a match in.
        
    Returns:
        str: The closest matching string from the choices list.
    """
    closest_match, score = process.extractOne(query, choices)
    return closest_match

def find_closest_match2(query, choices):
    """
    Find the closest match of a query string in a list of choices using Jaccard index.
    
    Args:
        query (str): The query string to find a match for.
        choices (list of str): The list of strings to search for a match in.
        
    Returns:
        str: The closest matching string from the choices list.
    """
    closest_match = max(choices, key=lambda x: textdistance.jaccard.normalized_similarity(query, x))
    return closest_match

def find_closest_match3(query, choices):
    """
    Find the closest match of a query string in a list of choices using difflib.
    
    Args:
        query (str): The query string to find a match for.
        choices (list of str): The list of strings to search for a match in.
        
    Returns:
        str: The closest matching string from the choices list.
    """
    closest_match = difflib.get_close_matches(query, choices, n=5, cutoff=0.6)
    if closest_match:
        return closest_match[:5]
    else:
        return None

# Example usage:
choices = ["apple", "banana", "orange", "grape", "watermelon"]
query = "appl"
closest_match = find_closest_match3(query, choices)
print("Closest match to '{}': {}".format(query, closest_match))
