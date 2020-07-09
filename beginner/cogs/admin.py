from beginner.cog import Cog, commands
import ast
import discord
import discord.ext.commands


class Admin(Cog):
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


def setup(client):
    client.add_cog(Admin(client))
