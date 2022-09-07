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

## Как перенести музыку из других сервисов?

Чтобы перенести музыку из сторонних сервисов (YouTube, Apple Music, Яндекс Музыка и т.д.), вам необходимо будет экспортировать из них треклист (текстовой файл с названиями треков). Это можно сделать с помощью стороннего сервиса [TuneMyMusic](https://www.tunemymusic.com/ru/):

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

- Яндекс Музыка: [расширение для Google Chrome](https://chrome.google.com/webstore/detail/yamutools-%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D1%84%D1%83%D0%BD%D0%BA%D1%86%D0%B8%D0%B8-%D0%B4/dgjneghdfaeajjemeklgmbojeeplehah).
- YouTube Музыка: сервис [yt.spotya.ru](https://yt.spotya.ru/).
- Apple Music, Deezer, Amazon и другие: вместо [TuneMyMusic](https://www.tunemymusic.com/ru/) можете воспользоваться конкурентом - [Soundiiz](https://soundiiz.com/).

## Настройки

### Добавление в мои аудиозаписи

По-умолчанию треки переносятся без добавления в раздел "мои аудиозаписи". Чтобы включить добавление музыки в свою
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
  импорта `import onnxruntime as rt` в `vk-music-import.py` и выключите распознавание капчи в
  файле `config.env`: `BYPASS_CAPTCHA="0"`.

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
- Запустите компиляцию:
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

## Условия пользования

Автор не несет ответственности за любые действия, которые предпринимаете с данным ПО, вы делаете всё на свой страх и
риск. Учитывайте, что данный метод импортирования музыки не является официальным, но банов за его использования пока не
было.
