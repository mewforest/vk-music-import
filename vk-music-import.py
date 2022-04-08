"""
Imports music to VK Music from Track list.

AUTH:
https://oauth.vk.com/oauth/authorize?client_id=6121396&scope=8&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991

"""
import json
import logging
import os
import platform
import re
import sys
import webbrowser
from datetime import datetime
from io import BytesIO
from time import sleep
import requests
import vk_api
from PIL import Image
import numpy as np
import onnxruntime as rt
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)


def fix_relative_path(relative_path: str) -> str:
    """
    PyInstaller fix for relative paths
    """
    application_path = ''
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(os.path.abspath(sys.executable))
    elif __file__:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(application_path, relative_path))


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def captcha_handler(captcha):
    captcha_url = captcha.get_url()
    captcha_params = re.match(r"https://api\.vk\.com/captcha\.php\?sid=(\d+)&s=(\d+)", captcha_url)
    if captcha_params is not None and os.getenv("BYPASS_CAPTCHA", "0") == "1":
        logging.info("Появилась капча, пытаюсь автоматически её решить...")
        key = solve(sid=int(captcha_params.group(1)), s=int(captcha_params.group(2)))
        logging.info("Текст на капче обнаружен, отправляю решение...")
    else:
        key = input("\n\n[!] Чтобы продолжить, введи сюда капчу с картинки {0}:\n> ".format(captcha.get_url())).strip()
    return captcha.try_again(key)


def solve(sid, s):
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


def get_token():
    if platform.system() == "Windows":
        text_welcome = """
 [!] Необходимо авторизоваться во ВКонтакте:

 1) Перейди по ссылке ниже и нажми "Разрешить" (чтобы скопировать ссылку, выдели её и нажми CTRL+C):
https://oauth.vk.com/oauth/authorize?client_id=6121396&scope=8&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991

 2) Скопируй ссылку из адресной строки браузера и вставь её сюда (жми CTRL+V):

 > """.lstrip()
    else:
        text_welcome = """
[!] Необходимо авторизоваться во ВКонтакте:
1) Перейди по ссылке ниже и нажми "Разрешить":
https://oauth.vk.com/oauth/authorize?client_id=6121396&scope=8&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991
2) Скопируй ссылку из адресной строки браузера и вставь её сюда:
> """.lstrip()
    token_match = None
    while token_match is None:
        token_url = input(text_welcome).strip()
        token_match = re.match(r'https://oauth.vk.com/blank.html#access_token=([^&]+).+', token_url)
        if token_match is not None:
            break
        logging.error("Некорректная ссылка. После того, как вы нажали \"Разрешить\" ссылка должна начинаться с "
                      "\"https://oauth.vk.com/blank.html#access_token=\"")
        text_welcome = "[!] Вставьте корректную ссылку\n> "
    os.environ["VK_TOKEN"] = token_match.group(1)
    logging.info("Сохраняю токен в .env файл...")
    with open(".env", "r", encoding="utf-8") as f:
        env_content = f.read().replace('\r', '').split()
    for i, env_str in enumerate(env_content):
        if env_str.startswith("VK_TOKEN=\""):
            env_content[i] = f'VK_TOKEN="{token_match.group(1)}"'
    with open(".env", "w", encoding="utf-8") as f:
        f.write('\n'.join(env_content))
    logging.info("Токен успешно сохранен в файл .env")


