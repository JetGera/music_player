import asyncio
import time
from math import floor
from types import NoneType

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from player import MP3Player
import uvicorn

app = FastAPI()
player = MP3Player()

started = False
is_playing = False

# Настройка CORS для Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/play_pause")
async def play():
    global is_playing
    player.toggle_pause_music()
    if is_playing:
        is_playing = False
        return {
            "status": "paused",
            "song_length": format_song_length()
        }

    else:
        is_playing = True
        return {
            "status": "playing",
            "song_length": format_song_length()
        }

def format_song_length():
    if player.file_length is not None:
        song_length = round(player.file_length - 0.2)
        minutes = floor(song_length / 60)
        seconds = song_length % 60
        return {f"{minutes:02d}:{seconds:02d}"}

@app.get("/next")
async def next():
    player.next_song()
    return {"song_length": format_song_length()}

@app.get("/prev")
async def prev():
    player.prev_song()
    return {"song_length": format_song_length()}

@app.get("/cover_art")
async def cover_art():
    try:
        base64_data = player.get_cover_art_base64()
        return JSONResponse({
            "status": "success",
            "data": f"data:image/jpeg;base64,{base64_data}"
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.get("/set_volume")
async def set_volume(volume: float):
    player.volume = volume
    player.set_volume(player.volume)
    return {"status": "volume set"}

@app.get("/volume_up")
async def volume_up():
    player.volume_up()
    return {"status": "volume set"}

@app.get("/set_position")
async def set_position(position: float):
    player.seconds = round(position + player.trim_start_silence)
    player.set_position(player.seconds)
    player.ms = 0
    return {"position": position}

@app.get("/volume_down")
async def volume_down():
    player.volume_down()
    return {"status": "volume set"}

@app.post("/refresh_info")
async def refresh_info():
    return {"status": "refresh info"}

@app.get("/start")
async def startt():
    global started
    if not started:
        player.start()
        time.sleep(1)
        started = True
        return {
            "status": "started",
            "song_length": format_song_length()
        }

@app.get("/current")
async def get_current_track():
    return {
        "song_title": player.song_name,
        "song_artist": player.artist_name,
        "song_album": player.song_album,
        "position": player.seconds,
        "is_playing": is_playing,
        "song_length": format_song_length()
    }

song_name = None
@app.get("/sse")
async def sse_endpoint():
    async def event_stream():
        global song_name
        while True:
            await asyncio.sleep(0.2)
            if song_name is None or song_name != player.song_name:
                song_name = player.song_name
                yield f"data: SONG_ENDED, {format_song_length()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    uvicorn.run("main:app", port=9000, reload=True)
