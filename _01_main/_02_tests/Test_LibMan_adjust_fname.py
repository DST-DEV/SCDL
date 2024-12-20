import os
import re
import pandas as pd



class LibManager:
    ob_strs = ["premiere", "P R E M I E R E", "𝐏𝐑𝐄𝐌𝐈𝐄𝐑𝐄", "free download",
               "Free DL", "FreeDL", "exclusive", r"\|", "preview", "sindex", 
               "motz", "outnow"]        #common obsolete strings

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

# =============================================================================
#         #Step 9: rename the file
#         #Note: os.replace is used instead of os.rename since os.replace 
#         #automatically overwrites if a file with the new filename already exists
#         os.replace(os.path.join(folder_path, filename), 
#                   os.path.join(folder_path, new_filename + extension))
# =============================================================================
        
        return new_filename, extension

if __name__ == "__main__":
    LibMan = LibManager()
    names = pd.read_excel("LibMan_renaming_test_names.xlsx")
    names["new_filename"]=""
    
    for i, name in names.iterrows():
        names.loc[i,"new_filename"], ext = LibMan.adjust_fname(name.filename + ".mp3", "")
