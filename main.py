import discord
import os
from discord.ext import commands
import asyncio

client = commands.Bot(command_prefix = '.', help_command=None, intents=discord.Intents.all())

@client.event
async def on_ready():

  for file in os.listdir('./cogs'):
    if file.endswith('.py'):
      
      file = file.replace('.py', '')

      print(f'loading cog: {file}')

      await client.load_extension(f'cogs.{file}')
  
  print(f"O bot está pronto! E está logado com o nick de '{client.user}'")


@commands.is_owner()
@client.command(hidden=True)
async def load(ctx, *, cog):
  await client.load_extension(f'cogs.{cog}')

  await ctx.send(f'A cog {cog} foi carregada no bot!')

@commands.is_owner()
@client.command(hidden=True)
async def unload(ctx, *, cog):
  await client.unload_extension(f'cogs.{cog}')

  await ctx.send(f'A cog {cog} foi descarregada do bot!')

@commands.is_owner()
@client.command(hidden=True)
async def update(ctx, *, cog):
  await client.unload_extension(f'cogs.{cog}')
  await asyncio.sleep(1)
  await client.load_extension(f'cogs.{cog}')

  await ctx.send(f'A cog {cog} atualizada!')

@client.command(help='use esse comando para relatar um bug')
async def bug(ctx):
  app = await client.application_info()

  owner = app.owner.mention
  
  await ctx.send(f'Se quiser relatar um bug entre em contato com {owner}')




client.run(os.environ['TOKEN'])



