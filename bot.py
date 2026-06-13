# # davey 라이브러리를 추가하여 다시 설치합니다.
# !apt-get -y install ffmpeg
# !pip install discord.py yt-dlp PyNaCl nest_asyncio davey

import discord
from discord.ext import commands
import yt_dlp
import asyncio
import nest_asyncio
import logging  # 💡 로깅 기능 추가

# 💡 코랩 환경에서의 비동기 충돌 방지
nest_asyncio.apply()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='구름', intents=intents)

# ==========================================
# � 로그 초기화 및 설정
# ==========================================
# 📝 이전에 누적된 로그 핸들러를 정리합니다
root_logger = logging.getLogger()
while root_logger.handlers:
    root_logger.removeHandler(root_logger.handlers[0])

discord_logger = logging.getLogger('discord')
while discord_logger.handlers:
    discord_logger.removeHandler(discord_logger.handlers[0])

# 💡 디스코드 로그 레벨을 INFO로 설정 (한 번만)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
# ==========================================

# ==========================================
# 📌 상태 관리
# ==========================================
states = {}

def get_state(guild_id):
    if guild_id not in states:
        states[guild_id] = {
            'queue': [],
            'autoplay': False,
            'last_video_id': None,
            'played_ids': [],
            'is_switching': False
        }
    return states[guild_id]

yt_dlp_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'auto',
    'quiet': True,
    'no_warnings': True,
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(yt_dlp_options)

# ==========================================
# 📌 색상 설정
# ==========================================
# 💡 구름이 봇 전용 색상 (하늘색)
GUROOM_COLOR = discord.Color.from_rgb(170, 219, 255)


# ==========================================
# � 헬퍼 함수 (데이터 파싱 및 임베드 생성)
# ==========================================

def parse_track_info(data):
    """yt_dlp 데이터로부터 트랙 정보 추출"""
    if 'entries' in data and len(data['entries']) > 0:
        track = data['entries'][0]
    else:
        track = data
    
    video_id = track.get('id')
    duration_seconds = track.get('duration', 0)
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    
    return {
        'stream_url': track.get('url'),
        'video_url': track.get('webpage_url', f"https://www.youtube.com/watch?v={video_id}"),
        'title': track.get('title', '제목 없음'),
        'id': video_id,
        'thumbnail': track.get('thumbnail', ''),
        'uploader': track.get('uploader', '작성된 채널 없음'),
        'duration_formatted': f"{minutes}:{seconds:02d}"
    }

def create_guroom_embed(track, title_prefix="", queue_list=None):
    """트랙 정보를 임베드 형식으로 변환"""
    embed_title = title_prefix if title_prefix else "🎶 노래 재생 정보냥! 🐾"
    embed_description = f"**[{track['title']}]({track['video_url']})**\n\n**{track['uploader']}** | `{track['duration_formatted']}`"
    
    embed = discord.Embed(
        title=embed_title,
        description=embed_description,
        color=GUROOM_COLOR
    )
    
    if track['thumbnail']:
        embed.set_thumbnail(url=track['thumbnail'])
        
    if queue_list and len(queue_list) > 0:
        queue_titles = [t['title'] for t in queue_list]
        embed.add_field(name="재생 목록", value="\n".join(queue_titles[:10]), inline=False)
        
    return embed


# ==========================================
# 📌 코어 기능 (오디오 재생 및 큐 관리)
# ==========================================

async def play_audio(ctx, track):
    """트랙을 재생"""
    state = get_state(ctx.guild.id)
    
    # 1️⃣ FFmpeg 오디오 소스 생성
    source = discord.FFmpegPCMAudio(track['stream_url'], **ffmpeg_options)
    
    # 2️⃣ 💡 볼륨을 30%로 조절
    volume_source = discord.PCMVolumeTransformer(source, volume=0.3)
    
    # 3️⃣ 볼륨 조절된 소스로 재생 시작
    ctx.voice_client.play(volume_source, after=lambda e: play_next(ctx))
    
    state['last_video_id'] = track['id']
    if track['id']:
        state['played_ids'].append(track['id'])
        if len(state['played_ids']) > 15:
            state['played_ids'].pop(0)

def play_next(ctx):
    asyncio.run_coroutine_threadsafe(advance_queue(ctx), bot.loop)

async def advance_queue(ctx):
    """대기열에서 다음 곡을 진행"""
    state = get_state(ctx.guild.id)
    if state['is_switching'] or not ctx.voice_client:
        return

    # 📝 대기열에 다음 곡이 있을 때
    if len(state['queue']) > 0:
        next_track = state['queue'].pop(0)
        await play_audio(ctx, next_track)
        
        embed = create_guroom_embed(next_track, title_prefix="🎶 다음 대기열 곡이다냥! 🐾", queue_list=state['queue'])
        await ctx.send(embed=embed)
        return

    # 📝 자동 추천 모드일 때
    if state['autoplay'] and state['last_video_id']:
        try:
            loop = asyncio.get_event_loop()
            last_id = state['last_video_id']
            video_url = f"https://www.youtube.com/watch?v={last_id}"
            info = await loop.run_in_executor(None, lambda: ytdl.extract_info(video_url, download=False))
            related = info.get('related_videos', [])

            if not related:
                state['autoplay'] = False
                await ctx.send("❌ 연관된 추천 노래를 찾지 못했다냥... 추천을 종료한다냥.")
                return

            next_video = next((v for v in related[:7] if v.get('id') not in state['played_ids']), related[0])
            next_id = next_video.get('id')
            
            next_info = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"https://www.youtube.com/watch?v={next_id}", download=False))
            track = parse_track_info(next_info)
            
            await play_audio(ctx, track)
            
            embed = create_guroom_embed(track, title_prefix="✨ 구름이의 추천 곡이다냥! 🐾")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ 추천 곡을 가져오다 에러났다냥: {str(e)}")


