from beginner.cog import Cog
import ast


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


def setup(client):
    client.add_cog(Fun(client))
