import discord
from discord.ext import commands
import json
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "categories": {},
            "claimed_users": {}
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ปุ่มกดแบบสร้างอัตโนมัติตามชื่อหมวดหมู่
class DynamicKeyButton(discord.ui.Button):
    def __init__(self, category_name: str, index: int):
        # สลับสีปุ่มให้อัตโนมัติ (น้ำเงิน, เขียว, เทา, แดง)
        styles = [
            discord.ButtonStyle.primary,
            discord.ButtonStyle.success,
            discord.ButtonStyle.secondary,
            discord.ButtonStyle.danger
        ]
        style = styles[index % len(styles)]
        super().__init__(
            label=f"🎁 รับคีย์ {category_name}",
            style=style,
            custom_id=f"claim_{category_name}"
        )
        self.category_name = category_name

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()
        user_claim_key = f"{user_id}_{self.category_name}"

        if user_claim_key in data["claimed_users"]:
            old_key = data["claimed_users"][user_claim_key]
            await interaction.response.send_message(
                f"❌ คุณรับสิทธิ์ **{self.category_name}** ไปแล้ว คีย์ของคุณคือ: ||`{old_key}`||",
                ephemeral=True
            )
            return

        if self.category_name not in data["categories"] or len(data["categories"][self.category_name]) == 0:
            await interaction.response.send_message(
                f"⚠️ ขออภัย คีย์ **{self.category_name}** หมดแล้ว",
                ephemeral=True
            )
            return

        claimed_key = data["categories"][self.category_name].pop(0)
        data["claimed_users"][user_claim_key] = claimed_key
        save_data(data)

        await interaction.response.send_message(
            f"✅ รับคีย์ **{self.category_name}** สำเร็จ คีย์ของคุณคือ: ||`{claimed_key}`||",
            ephemeral=True
        )

class DynamicKeyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        data = load_data()
        for idx, cat_name in enumerate(data["categories"].keys()):
            if idx < 25: # Discord จำกัดสูงสุด 25 ปุ่มต่อข้อความ
                self.add_item(DynamicKeyButton(cat_name, idx))

@bot.event
async def on_ready():
    bot.add_view(DynamicKeyView())
    print(f"บอทออนไลน์แล้วในชื่อ: {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    data = load_data()
    if not data["categories"]:
        await ctx.send("⚠️ ยังไม่มีสินค้าในระบบ กรุณาเพิ่มสินค้าด้วยคำสั่ง `!addkey \"ชื่อสินค้า\" คีย์1 คีย์2` ก่อนครับ", delete_after=10)
        return

    stock_lines = []
    for cat_name, keys in data["categories"].items():
        stock_lines.append(f"📦 สต็อก **{cat_name}** เหลือ: `{len(keys)}` คีย์")

    embed = discord.Embed(
        title="🌟 REFLEXZOFFICIAL แจกคีย์ฟรี",
        description="กดปุ่มด้านล่างเพื่อรับคีย์ที่คุณต้องการได้เลย!\n\n" + "\n".join(stock_lines),
        color=discord.Color.from_rgb(135, 206, 250)
    )
    await ctx.send(embed=embed, view=DynamicKeyView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def addkey(ctx, category: str, *new_keys):
    if not new_keys:
        await ctx.send("⚠️ กรุณาใส่คีย์อย่างน้อย 1 คีย์ เช่น `!addkey \"Drip Wire\" KEY-1 KEY-2`", delete_after=8)
        return

    data = load_data()
    is_new = False
    if category not in data["categories"]:
        data["categories"][category] = []
        is_new = True

    data["categories"][category].extend(new_keys)
    save_data(data)
    
    # อัปเดตปุ่มกดให้บอทรู้จักหมวดหมู่ใหม่ทันทีโดยไม่ต้องรีสตาร์ท
    bot.add_view(DynamicKeyView())

    await ctx.message.delete()
    msg = f"✅ สร้างสินค้าใหม่ **{category}** และเพิ่ม `{len(new_keys)}` คีย์เรียบร้อย (พิมพ์ `!setup` ใหม่เพื่ออัปเดตปุ่ม)" if is_new else f"✅ เพิ่มคีย์เข้า **{category}** จำนวน `{len(new_keys)}` คีย์เรียบร้อย"
    await ctx.send(msg, delete_after=10)

@bot.command()
@commands.has_permissions(administrator=True)
async def delcat(ctx, category: str):
    data = load_data()
    if category in data["categories"]:
        del data["categories"][category]
        save_data(data)
        await ctx.send(f"🗑️ ลบสินค้า **{category}** ออกจากระบบเรียบร้อย (พิมพ์ `!setup` ใหม่เพื่ออัปเดตปุ่ม)", delete_after=10)
    else:
        await ctx.send(f"⚠️ ไม่พบชื่อสินค้า **{category}** ในระบบ", delete_after=5)
    await ctx.message.delete()

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

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))