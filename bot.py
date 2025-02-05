import os
import db
import sys
import json
import math
import random
import psutil
import atexit
import locale
import typing
import discord
import sqlite3
import asyncio
import datetime
import calendar
import requests
import subprocess
from PIL import Image
from queue import Queue
from typing import Optional
from langdetect import detect
from collections import Counter
from discord import app_commands
from keep_alive import keep_alive
from discord.ui import Select, View
from question_pool import question_pool
from discord.ext import commands, tasks
from discord.ui import Modal, TextInput
from datetime import datetime, timedelta
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from database2 import nirvana_costs, body_training_costs
from database import song_list, fortune, rewards, items, item_prices, enemies
from mafia42 import class_skills, class_skills_3, class_skills_4_to_6, class_weights

intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix="/", intents=intents)
bot.remove_command("help")
restart_message_id = None
start_time = datetime.now()
IMMORTAL_KING_ID = int(os.getenv("IMMORTAL_KING_ID"))
DC_SERVER_ID = os.getenv("DC_SERVER_ID")
song_queue = Queue()
command_lock = {}
user_stats = {}
battle_states = {}
profession_image_folder = "images_mafia42"
skill_icon_folder = "icons_mafia42"
db.init_db()
conn = db.get_conn()
cursor = db.get_cursor()

@bot.event
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    activity = discord.CustomActivity("衝破空間壁障中~")
    #online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=activity)
    try:
        guild = discord.Object(DC_SERVER_ID)
        synced = await bot.tree.sync(guild=guild) 
        synced = await bot.tree.sync()
        print(f"✅ 成功同步 {len(synced)} 個指令！")
        asyncio.create_task(scheduled_reward())
    except Exception as e:
        print(f"❌ 無法同步指令: {e}")