# ==========================================
# 📌 명령어 핸들러
# ==========================================

async def handle_skip(ctx, state):
    """스킵 명령어 처리"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        
        if not state['queue'] and not state['autoplay']:
            embed = discord.Embed(title="🛑 재생 종료냥!", description="대기열이 비어 있어 노래를 멈췄다냥!", color=GUROOM_COLOR)
            await ctx.send(embed=embed)
    else:
        await ctx.send("지금은 재생 중인 노래가 없다냥!")

async def handle_stop_autoplay(ctx, state):
    """자동 추천 중지 명령어 처리"""
    state['autoplay'] = False
    state['queue'].clear()
    state['played_ids'].clear()
    if ctx.voice_client:
        ctx.voice_client.stop()
        embed = discord.Embed(title="🛑 자동 추천 종료냥!", description="연속 추천 모드를 끄고 노래를 멈췄다냥!", color=GUROOM_COLOR)
        await ctx.send(embed=embed)
    else:
        await ctx.send("구름이는 지금 통화방에 없다냥!")

async def ensure_voice_connection(ctx):
    """음성 채널 연결 확인 및 연결"""
    if not ctx.voice_client:
        if not ctx.author.voice:
            await ctx.send("어디있는거냥ㅠㅠ 먼저 음성 채널에 들어가달라냥!")
            return False
        await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)
    return True

async def handle_autoplay_start(ctx, state, real_search):
    """자동 추천 재생 시작"""
    state['autoplay'] = True
    msg = await ctx.send(f"🔍 `{real_search}` 검색 및 알고리즘 추천 모드 준비 중이다냥...")
    
    try:
        loop = asyncio.get_event_loop()
        search_data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{real_search}", download=False))
        
        if not search_data.get('entries'):
            await msg.edit(content="❌ 노래 검색에 실패했다냥...")
            return

        video_id = search_data['entries'][0]['id']
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False))
        track = parse_track_info(data)
        
        if ctx.voice_client.is_playing():
            state['is_switching'] = True
            ctx.voice_client.stop()
            await asyncio.sleep(0.3)
            state['is_switching'] = False

        await play_audio(ctx, track)
        
        embed = create_guroom_embed(track, title_prefix="**[연속 추천 재생 시작냥!]** 🐾")
        await msg.edit(content=None, embed=embed)
        
    except Exception as e:
        await msg.edit(content=f"❌ 에러가 발생했다냥: {str(e)}")

async def handle_normal_play(ctx, state, search_text):
    """일반 노래 검색 및 재생"""
    msg = await ctx.send(f"🔍 `{search_text}` 검색 중이다냥...")
    
    try:
        loop = asyncio.get_event_loop()
        search_data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search_text}", download=False))
        
        if not search_data.get('entries'):
            await msg.edit(content="❌ 노래 검색에 실패했다냥...")
            return

        video_id = search_data['entries'][0]['id']
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False))
        track = parse_track_info(data)

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            state['queue'].append(track)
            embed = create_guroom_embed(track, title_prefix="✅ 대기열 추가 완료냥! 🐾", queue_list=state['queue'])
        else:
            await play_audio(ctx, track)
            embed = create_guroom_embed(track, title_prefix="**구름이가 노래를 들려주겠다냥!** 🐾")
        
        await msg.edit(content=None, embed=embed)
        
    except Exception as e:
        await msg.edit(content=f"❌ 노래를 불러오다 에러났다냥: {str(e)}")


# ==========================================
# 📌 이벤트 및 명령어
# ==========================================

@bot.event
async def on_voice_state_update(member, before, after):
    """음성 채널 상태 변경 감지"""
    if member.id == bot.user.id or before.channel is None:
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=before.channel.guild)
    if voice_client and voice_client.channel.id == before.channel.id:
        if len([m for m in before.channel.members if not m.bot]) == 0:
            state = get_state(before.channel.guild.id)
            state['autoplay'] = False
            state['queue'].clear()
            state['played_ids'].clear()
            voice_client.stop()
            await voice_client.disconnect()
            
            for channel in before.channel.guild.text_channels:
                if channel.permissions_for(before.channel.guild.me).send_messages:
                    embed = discord.Embed(title="💤 다들 어디간거냥...", description="방에 아무도 없어서 구름이도 추천을 끄고 가보겠다냥! 🐾", color=GUROOM_COLOR)
                    await channel.send(embed=embed)
                    break

@bot.event
async def on_ready():
    """봇 시작 시 실행"""
    print(f'✅ 구름이 로그인 성공: {bot.user.name}')

@bot.command(name='아', aliases=['이'])
async def play_router(ctx, *, search: str):
    """메인 명령어 라우터"""
    search_text = search.strip()
    state = get_state(ctx.guild.id)

    if search_text == "스킵":
        await handle_skip(ctx, state)
        return
    
    if search_text == "추천중지":
        await handle_stop_autoplay(ctx, state)
        return

    is_connected = await ensure_voice_connection(ctx)
    if not is_connected:
        return

    if search_text.startswith("추천 "):
        real_search = search_text[3:].strip()
        await handle_autoplay_start(ctx, state, real_search)
    else:
        await handle_normal_play(ctx, state, search_text)


# ==========================================
# 📌 봇 설정 및 실행
# ==========================================
# 📝 아래에 봇 토큰을 입력하세요
BOT_TOKEN = "여기에_구름이_봇_토큰을_넣으세요"

bot.run(BOT_TOKEN)