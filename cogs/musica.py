import discord
import wavelink
from discord.ext import commands
from discord import Embed
import time
import DiscordUtils
import asyncio
from random import shuffle
from enum import Enum

def identifica(link):
  
  if link.startswith('https'):
    if 'youtu' in link:
      if 'list=' in link:
        return 'ytp'
      else:
        return 'ytl'
        
    if 'soundcloud' in link:
      return 'sc'
    
    return None
  else:
    return 'pesquisa'



class Loop(Enum):
  NONE = 0
  Song = 1
  List = 2





class Queue:
  def __init__(self):
    self.queue = []
    self.loop = Loop.NONE

  @property
  def is_empty(self):
    if self.queue:
      return False
    else:
      return True

  @property
  def current_track(self):
    if self.queue:
      return self.queue[0]
    else:
      return None

  @property
  def playlist(self):
    return self.queue

  @property
  def length(self):
    return self.queue.count

  def add(self, *args):
    self.queue.extend(args)

  def next_track(self):
    if self.loop == Loop.Song:
      pass
    elif self.loop == Loop.List:
      self.queue.extend(self.queue[0])
      self.queue.pop(0)
    else:
      self.queue.pop(0)

    if self.queue:
      return self.queue[0]

  def set_loop(self, mode):
    if mode == "NONE":
      self.loop = Loop.NONE
    elif mode == "SONG":
      self.loop = Loop.Song
    elif mode == "LIST":
      self.loop = Loop.List

  def remove_track(self, position):
    self.queue.pop(position)

  def shuffle(self):
    if self.queue:
      return shuffle(self.queue)

  def clear(self):
    self.queue.clear()

  def skip(self):
    self.queue.pop(0)

  def where(self, track):
    return self.queue.index(track)


    

class Player(wavelink.Player):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.queue = Queue()

  async def start_playing(self):
    await self.play(self.queue.current_track[0])

  async def start_next(self):
    try:
      await self.play(self.queue.next_track()[0])
    except TypeError:
      return




      

class Musicas(commands.Cog, description='Músicas :musical_note:'):
  
  def __init__(self, bot):
    self.bot = bot

    self.bot.loop.create_task(self.start_nodes())


  async def start_nodes(self):
    node = await wavelink.NodePool.create_node(bot=self.bot,
                                          host='lavalink-replit.bolofofodoidao.repl.co',
                                          port=443,
                                          password='youshallnotpass',
                                          https=True)

# =======================================================================================================
  @commands.Cog.listener() # quando o node estiver pronto printar informando
  async def on_wavelink_node_ready(self, node: wavelink.Node):
    print(f"Node {node.identifier} está conectado!")
  
# =======================================================================================================
  # toca a proxima musica quando a atual acabar
  @commands.Cog.listener()
  async def  on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
    await player.start_next()

# =======================================================================================================
  # printa erro e skipa musica
  @commands.Cog.listener()
  async def on_wavelink_track_exception(self, player: wavelink.Player, track: wavelink.Track, error):
    await player.queue.current_track[1].send(f":warning: Falha ao tocar a musica {player.queue.current_track[0].title}! Pulando para a proxima! wavelink.TrackExeception")

    await player.start_next()

# =======================================================================================================
  # printa erro e skipa a musica
  @commands.Cog.listener()
  async def on_wavelink_track_stuck(self, player: wavelink.Player, track: wavelink.Track, threshold):
    await player.queue.current_track[1].send(f":warning: Falha ao tocar a musica {player.queue.current_track[0].title}! Pulando para a proxima! wavelink.TrackStuck")
        
    await player.start_next()

