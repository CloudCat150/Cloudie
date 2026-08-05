from discord.ext import commands

@commands.command(name=':종료')
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("다음에 보자냥ㅠㅠ")
    await ctx.bot.close()