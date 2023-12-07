# vk-music-import

Программа для переноса плейлистов из Spotify и текстовых треклистов в VK Музыку.

![Untitled Diagram drawio-3](https://user-images.githubusercontent.com/15357833/161931217-9c374cf8-749a-4966-b3f5-4e8a85194572.png)

Преимущества:

- **Позволяет быстро импортировать плейлисты из Spotify в VK Музыку**
- Импортирует даже неточные по названию треки
- Имеет доступ только к аудиозаписям, данные никуда не "утекают"
- Поддерживает большие плейлисты (более 1000 треков)
- Позволяет импортировать также обычные текстовые списки треков в VK Музыку
- Умеет обходить капчу

---

## Как запустить? (для обычных пользователей)

Инструкция по использованию на Windows:

- Скачайте и распакуйте 
  архив ([vk-music-import-vX.X_win32.zip](https://github.com/mewforest/vk-music-import/releases))
  в любую папку
- Запустите исполняемый файл и следуйте инструкциям:

![2022-04-08_12h22_59](https://user-images.githubusercontent.com/15357833/167272239-55fc04eb-27c1-40bc-abe9-596390c64459.png)

**Более подробная инструкция на
DTF:** [Переносим плейлисты из Spotify в VK Музыку (подробное руководство)](https://dtf.ru/u/292194-mew-forest/1152260-perenosim-pleylisty-iz-spotify-v-vk-muzyku-podrobnoe-rukovodstvo)
.

## Как запустить? (для продвинутых пользователей)

1. Убедитесь, что у вас установлен Python 3.8 (или 3.9).
2. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```
3. Запустите скрипт и следуйте инструкциям:
   ```
   python vk-music-import.py
   ```
4. После переноса треков, скрипт сгенерирует отчет и выведет ссылку на плейлисты с импортированными треками.

## Перенос плейлистов из Apple Music

1. В приложении Музыка на Mac выберите плейлист в боковом меню, затем выберите «Файл» > «Медиатека» > «Экспортировать плейлист». Выберите формат «Простой Текст».
2. В файле настроек (`config.env`, лежит в папке с программой) с помощью блокнота выключите режим spotify: `SPOTIFY_MODE="0"`
3. Аналогично предыдущему шагу включите режим Apple Music: `APPLE_MODE="1"`
4. Запустите скрипт указав в аргументах файл с экспортированным плейлистом (удобно заранее положить файл в директорию со скриптом):
  ```
  python vk-music-import.py example.txt
  ```


## Описание настроек

| Параметр                | Описание                                                                                                   | Значение по умолчанию |
|-------------------------|------------------------------------------------------------------------------------------------------------|-----------------------|
| `VK_TOKEN`              | Токен для доступа к VK API**                                                                               | `""`                  |
| `BYPASS_CAPTCHA`        | Включить обход капчи автоматически (если отключить, будет предложено вводить капчу каждый раз вручную)     | `1`                   |
| `SPOTIFY_MODE`          | Включить режим импорта из Spotify                                                                          | `1`                   |
| `APPLE_MODE`            | Включить режим импорта из Apple Music                                                                      | `0`                   |
| `VK_LINKS_MODE`         | Включить режим импорта из списка ссылок на треки во Вконтакте (ссылки должны быть в файле `tracklist.txt`) | `0`                   |
| `REVERSE`               | Добавлять треки в обратном порядке (от новых к старым)                                                     | `1`                   |
| `STRICT_SEARCH`         | Искать только точные совпадения по исполнителю                                                             | `0`                   |
| `ADD_TO_LIBRARY`        | Добавлять треки в мои аудиозаписи                                                                          | `0`                   |
| `TIMEOUT_AFTER_ERROR`   | Задержка после ошибки (в секундах)*                                                                        | `10`                  |
| `TIMEOUT_AFTER_CAPTCHA` | Задержка после капчи (в секундах)*                                                                         | `30`                  |
| `TIMEOUT_AFTER_SUCCESS` | Задержка после успешного импорта (в секундах)*                                                             | `1`                   |

*Только для beta-версии.
** Ссылка для получения токена [здесь](https://oauth.vk.com/oauth/authorize?client_id=6121396&scope=audio,offline&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1&slogin_h=23a7bd142d757e24f9.93b0910a902d50e507&__q_hash=fed6a6c326a5673ad33facaf442b3991
).

## Как перенести музыку из других сервисов?

Чтобы перенести музыку из сторонних сервисов (YouTube, Apple Music, Яндекс Музыка и т.д.), вам необходимо будет экспортировать оттуда треклист (текстовой файл с названиями треков). Это можно сделать с помощью стороннего сервиса [TuneMyMusic](https://www.tunemymusic.com/ru/):

1. Перейдите на сайт [TuneMyMusic](https://www.tunemymusic.com/ru/) и нажмите кнопку «Давайте приступим».
2. Выберите сервис, из которого вы хотите перенести музыку, и авторизуйтесь в нем.
3. Выберите плейлист для переноса, нажав кнопку «Загрузить из вашей учетной записи».
4. На странице «Выберите целевую платформу» нажмите кнопку «Файл» и скачайте его в формате .txt.
5. Нажмите «Начать перенос музыки».
6. Сохраните файл на свой компьютер, а затем переместите его в папку с данной программой и переименуйте в `tracklist.txt`.
7. В файле настроек (`config.env`, лежит в папке с программой) с помощью блокнота выключите режим spotify: `SPOTIFY_MODE="0"`
8. Готово, запускайте скрипт!

*Инструкция частично заимствована [отсюда](https://zvuk.com/lp/howto)*.

### Альтернативы

- Яндекс Музыка: [расширение для Google Chrome](https://chrome.google.com/webstore/detail/yamutools-%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D1%84%D1%83%D0%BD%D0%BA%D1%86%D0%B8%D0%B8-%D0%B4/dgjneghdfaeajjemeklgmbojeeplehah) (могут быть неточности из-за формата экспорта [#5](https://github.com/mewforest/vk-music-import/issues/5)).
- YouTube Музыка: сервис [yt.spotya.ru](https://yt.spotya.ru/).
- Apple Music, Deezer, Amazon и другие: вместо [TuneMyMusic](https://www.tunemymusic.com/ru/) можете воспользоваться конкурентом - [Soundiiz](https://soundiiz.com/).

## Как создать плейлист из ссылок на треки во Вконтакте

На любой трек во ВКонтакте можно получить прямую ссылку, если вы создадите список таких ссылок, то их также можно будет добавить в плейлист
с помощью данной утилиты. Это может быть полезно, если вы создаете плейлисты в стороннем приложении для прослушивания музыки,
например, в AIMP с использованием плагина [VK Plugin](https://www.aimp.ru/forum/index.php?topic=64170.0).

Чтобы перейти в режим импорта из списка ссылок, в `config.env` отключите режим Spotify: `SPOTIFY_MODE="0"` и включите
режим `VK_LINKS_MODE="1"`. Теперь скрипт будет добавлять треки по ссылкам из файла `tracklist.txt` минуя поиск. Вот как
должен выглядеть этот список:

```
https://vk.com/audio570484580_456249918_30a6c863d7cb56d834
https://vk.com/audio570484580_456245588_3c170a3340106a374a
https://vk.com/audio570484580_456245614_4bb21fb36173e3c61b
https://vk.com/audio570484580_456254608_7784e1bddd07c3289f
```

### Как получить список ссылок на музыку в AIMP-е

1. Установить [VK Plugin](https://www.aimp.ru/forum/index.php?topic=64170.0) в AIMP
2. Правой кнопкой мыши по списку треков "Экспорт плейлиста"
3. Появится окошко с настройками экспорта, в поле "Форматная строка" написать `%Link` и кликнуть "ОК"
4. Готово! Треклист можно сохранять как `tracklist.txt`

## Настройки

### Добавление в мои аудиозаписи

По-умолчанию треки переносятся в плейлист без добавления в раздел "мои аудиозаписи". Чтобы включить добавление музыки в свою
медиатеку ВКонтакте, в `config.env` включите соответственный пункт: `ADD_TO_LIBRARY="1"`. 

**Используйте с осторожностью:** ВКонтакте не проверяет трек на наличие в аудиозаписях, так что при импорте возможны дубликаты.

### Импорт музыки из треклиста

По-умолчанию включен импорт треков из плейлиста Spotify, чтобы перейти в режим импорта из треклиста, в `config.env`
отключите режим Spotify: `SPOTIFY_MODE="0"`. Теперь скрипт будет искать треки из файла `tracklist.txt` (его нужно
создать самостоятельно в папке со скриптом), который должен содержать список треков, разделенных переносом, например:

```
Khalid - Better
Billie Eilish - i love you
```

> Если дефисы не проставлены, скрипт проставит их автоматически после первого слова.

### Треки в обратном порядке

По-умолчанию все плейлисты добавляются в обратном порядке (от новых к старым). Чтобы это отключить, в `config.env`
отключите режим обратного порядка: `REVERSE="0"`.

### Строгий поиск

По-умолчанию скрипт ищет неточные совпадения для треков и также их переносит, побочный эффект этого: в вашу медиатеку
могут попасть ремиксы и bassboosted-версии. Чтобы разрешить перенос только точных совпадений по исполнителю,
в `config.env` включите строгий режим: `STRICT_SEARCH="1"`.

## Возможные проблемы и их решения

### Обход капчи не работает на macOS на M1

Это происходит из-за проблем с установкой onnx-runtime.

- **Решение 1**: запустите скрипт через Python x64 с помощью Rosetta.
- **Решение 2**: отключить распознавание капчи и вводить ответы вручную. Для этого закомментируйте строчку
  импорта `import onnxruntime as rt` в `vk-music-import.py` (можете удалить строчки, где эта библиотека используется) и выключите распознавание капчи в
  файле `config.env`: `BYPASS_CAPTCHA="0"`.


### Не работает обход капчи

- Увеличьте значение `CAPTCHA_TIMEOUT` в `config.env` (по-умолчанию 30 секунд)*.
- Отключите автоматический обход капчи в `config.env`: `BYPASS_CAPTCHA="0"` и вводите ответы вручную.
- Повторите попытку через некоторое время, возможно ВКонтакте временно заблокировал ваш аккаунт.

### Слетела конфигурация по умолчанию

Все настройки хранятся в файле `config.env`, если он был удален или повредился, то его можно восстановить вручную, вставив настройки по умолчанию:

```dotenv 
VK_TOKEN=""
BYPASS_CAPTCHA="1"
SPOTIFY_MODE="1"
APPLE_MODE="0"
VK_LINKS_MODE="0"
REVERSE="1"
STRICT_SEARCH="0"
ADD_TO_LIBRARY="0"
TIMEOUT_AFTER_ERROR="10"
TIMEOUT_AFTER_CAPTCHA="30"
TIMEOUT_AFTER_SUCCESS="1"
```


## Компиляция программы

Вы можете скомпилировать данную утилиту самостоятельно, в том числе для своей операционной системы (в инструкции пример
для Windows).

- Создайте виртуальное окружение и установите зависимости и Pyinstaller:
  ```shell
  python -m virtualenv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  pip install pyinstaller
  ```
- Запустите компиляцию (да, это больно):
  ```shell
  pyinstaller --onefile --icon=app.ico --add-binary="venv\Lib\site-packages\onnxruntime\capi\onnxruntime_providers_shared.dll;.\onnxruntime\capi" .\vk-music-import.py
  ```
- Скопируйте в папку `dist` файл с моделями капчи (`models`) и файл конфигурации (`config.env`):
  ```shell
  cp -r .\models\ .\dist\models
  cp .\config.env .\dist
  ```

## Поддержка пользователей

- **[Оставить запрос на фичу или сообщить о баге](https://github.com/mewforest/vk-music-import/issues/new/choose)**
- [Поблагодарить разработчика](https://mewforest.github.io/donate/)

## Полезный материал

- [Айти заметки](https://t.me/mewnotes) - телеграм-канал автора сервиса.
- [Spotya](https://spotya.ru/) - сервис для переноса музыки из Spotify в Яндекс Музыку, некоторые метаданные о
  плейлистах я собираю с его API.
- [vkCaptchaBreaker](https://github.com/Defasium/vkCaptchaBreaker/) - модель для решения капчи ВК взята из данного
  репозитория
- [VK API Reference](https://vodka2.github.io/vk-audio-token/) - описание методов VK API для доступа к аудиозаписям.

## Альтернативные решения

- [Официальный сервис "Перенос Музыки"](https://vk.com/app8116845) - Умеет переносить пользовательскую библиотеку из резервных копий Spotify

## Условия пользования

Автор не несет ответственности за любые действия, которые предпринимаете с данным ПО, вы делаете всё на свой страх и
риск. Учитывайте, что данный метод импортирования музыки не является официальным, но банов за его использования пока не
было.
