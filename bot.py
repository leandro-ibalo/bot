import os
import asyncio
import random
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

music_status = {}

bag = ['End The Round']
total_bag = ['End The Round']
turn_log = []

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

def play_next(interaction_or_voice, guild_id):
    if isinstance(interaction_or_voice, discord.Interaction):
        voice_client = interaction_or_voice.guild.voice_client
    else:
        voice_client = interaction_or_voice

    if guild_id not in music_status:
        return

    ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -b:a 192k"
    }

    status = music_status[guild_id]

    if status['loop'] and status['current']:
        song_to_play = status['current']
    elif len(status['queue']) > 0:
        song_to_play = status['queue'].pop(0)
        status['current'] = song_to_play
    else:
        status['current'] = None
        return

    def after_playing(error):
        if error:
            print(f"error: {error}")
        play_next(voice_client, guild_id)

    try:
        source = discord.FFmpegOpusAudio(song_to_play['url'], **ffmpeg_options, executable="/usr/bin/ffmpeg")
        voice_client.play(source, after=after_playing)
        print(f"Reproduciendo en {guild_id}: {song_to_play['title']}")
    except Exception as e:
        print(f"error al iniciar audio: {e}")
        play_next(voice_client, guild_id)


TARGET_USER_ID = 
ALERT_CHANNEL_ID =

@bot.event
async def on_ready():
    await bot.tree.sync()
    bag.clear()
    total_bag.clear()
    bag.extend(['End The Round'])
    total_bag.extend(['End The Round'])
    print(f"{bot.user} conectado")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == TARGET_USER_ID:
        if before.channel is None and after.channel is not None:
            channel = bot.get_channel(ALERT_CHANNEL_ID)
            if channel:
                mis_gifs = [
                    "
                ]
                gif_elegido = random.choice(mis_gifs)
                await channel.send(f"")


@bot.tree.command(name="play", description="Poner musica en la cola")
@app_commands.describe(song_query="nombre o link")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    if interaction.user.voice is None:
        await interaction.followup.send("entrá a vc")
        return

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    guild_id = interaction.guild.id
    if guild_id not in music_status:
        music_status[guild_id] = {'queue': [], 'loop': False, 'current': None}

    ydl_option = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "cookiefile": "cookies.txt",
        "postprocessors": [{
            'key': 'FFmpegExtractAudio',
            'preferredquality': '192',
        }],
    }

    query = song_query if song_query.startswith(("http://", "https://", "www.")) else "ytsearch1: " + song_query

    try:
        results = await search_ytdlp_async(query, ydl_option)
        if "entries" in results:
            tracks = results["entries"]
            first_track = tracks[0] if tracks else None
        else:
            first_track = results
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")
        print(f"DEBUG ERROR: {e}")
        return

    if not first_track:
        await interaction.followup.send("No encontré nada pipipi...")
        return

    song = {
        'url': first_track["url"],
        'title': first_track.get("title", "Desconocido")
    }

    if voice_client.is_playing() or voice_client.is_paused():
        music_status[guild_id]['queue'].append(song)
        await interaction.followup.send(f"**{song['title']}** agregado a la lista")
    else:
        music_status[guild_id]['queue'].append(song)
        play_next(voice_client, guild_id)
        await interaction.followup.send(f"Reproduciendo **{song['title']}**")


@bot.tree.command(name="loop", description="Activar/desactivar loop")
async def loop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id not in music_status:
        await interaction.response.send_message("No hay nada sonando")
        return
    music_status[guild_id]['loop'] = not music_status[guild_id]['loop']
    estado = "activado" if music_status[guild_id]['loop'] else "desactivado"
    await interaction.response.send_message(f"Loop {estado}")

@bot.tree.command(name="stop", description="Parar/borrar")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    guild_id = interaction.guild.id
    if guild_id in music_status:
        music_status[guild_id]['queue'] = []
        music_status[guild_id]['loop'] = False
        music_status[guild_id]['current'] = None
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Lista borrada")
    else:
        await interaction.response.send_message("No sonando tal")

@bot.tree.command(name="pause", description="Pausar")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("Pausado")
    else:
        await interaction.response.send_message("No hay nada sonando")

@bot.tree.command(name="resume", description="Reanudar")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("Tuki")
    else:
        await interaction.response.send_message("No estaba pausado")

