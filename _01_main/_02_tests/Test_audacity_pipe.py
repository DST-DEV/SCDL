# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 09:42:05 2024

@author: davis
"""

"""Tests the audacity pipe.

Keep pipe_test.py short!!
You can make more complicated longer tests to test other functionality
or to generate screenshots etc in other scripts.

Make sure Audacity is running first and that mod-script-pipe is enabled
before running this script.

Requires Python 2.7 or later. Python 3 is strongly recommended.

"""

import os
import sys
import music_tag
import time

# PyAudacity has functions called open() and print(), so save the originals:
_open = open
_type = type
_format = format


if sys.platform == 'win32':
    print("pipe-test.py, running on windows")
    TONAME = '\\\\.\\pipe\\ToSrvPipe'
    FROMNAME = '\\\\.\\pipe\\FromSrvPipe'
    EOL = '\r\n\0'
else:
    print("pipe-test.py, running on linux or mac")
    TONAME = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
    FROMNAME = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
    EOL = '\n'

print("Write to  \"" + TONAME +"\"")
if not os.path.exists(TONAME):
    print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
    sys.exit()

print("Read from \"" + FROMNAME +"\"")
if not os.path.exists(FROMNAME):
    print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
    sys.exit()

print("-- Both pipes exist.  Good.")

# For reasons unknown, we need a slight pause after checking for the existence of the read file on Windows:
time.sleep(0.0001)
TOFILE = _open(TONAME, 'w')
print("-- File to write to has been opened")
FROMFILE = _open(FROMNAME, 'rt')
print("-- File to read from has now been opened too\r\n")



def send_command(command):
    """Send a single command."""
    print("Send: >>> \n"+command)
    TOFILE.write(command + EOL)
    TOFILE.flush()

def get_response():
    """Return the command response."""
    result = ''
    line = ''
    while True:
        result += line
        line = FROMFILE.readline()
        if line == '\n' and len(result) > 0:
            break
    return result

def do_command(command):
    """Send one command, and return the response."""
    send_command(command)
    response = get_response()
    print("Rcvd: <<< \n" + response)
    return response

def import_export(input_file):
    """Example list of commands."""
    # do_command('Help: Command=Help')
    # Metadata
    # title = "Pool Party"
    # artist = "Garcia Sauvage"
    # file = music_tag.load_file(input_file)
    # file["title"] = title
    # file["artist"] = artist
    # file.save()
    
    out_file = input_file.replace(".wav","_exp.wav")
    
    do_command(f'Import2: Filename="{input_file}"')
    do_command(f'Export2: Filename="{out_file}" NumChannels=2')
    do_command('TrackClose')

in1 = r"C:\Users\davis\Downloads\SCDL Test\Test data\Garcia Sauvage - Pool Party.wav"  # Replace with the path to your input file
in2 = r"C:\Users\davis\Downloads\SCDL Test\Test data\A2XBY - Scorpio (B̶L̸E̶K̸J̵A̶C̸K̴ Remix).wav"












