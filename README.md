# chunka_bank
a famility pseudo banking application

## How to run
- Start the server using the following command:
python -m cb_server <database path>

- Set the following environment variables
  - BOT_TOKEN - the token to connect to the bot (get it from the developer portal)
  - CB_SERVER_URL - get it from the previous command 
  - MAPPER_PATH - a csv map of discord user id to CB user ids 

- Start the bot with the following command (from repo root)
python -m cb_bot.cb_bot

## Under work
- Add user in repo and server

## TODO
- auth authentication to cb_server module
- add up and down messages (handle ctrl-c if needed)
- add error handling
- add timeout to dialogs
- add warning to public channels

