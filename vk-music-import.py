"""
Imports music to VK Music from Track list.

AUTH:
https://oauth.vk.com/oauth/authorize?client_id=6121396&scope=8&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991

"""
import csv
import json
import logging
import os
import platform
import re
import sys
import webbrowser
from datetime import datetime
from io import BytesIO
from logging.handlers import RotatingFileHandler
from time import sleep
from types import SimpleNamespace
from urllib.parse import urlparse, parse_qs
import requests
import vk_api
import numpy as np
import onnxruntime as rt
from PySide2.QtGui import QPixmap, QClipboard, QDesktopServices
from dotenv import load_dotenv, set_key
from vk_api import Captcha
from typing import Union, Optional, List
from PIL import Image, ImageTk
import qdarktheme
from PySide2.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QFormLayout, QCheckBox, QLineEdit, \
    QProgressBar, QTextEdit, QPushButton, QDialog, QLabel, QHBoxLayout, QRadioButton, QMessageBox, QInputDialog, \
    QFileDialog
from PySide2.QtCore import Qt, QUrl
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QApplication
from PySide2.QtGui import QPixmap, QImage
from PySide2.QtCore import Qt


# from curl_cffi import requests
# from bs4 import BeautifulSoup
# from fuzzywuzzy import fuzz

def fix_relative_path(relative_path: str) -> str:
    """
    Фикс относительных путей PyInstaller
    """
    application_path = ''
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(os.path.abspath(sys.executable))
    elif __file__:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(application_path, relative_path))


# Class for envs syncing (config.env)
class MainEnv:
    def __init__(self):
        self.env = SimpleNamespace()
        self.load_env_config()

    def load_env_config(self):
        self.env = SimpleNamespace()

        load_dotenv(config_path, override=True)

        self.env.BYPASS_CAPTCHA = os.getenv("BYPASS_CAPTCHA", "0") == "1"
        self.env.VK_TOKEN = os.getenv("VK_TOKEN")
        self.env.SPOTIFY_MODE = os.getenv("SPOTIFY_MODE", "0") == "1"
        self.env.APPLE_MODE = os.getenv("APPLE_MODE", "0") == "1"
        self.env.VK_LINKS_MODE = os.getenv("VK_LINKS_MODE", "0") == "1"
        self.env.REVERSE = os.getenv("REVERSE", "0") == "1"
        self.env.STRICT_SEARCH = os.getenv("STRICT_SEARCH", "0") == "1"
        self.env.ADD_TO_LIBRARY = os.getenv("ADD_TO_LIBRARY", "0") == "1"
        # self.env.UPDATE_PLAYLIST = os.getenv("UPDATE_PLAYLIST", "0") == "1"
        self.env.TIMEOUT_AFTER_ERROR = int(os.getenv("TIMEOUT_AFTER_ERROR", "10"))
        self.env.TIMEOUT_AFTER_CAPTCHA = int(os.getenv("TIMEOUT_AFTER_CAPTCHA", "10"))
        self.env.TIMEOUT_AFTER_SUCCESS = int(os.getenv("TIMEOUT_AFTER_SUCCESS", "10"))


# Creating a class for the main window
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Setting the window title and size
        self.setWindowTitle("VK Music import (beta)")
        self.resize(600, 300)
        # Creating a tab widget
        self.tab_widget = QTabWidget()
        # Creating two tabs
        self.main_tab = MainTab()
        self.settings_tab = SettingsTab()
        # Adding the tabs to the tab widget
        self.tab_widget.addTab(self.main_tab, "Главная")
        self.tab_widget.addTab(self.settings_tab, "Настройки")
        # Creating a layout for the window
        self.layout = QVBoxLayout()
        # Adding the tab widget to the layout
        self.layout.addWidget(self.tab_widget)
        # Setting the layout for the window
        self.setLayout(self.layout)


