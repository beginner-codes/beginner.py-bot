from beginner.cog import Cog
from io import StringIO
import discord
import sys
import ast
import re
import asyncio
import base64


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

        color = 0x4285F4
        title = "Exec - Success"
        code_message = f"{ctx.author.mention} here's the output from [your code]({ctx.message.jump_url})"
        message = []
        if not len(content.strip()) or content.find("```py") < 0 or content.rfind("```") <= 0:
            message.append(
                "\n**NO PYTHON CODE BLOCK FOUND**\n\nThe command format is as follows:\n\n"
                "\n!exec \\`\\`\\`py\nYOUR CODE HERE\n\\`\\`\\`\n"
            )
            title = "Exec - No Code"

        else:
            start = content.find("```python")
            if start >= 0:
                start += 9
            else:
                start = content.find("```py") + 5
            code = content[start: -3]

            code_message += f"\n```py\n{code}\n```"

            proc = await asyncio.create_subprocess_shell(
                "python -m beginner.runner", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(base64.b64encode(code.encode())), 2)
                if stdout:
                    out, *exceptions = map(lambda line: base64.b64decode(line).decode(), stdout.split(b"\n"))
                    if out:
                        out = out.strip()
                    else:
                        out = ""
                else:
                    out = ""
                    exceptions = [stderr]

            except asyncio.exceptions.TimeoutError:
                proc.kill()
                out, exceptions = "", ("TimeoutError: Your script took too long and was killed",)

            if not out and (not exceptions[0] or not exceptions[0].strip()):
                message.append("\n*No output or exceptions*")
            else:
                message.append(f"```\n")
                if out:
                    message.append(f"{out[:1000]}{'...' if len(out) > 1000 else ''}")

                if exceptions[0].strip():
                    color = 0xEA4335
                    title = "Exec - Exception Raised"
                    if out:
                        message.append("")

                    for exception in exceptions:
                        if exception:
                            message.append(f"{'...' if len(exception) > 500 else ''}{exception[-500:]}")
                message.append("```")

        await ctx.send(
            embed=discord.Embed(description=code_message, color=color).set_author(
                name=title, icon_url=self.server.icon_url
            ).add_field(name="Output", value="\n".join(message), inline=False)
        )

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
                        "reasons what code you can run is very limited. Use `!eval limits` for more details."
                    ),
                    color=0xFBBC05
                ).set_author(
                    name=f"Statement Eval - Help", icon_url=self.server.icon_url
                )
            )
            return

        if content.casefold().strip() == "limits":
            await ctx.send(
                embed=discord.Embed(
                    description=(
                        "For security purposes the following limits are placed on the eval command.\n"
                        "- Function stack is limited to 50\n"
                        "- `range` is limited to 50 steps\n"
                        "- Dunder functions, properties, methods, and variables are not accessible\n"
                        "- Protected builtins (name starts with `_` or `__`) are blacklisted\n"
                        "- The following are blacklisted:\n```"
                        + "".join(f"{name:12}" for name in sorted(self.blacklist))
                        + "```"
                    ),
                    color=0xFBBC05
                ).set_author(
                    name=f"Statement Eval - Limits", icon_url=self.server.icon_url
                )
            )
            return

        code = re.sub(r"^\s*(```(python|py)?)\s*|\s*(```|`)\s*$", "", content)
        result, prints, exception = self.evaluate(code)
        formatted_code = ">>> " + code.replace("\n", "\n>>> ")
        output = ''.join(prints)
        color = 0x4285F4
        if exception:
            color = 0xEA4335
            if output:
                output += "\n"
            output += f"\n{exception.__class__.__name__}: {str(exception)}"
        elif not prints or result:
            output += "" if not output or output[-1] == "\n" else "\n"
            output += repr(result)
        await ctx.send(
            embed=discord.Embed(
                description=f"```py\n{formatted_code}\n\n{output}```",
                color=color
            ).set_author(
                name=f"Statement Eval", icon_url=self.server.icon_url
            )
        )


def setup(client):
    client.add_cog(CodeRunner(client))
