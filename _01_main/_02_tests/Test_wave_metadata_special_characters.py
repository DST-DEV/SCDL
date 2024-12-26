#%% Imports
import numpy as np
import pandas as pd
import soundfile
import wave
from pathlib import Path
import unicodedata
from transliterate import translit

#%% Metadata function

def set_metadata_wave(filepath, **kwargs):
    """Writes the metadata provided via the **kwargs parameter into the 
        file provided by the filename
        Note: Supported file formats: .mp3, .wav, .aiff
    
    Parameters:
        filepath (str or type(Path())): 
            absolute path to the file to be edited
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

    
    #Copy current metadata
    with soundfile.SoundFile(filepath, 'r') as sf:
        meta = sf.copy_metadata()
    
    #Add metadata which isn't updated to the kwargs
    for key in ["genre", "artist", "title"]:
        kwargs.setdefault(key, meta.get(key, ""))
    
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
            if key in valid_keys and value:
                sf.__setattr__(key, value)

#%% Test which characters aren't insertec correctly

# =============================================================================
# folder = r"C:\Users\davis\Downloads\SCDL Test\Test files\Test 1"
# 
# fnames = ["Latex Dreams - Latex Dreams @Syndiakt Sessions Skate Park Outdoor  3.9.22",
#           "ACOUPHÈNES - Alerte Rouge",
#           "æsmå - ode à l'anarchie",
#           "GØWTHER - Tears Of The Crow",
#           "A2XBY - Scorpio (B̶L̸E̶K̸J̵A̶C̸K̴ Remix)",
#           "Karl Schwarz - Spasmodic Craving (Køzløv Remix)",
#           "YÅ - Step Back In Time",
#           "Brutalismus 3000 - Diskotéka",
#           "Melissa D'Lima - Paralysed By My Own Emotion",
#           "Bnzo - Nächte Im Park (Tiktok Hypertechno Remix)",
#           "Impuls - Отменяй (Hardtechno Remix)",
#           "Paulindaclub - Je sais ce que je fais (AD†AM Remix)",
#           "WILLOW - Wait A Minute!",
#           "B.unq! - Got that booty (Original Mix)",
#           "$uicideboy$ - Carrollton (Jawis Fallon Edit)",
#           "Marsi - Нас Не Догонят",
#           "IC3PEAK - Плак Плак (R Dude & TwoTypeZ Hard Remix)",
#           "Toxic Machinery x ÆRES x MOROS - Funeral",
#           "Brutalismus3000 - Atmosféra",
#           "Je$$e - Barbie (Hardtechno Edit)",
#           "molchat doma  - cудно (pete posteuropa edit)",
#           "Глеб Крижановский - Гуляю, Рассветы Встречаю",
#           "Wilderích X Idcs - Sloppy G-Day",
#           "Elley Duhé - Money",
#           "Céleste - The Shot",
#           "brvder jakob & YËDM - Girl Boss [FREE DL]",
#           "Bla - Special characters: § - % - & - / - ? - ß - € - : - ;"
#           ]
# test_df_1 = pd.DataFrame({"fnames":fnames})
# test_df_1["artist"] = test_df_1.fnames.map(lambda txt: txt.split(" - ",1)[0])
# test_df_1["title"] = test_df_1.fnames.map(lambda txt: txt.split(" - ",1)[1])
# 
# for index, row in test_df_1.iterrows():
#     set_metadata_wave(Path(folder, f"{int(index)}.wav"), 
#                       artist=row.artist,
#                       title=row.title)
# 
# # Results
# fnames_errors = [
#     "ACOUPHÈNES - Alerte Rouge",
#     "æsmå - ode à l'anarchie",
#     "GØWTHER - Tears Of The Crow",
#     "A2XBY - Scorpio (B̶L̸E̶K̸J̵A̶C̸K̴ Remix)",
#     "Karl Schwarz - Spasmodic Craving (Køzløv Remix)",
#     "YÅ - Step Back In Time",
#     "Brutalismus 3000 - Diskotéka",
#     "Bnzo - Nächte Im Park (Tiktok Hypertechno Remix)",
#     "Impuls - Отменяй (Hardtechno Remix)",
#     "Paulindaclub - Je sais ce que je fais (AD†AM Remix)",
#     "B.unq! - Got that booty (Original Mix)",
#     "Marsi - Нас Не Догонят",
#     "IC3PEAK - Плак Плак (R Dude & TwoTypeZ Hard Remix)",
#     "Toxic Machinery x ÆRES x MOROS - Funeral",
#     "Brutalismus3000 - Atmosféra",
#     "molchat doma  - cудно (pete posteuropa edit)",
#     "Глеб Крижановский - Гуляю, Рассветы Встречаю",
#     "Wilderích X Idcs - Sloppy G-Day",
#     "Elley Duhé - Money",
#     "Céleste - The Shot",
#     "brvder jakob & YËDM - Girl Boss [FREE DL]",
#     "Bla - Special characters: § - ß - €"
#           ]
# =============================================================================

#%% Test to convert to alphanumeric

folder = r"C:\Users\davis\Downloads\SCDL Test\Test files\Test 2"
strings_test = ["Accents: á - é - í - ó - ú",
                "German Umlauts: ä - ö - ü",
                "Special characters: § - % - & - / - ? - ß - €",
                "cyrillic upper A-E: А - Б - В - Г - Д - Е - Ё",
                "cyrillic upper Z-N: Ж - З - И - Й - К - Л - М - Н",
                "cyrillic upper O-C: О - П - Р - С - Т - У - Ф - Х - Ц - Ч",
                "cyrillic upper S-JA: Ш - Щ - Ъ - Ы - Ь - Э - Ю - Я",
                "cyrillic lower a-e: а - б - в - г - д - е - ё",
                "cyrillic lower z-n: ж - з - и - й - к - л - м - н",
                "cyrillic lower o-c: о - п - р - с - т - у - ф - х - ц - ч",
                "cyrillic lower s-ja: ш - щ - ъ - ы - ь - э - ю - я",
                ]
test_df_2 = pd.DataFrame({"input_str":strings_test})

def convert_to_alphanumeric(input_string):
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
    alphanumeric_string = translit(input_string, "ru", reversed=True)
    #Normalize the string to ensure compatibility with ASCII characters
    normalized_string = unicodedata.normalize(
        'NFKD', alphanumeric_string).encode('ascii', 'ignore').decode('ascii')
    
    #Remove non-alphanumeric characters
    alphanumeric_string = ''.join(char for char in normalized_string 
                                  if char.isalnum() or char.isspace() 
                                  or char in ['-','.','%','&','/','?',])
    
    # repl_dict = {"§": " _ ", " :": " :", ": ": "_ ", ":": "_", 
    #              "/":"", "*":" ", 
    #              " | ":" ", "|":""}                                    #Reserved characters in windows and their respective replacement
    # title = reduce(lambda x, y: x.replace(y, repl_dict[y]), 
    #                repl_dict, 
    #                title).strip()      #Title of the track (= filename)
    return alphanumeric_string

test_df_2["artist"] = test_df_2.input_str.map(convert_to_alphanumeric)
set_metadata_wave(Path(folder, "0.wav"), title="cyrillic upper S-JA: Ш - Щ - Ъ - Ы - Ь - Э - Ю - Я")