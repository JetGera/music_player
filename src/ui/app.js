const baseUrl = "http://localhost:9000";

let first_launch = false
let song_length = "00:00"
let is_playing = false


const UPDATE_INTERVAL = 50;



let currentTimeInSeconds = 0;
let timerId = null;
let isSeeking = false;

const song_current_time_text = document.getElementById('song-current-time')
const song_length_text = document.getElementById('song-length')

const music_position = document.getElementById('music-position')
music_position.step = "0.1";

const play_button = document.getElementById('play-button');
const next_button = document.getElementById('next-button');
const prev_button = document.getElementById('prev-button');

const cover_art = document.getElementById("cover-art")
const background = document.getElementById("background")

const song_title = document.getElementById('song-title');
const song_artist = document.getElementById('song-artist');
const song_album = document.getElementById('song-album');
const album_hyphen = document.getElementById('album-hyphen');

const volume_slider = document.getElementById("volume-slider")
const playImg = document.getElementById('play-img');


const eventSource = new EventSource("http://localhost:9000/sse");

function timeToSeconds(timeStr) {
    const time = Array.isArray(timeStr) ? timeStr[0] : timeStr;
    const [minutes, seconds] = time.split(':').map(Number);
    return (minutes * 60) + seconds;
}


function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Таймер для обновления позиции
function startTimer() {
    if (timerId) clearInterval(timerId);

    // Сохраняем время начала воспроизведения
    const startTime = Date.now() - currentTimeInSeconds * 1000;

    timerId = setInterval(() => {
        if (is_playing && !isSeeking) {
            // Рассчитываем текущее время с высокой точностью
            currentTimeInSeconds = (Date.now() - startTime) / 1000;

            // Обновляем ползунок с дробным значением
            music_position.value = currentTimeInSeconds.toFixed(1);

            // Обновляем отображаемое время (целые секунды)
            song_current_time_text.textContent = formatTime(Math.floor(currentTimeInSeconds));

            // Проверка окончания трека
            if (currentTimeInSeconds >= timeToSeconds(song_length)) {
                clearInterval(timerId);
                timerId = null;
            }
        }
    }, UPDATE_INTERVAL);
}


function stopTimer() {
    clearInterval(timerId);
    timerId = null;
}

music_position.addEventListener('input', function() {
    isSeeking = true;
    currentTimeInSeconds = parseFloat(this.value);
    song_current_time_text.textContent = formatTime(Math.floor(currentTimeInSeconds));
});

music_position.addEventListener('change', function() {
    isSeeking = false;
    currentTimeInSeconds = parseFloat(this.value);
    sendCommand(`set_position?position=${Math.floor(currentTimeInSeconds)}`);
});



eventSource.onmessage = (event) => {
    if (event.data.includes("SONG_ENDED")) {
        stopTimer();
        currentTimeInSeconds = 0;
        music_position.value = 0;
        song_current_time_text.textContent = "00:00";
        loadCoverAndSetBackgroundColor();
        updateCurrent();
        song_length = event.data.split(" ")[1].split("'")[1].split("'")[0]
        song_length_text.textContent = song_length
        music_position.max = timeToSeconds(song_length);
    }
};



const sendCommand = async (endpoint) => {
    try {
        const response = await fetch(`${baseUrl}/${endpoint}`);
        const data = await response.json();
        // console.log(data);
        if ( endpoint === "play_pause") {
            await updateCurrent();
            if (song_length === "00:00") {
                song_length = data.song_length[0]
                song_length_text.textContent = song_length;
                music_position.max = timeToSeconds(song_length);
            }

        }

        if (endpoint === "next" || endpoint === "prev") {
            stopTimer();
            currentTimeInSeconds = 0;
            music_position.value = 0;
            song_current_time_text.textContent = "00:00";
            song_length = data.song_length[0]
            song_length_text.textContent = song_length;
            music_position.max = timeToSeconds(song_length);
        }
        if ( endpoint.includes("set_volume")) {
            // console.log(endpoint.slice(11))
        }
    } catch (error) {
        console.error("Ошибка:", error);
    }
};




const updatePlayButtonIcon = async () => {
    const response = await fetch(`${baseUrl}/current`);
    const data = await response.json();
    // console.log(data)
    if (data.is_playing === true) {
        playImg.src = "./icons/pause.png"
        is_playing = true
        startTimer();
    }
    else {
        playImg.src = "./icons/play.png"
        is_playing = false
        stopTimer();
    }

    if (first_launch === false) {
        await loadCoverAndSetBackgroundColor();
        first_launch = true
    }
};

const updateSongInfo = async () => {
    const response = await fetch(`${baseUrl}/current`);
    const data = await response.json();
    // console.log(data)

    song_title.textContent = data.song_title;
    song_artist.textContent = data.song_artist;
    song_album.textContent = data.song_album;
    album_hyphen.style.display = song_album !== "none"
        ? "none"
        : "block"
    song_album.style.display = album_hyphen.style.display
};