@bot.tree.command(name="狀態", description="查看機器人狀態")
async def 狀態(interaction: discord.Interaction):
    server_count = len(bot.guilds)

    def get_user_count():
        cursor.execute("SELECT COUNT(*) FROM users")
        result = cursor.fetchone()
        if result:
            user_count = result[0]
            return user_count
        else:
            return 0

    user_count = get_user_count()

    uptime = datetime.now() - start_time

    memory_info = psutil.virtual_memory()
    total_memory = memory_info.total // (1024 * 1024)
    used_memory = memory_info.used // (1024 * 1024)

    embed = discord.Embed(title="🌸小新#6500🌸",
                          description="版本:1.0.3",
                          color=discord.Color.pink())
    embed.add_field(name="💻伺服器💻", value=f"{server_count}", inline=False)
    embed.add_field(name="👤成員👤", value=f"{user_count}", inline=False)
    embed.add_field(name="⏰已運行時長⏰", value=f"{uptime}", inline=False)
    embed.add_field(name="🖥️開機時間🖥️", value=f"{start_time}", inline=False)
    embed.add_field(name="💾記憶體狀況💾",
                    value=f"{memory_info.percent}%",
                    inline=False)
    embed.add_field(name="💾總內存💾", value=f"{total_memory}MB", inline=False)
    embed.add_field(name="💾已使用內存💾", value=f"{used_memory}MB", inline=False)
    embed.add_field(name="✶2.1.0更新內容✶", value=f"資料庫改為使用MYSQL，slash指令分類，新增修煉指令", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================================================
#                  📌 mafia42相關指令
# ==================================================

class mafia42群組(app_commands.Group):
    def __init__(self):
        super().__init__(name="mafia42", description="額外指令")
        
    @app_commands.command(name="抽卡", description="mafia42抽卡")
    async def 抽卡(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user_data(user_id)

        profession = random.choices(list(class_weights.keys()),
                                    weights=list(class_weights.values()),
                                    k=1)[0]

        tier_probabilities = [0.89091, 0.09899, 0.01, 0.0001]
        tier = random.choices([3, 4, 5, 6], weights=tier_probabilities, k=1)[0]

        user_data["total_draws"] += 1
        user_data["tier_counts"][tier] += 1

        skills = {}

        for level in range(1, min(3, tier + 1)):
            skills[level] = class_skills[profession][level - 1]

        if tier >= 3:
            skills[3] = random.choice(class_skills_3[profession])

        if tier >= 4:
            available_skills = class_skills_4_to_6[profession]
            selected_skills = random.sample(available_skills, k=tier - 3)
            for level, skill in enumerate(selected_skills, start=4):
                skills[level] = skill

        card_embed = discord.Embed(title="🎴 抽卡結果 🎴",
                                   description="抽取的卡片內容如下:",
                                   color=discord.Color.blue())
        card_embed.add_field(name="職業", value=profession, inline=False)
        card_embed.add_field(name="階級", value=f"{tier}階", inline=False)

        files = []

        profession_image_path = get_profession_image(profession)
        if profession_image_path and os.path.exists(profession_image_path):
            files.append(discord.File(profession_image_path, filename="profession.jpg"))
            card_embed.set_thumbnail(url="attachment://profession.jpg")

        skill_images = []
        skills_info = ""
        for level, skill in skills.items():
            icon_path = get_skill_icon(skill)
            if icon_path and os.path.exists(icon_path):
                skill_images.append(icon_path)
            skills_info += f"**{level}階**: {skill}\n"

        if skill_images:
            merged_image_path = merge_skill_images(skill_images, max_height=80)
            files.append(discord.File(merged_image_path, filename="merged_skills.jpg"))
            card_embed.set_image(url="attachment://merged_skills.jpg")

        card_embed.add_field(name="技能", value=skills_info, inline=False)

        await interaction.response.send_message(embed=card_embed, files=files)

    @app_commands.command(name="抽卡統計", description="查看自己的抽卡统计")
    async def 抽卡統計(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user_data(user_id)

        stats_embed = discord.Embed(title="📊 抽卡統計 📊", description="你的抽卡統計如下：", color=discord.Color.green())
        stats_embed.add_field(name="總抽卡次數", value=str(user_data["total_draws"]), inline=False)

        tier_counts = user_data["tier_counts"]
        tier_info = "\n".join([f"{tier}階: {count} 張" for tier, count in tier_counts.items()])
        stats_embed.add_field(name="階級分佈", value=tier_info, inline=False)

        await interaction.response.send_message(embed=stats_embed)

def get_user_data(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {
            "total_draws": 0,
            "tier_counts": {
                3: 0,
                4: 0,
                5: 0,
                6: 0
            }
        }
    return user_stats[user_id]
    
def get_profession_image(profession_name):
    image_path = os.path.join(profession_image_folder,
                              f"{profession_name}.jpg")
    if os.path.exists(image_path):
        return image_path
    return None

def get_skill_icon(skill_name):
    icon_path = os.path.join(skill_icon_folder, f"{skill_name}.jpg")
    if os.path.exists(icon_path):
        return icon_path
    return None

def resize_image(image_path, max_width=150):
    img = Image.open(image_path)
    width_percent = max_width / float(img.size[0])
    new_height = int(float(img.size[1]) * width_percent)
    
    img = img.resize((max_width, new_height), Image.LANCZOS)
    resized_path = image_path.replace(".jpg", "_resized.jpg")
    img.save(resized_path)

    os.remove(resized_path)
    
    return resized_path

def merge_skill_images(image_paths, max_height=80):
    images = [Image.open(img).convert("RGB") for img in image_paths]

    for i in range(len(images)):
        width, height = images[i].size
        new_width = int((max_height / height) * width)
        images[i] = images[i].resize((new_width, max_height), Image.LANCZOS)

    total_width = sum(img.width for img in images)
    merged_image = Image.new("RGB", (total_width, max_height), (255, 255, 255))

    x_offset = 0
    for img in images:
        merged_image.paste(img, (x_offset, 0))
        x_offset += img.width

    merged_path = "merged_skills.jpg"
    merged_image.save(merged_path, format="JPEG")
    return merged_path
    
bot.tree.add_command(mafia42群組())

# ==================================================
#                  📌 機器人相關指令
# ==================================================

def clean_up_cache():
    global restart_message_id
    if restart_message_id:
        restart_message_id = None

@bot.tree.command(name="重啟", description="重新啟動機器人", guild=discord.Object(DC_SERVER_ID))
async def 重啟(interaction: discord.Interaction):
    if interaction.user.id == IMMORTAL_KING_ID:
        await interaction.response.send_message("世界意志重啟中...", ephemeral=True)

        atexit.register(clean_up_cache)

        await interaction.followup.send("世界意志重啟成功！", ephemeral=True)
        subprocess.Popen([sys.executable, "bot.py"])
        await bot.close()
    else:
        await interaction.response.send_message("世界基礎規則，凡人無法撼動。", ephemeral=True)

@bot.tree.command(name="關閉", description="關閉機器人", guild=discord.Object(DC_SERVER_ID))
async def 關閉(interaction: discord.Interaction):
    if interaction.user.id == IMMORTAL_KING_ID:
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send('世界意志即將關閉...', ephemeral=True)

        await bot.close()
    else:
        await interaction.response.send_message('世界基礎規則，凡人無法撼動。', ephemeral=True)

# ==================================================
#                  📌 音樂相關指令
# ==================================================

class 音樂View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=20)
        
    @discord.ui.button(label="點我加入語音", style=discord.ButtonStyle.primary, emoji="🔊")
    async def 加入語音(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            await channel.connect()
            await interaction.response.send_message(f"✅ 機器人已加入 `{channel.name}` 語音頻道！", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 您不在任何語音頻道中！", ephemeral=True)
            
    @discord.ui.button(label="點我離開語音", style=discord.ButtonStyle.danger , emoji="🏃")
    async def 離開語音(self,interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client is None:
            await interaction.response.send_message("⚠️ 目前沒有連接到語音頻道！", ephemeral=True)
            return

        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("🏃 已離開語音頻道。", ephemeral=True)
        
    @discord.ui.button(label="播放歌曲", style=discord.ButtonStyle.success , emoji="🔊")
    async def 播放(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild.voice_client:
            view = JoinVoiceButton()
            await interaction.response.send_message("❌ 機器人尚未加入語音頻道，請先使用 `/加入語音`！", view=view, ephemeral=True)
            return

        items_per_page = 25
        pages = math.ceil(len(song_list) / items_per_page)

        def get_options(page):
            start_index = page * items_per_page
            end_index = start_index + items_per_page
            return[ 
                discord.SelectOption(label=f"{key}: {value}", value=str(key))
                for key, value in list(song_list.items())[start_index:end_index]]

        class SongSelectView(View):

            def __init__(self):
                super().__init__()
                self.current_page = 0
                self.update_select_menu()

            def update_select_menu(self):
                self.clear_items()
                options = get_options(self.current_page)
                select = discord.ui.Select(placeholder="選擇一首歌曲", options=options, custom_id="select_song")
                select.callback = self.select_callback
                self.add_item(select)

                if pages > 1:
                    prev_button = discord.ui.Button(label="⬅️ 上一頁", style=discord.ButtonStyle.primary)
                    prev_button.callback = self.previous_page
                    next_button = discord.ui.Button(label="下一頁 ➡️", style=discord.ButtonStyle.primary)
                    next_button.callback = self.next_page

                    self.add_item(prev_button)
                    self.add_item(next_button)

            async def select_callback(self, select_interaction: discord.Interaction):
                song_number = int(select_interaction.data['values'][0])
                mp3_file = os.path.join("music", song_list[song_number])
                if os.path.exists(mp3_file):
                    song_queue.put((mp3_file, 0.5))
                    song_name = os.path.basename(mp3_file)
                    await select_interaction.response.send_message(
                        f"✅ {song_name} 已加入播放隊列", ephemeral=True)

                    if not interaction.guild.voice_client.is_playing():
                        await play_next_song(interaction)
                else:
                    await select_interaction.response.send_message(f"❌ 找不到歌曲 {song_number}", ephemeral=True)

            async def previous_page(self, button_interaction: discord.Interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    self.update_select_menu()
                    await button_interaction.response.edit_message(view=self)

            async def next_page(self, button_interaction: discord.Interaction):
                if self.current_page < pages - 1:
                    self.current_page += 1
                    self.update_select_menu()
                    await button_interaction.response.edit_message(view=self)

        view = SongSelectView()
        await interaction.response.send_message("請選擇一首歌曲：", view=view, ephemeral=True)
    
    @discord.ui.button(label="播放順序", style=discord.ButtonStyle.secondary , emoji="⏏️")
    async def 查看播放順序(self,interaction: discord.Interaction, button: discord.ui.Button):
        if song_queue.empty():
            await interaction.response.send_message("沒有正在排隊的歌曲。", ephemeral=True)
        else:
            queued_songs = list(song_queue.queue)
            song_list_message = "\n".join([
                f"{i + 1}. {os.path.basename(song[0])} (音量: {song[1]})"
                for i, song in enumerate(queued_songs)])
            await interaction.response.send_message(f"歌曲播放順序：\n{song_list_message}", ephemeral=True)

    @discord.ui.button(label="調整音量(0.0~2.0)", style=discord.ButtonStyle.primary , emoji="🔊")
    async def 調整音量(self,interaction: discord.Interaction, volume: float, button: discord.ui.Button):
        if 0.0 <= volume <= 2.0:
            voice_client = interaction.guild.voice_client
            if voice_client.is_playing():
                voice_client.source.volume = volume
                await interaction.response.send_message(f"🔊 音量已調整為 {volume}", ephemeral=True)
            else:
                await interaction.response.send_message("❌ 沒有正在播放的歌曲", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ 請輸入有效的音量範圍（0.0 到 2.0）",ephemeral=True)

    @discord.ui.button(label="暫停", style=discord.ButtonStyle.danger , emoji="⏸️")
    async def 暫停(self,interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸️ 歌曲已暫停", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 沒有正在播放的歌曲", ephemeral=True)

    @discord.ui.button(label="繼續", style=discord.ButtonStyle.success , emoji="▶️")
    async def 繼續(self,interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶️ 歌曲已繼續播放", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 歌曲並未暫停", ephemeral=True)

    @discord.ui.button(label="隨機播放", style=discord.ButtonStyle.secondary , emoji="🔀")
    async def 隨機播放(self,interaction: discord.Interaction, button: discord.ui.Button):
        if not song_list:
            await interaction.response.send_message("❌ 歌曲列表為空", ephemeral=True)
            return

        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            await interaction.response.send_message("⚠️ 請先停止正在播放的歌曲再隨機播放", ephemeral=True)
            return

        random_song = random.choice(list(song_list.values()))
        mp3_file = os.path.join("music", random_song)

        if os.path.exists(mp3_file):
            source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
            transformed_source = PCMVolumeTransformer(source, volume=0.5)
            voice_client.play(transformed_source)
            await interaction.response.send_message(f"🔀 已隨機播放歌曲: {random_song}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ 找不到歌曲 {random_song}", ephemeral=True)

    @discord.ui.button(label="隨機循環播放", style=discord.ButtonStyle.primary , emoji="🔁")
    async def 循環播放(self,interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client

        while True:
            random_song = random.choice(list(song_list.values()))
            mp3_file = os.path.join("music", random_song)

            if os.path.exists(mp3_file):
                source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
                transformed_source = PCMVolumeTransformer(source, volume=0.5)
                voice_client.play(transformed_source)

                while voice_client.is_playing():
                    await asyncio.sleep(1)
            else:
                await interaction.response.send_message(f"找不到歌曲 {random_song}", ephemeral=True)
@bot.tree.command(name="音樂", description="音樂相關功能集合")    
async def 音樂(interaction: discord.Interaction):
    view = 音樂View()
    await interaction.response.send_message("請先加入語音：", view=view, ephemeral=True)

async def play_next_song(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if not song_queue.empty():
        mp3_file, volume = song_queue.get()

        source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
        transformed_source = PCMVolumeTransformer(source, volume=volume)
        voice_client.play(
            transformed_source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next_song(interaction), bot.loop),)
    else:
        await interaction.channel.send("播放隊列已清空！", ephemeral=True)
    
'''
class 音樂群組(app_commands.Group):
    def __init__(self):
        super().__init__(name="音樂", description="聽歌")

    @app_commands.command(name="加入語音", description="讓機器人加入您的語音頻道")
    async def 加入語音(self, interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("⚠️ 您不在任何語音頻道中！", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"✅ 已加入語音頻道：{channel.name}", ephemeral=True)

    @app_commands.command(name="離開語音", description="讓機器人離開語音頻道")
    async def 離開語音(self,interaction: discord.Interaction):
        if interaction.guild.voice_client is None:
            await interaction.response.send_message("⚠️ 目前沒有連接到語音頻道！", ephemeral=True)
            return

        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("🏃 已離開語音頻道。", ephemeral=True)

    @app_commands.command(name="播放", description="從播放清單選擇歌曲")
    async def 播放(self,interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            view = JoinVoiceButton()
            await interaction.response.send_message("❌ 機器人尚未加入語音頻道，請先使用 `/加入語音`！", view=view, ephemeral=True)
            return

        items_per_page = 25
        pages = math.ceil(len(song_list) / items_per_page)

        def get_options(page):
            start_index = page * items_per_page
            end_index = start_index + items_per_page
            return[ 
                discord.SelectOption(label=f"{key}: {value}", value=str(key))
                for key, value in list(song_list.items())[start_index:end_index]]

        class SongSelectView(View):

            def __init__(self):
                super().__init__()
                self.current_page = 0
                self.update_select_menu()

            def update_select_menu(self):
                self.clear_items()
                options = get_options(self.current_page)
                select = discord.ui.Select(placeholder="選擇一首歌曲", options=options, custom_id="select_song")
                select.callback = self.select_callback
                self.add_item(select)

                if pages > 1:
                    prev_button = discord.ui.Button(label="⬅️ 上一頁", style=discord.ButtonStyle.primary)
                    prev_button.callback = self.previous_page
                    next_button = discord.ui.Button(label="下一頁 ➡️", style=discord.ButtonStyle.primary)
                    next_button.callback = self.next_page

                    self.add_item(prev_button)
                    self.add_item(next_button)

            async def select_callback(self, select_interaction: discord.Interaction):
                song_number = int(select_interaction.data['values'][0])
                mp3_file = os.path.join("music", song_list[song_number])
                if os.path.exists(mp3_file):
                    song_queue.put((mp3_file, 0.5))
                    song_name = os.path.basename(mp3_file)
                    await select_interaction.response.send_message(
                        f"{song_name} 已加入播放隊列", ephemeral=True)

                    if not interaction.guild.voice_client.is_playing():
                        await play_next_song(interaction)
                else:
                    await select_interaction.response.send_message(f"找不到歌曲 {song_number}", ephemeral=True)

            async def previous_page(self, button_interaction: discord.Interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    self.update_select_menu()
                    await button_interaction.response.edit_message(view=self)

            async def next_page(self, button_interaction: discord.Interaction):
                if self.current_page < pages - 1:
                    self.current_page += 1
                    self.update_select_menu()
                    await button_interaction.response.edit_message(view=self)

        view = SongSelectView()
        await interaction.response.send_message("請選擇一首歌曲：", view=view, ephemeral=True)

    @app_commands.command(name="查看播放順序", description="查看當前播放隊列")
    async def 查看播放順序(self,interaction: discord.Interaction):
        if song_queue.empty():
            await interaction.response.send_message("沒有正在排隊的歌曲。", ephemeral=True)
        else:
            queued_songs = list(song_queue.queue)
            song_list_message = "\n".join([
                f"{i + 1}. {os.path.basename(song[0])} (音量: {song[1]})"
                for i, song in enumerate(queued_songs)])
            await interaction.response.send_message(f"歌曲播放順序：\n{song_list_message}", ephemeral=True)

    @app_commands.command(name="調整音量", description="調整當前播放的音量0.0~2.0")
    async def 調整音量(self,interaction: discord.Interaction, volume: float):
        if 0.0 <= volume <= 2.0:
            voice_client = interaction.guild.voice_client
            if voice_client.is_playing():
                voice_client.source.volume = volume
                await interaction.response.send_message(f"音量已調整為 {volume}", ephemeral=True)
            else:
                await interaction.response.send_message("沒有正在播放的歌曲", ephemeral=True)
        else:
            await interaction.response.send_message("請輸入有效的音量範圍（0.0 到 2.0）",ephemeral=True)

    @app_commands.command(name="暫停", description="暫停當前播放的歌曲")
    async def 暫停(self,interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("歌曲已暫停", ephemeral=True)
        else:
            await interaction.response.send_message("沒有正在播放的歌曲", ephemeral=True)

    @app_commands.command(name="繼續", description="繼續播放暫停的歌曲")
    async def 繼續(self,interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("歌曲已繼續播放", ephemeral=True)
        else:
            await interaction.response.send_message("歌曲並未暫停", ephemeral=True)

    @app_commands.command(name="隨機播放", description="隨機播放一首歌曲")
    async def 隨機播放(self,interaction: discord.Interaction):
        if not song_list:
            await interaction.response.send_message("歌曲列表為空", ephemeral=True)
            return

        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            await interaction.response.send_message("請先停止正在播放的歌曲再隨機播放", ephemeral=True)
            return

        random_song = random.choice(list(song_list.values()))
        mp3_file = os.path.join("music", random_song)

        if os.path.exists(mp3_file):
            source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
            transformed_source = PCMVolumeTransformer(source, volume=0.5)
            voice_client.play(transformed_source)
            await interaction.response.send_message(f"已隨機播放歌曲: {random_song}", ephemeral=True)
        else:
            await interaction.response.send_message(f"找不到歌曲 {random_song}", ephemeral=True)

    @app_commands.command(name="循環播放", description="啟動循環播放模式")
    async def 循環播放(self,interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        while True:
            random_song = random.choice(list(song_list.values()))
            mp3_file = os.path.join("music", random_song)

            if os.path.exists(mp3_file):
                source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
                transformed_source = PCMVolumeTransformer(source, volume=0.5)
                voice_client.play(transformed_source)

                while voice_client.is_playing():
                    await asyncio.sleep(1)
            else:
                await interaction.response.send_message(f"找不到歌曲 {random_song}", ephemeral=True)

    @app_commands.command(name="歌單", description="歌曲清單")
    async def 歌單(self,interaction: discord.Interaction):
        song_list_message = "可用的歌曲清單：\n"
        for number, song_name in song_list.items():
            song_list_message += f"{number}: {song_name}\n"
        embed = discord.Embed(title="歌曲清單", description=song_list_message, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)
async def play_next_song(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if not song_queue.empty():
        mp3_file, volume = song_queue.get()

        source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
        transformed_source = PCMVolumeTransformer(source, volume=volume)
        voice_client.play(
            transformed_source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next_song(interaction), bot.loop),)
    else:
        await interaction.channel.send("播放隊列已清空！", ephemeral=True)

bot.tree.add_command(音樂群組())
'''
# ==================================================
#                  📌 修仙相關指令
# ==================================================

class 修煉View(discord.ui.View):
    active_sessions = {}
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.chosen_mode = None

    async def 修煉處理(self, interaction: discord.Interaction, mode: str, gain: int, duration: int, cost: int = 0):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("⚠️ 這不是你的修煉選單！", ephemeral=True)
            return
        
        if self.user_id in self.active_sessions:
            await interaction.response.send_message("⏳ 你已經在修煉中，請耐心等待！", ephemeral=True)
            return

        self.active_sessions[self.user_id] = True
        
        cursor.execute("SELECT spirit_stone FROM users WHERE user_id=%s", (self.user_id,))
        result = cursor.fetchone()
        if not result:
            await interaction.response.send_message("❌ 你還沒有創建角色，請先入道！", ephemeral=True)
            del self.active_sessions[self.user_id]
            return
        spirit_stone = result[0]

        if cost > 0 and spirit_stone < cost:
            await interaction.response.send_message("❌ 你的靈石不足，無法選擇此修練方式！", ephemeral=True)
            del self.active_sessions[self.user_id]
            return

        if cost > 0:
            cursor.execute("UPDATE users SET spirit_stone = spirit_stone - %s WHERE user_id = %s", (cost, self.user_id))
            conn.commit()

        self.chosen_mode = mode
        end_time = datetime.utcnow() + timedelta(seconds=duration)

        await interaction.response.defer()
        message = await interaction.followup.send(
            f"🕰️ **{mode}** 開始！\n\n"
            f"進度：[{'░' * 20}] 0%",
            ephemeral=True
        )

        for button in self.children:
            button.disabled = True
        await message.edit(view=self)

        progress_bar = 20
        for i in range(1, progress_bar + 1):
            await asyncio.sleep(duration / progress_bar)
            remaining_time = duration - (i * (duration // progress_bar))
            percent = int((i / progress_bar) * 100)
            progress = "█" * i + "░" * (progress_bar - i)
            await message.edit(content=f"🕰️ **{mode}** 進行中...\n"
                                       f"進度：[{progress}] {percent}%  |  剩餘時間：{self.format_time(remaining_time)}")

        random_event = None
        if random.randint(1, 100) <= 5:
            event = random.choice(["一重天雷", "二重天雷", "仙靈降臨"])
            if event == "一重天雷":
                cursor.execute("UPDATE users SET cultivation = cultivation * 0.9 WHERE user_id = %s", (self.user_id,))
                random_event = "⚡ **一重天雷！** 你失去了 10% 修為！"
            elif event == "二重天雷":
                cursor.execute("UPDATE users SET cultivation = cultivation * 0.85 WHERE user_id = %s", (self.user_id,))
                random_event = "⚡ **二重天雷！** 你失去了 15% 修為！"
            elif event == "仙靈降臨":
                cursor.execute("UPDATE users SET cultivation = cultivation + 2000 WHERE user_id = %s", (self.user_id,))
                random_event = "🎁 **仙靈降臨！** 你額外獲得 2000 修為！"
            conn.commit()

        cursor.execute("UPDATE users SET cultivation = cultivation + %s WHERE user_id = %s", (gain, self.user_id))
        conn.commit()

        final_message = f"✅ 你完成了 **{mode}**，獲得 **{gain} 修為**！"
        if random_event:
            final_message += f"\n{random_event}"

        await message.edit(content=f"🕰️ **{mode}** 完成！\n進度：[{'█' * 20}] 100%\n{final_message}", view=None)

        del self.active_sessions[self.user_id]

        self.stop()
        
    def format_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    @discord.ui.button(label="入定修煉 🧘", style=discord.ButtonStyle.primary)
    async def 入定修煉(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.修煉處理(interaction, "入定修煉", gain=1000, duration=60)

    @discord.ui.button(label="閉關修煉 🏯", style=discord.ButtonStyle.success)
    async def 閉關修煉(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.修煉處理(interaction, "閉關修煉", gain=5000, duration=3600)

    @discord.ui.button(label="靈脈修煉 🔮", style=discord.ButtonStyle.danger)
    async def 靈脈修煉(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.修煉處理(interaction, "靈脈修煉", gain=8000, duration=7200, cost=100)

    @discord.ui.button(label="洞天福地 🏞️", style=discord.ButtonStyle.secondary)
    async def 洞天福地(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.修煉處理(interaction, "洞天福地", gain=15000, duration=10800, cost=300)


class 修仙群組(app_commands.Group):
    def __init__(self):
        super().__init__(name="修仙", description="修仙指令")

    @app_commands.command(name="入道", description="開始你的修煉之旅！")
    async def 入道(self, interaction: discord.Interaction):
        user_id = int(interaction.user.id)

        cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            await interaction.response.send_message("你已經是修煉者，無需再次入道。")
            return

        level_name = "凡人"
        layer_name = "一層"
        body_level_name = "凡人肉體"
        body_layer_name = "一階"

        cursor.execute(
            """INSERT INTO users (user_id, spirit_stone, level, layer, body_level, body_layer, attack, health, defense, cultivation, quench, crit_rate, crit_damage) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, 0, level_name, layer_name, body_level_name, body_layer_name, 20, 100, 10, 0, 0, 5.00, 150.00)
        )
        conn.commit()

        await interaction.response.send_message(f"✨ 歡迎踏入修仙之旅！\n你的初始境界為 **{level_name} {layer_name}**，請試著摸索其他指令。", ephemeral=True)

    @app_commands.command(name="感悟", description="每日簽到，獲得靈石獎勵！")
    async def 感悟(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        today = str(datetime.today())

        cursor.execute(
            "SELECT last_checkin, spirit_stone FROM users WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
            return

        last_checkin, spirit_stone = result

        if last_checkin == today:
            await interaction.response.send_message("今天已經感悟過了，請明天再來！", ephemeral=True)
        else:
            new_spirit_stone = spirit_stone + 100
            cursor.execute(
                "UPDATE users SET spirit_stone = %s, last_checkin = %s WHERE user_id = %s",
                (new_spirit_stone, today, user_id)
            )
            conn.commit()
            await interaction.response.send_message(
                f"感悟成功！你的靈石數量增加100，目前靈石：{new_spirit_stone}", ephemeral=True
            )

    @app_commands.command(name="占卜", description="每日占卜，獲得靈石獎勵！")
    async def 占卜(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        today = str(datetime.today())

        cursor.execute("SELECT last_draw, spirit_stone FROM users WHERE user_id=%s", (user_id,))
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
            return

        last_draw, spirit_stone = result

        if last_draw == today:
            await interaction.response.send_message("你今天已經占卜過了，請明天再來。", ephemeral=True)
        else:
            prob = [1] * len(fortune)
            drawn_fortune = random.choices(fortune, weights=prob)[0]
            reward = rewards.get(drawn_fortune, 0)
            spirit_stone += reward

            cursor.execute(
                "UPDATE users SET last_draw=%s, spirit_stone=%s WHERE user_id=%s",
                (today, spirit_stone, user_id)
            )
            conn.commit()

            embed = discord.Embed(
                title=f"你抽到了「{drawn_fortune}」!",
                description=f"獲得了獎勵：{reward}靈石。\n目前靈石：{spirit_stone}",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="靈石", description="查看玩家當前靈石數量。")
    async def 靈石(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        cursor.execute("SELECT spirit_stone FROM users WHERE user_id=%s", (user_id,))
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message("❌ 您還不是修煉者，請先使用 `/入道` 指令。", ephemeral=True)
        else:
            spirit_stone = result[0]
            await interaction.response.send_message(f"💎 你目前持有的靈石數量：{spirit_stone}", ephemeral=True)

    @app_commands.command(name="渡劫", description="突破境界！")
    async def 渡劫(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in command_lock and command_lock[user_id]:
            await interaction.response.send_message("請等待當前指令執行完畢後再使用。", ephemeral=True)
            return

        command_lock[user_id] = True

        try:
            cursor.execute(
                "SELECT cultivation, level, layer, attack, health, defense FROM users WHERE user_id=%s",
                (user_id, )
            )
            result = cursor.fetchone()

            if result:
                cultivation, level, layer, attack, health, defense = result
            else:
                await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
                return

            breakthrough_conditions = nirvana_costs.get(level, None)

            if not breakthrough_conditions:
                await interaction.response.send_message("您已達到最高境界，無法再升級。", ephemeral=True)
            else:
                current_layer = layer if layer in breakthrough_conditions else "一層"

                if current_layer != "大圓滿":
                    current_cultivation = cultivation
                    required_cultivation = breakthrough_conditions[current_layer]

                    if current_cultivation >= required_cultivation:
                        new_cultivation = current_cultivation - required_cultivation
                        new_layer = list(breakthrough_conditions.keys())[
                            list(breakthrough_conditions).index(current_layer) + 1
                        ]
                        new_attack = attack + 10
                        new_health = health + 55
                        new_defense = defense + 3

                        cursor.execute(
                            "UPDATE users SET cultivation=%s, layer=%s, attack=%s, health=%s, defense=%s WHERE user_id=%s",
                            (new_cultivation, new_layer, new_attack, new_health, new_defense, user_id)
                        )
                        conn.commit()

                        embed = discord.Embed(
                            title="🎉 恭喜您成功渡劫！",
                            description=f"您的境界提升到了 **{level} {new_layer}**！\n"
                                        f"⚔️ **攻擊**: {attack} ➟ {new_attack}\n"
                                        f"🛡️ **防禦**: {defense} ➟ {new_defense}\n"
                                        f"🩸 **氣血**: {health} ➟ {new_health}",
                            color=discord.Color.blue()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        await interaction.response.send_message(
                            f"您的修為不足以渡劫到下一層。\n"
                            f"⚡ 所需修為：{required_cultivation}\n"
                            f"🔹 您的修為：{current_cultivation}",
                            ephemeral=True
                        )
                else:
                    next_level_index = list(nirvana_costs.keys()).index(level) + 1
                    if next_level_index < len(nirvana_costs):
                        next_level = list(nirvana_costs.keys())[next_level_index]
                        next_layer = "一層"
                        required_cultivation = nirvana_costs[next_level][next_layer]

                        if cultivation >= required_cultivation:
                            new_cultivation = cultivation - required_cultivation
                            new_attack = attack + 20
                            new_health = health + 100
                            new_defense = defense + 6

                            cursor.execute(
                                "UPDATE users SET cultivation=%s, level=%s, layer=%s, attack=%s, health=%s, defense=%s WHERE user_id=%s",
                                (new_cultivation, next_level, next_layer, new_attack, new_health, new_defense, user_id)
                            )
                            conn.commit()

                            embed = discord.Embed(
                                title="🎉 恭喜您成功渡劫！",
                                description=f"您的境界提升到了 **{next_level} {next_layer}**！\n"
                                            f"⚔️ **攻擊**: {attack} ➟ {new_attack}\n"
                                            f"🛡️ **防禦**: {defense} ➟ {new_defense}\n"
                                            f"🩸 **氣血**: {health} ➟ {new_health}",
                                color=discord.Color.blue()
                            )
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        else:
                            await interaction.response.send_message(
                                f"您的修為不足以渡劫到下一境界的第一層。\n"
                                f"⚡ 所需修為：{required_cultivation}\n"
                                f"🔹 您的修為：{cultivation}",
                                ephemeral=True
                            )
                    else:
                        await interaction.response.send_message("您已達到最高境界，無法再升級。", ephemeral=True)

        except Exception as e:
            print(f"❌ 渡劫發生錯誤: {e}")
            await interaction.response.send_message("⚠️ 發生錯誤，請稍後再試。", ephemeral=True)

        finally:
            command_lock[user_id] = False

    @app_commands.command(name="煉體", description="淬鍊肉身！")
    async def 煉體(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in command_lock and command_lock[user_id]:
            await interaction.response.send_message("請等待當前指令執行完畢後再使用。", ephemeral=True)
            return

        command_lock[user_id] = True

        try:
            cursor.execute(
                "SELECT quench, body_level, body_layer, attack, health, defense FROM users WHERE user_id=%s",
                (user_id, )
            )
            result = cursor.fetchone()

            if result:
                quench, body_level, body_layer, attack, health, defense = result
            else:
                await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
                return

            breakthrough_conditions2 = body_training_costs.get(body_level, None)

            if not breakthrough_conditions2:
                await interaction.response.send_message("您已達到最高煉體境界，無法再升級。", ephemeral=True)
            else:
                current_body_layer = body_layer if body_layer in breakthrough_conditions2 else "一階"

                if current_body_layer != "大圓滿":
                    current_quench = quench
                    required_quench = breakthrough_conditions2[current_body_layer]

                    if current_quench >= required_quench:
                        new_quench = current_quench - required_quench
                        new_body_layer = list(breakthrough_conditions2.keys())[
                            list(breakthrough_conditions2).index(current_body_layer) + 1
                        ]
                        new_attack = attack + 4
                        new_health = health + 200
                        new_defense = defense + 6

                        cursor.execute(
                            "UPDATE users SET quench=%s, body_layer=%s, attack=%s, health=%s, defense=%s WHERE user_id=%s",
                            (new_quench, new_body_layer, new_attack, new_health, new_defense, user_id)
                        )
                        conn.commit()

                        embed = discord.Embed(
                            title="🎉 恭喜您成功淬煉！",
                            description=f"您的煉體境界提升到了 **{body_level} {new_body_layer}**！\n"
                                        f"⚔️ **攻擊**: {attack} ➟ {new_attack}\n"
                                        f"🛡️ **防禦**: {defense} ➟ {new_defense}\n"
                                        f"🩸 **氣血**: {health} ➟ {new_health}",
                            color=discord.Color.blue()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        await interaction.response.send_message(
                            f"您的精華不足以淬煉到下一階。\n"
                            f"⚡ **所需精華**：{required_quench}\n"
                            f"🔹 **您的精華**：{current_quench}",
                            ephemeral=True
                        )
                else:
                    next_body_level_index = list(body_training_costs.keys()).index(body_level) + 1
                    if next_body_level_index < len(body_training_costs):
                        next_body_level = list(body_training_costs.keys())[next_body_level_index]
                        next_body_layer = "一階"
                        required_quench = body_training_costs[next_body_level][next_body_layer]

                        if quench >= required_quench:
                            new_quench = quench - required_quench
                            new_attack = attack + 10
                            new_health = health + 400
                            new_defense = defense + 9

                            cursor.execute(
                                "UPDATE users SET quench=%s, body_level=%s, body_layer=%s, attack=%s, health=%s, defense=%s WHERE user_id=%s",
                                (new_quench, next_body_level, next_body_layer, new_attack, new_health, new_defense, user_id)
                            )
                            conn.commit()

                            embed = discord.Embed(
                                title="🎉 恭喜您成功淬煉！",
                                description=f"您的煉體境界提升到了 **{next_body_level} {next_body_layer}**！\n"
                                            f"⚔️ **攻擊**: {attack} ➟ {new_attack}\n"
                                            f"🛡️ **防禦**: {defense} ➟ {new_defense}\n"
                                            f"🩸 **氣血**: {health} ➟ {new_health}",
                                color=discord.Color.blue()
                            )
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        else:
                            await interaction.response.send_message(
                                f"您的精華不足以淬煉到下一階的第一層。\n"
                                f"⚡ **所需精華**：{required_quench}\n"
                                f"🔹 **您的精華**：{quench}",
                                ephemeral=True
                            )
                    else:
                        await interaction.response.send_message("您已達到最高煉體境界，無法再淬煉。", ephemeral=True)

        except Exception as e:
            print(f"❌ 煉體發生錯誤: {e}")
            await interaction.response.send_message("⚠️ 發生錯誤，請稍後再試。", ephemeral=True)

        finally:
            command_lock[user_id] = False

    @app_commands.command(name="查看修為", description="查看你的修練者詳細資料")
    async def 查看修為(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        cursor.execute(
            "SELECT level, layer, body_level, body_layer, cultivation, quench, attack, defense, health, current_health, spirit_stone FROM users WHERE user_id=%s",
            (user_id,))
        user_info = cursor.fetchone()

        if not user_info:
            await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。",
                                                    ephemeral=True)
            return

        (current_level, current_layer, current_body_level, current_body_layer,
         cultivation, quench, attack, defense, health, current_health,
         spirit_stone) = user_info

        required_cultivation = nirvana_costs.get(current_level,
                                                 {}).get(current_layer, "未定義")
        required_quench = body_training_costs.get(current_body_level,
                                                  {}).get(current_body_layer,
                                                          "未定義")

        資料 = discord.Embed(title="修練者資料",
                           description="以下是您的資料：",
                           color=discord.Color.orange())
        資料.add_field(name="修為：", value=f"{cultivation}", inline=True)
        資料.add_field(name="境界 : ", value=f"{current_level}", inline=True)
        資料.add_field(name="層數 : ", value=f"{current_layer}", inline=True)
        資料.add_field(name="當前境界所需修為 : ",
                     value=f"{required_cultivation}",
                     inline=True)
        資料.add_field(name="淬體值：", value=f"{quench}", inline=True)
        資料.add_field(name="煉體 : ", value=f"{current_body_level}", inline=True)
        資料.add_field(name="階級 : ", value=f"{current_body_layer}", inline=True)
        資料.add_field(name="當前煉體階級所需淬體值：", value=f"{required_quench}", inline=True)
        資料.add_field(name="攻擊 : ", value=f"{attack}", inline=True)
        資料.add_field(name="防禦 : ", value=f"{defense}", inline=True)
        資料.add_field(name="氣血上限/當前氣血 : ",
                     value=f"{health}/{current_health}",
                     inline=True)
        資料.add_field(name="靈石 : ", value=f"{spirit_stone}", inline=True)

        await interaction.response.send_message(embed=資料, ephemeral=True)

    @app_commands.command(name="修練", description="選擇修練方式以提升修為")
    async def 修煉(self, interaction: discord.Interaction):
        view = 修煉View(user_id=interaction.user.id)
        await interaction.response.send_message("請選擇你的修練方式：", view=view, ephemeral=True)

bot.tree.add_command(修仙群組())

# ==================================================
#                  📌 修改資料相關指令
# ==================================================

async def 修改數值(interaction: discord.Interaction, user_id: int, field: str, value: int, field_name: str):
    if interaction.user.id != IMMORTAL_KING_ID:
        await interaction.response.send_message("世界基礎規則，凡人無法撼動。", ephemeral=True)
        return

    cursor.execute(f"SELECT {field} FROM users WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()

    if user_data is None:
        await interaction.response.send_message("❌ 此玩家尚未入道，無法修改數據。", ephemeral=True)
        return

    current_value = user_data[0]

    sql = f"UPDATE users SET {field} = %s WHERE user_id = %s"
    cursor.execute(sql, (value, user_id))
    conn.commit()

    await interaction.response.send_message(
        f"✅ 成功將 <@{user_id}> 的 **{field_name}** 由 `{current_value}` 修改為 `{value}`。",
        ephemeral=True
    )

class 修改群組(app_commands.Group):
    def __init__(self):
        super().__init__(name="修改", description="修改用戶資料")

    @app_commands.command(name="修改修為", description="（仙王專用）改變修煉者的修為值")
    async def 修為值(self, interaction: discord.Interaction, user: typing.Optional[discord.User] = None, user_id: typing.Optional[int] = None, 修為: int = 0):
        if not user and not user_id:
            await interaction.response.send_message("❌ 請提供用戶或用戶 ID！", ephemeral=True)
            return
        target_id = user.id if user else user_id
        await 修改數值(interaction, target_id, "cultivation", 修為, "修為")

    @app_commands.command(name="修改精華", description="（仙王專用）改變修煉者的淬體值")
    async def 淬體值(self, interaction: discord.Interaction, user: typing.Optional[discord.User] = None, user_id: typing.Optional[int] = None, 煉體資源: int = 0):
        if not user and not user_id:
            await interaction.response.send_message("❌ 請提供用戶或用戶 ID！", ephemeral=True)
            return
        target_id = user.id if user else user_id
        await 修改數值(interaction, target_id, "quench", 淬體值, "淬體值")

    @app_commands.command(name="修改靈石", description="（仙王專用）修改玩家的靈石數量")
    async def 靈石(self, interaction: discord.Interaction, user: typing.Optional[discord.User] = None, user_id: typing.Optional[int] = None, 靈石: int = 0):
        if not user and not user_id:
            await interaction.response.send_message("❌ 請提供用戶或用戶 ID！", ephemeral=True)
            return
        target_id = user.id if user else user_id
        await 修改數值(interaction, target_id, "spirit_stone", 靈石, "靈石")

    @app_commands.command(name="查看修煉者資料", description="(仙王專用)查看所有修煉者的資料")
    async def 查看修煉者資料(self, interaction: discord.Interaction):
        if interaction.user.id != IMMORTAL_KING_ID:
            await interaction.response.send_message("⚠️ 你沒有權限執行此操作！", ephemeral=True)
            return

        cursor.execute("SELECT user_id, spirit_stone, level, layer FROM users")
        users = cursor.fetchall()

        if not users:
            await interaction.response.send_message("❌ 目前沒有修煉者數據！", ephemeral=True)
            return

        users_table = "```\n"
        users_table += f"{'用戶名稱': <20}{'用戶ID': <20}{'靈石': <10}{'境界': <10}{'層數': <10}\n"

        for user_data in users:
            user_id, spirit_stone, level, layer = user_data
            user = interaction.guild.get_member(user_id) or await bot.fetch_user(user_id)
            username = user.display_name if user else "未知用戶"

            users_table += f"{username: <20}{str(user_id): <20}{str(spirit_stone): <10}{str(level): <10}{str(layer): <10}\n"

        users_table += "```"

        await interaction.response.send_message(f"📜 **修煉者資料總表**：\n{users_table}", ephemeral=True)
       
bot.tree.add_command(修改群組())

# ==================================================
#                  📌 排行榜相關指令
# ==================================================

class 排行榜群組(app_commands.Group):
    def __init__(self):
        super().__init__(name="排行榜", description="查看排行榜並發放獎勵")

    @app_commands.command(name="境界", description="查看境界排行榜")
    async def 境界(self, interaction: discord.Interaction):
        leaderboard_data = get_leaderboard()

        if leaderboard_data:
            leaderboard_message = ""
            for index, (user_id, level, layer) in enumerate(leaderboard_data, start=1):
                user = interaction.guild.get_member(user_id) or await bot.fetch_user(user_id)
                username = user.display_name if user else f"未知用戶 (ID: {user_id})"

                leaderboard_message += f"{index}. {username} - {level} {layer}\n"

            embed = discord.Embed(title="🏆 境界排行榜 🏆",
                                  description=leaderboard_message,
                                  color=discord.Color.gold())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ 暫無排行榜數據。", ephemeral=True)

    @app_commands.command(name="問答遊戲", description="查看問答遊戲排行榜")
    async def 問答(self, interaction: discord.Interaction):
        leaderboard_data = get_quiz_game_leaderboard()

        if leaderboard_data:
            leaderboard_message = ""
            for index, (user_id, correct_answers) in enumerate(leaderboard_data, start=1):
                user = interaction.guild.get_member(user_id) or await bot.fetch_user(user_id)
                username = user.display_name if user else f"未知用戶 (ID: {user_id})"

                leaderboard_message += f"{index}. {username} - 答對次數：{correct_answers}\n"

            embed = discord.Embed(title="🏆 問答遊戲排行榜 🏆",
                                  description=leaderboard_message,
                                  color=discord.Color.gold())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ 暫無排行榜數據。", ephemeral=True)

@bot.tree.command(name="發放獎勵", description="發放排行榜獎勵並重置問答遊戲排行榜", guild=discord.Object(DC_SERVER_ID))
async def 發放獎勵(interaction: discord.Interaction):
    await interaction.response.send_message("🛠️ 正在發放排行榜獎勵，請稍候...", ephemeral=True)
        
    await reward_players()


    await interaction.followup.send("✅ 排行榜獎勵發放完畢！問答遊戲排行榜已重置。", ephemeral=True)

def get_leaderboard():
    cursor.execute(
        "SELECT user_id, level, layer FROM users ORDER BY level DESC, layer ASC LIMIT 50"
    )
    return cursor.fetchall()

def get_quiz_game_leaderboard():
    cursor.execute(
        "SELECT user_id, correct_answers FROM users WHERE correct_answers > 0 ORDER BY correct_answers DESC LIMIT 50"
    )
    return cursor.fetchall()

async def reward_players():
    quiz_leaderboard = get_quiz_game_leaderboard()
    leaderboard_data = get_leaderboard()
    
    for index, (user_id, correct_answers) in enumerate(quiz_leaderboard, start=0):
        reward1 = max(300 - (index * 5), 10)  # 第一名 100 靈石，依排名遞減 5 靈石，最低 10 靈石
        cursor.execute("UPDATE users SET spirit_stone = spirit_stone + %s WHERE user_id = %s", (reward1, user_id))

        user = await bot.fetch_user(user_id)  # 獲取使用者物件
        if user:
            try:
                await user.send(f"🏆 恭喜！你在問答排行榜中排名 **{index+1}**，獲得 **{reward1} 靈石**！🎉\n"
                                "請使用 `/靈石` 指令查看你的靈石數量！")
            except discord.Forbidden:
                print(f"❌ 無法發送 DM 給 {user_id}，可能關閉了私訊。")

    for index, (user_id, lavel, layer) in enumerate(leaderboard_data, start=0):
        reward2 = max(300 - (index * 5), 10)  # 第一名 100 靈石，依排名遞減 5 靈石，最低 10 靈石
        cursor.execute("UPDATE users SET spirit_stone = spirit_stone + %s WHERE user_id = %s", (reward2, user_id))
        
        user = await bot.fetch_user(user_id)  # 獲取使用者物件
        if user:
            try:
                await user.send(f"🏆 恭喜！你在境界排行榜中排名 **{index+1}**，獲得 **{reward2} 靈石**！🎉\n"
                                "請使用 `/靈石` 指令查看你的靈石數量！")
            except discord.Forbidden:
                print(f"❌ 無法發送 DM 給 {user_id}，可能關閉了私訊。")

    cursor.execute("UPDATE users SET correct_answers = 0")  # 重置問答排行榜
    conn.commit()

async def scheduled_reward():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        if now.weekday() == 6 and now.hour == 0:
            print("✅ 自動發放排行榜獎勵！")
            reward_players()
            await asyncio.sleep(86400)
        await asyncio.sleep(3600)

bot.tree.add_command(排行榜群組())

# ==================================================
#                  📌 遊戲相關指令
# ==================================================

class 遊戲群組(app_commands.Group):
    def __init__(self):
        super().__init__(name="遊戲", description="遊戲類的指令")

    @app_commands.command(name="1a2b", description="來挑戰 1A2B 遊戲，賺取靈石！")
    async def play1a2b(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id in command_lock and command_lock[user_id]:
            await interaction.response.send_message("請等待當前指令執行完畢後再使用。", ephemeral=True)
            return

        if interaction.channel.type != discord.ChannelType.private:
            await interaction.response.send_message("此指令僅在私訊中可用，請私訊機器人後再試！",
                                                    ephemeral=True)
            return

        command_lock[user_id] = True

        try:
            cursor.execute("SELECT spirit_stone FROM users WHERE user_id=%s", (user_id, ))
            result = cursor.fetchone()

            if not result:
                await interaction.response.send_message("請另尋財路，找不到你的帳戶。", ephemeral=True)
                return

            spirit_stone = result[0]
            if spirit_stone < 10:
                await interaction.response.send_message("你的靈石不足以參加遊戲，請確保有至少 10 靈石！", ephemeral=True)
                return

            answer = random.sample(range(1, 10), 4)
            a, b, attempts = 0, 0, 0

            await interaction.response.send_message(
                "1A2B 遊戲開始！請輸入一個不重複的四位數字（每次限時 60 秒）。", ephemeral=True)

            def check_guess(message: discord.Message):
                return (message.author == interaction.user
                        and message.channel == interaction.channel
                        and len(message.content) == 4
                        and message.content.isdigit()
                        and len(set(message.content)) == 4)

            while a != 4:
                try:
                    guess_message = await bot.wait_for("message", timeout=60, check=check_guess)
                    user_guess = list(map(int, guess_message.content))
                    attempts += 1
                    a, b = 0, 0

                    for i in range(4):
                        if user_guess[i] == answer[i]:
                            a += 1
                        elif user_guess[i] in answer:
                            b += 1

                    await interaction.followup.send(f"{a}A{b}B", ephemeral=True)

                except asyncio.TimeoutError:
                    await interaction.followup.send("操作超時，遊戲結束。", ephemeral=True)
                    command_lock[user_id] = False
                    return

            new_spirit_stone = spirit_stone + 10
            cursor.execute("UPDATE users SET spirit_stone=%s WHERE user_id=%s", (new_spirit_stone, user_id))
            conn.commit()

            await interaction.followup.send(
                f"恭喜你答對了！答案是 {''.join(map(str, answer))}，總共猜了 {attempts} 次。\n靈石 +10，你現在有 {new_spirit_stone} 靈石！",
                ephemeral=True,
            )

        except Exception as e:
            print(f"發生錯誤: {e}")
            await interaction.followup.send("發生錯誤，請稍後再試。", ephemeral=True)

        finally:
            command_lock[user_id] = False

    @app_commands.command(name="猜拳", description="參加猜拳遊戲，賺取或損失靈石！")
    async def 猜拳(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id in command_lock and command_lock[user_id]:
            await interaction.response.send_message("請等待當前指令執行完畢後再使用。", ephemeral=True)
            return

        command_lock[user_id] = True

        try:
            cursor.execute("SELECT spirit_stone FROM users WHERE user_id=%s", (user_id,))
            result = cursor.fetchone()

            if not result:
                await interaction.response.send_message("請先使用 `/入道`，獲取靈石", ephemeral=True)
                return

            spirit_stone = result[0]

            if spirit_stone < 10:
                await interaction.response.send_message("請達到 10 靈石再來參加遊戲！", ephemeral=True)
                return

            class GuessView(discord.ui.View):
                def __init__(self, user_id: int, spirit_stone: int):
                    super().__init__(timeout=15)
                    self.user_id = user_id
                    self.spirit_stone = spirit_stone

                async def process_choice(self, interaction: discord.Interaction, player_choice: str):
                    if interaction.user.id != self.user_id:
                        await interaction.response.send_message("這不是你的遊戲！", ephemeral=True)
                        return

                    bot_choice = random.choice(["✊", "✋", "✌️"])
                    win_relations = {"✊": "✌️", "✋": "✊", "✌️": "✋"}

                    if player_choice == bot_choice:
                        result_message = f"🤝 平局！你選擇了 {player_choice}，機器人選擇了 {bot_choice}。\n🔹 靈石數量不變。"
                    elif win_relations[player_choice] == bot_choice:
                        self.spirit_stone += 10
                        result_message = f"🎉 你贏了！你選擇了 {player_choice}，機器人選擇了 {bot_choice}。\n💎 靈石 +10，你現在有 {self.spirit_stone} 靈石！"
                    else:
                        self.spirit_stone -= 10
                        result_message = f"😢 你輸了！你選擇了 {player_choice}，機器人選擇了 {bot_choice}。\n💰 靈石 -10，你現在有 {self.spirit_stone} 靈石！"

                    cursor.execute("UPDATE users SET spirit_stone=%s WHERE user_id=%s", (self.spirit_stone, self.user_id))
                    conn.commit()

                    await interaction.response.edit_message(content=result_message, view=None)

                @discord.ui.button(label="石頭", emoji="✊", style=discord.ButtonStyle.primary)
                async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self.process_choice(interaction, "✊")

                @discord.ui.button(label="布", emoji="✋", style=discord.ButtonStyle.success)
                async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self.process_choice(interaction, "✋")

                @discord.ui.button(label="剪刀", emoji="✌️", style=discord.ButtonStyle.danger)
                async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self.process_choice(interaction, "✌️")

            view = GuessView(user_id=user_id, spirit_stone=spirit_stone)
            await interaction.response.send_message("✊✋✌️ 猜拳遊戲開始！請選擇你的拳頭：", view=view, ephemeral=True)

        except Exception as e:
            print(f"發生錯誤: {e}")
            await interaction.followup.send("發生錯誤，請稍後再試。", ephemeral=True)

        finally:
            command_lock[user_id] = False

    @app_commands.command(name="問答", description="進行一場問答遊戲")
    async def 問答(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in command_lock and command_lock[user_id]:
            await interaction.response.send_message("請等待當前指令執行完畢後再使用。", ephemeral=True)
            return

        command_lock[user_id] = True

        try:
            selected_question = random.choice(question_pool)
            question = selected_question['question']
            options = selected_question['options']

            random.shuffle(options)
            correct_answer_index = options.index(selected_question['correct_answer'])

            view = QuizView(user_id, correct_answer_index)
            for i, option in enumerate(options):
                view.children[i].label = option 

            await interaction.response.send_message(f"📝 **問答遊戲**：\n\n{question}", view=view, ephemeral=True)

            await view.wait()

            if not view.answer_selected:
                await interaction.followup.send(f"⏳ {interaction.user.mention} 答題超時，請在時間內作答。", ephemeral=True)

        except Exception as e:
            print(f"發生錯誤: {e}")
            await interaction.followup.send("⚠️ 發生錯誤，請稍後再試。", ephemeral=True)

        finally:
            command_lock[user_id] = False

class QuizView(discord.ui.View):

    def __init__(self, user_id, correct_answer_index):
        super().__init__(timeout=20)
        self.user_id = user_id
        self.correct_answer_index = correct_answer_index
        self.answer_selected = False

    @discord.ui.button(label="選項 1️⃣", style=discord.ButtonStyle.primary, row=0)
    async def option_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, 0)

    @discord.ui.button(label="選項 2️⃣", style=discord.ButtonStyle.primary, row=0)
    async def option_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, 1)

    @discord.ui.button(label="選項 3️⃣", style=discord.ButtonStyle.primary, row=1)
    async def option_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, 2)

    @discord.ui.button(label="選項 4️⃣", style=discord.ButtonStyle.primary, row=1)
    async def option_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, 3)

    async def handle_answer(self, interaction: discord.Interaction, answer_index):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("⚠️ 這不是你的問答遊戲！", ephemeral=True)
            return

        if self.answer_selected:
            await interaction.response.send_message("⚠️ 你已經回答過這個問題！", ephemeral=True)
            return

        self.answer_selected = True

        if answer_index == self.correct_answer_index:
            await interaction.response.send_message(f"✅ {interaction.user.mention} 回答正確！", ephemeral=True)
            cursor.execute("UPDATE users SET correct_answers = correct_answers + 1 WHERE user_id = %s", (self.user_id,))
            conn.commit()
        else:
            await interaction.response.send_message(f"❌ {interaction.user.mention} 回答錯誤。", ephemeral=True)

        self.stop()

bot.tree.add_command(遊戲群組())

# ==================================================
#                  📌 機器人啟動
# ==================================================

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)
