from beginner.cog import Cog
from beginner.colors import *
from beginner.brainfuck_runner import BrainfuckInterpreter
from datetime import datetime, timedelta
from typing import Tuple
import asyncio
import black
import dis
import nextcord
import io
import json
import pathlib
import re


class CodeRunner(Cog):
    def __init__(self, client):
        super().__init__(client)
        self._exec_rate_limit = {}
        self._code_runner_emojis = "▶️⏯"
        self._formatting_emojis = "✏️📝"
        self._delete_emojis = "🗑️"

    @Cog.command()
    async def dis(self, ctx, *, content=""):
        source = re.match(
            r"^(?:```(?:py|python)\n)?\n?(.+?)(?:\n```)?$", content, re.DOTALL
        ).groups()[0]
        buffer = io.StringIO()
        try:
            code = compile(source, "<discord>", "exec")
        except SyntaxError as excp:
            msg, (file, line_no, column, line) = excp.args
            spaces = " " * (column - 1)
            await ctx.send(
                embed=nextcord.Embed(
                    title="Disassemble - Exception",
                    description=f"```py\nLine {line_no}\n{line.rstrip()}\n{spaces}^\nSyntaxError: {msg}\n```",
                    color=YELLOW,
                )
            )
            return

        dis.dis(code, file=buffer)
        await ctx.send(
            embed=nextcord.Embed(
                title="Disassemble - Byte Code Instructions",
                description=f"```asm\n{buffer.getvalue()}\n```",
                color=BLUE,
            )
        )

    @Cog.command()
    async def exec(self, ctx, *, content=""):
        if content.strip().startswith("```bf") or content.strip().startswith(
            "```brainfuck"
        ):
            await self._exec_brainfuck(ctx.message, content)
            return

        if content.strip() == "modules":
            with (
                pathlib.Path(__file__).parent.parent / "allowed_modules.txt"
            ).open() as allowed_modules_file:
                allowed_modules_list = list(
                    line.strip()
                    for line in allowed_modules_file.readlines()
                    if line.strip()
                )
                length = len(max(allowed_modules_list, key=len)) + 2
                allowed_modules = "".join(
                    f"{module:{length}}" for module in allowed_modules_list
                )
            await ctx.send(
                embed=nextcord.Embed(
                    description=f"Here are all of the allowed modules:\n```\n{allowed_modules}\n```",
                    title="✅ Exec/Eval Allowed Modules",
                    color=BLUE,
                )
            )
            return

        message: nextcord.Message = ctx.message
        if message.reference:
            ref_message = await ctx.channel.fetch_message(message.reference.message_id)
            await self._exec(
                ctx.message,
                ref_message.content[ref_message.content.find("`") :].strip(),
                ctx.author,
                user_input=message.clean_content[message.clean_content.find(" ") + 1 :],
            )
            return

        await self._exec(ctx.message, content, ctx.author)

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction: nextcord.RawReactionActionEvent):
        if (
            reaction.emoji.name
            not in self._code_runner_emojis + self._formatting_emojis + self._delete_emojis
        ):
            return

        now = datetime.utcnow()
        delta = now - self._exec_rate_limit.get(reaction.message_id, now)
        channel: nextcord.TextChannel = self.client.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if timedelta(seconds=0) < delta < timedelta(minutes=2):
            await message.remove_reaction(reaction.emoji, reaction.member)
            return

        member = self.server.get_member(reaction.user_id)
        if member.bot:
            return

        self._exec_rate_limit[reaction.message_id] = now

        if reaction.emoji.name in self._code_runner_emojis and self.settings.get(
            "EXEC_ENABLED", False
        ):
            await self._exec(message, message.content, reaction.member)

        elif reaction.emoji.name in self._formatting_emojis:
            await self._black_formatting(message, message.content, reaction.member)

        elif (
            reaction.emoji.name in self._delete_emojis
            and reaction.member in message.mentions
            and message.author == self.client.user
            and "Exception Raised" in message.embeds[0].title
        ):
            await message.delete()

    async def _exec(
        self,
        message: nextcord.Message,
        content: str,
        member: nextcord.Member = None,
        user_input: str = "",
    ):
        if (
            not len(content.strip())
            or content.find("```") < 0
            or content.rfind("```") <= 0
        ):
            await message.channel.send(
                content="" if member is None else member.mention,
                embed=nextcord.Embed(
                    title="Exec - No Code",
                    description=(
                        "\n**NO PYTHON CODE BLOCK FOUND**\n\nThe command format is as follows:\n\n"
                        "\n!exec \\`\\`\\`py\nYOUR CODE HERE\n\\`\\`\\`\n"
                    ),
                    color=RED,
                ),
                reference=message,
                allowed_mentions=nextcord.AllowedMentions(
                    replied_user=member is None, users=[member] if member else False
                ),
            )
            return

        title = "✅ Exec - Success"
        color = BLUE

        restricted = not member.guild_permissions.manage_messages
        if not restricted:
            title += " (Super User 🦸)"

        if user_input:
            code, *_ = re.match(
                r"^.*?```(?:python|py)?\s*(.+?)\s*```.*$", content, re.DOTALL
            ).groups()
        else:
            code, user_input = re.match(
                r"^.*?```(?:python|py)?\s*(.+?)\s*```\s*(.+)?$", content, re.DOTALL
            ).groups()

        out, err, duration = await self.code_runner(
            "exec",
            code,
            user_input,
            restricted=restricted,
        )

        output = [out]
        if err:
            title = "❌ Exec - Exception Raised"
            color = YELLOW
            output.append(err)

        elif not out:
            output = ["*No output or exceptions*"]

        out = "\n\n".join(output)
        old_out = out
        if out.count("\n") > 30:
            lines = out.split("\n")
            out = "\n".join(
                lines[:15]
                + [f".\n.\nRemoved {len(lines) - 30:,} lines\n.\n."]
                + lines[-17:]
            )
        if len(out) > 1000:
            out = (
                old_out[:497]
                + f"\n.\n.\nRemoved {len(old_out) - 1000:,} characters\n.\n.\n"
                + old_out[-504:]
            )
        embed = nextcord.Embed(
            title=title, description=f"```\n{out}\n```", color=color
        ).set_footer(text=f"!exec modules | Completed in {duration:0.4f} milliseconds")
        if "https://xkcd.com/353/" in old_out:
            embed.set_image(url="https://imgs.xkcd.com/comics/python.png")
        await message.channel.send(
            content="" if member is None else member.mention,
            embed=embed,
            reference=message,
            allowed_mentions=nextcord.AllowedMentions(
                replied_user=member is None,
                users=[member] if member else False,
                roles=[],
            ),
        )

    async def _exec_brainfuck(self, message: nextcord.Message, content: str):
        title = "✅ Exec Brainfuck - Success"
        color = BLUE

        code, user_input = re.match(
            r"^.*?```(?:bf|brainfuck)?\s*(.+?)\s*```\s*(.+)?$", content, re.DOTALL
        ).groups()

        interpreter = BrainfuckInterpreter(
            code, user_input + "\n" if user_input else ""
        )
        out, err = interpreter.run()

        output = [out]
        if err:
            title = "❌ Exec - Exception Raised"
            color = YELLOW
            output.append(err)

        elif not out:
            output = ["*No output or exceptions*"]

        out = "\n\n".join(output)
        if len(out) > 1000:
            out = out[:497] + "\n.\n.\n.\n" + out[-504:]
        await message.channel.send(
            embed=nextcord.Embed(
                title=title, description=f"```\n{out}\n```", color=color
            ),
            reference=message,
            allowed_mentions=nextcord.AllowedMentions(replied_user=True),
        )

    async def _black_formatting(
        self, message: nextcord.Message, content: str, member: nextcord.Member = None
    ):
        if (
            not len(content.strip())
            or content.find("```") < 0
            or content.rfind("```") <= 0
        ):
            code = content
        else:
            code = re.match(
                r"^.*?```(?:py|python)?\s*(.+?)\s*```\s*$", content, re.DOTALL
            ).group(1)

        title = "✅ Formatting - Success"
        color = BLUE

        try:
            formatted_code = f"py\n{black.format_file_contents(code, mode=black.FileMode(), fast=True)}\n"
        except black.NothingChanged:
            title = "✅ Formatting - Nothing Changed"
            color = BLUE
            formatted_code = "Code already formatted correctly."
        except black.InvalidInput as e:
            title = "❌ Formatting - Invalid Input"
            color = YELLOW
            formatted_code = f"\n{e}\n"

        await message.channel.send(
            content="" if member is None else member.mention,
            embed=nextcord.Embed(
                title=title, description=f"```{formatted_code}```", color=color
            ),
            reference=message,
            allowed_mentions=nextcord.AllowedMentions(
                replied_user=member is None, users=[member] if member else False
            ),
        )

    async def code_runner(
        self, mode: str, code: str, user_input: str = "", restricted=True
    ) -> Tuple[str, str, float]:
        proc = await asyncio.create_subprocess_shell(
            f"python -m beginner.runner {mode}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        data = json.dumps(
            {
                "code": code.replace(" ", " "),
                "input": user_input,
                "restricted": restricted,
            }
        ).encode()
        self.logger.debug(f"Running code:\n{code}")
        stdout, stderr = await proc.communicate(data)
        out, duration = self._split_run_time(stdout.decode())

        self.logger.debug(f"Done {duration}\n{out}\n{stderr}\n{duration}")
        return out, stderr.decode(), duration

    @Cog.command()
    async def eval(self, ctx, *, content):
        if content.casefold().strip() == "help":
            await ctx.send(
                embed=nextcord.Embed(
                    title="Statement Eval - Help",
                    description=(
                        "This command allows you to run a single statement and see the results. For security "
                        "reasons what code you can run is very limited."
                    ),
                    color=0xFBBC05,
                ),
            )
            return

        code = re.sub(r"^\s*(```(python|py)|`?)\s*|\s*(```|`)\s*$", "", content)
        title = "✅ Eval - Success"
        color = BLUE

        code_message = f"\n```py\n>>> {code}"

        out, err, duration = await self.code_runner("eval", code)

        output = out
        if err:
            title = "❌ Eval - Exception Raised"
            color = YELLOW
            output = err

        await ctx.send(
            embed=nextcord.Embed(
                title=title,
                description=f"{code_message.strip()}\n{output}\n```",
                color=color,
            ).set_footer(text=f"Completed in {duration:0.4f} milliseconds"),
            reference=ctx.message,
            mention_author=True,
        )

    @Cog.command()
    async def docs(self, ctx, *, content):
        if not self.settings.get("EVAL_ENABLED", False):
            await ctx.send("The docs command has been disabled.")
            return

        code = re.sub(r"^\s*(```(python|py)|`?)\s*|\s*(```|`)\s*$", "", content)
        title = "Code Docs"
        color = 0x4285F4

        code_message = f"{ctx.author.mention} here are the docs you requested"
        code_message += f"\n```py\n{code}```"

        message, exceptions = await self.code_runner("docs", code)

        if exceptions:
            title = "Code Docs - Unable to retrieve"
            color = 0xEA4335

        output = "\n".join(message)
        await ctx.send(
            embed=nextcord.Embed(
                title=title, description=f"```{output}\n```", color=color
            ),
            reference=ctx.message,
            mention_author=True,
        )

    def _split_run_time(self, content: str):
        parts = re.match(r"^(.+?)?\n\^{4}(\d+)\^{4}$", content, re.DOTALL)
        if parts:
            parts = parts.groups()
            if len(parts) == 2 and parts[-1].isdigit():
                return parts[0] if parts[0] else "", int(parts[1]) / 1000000
        return content, 0


def setup(client):
    client.add_cog(CodeRunner(client))
