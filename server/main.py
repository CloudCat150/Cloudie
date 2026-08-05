import os
import discord
from discord.ext import commands
from server.commands import admin, music
from server.config import load_token, GUROOM_COLOR
from server.music import player

# Opus 로딩 시도
if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus('/usr/lib/libopus.so')
    except Exception as e:
        print(f"⚠️ Opus 로딩 실패: {e}")
    else:
        print("✅ Opus 라이브러리 로딩 성공!")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='구름', intents=intents)

bot.add_command(admin.shutdown)
bot.add_command(music.play_router)

@bot.event
async def on_ready():
    print(f"✅ 로그인 완료: {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    """음성 채널 상태 변경 감지"""
    if member.id == bot.user.id or before.channel is None:
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=before.channel.guild)
    if voice_client and voice_client.channel.id == before.channel.id:
        if len([m for m in before.channel.members if not m.bot]) == 0:
            state = player.get_state(before.channel.guild.id)
            state['queue'].clear()
            voice_client.stop()
            await voice_client.disconnect()
            
            for channel in before.channel.guild.text_channels:
                if channel.permissions_for(before.channel.guild.me).send_messages:
                    embed = discord.Embed(
                        title="💤 다들 어디간거냥...",
                        description="방에 아무도 없어서 구름이도 나가볼게다냥! 🐾",
                        color=GUROOM_COLOR
                    )
                    await channel.send(embed=embed)
                    break

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f'오류! 오류다냥! {str(error)}')

def start_bot():
    token = load_token()
    bot.run(token)
