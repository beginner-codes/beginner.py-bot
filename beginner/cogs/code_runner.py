from beginner.cog import Cog
from beginner.colors import *
import discord
import re
import asyncio
import base64
from typing import Tuple
import time
import json


class CodeRunner(Cog):
    @Cog.command()
    async def exec(self, ctx, *, content=""):
        if not self.settings.get("EXEC_ENABLED", False):
            await ctx.send("The exec command has been disabled.")
            return

        if (
            not len(content.strip())
            or content.find("```") < 0
            or content.rfind("```") <= 0
        ):
            await ctx.send(
                embed=discord.Embed(
                    title="Exec - No Code",
                    description=(
                        "\n**NO PYTHON CODE BLOCK FOUND**\n\nThe command format is as follows:\n\n"
                        "\n!exec \\`\\`\\`py\nYOUR CODE HERE\n\\`\\`\\`\n"
                    ),
                    color=RED,
                ),
                reference=ctx.message,
                mention_author=True,
            )
            return

        title = "✅ Exec - Success"
        color = BLUE

        code, user_input = re.match(
            r"^```(?:py|python)?\n((?:.|\n)+?)\n```\n?(.+)?$", content
        ).groups()

        out, err, duration = await self.code_runner("exec", code, user_input)

        output = [out]
        if err:
            title = "❌ Exec - Exception Raised"
            color = YELLOW
            output.append(err)

        elif not out:
            output = ["*No output or exceptions*"]

        out = "\n\n".join(output)
        await ctx.send(
            embed=discord.Embed(
                title=title, description=f"```py\n{out}\n```", color=color
            ).set_footer(text=f"Completed in {duration:0.4f} seconds"),
            reference=ctx.message,
            mention_author=True,
        )

    async def code_runner(
        self, mode: str, code: str, user_input: str = ""
    ) -> Tuple[str, str, float]:
        proc = await asyncio.create_subprocess_shell(
            f"python -m beginner.runner {mode}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        data = json.dumps(
            {
                "code": code,
                "input": user_input,
            }
        ).encode()
        start = time.time_ns()
        stdout, stderr = await proc.communicate(data)
        duration = (time.time_ns() - start) / 1_000_000_000

        return stdout.decode(), stderr.decode(), duration

    @Cog.command()
    async def eval(self, ctx, *, content):
        if not self.settings.get("EVAL_ENABLED", False):
            await ctx.send("The eval command has been disabled.")
            return

        if content.casefold().strip() == "help":
            await ctx.send(
                embed=discord.Embed(
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
            embed=discord.Embed(
                title=title,
                description=f"{code_message.strip()}\n{output}\n```",
                color=color,
            ).set_footer(text=f"Completed in {duration:0.4f} seconds"),
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
            embed=discord.Embed(
                title=title, description=f"```{output}\n```", color=color
            ),
            reference=ctx.message,
            mention_author=True,
        )


def setup(client):
    client.add_cog(CodeRunner(client))
