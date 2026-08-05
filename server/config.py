import os
import discord

def load_token():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN이 설정되지 않았습니다!")
    return token

# 💡 구름이 봇 전용 색상 (하늘색)
GUROOM_COLOR = discord.Color.from_rgb(170, 219, 255)

# FFMPEG 및 YTDL 설정
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YT_DLP_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'auto',
    'quiet': True,
    'no_warnings': True,
    'source_address': '0.0.0.0'
}

# 명령어 상수 그룹
SKIP_COMMANDS = {
    '스킵', '다음', '넘기기', '다음곡', '다음노래', '다음곡재생', '다음노래재생'
}
CLEAR_COMMANDS = {'청소'}
HELP_COMMANDS = {'핼프', '헬프', 'help', '도움'}
