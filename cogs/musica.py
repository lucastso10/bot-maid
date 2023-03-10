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




      

class Musicas(commands.Cog, description='M??sicas :musical_note:'):
  
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
    print(f"Node {node.identifier} est?? conectado!")
  
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
  # se o bot j?? estiver tocando algo o parametro do comando vai para a fila
  @commands.command(aliases=['t','play','p'], help='Toca v??deos do youtube no canal de voz que voc?? est?? conectado', description='.tocar <link do video do youtube/termo pra pesquisar no youtube>')
  async def tocar(self, ctx,*, musica: str):
    vc: Player = ctx.voice_client
    
    # conecta no canal de voz
    if not vc:
      if ctx.author.voice is None:
        await ctx.send('Voc?? n??o est?? conectado a nenhum canal de voz! :skull:')
        return
      vc: Player = await ctx.author.voice.channel.connect(cls=Player)
    else:
      if ctx.author.voice.channel.id != ctx.message.author.voice.channel.id:
        await ctx.send('Desculpa mas voc?? n??o est?? no mesmo canal de voz que eu estou! sucumba :skull:')
        return

    # pega o tipo de str que o usuario mando
    tipo = identifica(musica)
    
    # dependendo do tipo da str o bot faz algo diferente
    if tipo == 'pesquisa' or tipo == 'ytl': # link do youtube e pesquisa s??o o mesmo comando da pra juntar
      musica = await wavelink.YouTubeTrack.search(query=musica, return_first=True)
      if not musica:
        await ctx.send(':warning: Erro: sua m??sica n??o foi encontrada')
        return
    elif tipo == 'ytp':
      playlist = await wavelink.YouTubePlaylist.search(query=musica)
      musicas = playlist.tracks
      if not musicas:
        await ctx.send(':warning: Erro: sua m??sica n??o foi encontrada')
        return
      embed = await mensagemBunita.playlist(ctx=ctx, playlist=playlist)
      await ctx.send(embed=embed)
    elif tipo == 'sc':
      await ctx.send('N??o tenho suporte pra soundcloud ainda! :skull:')
      return
    elif tipo is None:
      await ctx.send(f'Link invalido! S?? aceito links do youtube ou termos de pesquisa! :disguised_face:')
      return

    #adiciona a musica a playlist 
    if tipo == 'ytp':
      for musica in musicas:
        vc.queue.add(musica, ctx)
    elif musica == None:
      ctx.send("Desculpa mas n??o encontrei essa musica! :disguised_face:")
    else:
      vc.queue.add(musica, ctx)

    # se o bot estiver tocando algo j?? ele s?? manda uma mensagem falando que adiciono na playlist
    if vc.is_playing() and not vc.is_paused():
      embed = await mensagemBunita.musicaQueue(ctx=ctx, musica=musica, posi????o=vc.queue.length)
      await ctx.send(embed=embed)
      return

    await vc.start_playing()

    await ctx.send(f'Tocando `{vc.queue.current_track[0].title}` agora! No canal de voz `{vc.queue.current_track[1].author.voice.channel.name}` :musical_note:')

# =======================================================================================================
  # mostra a musica que est?? tocando atualmente
  # a thumb do yt
  # o tempo do video que est?? e o tempo m??ximo
  @commands.command(aliases=['np', 'tc', 'nowPlaying'], help='mostra a musica que est?? sendo tocada agora')
  async def tocandoagora(self, ctx):
    vc: Player = ctx.voice_client

    #verifica se o bot ta em um canal de voz
    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
      return

    # verifica se o bot ta tocando alguma coisa
    elif not vc.is_playing and not vc.is_paused:
      await ctx.send('N??o t?? tocando nada!')
      return
    
    # cria o embed e manda
    embed = await mensagemBunita.musicayt(ctx=vc.queue.current_track[1], musica=vc.queue.current_track[0], player=vc)
    await ctx.send(embed=embed)

