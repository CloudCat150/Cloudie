import os
import discord
from discord.ext import commands
from server.commands import admin
from server.config import load_token
from server.music import player
from server.commands import system

async def skip(ctx,search):
    if search == "스킵":  # 만약 사용자가 '스킵'을 입력하면
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(
              title="**다음곡으로냥!** 🐾",
              color=discord.Color.from_rgb(170, 219, 255)
            )
        return  # '스킵' 명령 처리 후 함수 종료
    