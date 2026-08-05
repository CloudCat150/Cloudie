import asyncio
import discord
import yt_dlp
import re
from server.config import GUROOM_COLOR, FFMPEG_OPTIONS, YT_DLP_OPTIONS

states = {}

def get_state(guild_id):
    if guild_id not in states:
        states[guild_id] = {
            'queue': []
        }
    return states[guild_id]

ytdl = yt_dlp.YoutubeDL(YT_DLP_OPTIONS)

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

def split_bulk_tracks(text):
    """true 단위로 텍스트를 분리하여 곡 그룹 리스트 반환"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    tracks = []
    current = []

    for line in lines:
        if line.lower() == 'true':
            if current:
                tracks.append(current)
            current = []
        else:
            current.append(line)

    if current:
        tracks.append(current)

    return tracks

def build_search_query_from_group(group):
    """곡 그룹에서 검색어를 구성"""
    cleaned = [line for line in group if not re.match(r'^\d{1,2}:\d{2}$', line)]
    return ' '.join(cleaned).strip()

async def play_audio(ctx, track):
    """트랙을 재생"""
    source = discord.FFmpegPCMAudio(track['stream_url'], **FFMPEG_OPTIONS)
    volume_source = discord.PCMVolumeTransformer(source, volume=0.3)
    ctx.voice_client.play(volume_source, after=lambda e: play_next(ctx))

def play_next(ctx):
    asyncio.run_coroutine_threadsafe(advance_queue(ctx), ctx.bot.loop)

async def advance_queue(ctx):
    """대기열에서 다음 곡을 진행"""
    state = get_state(ctx.guild.id)
    if not ctx.voice_client:
        return

    # 대기열에 다음 곡이 있을 때
    if len(state['queue']) > 0:
        next_track = state['queue'].pop(0)
        await play_audio(ctx, next_track)
        
        embed = create_guroom_embed(next_track, title_prefix="🎶 다음 대기열 곡이다냥! 🐾", queue_list=state['queue'])
        await ctx.send(embed=embed)
        return

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

async def handle_bulk_play(ctx, state, bulk_text):
    """true 단위 텍스트를 곡으로 검색하고 재생 목록에 추가"""
    groups = split_bulk_tracks(bulk_text)
    if not groups:
        await ctx.send("❌ 재생 목록을 해석할 수 없다냥... 다시 입력해줄래냥?")
        return

    queries = [build_search_query_from_group(group) for group in groups]
    queries = [q for q in queries if q]
    if not queries:
        await ctx.send("❌ 검색할 곡 제목을 찾을 수 없다냥...")
        return

    msg = await ctx.send("🔍 재생목록을 검색 중이다냥... 잠시만 기다려달라냥!")
    loop = asyncio.get_event_loop()
    
    # 1️⃣ 첫 곡만 먼저 빠르게 검색 및 재생
    first_track = None
    
    try:
        search_data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{queries[0]}", download=False))
        if search_data and search_data.get('entries'):
            video_id = search_data['entries'][0]['id']
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False))
            first_track = parse_track_info(data)
            
            # 대기열이 비어있고 재생 중이 아니면 바로 재생
            if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused() and not state['queue']:
                await play_audio(ctx, first_track)
                embed_title = "**구름이가 재생을 시작했냥!** 🐾"
            else:
                state['queue'].append(first_track)
                embed_title = "✅ 대기열에 추가했냥! 🐾"
    except Exception as e:
        await msg.edit(content=f"❌ 첫 곡 검색 중 에러가 발생했다냥: {str(e)}")
        return
    
    if not first_track:
        await msg.edit(content="❌ 첫 곡을 찾을 수 없다냥...")
        return
    
    # 2️⃣ 첫 곡 정보로 임베드 생성 및 전송
    embed = create_guroom_embed(first_track, title_prefix=embed_title, queue_list=state['queue'])
    embed.add_field(name="추가 중인 곡", value=f"⏳ {len(queries) - 1}개 곡 검색 중...", inline=False)
    await msg.edit(content=None, embed=embed)
    
    # 3️⃣ 나머지 곡들을 비동기로 검색하여 대기열에 추가
    added_tracks = [first_track]
    
    async def fetch_remaining_tracks():
        """나머지 곡들을 비동기로 검색"""
        try:
            for query in queries[1:]:
                try:
                    search_data = await loop.run_in_executor(None, lambda q=query: ytdl.extract_info(f"ytsearch:{q}", download=False))
                    if search_data and search_data.get('entries'):
                        video_id = search_data['entries'][0]['id']
                        data = await loop.run_in_executor(None, lambda v=video_id: ytdl.extract_info(f"https://www.youtube.com/watch?v={v}", download=False))
                        track = parse_track_info(data)
                        state['queue'].append(track)
                        added_tracks.append(track)
                except Exception as e:
                    print(f"⚠️ '{query}' 검색 중 에러: {str(e)}")
                    continue
            
            # 모든 곡이 추가된 후 최종 임베드 업데이트
            if len(added_tracks) > 1:
                final_embed = create_guroom_embed(first_track, title_prefix=embed_title, queue_list=state['queue'])
                queue_names = [track['title'] for track in added_tracks]
                final_embed.add_field(name="추가된 곡", value="\n".join(queue_names[:10]), inline=False)
                try:
                    await msg.edit(embed=final_embed)
                except:
                    pass  # 메시지가 삭제되었을 수 있으므로 무시
        except Exception as e:
            print(f"⚠️ 나머지 곡 검색 중 에러: {str(e)}")
    
    # 비동기 작업을 백그라운드에서 실행
    asyncio.create_task(fetch_remaining_tracks())

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
