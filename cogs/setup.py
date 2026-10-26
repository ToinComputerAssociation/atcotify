"""初期設定コマンド /setup。

Botを新しいサーバーに入れた直後に使うコマンド。学校を設定し、
現在設定状況と次にやることをまとめて表示する。
各通知チャンネルの設定は、それぞれの専用コマンドで行う。
"""

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permission_checks import can_manage_bot_settings
from cogs.school_rank import filter_school_choices, load_all_school_names
from cogs.school_settings import (
    DEFAULT_SCHOOL_TYPE,
    format_school_label,
    get_admin_role_id_for_guild,
    get_school_for_guild,
    infer_school_type,
    normalize_school_type,
    set_school_for_guild,
)

NEXT_STEP_COMMANDS = [
    ("/admin_role_set", "副管理者ロールの設定（サーバー管理者のみ）"),
    ("/reminder---set_channel", "コンテストリマインダーの送信先"),
    ("/result---set_channel", "コンテスト結果の自動送信先"),
    ("/thread---set_channel", "コンテスト前スレッド作成先"),
    ("/school_rank_set_ch", "学校順位の定期通知先"),
    ("/school_student_rank_set_ch", "生徒順位の定期通知先"),
]


def describe_setup_state(
    school_name: str | None,
    school_type: str | None,
    admin_role_id: int | None,
) -> dict[str, str]:
    """設定状況の表示文字列を作る。"""
    return {
        "school": (
            format_school_label(school_name, school_type)
            if school_name
            else "未設定"
        ),
        "admin_role": f"<@&{admin_role_id}>" if admin_role_id else "未設定",
    }


def build_next_steps(school_is_set: bool) -> list[str]:
    steps = []
    if not school_is_set:
        steps.append("`/setup 学校名` または `/school_set` で学校を設定する")
    steps.extend(f"`{name}` — {desc}" for name, desc in NEXT_STEP_COMMANDS)
    return steps


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def setup_school_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        schools = load_all_school_names()
        return [
            app_commands.Choice(
                name=format_school_label(school_name, school_type),
                value=school_name,
            )
            for school_name, school_type in filter_school_choices(schools, current)
        ]

    @app_commands.command(
        name="setup",
        description="初期設定：学校を設定し、このサーバーの設定状況を表示します。",
    )
    @app_commands.describe(
        school_name="このサーバーの学校名（AJLの学校一覧から候補が出ます）",
        school_type="中学／高校。学校名から自動で分かる場合は省略できます。",
    )
    @app_commands.choices(
        school_type=[
            app_commands.Choice(name="中学", value="junior_high"),
            app_commands.Choice(name="高校", value="high"),
        ]
    )
    @app_commands.autocomplete(school_name=setup_school_autocomplete)
    @can_manage_bot_settings()
    async def setup_command(
        self,
        interaction: discord.Interaction,
        school_name: str | None = None,
        school_type: str = DEFAULT_SCHOOL_TYPE,
    ):
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "このコマンドはサーバー内で実行してください。", ephemeral=True
            )
            return

        if school_name and school_name.strip():
            resolved_type = infer_school_type(
                school_name, normalize_school_type(school_type)
            )
            set_school_for_guild(interaction.guild_id, school_name, resolved_type)

        school = get_school_for_guild(interaction.guild_id)
        state = describe_setup_state(
            school[0] if school else None,
            school[1] if school else None,
            get_admin_role_id_for_guild(interaction.guild_id),
        )
        embed = discord.Embed(
            title="Atcotify セットアップ",
            description="このサーバーの設定状況です。",
            color=discord.Color.green(),
        )
        embed.add_field(name="学校", value=state["school"], inline=False)
        embed.add_field(name="副管理者ロール", value=state["admin_role"], inline=False)
        embed.add_field(
            name="次にやること",
            value="\n".join(f"・{step}" for step in build_next_steps(school is not None)),
            inline=False,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Setup(bot))
