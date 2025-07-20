import os
import discord
from discord.ext import commands
from server.commands import admin
from server.config import load_token
from server.music import player
from server.commands import system

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

bot = commands.Bot(command_prefix="구르", intents=intents)

bot.add_command(admin.shutdown)
bot.add_command(admin.skip)

@bot.event
async def on_ready():
    print(f"✅ 로그인 완료: {bot.user}")

@bot.command(name='밍', aliases=['망'])
async def play(ctx, *, search: str):
    system.skip(ctx,search)
    player.play(ctx,search,bot)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f'오류! 오류다냥! {str(error)}')

def start_bot():
    token = load_token()
    bot.run(token)