def main():
    # VK Authentication
    logging.info("Авторизуюсь в ВКонтакте...")
    if os.getenv("VK_TOKEN") == "":
        logging.warning("Не обнаружен токен VK API в .env файле, запрашиваю авторизацию вручную...")
        get_token()
    vk_session = vk_api.VkApi(token=os.getenv("VK_TOKEN"), captcha_handler=captcha_handler)
    vk = vk_session.get_api()
    tracklist = []
    try:
        user_info = vk.users.get()[0]
    except vk_api.exceptions.ApiError as e:
        logging.error(f"Кажется, ваш токен устарел, необходимо заново авторизоваться (ошибка: {e})")
        get_token()
        user_info = vk.users.get()[0]
        logging.info("Токен в файле .env успешно сброшен")
    title_playlist = f"Импортированная музыка от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    report_filename = f"Отчет об импорте за {datetime.now().strftime('%d.%m.%Y %H-%M')}.txt"
    playlist_img = None
    logging.info(f"Авторизировался как {user_info['first_name']} {user_info['last_name']} (id: {user_info['id']})")
    sleep(0.1)
    # Getting Spotify playlist
    if os.getenv("SPOTIFY_MODE", "0"):
        while True:
            spotify_playlist_url = input('\n[!] Вставь сюда ссылку на плейлист в Spotify:\n> ').strip()
            tracklist_response = requests.post('https://spotya.ru/data.php', json={
                "url": f"https://spotya.ru/api.php?playlist={spotify_playlist_url}",
                "type": "playlist"
            })
            tracklist_text = tracklist_response.text.replace('\ufeff', '')
            if len(tracklist_text) != 0:
                break
            logging.warning("Не сумел прочитать треки из плейлиста. У тебя точно открытый плейлист?")
        logging.info(f"Нашел {tracklist_text.count('&#10;') + 1} треков в плейлисте")
        tracklist_content = tracklist_text.replace('&#10;', '\n').strip()
        logging.info("Сохраняю в tracklist.txt...")
        with open("tracklist.txt", "w", encoding="utf-8") as f:
            f.write(tracklist_content)
        playlist_info_response = requests.post('https://spotya.ru/data.php', json={
            "url": f"https://spotya.ru/api.php?playlist={spotify_playlist_url}",
            "type": "poster"
        })
        logging.info("Загружаю метаданные...")
        try:
            playlist_info = json.loads(playlist_info_response.text.replace('\ufeff', ''))
        except json.JSONDecodeError as e:
            logging.warning("Не сумел загрузить метаданные из плейлиста. Пропускаю этот этап...")
        else:
            title_playlist = playlist_info["name"]
            playlist_img = playlist_info["image"]
            logging.info(f"Получил метаданные для плейлиста \"{playlist_info['name']}\"")
    # Open tracklist
    logging.info("Загружаю треклист...")
    with open("tracklist.txt", "r", encoding="utf-8") as f:
        text_lines = f.readlines()
    for text_line in text_lines:
        parsed_row = re.match(r"^([^-—]+)[-—]([^\r\n]+)", text_line)
        if parsed_row is not None:
            tracklist.append((parsed_row.group(1).strip(), parsed_row.group(2).strip()))
    # Search and add tracks
    logging.info(f"Буду искать {len(tracklist)} из {len(text_lines)} треков...")
    ok_tracks = []
    failed_tracks = []
    questionable_tracks = []
    added_count = 0
    chucked_rows = list(chunks(tracklist, 1000))
    playlists = []
    for k, chunk_row in enumerate(chucked_rows, 1):
        logging.info("Создаем плейлист для добавления музыки...")
        if len(chucked_rows) > 1:
            title_playlist = f'[{k}/{len(chucked_rows)}] {title_playlist}'
        playlist_response = vk_session.method("audio.createPlaylist", {
            "owner_id": user_info['id'],
            "title": title_playlist
        })
        playlists.append(f"https://vk.com/audios{user_info['id']}?"
                         f"section=all&z=audio_playlist{user_info['id']}_{playlist_response['id']}")
        if 'id' not in playlist_response:
            raise PermissionError(
                f"VK не позволяет создать плейлист, повторите позже. Доп. информация: {playlist_response}")
        for i, track_row in enumerate(chunk_row, 1):
            artist, title = track_row
            logging.info(f"Ищу трек \"{title}\" от исполнителя {artist} ({i} из {len(tracklist)})...")
            try:
                response = vk_session.method("audio.search", {"q": f"{artist} - {title}", "count": 3})
            except vk_api.VkApiError as e:
                logging.warning(f"Не получить трек, ошибка: \"{e}\". Жду 10 секунд...")
                sleep(10)
                response = vk_session.method("audio.search", {"q": f"{artist} - {title}", "count": 3})
            if 'items' not in response:
                raise PermissionError(
                    f"VK временно заблокировал доступ к API, повторите позже. Доп. информация: {response}")
            if len(response['items']) == 0:
                failed_tracks.append(track_row)
                logging.warning(f"Трек не найден в VK Музыке (исполнитель: {artist}, трек: {title})")
                continue
            full_matched = None
            for item in response['items']:
                if item['artist'].lower() == artist.lower() and title.lower() == item['title'].lower():
                    full_matched = item
                    break
            track_info = None
            if full_matched is not None:
                ok_tracks.append(track_row)
                track_info = full_matched
                logging.info(f"Успешно нашел трек \"{title}\" от исполнителя {artist}")
            else:
                partially_matched = response['items'][0]
                track_info = partially_matched
                questionable_tracks.append(track_row + (partially_matched['artist'], partially_matched['title'],))
                logging.info(f"Нашел похожий трек: \"{artist} - {title}\" → \"{partially_matched['artist']} - "
                             f"{partially_matched['title']}\"")
            logging.info(
                f"Добавляю \"{track_info['artist']} - {track_info['title']}\" (id: {track_info['id']}) в плейлист...")
            try:
                add_to_playlist_response = vk_session.method("audio.addToPlaylist", {
                    "owner_id": user_info['id'],
                    "playlist_id": playlist_response['id'],
                    "audio_ids": f"{track_info['owner_id']}_{track_info['id']}",
                })
            except vk_api.VkApiError as e:
                logging.warning(f"Не получается добавить трек в плейлист, ошибка: \"{e}\". Жду 10 секунд...")
                sleep(10)
                delayed_response = None
                try:
                    delayed_response = vk_session.method("audio.addToPlaylist", {
                        "owner_id": user_info['id'],
                        "playlist_id": playlist_response['id'],
                        "audio_ids": track_info['id'],
                    })
                except vk_api.VkApiError as e:
                    logging.warning(f"Не получается повторно добавить трек в плейлист \"{e}\". Если ошибка повторится, "
                                    f"перезапустите скрипт спустя некоторое время ({delayed_response}).")
            else:
                if len(add_to_playlist_response) == 0:
                    logging.warning(f"Ошибка добавления в плейлист: возвращен пустой ответ, возможно, "
                                    f"у вас нет прав на добавление трека (id: {track_info['id']})")
                    continue
            logging.info(f"Успешно добавил в плейлист: \"{track_info['artist']} - {track_info['title']}\"")
            added_count += 1

    if len(tracklist) != added_count:
        logging.warning(f"Выполнено, но в плейлист добавилось не всё: {added_count} из {len(tracklist)}")
    else:
        logging.info(f"Выполнено успешно! Все найденные треки добавлены")

    logging.info(f"Найдено треков с точными совпадениями: {len(ok_tracks)}")
    logging.info(f"Найдено треков с примерными совпадениями: {len(questionable_tracks)}")
    logging.info(f"Не найдено треков: {len(failed_tracks)}")

    logging.info(f"Всего перенесено треков: {added_count} из {len(text_lines)}")
    with open(fix_relative_path(report_filename), 'w', encoding='utf-8') as f:
        questionable_tracks_str = '\n'.join(f'- "{t[0]} - {t[1]}" → "{t[2]} - {t[3]}"' for t in questionable_tracks)
        ok_tracks_str = '\n'.join(f'- "{t[0]} - {t[1]}"' for t in ok_tracks)
        failed_tracks_str = '\n'.join(f'- "{t[0]} - {t[1]}"' for t in failed_tracks)
        playlists_str = '\n'.join(f'- {p}' for p in playlists)
        f.write(f"""
[ Отчет о перенесенных треках в VK Музыку ]

Дата/время: {datetime.now().strftime('%d.%m.%Y %H:%M')}.
Название плейлиста (если доступно): {title_playlist or '-'}
Изображение плейлиста (если доступно): {playlist_img or '-'}
Найдено треков с точными совпадениями: {len(ok_tracks)}
Найдено треков с примерными совпадениями: {len(questionable_tracks)}
Не найдено треков: {len(failed_tracks)}")


ССЫЛКИ:

{playlists_str or '[x]'}


СПИОК НАЙДЕННЫХ ТРЕКОВ:

{ok_tracks_str or '[x]'}


СПИСОК НАЙДЕННЫХ ПОХОЖИХ ТРЕКОВ:

{questionable_tracks_str or '[x]'}


СПИСОК НЕНАЙДЕННЫХ ТРЕКОВ:

{failed_tracks_str or '[x]'}


- by vk-music-import (Mew Forest)
src: https://github.com/mewforest/vk-music-import
    """.strip())

    logging.info(f"Файл отчета сгенерирован в текущей папке (\"{report_filename}\")")
    if len(playlists) == 1:
        logging.info(f"Скрипт выполнен! Твой плейлист готов: {playlists[0]}")
    else:
        logging.info(f"Скрипт выполнен! Ваши плейлисты готовы: {', '.join(playlists)}")
    if playlist_img is not None:
        logging.info(f"Дополнительно: скачать обложку плейлиста можно здесь: {playlist_img}")
    if platform.system() == "Windows":
        webbrowser.open(fix_relative_path(report_filename))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(e)
    finally:
        input("Нажмите Enter, чтобы завершить работу программы...")

