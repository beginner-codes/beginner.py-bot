import beginner.bootstrap


logger = beginner.bootstrap.setup_logger()
client = beginner.bootstrap.create_bot(logger)
beginner.bootstrap.load_cogs(client, logger)
beginner.bootstrap.connect_db(logger)
beginner.bootstrap.run(client, logger)
