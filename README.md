# beginner.py-bot
Discord bot for the beginner.py server. A bit of a hodge podge of coding style and experience levels as it is a collaboration between various people, all of whom had no experience with Discord.py before this.

## Setup & Running
To run the bot you need to first define the authentication token. Then you the bot can be run either directly with the local python interpreter or using the included Dockerfile.

### Authentication Token
The authentication token can be stored either as an environment variable or as a file at the root of the bot file structure.

Environment variable in a bash shell

    EXPORT DISCORD_TOKEN="token value"

Environment variable in a Windows shell

    setx DISCORD_TOKEN "token value"

Or the token value can be placed into a file named `bot.token` in the same directory as the `beginner.py` file.

### Running
First install the requirements

    pip install -r requirements.txt

Then you can run as normal

    python -m beginner

#### Docker Compose
Alternatively if you have docker installed you can have it handle all of that for you by running it with the this command:

    docker-compose -f bot-compose.yaml up

To stop the bot press `CTRL-C`.

It will be necessary to create a file at the root of the project named `bot.config`, inside the file you will need to provide the bot token like this:

    DISCORD_TOKEN=TOKEN GOES HERE
    
To simplify this process you can make a copy of the `example_bot.config` and fill in the token. Docker compose will load the contents of this file into the bot's container environment.
