import discord
import logging
import re

from .utils import config
from .utils.allmsgs import quickcmds, custom
from .utils.checks import permEmbed, me
from datetime import datetime

log = logging.getLogger('LOG')


class OnMessage:
    def __init__(self, bot):
        self.bot = bot
        self.config = config.Config('config.json')
        self.logging = config.Config('log.json')

    async def on_message(self, message):
        # Increase Message Count
        if hasattr(self.bot, 'message_count'):
            self.bot.message_count += 1

        # Custom commands
        if me(message):
            if hasattr(self.bot, 'icount'):
                self.bot.icount += 1
            prefix = ''
            for i in self.config.get('prefix', []):
                if message.content.startswith(i):
                    prefix = i
                    break
            if prefix is not '':
                response = custom(prefix, message.content)
                if response is None:
                    pass
                else:
                    if response[0] == 'embed':
                        if permEmbed(message):
                            await message.edit(content='%s' % response[2], embed=discord.Embed(colour=discord.Color.purple()).set_image(url=response[1]))
                        else:
                            await message.edit('{0}\n{1}'.format(response[2], response[1]))
                    else:
                        await message.edit('{0}\n{1}'.format(response[2], response[1]))
                    self.bot.commands_triggered[response[3]] += 1
                    destination = None
                    if isinstance(message.channel, discord.DMChannel):
                        destination = 'Private Message'
                    else:
                        destination = '#{0.channel.name},({0.guild.name})'.format(message)
                    log.info('In {1}:{0.content}'.format(message, destination))
            else:
                response = quickcmds(message.content.lower().strip())
                if response:
                    self.bot.commands_triggered[response[1]] += 1
                    await message.edit(content=response[0])
                    destination = None
                    if isinstance(message.channel, discord.DMChannel):
                        destination = 'Private Message'
                    else:
                        destination = '#{0.channel.name},({0.guild.name})'.format(message)
                    log.info('In {1}:{0.content}'.format(message, destination))
        elif (message.guild is not None) and (self.config.get('setlog', []) == 'on'):
            if message.author.id in self.logging.get('block-user', []):
                return
            if message.channel.id in self.logging.get('block-channel', []):
                return
            if message.guild.id in self.logging.get('guild', []) or message.channel.id in self.logging.get('channel', []):
                msg = re.sub('[,.!?]', '', message.content.lower())
                if any(map(lambda v: v in msg.split(), self.logging.get('block-key', []))):
                    return
                notify = False
                if (message.guild.get_member(self.config.get('me', [])).mentioned_in(message)):
                    notify = True
                    if message.role_mentions != []:
                        em = discord.Embed(title='\N{SPEAKER WITH THREE SOUND WAVES} ROLE MENTION', colour=discord.Color.dark_blue())
                        log.info("Role Mention from #%s, %s" % (message.channel, message.guild))
                    else:
                        em = discord.Embed(title='\N{BELL} MENTION', colour=discord.Color.dark_gold())
                        log.info("Mention from #%s, %s" % (message.channel, message.guild))
                    if hasattr(self.bot, 'mention_count'):
                        self.bot.mention_count += 1
                else:
                    for word in self.logging.get('key', []):
                        if word in msg.split():
                            notify = True
                            em = discord.Embed(title='\N{HEAVY EXCLAMATION MARK SYMBOL} %s MENTION' % word.upper(), colour=discord.Color.dark_red())
                            log.info("%s Mention in #%s, %s" % (word.title(), message.channel, message.guild))
                            if hasattr(self.bot, 'mention_count_name'):
                                self.bot.mention_count_name += 1
                            break
                if notify:
                    em.set_author(name=message.author, icon_url=message.author.avatar_url)
                    em.add_field(name='In',
                                 value="#%s, ``%s``" % (message.channel, message.guild), inline=False)
                    em.add_field(name='At',
                                 value="%s" % datetime.now().__format__('%A, %d. %B %Y @ %H:%M:%S'), inline=False)
                    em.add_field(name='Message',
                                 value="%s" % message.clean_content, inline=False)
                    em.set_thumbnail(url=message.author.avatar_url)
                    await self.bot.get_channel(self.config.get('log_channel', [])).send(embed=em)

    async def on_message_edit(self, before, after):
        if me(before):
            if before.content != after.content:
                del before
                await self.on_message(after)
                await self.bot.process_commands(after)


def setup(bot):
    bot.add_cog(OnMessage(bot))