# Creating a class for the main tab
class MainTab(QWidget, MainEnv):
    def __init__(self):
        # Call both parents constructors
        QWidget.__init__(self)
        MainEnv.__init__(self)
        # Environment variables
        self.env = SimpleNamespace()
        # Creating buttons (start, pause, stop)
        self.start_button = QPushButton("Начать импорт")
        self.start_button.setStyleSheet("QPushButton {font-weight: bold; height: 24px}")
        # Connecting the buttons to their functions
        self.start_button.clicked.connect(self.start)
        # Creating a progress bar
        self.progress_bar = QProgressBar()
        # Setting the initial value and range of the progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        # Creating a text edit
        self.text_edit = QTextEdit()
        # Setting the text edit to read only
        self.text_edit.setReadOnly(True)
        # Creating a layout for the tab
        self.layout = QVBoxLayout()
        # Adding the buttons to the layout
        self.layout.addWidget(self.start_button)
        # Adding the progress bar and the text edit to the layout
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.text_edit)
        # Setting the layout for the tab
        self.setLayout(self.layout)
        # Main
        self.is_running = False
        self.is_under_ban = False
        self.ok_tracks = None
        self.questionable_tracks = None
        self.playlist_response = None

    def update_progress_bar(self, value: int):
        """
        Обновляет прогресс бар
        """
        self.progress_bar.setValue(value)
        QApplication.processEvents()

    def add_log(self, text: str, level: str = 'INFO'):
        """
        Добавляет текст в лог
        """
        self.text_edit.append(text)
        if level == 'INFO':
            logging.info(text)
        else:
            logging.warning(text)
        QApplication.processEvents()

    def show_input_dialog(self, title: str, text: str, default_text: str = "") -> str:
        """
        Показывает диалог ввода текста
        """
        text, ok = QInputDialog.getText(self, title, text, QLineEdit.Normal, default_text)
        if ok:
            return text
        else:
            return None

    # Defining a function that starts the import process
    def start(self):
        self.load_env_config()

        if self.is_running:
            # Ask user is he sure to stop
            reply = QMessageBox.question(self, 'Подтверждение', 'Вы уверены, что хотите остановить импорт?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.stop_import()
                self.add_log("Останавливается пользователем...")

            return

        # Rename the start button to pause
        self.is_running = True
        self.start_button.setText("Стоп")

        # VK Authentication
        self.add_log("Авторизуюсь в ВКонтакте...")
        if self.env.VK_TOKEN is None:
            self.add_log("Не обнаружен токен VK API в config_path файле, запрашиваю авторизацию вручную...")
            self.get_token()
        vk_session = vk_api.VkApi(token=self.env.VK_TOKEN,
                                  captcha_handler=lambda captcha: self.captcha_handler(captcha))
        vk = vk_session.get_api()
        tracklist = []
        try:
            user_info = vk.users.get()[0]
        except vk_api.exceptions.ApiError as e:
            self.add_log(f"Кажется, ваш токен устарел, необходимо заново авторизоваться (ошибка: {e})")
            self.stop_import()

            # Show info dialog with suggestion to go to settings and update token, only with OK button
            reply = QMessageBox.information(self, 'Токен устарел',
                                            'Кажется, ваш токен устарел, необходимо войти в VK.\n\n'
                                            'Перейдите в настройки и нажмите "Авторизоваться".',
                                            QMessageBox.Ok, QMessageBox.Ok)

            # Show info dialog with suggestion to go to settings and update token
            # reply = QMessageBox.question(self, 'Токен устарел',
            #                              'Кажется, ваш токен устарел, необходимо заново авторизоваться.\n'
            #                              'Перейти в настройки?',
            #                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            # if reply == QMessageBox.Yes:
            #     self.tab_widget.setCurrentIndex(1)
            return

            # self.get_token()
            # user_info = vk.users.get()[0]
            # self.add_log("Токен в файле config_path успешно сброшен")
        title_playlist = f"Импортированная музыка от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        report_filename = f"Отчет об импорте за {datetime.now().strftime('%d.%m.%Y %H-%M')}.txt"
        playlist_img = None
        self.add_log(f"Авторизовался как {user_info['first_name']} {user_info['last_name']} (id: {user_info['id']})")

        # Getting Spotify playlist
        use_audio_links = False
        if self.env.SPOTIFY_MODE:
            while True:
                spotify_playlist_url = self.show_input_dialog('Ссылка на Spotify',
                                                              'Вставь сюда ссылку на плейлист в Spotify')
                if spotify_playlist_url is None:
                    self.stop_import()
                    self.add_log("Отменено пользователем...")
                    return
                spotify_playlist_url = spotify_playlist_url.strip()
                # Use better input dialog in pyside2 (QInputDialog)
                tracklist_response = requests.post('https://spotya.ru/data.php', json={
                    "url": f"https://spotya.ru/api.php?playlist={spotify_playlist_url}",
                    "type": "playlist"
                })
                tracklist_text = tracklist_response.text.replace('\ufeff', '')
                if len(tracklist_text) != 0:
                    break
                self.add_log("Не сумел прочитать треки из плейлиста. У тебя точно открытый плейлист?")
            self.add_log(f"Нашел {tracklist_text.count('&#10;') + 1} треков в плейлисте")
            tracklist_content = tracklist_text.replace('&#10;', '\n').strip()
            self.add_log("Сохраняю в tracklist.txt...")
            with open("tracklist.txt", "w", encoding="utf-8") as f:
                f.write(tracklist_content)
            playlist_info_response = requests.post('https://spotya.ru/data.php', json={
                "url": f"https://spotya.ru/api.php?playlist={spotify_playlist_url}",
                "type": "poster"
            })
            self.add_log("Загружаю метаданные...")
            try:
                playlist_info = json.loads(playlist_info_response.text.replace('\ufeff', ''))
            except json.JSONDecodeError as e:
                self.add_log(f"Не сумел загрузить метаданные из плейлиста ({e}). Пропускаю этот этап...")
            else:
                title_playlist = playlist_info["name"]
                playlist_img = playlist_info["image"]
                self.add_log(f"Получил метаданные для плейлиста \"{playlist_info['name']}\"")
        elif self.env.APPLE_MODE:
            self.add_log('Начинаю импорт из Apple Music...')
            self.add_log('Важно: данный функционал находится в бета-тестировании и может работать некорректно.')
            try:
                with open(fix_relative_path('tracklist.csv'), newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile, dialect='excel-tab')
                    tracks = open(fix_relative_path('export-tracklist.txt'), 'w', encoding="utf-8")
                    for row in reader:
                        tracks.write(row['Артист'] + ' - ' + row['Название'] + '\n')
                    tracks.close()
            except FileNotFoundError:
                self.add_log("Не найден плейлист. Нужно указать корректный путь до файла <имя плейлиста>.txt")
                return
        elif self.env.VK_LINKS_MODE:
            use_audio_links = True

        # Open tracklist
        self.add_log("Загружаю треклист...")
        try:
            with open("tracklist.txt", "r", encoding="utf-8") as f:
                text_lines = f.readlines()
        except FileNotFoundError:
            self.add_log("Не найден треклист (tracklist.txt). Вы не забыли его предварительно создать?")
            return
        if use_audio_links:
            for text_line in text_lines:
                parsed_row = re.match(r"^https://vk\.com/audio(\d+)_(\d+)(?:_([a-z0-9]+))?", text_line)
                if parsed_row is not None and len(parsed_row.groups()) == 3:
                    tracklist.append(parsed_row.groups())
        else:
            for text_line in text_lines:
                parsed_row = re.match(r"^([^-—]+)[-—]([^\r\n]+)", text_line)
                if parsed_row is not None:
                    tracklist.append((parsed_row.group(1).strip(), parsed_row.group(2).strip()))
                    continue
                parsed_row = re.match(r"^(\S+)\s(.+)", text_line)
                if parsed_row is not None:
                    track_info = (parsed_row.group(1).strip(), parsed_row.group(2).strip(),)
                    tracklist.append(track_info)
                    self.add_log(
                        f"В строчке треклиста нет дефиса, разделил вручную: {track_info[0]} - {track_info[1]}")

        # Search and add tracks
        if self.env.REVERSE:
            tracklist.reverse()
        self.add_log(
            f"Буду {'добавлять' if use_audio_links else 'искать'} {len(tracklist)} из {len(text_lines)} треков...")

        is_continue = False
        if os.path.exists(fix_relative_path("progress.json")):
            # Ask user to continue from last progress
            reply = QMessageBox.question(self, 'Подтверждение',
                                         'Найден файл с прошлого незаконченного переноса, продолжить с него?\n'
                                         'Важно: треклист должен быть тот же самый, иначе возможны ошибки.',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                with open(fix_relative_path("progress.json"), "r", encoding="utf-8") as f:
                    progress = json.load(f)
                self.ok_tracks = progress['ok_tracks']
                self.questionable_tracks = progress['questionable_tracks']
                self.playlist_response = progress['playlist_response']
                is_continue = True
                self.add_log(f"Продолжаю с {len(self.ok_tracks) + len(self.questionable_tracks)} трека...")

                # Удаляем треки из tracklist, которые уже добавлены
                for track in self.ok_tracks + self.questionable_tracks:
                    if (track[0], track[1]) in tracklist:
                        tracklist.remove((track[0], track[1]))
            else:
                os.remove(fix_relative_path("progress.json"))
                self.add_log("Начинаю сначала...")

        # if self.env.UPDATE_PLAYLIST:
        #     # Ask user to input link to existing VK playlist
        #     playlist_url = self.show_input_dialog('Ссылка на плейлист',
        #                                           'Вставьте ссылку на существующий плейлист в VK, чтобы обновить его.')
        #     if playlist_url is None:
        #         self.stop_import()
        #         self.add_log("Отменено пользователем...")
        #         return
        #     playlist_url = playlist_url.strip()
        #     parsed_url = urlparse(playlist_url)
        #     if parsed_url.scheme != 'https' or \
        #             parsed_url.netloc != 'vk.com' or \
        #             not (parsed_url.path.startswith('/audios') or parsed_url.path.startswith('/music')):
        #         self.add_log("Некорректная ссылка на плейлист, пропускаю этот этап...")
        #     else:
        #         playlist_id = ''
        #         # https://vk.com/audios95755136?section=all&z=audio_playlist95755136_77191690 -> 77191690
        #         if parsed_url.path.startswith('/audios'):
        #             playlist_id = parse_qs(parsed_url.query)['z'][0].split('_')[-1]
        #         # https://vk.com/music/playlist/95755136_77191690_501288fa2e11eed984 -> 77191690
        #         elif parsed_url.path.startswith('/music'):
        #             playlist_id = parsed_url.path.split('/')[-1].split('_')[1]
        #
        #         try:
        #             assert playlist_id.isdigit(), "Некорректная ссылка на плейлист (id not int), пропускаю этот этап..."
        #             self.playlist_response = vk_session.method("audio.getPlaylistById", {
        #                 "owner_id": user_info['id'],
        #                 "playlist_id": int(playlist_id),
        #             })
        #         except (vk_api.VkApiError, AssertionError) as e:
        #             self.add_log(
        #                 f"Не получается получить информацию о плейлисте, ошибка: \"{e}\". Останавливаю импорт...")
        #             self.stop_import()
        #         else:
        #             self.add_log(f"Получил базовую информацию о плейлисте \"{self.playlist_response['title']}\"")
        #             title_playlist = self.playlist_response['title']
        #             count = self.playlist_response['count']
        #             # playlist_img = self.playlist_response['photo']['photo_600']
        #             is_continue = True
        #
        #             # Getting playlist tracks by HTML parsing
        #             parsed_tracklist = []
        #             try:
        #                 raw_response = requests.get(f"https://m.vk.com/music/playlist/{user_info['id']}_{playlist_id}", impersonate="chrome101")
        #                 soup = BeautifulSoup(raw_response.text, 'lxml')
        #                 for track in soup.find_all('div', {'class': 'audio_row__inner'}):
        #                     artist = track.find('div', {'class': 'audio_row__performers'}).text
        #                     title = track.find('div', {'class': 'audio_row__title_inner'}).text
        #                     parsed_tracklist.append((artist, title,))
        #             except Exception as e:
        #                 self.add_log(f"Не получается получить содержимое плейлиста в VK (он точно публичный?), ошибка: \"{e}\".\n"
        #                              f"Возможно, метод парсинга устарел. Останавливаю импорт...")
        #                 self.stop_import()
        #
        #             if len(parsed_tracklist) != count:
        #                 self.add_log(f"Количество спарсенных треков в плейлисте не совпадает с данными VK API ({len(parsed_tracklist)} != {count}). Останавливаю импорт...")
        #                 self.stop_import()
        #
        #             # Удаляем треки из tracklist, которые уже добавлены до последнего трека в плейлисте (parsed_tracklist)
        #             last_track = parsed_tracklist[-1]
        #             for i, track in enumerate(tracklist):
        #                 if fuzz.ratio(track[0], last_track[0]) > 80 and fuzz.ratio(track[1], last_track[1]) > 80:
        #                     self.add_log(f"Нашел последний добавленный трек в плейлисте: \"{track[0]} - {track[1]}\" (номер {i + 1} в импортируемом треклисте)")
        #                     tracklist = tracklist[i + 1:]
        #                     break

        self.ok_tracks = []
        self.questionable_tracks = []
        failed_tracks = []
        added_count = 0
        chucked_rows = list(chunks(tracklist, 1000))
        playlists = []
        for k, chunk_row in enumerate(chucked_rows, 1):
            self.add_log("Создаем плейлист для добавления музыки...")
            if len(chucked_rows) > 1:
                title_playlist = f'[{k}/{len(chucked_rows)}] {title_playlist}'
            if not is_continue:
                try:
                    self.playlist_response = vk_session.method("audio.createPlaylist", {
                        "owner_id": user_info['id'],
                        "title": title_playlist
                    })
                except vk_api.VkApiError as e:
                    self.add_log(
                        f"Не получается создать плейлист, ошибка: \"{e}\".Попробуйте еще раз позже или обновите токен.")
                    self.stop_import()
                    return
            is_continue = False
            playlists.append(f"https://vk.com/audios{user_info['id']}?"
                             f"section=all&z=audio_playlist{user_info['id']}_{self.playlist_response['id']}")
            if 'id' not in self.playlist_response:
                raise PermissionError(
                    f"VK не позволяет создать плейлист, повторите позже. Доп. информация: {self.playlist_response}")
            for i, track_row in enumerate(chunk_row, 1):
                if not use_audio_links:
                    artist, title = track_row
                    if self.is_running is False:
                        return
                    self.add_log(f"Ищу трек \"{title}\" от исполнителя {artist} ({i} из {len(tracklist)})...")
                    self.update_progress_bar(int(i / len(tracklist) * 100))
                    try:
                        response = vk_session.method("audio.search", {"q": f"{artist} - {title}", "count": 3})
                    except vk_api.VkApiError as e:
                        self.add_log(f"Не получить трек, ошибка: \"{e}\". Жду 10 секунд (программа может зависнуть)...")
                        sleep(self.env.TIMEOUT_AFTER_ERROR)
                        response = vk_session.method("audio.search", {"q": f"{artist} - {title}", "count": 3})
                    if 'items' not in response:
                        raise PermissionError(
                            f"VK временно заблокировал доступ к API, повторите позже. Доп. информация: {response}")
                    if len(response['items']) == 0:
                        failed_tracks.append(track_row)
                        self.add_log(f"Трек не найден в VK Музыке (исполнитель: {artist}, трек: {title})")
                        continue
                    full_matched = None
                    for item in response['items']:
                        if item['artist'].lower() == artist.lower() and title.lower() == item['title'].lower():
                            full_matched = item
                            break
                    if full_matched is not None:
                        self.ok_tracks.append(track_row)
                        track_info = full_matched
                        self.add_log(f"Успешно нашел трек \"{title}\" от исполнителя {artist}")
                    elif self.env.STRICT_SEARCH:
                        failed_tracks.append(track_row)
                        self.add_log(
                            f"Точного совпадения не найдено, пропускаю трек (исполнитель: {artist}, трек: {title})")
                        continue
                    else:
                        partially_matched = response['items'][0]
                        track_info = partially_matched
                        self.questionable_tracks.append(
                            track_row + (partially_matched['artist'], partially_matched['title'],))
                        self.add_log(f"Нашел похожий трек: \"{artist} - {title}\" → \"{partially_matched['artist']} - "
                                     f"{partially_matched['title']}\"")
                    self.add_log(
                        f"Добавляю \"{track_info['artist']} - {track_info['title']}\" (id: {track_info['id']}) в плейлист...")
                else:
                    owner_id, track_id, access_key = track_row
                    track_info = {
                        'owner_id': owner_id,
                        'id': track_id,
                        'access_key': access_key,
                        'title': '',
                        'artist': '',
                    }
                audio_ids = f"{track_info['owner_id']}_{track_info['id']}"
                if use_audio_links and track_info['access_key'] is not None:
                    audio_ids += f"_{track_info['access_key']}"
                try:
                    add_to_playlist_response = vk_session.method("audio.addToPlaylist", {
                        "owner_id": user_info['id'],
                        "playlist_id": self.playlist_response['id'],
                        "audio_ids": audio_ids,
                    })
                except vk_api.VkApiError as e:
                    self.add_log(
                        f"Не получается добавить трек в плейлист, ошибка: \"{e}\". Жду 10 секунд (программа может зависнуть)...")
                    sleep(self.env.TIMEOUT_AFTER_ERROR)
                    delayed_response = None
                    try:
                        delayed_response = vk_session.method("audio.addToPlaylist", {
                            "owner_id": user_info['id'],
                            "playlist_id": self.playlist_response['id'],
                            "audio_ids": track_info['id'],
                        })
                    except vk_api.VkApiError as e:
                        self.add_log(
                            f"Не получается повторно добавить трек в плейлист \"{e}\". Если ошибка повторится, "
                            f"перезапустите скрипт спустя некоторое время ({delayed_response}).")
                else:
                    if len(add_to_playlist_response) == 0:
                        self.add_log(f"Ошибка добавления в плейлист: возвращен пустой ответ, возможно, "
                                     f"у вас нет прав на добавление трека (id: {track_info['id']})")
                        continue
                if self.env.ADD_TO_LIBRARY:
                    self.add_log(
                        f"Добавляю \"{track_info['artist']} - {track_info['title']}\" (id: {track_info['id']}) в мои аудиозаписи...")
                    add_params = {
                        'audio_id': track_info['id'],
                        'owner_id': track_info['owner_id']
                    }
                    if use_audio_links and track_info['access_key'] is not None:
                        add_params['access_key'] = track_info['access_key']
                    try:
                        vk_session.method("audio.add", add_params)
                    except vk_api.VkApiError as e:
                        self.add_log(
                            f"Не получается добавить трек в мои аудиозаписи, ошибка: \"{e}\". Пропускаю трек...")
                    else:
                        self.add_log(
                            f"Успешно добавил в мои аудиозаписи: \"{track_info['artist']} - {track_info['title']}\"")
                if use_audio_links:
                    self.add_log(f"Успешно добавил в плейлист: \"id: {track_info['id']}\"")
                else:
                    self.add_log(f"Успешно добавил в плейлист: \"{track_info['artist']} - {track_info['title']}\"")
                added_count += 1
                if self.env.TIMEOUT_AFTER_SUCCESS > 0:
                    self.add_log(f"Жду {self.env.TIMEOUT_AFTER_SUCCESS} секунд (программа может зависнуть)...")
                    sleep(self.env.TIMEOUT_AFTER_SUCCESS)
                self.is_under_ban = False

        if len(tracklist) != added_count:
            self.add_log(f"Выполнено, но в плейлист добавилось не всё: {added_count} из {len(tracklist)}")
        else:
            self.add_log(f"Выполнено успешно! Все найденные треки добавлены")

        self.add_log(f"Найдено треков с точными совпадениями: {len(self.ok_tracks)}")
        self.add_log(f"Найдено треков с примерными совпадениями: {len(self.questionable_tracks)}")
        self.add_log(f"Не найдено треков: {len(failed_tracks)}")

        self.add_log(f"Всего перенесено треков: {added_count} из {len(text_lines)}")
        with open(fix_relative_path(report_filename), 'w', encoding='utf-8') as f:
            questionable_tracks_str = '\n'.join(
                f'- "{t[0]} - {t[1]}" → "{t[2]} - {t[3]}"' for t in self.questionable_tracks)
            ok_tracks_str = '\n'.join(f'- "{t[0]} - {t[1]}"' for t in self.ok_tracks)
            failed_tracks_str = '\n'.join(f'- "{t[0]} - {t[1]}"' for t in failed_tracks)
            playlists_str = '\n'.join(f'- {p}' for p in playlists)
            f.write(f"""
[ Отчет о перенесенных треках в VK Музыку ]

Дата/время: {datetime.now().strftime('%d.%m.%Y %H:%M')}.
Название плейлиста (если доступно): {title_playlist or '-'}
Изображение плейлиста (если доступно): {playlist_img or '-'}
Найдено треков с точными совпадениями: {len(self.ok_tracks)}
Найдено треков с примерными совпадениями: {len(self.questionable_tracks)}
Не найдено треков: {len(failed_tracks)}
{f'Добавлено треков по прямым ссылкам: {len(tracklist)}' if use_audio_links else ''}

ССЫЛКИ:

{playlists_str or '[x]'}


СПИОК НАЙДЕННЫХ ТРЕКОВ:

{ok_tracks_str or '[x]'}


СПИСОК НАЙДЕННЫХ ПОХОЖИХ ТРЕКОВ:

{questionable_tracks_str or '[x]'}


СПИСОК НЕНАЙДЕННЫХ ТРЕКОВ:

{failed_tracks_str or '[x]'}


♫ Музыка перенесена с помощью vk-music-import

- Телеграм-канал автора: https://t.me/mewnotes
- Поддержать разработчика: https://mewforest.github.io/donate/
- Исходный код: https://github.com/mewforest/vk-music-import
            """.strip())

        self.add_log(f"Файл отчета сгенерирован в текущей папке (\"{report_filename}\")")

        # Set gui to Start again
        self.stop_import()

        if os.path.exists(fix_relative_path("progress.json")):
            os.remove(fix_relative_path("progress.json"))
        if len(playlists) == 1:
            self.add_log(f"Скрипт выполнен! Твой плейлист готов: {playlists[0]}")
        else:
            self.add_log(f"Скрипт выполнен! Ваши плейлисты готовы: {', '.join(playlists)}")
        # if playlist_img is not None:
        #    self.add_log(f"Дополнительно: скачать обложку плейлиста можно здесь: {playlist_img}")
        self.show_success_dialog("Импорт завершен", playlists, report_filename, playlist_img)
        # if platform.system() == "Windows":
        #     webbrowser.open(fix_relative_path(report_filename))

    def show_success_dialog(self, title: str, playlists_urls: List[str], report_filename,
                            playlistImageUrl: Optional[str] = None):
        """
        Показывает диалог успешного завершения импорта плейлиста: ссылки на плейлисты и обложку с кнопкой скачивания (если есть).
        А еще тут есть кнопка "просмотреть отчет"
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.resize(400, 200)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(
            "<b>Импорт завершен!</b>\n\n"
            "Треки успешно импортированы, посмотрите отчет или скачайте обложку плейлиста."))
        for playlist_url in playlists_urls:
            playlist_url_label = QLabel(f'<a href="{playlist_url}">{playlist_url}</a>')
            playlist_url_label.setOpenExternalLinks(True)
            layout.addWidget(playlist_url_label)

        # Playlist image
        if playlistImageUrl is not None:
            playlist_image_response = requests.get(playlistImageUrl)
            playlist_image = QImage()
            playlist_image.loadFromData(playlist_image_response.content)
            playlist_image_label = QLabel()
            playlist_image_pixmap = QPixmap.fromImage(playlist_image).scaled(200, 200,
                                                                             aspectRatioMode=Qt.KeepAspectRatio)
            playlist_image_label.setPixmap(playlist_image_pixmap)
            layout.addWidget(playlist_image_label, alignment=Qt.AlignCenter)
            download_image_button = QPushButton("Скачать обложку")
            download_image_button.clicked.connect(lambda: self.download_image(playlist_image_response.content))

        if platform.system() == "Windows":
            show_report_button = QPushButton("Просмотреть отчет")
            show_report_button.setStyleSheet("QPushButton {font-weight: bold; margin-top: 10px;}")
            show_report_button.setFixedHeight(40)
            show_report_button.clicked.connect(
                lambda: webbrowser.open(fix_relative_path(report_filename)))
            layout.addWidget(show_report_button)

        if playlistImageUrl is not None:
            layout.addWidget(download_image_button)
        dialog.setLayout(layout)
        dialog.exec_()

    def download_image(self, image: bytes):
        """
        Скачивает обложку плейлиста
        """
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранить обложку плейлиста', 'playlist.jpg',
                                                  "Images (*.jpg *.png)")
        if filename:
            with open(filename, "wb") as f:
                f.write(image)

    def stop_import(self):
        self.is_running = False
        self.start_button.setText("Начать импорт")

    def save_progress_to_file(self):
        """
        Сохраняет прогресс в JSON файл (self.ok_tracks, self.questionable_tracks, self.playlist_response)
        """
        with open(fix_relative_path("progress.json"), "w", encoding="utf-8") as f:
            json.dump({
                "ok_tracks": self.ok_tracks,
                "questionable_tracks": self.questionable_tracks,
                "playlist_response": self.playlist_response,
            }, f, indent=4)

    def captcha_handler(self, captcha: Captcha):
        """
        Хендлер для обработки капчи из VK
        """
        if self.is_under_ban:
            # If captcha showed up before, show dialog yes/no to pause current progress and exit
            reply = QMessageBox.question(self, 'Сделаем паузу?',
                                         'Кажется, VK снова запросил капчу, это значит, что vk временно блокирует возможность импорта музыки.\n'
                                         'Возможно, стоит сделать перерыв в запросах и продолжить позже?\n\n'
                                         'Если вы нажмете "Да", то скрипт остановится, но вы сможете продолжить импорт позже.\n'
                                         'Если вы нажмете "Нет", то скрипт продолжит работу, но возможно, что vk так и не захочет импортировать.\n',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.save_progress_to_file()
                self.stop_import()
                self.add_log("Останавливается пользователем...")
                return captcha.try_again('')
            else:
                self.add_log("Продолжаю работу, но vk может не захотеть импортировать...")
                self.is_under_ban = False

        self.is_under_ban = True
        start_time = datetime.now()
        captcha_url = captcha.get_url()
        parsed_url = urlparse(captcha_url)
        parsed_url_params = parse_qs(parsed_url.query)
        captcha_sid = parsed_url_params["sid"][0]
        captcha_s = parsed_url_params["s"][0]
        captcha_params_parsed = {
            "sid": int(captcha_sid),
            "s": int(captcha_s)
        }
        if self.env.BYPASS_CAPTCHA:
            self.add_log("Появилась капча, пытаюсь автоматически её решить...")
            key = solve_captcha(sid=captcha_params_parsed["sid"], s=captcha_params_parsed["s"])
        else:
            self.add_log("Чтобы продолжить, введи капчу с картинки во всплывающем окне")
            response = requests.get(f'https://api.vk.com/captcha.php?sid={0}&s={1}'.format(
                captcha_params_parsed["sid"], captcha_params_parsed["s"]))
            img = Image.open(BytesIO(response.content)).resize((128, 64)).convert('RGB')
            key = get_user_solve(captcha_image=img, captcha_params_parsed=captcha_params_parsed)
            if key is None:
                self.add_log("Капча не решена, завершаю работу...")
                sys.exit(1)
        elapsed_time = datetime.now() - start_time
        self.add_log(f"Капча решена за {elapsed_time.microseconds * 0.001}мс")
        if self.env.TIMEOUT_AFTER_CAPTCHA > 0:
            self.add_log(f"Чтобы VK не ругался, жду {self.env.TIMEOUT_AFTER_CAPTCHA} сек...")
            self.add_log(f"(Программа может подвиснуть на {self.env.TIMEOUT_AFTER_CAPTCHA} секунд)")
            sleep(self.env.TIMEOUT_AFTER_CAPTCHA)
        self.add_log("Отправляю решение капчи...")
        return captcha.try_again(key)


# Creating a class for the settings tab
class SettingsTab(QWidget, MainEnv):
    def __init__(self):
        # Call both parents constructors
        QWidget.__init__(self)
        MainEnv.__init__(self)
        # Creating a form layout for the tab
        self.layout = QFormLayout()
        # Creating radio buttons for the mode selection
        self.tracklist_mode = QRadioButton("Треклист (tracklist.txt)")
        self.spotify_mode = QRadioButton("Плейлист Spotify")
        self.apple_mode = QRadioButton("Плейлист из Apple Music")
        self.vk_links_mode = QRadioButton("Список ссылок на треки в VK")
        self.reverse = QCheckBox()
        self.strict_search = QCheckBox()
        self.add_to_library = QCheckBox()
        self.bypass_captcha = QCheckBox()
        # self.update_playlist = QCheckBox()
        # Creating line edits for the string and integer environment variables
        self.vk_token = QLineEdit()
        self.vk_token.setPlaceholderText("Нажмите \"Авторизоваться\", чтобы войти в VK")
        self.timeout_after_error = QLineEdit()
        self.timeout_after_captcha = QLineEdit()
        self.timeout_after_success = QLineEdit()
        # Setting the initial values of the widgets from the environment variables
        self.tracklist_mode.setChecked(
            not self.env.SPOTIFY_MODE and not self.env.APPLE_MODE and not self.env.VK_LINKS_MODE)
        self.spotify_mode.setChecked(self.env.SPOTIFY_MODE)
        self.apple_mode.setChecked(self.env.APPLE_MODE)
        self.vk_links_mode.setChecked(self.env.VK_LINKS_MODE)
        self.bypass_captcha.setChecked(self.env.BYPASS_CAPTCHA)
        self.reverse.setChecked(self.env.REVERSE)
        self.strict_search.setChecked(self.env.STRICT_SEARCH)
        self.add_to_library.setChecked(self.env.ADD_TO_LIBRARY)
        # self.update_playlist.setChecked(self.env.UPDATE_PLAYLIST)
        self.vk_token.setText(self.env.VK_TOKEN)
        self.timeout_after_error.setText(str(self.env.TIMEOUT_AFTER_ERROR))
        self.timeout_after_captcha.setText(str(self.env.TIMEOUT_AFTER_CAPTCHA))
        self.timeout_after_success.setText(str(self.env.TIMEOUT_AFTER_SUCCESS))
        # Adding help tooltips to the widgets
        self.tracklist_mode.setToolTip("Импортировать треки из файла tracklist.txt")
        self.spotify_mode.setToolTip("Импортировать треки из плейлиста Spotify (SPOTIFY_MODE)")
        self.apple_mode.setToolTip("Импортировать треки из экспортированного CSV-плейлиста Apple Music (APPLE_MODE)")
        self.vk_links_mode.setToolTip("Импортировать треки из списка ссылок на треки в VK Музыке (VK_LINKS_MODE)")
        self.bypass_captcha.setToolTip(
            "Автоматически решать капчу, если выключена, ответ придётся вводить вручную (BYPASS_CAPTCHA)")
        self.reverse.setToolTip(
            "Добавлять треки в обратном порядке - подходит по-умолчанию для плейлистов Spotify (REVERSE)")
        self.strict_search.setToolTip(
            "Искать только точные совпадения, если выключено может добавить ремикс или 'перезалив' оригинальной композиции (STRICT_SEARCH)")
        self.add_to_library.setToolTip("Добавлять треки в Мои Аудиозаписи (ADD_TO_LIBRARY)")
        # self.update_playlist.setToolTip("Обновлять плейлист, если он уже существует (UPDATE_PLAYLIST)")
        self.vk_token.setToolTip("Токен VK API, через него утилита получает доступ к вашим аудиозаписям (VK_TOKEN)")
        self.timeout_after_error.setToolTip("Задержка после ошибки, сек (TIMEOUT_AFTER_ERROR)")
        self.timeout_after_captcha.setToolTip("Задержка после капчи, сек (TIMEOUT_AFTER_CAPTCHA)")
        self.timeout_after_success.setToolTip(
            "Задержка после успешного добавления аудиозаписи, сек (TIMEOUT_AFTER_SUCCESS)")
        # Adding the widgets and their labels to the form layout
        # VK Token + refresh button
        self.vk_token_layout = QHBoxLayout()
        self.vk_token_layout.addWidget(self.vk_token)
        self.vk_token_refresh_button = QPushButton("Авторизоваться заново" if self.env.VK_TOKEN else 'Авторизоваться')
        self.vk_token_refresh_button.clicked.connect(self.get_token)
        self.vk_token_layout.addWidget(self.vk_token_refresh_button)
        self.layout.addRow("Токен от ВКонтакте", self.vk_token_layout)
        self.layout.addRow("Откуда импортировать:", self.tracklist_mode)
        self.layout.addRow("", self.spotify_mode)
        self.layout.addRow("", self.apple_mode)
        self.layout.addRow("", self.vk_links_mode)
        self.layout.addRow("Автоматический обход капчи", self.bypass_captcha)
        self.layout.addRow("В обратном порядке", self.reverse)
        self.layout.addRow("Только точные совпадения", self.strict_search)
        self.layout.addRow("Добавлять в Мои Аудиозаписи", self.add_to_library)
        # self.layout.addRow("Обновлять существующий плейлист", self.update_playlist)
        self.layout.addRow("Задержка после ошибок, сек", self.timeout_after_error)
        self.layout.addRow("Задержка после капчи, сек", self.timeout_after_captcha)
        self.layout.addRow("Задержка после успеха, сек", self.timeout_after_success)
        # Creating save and reset button
        self.save_button = QPushButton("Сохранить настройки")
        self.reset_button = QPushButton("Сбросить настройки")
        self.save_button.setStyleSheet("QPushButton {font-weight: bold; margin-top: 10px;}")
        self.save_button.setFixedHeight(40)
        # Connecting save and reset button to a function that updates the environment variables
        self.save_button.clicked.connect(self.save_envs)
        self.reset_button.clicked.connect(self.reset_envs)
        # Adding save and reset button to the form layout
        self.layout.addRow(self.save_button)
        self.layout.addRow(self.reset_button)
        # Setting the layout for the tab
        self.setLayout(self.layout)

    def reset_envs(self):
        # Ask user to confirm reset
        reply = QMessageBox.question(self, 'Подтверждение',
                                     'Вы уверены, что хотите сбросить настройки?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        # Setting the environment variables using the set_key function
        set_key(config_path, "BYPASS_CAPTCHA", "1")
        set_key(config_path, "SPOTIFY_MODE", "1")
        set_key(config_path, "APPLE_MODE", "0")
        set_key(config_path, "VK_LINKS_MODE", "0")
        set_key(config_path, "REVERSE", "1")
        set_key(config_path, "STRICT_SEARCH", "0")
        set_key(config_path, "ADD_TO_LIBRARY", "1")
        set_key(config_path, "VK_TOKEN", "")
        set_key(config_path, "TIMEOUT_AFTER_ERROR", "1")
        set_key(config_path, "TIMEOUT_AFTER_CAPTCHA", "0")
        set_key(config_path, "TIMEOUT_AFTER_SUCCESS", "0")
        # set_key(config_path, "UPDATE_PLAYLIST", "0")
        # Reloading the config_path file
        self.load_env_config()
        # Setting the initial values of the widgets from the environment variables
        self.tracklist_mode.setChecked(
            not self.env.SPOTIFY_MODE and not self.env.APPLE_MODE and not self.env.VK_LINKS_MODE)
        self.spotify_mode.setChecked(self.env.SPOTIFY_MODE)
        self.apple_mode.setChecked(self.env.APPLE_MODE)
        self.vk_links_mode.setChecked(self.env.VK_LINKS_MODE)
        self.bypass_captcha.setChecked(self.env.BYPASS_CAPTCHA)
        self.reverse.setChecked(self.env.REVERSE)
        self.strict_search.setChecked(self.env.STRICT_SEARCH)
        self.add_to_library.setChecked(self.env.ADD_TO_LIBRARY)
        self.vk_token.setText(self.env.VK_TOKEN)
        self.timeout_after_error.setText(str(self.env.TIMEOUT_AFTER_ERROR))
        self.timeout_after_captcha.setText(str(self.env.TIMEOUT_AFTER_CAPTCHA))
        self.timeout_after_success.setText(str(self.env.TIMEOUT_AFTER_SUCCESS))
        # self.add_log("Настройки сброшены")

    # Defining a function that updates the environment variables
    def save_envs(self):
        # Converting the checkboxes to 0 or 1
        bypass_captcha = "1" if self.bypass_captcha.isChecked() else "0"
        spotify_mode = "1" if self.spotify_mode.isChecked() else "0"
        apple_mode = "1" if self.apple_mode.isChecked() else "0"
        vk_links_mode = "1" if self.vk_links_mode.isChecked() else "0"
        reverse = "1" if self.reverse.isChecked() else "0"
        strict_search = "1" if self.strict_search.isChecked() else "0"
        add_to_library = "1" if self.add_to_library.isChecked() else "0"
        # update_playlist = "1" if self.update_playlist.isChecked() else "0"
        # If tracklist mode is selected, set all the other modes to 0
        if self.tracklist_mode.isChecked():
            spotify_mode = "0"
            apple_mode = "0"
            vk_links_mode = "0"
        # Getting the values of the line edits
        vk_token = self.vk_token.text()
        timeout_after_error = self.timeout_after_error.text()
        timeout_after_captcha = self.timeout_after_captcha.text()
        timeout_after_success = self.timeout_after_success.text()
        # Setting the environment variables using the set_key function
        set_key(config_path, "BYPASS_CAPTCHA", bypass_captcha)
        set_key(config_path, "SPOTIFY_MODE", spotify_mode)
        set_key(config_path, "APPLE_MODE", apple_mode)
        set_key(config_path, "VK_LINKS_MODE", vk_links_mode)
        set_key(config_path, "REVERSE", reverse)
        set_key(config_path, "STRICT_SEARCH", strict_search)
        set_key(config_path, "ADD_TO_LIBRARY", add_to_library)
        set_key(config_path, "VK_TOKEN", vk_token)
        # set_key(config_path, "UPDATE_PLAYLIST", update_playlist)
        set_key(config_path, "TIMEOUT_AFTER_ERROR", timeout_after_error)
        set_key(config_path, "TIMEOUT_AFTER_CAPTCHA", timeout_after_captcha)
        set_key(config_path, "TIMEOUT_AFTER_SUCCESS", timeout_after_success)
        # Reloading the config_path file
        self.load_env_config()

    def get_token(self):
        self.token_dialog = QDialog()
        self.token_dialog.setWindowTitle('Необходимо авторизоваться во ВКонтакте')
        self.token_dialog.setFixedSize(500, 150)

        layout = QVBoxLayout()

        # Add instructions label
        instructions_label = QLabel(self.token_dialog)
        instructions_label.setText(
            "1. Перейди по ссылке ниже и нажми 'Разрешить'\n"
            "2. Скопируй ссылку из адресной строки браузера и вставь её в следующем\n"
            "диалоге.".strip())
        layout.addWidget(instructions_label)

        # Add open link button
        open_link_button = QPushButton(self.token_dialog)
        open_link_button.setText('Открыть ссылку для авторизации')
        layout.addWidget(open_link_button)

        # Add copy link button
        copy_link_button = QPushButton(self.token_dialog)
        copy_link_button.setText('Скопировать ссылку в буфер обмена')
        layout.addWidget(copy_link_button)

        # Connect open link button clicked event
        open_link_button.clicked.connect(self.open_vk_authorization_link)

        # Connect copy link button clicked event
        copy_link_button.clicked.connect(self.copy_vk_authorization_link)

        self.token_dialog.setLayout(layout)
        self.token_dialog.exec_()

    def open_vk_authorization_link(self):
        link = 'https://oauth.vk.com/oauth/authorize?client_id=6121396' \
               '&scope=audio,offline' \
               '&redirect_uri=https://oauth.vk.com/blank.html' \
               '&display=page' \
               '&response_type=token' \
               '&revoke=1' \
               '&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991'
        QDesktopServices.openUrl(QUrl(link))
        self.input_token_url()

    def copy_vk_authorization_link(self):
        link = 'https://oauth.vk.com/oauth/authorize?client_id=6121396' \
               '&scope=audio,offline' \
               '&redirect_uri=https://oauth.vk.com/blank.html' \
               '&display=page' \
               '&response_type=token' \
               '&revoke=1' \
               '&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991'
        clipboard = QApplication.clipboard()
        clipboard.setText(link, QClipboard.Clipboard)
        self.input_token_url()

    def input_token_url(self):
        """
        Shows input dialog for token url and saves it to config_path
        """
        self.token_input_dialog = QDialog()
        self.token_input_dialog.setWindowTitle('Вставь ссылку с токеном')
        self.token_input_dialog.setFixedSize(400, 150)

        layout = QVBoxLayout()

        # Add instructions label
        instructions_label = QLabel(self.token_input_dialog)
        instructions_label.setText(
            "После того, как вы нажмёте \"Разрешить\" откроется пустая\n"
            "страница, скопируй ссылку на неё из адресной строки\n"
            "браузера и вставь её в поле ниже:")
        layout.addWidget(instructions_label)

        # Add token entry
        token_entry = QLineEdit(self.token_input_dialog)
        layout.addWidget(token_entry)

        # Add submit button
        submit_button = QPushButton(self.token_input_dialog)
        submit_button.setText('Сохранить')
        layout.addWidget(submit_button)

        # Connect submit button clicked event
        submit_button.clicked.connect(self.apply_token)

        self.token_input_dialog.setLayout(layout)
        self.token_input_dialog.exec_()

    def apply_token(self):
        """
        Функция для запроса токена от ВКонтакте
        """
        token_url = self.token_input_dialog.findChild(QLineEdit).text()
        token_match = re.match(r'https://oauth.vk.com/blank.html#access_token=([^&]+).+', token_url)
        if token_match is None:
            # self.token_dialog.accept()
            warn_text = "Некорректная ссылка. После того, как вы нажали \"Разрешить\" ссылка должна начинаться с https://oauth.vk.com/blank.html#access_token="
            QMessageBox.warning(self.token_input_dialog, "Некорректная ссылка", warn_text)
            return
        # Applying token
        self.token_input_dialog.accept()
        self.env.VK_TOKEN = token_match.group(1)
        set_key(config_path, "VK_TOKEN", token_match.group(1))
        self.load_env_config()
        # Close token dialog
        self.token_input_dialog.close()
        self.token_dialog.close()
        self.vk_token.setText(token_match.group(1))
        self.vk_token_refresh_button.setText("Авторизоваться заново" if self.env.VK_TOKEN else 'Авторизоваться')


def chunks(lst, n):
    """
    Разделяет список на чанки
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_user_solve(captcha_image: Image, captcha_params_parsed: dict[str, int]) -> Union[str, None]:
    """
    Получает решение капчи от пользователя (GUI)
    """
    dialog = QDialog()
    dialog.setWindowTitle('Введи капчу с картинки')
    dialog.setFixedSize(285, 145)

    layout = QVBoxLayout()

    # Add image label
    image_label = QLabel(dialog)
    captcha_image_bytes = captcha_image.tobytes("raw", "RGB")
    qimage = QImage(captcha_image_bytes, captcha_image.size[0], captcha_image.size[1], QImage.Format_RGB888)
    image_label.setPixmap(QPixmap.fromImage(qimage))
    layout.addWidget(image_label)

    # Add captcha solve entry
    captcha_solve_entry = QLineEdit(dialog)
    captcha_solve_entry.setText(
        solve_captcha(sid=captcha_params_parsed["sid"], s=captcha_params_parsed["s"], img=captcha_image))
    captcha_solve_entry.selectAll()
    layout.addWidget(captcha_solve_entry)

    # Add submit button
    submit_button = QPushButton('Отправить решение', dialog)
    submit_button.clicked.connect(dialog.accept)
    layout.addWidget(submit_button)

    dialog.setLayout(layout)

    if dialog.exec_() == QDialog.Accepted:
        captcha_solve = captcha_solve_entry.text()
        return captcha_solve if captcha_solve else None
    else:
        return None


def solve_captcha(sid, s, img=None):
    """
    Обработчик капчи с помощью машинного зрения
    """
    if img is None:
        response = requests.get(f'https://api.vk.com/captcha.php?sid={sid}&s={s}')
        img = Image.open(BytesIO(response.content)).resize((128, 64)).convert('RGB')
    x = np.array(img).reshape(1, -1)
    x = np.expand_dims(x, axis=0)
    x = x / np.float32(255.)
    session = rt.InferenceSession(fix_relative_path('models/captcha_model.onnx'))
    session2 = rt.InferenceSession(fix_relative_path('models/ctc_model.onnx'))
    out = session.run(None, dict([(inp.name, x[n]) for n, inp in enumerate(session.get_inputs())]))
    out = session2.run(None, dict([(inp.name, np.float32(out[n])) for n, inp in enumerate(session2.get_inputs())]))
    char_map = ' 24578acdehkmnpqsuvxyz'
    captcha = ''.join([char_map[c] for c in np.uint8(out[-1][out[0] > 0])])
    return captcha


if __name__ == "__main__":
    # Logging formatting
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    # Create a RotatingFileHandler with a max size of 10MB
    file_handler = RotatingFileHandler(fix_relative_path('debug.log'), maxBytes=10 * 1024 * 1024, backupCount=1,
                                       encoding='utf-8'
                                       )
    file_handler.setLevel(logging.DEBUG)
    # Add the file handler to the root logger
    logging.getLogger().addHandler(file_handler)

    try:
        # Config path
        config_path = fix_relative_path("config.env")
        # Creating an application instance
        app = QApplication(sys.argv)
        # Apply the complete dark theme to your Qt App.
        qdarktheme.setup_theme('auto', additional_qss="QToolTip {color: black;}")
        # Setting the high DPI scaling
        qdarktheme.enable_hi_dpi()
        # Creating a main window instance
        window = MainWindow()
        # Showing the main window
        window.show()
        # Executing the application
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(e)