# =======================================================================================================
  # pausa a musica que estiver tocando
  @commands.command(aliases=['pause'], help='Pausa a m??sica que est?? tocando')
  async def pausar(self, ctx):
    vc: Player = ctx.voice_client

    #verifica se o bot ta conectado no canal de voz / ta no mesmo canal que o autor / se o autor ta em um canal de voz
    if not vc:
      await ctx.send('N??o to conectado a nenhum canal de voz!')
    
    #verifica se o player ta tocando musica se sim ele pausa
    elif vc.is_playing():
      await vc.set_pause(True)
      await ctx.send('M??sica pausada! :thumbsup:')
    
    #verifica se o player j?? ta pausado
    elif vc.is_paused():
      await ctx.send('A m??sica ja est?? pausada')
    
    #a ultima op????o ?? o bot n??o ta tocando nada
    else:
      await ctx.send('N??o tem nenhuma m??sica tocando')

# =======================================================================================================
  # verifica se tem uma musica pausada e continua ela se houver
  @commands.command(aliases=['resume', 'continuar', 'resumir'], help='despausa a musica se ela foi pausada')
  async def despausar(self, ctx):
    vc: Player = ctx.voice_client

    #verifica se o bot ta conectado no canal de voz
    if not vc:
      await ctx.send('N??o estou conectado a nenhum canal de voz')
    
    #verifica se o player ta pausado se sim ele despausa
    elif vc.is_paused():
      await vc.set_pause(False)
      await ctx.send('M??sica despausada! :thumbsup:')
    
    #verifica se o player ta tocando
    elif vc.is_playing():
      await ctx.send('A m??sica j?? est?? tocando! :musical_note:')
    
    #a ultima op????o ?? o bot n??o ta tocando nada
    else:
      await ctx.send('n??o tem nenhuma musica tocando! :skull:')

# =======================================================================================================
  # pula para proxima m??sica da fila se o loop estiver ativado pergunta se quer realmente remove
  @commands.command(aliases=['s', 'skip', 'skipar'], help='Pula para a pr??xima m??sica da playlist e se n??o tiver nenhuma s?? n??o toca nada')
  async def pular(self, ctx):
    vc: Player = ctx.voice_client
    #verifica se o bot ta conectado no canal de voz
    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
      return
    
    if not vc.is_playing() and not vc.is_paused():
      await ctx.send('Eu n??o to tocando nada')
      return
    
    if vc.queue.loop == Loop.List:
        
      def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == '1' or m.content == '2' or m.content == '3'

      await ctx.send('A playlist est?? trancada! :lock: Porque o loop est?? ativo! Se voc?? realmente quer usar esse comando escolha uma dessas 2 op????es (responda com o n??mero da op????o que escolher) \n `1. pular a m??sica atual sem remove-l?? do loop` \n `2. pular a m??sica atual e remove-l?? do loop` \n `3. cancelar`')
      try:
        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa mas voc?? demorou muito para responder, nada foi feito!')
        return
          
      if msg.content == '1':
        await ctx.send('Okay, pulando a m??sica e mantendo a no loop...')
      
      elif msg.content == '2':
        await ctx.send('Okay, pulando a m??sica e removendo ela do loop...')
        await vc.stop()
        vc.queue.set_loop("NONE")
        await asyncio.sleep(0.5)
        await vc.start_next()
        vc.queue.set_loop("LIST")
        return

      else:
        await ctx.send('Opera????o cancelada! :robot: bep bop')
        return
    
    await vc.stop()
    await ctx.send('M??sica skipada! :thumbsup:')
    await asyncio.sleep(0.5)
    await vc.start_next()

# =======================================================================================================
  # faz o bot sair do canal de voz e destroi o player
  @commands.command(aliases=['stop', 'leave', 'sair'], help='Faz o bot sair do canal de voz e limpa a playlist')
  async def parar(self, ctx):
    vc: Player = ctx.voice_client

     #verifica se o bot ta conectado no canal de voz
    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
    
     #verifica se o usuario que invoco t?? em um canal de voz em primeiro lugar
    elif ctx.message.author.voice is None:
      await ctx.send('Voc?? nem ta em um canal de voz... sucumba :skull:')
    
    #se o bot tiver conectado ao canal de voz ele ele quita e limpa a queue
    elif vc.is_connected():
      await vc.disconnect()
      await vc.teardown()
      await ctx.send('ta parei')

