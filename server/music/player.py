from discord.ext import commands
from server.music.ytdl_source import YTDLSource
import discord
import asyncio

queue = []
first_song = True

async def play(ctx, search,bot):
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
        await play_next(ctx,bot)

async def play_next(ctx,bot):
    global first_song
    try:
        player = queue.pop(0)
    except IndexError:
        first_song = True
        embed = discord.Embed(
            title="**재생 목록이 비어있어냥ㅠㅠ**",
            color=discord.Color.from_rgb(170, 219, 255)
        )
        await ctx.send(embed=embed)
        return
    ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(ctx)))
