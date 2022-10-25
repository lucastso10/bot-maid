import discord
import wavelink
from discord.ext import commands
from discord import Embed
import time
import DiscordUtils
import asyncio

queues = {}

loop = {}

class Musicas(commands.Cog, description='Músicas :musical_note:'):
    def __init__(self, bot):
        self.bot = bot

        self.bot.loop.create_task(self.start_nodes())


    async def start_nodes(self):
        node = await wavelink.NodePool.create_node(bot=self.bot,
                                              host='lavalink-replit.bolofofodoidao.repl.co',
                                              port=443,
                                              password='penishaha',
                                              https=True)
    
# =======================================================================================================
    # toca a proxima musica quando a atual acabar
    @commands.Cog.listener()
    async def  on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if reason == 'FINISHED':
            if loop[player.guild.id]:
                atual = queues[player.guild.id][0]
                queues[player.guild.id].append(atual)

            queues[player.guild.id].pop(0)
            if queues[player.guild.id]:
                await player.play(queues[player.guild.id][0]['track'])

  # =======================================================================================================
    @commands.Cog.listener() # quando o node estiver pronto printar informando
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node {node.identifier} está conectado!")
  
  # =======================================================================================================
    @commands.Cog.listener() # printa erro e skipa musica
    async def on_wavelink_track_exception(self, player: wavelink.Player, track: wavelink.Track, error):
        await queues[player.guild_id][0]['ctx'].send(f":warning: Falha ao tocar a musica {queues[player.guild_id][0]['track']}! Pulando para a proxima! wavelink.TrackExeception")

        queues[player.guild_id].pop(0)
        if len(queues[player.guild_id]) != 0:
            await player.play(queues[player.guild_id][0]['track'])

  # =======================================================================================================
    @commands.Cog.listener() # printa erro e skipa a musica
    async def on_wavelink_track_stuck(self, player: wavelink.Player, track: wavelink.Track, threshold):
        await queues[player.guild_id][0]['ctx'].send(f":warning: Falha ao tocar a musica {queues[player.guild_id][0]['track']}! Pulando para a proxima! wavelink.TrackStuck")
            
        queues[player.guild_id].pop(0)
        if len(queues[player.guild_id]) != 0:
            await player.play(queues[player.guild_id][0]['track'])


  # =======================================================================================================
    # toca a musica no bot se ele n estiver conectado ele conecta no chat de voz e toca ou link do youtube ou
    # pesquisa o que foi dado no youtube
    # se o bot já estiver tocando algo o parametro do comando vai para a fila
    @commands.command(aliases=['t','play','p'], help='Toca vídeos do youtube no canal de voz que você está conectado', description='.tocar <link do video do youtube/termo pra pesquisar no youtube>')
    async def tocar(self, ctx, *, musica: str):
        vc: wavelink.Player = ctx.voice_client
        
        # conecta no canal de voz
        if not vc:

            if ctx.author.voice is None:
                await ctx.send('Você não está conectado a nenhum canal de voz! :skull:')
                return
            
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

            if ctx.guild.id in queues:
                queues[ctx.guild.id].clear()

        #else:
            #if player.channel_id != ctx.message.author.voice.channel.id:
                #await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
                #return
            # esse codigo n funciona mais, porque player.channel_id não é mais valido
        
        if not ctx.guild.id in loop: # jeito bem pesado de fazer isso
            loop[ctx.guild.id] = False

        #coloca o server na lista de queues
        if not ctx.guild.id in queues:
            queues[ctx.guild.id] = ['']
            queues[ctx.guild.id].pop(0)

        # pega o tipo de str que o usuario mando
        tipo = await Identificador.identifica(link=musica) # rever !!!
        
        # dependendo do tipo da str o bot faz algo diferente
        if tipo == 'pesquisa': # link do youtube e pesquisa são o mesmo comando da pra juntar
            musica = await wavelink.YouTubeTrack.search(query=musica, return_first=True)
            if not musica:
                await ctx.send(':warning: Erro: sua música não foi encontrada')
                return
        elif tipo == 'ytl':
            musica = await wavelink.YouTubeTrack.search(query=musica, return_first=True)
            if not musica:
                await ctx.send(':warning: Erro: sua música não foi encontrada')
                return
        #elif tipo == 'ytp':                                             codigo de playlist
           # playlist = await self.bot.wavelink.get_tracks(musica)
            #musicas = playlist.tracks
           # if not musicas:
           #     await ctx.send(':warning: Erro: sua música não foi encontrada')
           #     return
           # embed = await mensagemBunita.playlist(ctx=ctx, playlist=playlist, first=musicas[0])
           # await ctx.send(embed=embed)
        elif tipo == 'sc':
            await ctx.send('Não tenho suporte pra soundcloud ainda! :skull:')
            return
        elif tipo is None:
            await ctx.send(f'Link invalido! Só aceito links do youtube ou termos de pesquisa! :disguised_face:')
            return

        #adiciona a musica a playlist 
        #if tipo != 'ytp': 
            #if len(queues[ctx.guild.id]) <= 1000:
                #musica = musicas[0]
                #content = {'track' : musica, 'ctx' : ctx ,'tipo' : tipo}
                #queues[ctx.guild.id].append(content)
           # else:
               # await ctx.send(':warning: Você alcançou o limite de 5000 musicas por queue! Música não adicionada! :skull:')
                #return
        #else:
        if len(queues[ctx.guild.id]) <= 1000:
            content = {'track' : musica, 'ctx' : ctx ,'tipo' : tipo}
            queues[ctx.guild.id].append(content)
        else:
            await ctx.send(':warning: Você alcançou o limite de 1000 musicas por queue! Música não adicionada! :skull:')
            return

        print(f"player da guilda {vc.guild.name} tocando = {vc.is_playing()} pausado = {vc.is_paused()}")

        if vc.is_playing() and not vc.is_paused():
            embed = await mensagemBunita.musicaQueue(ctx=ctx, musica=queues[ctx.guild.id][len(queues[ctx.guild.id]) - 1]['track'], posição=len(queues[ctx.guild.id]) - 1)
            await ctx.send(embed=embed)
            return

        await vc.play(queues[ctx.guild.id][0]['track'])

        await ctx.send(f'Tocando `{queues[ctx.guild.id][0]["track"]}` agora! No canal de voz `{ctx.author.voice.channel.name}` :musical_note:')