@bot.tree.command(name="skip", description="Saltar canción")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    guild_id = interaction.guild.id
    if voice_client and voice_client.is_playing():
        if guild_id in music_status:
            music_status[guild_id]['loop'] = False
        voice_client.stop()
        await interaction.response.send_message("Skip")
    else:
        await interaction.response.send_message("No hay nada sonando")

@bot.tree.command(name="leave", description="Sacar al bot")
async def leave(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        gif_url = "https://tenor.com/view/fade-away-oooooooooooo-aga-emoji-crumble-gif-20008708"
        await interaction.response.send_message(f"AAAAAAARGHHHH \n{gif_url}")
    else:
        await interaction.response.send_message("No estoy conectado master")


@bot.tree.command(name='empty', description='vacia la bolsa excepto el token de final de ronda')
async def empty(interaction: discord.Interaction):
    bag.clear()
    total_bag.clear()
    turn_log.clear()
    bag.extend(['End The Round'])
    total_bag.extend(['End The Round'])
    await interaction.response.send_message('bolsa vaciada')

@bot.tree.command(name='add', description='agregar tokens a la bolsa')
@app_commands.describe(count="cantidad de tokens a agregar", token_name="nombre del token")
async def add(interaction: discord.Interaction, count: int, token_name: str):
    if count <= 0:
        await interaction.response.send_message("tenes que agregar al menos 1 token")
        return
    bag.extend(count * [token_name])
    total_bag.extend(count * [token_name])
    await interaction.response.send_message(f'Agregados {count} tokens de {token_name}.')

@bot.tree.command(name='remove', description='quitar tokens de la bolsa')
@app_commands.describe(count="cantidad a sacar", token_name="nombre del token a sacar")
async def remove(interaction: discord.Interaction, count: int, token_name: str):
    in_bag = total_bag.count(token_name)
    if in_bag >= count:
        for _ in range(count):
            total_bag.remove(token_name)
            if token_name in bag:
                bag.remove(token_name)
        await interaction.response.send_message(f'removidos {count} tokens de {token_name}')
    else:
        await interaction.response.send_message(
            f'no se pueden sacar {count} tokens de {token_name}, solo hay {in_bag} en la bolsa'
        )

@bot.tree.command(name='draw', description='saca un token de la bolsa')
async def draw(interaction: discord.Interaction):
    if len(bag) > 0:
        random.shuffle(bag)
        drawn_token = bag.pop()
        if drawn_token == 'End The Round':
            turn_log.append('Round End')
            await interaction.response.send_message(
                '**la ronda termino**\ndevolviendo todos los tokens a la bolsa\n'
                'quita cualquier token que esté fuera y resuelve  actividades de fin de ronda\n'
                'entoces saca nuevos tokens'
            )
        else:
            turn_log.append(drawn_token)
            await interaction.response.send_message(drawn_token)
    else:
        await interaction.response.send_message(
            'la bolsa está vacio'
        )

@bot.tree.command(name='reset_bag', description='devolver los tokens a la bolsa')
async def reset_bag(interaction: discord.Interaction):
    bag.clear()
    bag.extend(total_bag)
    await interaction.response.send_message('los tokens se mezclaron')

@bot.tree.command(name='display', description='mostrar el contenido actual y total de la bolsa')
async def display_current(interaction: discord.Interaction):
    bag.sort()
    items = sorted(set(total_bag))
    lines = []
    for item in items:
        total_count = total_bag.count(item)
        bag_count = bag.count(item)
        lines.append(f"**{item}**: {bag_count}/{total_count} in bag")
    output_string = "** Bag Contents (in bag / total):**\n" + "\n".join(lines)
    await interaction.response.send_message(output_string)

@bot.tree.command(name='log', description='mostrar la iniciativa en el log.')
async def log(interaction: discord.Interaction):
    if not turn_log:
        await interaction.response.send_message('el log esta vacio')
        return
    output_string = '\n'.join(f'{i+1}. {entry}' for i, entry in enumerate(turn_log))
    await interaction.response.send_message(output_string)

@bot.tree.command(name='entry', description='añadir de forma manual al log')
@app_commands.describe(text="texto a agregar al log")
async def entry(interaction: discord.Interaction, text: str):
    turn_log.append(text)
    await interaction.response.send_message('se cargo correctamente')


bot.run(TOKEN)