# =======================================================================================================
  # toca a musica no bot se ele n estiver conectado ele conecta no chat de voz e toca ou link do youtube ou
  # pesquisa o que foi dado no youtube
  # se o bot já estiver tocando algo o parametro do comando vai para a fila
  @commands.command(aliases=['t','play','p'], help='Toca vídeos do youtube no canal de voz que você está conectado', description='.tocar <link do video do youtube/termo pra pesquisar no youtube>')
  async def tocar(self, ctx, *, musica: str):
    vc: Player = ctx.voice_client
    
    # conecta no canal de voz
    if not vc:
      if ctx.author.voice is None:
        await ctx.send('Você não está conectado a nenhum canal de voz! :skull:')
        return
      vc: Player = await ctx.author.voice.channel.connect(cls=Player)
    else:
      if ctx.author.voice.channel.id != ctx.message.author.voice.channel.id:
        await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
        return

    # pega o tipo de str que o usuario mando
    tipo = identifica(musica)
    
    # dependendo do tipo da str o bot faz algo diferente
    if tipo == 'pesquisa' or tipo == 'ytl': # link do youtube e pesquisa são o mesmo comando da pra juntar
      musica = await wavelink.YouTubeTrack.search(query=musica, return_first=True)
      if not musica:
        await ctx.send(':warning: Erro: sua música não foi encontrada')
        return
    elif tipo == 'ytp':
      playlist = await wavelink.YouTubePlaylist.search(query=musica)
      musicas = playlist.tracks
      if not musicas:
        await ctx.send(':warning: Erro: sua música não foi encontrada')
        return
      embed = await mensagemBunita.playlist(ctx=ctx, playlist=playlist)
      await ctx.send(embed=embed)
    elif tipo == 'sc':
      await ctx.send('Não tenho suporte pra soundcloud ainda! :skull:')
      return
    elif tipo is None:
      await ctx.send(f'Link invalido! Só aceito links do youtube ou termos de pesquisa! :disguised_face:')
      return

    #adiciona a musica a playlist 
    if tipo == 'ytp':
      for musica in musicas:
        vc.queue.add((musica, ctx))
    else:
      vc.queue.add((musica, ctx))
      
    # se o bot estiver tocando algo já ele só manda uma mensagem falando que adiciono na playlist
    if vc.is_playing() and not vc.is_paused():
      embed = await mensagemBunita.musicaQueue(ctx=ctx, musica=musica, posição=vc.queue.where( (musica,ctx)))
      await ctx.send(embed=embed)
      return

    await vc.start_playing()

    await ctx.send(f'Tocando `{vc.queue.current_track[0].title}` agora! No canal de voz `{vc.queue.current_track[1].author.voice.channel.name}` :musical_note:')

# =======================================================================================================
  # mostra a musica que está tocando atualmente
  # a thumb do yt
  # o tempo do video que está e o tempo máximo
  @commands.command(aliases=['np', 'tc', 'nowPlaying'], help='mostra a musica que está sendo tocada agora')
  async def tocandoagora(self, ctx):
    vc: Player = ctx.voice_client

    #verifica se o bot ta em um canal de voz
    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    # verifica se o bot ta tocando alguma coisa
    elif not vc.is_playing and not vc.is_paused:
      await ctx.send('Não tô tocando nada!')
      return
    
    # cria o embed e manda
    embed = await mensagemBunita.musicayt(ctx=vc.queue.current_track[1], musica=vc.queue.current_track[0], player=vc)
    await ctx.send(embed=embed)

# =======================================================================================================
  # pausa a musica que estiver tocando
  @commands.command(aliases=['pause'], help='Pausa a música que está tocando')
  async def pausar(self, ctx):
    vc: Player = ctx.voice_client

    #verifica se o bot ta conectado no canal de voz / ta no mesmo canal que o autor / se o autor ta em um canal de voz
    if not vc:
      await ctx.send('Não to conectado a nenhum canal de voz!')
    
    #verifica se o player ta tocando musica se sim ele pausa
    elif vc.is_playing():
      await vc.set_pause(True)
      await ctx.send('Música pausada! :thumbsup:')
    
    #verifica se o player já ta pausado
    elif vc.is_paused():
      await ctx.send('A música ja está pausada')
    
    #a ultima opção é o bot não ta tocando nada
    else:
      await ctx.send('Não tem nenhuma música tocando')

# =======================================================================================================
  # verifica se tem uma musica pausada e continua ela se houver
  @commands.command(aliases=['resume', 'continuar', 'resumir'], help='despausa a musica se ela foi pausada')
  async def despausar(self, ctx):
    vc: Player = ctx.voice_client

    #verifica se o bot ta conectado no canal de voz
    if not vc:
      await ctx.send('Não estou conectado a nenhum canal de voz')
    
    #verifica se o player ta pausado se sim ele despausa
    elif vc.is_paused():
      await vc.set_pause(False)
      await ctx.send('Música despausada! :thumbsup:')
    
    #verifica se o player ta tocando
    elif player.is_playing():
      await ctx.send('A música já está tocando! :musical_note:')
    
    #a ultima opção é o bot não ta tocando nada
    else:
      await ctx.send('não tem nenhuma musica tocando! :skull:')

