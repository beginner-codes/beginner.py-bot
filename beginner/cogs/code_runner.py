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
    def __init__(self, client):
        super().__init__(client)
        self.blacklist = {"exec", "eval", "exit", "compile", "breakpoint", "credits", "help", "input", "license", "memoryview", "open", "quit", "globals"}

    def evaluate(self, input_code):
        exception = None
        prints = []
        result = None
        internal_globals = {}
        internal_locals = {}

        def printer(*args, **kwargs):
            kwargs["file"] = StringIO()
            kwargs["flush"] = True
            print(*args, **kwargs)
            prints.append(kwargs["file"].getvalue())
            kwargs["file"].close()

        def ranger(*args, **kwargs):
            r = range(*args, **kwargs)
            if (r.stop - r.start) // r.step > 50:
                raise ValueError("Ranges are limited to 50 steps")
            return r

        def attergetter(obj, name, *args, **kwargs):
            if name.startswith("__") and name.endswith("__"):
                raise NameError("Dunder names cannot be accessed")
            return getattr(obj, name, *args, **kwargs)

        scan_builtins = __builtins__ if isinstance(__builtins__, dict) else dict(__builtins__)
        builtins = {
            name: scan_builtins[name]
            for name in scan_builtins
            if not name.startswith("_") and name not in self.blacklist
        }
        builtins.update({
            "print": printer,
            "range": ranger,
            "getattr": attergetter
        })
        internal_globals["__builtins__"] = builtins
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(50)
        try:
            lines = input_code.split("\n")
            statement = []
            for line in lines:
                if (assignment := re.match(r"([_a-zA-Z][_a-zA-Z0-9]*)\s*=\s*([^=].*)", line)):
                    name, value = assignment.groups()
                    print("FOUND local", name, repr(value.strip()))
                    internal_globals[name] = ast.literal_eval(value.strip())
                else:
                    statement.append(line)

            code = compile("\n".join(statement), "<string>", "eval")
            for name in code.co_names:
                if name.startswith("__") and name.endswith("__"):
                    raise NameError("Dunder names cannot be accessed")
            print(statement, internal_globals, internal_locals)
            result = eval(code, internal_globals, internal_locals)
        except Exception as e:
            exception = e
        sys.setrecursionlimit(old_limit)

        return result, prints, exception

    @Cog.command()
    async def exec(self, ctx, *, content=""):
        if not self.settings.get("EXEC_ENABLED", False):
            await ctx.send("The exec command has been disabled.")
            return

        if not len(content.strip()) or content.find("```py") < 0 or content.rfind("```") <= 0:
            await ctx.send(
                embed=discord.Embed(
                    description=(
                        "\n**NO PYTHON CODE BLOCK FOUND**\n\nThe command format is as follows:\n\n"
                        "\n!exec \\`\\`\\`py\nYOUR CODE HERE\n\\`\\`\\`\n"
                    ),
                    color=0xEA4335
                ).set_author(
                    name="Exec - No Code", icon_url=self.server.icon_url
                )
            )

        else:
            title = "Exec - Success"
            color = 0x4285F4

            start = content.find("```python")
            if start >= 0:
                start += 9
            else:
                start = content.find("```py") + 5
            code = content[start: -3]

            code_message = f"{ctx.author.mention} here's the output from [your code]({ctx.message.jump_url})"
            code_message += f"\n```py\n{code}\n```"

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
                embed=discord.Embed(description=code_message, color=color).set_author(
                    name=title, icon_url=self.server.icon_url
                ).add_field(name="Output", value=output, inline=False)
            )

    async def code_runner(self, mode: str, code: str) -> Tuple[List[str], bool]:
        message = []

        proc = await asyncio.create_subprocess_shell(
            f"python -m beginner.runner {mode}", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate(base64.b64encode(code.encode()))
        if stdout:
            out, *exceptions = map(lambda line: base64.b64decode(line).decode(), stdout.split(b"\n"))
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
                        message.append(f"{'...' if len(exception) > 500 else ''}{exception[-500:]}")

        return message, len(exceptions) > 0

    @Cog.command()
    async def eval(self, ctx, *, content):
        if not self.settings.get("EVAL_ENABLED", False):
            await ctx.send("The eval command has been disabled.")
            return

        if content.casefold().strip() == "help":
            await ctx.send(
                embed=discord.Embed(
                    description=(
                        "This command allows you to run a single statement and see the results. For security "
                        "reasons what code you can run is very limited."
                    ),
                    color=0xFBBC05
                ).set_author(
                    name=f"Statement Eval - Help", icon_url=self.server.icon_url
                )
            )
            return

        code = re.sub(r"^\s*(```(python|py)|`?)\s*|\s*(```|`)\s*$", "", content)
        title = "Eval - Success"
        color = 0x4285F4

        code_message = f"{ctx.author.mention} here's the output from [your code]({ctx.message.jump_url})"
        code_message += f"\n```py\n>>> {code}"

        message, exceptions = await self.code_runner("eval", code)

        if exceptions:
            title = "Eval - Exception Raised"
            color = 0xEA4335

        output = "\n".join(message)
        await ctx.send(
            embed=discord.Embed(description=f"{code_message.strip()}\n\n{output}\n```", color=color).set_author(
                name=title, icon_url=self.server.icon_url
            )
        )


def setup(client):
    client.add_cog(CodeRunner(client))
