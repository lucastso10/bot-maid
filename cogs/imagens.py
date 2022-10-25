import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO
import os


class Imagens(commands.Cog, description='Imagens :frame_photo:'):

    def __init__(self, client):
        self.client = client
    
    @commands.command(hidden=True)
    async def bundadocaio(self, ctx):

        channel = ctx.message.author.dm_channel

        if channel is None:
            channel = await ctx.message.author.create_dm()
        
        await channel.send(file=discord.File('memes/Bunda_do_caio.png'))
    
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
    
    @commands.command(aliases = ['gozarem'], help= 'de @ em uma pessoa e expalhe liquido duvidoso em sua foto de perfil (porfavor não use esse comando com uma pessoa que você acha que não gostaria!)' , description='.cumon <@usuário>')
    async def cumon(self, ctx, user: discord.Member):

        meme = Image.open("memes/cum.png")

        asset = user.display_avatar
        data = BytesIO(await asset.read()) #512
        pfp = Image.open(data)
        pfp = pfp.convert('RGB')
            
        tamanho = pfp.size
        bruh = tamanho[1]
        div = int(bruh / 8)
        final = (bruh - div, bruh - div)

        meme = meme.resize(final)

        pfp.paste(meme, (int(div/2),int(div/2)), meme)
        pfp.save("CUM.jpg")

        myid = ctx.message.author.id
            
        await ctx.send(f'{ctx.message.author.mention} gozou no(a) {user.mention}', file=discord.File("CUM.jpg"))

        os.remove("CUM.jpg")
    

async def setup(client):
    await client.add_cog(Imagens(client))