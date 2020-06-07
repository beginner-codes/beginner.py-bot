from beginner.beginner import BeginnerCog
from beginner.logging import create_logger


logger = create_logger()
BeginnerCog.setup_logging()

logger.debug("Hello")
client = BeginnerCog.get_client()
logger.debug("Created client")
BeginnerCog.load_cogs(client)
logger.debug("Created cogs")
client.run(BeginnerCog.get_token())
logger.debug("Good bye")
