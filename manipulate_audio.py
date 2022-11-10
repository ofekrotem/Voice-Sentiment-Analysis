import operator
import random
import convert_wavs
from pydub import AudioSegment
import os

from pydub.generators import WhiteNoise

global counter


def export_audio_to_dir(audio, path, name):
    if '_' in name:
        index = name.rfind('_')
        index = len(path) - len(name) + index
    else:
        index = path.rfind('.')

    path = path[:index] + 'Manipulated' + path[index:]
    audio.export(os.path.join(f"{path}"), format="wav")
    if '_' in name:
        index = name.rfind('_')
        index = len(path) - len(name) + index
    else:
        index = path.rfind('.')
    new_path = path[:index] + 'Converted' + path[index:]
    convert_wavs.convert_audio(path, new_path, True)
    print(f"Saved + converted {new_path}")


def get_third_audio_limits(length, third) -> (int, int):
    bottom = int(((third - 1) * length) / 3)
    top = int((third * length) / 3)
    return bottom, top


def change_vol_help(audio, name, third):
    limits = get_third_audio_limits(len(audio), third)
    if name == "normal":
        return audio[limits[0]:limits[1]]
    elif name == "high":
        return audio[limits[0]:limits[1]] + 10
    else:  # low
        return audio[limits[0]:limits[1]] - 10


def change_vol(audio):
    increased_third = random.randint(1, 3)
    decrease_third = increased_third
    while decrease_third == increased_third:
        decrease_third = random.randint(1, 3)
    normal_third = 0
    for i in range(1, 3):
        if i != decrease_third and i != increased_third:
            normal_third = i
            break
    sorted_thirds = {"normal": normal_third, "high": increased_third, "low": decrease_third}
    sorted_thirds = sorted(sorted_thirds.items(), key=operator.itemgetter(1))
    new_audio = AudioSegment.empty()
    for name, third in sorted_thirds:
        new_audio = new_audio + change_vol_help(audio, name, third)
    return new_audio


def add_white_noise(audio):
    noise = WhiteNoise().to_audio_segment(duration=len(audio), volume=-35)
    return audio.overlay(noise)


def decide_manipulate():
    return random.randint(0, 1)


global vol_counter
global white_counter
global both_counter
vol_counter = 0
white_counter = 0
both_counter = 0


def manipulate_audio_file(path, name):
    """
    This function takes .wav files and does the following:
    1. Changes the volume of each 1/3 length of the audio file
    (Randomly chooses 1/3 increased volume, 1/3 normal volume, 1/3 decreased volume)
    2. Add white noise in the background
    """
    global vol_counter, white_counter, both_counter
    audio = AudioSegment.from_wav(path)
    decide_vol = decide_manipulate()
    decide_white = decide_manipulate()
    if decide_vol and decide_white:
        audio = change_vol(audio)
        audio = add_white_noise(audio)
        both_counter = both_counter + 1
        print(f"Changed both for {path}")
    elif decide_vol:
        audio = change_vol(audio)
        vol_counter = vol_counter + 1
        print(f"Changed vol for {path}")
    elif decide_white:
        audio = add_white_noise(audio)
        white_counter = white_counter + 1
        print(f"Added white to {path}")
    if decide_vol or decide_white:
        export_audio_to_dir(audio, path, name)


def search_in_folder(path):
    """
    Search in path folder for all files (not folders)
    """
    for file in os.scandir(path):
        if not file.is_file():
            search_in_folder(file)
        else:
            if decide_manipulate():
                print(file.name)
                manipulate_audio_file(file.path, file.name)


search_in_folder('.\data')
print(f"Manipulated vol: {vol_counter} files")
print(f"Manipulated white: {white_counter} files")
print(f"Manipulated both: {both_counter} files")
