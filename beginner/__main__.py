from beginner.beginner import BeginnerCog


print("Hello")
client = BeginnerCog.get_client()
print("We've got a client")
BeginnerCog.load_cogs(client)
print("Cogs loaded")
client.run(BeginnerCog.get_token())
print("Good bye")