volume_slider.addEventListener('change', () => sendCommand(`set_volume?volume=${volume_slider.value}`))
play_button.addEventListener('click', () => sendCommand("play_pause"));
next_button.addEventListener('click', () => sendCommand("next"));
prev_button.addEventListener('click', () => sendCommand("prev"));

const updateCurrent = async ()  => {
    await updatePlayButtonIcon();
    await updateSongInfo();
}

function getAverageRGB(imgEl, borderThreshold = 220, borderWidth = 10) {
    var blockSize = 5,
        defaultRGB = {r:0,g:0,b:0},
        canvas = document.createElement('canvas'),
        context = canvas.getContext && canvas.getContext('2d'),
        data, width, height,
        i = -4,
        length,
        rgb = {r:0,g:0,b:0},
        count = 0;

    if (!context) {
        return defaultRGB;
    }

    height = canvas.height = imgEl.naturalHeight || imgEl.offsetHeight || imgEl.height;
    width = canvas.width = imgEl.naturalWidth || imgEl.offsetWidth || imgEl.width;

    if (width === 0 || height === 0) {
        return defaultRGB;
    }

    context.drawImage(imgEl, 0, 0);

    try {
        data = context.getImageData(0, 0, width, height);
    } catch(e) {
        return defaultRGB;
    }

    var dataArr = data.data;
    var borderSum = {r:0, g:0, b:0};
    var borderPixels = 0;
    var borderAvg = {r:0, g:0, b:0};
    var isBorderUniform = true;

    // Собираем данные с границы
    for (var y = 0; y < height; y++) {
        for (var x = 0; x < width; x++) {
            // Проверяем не только крайние пиксели, а полосу шириной borderWidth
            if (y < borderWidth || y >= height - borderWidth ||
                x < borderWidth || x >= width - borderWidth) {
                var idx = (y * width + x) * 4;
                borderSum.r += dataArr[idx];
                borderSum.g += dataArr[idx+1];
                borderSum.b += dataArr[idx+2];
                borderPixels++;
            }
        }
    }

    // Рассчитываем среднее для границы
    if (borderPixels > 0) {
        borderAvg.r = Math.round(borderSum.r / borderPixels);
        borderAvg.g = Math.round(borderSum.g / borderPixels);
        borderAvg.b = Math.round(borderSum.b / borderPixels);

        // Проверяем однородность границы
        for (var y = 0; y < height; y++) {
            for (var x = 0; x < width; x++) {
                if (y === 0 || y === height-1 || x === 0 || x === width-1) {
                    var idx = (y * width + x) * 4;
                    var dr = Math.abs(dataArr[idx] - borderAvg.r);
                    var dg = Math.abs(dataArr[idx+1] - borderAvg.g);
                    var db = Math.abs(dataArr[idx+2] - borderAvg.b);

                    if (dr > borderThreshold || dg > borderThreshold || db > borderThreshold) {
                        isBorderUniform = false;
                        break;
                    }
                }
            }
            if (!isBorderUniform) break;
        }

        // Если граница однородна - возвращаем средний цвет границы
        if (isBorderUniform) {
            return borderAvg;
        }
    }

    // Если граница не однородна - считаем среднее по всему изображению
    length = dataArr.length;
    while ((i += blockSize * 4) < length) {
        ++count;
        rgb.r += dataArr[i];
        rgb.g += dataArr[i+1];
        rgb.b += dataArr[i+2];
    }

    rgb.r = ~~(rgb.r / count);
    rgb.g = ~~(rgb.g / count);
    rgb.b = ~~(rgb.b / count);

    return rgb;
}

async function loadCoverArt() {
  try {
    const coverElement = document.getElementById('cover-art');
    if (!coverElement) {
      console.error('Error: Element with id "cover_art" not found');
      return;
    }

    const response = await fetch(`http://localhost:9000/cover_art`);
    const data = await response.json();

    if (data.status === "success") {
      coverElement.src = data.data;
      coverElement.style.display = 'block'; // Показываем после загрузки

      return data.data; // Возвращаем данные для возможного дальнейшего использования
    } else {
      console.error('Server error:', data.message);
    }
  } catch (error) {
    console.error("Error loading cover art:", error);
    throw error; // Пробрасываем ошибку дальше при необходимости
  }
}

async function loadCoverAndSetBackgroundColor() {
    await loadCoverArt()
    r = getAverageRGB(cover_art).r
    g = getAverageRGB(cover_art).g
    b = getAverageRGB(cover_art).b

    background.style.background = "rgb(" + r + "," + g + "," + b + ")";
}


music_position.value = 0;
song_current_time_text.textContent = "00:00";

fetch(`${baseUrl}/start`)
