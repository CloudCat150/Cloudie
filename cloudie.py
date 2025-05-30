import nest_asyncio
nest_asyncio.apply()

import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os

# Intents 설정
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='구름', intents=intents)

# FFMPEG 옵션
FFMPEG_OPTIONS = {
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

@bot.command(name='이')
async def play(ctx, *, search: str):
    if not ctx.voice_client:
        if not ctx.author.voice:
            await ctx.send("어디있는거냥ㅠㅠ")
            return
        await ctx.author.voice.channel.connect()

    async with ctx.typing():
        player = await YTDLSource.from_url(f"ytsearch:{search}", loop=bot.loop, stream=True)
        queue.append(player)
        await ctx.send(f'{player.title}을(를) 재생 목록에 추가했어냥!')

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

async def play_next(ctx):
    if len(queue) > 0:
        player = queue.pop(0)
        ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(ctx)))
        await ctx.send(f'{player.title}을(를) 불러 주겠다냥!')

@bot.command(name='스킵')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("다음 곡으로냥!")

@bot.command(name='아잘가')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("빠빠!")

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f'오류! 오류다냥! {str(error)}')

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)