# =======================================================================================================
  # limpa todas as m??sicas da playlist
  @commands.command(aliases=['clear'], help='Limpa todas as m??sicas da playlist')
  async def limpar(self, ctx):
    vc: Player = ctx.voice_client
    if vc.queue.loop == Loop.List:
        
      def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['s', 'n', 'sim', 'nao']

      await ctx.send('A playlist est?? trancada! :lock: Porque o loop est?? ativo! Voc?? quer mesmo fazer isso? (responda com S ou N)')
      try:
        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa mas voc?? demorou muito para responder, a playlist n??o foi limpada!')
            
      if msg.content.lower() == 's' or msg.content.lower() == 'sim':
        await ctx.send('Okay, limpando playlist...')
      else:
        await ctx.send('Playlist n??o limpada!')
        return
    
    vc.queue.clear()
    await ctx.send('Queue limpada! :thumbsup:')

# =======================================================================================================
  # mostra todas as m??sicas da playlist
  @commands.command(hidden=True, help='Mostra todas as m??sicas que est??o na playlist')
  async def printlist(self, ctx):
    vc: Player = ctx.voice_client
    print(vc.queue.playlist)

# =======================================================================================================
  # mostra todas as m??sicas da playlist
  @commands.command(aliases=['queue'], help='Mostra todas as m??sicas que est??o na playlist')
  async def playlist(self, ctx):
    vc: Player = ctx.voice_client
    
    if not vc or vc.queue.is_empty:
      await ctx.send('N??o tem nenhuma m??sica na playlist!')
      return

    if vc.queue.length == 1:
      await self.tocandoagora(ctx)
      return

    await mensagemBunita.Queue(queues=vc.queue.playlist, ctx=ctx)


# =======================================================================================================
  #
  @commands.command(aliases=['skipto', 'sp', 'st', 'skiparpara'], help='Pula para o n??mero da playlist mandado', description='.pularpara <posi????o da playlist>')
  async def pularpara(self, ctx, *, position: int):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
      return
    
    elif not vc.is_playing() and not vc.is_paused():
      print(f"is_playing = {vc.is_playing()} and is_paused: {vc.is_paused()}")
      await ctx.send('N??o t?? tocando nada')
      return
  
    elif vc.queue.length <= 2:
      await ctx.send('N??o h?? musicas o suficiente na playlist para executar esse comando! :skull:')
      return

    elif vc.queue.length < position:
      await ctx.send("A posi????o dada excede o n??mero de m??sicas na playlist! :disguised_face:")

    elif vc.queue.loop == Loop.List:
      
      def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == '1' or m.content == '2' or m.content == '3'

      await ctx.send('A playlist est?? trancada! :lock: Porque o loop est?? ativo! Se voc?? realmente quer usar esse comando escolha uma dessas 2 op????es (responda com o n??mero da op????o que querer) \n `1. remover todas as m??sicas at?? a posi????o da queue que escolheu` \n `2. ir at?? a posi????o da queue que escolheu sem remover as m??sicas do loop` \n `3. cancelar`')
      try:
        msg = await self.bot.wait_for('message', check=check, timeout=30.0)
      except asyncio.TimeoutError:
        await ctx.send('Desculpa mas voc?? demorou muito para responder, nada foi feito!')
        return
          
      if msg.content == '1':
        await ctx.send('Okay, removendo as m??sicas...')
        
      elif msg.content == '2':
        await ctx.send('Okay, pulando at?? a posi????o que escolheu...')
        await vc.stop()

        for i in range(0,position):
          atual = vc.queue.current_track
          vc.queue.skip()
          vc.queue.add(atual[0], atual[1])

        await asyncio.sleep(0.5)
        await vc.start_playing()
        return
        
      else:
        await ctx.send('Opera????o cancelada! :robot: bep bop')
        return
    
    if position == 1:
      self.pular(ctx)
      return
    
    await vc.stop()

    for i in range(0,position):
      vc.queue.skip()

    await asyncio.sleep(0.5)
    await vc.start_playing()
    await ctx.send(f"Queue skipada para posi????o `{position}. {vc.queue.current_track[0].title}`")