# =======================================================================================================
  # pula para proxima música da fila
  @commands.command(aliases=['s', 'skip', 'skipar'], help='Pula para a próxima música da playlist e se não tiver nenhuma só não toca nada')
  async def pular(self, ctx):
    vc: Player = ctx.voice_client

    #verifica se o bot ta conectado no canal de voz
    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return
    
    if not vc.is_playing() and not vc.is_paused():
      await ctx.send('Eu não to tocando nada')
      return
    
    if vc.queue.loop == Loop.List:
        
      def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == '1' or m.content == '2' or m.content == '3'

      await ctx.send('A playlist está trancada! :lock: Porque o loop está ativo! Se você realmente quer usar esse comando escolha uma dessas 2 opções (responda com o número da opção que escolher) \n `1. pular a música atual sem remove-lá do loop` \n `2. pular a música atual e remove-lá do loop` \n `3. cancelar`')
      try:
        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa mas você demorou muito para responder, nada foi feito!')
        return
          
      if msg.content == '1':
        await ctx.send('Okay, pulando a música e mantendo a no loop...')
        vc.queue.add(vc.queue.current_track)
      
      elif msg.content == '2':
        await ctx.send('Okay, pulando a música e removendo ela do loop...')

      else:
        await ctx.send('Operação cancelada! :robot: bep bop')
        return
    
    await vc.stop()
    await ctx.send('Música skipada! :thumbsup:')
    await vc.start_next()

# =======================================================================================================

  @commands.command(aliases=['stop', 'leave', 'sair'], help='Faz o bot sair do canal de voz e limpa a playlist')
  async def parar(self, ctx):
    player = self.bot.wavelink.get_player(ctx.guild.id)

     #verifica se o bot ta conectado no canal de voz
    if not player.is_connected:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
    
     #verifica se o usuario que invoco tá em um canal de voz em primeiro lugar
    elif ctx.message.author.voice is None:
      await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
    
    #verifica se o usuario que invoco tá no mesmo canal de voz que o bot
    elif player.channel_id != ctx.message.author.voice.channel.id:
      await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
    
    #se o bot tiver conectado ao canal de voz ele ele quita e limpa a queue
    elif player.is_connected:
      await player.disconnect()
      queues[ctx.guild.id].clear()
      await ctx.send('ta parei')
      if loop[ctx.guild.id]:
        loop[ctx.guild.id] = False

# =======================================================================================================

  @commands.command(aliases=['clear'], help='Limpa todas as músicas da playlist')
  async def limpar(self, ctx):
    if loop[ctx.guild.id]:
        
      def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['s', 'n', 'sim', 'nao']

      await ctx.send('A playlist está trancada! :lock: Porque o loop está ativo! Você quer mesmo fazer isso? (responda com S ou N)')
      try:
        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa mas você demorou muito para responder, a playlist não foi limpada!')
            
      if msg.content.lower() == 's' or msg.content.lower() == 'sim':
        await ctx.send('Okay, limpando playlist...')
      else:
        await ctx.send('Playlist não limpada!')
        return
    atual = queues[ctx.guild.id][0]
    queues[ctx.guild.id].clear()
    queues[ctx.guild.id].append(atual)

    await ctx.send('Queue limpada! :thumbsup:')

# =======================================================================================================

  @commands.command(aliases=['queue'], help='Mostra todas as músicas que estão na playlist')
  async def playlist(self, ctx):
    vc: Player = ctx.voice_client
    
    if not vc or vc.queue.is_empty:
      await ctx.send('Não tem nenhuma música na playlist!')
      return

    if vc.queue.length == 1:
      await self.tocandoagora(ctx=ctx)
      return

    await mensagemBunita.Queue(queues=vc.queue.playlist, ctx=ctx)


