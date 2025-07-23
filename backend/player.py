import base64
import os

import pygame
import threading
import keyboard
import time

from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import EasyMP3
from mutagen import File
import random

from pathlib import Path


def find_mp3_files(root_folder):
    return list(Path(root_folder).rglob('*.mp3'))


class MP3Player:
    def __init__(self):
        self.file_length = None
        self.song_metadata = None
        self.replay = "queue" # [queue, single, none]
        self.volume = 50
        self.seconds = 0
        self.is_playing = False
        self.ctrl_pressed = False
        self.folder_path = r"C:\Music\JUICE WRLD UNRELEASED\Unreleased"
        self.mp3file = None


        self.seconds_skip = 160
        self.shuffle_enabled = True
        self.refresh_rate = 20 # [from 1 to 1000] -- per second
        self.trim_start_silence = 0.15 # [from 0 to 0.5 recommended]
        self.trim_end = 0.07 # [from 0 to 0.2 recommended]

        self.song_queue = find_mp3_files(self.folder_path)
        self.started = False

        self.artist_name = "untitled"
        self.song_name = "???"
        self.song_album = "none"


        if self.shuffle_enabled:
            random.shuffle(self.song_queue)
        self.queue_position = 0
        self.ms = 0

    def get_cover_art_base64(self):
        try:
            file = File(self.mp3file)
            try:
                artwork = file.tags['APIC:'].data
                if artwork:  # Check if artwork exists
                    return base64.b64encode(artwork).decode('utf-8')
            except (KeyError, AttributeError):
                pass  # Fall through to default image

            # Load default image properly
            default_image_path = os.path.join(os.path.dirname(__file__), "../src/ui/icons/img.png")
            with open(default_image_path, 'rb') as f:
                default_artwork = f.read()
            return base64.b64encode(default_artwork).decode('utf-8')

        except Exception as e:
            print(f"Error getting cover art: {e}")
            # Return a minimal transparent pixel as fallback
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    def play_music(self,mp3file):
        self.mp3file = mp3file
        self.song_metadata = EasyMP3(mp3file)
        self.file_length = self.song_metadata.info.length
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.load(mp3file)

        self.seconds = 0
        self.ms = 0
        pygame.mixer.music.play()

        if not self.is_playing:
            pygame.mixer.music.pause()
        pygame.mixer.music.set_pos(self.trim_start_silence)
        self.is_playing = True

        try:
            self.artist_name = str(self.song_metadata['artist'])[2:-2]
            self.song_name = str(self.song_metadata['title'])[2:-2]
        except (ID3NoHeaderError, Exception) as e:
            self.song_name= str(self.song_queue[self.queue_position]).split('\\')[-1].split('.mp3')[0]
            if " - " in self.song_name or " -- " in self.song_name:
                self.artist_name = self.song_name.split(' - ')[0]
                self.song_name = self.song_name.split(' - ')[1].split('.mp3')[0]
            else:
                self.artist_name = "untitled"
                self.song_name = str(self.song_queue[self.queue_position]).split('\\')[-1].split('.mp3')[0]




    def next_song(self):
        self.seconds = 0
        self.ms = 0
        self.queue_position += 1
        if self.queue_position == len(self.song_queue):
            self.queue_position = 0
        self.play_music(fr"{self.song_queue[self.queue_position]}")
        pygame.mixer.music.set_pos(self.trim_start_silence)
        self.set_volume(self.volume)


    def prev_song(self):
        if self.queue_position > 0:
            self.queue_position -= 1
            self.play_music(fr"{self.song_queue[self.queue_position]}")
            self.set_volume(self.volume)
            self.seconds = 0
            self.ms = 0
            pygame.mixer.music.set_pos(self.trim_start_silence)
        else:
            self.play_music(fr"{self.song_queue[self.queue_position]}")
            self.set_volume(self.volume)
            self.seconds = 0
            self.ms = 0
            pygame.mixer.music.set_pos(self.trim_start_silence)

    def seconds_handler(self):
        time.sleep(1)
        self.seconds += 1
        self.ms = 0
        while not pygame.mixer.music.get_busy():
            time.sleep(1/self.refresh_rate)
        while True:
            time.sleep(1/self.refresh_rate)


            # print(seconds + ms/refresh_rate)
            # print(f"file_length - {file_length}")
            if pygame.mixer.music.get_busy():
                self.ms += 1
                if self.ms == self.refresh_rate or not pygame.mixer.music.get_busy():
                    self.seconds += 1
                    self.ms = 0
                    # self.print_current_song()
            # print(pygame.mixer.music.get_busy())
            # print(not pygame.mixer.music.get_busy() and is_playing)
            # print("\n\n")
            if (not pygame.mixer.music.get_busy() and self.is_playing) or (self.seconds + self.ms/self.refresh_rate >= self.file_length-(self.trim_start_silence + self.trim_end)):
                if self.replay == "single":
                    self.seconds = 0
                    self.ms = 0
                    pygame.mixer.music.set_pos(self.seconds)

                elif self.replay == "queue":
                    self.next_song()
                    self.is_playing = True


                elif self.replay == "none":
                    pygame.mixer.music.pause()
                    self.is_playing = False
                    self.seconds = 0
                    self.ms = 0
                    pygame.mixer.music.set_pos(self.seconds)



    def print_current_song(self):
        # percent = 100.0 * self.seconds / self.file_length
        # print("\n")
        # print(
        #     f"{self.artist_name} -- '{self.song_name}'\t\t\t\t\tVolume: {str(int(self.volume * 10))}")
        #
        # print("{:02d}:{:02d} |{:{}}| {:02d}:{:02d}"
        # .format(
        #     int(self.seconds) // 60, int(self.seconds) % 60,  # Левый таймер (MM:SS)
        #     '█' * int(percent / (100.0 / 100)), 100,  # Прогресс-бар
        #     int(self.file_length) // 60, int(self.file_length) % 60  # Правый таймер (MM:SS)
        # ))
        pass


    def toggle_pause_music(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_playing = False
            print("Paused")
        else:
            pygame.mixer.music.unpause()
            self.is_playing = True
            print("Playing")

    def wait_for_input(self):
        pass
        while True:
            event = keyboard.read_event()

            if event.event_type == keyboard.KEY_DOWN and event.name == 'space':
                self.toggle_pause_music()

            if event.event_type == keyboard.KEY_DOWN and event.name == 'up':
                self.volume_up()

            if event.event_type == keyboard.KEY_DOWN and event.name == 'down':
                self.volume_down()

            if event.event_type == keyboard.KEY_DOWN and event.name == 'left':
                if self.ctrl_pressed:
                    self.prev_song()
                else:
                    self.skip_forward()
                self.print_current_song()

            if event.event_type == keyboard.KEY_DOWN and event.name == 'ctrl':
                self.ctrl_pressed = True
            if event.event_type == keyboard.KEY_UP and event.name == 'ctrl':
                self.ctrl_pressed = False


            if event.event_type == keyboard.KEY_DOWN and event.name == 'right':
                if self.ctrl_pressed:
                    self.next_song()
                else:
                    self.skip_backward()
                self.print_current_song()

    def skip_backward(self):
        self.seconds = min(self.file_length, self.seconds)
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_pos(self.seconds)

    def skip_forward(self):
        self.seconds = max(0, self.seconds - self.seconds_skip)
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_pos(self.seconds)

    def set_song_position(self, position):
        self.seconds = max(0, min(self.file_length, position))
        self.ms = 0
        pygame.mixer.music.set_pos(self.seconds)

    def set_volume(self, volume):
        self.volume = volume
        pygame.mixer.music.set_volume(self.volume/100)
        self.print_current_song()

    def volume_down(self):
        self.volume = round(max(0, self.volume - 0.1), 1)
        pygame.mixer.music.set_volume(self.volume)
        self.print_current_song()

    def volume_up(self):
        self.volume = round(min(1, self.volume + 0.1), 1)
        pygame.mixer.music.set_volume(self.volume)
        self.print_current_song()


    def start(self):
        if not self.started:
            print("Application Started")
            music_thread = threading.Thread(target=self.play_music, args=(f"{self.song_queue[0]}",))
            music_thread.start()

            second_counter_thread = threading.Thread(target=self.seconds_handler)
            second_counter_thread.start()
            # input_thread = threading.Thread(target=self.wait_for_input)
            # input_thread.start()
            # input_thread.join()
            self.started = True

if __name__ == "__main__":
    player = MP3Player()
    player.start()