# =======================================================================================================

  @commands.command(aliases=['seek'], help='Vai para o minuto da m??sica que comandar (no modelo horas:minutos:segundos)', description='.tempo <horas:minutos:segundos / minutos:segundos>')
  async def tempo(self, ctx, *, tempo):
    vc: Player = ctx.voice_client

    verifica????o = tempo.split(':')
    
    if len(verifica????o) == 2:
      try:
        tempoML = int(verifica????o[0]) * 60 + int(verifica????o[1])
        tempoML = int(tempoML * 1000)
      except:
        await ctx.send('Tempo inv??lido!')
        return
    elif len(verifica????o) == 3:
      try:
        tempoML = int(verifica????o[0]) * 60 + int(verifica????o[1])
        tempoML = tempoML * 60 + int(verifica????o[2])
        tempoML = int(tempoML * 1000)
      except:
        await ctx.send('Tempo inv??lido!')
        return
    else:
      await ctx.send('Tempo inv??lido!')
      return
    
    if tempoML > vc.queue.current_track[0].length:
      await ctx.send('Tempo maior que a dura????o do video! :skull:')
      return

    await vc.seek(tempoML)

    await ctx.send(f'Video avan??ado para o tempo `{tempo}`! :thumbsup:')


# =======================================================================================================
  
  @commands.command(name='loop', help='Loopa uma m??sica ou a playlist toda! (pra desativar/trocar o modo use o comando novamente)')
  async def loop_command(self, ctx):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
      return

    if ctx.message.author.voice is None:
      await ctx.send('Voc?? nem ta em um canal de voz... sucumba :skull:')
      return

    if not vc.is_playing and not vc.is_paused:
      await ctx.send('N??o t?? tocando nada')
      return
    
    if vc.queue.loop == Loop.NONE:
      vc.queue.set_loop("SONG")
      await ctx.send("Loop ativado para a m??sica atual! :repeat_one:")
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
  @commands.command(aliases=['remove'], help='remove uma m??sica na posi????o comandar', description='.remover <posi????o da playlist>')
  async def remover(self, ctx, *, posi????o : int):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
      return

    if posi????o > vc.queue.length or posi????o <= 0:
      await ctx.send(':warning: Erro: N??mero invalido!')
      return
    
    await ctx.send(f'O video `{vc.queue.remove_track(posi????o)[0].title}`, foi removido com sucesso da queue!')

# =======================================================================================================
  
  @commands.command(aliases=['v'], help='Muda o volume da m??sica! O volume vai de 0 at?? 1000 (cuidado 1000 ?? muito alto), sendo 100 o n??mero padr??o', description='.volume <n??mero do volume>')
  async def volume(self, ctx, *, vol : int):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
      return

    await vc.set_volume(vol)


# =======================================================================================================
  @commands.command(aliases=['playskip' ,'ps' ,'ta'], help='Pula a m??sica atual e imediatamente toca a m??sica que comandar ignorando a queue', description='.tocaragora <link do video do youtube/termo pra pesquisar no youtube>')
  async def tocaragora(self, ctx, *, musica):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
      return
    
    if not vc.is_playing and not vc.is_paused:
      await ctx.send('N??o tem nenhuma m??sica tocando!') 
      return

    await vc.stop()

    # pega o tipo de str que o usuario mando
    tipo = identifica(musica)
    
    # dependendo do tipo da str o bot faz algo diferente
    if tipo == 'pesquisa' or tipo == 'ytl':
      musica = await wavelink.YouTubeTrack.search(query=musica, return_first=True)
      if not musica:
        await ctx.send(':warning: Erro: sua m??sica n??o foi encontrada')
        return
    elif tipo == 'ytp':
      await ctx.send("Desculpe mas esse comando n??o aceita playlist! :disguised_face:")
    elif tipo == 'sc':
      await ctx.send('N??o tenho suporte pra soundcloud ainda! :skull:')
      return
    elif tipo is None:
      await ctx.send('Link invalido! S?? aceito links do youtube ou termos de pesquisa! :disguised_face:')
      return

    vc.queue.skip()
    vc.queue.add_to_front(musica,ctx)

    await asyncio.sleep(0.5)
    await vc.start_playing()

    await ctx.send(f'Tocando `{vc.queue.current_track[0].title}` agora! No canal de voz `{vc.queue.current_track[1].author.voice.channel.name}` :musical_note:')