# =======================================================================================================

  @commands.command(aliases=['skipto', 'sp', 'st', 'skiparpara'], help='Pula para o número da playlist mandado', description='.pularpara <posição da playlist>')
  async def pularpara(self, ctx, *, position: int):
    player = self.bot.wavelink.get_player(ctx.guild.id)

    if not player.is_connected:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    elif ctx.message.author.voice is None:
      await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
      return
    
    elif not player.is_playing and not player.is_paused:
      await ctx.send('Não tô tocando nada')
      return

    elif player.channel_id != ctx.message.author.voice.channel.id:
      await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
      return
  
    elif len(queues[ctx.guild.id]) <= 2:
      await ctx.send('Não há musicas o suficiente na playlist para executar esse comando! :skull:')
      return

    elif loop[ctx.guild.id]:
      
      def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == '1' or m.content == '2' or m.content == '3'

      await ctx.send('A playlist está trancada! :lock: Porque o loop está ativo! Se você realmente quer usar esse comando escolha uma dessas 2 opções (responda com o número da opção que querer) \n `1. remover todas as músicas até a posição da queue que escolheu` \n `2. ir até a posição da queue que escolheu sem remover as músicas do loop` \n `3. cancelar`')
      try:
        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa mas você demorou muito para responder, nada foi feito!')
          
      if msg.content == '1':
        await ctx.send('Okay, removendo as músicas...')
        
      elif msg.content == '2':
        await ctx.send('Okay, pulando até a posição que escolheu...')
        await player.stop()

        for i in range(0,position):
          atual = queues[ctx.guild.id][0]
          queues[ctx.guild.id].pop(0)
          queues[ctx.guild.id].append(atual)
        
        await player.play(queues[ctx.guild.id][0]['track'])
        return
        
      else:
        await ctx.send('Operação cancelada! :robot: bep bop')
        return
    
    if position == 1:
      self.pular(ctx=ctx)
      return
    
    await player.stop()

    for i in range(0,position):
      queues[ctx.guild.id].pop(0)
    
    await asyncio.sleep(0.5)

    await player.play(queues[ctx.guild.id][0]['track'])

    await ctx.send(f"Queue skipada para posição `{position}. {queues[ctx.guild.id][0]['track'].title}`")

# =======================================================================================================

  @commands.command(aliases=['seek'], help='Vai para o minuto da música que comandar (no modelo horas:minutos:segundos)', description='.tempo <horas:minutos:segundos / minutos:segundos>')
  async def tempo(self, ctx, *, tempo):
    player = self.bot.wavelink.get_player(ctx.guild.id)

    verificação = tempo.split(':')
    
    if len(verificação) == 2:
      try:
        tempoML = int(verificação[0]) * 60 + int(verificação[1])
        tempoML = int(tempoML * 1000)
      except:
        await ctx.send('Tempo inválido!')
        return
    elif len(verificação) == 3:
      try:
        tempoML = int(verificação[0]) * 60 + int(verificação[1])
        tempoML = tempoML * 60 + int(verificação[2])
        tempoML = int(tempoML * 1000)
      except:
        await ctx.send('Tempo inválido!')
        return
    else:
      await ctx.send('Tempo inválido!')
      return
    
    if tempoML > queues[ctx.guild.id][0]['track'].duration:
      await ctx.send('Tempo maior que a duração do video! :skull:')
      return

    await player.seek(tempoML)

    await ctx.send(f'Video avançado para o tempo `{tempo}`! :thumbsup:')


# =======================================================================================================
  
  @commands.command(name='loop', help='Loopa uma música ou a playlist toda! (pra desativar/trocar o modo use o comando novamente)')
  async def loop_command(self, ctx):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    if ctx.message.author.voice is None:
      await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
      return

    if not vc.is_playing and not vc.is_paused:
      await ctx.send('Não tô tocando nada')
      return
    
    if vc.queue.loop == Loop.NONE:
      vc.queue.set_loop("SONG")
      await ctx.send("Loop ativado para a música atual! :repeat_one:")
      return
    elif vc.queue.loop == Loop.Song:
      vc.queue.set_loop("LIST")
      await ctx.send("Loop ativado para a playlist toda! :repeat:")
      return
    elif vc.queue.loop == Loop.List:
      vc.queue.set_loop("NONE")
      await ctx.send("Loop desativado! :no_entry_sign:")
      return