# =======================================================================================================
    # mostra a musica que está tocando atualmente
    # a thumb do yt
    # o tempo do video que está e o tempo máximo
    @commands.command(aliases=['np', 'tc', 'nowPlaying'], help='mostra a musica que está sendo tocada agora')
    async def tocandoagora(self, ctx):
        player = wavelink.player

        #verifica se o bot ta em um canal de voz
        if not player.is_connected:
            await ctx.send('Eu não estou em um canal de voz! :skull:')
            return

        # verifica se o bot ta tocando alguma coisa
        elif not player.is_playing and not player.is_paused and not queues[ctx.guild.id]:
            await ctx.send('Não tô tocando nada')
            return
        
        # cria o embed e manda
        embed = await mensagemBunita.musicayt(ctx=ctx, musica=queues[ctx.guild.id][0]['track'], player=player)
        await ctx.send(embed=embed)

# =======================================================================================================
    # pausa a musica que estiver tocando
    @commands.command(aliases=['pause'], help='Pausa a música que está tocando')
    async def pausar(self, ctx):
        player = wavelink.player

        #verifica se o bot ta conectado no canal de voz
        if not player.is_connected:
            await ctx.send('Não to conectado a nenhum canal de voz!')

        #verifica se o usuario que invoco tá em um canal de voz em primeiro lugar
        elif ctx.message.author.voice is None:
            await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')

        #verifica se o usuario que invoco tá no mesmo canal de voz que o bot
        #elif player.channel_id != ctx.message.author.voice.channel.id:
            #await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
          # player.channel_id n funciona mais
        
        #verifica se o player ta tocando musica se sim ele pausa
        elif player.is_playing:
            await player.set_pause(True)
            await ctx.send('Música pausada! :thumbsup:')
        
        #verifica se o player já ta pausado
        elif player.is_paused:
            await ctx.send('A música ja está pausada')
        
        #a ultima opção é o bot não ta tocando nada
        else:
            await ctx.send('Não tem nenhuma música tocando')

  # =======================================================================================================
    # verifica se tem uma musica pausada e continua ela se houver
    @commands.command(aliases=['resume', 'continuar', 'resumir'], help='despausa a musica se ela foi pausada')
    async def despausar(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)

        #verifica se o bot ta conectado no canal de voz
        if not player.is_connected:
            await ctx.send('Não estou conectado a nenhum canal de voz')

        #verifica se o usuario que invoco tá em um canal de voz em primeiro lugar
        elif ctx.message.author.voice is None:
            await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
        
        #verifica se o usuario que invoco tá no mesmo canal de voz que o bot
        #elif player.channel_id != ctx.message.author.voice.channel.id :
            #await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
        # player.channel_id n funciona mais
        
        #verifica se o player ta pausado se sim ele despausa
        elif player.is_paused:
            await player.set_pause(False)
            await ctx.send('Música despausada! :thumbsup:')
        
        #verifica se o player ta tocando
        elif player.is_playing:
            await ctx.send('A música já está tocando! :musical_note:')
        
        #a ultima opção é o bot não ta tocando nada
        else:
            await ctx.send('não tem nenhuma musica tocando! :skull:')

 # =======================================================================================================
    # pula para proxima música da fila
    @commands.command(aliases=['s', 'skip', 'skipar'], help='Pula para a próxima música da playlist e se não tiver nenhuma só não toca nada')
    async def pular(self, ctx):
        player = wavelink.player

        #verifica se o bot ta conectado no canal de voz
        if not player.is_connected:
            await ctx.send('Eu não estou em um canal de voz')
            return

        #verifica se o usuario que invoco tá em um canal de voz em primeiro lugar
        elif ctx.message.author.voice is None:
            await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
            return
        
        #verifica se o usuario que invoco tá no mesmo canal de voz que o bot
        #elif player.channel_id != ctx.message.author.voice.channel.id:
            #await ctx.send('Desculpa mas você não está no mesmo canal de voz que eu estou! sucumba :skull:')
            #return
        # player.channel_id n funfa mais carai
        
        if not player.is_playing and not player.is_paused:
            await ctx.send('Eu não to tocando nada')
            return
        
        atual = []
        
        if loop[ctx.guild.id]:
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content == '1' or m.content == '2' or m.content == '3'

            await ctx.send('A playlist está trancada! :lock: Porque o loop está ativo! Se você realmente quer usar esse comando escolha uma dessas 2 opções (responda com o número da opção que escolher) \n `1. pular a música atual sem remove-lá do loop` \n `2. pular a música atual e remove-lá do loop` \n `3. cancelar`')
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send('Desculpa mas você demorou muito para responder, video não removido!')
                return
                
            if msg.content == '1':
                await ctx.send('Okay, pulando a música e mantendo a no loop...')
                atual.append(queues[ctx.guild.id][0])
            
            elif msg.content == '2':
                await ctx.send('Okay, pulando a música e removendo ela do loop...')

            else:
                await ctx.send('Operação cancelada! :robot: bep bop')
                return
        
        await player.stop()
        await ctx.send('Música skipada! :thumbsup:')
        queues[ctx.guild.id].pop(0)
        if atual:
            queues[ctx.guild.id].append(atual[0])
        if queues[ctx.guild.id]:
            await player.play(queues[ctx.guild.id][0]['track'])

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
        
        if not queues[ctx.guild.id]:
            await ctx.send('Não tem nenhuma música na playlist!')
            return

        if len(queues[ctx.guild.id]) == 1:
            await self.tocandoagora(ctx=ctx)
            return

        await mensagemBunita.Queue(queues=queues[ctx.guild.id], ctx=ctx)


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
    
    @commands.command(name='loop', help='Tranca a playlist atual e loopa ela (para desativar esse comando é só usar ele denovo)')
    async def loop_command(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.is_connected:
            await ctx.send('Eu não estou em um canal de voz! :skull:')
            return

        if ctx.message.author.voice is None:
            await ctx.send('Você nem ta em um canal de voz... sucumba :skull:')
            return

        if not player.is_playing and not player.is_paused:
            await ctx.send('Não tô tocando nada')
            return
        
        if loop[ctx.guild.id]:
            loop[ctx.guild.id] = False
            estado = 'desativado'
            await ctx.send('Loop desativado! :no_mouth:')

        elif not loop[ctx.guild.id]:
            loop[ctx.guild.id] = True
            estado = 'ativado'
            await ctx.send('Loop ativado!!! :repeat: :grinning:')
        else:
            await ctx.send(':warning: Erro! O estado do loop não foi alterado!')


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
    
class Identificador():

    async def identifica(link):

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

class mensagemBunita():

    async def playlist(ctx, playlist, first):
        data = playlist.data

        embed = Embed(title='Playlist adicionada a playlist do server! :thumbsup:', 
        description=f"{data['playlistInfo']['name']}", 
        colour=0xFF0080)

        duração = 0
        for i in range(0,len(data['tracks'])):
            duração = duração + data['tracks'][i]['info']['length'] /1000
        
        duração = time.strftime('%M:%S', time.gmtime(duração))

        embed.add_field(name='Duração total', 
        value=f"{duração}")

        embed.add_field(name='Músicas adicionadas',
        value=f"`{len(data['tracks'])}`",
        inline=True)
            
        embed.set_author(name='Pediu essa', 
        icon_url=ctx.author.avatar_url)

        embed.set_thumbnail(url=first.thumb)

        return embed

    async def musicayt(ctx, musica, player):
        embed = Embed(title=musica.title, url=f"https://www.youtube.com/watch?v={musica.ytid}", colour=0xFF0080)

        if musica.duration >= 3600000000:
            duração = time.strftime('%H:%M:%S', time.gmtime(musica.duration/1000))
            posição = time.strftime('%H:%M:%S', time.gmtime(player.position/1000))
        else:    
            duração = time.strftime('%M:%S', time.gmtime(musica.duration/1000))
            posição = time.strftime('%M:%S', time.gmtime(player.position/1000))

        string_tempo = f'`{posição}\{duração}`'
        if musica.is_stream:
            string_tempo = '`Ao vivo`'
        embed.add_field(name='Duração', value=string_tempo)
        embed.add_field(name='Canal', value=f"`{musica.author}`")
        embed.set_author(name='Pediu essa', icon_url=ctx.author.avatar_url)
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
        for i in range(0,len(queues)):
            duração = duração + queues[i]['track'].duration /1000
        
        duração = time.strftime('%M:%S', time.gmtime(duração))


        musicas = '`Música atual:`' + f"[{queues[0]['track'].title}](https://www.youtube.com/watch?v={queues[0]['track'].ytid}) | `{time.strftime('%M:%S', time.gmtime(queues[0]['track'].duration / 1000))}`" + '\n \n'

        for i in range(1, len(queues)):
                
            if i % 10 == 0 or i == len(queues) - 1:
                musicas = musicas + f'`{i}.`' + f"[{queues[i]['track'].title}](https://www.youtube.com/watch?v={queues[i]['track'].ytid}) | `{time.strftime('%M:%S', time.gmtime(queues[i]['track'].duration / 1000))}`" + '\n \n' 
                musicas = musicas + f'{len(queues) - 1} músicas na playlist | Tempo total: {duração}'

                embed = Embed(title='Músicas na playlist :disguised_face:', description=musicas, colour=0xFF0080)

                embed.set_footer(text=f'página {len(lista_embeds)+ 1} de {(len(queues) - (len(queues) % 10)) / 10 + 1:.0f}')
                lista_embeds.append(embed)
                musicas = ''
                
            elif i % 10 != 0:
                musicas = musicas + f'`{i}.`' + f"[{queues[i]['track'].title}](https://www.youtube.com/watch?v={queues[i]['track'].ytid}) | `{time.strftime('%M:%S', time.gmtime(queues[i]['track'].duration / 1000))}`" + '\n \n'


        if len(lista_embeds) > 1:
            paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx)
            paginator.add_reaction('◀', "back")
            paginator.add_reaction('▶', "next")

            await paginator.run(lista_embeds)
        else:
            await ctx.send(embed=lista_embeds[0])


async def setup(client):
    await client.add_cog(Musicas(client))
        