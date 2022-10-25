import discord
from discord.ext import commands
from discord import Embed

class Help(commands.Cog, description=''):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=['help'])
    async def ajuda(self, ctx, *input : str):
        owner = 'Bolofofodoidao#3095'

        if not input:

            embed = Embed(title='Categoria de comandos :thumbsup:', colour=0xFF0080, 
            description='Use `.ajuda <comando>` para receber mais informação sobre aquele comando :)')
            
            dict_cogs = self.bot.cogs

            for cog in self.bot.cogs:
                
                obj = dict_cogs[cog]
                commands_list = obj.get_commands()

                commands_string = ''
                for command in commands_list:

                    if command.hidden == False:
                        commands_string += '`' + command.name + '` | '

                if cog != 'Help':
                    embed.add_field(name=f'{obj.description}', value=f'{commands_string}', inline=False)
            
            embed.set_author(name=f'Esse bot foi feito por {owner}', icon_url=self.bot.user.display_avatar)

            await ctx.send(embed=embed)
            return
        else:
            input = input[0]
            comando_escolhido = ''
            dict_cogs = self.bot.cogs
            commands_list = []
            for cog in self.bot.cogs:
                obj_cog = dict_cogs[cog]
                commands_list = commands_list + obj_cog.get_commands()
            
            for i in range(0, len(commands_list)):
                
                if input.lower() == commands_list[i].name.lower():
                    comando_escolhido = commands_list[i]

            if comando_escolhido == '':
                await ctx.send('Comando não encontrado!')
                return
            
            aliases = comando_escolhido.aliases
            if aliases:
                if len(aliases) == 1:
                    texto = 'Outro jeito de usar esse comando é: '
                else:
                    texto = 'Outros jeito de usar esse comandos são: '
                for i in range(0, len(aliases)):
                    
                    if not i == len(aliases) - 1:
                        texto += aliases[i] + ', '
                    else:
                        texto += aliases[i]
            
            if aliases:
                embed = Embed(title=f'{comando_escolhido.name}' , description=f'{texto}', colour=0xFF0080)
            else:
                embed = Embed(title=f'{comando_escolhido.name}', colour=0xFF0080)
            embed.add_field(name='Como funciona:', value=f'{comando_escolhido.help}', inline=False)
            if not comando_escolhido.description == '':
                embed.add_field(name='Como utilizar:', value=f'{comando_escolhido.description}')
            embed.set_author(name=f'Esse bot foi feito por {owner}', icon_url=self.bot.user.display_avatar)

            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))