from beginner.cog import Cog, commands
from beginner.colors import *
import ast
import discord
import discord.ext.commands


class Admin(Cog):
    @Cog.group()
    @commands.has_guild_permissions(manage_messages=True)
    async def silence(self, ctx: discord.ext.commands.Context):
        if ctx.invoked_subcommand:
            return

        role = self.get_role("coders")
        permissions = role.permissions
        permissions.send_messages = False
        await role.edit(permissions=permissions)

        await ctx.send(
            embed=discord.Embed(
                description="The server has been silenced. Use `!silence stop` to end the silence.",
                color=RED,
                title="Silence Activated"
            )
        )

        await self.get_channel("mod-action-log").send(
            embed=discord.Embed(
                description=f"The server has been silenced by {ctx.author.mention}.",
                color=RED,
                title="Silence Activated"
            )
        )

    @silence.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def stop(self, ctx: discord.ext.commands.Context):
        role = self.get_role("coders")
        permissions = role.permissions
        permissions.send_messages = True
        await role.edit(permissions=permissions)

        await ctx.send(
            embed=discord.Embed(
                description="The server silence has been stopped.",
                color=GREEN,
                title="Silence Deactivated"
            )
        )

        await self.get_channel("mod-action-log").send(
            embed=discord.Embed(
                description=f"The server silence has been stopped by {ctx.author.mention}.",
                color=GREEN,
                title="Silence Deactivated"
            )
        )

    @Cog.group()
    @commands.has_guild_permissions(manage_channels=True)
    async def channel(self, ctx: discord.ext.commands.Context):
        return

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def details(self, ctx: discord.ext.commands.Context, channel: discord.TextChannel):
        await ctx.send(
            f"**#{channel.name}**\n"
            f"Position: {channel.position}\n"
            f"Topic: {channel.topic}\n"
            f"NSFW: {channel.nsfw}\n"
            f"Slowmode Delay: {channel.slowmode_delay}\n"
            f"Category: {channel.category.name}"
        )

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def delete(
            self,
            ctx: discord.ext.commands.Context,
            channel: discord.TextChannel,
            *,
            reason: str = "Delete channel"
    ):
        await channel.delete(reason=reason)
        await ctx.send(f"{ctx.author.mention} #{channel.name} has been deleted")

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def clone(
            self,
            ctx: discord.ext.commands.Context,
            channel: discord.TextChannel,
            name: str,
            *,
            reason: str = "Delete channel"
    ):
        new_channel: discord.TextChannel = await channel.clone(name=name, reason=reason)
        await new_channel.edit(position=channel.position + 1)
        await channel.send(f"{ctx.author.mention} channel cloned to {new_channel.mention}")

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def edit(
            self,
            ctx: discord.ext.commands.Context,
            channel: discord.TextChannel,
            *,
            raw_settings: str
    ):
        settings = ast.literal_eval(raw_settings)
        await channel.edit(**settings)
        await ctx.send(f"{ctx.author.mention} {channel.mention} has been edited")

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def permissions(
            self,
            ctx: discord.ext.commands.Context,
            channel: discord.TextChannel,
            raw_role: str,
            *,
            raw_permissions: str
    ):
        role = self.get_role(raw_role.casefold())
        permissions = channel.overwrites_for(role)
        permissions.update(**ast.literal_eval(raw_permissions))
        await channel.set_permissions(target=role, overwrite=permissions)
        await ctx.send(
            embed=discord.Embed(
                description=f"{ctx.author.mention} {channel.mention} permissions for {role.mention} have been updated",
                color=BLUE
            )
        )


def setup(client):
    client.add_cog(Admin(client))
