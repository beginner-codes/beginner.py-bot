from beginner.cog import Cog, commands
from beginner.colors import *
from beginner.scheduler import schedule
from beginner.tags import tag
from datetime import timedelta
import ast
import nextcord
import nextcord.ext.commands


class Admin(Cog):
    @Cog.command()
    async def sus(self, ctx: nextcord.ext.commands.Context):
        members = [ctx.author]
        if ctx.author.guild_permissions.manage_messages:
            members = ctx.message.mentions

        role = nextcord.utils.get(ctx.guild.roles, name="🚨sus🚨")
        for user in members:
            if isinstance(user, nextcord.Member):
                if role not in user.roles:
                    await user.add_roles(role)
                    schedule(
                        "remove-sus",
                        timedelta(days=1),
                        self.remove_sus,
                        user.id,
                        ctx.guild.id,
                    )
                await ctx.send(f"🚨 {user.mention} is sus 🚨")

    @Cog.command()
    async def list_sus(self, ctx: nextcord.ext.commands.Context):
        await ctx.reply(
            embed=nextcord.Embed(
                title=f"🚨Sus Members 🚨",
                description="\n".join(
                    member.mention
                    for member in nextcord.utils.get(
                        ctx.guild.roles, name="🚨sus🚨"
                    ).members
                )
                or "*No One Is Sus*",
                color=0x00A35A,
            )
        )

    @tag("schedule", "remove-sus")
    async def remove_sus(self, user_id, guild_id):
        guild = self.client.get_guild(guild_id)
        member = guild.get_member(user_id)
        if member:
            role = nextcord.utils.get(guild.roles, name="🚨sus🚨")
            await member.remove_roles(role)

    @Cog.group()
    @commands.has_guild_permissions(manage_messages=True)
    async def silence(self, ctx: nextcord.ext.commands.Context):
        if ctx.invoked_subcommand:
            return

        role = self.get_role("coders")
        permissions = role.permissions
        permissions.send_messages = False
        await role.edit(permissions=permissions)

        await ctx.send(
            embed=nextcord.Embed(
                description="The server has been silenced. Use `!silence stop` to end the silence.",
                color=RED,
                title="Silence Activated",
            )
        )

        await self.get_channel("mod-action-log").send(
            embed=nextcord.Embed(
                description=f"The server has been silenced by {ctx.author.mention}.",
                color=RED,
                title="Silence Activated",
            )
        )

    @silence.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def stop(self, ctx: nextcord.ext.commands.Context):
        role = self.get_role("coders")
        permissions = role.permissions
        permissions.send_messages = True
        await role.edit(permissions=permissions)

        await ctx.send(
            embed=nextcord.Embed(
                description="The server silence has been stopped.",
                color=GREEN,
                title="Silence Deactivated",
            )
        )

        await self.get_channel("mod-action-log").send(
            embed=nextcord.Embed(
                description=f"The server silence has been stopped by {ctx.author.mention}.",
                color=GREEN,
                title="Silence Deactivated",
            )
        )

    @Cog.group()
    @commands.has_guild_permissions(manage_channels=True)
    async def channel(self, ctx: nextcord.ext.commands.Context):
        return

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def details(
        self, ctx: nextcord.ext.commands.Context, channel: nextcord.TextChannel
    ):
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
        ctx: nextcord.ext.commands.Context,
        channel: nextcord.TextChannel,
        *,
        reason: str = "Delete channel",
    ):
        await channel.delete(reason=reason)
        await ctx.send(f"{ctx.author.mention} #{channel.name} has been deleted")

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def clone(
        self,
        ctx: nextcord.ext.commands.Context,
        channel: nextcord.TextChannel,
        name: str,
        *,
        reason: str = "Delete channel",
    ):
        new_channel: nextcord.TextChannel = await channel.clone(
            name=name, reason=reason
        )
        await new_channel.edit(position=channel.position + 1)
        await channel.send(
            f"{ctx.author.mention} channel cloned to {new_channel.mention}"
        )

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def edit(
        self,
        ctx: nextcord.ext.commands.Context,
        channel: nextcord.TextChannel,
        *,
        raw_settings: str,
    ):
        settings = ast.literal_eval(raw_settings)
        await channel.edit(**settings)
        await ctx.send(f"{ctx.author.mention} {channel.mention} has been edited")

    @channel.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def permissions(
        self,
        ctx: nextcord.ext.commands.Context,
        channel: nextcord.TextChannel,
        raw_role: str,
        *,
        raw_permissions: str,
    ):
        role = self.get_role(raw_role.casefold())
        permissions = channel.overwrites_for(role)
        permissions.update(**ast.literal_eval(raw_permissions))
        await channel.set_permissions(target=role, overwrite=permissions)
        await ctx.send(
            embed=nextcord.Embed(
                description=f"{ctx.author.mention} {channel.mention} permissions for {role.mention} have been updated",
                color=BLUE,
            )
        )


def setup(client):
    client.add_cog(Admin(client))
