import re

sc_name = r"DJ KINNER - Back To The 90's (Original Mix)"
dl_name = r"DJ_KINNER_-_Back_To_The_90s_Original_Mix"

def convert_title (track_title):
    """Converts a track_title string to the naming format that is used by 
    the soundcloudtomp3.biz website
    
    Parameters:
        track_title (string):
            The title of the track as written on Soundcloud
    
    Returns:
        track_title (string):
            The track title in the format from the soundcloudtomp3.biz 
            website
    """
    
    # Define the list of invalid characters (escaped for regex compatibility)
    rem_chars = [",", r"\(", r"\)", r"\[", r"\]", r"\$", "&", 
                 "~", r"\.", r"\?", r"\!", r"\^", r"\+", 
                 r"\*", r"/", r":"]

    # Combine all characters into a single regex pattern
    rem_chars_pattern = "|".join(rem_chars)

    # Remove any rem_char at the start of the string
    track_title = re.sub(f"^({rem_chars_pattern})+", "", track_title)
    # Remove any rem_char at the end of the string
    track_title = re.sub(f"({rem_chars_pattern})+$", "", track_title)
    # Step 1: Replace any invalid character surrounded by whitespace with an underscore
    track_title = re.sub(rf"\s(({rem_chars_pattern})+)\s", "_", track_title)
    # Step 2: Replace invalid characters followed by whitespace with an underscore
    track_title = re.sub(rf"({rem_chars_pattern})\s", "_", track_title)
    # Step 3: Replace invalid characters preceded by whitespace with an underscore
    track_title = re.sub(rf"\s({rem_chars_pattern})+", "_", track_title)
    # Step 4: Replace remaining individual invalid characters with an underscore
    track_title = re.sub(rf"({rem_chars_pattern})", "_", track_title)
    #Step 5: Remove "'" 
    track_title = track_title.replace("'","")
    #Step 6: Remove leading and trailing edges
    track_title = track_title.strip()
    
    #Step 7: Replace white spaces with underscores
    track_title = track_title.replace(" ", "_")
    #Step 8: Replace multiple adjacent underscore
    track_title =  re.sub(r"_+", "_", track_title)
    
    return track_title.strip()

dl_name_artificial = convert_title(sc_name)