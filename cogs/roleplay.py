import discord
from discord.ext import commands
from discord import Embed

# https://tenor.com/gifapi/documentation#quickstart

class Roleplay(commands.Cog, description='Roleplay :pleading face:'):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(hidden=True)
  async def abraçar(self, ctx, user : discord.member):
    return














async def setup(bot):
  await bot.add_cog(Roleplay(bot))