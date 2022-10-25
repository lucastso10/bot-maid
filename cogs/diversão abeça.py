import discord
from discord.ext import commands
import random

class Diversão(commands.Cog, description='Diversão abeça :nerd:'):

  def __init__(self, client):
      self.client = client
  
  @commands.command(help='Mede o tamanho do pênis do amiguinho(a)', description='.penis <@usuário>' )
  async def penis(self, ctx, user : discord.Member):
    tamanho = random.randint(0, 10)
    corpo = ''
    cabeça = 'D'
    bolas = '8'
    mensagem = ''

    for i in range(0, tamanho):
        corpo += '='
    
    if tamanho == 0:
      mensagem = 'Me desculpe amigo mas você tem micro penis :disguised_face:'
    elif tamanho >= 1 and not tamanho >= 3:
      mensagem = 'Que mixuruca'
    elif tamanho >= 3 and not tamanho >= 5:
      mensagem = 'Ta na média'
    elif tamanho >= 5 and not tamanho >= 8:
      mensagem = ':flushed:'
    elif tamanho >= 8 and not tamanho == 10:
      mensagem = 'Kid bengala 2'
    
    await ctx.send(f'O pingolin de {user.mention}: \n {bolas}{corpo}{cabeça} \n {mensagem}')
  
  @commands.command(help='De duas opções pro bot e ele escolhe uma!', description='.escolha <opção 1>:<opção 2>')
  async def escolha(self, ctx, *, mensagem):
    opções = mensagem.split(':')

    if len(opções) >= 3 or len(opções) <= 1:
      await ctx.send(':warning: Erro: número de opções inválido! Veja .ajuda escolha para ver como o comando funciona!')
      return

    falas = ['Eu prefiro esse aqui: ', 'Esse aqui é mais mandrak: ', 'Esse aqui é poggers :', 'Esse aqui é bruh moment: ', 'Esse aqui é melhor do que sexo: ', ':face_vomiting: :', 'Não gostei desse: ', 'bruh :skull::']

    await ctx.send(f'{random.choice(falas)}{random.choice(opções)}')

@commands.command(hidden=True)
async def ship(self, ctx, user1 : discord.member, user2 : discord.member):
    ship = random.randint(0,100)
    mensagem = ''
    return
      

async def setup(client):
  await client.add_cog(Diversão(client))