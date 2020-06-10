from beginner.cog import Cog
from beginner.models.points import Points
from beginner.scheduler import schedule, task_scheduled
from beginner.tags import tag
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import discord
import os
import peewee
import re


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

        await ctx.send(message)


def setup(client):
    client.add_cog(Fun(client))
