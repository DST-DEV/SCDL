import soundfile
from pathlib import Path

from time import perf_counter
start = perf_counter()

filepath = Path(r"C:\Users\davis\Downloads\Souncloud Download\test_files\A-05 - Walking On A Dream.wav")

# #Read file
# with soundfile.SoundFile(filepath, 'r') as f:
#     artist = f.__getattr__("artist")
#     title = f.__getattr__("title")

#     sr = f.samplerate
#     st = f.subtype
#     data = f.read() 

#Rewrite Metadata
sf = soundfile.SoundFile(filepath, 'r+')
artist = sf.__getattr__("artist")
title = sf.__getattr__("title")
data = sf.read()
sf.__setattr__("artist", "Chris")
sf.__setattr__("title", "Rave Nappo2")
sf.write(data)
sf.close()

#Check metadata
with soundfile.SoundFile(filepath, 'r') as f_new:
    artist_new = f_new.__getattr__("artist")
    title_new = f_new.__getattr__("title")

end = perf_counter()
print(f"Script took {end-start :.6}s")
