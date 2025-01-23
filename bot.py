import os
import pymysql
import sys
import json
import math
import random
import psutil
import atexit
import discord
import asyncio
import datetime
import requests
import subprocess
from queue import Queue
from typing import Optional
from discord import app_commands
from keep_alive import keep_alive
from discord.ext import commands
from discord.ui import Select, View

# 連接 MySQL
MYSQLHOST = "monorail.proxy.rlwy.net"
MYSQLPORT = 18424
MYSQLUSER = "root"
MYSQLPASSWORD = "IebRbauIYseiiwoahmZNbUECpNtoOYpS"
MYSQLDATABASE = "railway"

def get_conn():
    return pymysql.connect(
        host=MYSQLHOST,
        port=MYSQLPORT,
        user=MYSQLUSER,
        password=MYSQLPASSWORD,
        database=MYSQLDATABASE,
        charset="utf8mb4",
        autocommit=True
    )

def get_cursor():
    conn = get_conn()
    return conn.cursor()

conn = get_conn()
cursor = get_cursor()

# Discord Bot 設置
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("衝破空間壁障中~"))
    try:
        synced = await bot.tree.sync()
        print(f"✅ 成功同步 {len(synced)} 個指令！")
    except Exception as e:
        print(f"❌ 無法同步指令: {e}")

# MySQL 備份指令
backup_filename = f"backup_{datetime.datetime.now().strftime('%Y%m%d')}.sql"
backup_cmd = f"mysqldump -h {MYSQLHOST} -P {MYSQLPORT} -u {MYSQLUSER} -p{MYSQLPASSWORD} {MYSQLDATABASE} > {backup_filename}"
subprocess.run(backup_cmd, shell=True)
print(f"✅ 已備份 MySQL 到 {backup_filename}")

@bot.tree.command(name="入道", description="開始你的修煉之旅！")
async def 入道(interaction: discord.Interaction):
    user_id = interaction.user.id
    cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        await interaction.response.send_message("你已經是修煉者，無需再次入道。")
    else:
        cursor.execute(
            """
            INSERT INTO users (user_id, spirit_stone, level, layer, body_level, body_layer, attack, health, defense, cultivation, quench) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, 0, '凡人', '一層', '凡人肉體', '一階', 20, 100, 10, 0, 0)
        )
        await interaction.response.send_message("歡迎您踏入修仙之旅，請試著摸索其他指令")

@bot.tree.command(name="查看修為", description="查看你的修練者詳細資料")
async def 查看修為(interaction: discord.Interaction):
    user_id = interaction.user.id
    cursor.execute(
        """
        SELECT level, layer, body_level, body_layer, cultivation, quench, attack, defense, health, spirit_stone 
        FROM users WHERE user_id=%s
        """,
        (user_id,))
    user_info = cursor.fetchone()

    if not user_info:
        await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
        return

    level, layer, body_level, body_layer, cultivation, quench, attack, defense, health, spirit_stone = user_info
    embed = discord.Embed(title="修練者資料", color=discord.Color.orange())
    embed.add_field(name="境界", value=level, inline=True)
    embed.add_field(name="層數", value=layer, inline=True)
    embed.add_field(name="修為", value=cultivation, inline=True)
    embed.add_field(name="煉體", value=body_level, inline=True)
    embed.add_field(name="階級", value=body_layer, inline=True)
    embed.add_field(name="攻擊", value=attack, inline=True)
    embed.add_field(name="防禦", value=defense, inline=True)
    embed.add_field(name="氣血", value=health, inline=True)
    embed.add_field(name="靈石", value=spirit_stone, inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)
