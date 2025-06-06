import nest_asyncio
nest_asyncio.apply()

import discord

# Opus 로딩 시도
if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus('/usr/lib/libopus.so')  # 실제 위치로
    except Exception as e:
        print(f"⚠️ Opus 로딩 실패: {e}")
    else:
        print("✅ Opus 라이브러리 로딩 성공!")

from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os

# Intents 설정
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='구르', intents=intents)

# FFMPEG 옵션
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# YouTube_DL 설정
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.3):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


queue = []

@bot.event
async def on_ready():
    print(f'냥냥! {bot.user} 로그인했어냥!')

first_song = True

@bot.command(name=':종료')
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("다음에 보자냥ㅠㅠ")
    await bot.close()

@bot.command(name=':스킵')
@commands.is_owner()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("다음곡으로냥!")

@bot.command(name=':잘가')
@commands.is_owner()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("빠빠!")

@bot.command(name='밍', aliases=['망'])
async def play(ctx, *, search: str):
    global first_song
    if search.strip().lower() == "스킵":  # 만약 사용자가 '스킵'을 입력하면
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(
              title="**다음곡으로냥!** 🐾",
              color=discord.Color.from_rgb(170, 219, 255)
            )
            if first_song == False:
              queue_titles = [track.title for track in queue]  # 대기열에서 제목 가져오기
              queue_display = "\n".join(queue_titles)
              embed.add_field(name="재생 목록", value=queue_display, inline=False)
            await ctx.send(embed=embed)  # Embed 메시지 전송
        return  # '스킵' 명령 처리 후 함수 종료

    if not ctx.voice_client:
        if not ctx.author.voice:
            await ctx.send("어디있는거냥ㅠㅠ")
            return
        await ctx.author.voice.channel.connect()

    async with ctx.typing():
        if first_song == True:
            embed = discord.Embed(
                title="**구르밍이 노래를 들려주겠다냥!** 🐾",
                color=discord.Color.from_rgb(170, 219, 255)
            )
            await ctx.send(embed=embed)  # Embed 메시지 전송
        player = await YTDLSource.from_url(f"ytsearch:{search}", loop=bot.loop, stream=True)
        queue.append(player)

        # 썸네일, 재생 시간, 작성된 채널 정보를 가져오기
        thumbnail = player.data.get('thumbnail', '썸네일 없음')
        duration_seconds = player.data.get('duration', 0)  # 기본값을 0으로 설정
        channel = player.data.get('uploader', '작성된 채널 없음')

        # 분:초 형식으로 변환
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        duration_formatted = f"{minutes}:{seconds:02d}"

        # 현재 재생 중인 곡 정보
        current_track = player.title

        # 대기열의 곡 제목 목록
        queue_titles = [track.title for track in queue]  # 대기열에서 제목 가져오기
        queue_display = "\n".join(queue_titles) if queue_titles else None  # 대기열이 비어있으면 None

        # Embed 객체 생성
        embed = discord.Embed(
            title=current_track,  # 현재 곡 제목을 임베드 제목으로 설정
            description=f"**{channel}** | `{duration_formatted}`",
            color=discord.Color.from_rgb(0, 120, 255)
        )
        embed.set_thumbnail(url=thumbnail)  # 썸네일 추가

        if first_song == False:
            embed.add_field(name="재생 목록", value=queue_display, inline=False)  # 대기열 추가
        else:
            first_song = False

        embed.url = player.url  # 비디오 URL 추가 (클릭 시 이동)
        await ctx.send(embed=embed)  # Embed 메시지 전송

    if not ctx.voice_client.is_playing():
        await play_next(ctx)


async def play_next(ctx):
    global first_song
    if len(queue) > 0:
        player = queue.pop(0)
        ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(ctx)))
    else:
        first_song=True
        embed = discord.Embed(
            title="**재생 목록이 비어있어냥ㅠㅠ**",
            color=discord.Color.from_rgb(170, 219, 255)
        )
        await ctx.send(embed=embed)  # Embed 메시지 전송  # 대기열이 비어있을 때 메시지 전송


@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f'오류! 오류다냥! {str(error)}')

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("환경변수 DISCORD_TOKEN이 설정되지 않았습니다!")
    else:
        bot.run(TOKEN)
