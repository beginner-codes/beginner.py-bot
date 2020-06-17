from beginner.cog import Cog
import discord
import ast
import os
import math


class Fun(Cog):
    @Cog.command()
    async def stack(self, ctx, v: str = "",  *, instructions):
        class InvalidInstruction(Exception):
            ...

        stack = [0]
        operations = instructions.split()
        try:
            output = []
            for operation in operations:
                if operation.isdigit():
                    output.append(f"Push {operation}")
                    stack.append(int(operation))
                elif operation == "+":
                    a, b = stack.pop(), stack.pop()
                    stack.append(a + b)
                    output.append(f"Pop {a}, Pop {b}, Add, Push {stack[-1]}")
                elif operation == "-":
                    a, b = stack.pop(), stack.pop()
                    stack.append(a - b)
                    output.append(f"Pop {a}, Pop {b}, Subtract, Push {stack[-1]}")
                elif operation == "*":
                    a, b = stack.pop(), stack.pop()
                    stack.append(a * b)
                    output.append(f"Pop {a}, Pop {b}, Multiply, Push {stack[-1]}")
                elif operation == "/":
                    a, b = stack.pop(), stack.pop()
                    stack.append(a // b)
                    output.append(f"Pop {a}, Pop {b}, Divide, Push {stack[-1]}")
                elif operation == "DUP":
                    stack.append(stack[-1])
                    output.append(f"Pop {stack[-1]}, Push {stack[-1]}, Push {stack[-1]}")
                elif operation == "POP":
                    output.append(f"Pop {stack.pop()}")
                else:
                    raise InvalidInstruction(operation)
            message = f"Final value: {stack.pop()}"
            if v == "-v":
                o = "\n".join(output)
                message = f"```\n{o}\n```{message}"
        except InvalidInstruction as e:
            message = f"Invalid Instruction: {e.args[0]}"
        except IndexError:
            message = f"IndexError: current stack = {stack}"
        except ZeroDivisionError:
            message = f"Division by zero: current stack = {stack}"

        await ctx.send(message)

    @Cog.command()
    async def remove_extras(self, ctx, count: int, *, raw_literals):
        try:
            literals = ast.literal_eval(raw_literals)
        except (SyntaxError, ValueError):
            await ctx.send("You must provide a sequence of literals")
            return

        result = [item for index, item in enumerate(literals) if literals[:index].count(item) < count]
        await ctx.send(f"Result: {result}")

    @Cog.command()
    async def directionally_challenged(self, ctx, *, raw_directions: str):
        try:
            directions = ast.literal_eval(raw_directions)
        except (SyntaxError, ValueError):
            await ctx.send("You must provide a sequence of strings")
            return

        walked = len(directions)
        shortest = abs(directions.count("N") - directions.count("S")) + abs(directions.count("E") - directions.count("W"))
        await ctx.send(
            f"Your path had a length of `{walked}`\n"
            f"The shortest path had a length of `{shortest}`\n"
            f"The answer was that they have a difference of `{walked - shortest}`"
        )

    @Cog.command()
    async def mystery_function(self, ctx, *, number: str):
        if not number.isdigit():
            await ctx.send("You must provide a positive integer")
            return

        result = math.prod(map(int, str(number)))
        await ctx.send(f"```py\n>>> mystery_function({number})\n{result}```")

    @Cog.command()
    async def dgo(self, ctx):
        await ctx.send(
            embed=discord.Embed().set_image(
                url="https://media1.tenor.com/images/f688c77103e32fdd6a9599713b546435/tenor.gif?itemid=7666830"
            )
        )


def setup(client):
    client.add_cog(Fun(client))
