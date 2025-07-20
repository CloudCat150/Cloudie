from discord.ext import commands

@commands.command(name='-종료')
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("봇을 종료합니다.")
    await ctx.bot.close()

@commands.command(name='-스킵')
@commands.is_owner()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("다음 곡으로 넘어갑니다.")