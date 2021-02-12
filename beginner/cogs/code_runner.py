from beginner.cog import Cog
from io import StringIO
import discord
import sys
import ast
import re
import asyncio
import base64
from typing import List, Tuple


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
                    color=0xEA4335,
                ),
                reference=ctx.message,
                mention_author=True,
            )

        else:
            title = "Exec - Success"
            color = 0x4285F4

            start = content.find("```python")
            if start >= 0:
                start += 9
            else:
                start = content.find("```py") + 5
            code = content[start:-3]

            message, exceptions = await self.code_runner("exec", code)

            if exceptions:
                title = "Exec - Exception Raised"
                color = 0xEA4335

            output = "\n".join(message)
            if not message:
                output = "*No output or exceptions*"
            else:
                output = f"```\n{output}\n```"

            await ctx.send(
                embed=discord.Embed(title=title, description=output, color=color),
                reference=ctx.message,
                mention_author=True,
            )

    async def code_runner(self, mode: str, code: str) -> Tuple[List[str], bool]:
        message = []

        proc = await asyncio.create_subprocess_shell(
            f"python -m beginner.runner {mode}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(base64.b64encode(code.encode())), timeout=5
            )
        except asyncio.exceptions.TimeoutError:
            proc.kill()
            stdout = ""
            stderr = "TimeoutError"

        if stdout:
            out, *exceptions = map(
                lambda line: base64.b64decode(line).decode(), stdout.split(b"\n")
            )
            exceptions = list(filter(bool, exceptions))
            if out:
                out = out.strip()
            else:
                out = ""
        else:
            out = ""
            exceptions = [stderr]

        if out or exceptions:
            if out:
                message.append(f"{out[:1000]}{'...' if len(out) > 1000 else ''}")

            if exceptions:
                if out:
                    message.append("")

                for exception in exceptions:
                    if exception:
                        message.append(
                            f"{'...' if len(exception) > 500 else ''}{exception[-500:]}"
                        )

        return message, len(exceptions) > 0

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
        title = "Eval - Success"
        color = 0x4285F4

        code_message = f"\n```py\n>>> {code}"

        message, exceptions = await self.code_runner("eval", code)

        if exceptions:
            title = "Eval - Exception Raised"
            color = 0xEA4335

        output = "\n".join(message)
        await ctx.send(
            embed=discord.Embed(
                title=title,
                description=f"{code_message.strip()}\n\n{output}\n```",
                color=color,
            ),
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
