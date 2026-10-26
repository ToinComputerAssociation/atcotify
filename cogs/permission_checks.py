import discord
from discord import app_commands

from cogs.school_settings import get_admin_role_id_for_guild


async def user_can_manage_bot_settings(interaction: discord.Interaction) -> bool:
    """Bot設定を変更できるユーザーか（サーバー管理者または副管理者ロール保持者）。"""
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    admin_role_id = get_admin_role_id_for_guild(interaction.guild.id)
    if admin_role_id is None:
        return False
    return any(role.id == admin_role_id for role in interaction.user.roles)


async def user_is_guild_administrator(interaction: discord.Interaction) -> bool:
    """サーバー管理者か。"""
    return (
        interaction.guild is not None
        and isinstance(interaction.user, discord.Member)
        and interaction.user.guild_permissions.administrator
    )


def can_manage_bot_settings():
    async def predicate(interaction: discord.Interaction) -> bool:
        if await user_can_manage_bot_settings(interaction):
            return True
        raise app_commands.MissingPermissions(["administrator"])

    return app_commands.check(predicate)


def is_guild_administrator():
    async def predicate(interaction: discord.Interaction) -> bool:
        if await user_is_guild_administrator(interaction):
            return True
        raise app_commands.MissingPermissions(["administrator"])

    return app_commands.check(predicate)


async def ensure_can_manage_bot_settings(interaction: discord.Interaction) -> bool:
    """Viewの操作時チェック用。権限がなければエフェメラルで通知して False を返す。"""
    if await user_can_manage_bot_settings(interaction):
        return True
    message = (
        "この設定を変更する権限がありません。"
        "サーバー管理者または副管理者に依頼してください。"
    )
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)
    return False
