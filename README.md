# Beginner.py Discord Bot
[![Join Us On Discord!!!](https://discord.com/api/guilds/644299523686006834/embed.png)](https://discord.gg/sfHykntuGy)

This is the discord bot for the beginner.py discord server. A bit of a hodge podge of coding style and experience levels as it is a collaboration between various people, all of whom had no experience with Discord.py before this.

## Wanna Join Us?
If you'd like to join us, we're a welcoming community with over 1,000 members. [We will happily have you!!!](https://discord.gg/RGPs5TmqD5)

## Requirements
The bot uses [Poetry](https://python-poetry.org/) for packaging and dependency management. You will need to follow the [installation instructions](https://python-poetry.org/docs/#installation) before you can get started with the bot.

Additionally you will need a bot token from Discord. You can read about how to get yours [here](https://realpython.com/how-to-make-a-discord-bot-python/#creating-an-application).

## Configuration & Setup
First things first, we need to install all of the dependencies. To do that run:
```sh
poetry install
```
Next you need to configure the bot with the local dev settings. To do this copy the `development.example.yaml` file and name the new copy `development.yaml`. 

Once that’s done open it up and in the `bot` section change the `token` string to your dev bot token.
## Running
To run the bot you’ll need to be in the directory which you cloned the repo, and run the following command:
```sh
poetry run python -m beginner
```
This will create a virtual environment with all the required dependencies and run the beginner.py bot package.

Of course this will not have any real cogs enabled. By default the `development.yaml` only has the `devcog` enabled which allows you to load, unload, and reload cogs using discord commands. To enable a cog open `development.yaml` and in the `cogs` section find the cog you want and change its value from `false` to `true`. If it has an `enabled` field you’d update that field’s value to `true` instead. This allows you to work with just the cogs you are making changes to and not have to have them all running all the time.

## Building
The bot uses Docker containers for deployment. We also use GitHub Actions for our Continuous Delivery pipeline, however because it doesn’t support docker image layer caching we’ve split the dockerfile into two parts. `base.Dockerfile` installs Poetry and all the necessary dependencies on top of a `slim-buster` Python image. `Dockerfile` then copies in all the code and configuration files needed and runs the bot using the image created using `base.Dockerfile` as a base.

Now because this requires publishing the image for `base.Dockerfile` we’ve also included `dev.Dockerfile` which is the other two dockerfiles in one. This image is the one that can be built locally like this:
```sh
docker build -f dev.Dockerfile .
```

## Database
We use PostgreSQL for the bot. If you’d like to run one locally we’ve included a Docker Compose file that will spin up a local server: `compose/postgres.yaml`. It’ll have the following config settings:
```
User: postgresadmin
Pass: dev-env-password-safe-to-be-public
DB:   bpydb
Port: 5432
Host: 0.0.0.0
```
You’ll need to update `development.yaml` with your database configuration by changing the values in the `database` section.

## The Hard Stuff
Currently working on the Google cog requires a Google Custom Search Key and a Google Custom Search Engine token. This is kinda complicated to get setup. As such no one will be expected to work on that cog. However if you’re feeling adventurous you’ll just need to add and fillout the following in your `develompent.yaml`:
```yaml
google:
  custom_search_key: "YOUR KEY HERE"
  custom_search_engine: "YOUR SEARCH ENGINE HERE"
```
