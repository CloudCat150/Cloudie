import discord
from discord.ext import commands
from server.config import GUROOM_COLOR, SKIP_COMMANDS, CLEAR_COMMANDS, HELP_COMMANDS
from server.music.player import get_state, ensure_voice_connection, handle_bulk_play, handle_normal_play

async def handle_skip(ctx, state):
    """스킵 명령어 처리"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        
        if not state['queue']:
            embed = discord.Embed(title="🛑 재생 종료냥!", description="대기열이 비어 있어 노래를 멈췄다냥!", color=GUROOM_COLOR)
            await ctx.send(embed=embed)
    else:
        await ctx.send("지금은 재생 중인 노래가 없다냥!")

async def handle_clear_queue(ctx, state):
    """대기열 전체를 비웁니다"""
    if state['queue']:
        state['queue'].clear()
        embed = discord.Embed(
            title="🧹 재생 목록을 비웠다냥!",
            description="대기열을 모두 정리했어! 현재 재생 중인 곡은 계속된다냥.",
            color=GUROOM_COLOR
        )
    else:
        embed = discord.Embed(
            title="ℹ️ 이미 재생 목록이 비어있다냥!",
            description="추가할 곡을 불러와줘!",
            color=GUROOM_COLOR
        )
    await ctx.send(embed=embed)

async def handle_help(ctx):
    """명령어 사용법 목록을 임베드로 출력합니다"""
    embed = discord.Embed(
        title="📘 구름이 명령어 도움말",
        description="아래 명령어로 구름이를 부를 수 있다냥!",
        color=GUROOM_COLOR
    )
    embed.add_field(
        name="노래 재생",
        value="`구름아 <곡 제목>`\n검색 후 재생하거나 대기열에 추가한다냥.",
        inline=False
    )
    embed.add_field(
        name="대기열 스킵",
        value="`구름아 스킵`, `구름아 다음`, `구름아 넘기기`, `구름아 다음곡`",
        inline=False
    )
    embed.add_field(
        name="재생 목록 비우기",
        value="`구름아 청소`\n대기열을 모두 정리한다냥.",
        inline=False
    )
    embed.add_field(
        name="재생 목록 일괄 추가",
        value="`구름아 리스트 ...` 또는 `true` 단위로 곡을 나누어 입력한다냥.",
        inline=False
    )
    embed.add_field(
        name="도움말",
        value="`구름아 핼프`\n현재 명령어 목록을 확인한다냥.",
        inline=False
    )
    await ctx.send(embed=embed)

@commands.command(name='아', aliases=['이'])
async def play_router(ctx, *, search: str):
    """메인 명령어 라우터"""
    search_text = search.strip()
    state = get_state(ctx.guild.id)

    if search_text in SKIP_COMMANDS:
        await handle_skip(ctx, state)
        return

    if search_text in CLEAR_COMMANDS:
        await handle_clear_queue(ctx, state)
        return

    if search_text in HELP_COMMANDS:
        await handle_help(ctx)
        return

    if 'true' in search_text.lower() or search_text.lower().startswith('리스트'):
        is_connected = await ensure_voice_connection(ctx)
        if not is_connected:
            return

        await handle_bulk_play(ctx, state, search_text)
        return

    is_connected = await ensure_voice_connection(ctx)
    if not is_connected:
        return

    await handle_normal_play(ctx, state, search_text)
