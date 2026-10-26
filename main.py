import traceback

import discord
from discord.ext import commands

from env.config import Config

INITIAL_EXTENSIONS = [
    "cogs.school_rank",
    "cogs.school_student_rank",
    "cogs.help",
    "cogs.reminder",
    "cogs.result",
    "cogs.perf_score",
    "cogs.threads",
    "cogs.contest_data",
    "cogs.admin_roles",
    "cogs.setup",
]

config = Config()

TOKEN = config.token

# Intents は従来どおり全て有効にする（jishaku が MESSAGE CONTENT を
# 必要とするため、当面は削減しない）。100サーバー規模になったら
# 特権 Intents の要否を再検討する。
intents = discord.Intents.all()
activity = discord.Activity(name="起動中", type=discord.ActivityType.playing)

bot = commands.Bot(command_prefix="/", intents=intents, activity=activity)


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            name=str(len(bot.guilds)) + "サーバー", type=discord.ActivityType.competing
        )
    )
    try:
        await bot.load_extension("jishaku")
        print("jishakuを読み込みました\n")
    except Exception as e:
        print(
            "jishakuの読み込み中にエラーが発生しました: ",
            "".join(traceback.format_exception(e)),
        )
    try:
        print("スラッシュコマンドを読み込み中...\n")
        await load_extension()
        print("スラッシュコマンドを読み込みました\n")
    except Exception as e:
        print(
            "スラッシュコマンドの読み込み中にエラーが発生しました: ",
            "".join(traceback.format_exception(e)),
        )

    try:
        print("スラッシュコマンドを同期中...")
        synced = await bot.tree.sync()
        print("スラッシュコマンドを同期しました: ", len(synced))
        print("-----------")
        print("起動しました")
        print("-----------")
    except Exception as e:
        print(
            "スラッシュコマンドの同期中にエラーが発生しました: ",
            "".join(traceback.format_exception(e)),
        )


async def load_extension():
    for cog in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(cog)
            print(f"{cog}を読み込みました")
        except Exception as e:
            print(
                f"{cog}の読み込み中にエラーが発生しました: ",
                "".join(traceback.format_exception(e)),
            )


@bot.tree.error
async def on_error(interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        missing_permissions = "、".join(error.missing_permissions)
        message = (
            "このコマンドを実行する権限がありません。"
            f"必要な権限: {missing_permissions}"
        )
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return

    # 詳細（トレースバック）は運用ログにのみ出し、利用者には簡潔に伝える
    print("".join(traceback.format_exception(error)))
    message = (
        "エラーが発生しました。しばらくしてからもう一度お試しください。"
        "解決しない場合はBotの管理者にお知らせください。"
    )
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


bot.run(token=TOKEN)
