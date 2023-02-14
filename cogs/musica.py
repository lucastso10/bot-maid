import discord
import os
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
    if self.length <= 0:
      return None
    else:
      return self.queue[0]

  @property
  def current_ctx(self):
    if self.queue:
      return self.queue[1]
    else:
      return None

  @property
  def playlist(self):
    return self.queue

  @property
  def length(self):
    return len(self.queue)

  def add(self, track, ctx):
    self.queue.append((track, ctx))

  def add_to_front(self, track, ctx):
    self.queue.insert(0,(track, ctx))

  def next_track(self):
    if self.length <= 0:
      return None
    
    if self.loop == Loop.Song:
      pass
    elif self.loop == Loop.List:
      self.add(self.queue[0][0],self.queue[0][1])
      self.skip()
    else:
      self.skip()
      
    return self.queue[0]

  def set_loop(self, mode):
    if mode == "NONE":
      self.loop = Loop.NONE
    elif mode == "SONG":
      self.loop = Loop.Song
    elif mode == "LIST":
      self.loop = Loop.List

  def remove_track(self, position):
    return self.queue.pop(position)

  def shuffle(self):
    atual = self.current_track
    self.queue.pop(0)
    shuffle(self.queue)
    self.add_to_front(atual[0], atual[1])

  def clear(self):
    atual = self.current_track
    self.queue.clear()
    self.add(atual[0], atual[1])

  def skip(self):
    self.queue.pop(0)


    

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

  async def teardown(self):
    if self.is_connected():
      await self.disconnect()
    try:
      del self
    except KeyError:
      pass




      

class Musicas(commands.Cog, description='Músicas :musical_note:'):
  
  def __init__(self, bot):
    self.bot = bot

    self.bot.loop.create_task(self.start_nodes())


  async def start_nodes(self):
    node = await wavelink.NodePool.create_node(bot=self.bot,
                                          host=os.environ['SERVER'],
                                          port=443,
                                          password='youshallnotpass',
                                          https=True)

# =======================================================================================================
  # quando o node estiver pronto printar informando
  @commands.Cog.listener()
  async def on_wavelink_node_ready(self, node: wavelink.Node):
    print(f"Node {node.identifier} está conectado!")
  
# =======================================================================================================
  # toca a proxima musica quando a atual acabar
  @commands.Cog.listener()
  async def  on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
    if reason == "FINISHED":
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
  async def tocar(self, ctx,*, musica: str):
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
        vc.queue.add(musica, ctx)
    elif musica == None:
      ctx.send("Desculpa mas não encontrei essa musica! :disguised_face:")
    else:
      vc.queue.add(musica, ctx)

    # se o bot estiver tocando algo já ele só manda uma mensagem falando que adiciono na playlist
    if vc.is_playing() and not vc.is_paused():
      embed = await mensagemBunita.musicaQueue(ctx=ctx, musica=musica, posição=vc.queue.length)
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
    elif vc.is_playing():
      await ctx.send('A música já está tocando! :musical_note:')
    
    #a ultima opção é o bot não ta tocando nada
    else:
      await ctx.send('não tem nenhuma musica tocando! :skull:')

# =======================================================================================================
  # pula para proxima música da fila se o loop estiver ativado pergunta se quer realmente remove
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
      
      elif msg.content == '2':
        await ctx.send('Okay, pulando a música e removendo ela do loop...')
        await vc.stop()
        vc.queue.set_loop("NONE")
        await asyncio.sleep(0.5)
        await vc.start_next()
        vc.queue.set_loop("LIST")
        return

      else:
        await ctx.send('Operação cancelada! :robot: bep bop')
        return
    
    await vc.stop()
    await ctx.send('Música skipada! :thumbsup:')
    await asyncio.sleep(0.5)
    await vc.start_next()

# =======================================================================================================
  # faz o bot sair do canal de voz e destroi o player
  @commands.command(aliases=['stop', 'leave', 'sair'], help='Faz o bot sair do canal de voz e limpa a playlist')
  async def parar(self, ctx):
    vc: Player = ctx.voice_client

     #verifica se o bot ta conectado no canal de voz
    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
    
     #verifica se o usuario que invoco tá em um canal de voz em primeiro lugar
    elif ctx.message.author.voice is None:
      await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
    
    #se o bot tiver conectado ao canal de voz ele ele quita e limpa a queue
    elif vc.is_connected():
      await vc.disconnect()
      await vc.teardown()
      await ctx.send('ta parei')