# =======================================================================================================
  @commands.command(aliases=['remove'], help='remove uma música na posição comandar', description='.remover <posição da playlist>')
  async def remover(self, ctx, *, posição : int):
    player = self.bot.wavelink.get_player(ctx.guild.id)

    if not player.is_connected:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    if ctx.message.author.voice is None:
      await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
      return

    if player.channel_id != ctx.message.author.voice.channel.id:
      await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
      return

    if posição > len(queues[ctx.guild.id]) or posição <= 0:
      await ctx.send(':warning: Erro: Número invalido')
      return
    
    await ctx.send(f'O video `{queues[ctx.guild.id][posição]["track"].title}`, foi removido com sucesso da queue!')
    queues[ctx.guild.id].pop(posição)

# =======================================================================================================
  
  @commands.command(aliases=['v'], help='Muda o volume da música! O volume vai de 0 até 1000 (cuidado 1000 é muito alto)', description='.volume <número do volume>', hidden=True)
  async def volume(self, ctx, *, vol : int):
    player = self.bot.wavelink.get_player(ctx.guild.id)

    if not player.is_connected:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    if ctx.message.author.voice is None:
      await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
      return

    if player.channel_id != ctx.message.author.voice.channel.id:
      await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
      return

    await player.set_volume(vol)


# =======================================================================================================
  @commands.command(aliases=['playskip' ,'ps' ,'ta'], help='Pula a música atual e imediatamente toca a música que comandar ignorando a queue', description='.tocaragora <link do video do youtube/termo pra pesquisar no youtube>')
  async def tocaragora(self, ctx, *, musica):
    player = self.bot.wavelink.get_player(ctx.guild.id)

    if not player.is_connected:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    if ctx.message.author.voice is None:
      await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
      return

    if player.channel_id != ctx.message.author.voice.channel.id:
      await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
      return
    
    if not player.is_playing and not player.is_paused:
      await ctx.send('Não tem nenhuma música tocando!') 
      return

    await player.stop()

    queues[ctx.guild.id].pop(0)

    # pega o tipo de str que o usuario mando
    tipo = await Identificador.identifica(link=musica)
    
    # dependendo do tipo da str o bot faz algo diferente
    if tipo == 'pesquisa':
      musicas = await self.bot.wavelink.get_tracks(f'ytsearch:{musica}')
      if not musicas:
        await ctx.send(':warning: Erro: sua música não foi encontrada')
        return
    elif tipo == 'ytl':
      musicas = await self.bot.wavelink.get_tracks(musica)
      if not musicas:
        await ctx.send(':warning: Erro: sua música não foi encontrada')
        return
    elif tipo == 'ytp':
      penis = await self.bot.wavelink.get_tracks(musica)
      musicas = penis.tracks
      if not musicas:
        await ctx.send(':warning: Erro: sua música não foi encontrada')
        return
      embed = await mensagemBunita.playlist(ctx=ctx, playlist=penis, first=musicas[0])
      await ctx.send(embed=embed)
    elif tipo == 'sc':
      await ctx.send('Não tenho suporte pra soundcloud ainda! :skull:')
      return
    elif tipo is None:
      await ctx.send(f'Link invalido! Só aceito links do youtube ou termos de pesquisa! :disguised_face:')
      return

    #adiciona a musica a playlist
    if tipo != 'ytp':
      if len(queues[ctx.guild.id]) <= 1000:
        musica = musicas[0]
        content = {'track' : musica, 'ctx' : ctx ,'tipo' : tipo}
        queues[ctx.guild.id].insert(0, content)
      else:
        await ctx.send(':warning: Você alcançou o limite de 5000 musicas por queue! Música não adicionada! :skull:')
        return
    else:
      songs = []
      for i in range(0, len(musicas)):
        if len(queues[ctx.guild.id]) <= 1000:
          content = {'track' : musicas[i], 'ctx' : ctx ,'tipo' : tipo}
          songs.append(content)
        else:
          await ctx.send(':warning: Você alcançou o limite de 5000 musicas por queue! Música não adicionada! :skull:')
          break
      queues[ctx.guild.id] = songs + queues[ctx.guild.id]

    await player.play(queues[ctx.guild.id][0]['track'])

    await ctx.send(f'Tocando `{queues[ctx.guild.id][0]["track"]}` agora! No canal de voz `{ctx.author.voice.channel.name}` :musical_note:')


