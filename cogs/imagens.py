import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO
import os


class Imagens(commands.Cog, description='Imagens :frame_photo:'):

  def __init__(self, client):
      self.client = client
  
  @commands.command(help = 'de @ em álguem e verás ele em um meme muito engraçado haha', description='.memehaha <@usuário>')
  async def memehaha(self, ctx, user: discord.Member):
    meme = Image.open('memes/memehaha.jpg')

    asset = user.display_avatar
    data = BytesIO(await asset.read()) #128
    pfp = Image.open(data)

    pfp = pfp.resize((48,48))

    meme.paste(pfp, (254,179))

    meme.save("memeha.jpg")

    await ctx.send(file=discord.File("memeha.jpg"))

    os.remove("memeha.jpg")
  

async def setup(client):
  await client.add_cog(Imagens(client))