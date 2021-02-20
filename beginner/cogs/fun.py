from beginner.cog import Cog
import discord
import discord.ext.commands
import ast
import os
import math
import re
import socket


class Fun(Cog):
    @Cog.command()
    async def stack(self, ctx, v: str = "", *, instructions):
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
                    output.append(
                        f"Pop {stack[-1]}, Push {stack[-1]}, Push {stack[-1]}"
                    )
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

        result = [
            item
            for index, item in enumerate(literals)
            if literals[:index].count(item) < count
        ]
        await ctx.send(f"Result: {result}")

    @Cog.command()
    async def directionally_challenged(self, ctx, *, raw_directions: str):
        try:
            directions = ast.literal_eval(raw_directions)
        except (SyntaxError, ValueError):
            await ctx.send("You must provide a sequence of strings")
            return

        walked = len(directions)
        shortest = abs(directions.count("N") - directions.count("S")) + abs(
            directions.count("E") - directions.count("W")
        )
        await ctx.send(
            f"Your path had a length of `{walked}`\n"
            f"The shortest path had a length of `{shortest}`\n"
            f"The answer was that they have a difference of `{walked - shortest}`"
        )

    @Cog.command(
        aliases=[
            "mystery_func",
            "mystery_fun",
            "mysteryfunction",
            "mysteryfunc",
            "mysteryfun",
        ]
    )
    async def mystery_function(self, ctx, *, number: str):
        if not number.isdigit():
            await ctx.send("You must provide a positive integer")
            return

        result = math.prod(map(int, str(number)))
        await ctx.send(f"```py\n>>> mystery_function({number})\n{result}```")

    @Cog.command(aliases=["minipeaks", "peaks"])
    async def mini_peaks(self, ctx, *, raw_numbers: str):
        try:
            numbers = ast.literal_eval(raw_numbers)
        except (SyntaxError, ValueError):
            numbers = None

        if not hasattr(numbers, "__iter__") or any(
            not isinstance(item, (int, float)) for item in numbers
        ):
            await ctx.send("You must provide a sequence of integers")
            return

        result = [
            y
            for x, y, z in zip(numbers[:-2], numbers[1:-1], numbers[2:])
            if y > x and y > z
        ]
        await ctx.send(f"```py\n>>> mini_peaks({raw_numbers})\n{result}```")

    @Cog.command(aliases=["compass", "directions", "compassdirections"])
    async def compass_directions(self, ctx, raw_facing: str, *, raw_directions: str):
        try:
            facing = ast.literal_eval(raw_facing)
            assert isinstance(facing, str)
            directions = ast.literal_eval(raw_directions)
            assert hasattr(directions, "__iter__") and list(
                filter(lambda item: isinstance(item, str), directions)
            )
        except (AssertionError, SyntaxError, ValueError):
            await ctx.send(
                "Facing must be a string, directions must be a sequence of strings"
            )
            return

        cardinals = {"N": 0, "E": 1, "S": 2, "W": 3}
        direction = cardinals[facing]
        direction -= directions.count("L")
        direction += directions.count("R")
        result = {item: key for key, item in cardinals.items()}[direction % 4]
        await ctx.send(
            f"```py\n>>> final_direction({raw_facing}, {raw_directions})\n{result}```"
        )

    @Cog.command(aliases=["intersection", "union", "intersectionunion"])
    async def intersection_union(self, ctx, *, code: str):
        def intersection_union(list_a, list_b):
            intersection = list({item for item in list_a if item in list_b})
            intersection.sort()
            union = list(set(list_a) | set(list_b))
            union.sort()
            return intersection, union

        try:
            lists = re.findall(r"(\[[0-9,\s]+\])", code)
            print(lists)
            list_a = ast.literal_eval(lists[0])
            list_b = ast.literal_eval(lists[1])
        except (SyntaxError, ValueError) as e:
            await ctx.send(f"There was an exception: {e.__name__}")
        else:
            result = intersection_union(list_a, list_b)
            await ctx.send(
                f"```py\n>>> intersection_union({str(list_a)}, {str(list_b)})\n{result}```"
            )

    @Cog.command(aliases=["countoverlapping", "overlapping"])
    async def count_overlapping(self, ctx, *, code: str):
        def count_overlapping(intervals, point):
            return len([a for a, b in intervals if a <= point <= b])

        try:
            data = re.findall(r"(\[[0-9,\s\[\]]+\]|\d+)", code)
            intervals = ast.literal_eval(data[0])
            point = ast.literal_eval(data[1])
        except (SyntaxError, ValueError) as e:
            await ctx.send(f"There was an exception: {e.__name__}")
        else:
            result = count_overlapping(intervals, point)
            await ctx.send(
                f"```py\n>>> count_overlapping({intervals}, {point})\n{result}```"
            )

    @Cog.command(aliases=["rearranged"])
    async def rearranged_difference(self, ctx, number: int):
        result = int("".join(reversed(sorted(str(number))))) - int(
            "".join(sorted(str(number)))
        )
        await ctx.send(f"```py\n>>> rearranged_difference({number})\n{result}```")

    @Cog.command(
        aliases=[
            "left",
            "leftdigit",
            "leftmost",
            "left_most",
            "leftmost_digit",
            "left_most_digit",
            "leftmostdigit",
        ]
    )
    async def left_digit(self, ctx, input_string: str):
        def left_digit(string: str):
            for c in string:
                if c.isdigit():
                    return int(c)
            return None

        result = left_digit(input_string)
        await ctx.send(f'```py\n>>> left_digit("{input_string}")\n{result}```')

    @Cog.command(aliases=["correctinequality", "inequality"])
    async def correct_inequality(self, ctx, *, expression: str):
        def correct_inequality(expression: str):
            tokens = expression.split(" ")
            steps = []

            if len(tokens) < 3 or (len(tokens) - 3) % 2 != 0:
                steps.append("INVALID INPUT")
                return steps

            valid = True
            for index in range(0, len(tokens) - 2, 2):
                a, op, b = tokens[index : index + 3]
                steps.append(f"{a} {op} {b}")
                if op not in {">", "<"} or not a.isdigit() or not b.isdigit():
                    steps[-1] += " - INVALID"
                    valid = False
                    break
                elif op == "<" and int(a) >= int(b):
                    steps[-1] += " - False"
                    valid = False
                    break
                elif op == ">" and int(a) <= int(b):
                    steps[-1] += " - False"
                    valid = False
                    break
                else:
                    steps[-1] += " - True"

            steps.append("VALID EXPRESSION" if valid else "INVALID EXPRESSION")
            return steps

        result = "\n".join(correct_inequality(expression))
        await ctx.send(f"`{expression}`\n```py\n{result}\n```")

    @Cog.command()
    async def dgo(self, ctx):
        await ctx.send(
            embed=discord.Embed().set_image(
                url="https://media1.tenor.com/images/f688c77103e32fdd6a9599713b546435/tenor.gif?itemid=7666830"
            )
        )

    @Cog.command()
    async def dns(self, ctx, domain_name: str):
        try:
            ip = socket.gethostbyname(domain_name)
        except socket.gaierror:
            message = f"Could not find the domain {domain_name}"
        else:
            message = f"The IP address for {domain_name} is {ip}"
        await ctx.send(message)

    @Cog.command()
    async def raw(self, ctx: discord.ext.commands.Context):
        message: discord.Message = ctx.message
        await ctx.send(
            f"```\n{message.content}\n```",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=False, roles=False
            ),
        )

    @Cog.command(aliases=["ducci"])
    async def ducci_sequence(self, ctx, *, content):
        try:
            sequence = ast.literal_eval(content)
        except Exception:
            await ctx.send("There was an error")
            return

        h = [sequence]
        exited = False
        while h.count(h[-1]) == 1 and not all(i == 0 for i in h[-1]):
            h.append(tuple(abs(a - b) for a, b in zip(h[-1], [*h[-1][1:], h[-1][0]])))

            if len(h) == 100:
                exited = True
                break

        sequences = "\n".join(
            f"{str(index) + '.':4} {sequence!r}"
            for index, sequence in enumerate(h, start=1)
        )
        message = f"```py\n{sequences}\n```\n{'Finished in' if not exited else 'Exited after'} {len(h)} steps"
        await ctx.send(message)


def setup(client):
    client.add_cog(Fun(client))
