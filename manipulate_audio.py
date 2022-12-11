import operator
import os
import random

import pydub.effects
import youtube_dl
from pydub import AudioSegment
from random_word import RandomWords
from youtube_dl.postprocessor import ffmpeg
from youtubesearchpython import *

import convert_wavs

global counter


def export_audio_to_dir(audio, path, name):
    """
    Save as wav file with Addition ManipulatedConverted to the name
    """
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
    """
    Returns limits of given third of audio file - in milliseconds
    """
    bottom = int(((third - 1) * length) / 3)
    top = int((third * length) / 3)
    return bottom, top


def change_vol_help(audio, name, third):
    """
    Changes volume of given third according to name parameter given - high/low/normal
    """
    limits = get_third_audio_limits(len(audio), third)
    if name == "normal":
        return audio[limits[0]:limits[1]]
    elif name == "high":
        return audio[limits[0]:limits[1]] + 10
    else:  # low
        return audio[limits[0]:limits[1]] - 10


def change_vol(audio):
    """
    Changes volume of audio file - divides the audio into 3 parts and randomly selects:
    1 third - increase volume
    1 third - decrease volume
    1 third - keep volume
    """
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
    """
    Speed up audio by 1.5
    """
    return pydub.effects.speedup(audio, playback_speed=1.5)


def decide_manipulate():
    """
    AKA flip a coin
    """
    return random.randint(0, 1)


global changed_counter
changed_counter = 0
global noise_list
noise_list = []
for file in os.scandir('./background_noises'):
    noise_list.append(file.name)


def add_background_noise(audio):
    """
    Add random background noise to given audio
    """
    global noise_list
    decide_noise = random.randint(0, len(noise_list) - 1)
    noise_file = "./background_noises/" + noise_list[decide_noise]
    noise = AudioSegment.from_wav(noise_file)
    noise = noise[:len(audio)] - 18
    return audio.overlay(noise)


def manipulate_audio_file(path, name):
    """
    This function takes .wav files and does the following:
    1. Changes the volume of each 1/3 length of the audio file
    (Randomly chooses 1/3 increased volume, 1/3 normal volume, 1/3 decreased volume)
    2. Add background noise
    3. Change speed of audio (slow down/speed up)

    AKA the G.O.A.T
    """
    audio = AudioSegment.from_wav(path)
    decide_vol = False
    decide_speed = False
    decide_background = True

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
    """
    Helper function to save from original dataset, to a dataset with 3 emotions - happy,sad,neutral
    """
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
    """
    Helper function to change from original dataset, to a dataset with 3 emotions - happy,sad,neutral
    """
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


def youtube2wav(link, word, counter):
    """
    Receive youtube link and download wav file
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'output.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
    out = AudioSegment.from_wav('.\output.wav')
    mid = int(len(out) / 2)
    out = out[mid:mid + 1000]
    out.export(f".\\background_noises\\output.wav")

    if os.path.exists(".\\output.wav"):
        os.remove(".\\output.wav")
    else:
        print("The file does not exist")

    convert_wavs.convert_audio(f".\\background_noises\\output.wav", f".\\background_noises\\{word}{counter}.wav", True)


def Auto_background_noises_generator():
    """
    Generates 1000 background noises:
    1. Generates random word:
    2. For each random word, search youtube and return 20 video links
    3. For each link, send to youtube2wav function to try to download a wav file from the video
    """
    NEED_TO_DOWNLOAD = 1000
    RW = RandomWords()
    error_counter = 0
    total_downloaded = 0
    word_counter = 0
    while total_downloaded <= NEED_TO_DOWNLOAD:
        word = RW.get_random_word()
        word_counter = word_counter + 1
        video_search = VideosSearch(query=word, limit=20)
        vidNum = 1
        for video in video_search.result()["result"]:
            print(f"Word: {word} || wordNum: {word_counter} || vidNum: {vidNum}")
            print(video["title"])
            print(video["link"])
            try:
                youtube2wav(video["link"], word, vidNum)
                total_downloaded = total_downloaded + 1
                print(
                    f"Downloaded successfully - DownloadNum: {total_downloaded} || ErrorNum: {error_counter} || Word: {word} || wordNum: {word_counter} || vidNum: {vidNum}")
            except:
                error_counter = error_counter + 1
                print(
                    f"Error - DownloadNum: {total_downloaded} || ErrorNum: {error_counter} || Word: {word} || wordNum: {word_counter} || vidNum: {vidNum}")

            vidNum = vidNum + 1
            print("*******************************************************************")
    print(f"Downloaded: {total_downloaded} || Error count: {error_counter}")


# Auto_background_noises_generator()
search_in_folder('./data')

print(f"Manipulated: {changed_counter} files")
