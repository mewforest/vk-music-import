"""
Imports music to VK Music from Track list.

AUTH:
https://oauth.vk.com/oauth/authorize?client_id=6121396&scope=8&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991

"""
import json
import logging
import os
import re
from datetime import datetime
from time import sleep
import requests
import vk_api
from dotenv import load_dotenv


# if os.getenv("BYPASS_CAPTCHA", "0") == "1":
import vk_captchasolver as vc

logging.basicConfig(level=logging.INFO)


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def captcha_handler(captcha):
    captcha_url = captcha.get_url()
    captcha_params = re.match(r"https://api\.vk\.com/captcha\.php\?sid=(\d+)&s=(\d+)", captcha_url)
    if captcha_params is not None and os.getenv("BYPASS_CAPTCHA", "0") == "1":
        logging.info("Появилась капча, пытаюсь автоматически её решить...")
        key = vc.solve(sid=int(captcha_params.group(1)), s=int(captcha_params.group(2)))
        logging.info("Текст на капче обнаружен, отправляю решение...")
    else:
        key = input("\n[!] Чтобы продолжить, введи сюда капчу с картинки {0}:\n> ".format(captcha.get_url())).strip()
    return captcha.try_again(key)


load_dotenv()
logging.info("Авторизуюсь в ВКонтакте...")
if os.getenv("VK_TOKEN") == "":
    logging.warning("Не обнаружен токен VK API в .env файле, запрашиваю авторизацию вручную...")
    token_url = input("""
[!] Вам нужно авторизоваться в ВКонтакте:
1) Перейдите по ссылке ниже и нажмите "Разрешить:
https://oauth.vk.com/oauth/authorize?client_id=6121396&scope=8&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991
2) Скопируйте ссылку из адресной строки браузера и вставьте сюда:
> """.lstrip()).strip()
    token_match = re.match(r'https://oauth.vk.com/blank.html#access_token=([^&]+).+', token_url)
    if token_match is None:
        logging.error("Некорректная ссылка. После того, как вы нажали \"Разрешить\" ссылка должна начинаться с \"https://oauth.vk.com/blank.html#access_token=\"")
        exit()
    os.environ["VK_TOKEN"] = token_match.group(1)
    logging.info(f"На будущее: можно сохранить токен в .env файл, чтобы авторизация сохранилась (переменная VK_TOKEN)")
vk_session = vk_api.VkApi(token=os.getenv("VK_TOKEN"), captcha_handler=captcha_handler)
vk = vk_session.get_api()
tracklist = []
user_info = vk.users.get()[0]
title_playlist = f"Импортированная музыка от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
playlist_img = None
logging.info(f"Авторизировался как {user_info['first_name']} {user_info['last_name']} (id: {user_info['id']})")
sleep(0.1)
if os.getenv("SPOTIFY_MODE", "0"):
    spotify_playlist_url = input('[!] Вставь сюда ссылку на плейлист в Spotify:\n> ').strip()
    tracklist_response = requests.post('https://spotya.ru/data.php', json={
        "url": f"https://spotya.ru/api.php?playlist={spotify_playlist_url}",
        "type": "playlist"
    })
    tracklist_text = tracklist_response.text.replace('\ufeff', '')
    if len(tracklist_text) == 0:
        logging.error("Не сумел прочитать треки из плейлиста. У тебя точно открытый плейлист?")
        exit()
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

logging.info("Загружаю треклист...")
with open("tracklist.txt", "r", encoding="utf-8") as f:
    text_lines = f.readlines()
for text_line in text_lines:
    parsed_row = re.match(r"^([^-—]+)[-—]([^\r\n]+)", text_line)
    if parsed_row is not None:
        tracklist.append((parsed_row.group(1).strip(), parsed_row.group(2).strip()))

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
            questionable_tracks.append(track_row)
            partially_matched = response['items'][0]
            track_info = partially_matched
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
            try:
                add_to_playlist_response = vk_session.method("audio.addToPlaylist", {
                    "owner_id": user_info['id'],
                    "playlist_id": playlist_response['id'],
                    "audio_ids": track_info['id'],
                })
            except vk_api.VkApiError as e:
                logging.warning(f"Не получается повторно добавить трек в плейлист \"{e}\". "
                                f"Если ошибка повторится, перезапустите скрипт спустя некоторое время.")
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
with open('отчет.txt', 'w', encoding='utf-8') as f:
    questionable_tracks_str = '\n'.join(f"{t[0]} - {t[1]}" for t in questionable_tracks)
    ok_tracks_str = '\n'.join(f"{t[0]} - {t[1]}" for t in ok_tracks)
    failed_tracks_str = '\n'.join(f"{t[0]} - {t[1]}" for t in failed_tracks)
    f.write(f"""
Отчет о перенесенных треках в VK Музыку от {datetime.now().strftime('%d.%m.%Y %H:%M')}.

Список найденных треков:
{ok_tracks_str or '[x]'}

Список найденных похожих треков:
{questionable_tracks_str or '[x]'}

Список не найденных треков:
{failed_tracks_str or '[x]'}

- by Mew Forest (https://github.com/mewforest/vk-music-import)
    """)

logging.info(f"Файл отчета сгенерирован в текущей папке (отчет.txt)")
if len(playlists) == 1:
    logging.info(f"Скрипт выполнен! Твой плейлист готов: {playlists[0]}")
else:
    logging.info(f"Скрипт выполнен! Ваши плейлисты готовы: {', '.join(playlists)}")
if playlist_img is not None:
    logging.info(f"Дополнительно: скачать обложку плейлиста можно здесь: {playlist_img}")
