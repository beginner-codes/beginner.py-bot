# beginner.py-bot
Discord bot for the beginner.py server.

## Running
To run the bot you need to first define the authentication token. Then you the bot can be run either directly with the local python interpreter or using the included Dockerfile.

### Authentication Token
The authentication token can be stored either as an environment variable or as a file at the root of the bot file structure.

Environment variable in a bash shell

    EXPORT DISCORD_BOT="token value"

Environment variable in a Windows shell

    setx DISCORD_BOT "token value"

Or the token value can be placed into a file named `bot.token` in the same directory as the `beginner.py` file.

### Running
First install the requirements

    pip install -r requirements.txt

Then you can run as normal

    python beginner.py

Alternatively if you have docker installed you can run

    docker build -t beginner-py-bot:latest .
    docker run -it -e DISCORD_BOT="token value" beginner-py-bot:latest
