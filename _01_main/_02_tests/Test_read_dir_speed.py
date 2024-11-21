import os
import pandas as pd
import numpy as np
from pathlib import Path

#%% Variant 1: numpy array
# Variant 1a: vstack
def read_dir_1a (directory, excluded_folders=["00_Organization"]):
    files_array = np.array(["folder","filename","ext"])[np.newaxis,:]
    for root, _, files in os.walk(directory):
        #Exclude the excluded folders:
        if not any(excl in root for excl in excluded_folders if excl!=""):        
            music_files = np.array([[Path(f).stem, 
                                     Path(f).suffix] 
                                    for f in files 
                                    if f.endswith(".mp3") 
                                    or f.endswith(".wav")])
            
            if music_files.shape[0]>0:            #check if there are files
                music_files = np.hstack((np.full((music_files.shape[0],1), 
                                                 str(Path(root).relative_to(directory))), 
                                         music_files))
            
                files_array = np.vstack((files_array, music_files))
    
    doc = pd.DataFrame(columns=files_array[0,:],
                       data=files_array[1:,:])
    doc["directory"] = str(directory)
    return doc

# Variant 1b: Preallocating
def read_dir_1b (directory, excluded_folders=["00_Organization"]):
    files_array = np.full((20000,3),"")
    i=0
    for root, _, files in os.walk(directory):
        #Exclude the excluded folders:
        if not any(excl in root for excl in excluded_folders if excl!=""):        
            for file in files:
                if file.endswith((".mp3", ".wav")):
                    relative_folder = str(Path(root).relative_to(directory))
                    file_stem = Path(file).stem
                    file_ext = Path(file).suffix
                    files_array[i,:] = (relative_folder, file_stem, file_ext)
                    i+=1
    
    doc = pd.DataFrame(columns=["folder","filename","ext"],
                       data=files_array[:i,:])
    doc["directory"] = str(directory)
    return doc
                
#%% Variant 2: Pandas dataframe                
def read_dir_2 (directory, excluded_folders=["00_Organization"]):
    doc = pd.DataFrame(columns=["folder", "filename", "extension"])
    for root, _, files in os.walk(directory):
        #Exclude the excluded folders:
        if not any(excl in root for excl in excluded_folders if excl!=""):        
            music_files = np.array([[Path(Path(f).stem), Path(f).suffix] 
                                    for f in files 
                                    if f.endswith(".mp3") 
                                    or f.endswith(".wav")])
            
            if music_files.shape[0]>0:            #check if there are files
                doc = pd.concat([doc,
                           pd.DataFrame(
                               dict(folder=[str(Path(root).relative_to(directory))]*len(music_files), 
                                    filename = music_files[:,0],
                                    extension = music_files[:,1]
                                    )
                               )
                           ])
    doc["directory"] = str(directory)
    return doc

#%% Variant 3: List
def read_dir_3 (directory, excluded_folders=["00_Organization"]):
    results = []

    # Use os.walk with early exclusion of unwanted folders
    for root, _, files in os.walk(directory):
        if any(excluded in root for excluded in excluded_folders if excluded!=""):
            continue

        # Filter relevant files and collect their attributes
        for file in files:
            if file.endswith((".mp3", ".wav")):
                relative_folder = str(Path(root).relative_to(directory))
                file_stem = Path(file).stem
                file_ext = Path(file).suffix
                results.append((relative_folder, file_stem, file_ext))

    # Create a DataFrame directly from the results list
    doc = pd.DataFrame(results, columns=["folder", "filename", "extension"])
    doc["directory"] = str(directory)
    return doc


#%% Testing
from time import perf_counter
directory = r"C:\Users\davis\00_data\04_Track_Library"
excluded_folders=[""]

s1a = perf_counter()
df_1a = read_dir_1a (directory,excluded_folders)
e1a=perf_counter()
print(f"Numpy vstack: {e1a-s1a :.5f}")
s1b = perf_counter()
df_1b = read_dir_1b (directory,excluded_folders)
e1b=perf_counter()
print(f"Numpy preallocated: {e1b-s1b :.5f}")

s2 = perf_counter()
df_2 = read_dir_2 (directory,excluded_folders)
e2=perf_counter()
print(f"Pandas: {e2-s2 :.5f}")

s3 = perf_counter()
df_3 = read_dir_3 (directory,excluded_folders)
e3=perf_counter()
print(f"List: {e3-s3 :.5f}")

# Results:
# Variant 3 (list) wins, yet for "small" libraries with less than 2000 files 
# and ~60 subfolders, the effect is negligible. For larger libraries however, 
# the variant 3 is clearly faster, followed by the pandas approach, followed 
# by the numpy approach

