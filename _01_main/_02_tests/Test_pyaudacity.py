import os
import time
import pyaudacity as audacity

def main():
    # File paths
    input_file = r"C:\Users\davis\Downloads\SCDL Test\Test data\Garcia Sauvage - Pool Party.wav"  # Replace with the path to your input file
    
    audacity.do(f'Import2: Filename="{input_file}"')
    audacity.do(f'Export2: Filename="{input_file}" NumChannels=2')
    audacity.do('TrackClose')
    # audacity.track_close()

    print("File edited and exported successfully.")

if __name__ == "__main__":
    main()
