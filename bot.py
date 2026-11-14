import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "categories": {
                "phantom": [],
                "aimhack": []
            },
            "claimed_users": {}
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class MultiKeyClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 รับคีย์ Phantom", style=discord.ButtonStyle.primary, custom_id="claim_phantom")
    async def claim_phantom(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_claim(interaction, "phantom", "Phantom")

    @discord.ui.button(label="⚡ รับคีย์ Aim Hack", style=discord.ButtonStyle.success, custom_id="claim_aimhack")
    async def claim_aimhack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_claim(interaction, "aimhack", "Aim Hack")

    async def process_claim(self, interaction: discord.Interaction, category: str, cat_name: str):
        user_id = str(interaction.user.id)
        data = load_data()
        user_claim_key = f"{user_id}_{category}"

        if user_claim_key in data["claimed_users"]:
            old_key = data["claimed_users"][user_claim_key]
            await interaction.response.send_message(
                f"❌ คุณรับสิทธิ์ **{cat_name}** ไปแล้ว คีย์ของคุณคือ: ||`{old_key}`||",
                ephemeral=True
            )
            return

        if len(data["categories"][category]) == 0:
            await interaction.response.send_message(
                f"⚠️ ขออภัย คีย์ **{cat_name}** หมดแล้ว",
                ephemeral=True
            )
            return

        claimed_key = data["categories"][category].pop(0)
        data["claimed_users"][user_claim_key] = claimed_key
        save_data(data)

        await interaction.response.send_message(
            f"✅ รับคีย์ **{cat_name}** สำเร็จ คีย์ของคุณคือ: ||`{claimed_key}`||",
            ephemeral=True
        )

@bot.event
async def on_ready():
    bot.add_view(MultiKeyClaimView())
    print(f"บอทออนไลน์แล้วในชื่อ: {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    data = load_data()
    count_phantom = len(data["categories"]["phantom"])
    count_aimhack = len(data["categories"]["aimhack"])

    embed = discord.Embed(
        title="🌟 REFLEXZOFFICIAL แจกคีย์ฟรี",
        description=(
            "กดปุ่มด้านล่างเพื่อรับคีย์ที่คุณต้องการได้เลย!\n\n"
            f"📦 สต็อก Phantom เหลือ: `{count_phantom}` คีย์\n"
            f"📦 สต็อก Aim Hack เหลือ: `{count_aimhack}` คีย์"
        ),
        color=discord.Color.from_rgb(135, 206, 250)
    )
    await ctx.send(embed=embed, view=MultiKeyClaimView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def addkey(ctx, category: str, *new_keys):
    data = load_data()
    if category not in data["categories"]:
        await ctx.send("⚠️ หมวดหมู่ไม่ถูกต้อง ใช้ phantom หรือ aimhack เท่านั้น", delete_after=5)
        return

    data["categories"][category].extend(new_keys)
    save_data(data)
    
    await ctx.message.delete()
    await ctx.send(f"✅ เพิ่มคีย์เข้า **{category}** จำนวน `{len(new_keys)}` คีย์เรียบร้อย", delete_after=10)

@bot.command()
@commands.has_permissions(administrator=True)
async def resetall(ctx):
    data = load_data()
    data["claimed_users"] = {}
    save_data(data)

    await ctx.message.delete()
    await ctx.send("🔄 รีเซ็ตสิทธิ์ทั้งหมดแล้ว ทุกคนกดรับใหม่ได้", delete_after=10)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    user_id = str(member.id)
    data = load_data()
    
    removed = False
    for k in list(data["claimed_users"].keys()):
        if k.startswith(user_id):
            del data["claimed_users"][k]
            removed = True

    if removed:
        save_data(data)
        await ctx.send(f"🔄 รีเซ็ตสิทธิ์ให้ {member.mention} เรียบร้อย", delete_after=10)
    else:
        await ctx.send(f"⚠️ {member.mention} ยังไม่เคยกดรับคีย์", delete_after=5)

    await ctx.message.delete()

import os
bot.run(os.getenv("DISCORD_TOKEN"))