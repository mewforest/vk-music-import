if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
  $arguments = "& '" +$myinvocation.mycommand.definition + "'"
  Start-Process powershell -Verb runAs -ArgumentList $arguments
  Break
}
$text = @"
             *     ,MMM8&&&.            *
                  MMMM88&&&&&    .
                 MMMM88&&&&&&&
     *           MMM88&&&&&&&&
                 MMM88&&&&&&&&
                 'MMM88&&&&&&'
                   'MMM8&&&'      *
          |\___/|
          )     (             .              '
         =\     /=
           )===(       *
          /     \         ЖДИТЕ...)
          |     |
         /       \
         \       /
  _/\_/\_/\__  _/_/\_/\_/\_/\_/\_/\_/\_/\_/\_
  |  |  |  |( (  |  |  |  |  |  |  |  |  |  |
  |  |  |  | ) ) |  |  |  |  |  |  |  |  |  |
  |  |  |  |(_(  |  |  |  |  |  |  |  |  |  |
  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

"@

Write-Output $text

$url = "https://www.python.org/ftp/python/3.9.2/python-3.9.2-embed-amd64.zip"
$installPath = "C:/tmp/vk-music-import"
$pythonPath = "$installPath/bin"
$installer = "$installPath/python-3.9.2-embed-amd64.zip"

Write-Host "[~] Подождите, пока установятся зависимости (тут будет много букав, ничего не бойтесь и окно не закрывайте!)..."
Write-Host "[~] Проверка установленных зависимостей..."

if (Test-Path "$pythonPath/python.exe")
{
    Write-Host "[v] Отлично, Python 3.9 уже установлен локально"
}
else
{
    if (Test-Path $installer)
    {
        Write-Host "[~] Пропускаю скачивание установочного файла..."
    }
    else
    {
        Write-Host "[~] Установка зависимостей для скрипта будет происходить в папку: $pythonPath..."
        Write-Host "[~] Выполняю скачивание установочного файла Python 3.9..."
        New-Item -ItemType Directory -Force -Path "$installPath"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $installer
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "$installPath/get-pip.py"
    }
    Write-Host "[~] Устанавливаю локально Python 3.9..."
    Expand-Archive -LiteralPath $installer -DestinationPath "$pythonPath"
    Remove-Item $pythonPath/python39._pth
    & $pythonPath/python.exe $installPath/get-pip.py
    Write-Host "[v] Отлично, Python 3.9 установлен в ${pythonPath}."
}

# Write-Host "[~] Проверяю зависимости библиотек в Python..."
# $freezeOutput = (& $pythonPath/Scripts/pip.exe freeze)
# $dependencies = @("python-dotenv==0.20.0", "vk-api==11.9.7", "vk-captchasolver==1.0.0")
# $isDepsInstalled = $true
# For ($i = 0; $i -lt $dependencies.Length; $i++) {
#     $dep = $dependencies[$i]
#     if ($freezeOutput -NotLike "*$dep*")
#     {
#         $isDepsInstalled = $false
#         Write-Host "[~] Жду установку: $dep..."
#     }
# }
# if (-Not $isDepsInstalled)
# {
#     Write-Host "[~] Установка необходимых библиотек в Python..."
#     & $pythonPath/Scripts/pip.exe install --user -r $PSScriptRoot/requirements.txt
# }

Write-Host "[~] Установка необходимых библиотек в Python..."
& $pythonPath/Scripts/pip.exe install --user -r $PSScriptRoot/requirements.txt

Write-Host "[v] Библиотеки установлены, запускаем скрипт..."
#Clear-Host

$successCats = @"
            *     ,MMM8&&&.            *
                  MMMM88&&&&&    .
                 MMMM88&&&&&&&
     *           MM Работает &&
                 MMM88&&&&&&&&
                 'MMM88&&&&&&'
                   'MMM8&&&'      *
          |\___/|     /\___/\
          )     (     )    ~( .              '
         =\     /=   =\~    /=
           )===(       ) ~ (     Установка
          /     \     /     \    завершена :)
          |     |     ) ~   (
         /       \   /     ~ \
         \       /   \~     ~/
  ___/\_/\__  _/_/\_/\__~__/_/\_/\_/\_/\_/\_
  |  |  |  |( (  |  |  | ))  |  |  |  |  |  |
  |  |  |  | ) ) |  |  |//|  |  |  |  |  |  |
  |  |  |  |(_(  |  |  (( |  |  |  |  |  |  |
  |  |  |  |  |  |  |  |\)|  |  |  |  |  |  |
  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
"@

Write-Host $successCats
Set-Location -Path $PSScriptRoot

$ok = $true
try {
    & $pythonPath/python.exe vk-music-import.py
} catch {
    $ok = $false
}

if ($ok) {
    Write-Host '[v] Скрипт завершил свою работу';
} else {
    Write-Host '[x] Скрипт завершил свою работу с ошибками';
}
Write-Host -NoNewLine '[!] Нажмите Enter, чтобы закрыть...';
pause