# =======================================================================================================
  @commands.is_owner()
  @commands.command(hidden=True)
  async def infiltrar(self, ctx, *, id : int):
    player = self.bot.wavelink.get_player(id)

    def check(m):
      return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['s', 'n', 'sim', 'nao']
    
    server = self.bot.get_guild(id)

    await ctx.send(f'vc quer infiltrar no servidor {server.name}')
    try:
      msg = await self.bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
      await ctx.send('Desculpa vc demorou muito pra responde')
      return
    
    if msg.content.lower() == 'n' or msg.content.lower() == 'nao':
      await ctx.send('Operação cancelada! :robot: BEP BOP')
      return
    
    if not player.is_connected:
      nome_canais = []
      canais = server.voice_channels
      canais_ativos = []

      for canal in canais:
        if not canal.members == '':
          canais_ativos.append(canal)
      
      if not canais_ativos:
        await ctx.send('não tem ninguem conectado nesse servidor')
        return
      
      if len(canais_ativos) > 1:
        nomes = []
        mensagem = 'Quais desses canais de voz eu devo infiltrar? (coloque o número do servidor que quer invadir) \n'
        for i in range(0,len(canais_ativos)):
          mensagem = mensagem + f'`{i}.` ' + canais_ativos[i].name + ' \n'

        await ctx.send(mensagem)
        try:
          msg = await self.bot.wait_for('message', check=None, timeout=30.0)
        except asyncio.TimeoutError:
          await ctx.send('Desculpa vc demorou muito pra responde')
          return
        
        canal = canais_ativos[int(msg.content)]
      else:
        canal = canais_ativos[0]
        
      await ctx.send('Qual música vc quer infiltrar?(so link do youtube)')
      try:
        msg = await self.bot.wait_for('message', check=None, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa vc demorou muito pra responde')
        return
      
      musicas = await self.bot.wavelink.get_tracks(msg.content)

      if not musicas:
        await ctx.send('Deu ruim na música! Operação cancelada! :robot: BEP BOP')
        return

      def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['s', 'n', 'sim', 'nao']
      
      await ctx.send('quer mudar o volume?')
      try:
        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa vc demorou muito pra responde')
        return
      
      if msg.content.lower() == 's' or msg.content.lower() == 'sim':
        await ctx.send('pra qual valor?')
        try:
          msg = await self.bot.wait_for('message', check=None, timeout=30.0)
        except asyncio.TimeoutError:
          await ctx.send('Desculpa vc demorou muito pra responde')
          return
        
        volume = msg.content
      
      await ctx.send('se infiltrando :smiling_imp:')

      if not player.is_connected:
        await player.connect(canal.id)
      
      if player.is_playing or player.is_paused:
        await player.stop()
        queues[id].pop(0)
      
      content = {'track' : musicas[0], 'ctx' : ctx}
      queues[id].insert(0, content)
      
      await player.play(musicas[0])

      await player.set_volume(int(volume))


# =======================================================================================================
  
  @commands.command(hidden=True)
  async def pi(self, ctx):
    if ctx.guild.id == 276110988028411904:
      await self.tocar(ctx=ctx, musica='https://youtu.be/tV1grJ4jIH0?list=PL2n0HC2aP0HSO3UOomdROxLN19GfXN35r')

# =======================================================================================================
  @commands.Cog.listener()
  async def on_voice_state_update(self, member, before, after):
    if not member.bot:
      return
    
    elif not member.id == self.bot.user.id:
      return
    
    elif before.mute == False and after.mute == True:
      player = wavelink.Player
      await player.set_pause(True)
      return
    
    elif before.mute == True and after.mute == False:
      player = wavelink.Player
      await player.set_pause(False)
      return
    
    elif not before.channel is None and not after.channel is None:
      player = wavelink.Player
      await player.set_pause(True)
      await asyncio.sleep(0.5)
      await player.set_pause(False)
      return

    elif before.channel is None:
      player = wavelink.Player
      time = 0
      while True:
        await asyncio.sleep(1)
        time = time + 1
        if player.is_playing and not player.is_paused:
          time = 0
        if time == 600:
          await player.disconnect() #if not it disconnects
        if not player.is_connected:
          break
      return
    
    elif after.channel is None:
      player = wavelink.Player
      if not player.is_connected:
        await player.stop()
        queues[before.channel.guild.id].clear()

# =======================================================================================================

class mensagemBunita():

  async def playlist(ctx, playlist):
    embed = Embed(title='Playlist adicionada a queue do server! :thumbsup:', 
    description=f"{playlist.name}", 
    colour=0xFF0080)

    duração = 0
    for musica in playlist.tracks:
      duração = duração + musica.length

    if not duração >= 3600:
      duração = time.strftime('%M:%S', time.gmtime(duração))
    else:
      duração = time.strftime('%H:%M:%S', time.gmtime(duração))

    embed.add_field(name='Duração total', 
    value=f"`{duração}`")

    embed.add_field(name='Músicas adicionadas',
    value=f"`{len(playlist.tracks)}`",
    inline=True)
        
    embed.set_author(name='Pediu essa', 
    icon_url=ctx.author.display_avatar)

    embed.set_thumbnail(url=playlist.tracks[0].thumb)

    return embed

  async def musicayt(ctx, musica, player):
    embed = Embed(title=musica.title, url=f"{musica.uri}", colour=0xFF0080)

    if musica.is_stream():
      string_tempo = '`Ao vivo :red_circle:`'
    else:
      if musica.length >= 3600:
        duração = time.strftime('%H:%M:%S', time.gmtime(musica.length))
        posição = time.strftime('%H:%M:%S', time.gmtime(player.position))
      else:    
        duração = time.strftime('%M:%S', time.gmtime(musica.length))
        posição = time.strftime('%M:%S', time.gmtime(player.position))

      string_tempo = f'`{posição}\{duração}`'
    
    embed.add_field(name='Duração', value=string_tempo)
    embed.add_field(name='Canal', value=f"`{musica.author}`")
    embed.set_author(name='Pediu essa', icon_url=ctx.author.display_avatar)
    embed.set_thumbnail(url=musica.thumb)

    return embed
  
  async def musicaQueue(ctx, musica, posição):
    embed = Embed(title=musica.title, url=f"https://www.youtube.com/watch?v={musica.uri}", colour=0xFF0080)
    
    duração = time.strftime('%M:%S', time.gmtime(musica.length/1000))
    embed.add_field(name='Duração', value=f'`{duração}`')
    embed.add_field(name='Canal', value=f"`{musica.author}`")
    embed.add_field(name='Posição na playlist', value=f"`{posição}`", inline=False)
    embed.set_author(name='Música adicionada a playlist', icon_url=ctx.author.display_avatar)
    embed.set_thumbnail(url=musica.thumb)

    return embed
  
  async def Queue(queues, ctx):
      
    lista_embeds = []
    musicas = ''
    duração = 0
    for musica in queues:
      duração = duração + musica[0].length
    
    if not duração >= 3600:
      duração = time.strftime('%M:%S', time.gmtime(duração))
    else:
      duração = time.strftime('%H:%M:%S', time.gmtime(duração))


    musicas = "`Música atual:`" + f"[{queues[0][0].title}]({queues[0][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[0][0].length))}`" + "\n \n"

    for i in range(1, len(queues)):
            
      if i % 10 == 0 or i == len(queues) - 1:
        musicas = musicas + f'`{i}.`' + f"[{queues[i][0].title}]({queues[i][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[i][0].length))}`" + '\n \n' 
        musicas = musicas + f'{len(queues) - 1} músicas na playlist | Tempo total: {duração}'

        embed = Embed(title='Músicas na playlist :disguised_face:', description=musicas, colour=0xFF0080)

        embed.set_footer(text=f'página {len(lista_embeds)+ 1} de {(len(queues) - (len(queues) % 10)) / 10 + 1:.0f}')
        lista_embeds.append(embed)
        musicas = ''
          
      elif i % 10 != 0:
        musicas = musicas + f'`{i}.`' + f"[{queues[i][0].title}]({queues[i][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[i][0].length))}`" + '\n \n'


    if len(lista_embeds) > 1:
      paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx)
      paginator.add_reaction('◀', "back")
      paginator.add_reaction('▶', "next")

      await paginator.run(lista_embeds)
    else:
      await ctx.send(embed=lista_embeds[0])


async def setup(client):
  await client.add_cog(Musicas(client))
      