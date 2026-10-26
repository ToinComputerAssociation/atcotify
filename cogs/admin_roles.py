import discord
from discord import app_commands
from discord.ext import commands

from cogs.permission_checks import can_manage_bot_settings, is_guild_administrator
from cogs.school_settings import (
    get_admin_role_id_for_guild,
    set_admin_role_id_for_guild,
    unset_admin_role_id_for_guild,
)


class AdminRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="admin_role_set",
        description="副管理者ロールを設定します（サーバー管理者のみ）。",
    )
    @app_commands.describe(role="副管理者に指定するロール")
    @is_guild_administrator()
    async def admin_role_set(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        set_admin_role_id_for_guild(interaction.guild_id, role.id)
        await interaction.response.send_message(
            f"副管理者ロールを {role.mention} に設定しました。"
            "このロールのメンバーはBotの設定を変更できます"
            "（Discordサーバー自体の管理権限は付きません）。",
            ephemeral=True,
        )

    @app_commands.command(
        name="admin_role_unset",
        description="副管理者ロールを解除します（サーバー管理者のみ）。",
    )
    @is_guild_administrator()
    async def admin_role_unset(self, interaction: discord.Interaction):
        if unset_admin_role_id_for_guild(interaction.guild_id):
            await interaction.response.send_message(
                "副管理者ロールを解除しました。"
                "以降、Botの設定を変更できるのはサーバー管理者のみです。",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "副管理者ロールは設定されていません。", ephemeral=True
            )

    @app_commands.command(
        name="admin_role_show",
        description="現在の副管理者ロールを表示します。",
    )
    @can_manage_bot_settings()
    async def admin_role_show(self, interaction: discord.Interaction):
        role_id = get_admin_role_id_for_guild(interaction.guild_id)
        if role_id is None:
            await interaction.response.send_message(
                "副管理者ロールは設定されていません。"
                "Botの設定を変更できるのはサーバー管理者のみです。",
                ephemeral=True,
            )
            return
        role = interaction.guild.get_role(role_id) if interaction.guild else None
        if role is None:
            await interaction.response.send_message(
                f"副管理者ロール（ID: {role_id}）は見つかりませんでした。"
                "ロールが削除されている可能性があります。",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"副管理者ロールは {role.mention} です。", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminRoles(bot))