# =======================================================================================================
  @commands.command(aliases=['shuffle'], help='Embaralha as m??sicas da playlist')
  async def embaralhar(self, ctx):
    vc: Player = ctx.voice_client

    if not vc:
      await ctx.send('Eu n??o estou em um canal de voz! :skull:')
      return

    if vc.queue.length <= 3:
      await ctx.send("N??o tem m??sica o suficiente para embaralhar a playlist! :zany_face:")
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

    dura????o = 0
    for musica in playlist.tracks:
      dura????o = dura????o + musica.length

    if not dura????o >= 3600:
      dura????o = time.strftime('%M:%S', time.gmtime(dura????o))
    else:
      dura????o = time.strftime('%H:%M:%S', time.gmtime(dura????o))

    embed.add_field(name='Dura????o total', 
    value=f"`{dura????o}`")

    embed.add_field(name='M??sicas adicionadas',
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
        dura????o = time.strftime('%H:%M:%S', time.gmtime(musica.length))
        posi????o = time.strftime('%H:%M:%S', time.gmtime(player.position))
      else:    
        dura????o = time.strftime('%M:%S', time.gmtime(musica.length))
        posi????o = time.strftime('%M:%S', time.gmtime(player.position))

      string_tempo = f'`{posi????o}\{dura????o}`'
    
    embed.add_field(name='Dura????o', value=string_tempo)
    embed.add_field(name='Canal', value=f"`{musica.author}`")
    embed.set_author(name='Pediu essa', icon_url=ctx.author.display_avatar)
    embed.set_thumbnail(url=musica.thumb)

    return embed
  
  async def musicaQueue(ctx, musica, posi????o):
    embed = Embed(title=musica.title, url=f"https://www.youtube.com/watch?v={musica.uri}", colour=0xFF0080)

    
    if musica.length >= 3600:
      dura????o = time.strftime('%H:%M:%S', time.gmtime(musica.length))
    else:
      dura????o = time.strftime('%M:%S', time.gmtime(musica.length))
    embed.add_field(name='Dura????o', value=f'`{dura????o}`')
    embed.add_field(name='Canal', value=f"`{musica.author}`")
    embed.add_field(name='Posi????o na playlist', value=f"`{posi????o}`", inline=False)
    embed.set_author(name='M??sica adicionada a playlist', icon_url=ctx.author.display_avatar)
    embed.set_thumbnail(url=musica.thumb)

    return embed
  
  async def Queue(queues, ctx):
      
    lista_embeds = []
    musicas = ''
    dura????o = 0
    for musica in queues:
      dura????o = dura????o + musica[0].length
    
    if not dura????o >= 3600:
      dura????o = time.strftime('%M:%S', time.gmtime(dura????o))
    else:
      dura????o = time.strftime('%H:%M:%S', time.gmtime(dura????o))


    musicas = "`M??sica atual:`" + f"[{queues[0][0].title}]({queues[0][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[0][0].length))}` | pedida por `{queues[0][1].author.name}`" + "\n \n"

    for i in range(1, len(queues)):
            
      if i % 10 == 0 or i == len(queues) - 1:
        musicas = musicas + f'`{i}.`' + f"[{queues[i][0].title}]({queues[i][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[i][0].length))}` | pedida por `{queues[i][1].author.name}`" + '\n \n' 
        musicas = musicas + f'{len(queues) - 1} m??sicas na playlist | Tempo total: {dura????o}'

        embed = Embed(title='M??sicas na playlist :disguised_face:', description=musicas, colour=0xFF0080)

        embed.set_footer(text=f'p??gina {len(lista_embeds)+ 1} de {(len(queues) - (len(queues) % 10)) / 10 + 1:.0f}')
        lista_embeds.append(embed)
        musicas = ''
          
      elif i % 10 != 0:
        musicas = musicas + f'`{i}.`' + f"[{queues[i][0].title}]({queues[i][0].uri}) | `{time.strftime('%M:%S', time.gmtime(queues[i][0].length))}` | pedida por `{queues[i][1].author.name}`" + '\n \n'


    if len(lista_embeds) > 1:
      paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx)
      paginator.add_reaction('???', "back")
      paginator.add_reaction('???', "next")

      await paginator.run(lista_embeds)
    else:
      await ctx.send(embed=lista_embeds[0])


async def setup(client):
  await client.add_cog(Musicas(client))
      