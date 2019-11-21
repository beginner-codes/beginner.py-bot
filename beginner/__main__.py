from beginner.beginner import BeginnerCog


client = BeginnerCog.get_client()
BeginnerCog.load_cogs(client)
client.run(BeginnerCog.get_token())
