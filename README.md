# chunka_bank
a famility pseudo banking application

## How to run
- Start the server using the following command:
python -m cb_server.cb_server <database path>
- add the mapper file with the following columns
  - discord_user_id
  - cb_user_id
- Set the following environment variables
  - BOT_TOKEN - the token to connect to the bot (get it from the developer portal)
  - CB_SERVER_URL - get it from the previous command 
  - MAPPER_PATH - a csv map of discord user id to CB user ids 


- Start the bot with the following command (from repo root)
python -m cb_bot.cb_bot

## Under work
- Add user in repo and server

## TODO
pre MVP
- add notification
- add transactions query
- add the following requests
  - withdraw
  - trasnfer 
- add deposit
- add withdraw
- add import (include initial balance)
- add error handling
- add timeout to dialogs
- support only DMs
- replace web server for cb_server to waitress

post MVP
- auth authentication to cb_server module
- add transaction id
