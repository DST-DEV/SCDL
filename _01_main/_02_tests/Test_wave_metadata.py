#%% wavfile package approach (takes forever to do something)

# =============================================================================
# import wavfile
# from pathlib import Path
# filepath = Path(r"C:\Users\davis\Downloads\test\Akon - Bananza (Atzenernst Edit).wav")
# 
# with wavfile.open(filepath, 'r') as f:
#     # f.add_metadata(track="Test_title", artist="Test_artist")
#     audio = f.read()
#     sr = f.sample_rate
#     bits_per_sample  = f.bits_per_sample
#     
# with wavfile.open(filepath, 'w') as f:
#     f.write(filepath,
#               audio,
#               sample_rate=44100,
#               bits_per_sample=16,
#               fmt=wavfile.chunk.WavFormat.PCM,
#               metadata=dict(track="Test_title", artist="Test_artist"))
# =============================================================================

#%% ChatGPT
# =============================================================================
# import wave
# 
# def add_metadata_to_wav(file_path, output_path, artist, title):
#     """
#     Adds metadata to a WAV file's INFO chunk and writes to a new file.
#     """
#     with wave.open(file_path, 'rb') as original:
#         # Read the original audio data
#         params = original.getparams()
#         audio_frames = original.readframes(params.nframes)
# 
#     # Create a new WAV file with metadata
#     with wave.open(output_path, 'wb') as modified:
#         modified.setparams(params)  # Copy original audio parameters
#         modified.writeframes(audio_frames)
# 
#         # # Construct the INFO chunk for metadata
#         # info_chunk = (
#         #     b'LIST' +                  # RIFF chunk type
#         #     (4 + len(artist) + 1 + len(title) + 1 + 8).to_bytes(4, 'little') +
#         #     b'INFO' +                  # INFO chunk identifier
#         #     b'IART' +                  # Artist metadata field
#         #     len(artist).to_bytes(4, 'little') +
#         #     artist.encode('utf-8') +
#         #     b'\x00' +
#         #     b'INAM' +                  # Title metadata field
#         #     len(title).to_bytes(4, 'little') +
#         #     title.encode('utf-8') +
#         #     b'\x00'
#         # )
#         # # Append the INFO chunk to the file
#         # modified.writeframes(info_chunk)
# 
# 
# # Example usage:
# file_path = r"C:\Users\davis\Downloads\test\Wilderch - Sloppy G-Day.wav"
# output_path = r"C:\Users\davis\Downloads\test\Wilderch - Sloppy G-Day_modified.wav"
# add_metadata_to_wav(file_path, output_path, artist="Chris", title="Rave Nappo2")
# 
# =============================================================================
#%% My approach
# =============================================================================
# import soundfile
# from pathlib import Path
# 
# from time import perf_counter
# start = perf_counter()
# 
# # filepath = Path(r"C:\Users\davis\Downloads\test\Wilderch - Sloppy G-Day_modified.wav")
# filepath = Path(r"C:\Users\davis\Downloads\test\Akon - Bananza (Atzenernst Edit).wav")
# 
# # #Read file
# # with soundfile.SoundFile(filepath, 'r') as f:
# #     artist = f.__getattr__("artist")
# #     title = f.__getattr__("title")
# 
# #     sr = f.samplerate
# #     st = f.subtype
# #     data = f.read() 
# 
# #Rewrite Metadata
# sf = soundfile.SoundFile(filepath, 'r+')
# artist = sf.__getattr__("artist")
# title = sf.__getattr__("title")
# data = sf.read()
# sf.__setattr__("artist", "Akon")
# sf.__setattr__("title", "Bananza (Atzenernst Edit")
# sf.write(data)
# sf.close()
# 
# #Check metadata
# with soundfile.SoundFile(filepath, 'r') as f_new:
#     artist_new = f_new.__getattr__("artist")
#     title_new = f_new.__getattr__("title")
# 
# end = perf_counter()
# print(f"Script took {end-start :.6}s")
# 
# 
# =============================================================================
#%% My approach revised
#Note: this apparently only works if the info chunk of the .wav file has a 
# certain format. However, if running the ChatGPT approach first (which does 
# not insert the metadata correctly) and afterwards running my code, then it 
# works => check how to adjust the info chunk before adjusting the metadata 
# with soundfile

# =============================================================================
# import numpy as np
# import soundfile
# import wave
# from pathlib import Path
# 
# # filepath = Path(r"C:\Users\davis\Downloads\test\Wilderch - Sloppy G-Day_modified.wav")
# filepath = str(Path(r"C:\Users\davis\Downloads\test\Sample - File.aiff"))
# 
# #Open file with wave package and rewrite contents (gets rid of any problematic 
# # header data)
# with wave.open(filepath, 'rb') as f_original:
#     # Read the original audio data
#     params = f_original.getparams()
#     audio_frames = f_original.readframes(params.nframes)
# 
# with wave.open(filepath, 'wb') as f_adjusted:
#     f_adjusted.setparams(params)
#     f_adjusted.writeframes(audio_frames)
# 
# #Insert metadata with soundfile package
# with soundfile.SoundFile(filepath, 'r+') as sf:
#     # sr = sf.samplerate
#     # st = sf.subtype
#     # data = sf.read() 
#     sf.__setattr__("artist", "Akon")
#     sf.__setattr__("title", "Bananza (Atzenernst Edit")
# =============================================================================

#%% Load metadata from file

# import soundfile
# from pathlib import Path
# filepath = r"C:\Users\davis\Downloads\SCDL Test\Test new files\Trance - Bounce - Low Energy - Vocal\5eurogoldi - Mehr von dem was du liebe nennst.wav"

# with soundfile.SoundFile(filepath, 'r') as sf:
#     meta = sf.copy_metadata()

import music_tag
filepath = r"C:\Users\davis\Downloads\SCDL Test\Test new files\Trance - Bounce - Low Energy - Vocal\100 Gecs - Doritos & fritos.mp3"

file = music_tag.load_file(filepath)
genre = str(file["genre"])