# =======================================================================================================
  # limpa todas as músicas da playlist
  @commands.command(aliases=['clear'], help='Limpa todas as músicas da playlist')
  async def limpar(self, ctx):
    vc: Player = ctx.voice_client
    if vc.queue.loop == Loop.List:
        
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
    
    vc.queue.clear()
    await ctx.send('Queue limpada! :thumbsup:')

# =======================================================================================================
  # mostra todas as músicas da playlist
  @commands.command(hidden=True, help='Mostra todas as músicas que estão na playlist')
  async def printlist(self, ctx):
    vc: Player = ctx.voice_client
    print(vc.queue.playlist)

# =======================================================================================================
  # mostra todas as músicas da playlist
  @commands.command(aliases=['queue'], help='Mostra todas as músicas que estão na playlist')
  async def playlist(self, ctx):
    vc: Player = ctx.voice_client
    
    if not vc or vc.queue.is_empty:
      await ctx.send('Não tem nenhuma música na playlist!')
      return

    if vc.queue.length == 1:
      await self.tocandoagora(ctx)
      return

    await mensagemBunita.Queue(queues=vc.queue.playlist, ctx=ctx)


# =======================================================================================================
  #
  @commands.command(aliases=['skipto', 'sp', 'st', 'skiparpara'], help='Pula para o número da playlist mandado', description='.pularpara <posição da playlist>')
  async def pularpara(self, ctx, *, position: int):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return
    
    elif not vc.is_playing() and not vc.is_paused():
      print(f"is_playing = {vc.is_playing()} and is_paused: {vc.is_paused()}")
      await ctx.send('Não tô tocando nada')
      return
  
    elif vc.queue.length <= 2:
      await ctx.send('Não há musicas o suficiente na playlist para executar esse comando! :skull:')
      return

    elif vc.queue.length < position:
      await ctx.send("A posição dada excede o número de músicas na playlist! :disguised_face:")

    elif vc.queue.loop == Loop.List:
      
      def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == '1' or m.content == '2' or m.content == '3'

      await ctx.send('A playlist está trancada! :lock: Porque o loop está ativo! Se você realmente quer usar esse comando escolha uma dessas 2 opções (responda com o número da opção que querer) \n `1. remover todas as músicas até a posição da queue que escolheu` \n `2. ir até a posição da queue que escolheu sem remover as músicas do loop` \n `3. cancelar`')
      try:
        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa mas você demorou muito para responder, nada foi feito!')
        return
          
      if msg.content == '1':
        await ctx.send('Okay, removendo as músicas...')
        
      elif msg.content == '2':
        await ctx.send('Okay, pulando até a posição que escolheu...')
        await vc.stop()

        for i in range(0,position):
          atual = vc.queue.current_track
          vc.queue.skip()
          vc.queue.add(atual[0], atual[1])

        await asyncio.sleep(0.5)
        await vc.start_playing()
        return
        
      else:
        await ctx.send('Operação cancelada! :robot: bep bop')
        return
    
    if position == 1:
      self.pular(ctx)
      return
    
    await vc.stop()

    for i in range(0,position):
      vc.queue.skip()

    await asyncio.sleep(0.5)
    await vc.start_playing()
    await ctx.send(f"Queue skipada para posição `{position}. {vc.queue.current_track[0].title}`")

# =======================================================================================================

  @commands.command(aliases=['seek'], help='Vai para o minuto da música que comandar (no modelo horas:minutos:segundos)', description='.tempo <horas:minutos:segundos / minutos:segundos>')
  async def tempo(self, ctx, *, tempo):
    vc: Player = ctx.voice_client

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
    
    if tempoML > vc.queue.current_track[0].length:
      await ctx.send('Tempo maior que a duração do video! :skull:')
      return

    await vc.seek(tempoML)

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
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    if posição > vc.queue.length or posição <= 0:
      await ctx.send(':warning: Erro: Número invalido!')
      return
    
    await ctx.send(f'O video `{vc.queue.remove_track(posição)[0].title}`, foi removido com sucesso da queue!')

# =======================================================================================================
  
  @commands.command(aliases=['v'], help='Muda o volume da música! O volume vai de 0 até 1000 (cuidado 1000 é muito alto), sendo 100 o número padrão', description='.volume <número do volume>')
  async def volume(self, ctx, *, vol : int):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    await vc.set_volume(vol)


