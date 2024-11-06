import time
file= "C:/Users/davis/Downloads/Paul Seul - Open Up.wav"
folder = "C:/Users/davis/Downloads/"

#%% Change tags
# import music_tag

# start = time.time()
# f = music_tag.load_file(file)
# f['genre'] = 'tech'
# f['artist']='franz'
# f['title']='ladt'
# f.save()



# #%% change sampling rate
# from tinytag import TinyTag

# start = time.time()
# tag = TinyTag.get(file)
# print(f"genre: {tag.artist}")
# end = time.time()
# print(end-start)

#%%
# import librosa
# import soundfile as sf
# import numpy as np

# # Load the audio file
# audio_file = file
# y, sr = librosa.load(audio_file, sr=None)  # sr=None to keep original sample rate

# # Desired sample rate
# new_sr = 48000  # For example, 44.1 kHz

# # Resample the audio
# y_resampled = librosa.resample(y=y, orig_sr=sr, target_sr=new_sr)

# # Save the resampled audio to a new file
# output_file = 'C:/Users/davis/Downloads/output.wav'
# sf.write(output_file, y_resampled, new_sr)


#%% Change Bitrate (works but audio quality is horrible afterwards)

# import wave
# import numpy as np
# from scipy.io import wavfile
# from scipy.signal import resample


# with wave.open(file) as wav_file:
#     metadata = wav_file.getparams()
#     frames = wav_file.readframes(metadata.nframes)
#     or_sr = wav_file.getframerate()
#     or_sw = wav_file.getsampwidth()
#     or_ch = wav_file.getnchannels()
    
    
# # Convert binary data to numpy array
# data_array = np.frombuffer(frames, dtype=np.int16)
# # Define the new sample rate
# new_sample_rate = 48000  # for example

# # Resample the data
# resampled_data = resample(data_array, int(len(data_array) * (new_sample_rate / or_sr)))


# with wave.open(folder+"output.wav", mode="wb") as wav_file:
#     wav_file.setnchannels(or_ch)
#     wav_file.setsampwidth(or_sw)
#     wav_file.setframerate(new_sample_rate)
#     wav_file.writeframes(resampled_data.astype(np.int16))

#%% works, but not sure whether the resolution can be adjusted

import wave
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample


def adjust_wav_1 ():
    with wave.open(file) as wav_file:
        metadata = wav_file.getparams()
        frames = wav_file.readframes(metadata.nframes)
        or_sr = wav_file.getframerate()
        or_sw = wav_file.getsampwidth()
        or_ch = wav_file.getnchannels()
    
    with wave.open(folder+"output.wav", mode="wb") as wav_file:
        wav_file.setnchannels(or_ch)
        wav_file.setsampwidth(or_sw)
        wav_file.setframerate(or_sr)
        wav_file.writeframes(frames)
    
    # Convert data to numpy array
    _, data_array = wavfile.read(folder+"output.wav")
    
    # Define the new sample rate
    new_sample_rate = 48000  # for example
    
    # Resample the data
    resampled_data = resample(data_array, int(len(data_array) * (new_sample_rate / or_sr)))
    
    # Write the resampled data to a new wave file
    with wave.open(folder+'output_2.wav', 'wb') as wav:
        wav.setnchannels(or_ch)
        wav.setsampwidth(or_sw)
        wav.setframerate(new_sample_rate)
        wav.writeframes(resampled_data.astype(np.int16))


#%% works and can adjust resolution
import numpy as np
from scipy.signal import resample
import soundfile


def adjust_wav_2():
    data, samplerate = soundfile.read(file)
    
    # Define the new sample rate
    new_sample_rate = 48000  # for example
    
    # Resample the data
    resampled_data = resample(data, int(len(data) * (new_sample_rate / samplerate)))
    
    soundfile.write(folder + 'new.wav', resampled_data, new_sample_rate, subtype='PCM_16')

wav_1_dur = []
wav_2_dur=[]
for i in range(20):
    start = time.time()
    adjust_wav_1()
    end = time.time()
    wav_1_dur.append(end-start)
    
    start = time.time()
    adjust_wav_2()
    end = time.time()
    wav_2_dur.append(end-start)

print(f"avg time 1: {np.mean(wav_1_dur)}")