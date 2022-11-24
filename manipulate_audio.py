import operator
import os
import random

import pydub.effects
from pydub import AudioSegment
from random_word import RandomWords
from youtubesearchpython import *

import convert_wavs

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


def change_speed(audio):
    return pydub.effects.speedup(audio, playback_speed=1.5)


def decide_manipulate():
    return random.randint(0, 1)


global changed_counter
changed_counter = 0


def add_background_noise(audio):
    noise_list = ["birds.wav", "farm.wav", "people.wav", "rain.wav", "sea.wav", "white_noise.wav", "wind.wav"]
    decide_noise = random.randint(0, 6)
    noise_file = "./background_noises/" + noise_list[decide_noise]
    noise = AudioSegment.from_wav(noise_file)
    noise = noise[:len(audio)] - 18
    return audio.overlay(noise)


def manipulate_audio_file(path, name):
    """
    This function takes .wav files and does the following:
    1. Changes the volume of each 1/3 length of the audio file
    (Randomly chooses 1/3 increased volume, 1/3 normal volume, 1/3 decreased volume)
    2. Add white noise in the background
    3. Change speed of audio (slow down/speed up)
    """
    audio = AudioSegment.from_wav(path)
    decide_vol = True
    decide_speed = True
    decide_background = False

    if decide_background:
        audio = add_background_noise(audio)
        print(f"Added background to {path}")
    if decide_vol:
        audio = change_vol(audio)
        print(f"Changed vol for {path}")
    if decide_speed:
        audio = change_speed(audio)
        print(f"Changed speed for {path}")
    if decide_vol or decide_speed or decide_background:
        global changed_counter
        changed_counter = changed_counter + 1
        export_audio_to_dir(audio, path, name)


global unique
unique = 0


def save_with_new_emotion(audio, path, is_dot, emotion):
    global unique
    if is_dot:
        index = path.rfind('.') - 2
        new_path = f"{path[:index]}{unique}{emotion}{path[index + 1:]}"
        unique = unique + 1
    else:
        index = path.rfind('_')
        new_path = f"{path[:index]}{unique}_{emotion}.wav"
        unique = unique + 1

    convert_wavs.convert_audio(path, new_path, True)
    print(f"saved {path} as {new_path}")


def unite_data_to_three_emotions(path, name):
    categories = {
        "W": "angry",
        "L": "boredom",
        "E": "disgust",
        "A": "fear",
        "F": "happy",
        "T": "sad",
        "N": "neutral"
    }
    audio = AudioSegment.from_wav(path)
    positive_emotions = ["ps"]
    negative_emotions = ["angry", "disgust", "fear", "W", "E", "A"]
    neutral_emotions = ["boredom", "calm", "L"]
    is_dot = False
    if '_' in name:
        start_index = name.rfind('_') + 1
        end_index = name.rfind('.')
        emotion = name[start_index:end_index]
    else:
        index = path.rfind('.')
        emotion = path[index - 2:index - 1]
        is_dot = True
    if emotion in positive_emotions:
        if is_dot:
            emotion = "F"
        else:
            emotion = "happy"
        save_with_new_emotion(audio, path, is_dot, emotion)
    elif emotion in negative_emotions:
        if is_dot:
            emotion = "T"
        else:
            emotion = "sad"
        save_with_new_emotion(audio, path, is_dot, emotion)
    elif emotion in neutral_emotions:
        if is_dot:
            emotion = "N"
        else:
            emotion = "neutral"
        save_with_new_emotion(audio, path, is_dot, emotion)
    else:
        pass


def search_in_folder(path):
    """
    Search in path folder for all files (not folders)
    """
    global changed_counter
    for file in os.scandir(path):
        if "train" in file.path:

            if not file.is_file():
                search_in_folder(file)
            else:
                if decide_manipulate():
                    manipulate_audio_file(file.path, file.name)


def Auto_background_noises_manipulator():
    RW = RandomWords()
    for i in range(0, 1):
        word = RW.get_random_word()
        print(f"The selected word is: {word}")
        video_search = VideosSearch(word, 3, 'en')
        for video in video_search.result()["result"]:
            print(video["title"])
            print(video["link"])
            print("*******************************************************************")


Auto_background_noises_manipulator()
# search_in_folder('./data')

print(f"Manipulated: {changed_counter} files")
