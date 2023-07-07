import asyncio
import nextcord
from discord import FFmpegPCMAudio
from discord.ext import commands
from nextcord.utils import get
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch


bot = commands.Bot()
guilds = []
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1   -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
instances = {}
queues = {}


class Play(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label='Next', custom_id='next_btn')
    async def next_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await play_next(interaction)

    async def main_window(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.edit_message()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    for guild in bot.guilds:
        guilds.append(guild)


@bot.slash_command(description="next")
async def play_next(interaction: nextcord.Interaction):
    guild = interaction.guild
    await check_queue(guild.id, interaction)


loop = asyncio.get_event_loop()


@bot.slash_command(description="Play a song by name or link")
async def play(interaction: nextcord.Interaction, arg: str):
    if arg.__contains__(".com"):
        if arg.__contains__("youtube.com"):
            user = interaction.user
            guild = interaction.guild

            if not user.voice:
                await interaction.send("You are not connected to a voice channel!")
                return

            if not guild.id in instances:
                vc = await user.voice.channel.connect()
                instances[guild.id] = vc
            else:
                vc = instances[guild.id]

            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(arg, download=False)
                video_name = info.get('title')

                if guild.id in queues and queues[guild.id] != [] or vc.is_playing():
                    queues.setdefault(guild.id, []).append(info)
                    print(queues[guild.id])
                    await interaction.send('added to queue ')
                    view = Play()
                    queue = []
                    for song in queues[guild.id]:
                        queue.append(song.get('title') + '\n')
                    await interaction.send(
                        "added " + video_name + " to queue" + '\n' + 'queue: ' + '\n' + ''.join(queue), view=view)

                else:
                    if guild.id not in queues:
                        queues[guild.id] = []
                    vc.play(FFmpegPCMAudio(info.get('url'), **FFMPEG_OPTIONS),
                            after=lambda e: loop.create_task(check_queue(guild.id, interaction)))
                    view = Play()
                    await interaction.send("playing " + video_name, view=view)
    else:
        videos_search = VideosSearch(arg, limit = 1)
        user = interaction.user
        guild = interaction.guild

        if not user.voice:
            await interaction.send("You are not connected to a voice channel!")
            return

        if not guild.id in instances:
            vc = await user.voice.channel.connect()
            instances[guild.id] = vc
        else:
            vc = instances[guild.id]

        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(videos_search.result()['result'][0].get('link'), download=False)
            video_name = info.get('title')
            if guild.id in queues and queues[guild.id] != [] or vc.is_playing():
                queues.setdefault(guild.id, []).append(info)
                await interaction.send('added to queue ')
                view = Play()
                queue = []
                for song in queues[guild.id]:
                    queue.append(song.get('title') + '\n')
                await interaction.send(
                    "added " + video_name + " to queue" + '\n' + 'queue: ' + '\n' + ''.join(queue), view=view)

            else:
                if guild.id not in queues:
                    queues[guild.id] = []
                vc.play(FFmpegPCMAudio(info.get('url'), **FFMPEG_OPTIONS),
                        after=lambda e: loop.create_task(check_queue(guild.id, interaction)))
                view = Play()
                await interaction.send("playing " + video_name, view=view)


def is_connected(interaction):
    voice_client = get(interaction.bot.voice_clients, guild=interaction.guild)
    return voice_client and voice_client.is_connected()


async def check_queue(id, interaction):
    if queues[id]:
        vc = instances[id]
        vc.stop()
        info = queues[id].pop(0)
        vc.play(FFmpegPCMAudio(info.get('url'), **FFMPEG_OPTIONS),
                after=lambda e: loop.create_task(check_queue(id, interaction)))
        view = Play()
        queue = []
        for song in queues[id]:
            queue.append(song.get('title') + '\n')
        await interaction.send("playing " + info.get('title') + '\n' + 'queue: ' + '\n' + ''.join(queue), view=view)


def check_queue_coroutine(id, interaction):
    loop = asyncio.get_event_loop()
    loop.create_task(check_queue(id, interaction))


bot.run('Your token goes here!')