# =======================================================================================================
  @commands.command(aliases=['playskip' ,'ps' ,'ta'], help='Pula a música atual e imediatamente toca a música que comandar ignorando a queue', description='.tocaragora <link do video do youtube/termo pra pesquisar no youtube>')
  async def tocaragora(self, ctx, *, musica):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return
    
    if not vc.is_playing and not vc.is_paused:
      await ctx.send('Não tem nenhuma música tocando!') 
      return

    await vc.stop()

    # pega o tipo de str que o usuario mando
    tipo = identifica(musica)
    
    # dependendo do tipo da str o bot faz algo diferente
    if tipo == 'pesquisa' or tipo == 'ytl':
      musica = await wavelink.YouTubeTrack.search(query=musica, return_first=True)
      if not musica:
        await ctx.send(':warning: Erro: sua música não foi encontrada')
        return
    elif tipo == 'ytp':
      await ctx.send("Desculpe mas esse comando não aceita playlist! :disguised_face:")
    elif tipo == 'sc':
      await ctx.send('Não tenho suporte pra soundcloud ainda! :skull:')
      return
    elif tipo is None:
      await ctx.send('Link invalido! Só aceito links do youtube ou termos de pesquisa! :disguised_face:')
      return

    vc.queue.skip()
    vc.queue.add_to_front(musica,ctx)

    await asyncio.sleep(0.5)
    await vc.start_playing()

    await ctx.send(f'Tocando `{vc.queue.current_track[0].title}` agora! No canal de voz `{vc.queue.current_track[1].author.voice.channel.name}` :musical_note:')

# =======================================================================================================
  @commands.command(aliases=['shuffle'], help='Embaralha as músicas da playlist')
  async def embaralhar(self, ctx):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu não estou em um canal de voz! :skull:')
      return

    if vc.queue.length <= 3:
      await ctx.send("Não tem música o suficiente para embaralhar a playlist! :zany_face:")
      return

    vc.queue.shuffle()
    await ctx.send("Queue foi embaralhada com sucesso! :robot:")

# =======================================================================================================
  @commands.Cog.listener()
  async def on_voice_state_update(self, member, before, after):
    if not member.bot:
      return
    
    elif not member.id == self.bot.user.id:
      return
    
    elif before.mute == False and after.mute == True:
      vc: Player = after.channel.guild.voice_client
      await vc.set_pause(True)
      return
    
    elif before.mute == True and after.mute == False:
      vc: Player = after.channel.guild.voice_client
      await vc.set_pause(False)
      return
    
    elif not before.channel is None and not after.channel is None:
      vc: Player = after.channel.guild.voice_client
      await vc.set_pause(True)
      await asyncio.sleep(0.5)
      await vc.set_pause(False)
      return

    elif before.channel is None:
      vc: Player = after.channel.guild.voice_client
      time = 0
      while True:
        await asyncio.sleep(1)
        time = time + 1
        if vc.is_playing() and not vc.is_paused():
          time = 0
        if time == 600:
          await vc.teardown() #if not it disconnects
          break
        if vc is None:
          break
      return
    
    elif after.channel is None:
      vc: Player = before.channel.guild.voice_client
      if vc:
        await vc.teardown()

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

    
    if musica.length >= 3600:
      duração = time.strftime('%H:%M:%S', time.gmtime(musica.length))
    else:
      duração = time.strftime('%M:%S', time.gmtime(musica.length))
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


    musicas = "`Música atual:`" + f"[{queues[0][0].title}]({queues[0][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[0][0].length))}` | pedida por `{queues[0][1].author.name}`" + "\n \n"

    for i in range(1, len(queues)):
            
      if i % 10 == 0 or i == len(queues) - 1:
        musicas = musicas + f'`{i}.`' + f"[{queues[i][0].title}]({queues[i][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[i][0].length))}` | pedida por `{queues[i][1].author.name}`" + '\n \n' 
        musicas = musicas + f'{len(queues) - 1} músicas na playlist | Tempo total: {duração}'

        embed = Embed(title='Músicas na playlist :disguised_face:', description=musicas, colour=0xFF0080)

        embed.set_footer(text=f'página {len(lista_embeds)+ 1} de {(len(queues) - (len(queues) % 10)) / 10 + 1:.0f}')
        lista_embeds.append(embed)
        musicas = ''
          
      elif i % 10 != 0:
        musicas = musicas + f'`{i}.`' + f"[{queues[i][0].title}]({queues[i][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[i][0].length))}` | pedida por `{queues[i][1].author.name}`" + '\n \n'


    if len(lista_embeds) > 1:
      paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx)
      paginator.add_reaction('◀', "back")
      paginator.add_reaction('▶', "next")

      await paginator.run(lista_embeds)
    else:
      await ctx.send(embed=lista_embeds[0])


async def setup(client):
  await client.add_cog(Musicas(client))
      