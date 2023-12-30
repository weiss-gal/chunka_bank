# chunka_bank
a family pseudo banking application

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
- add transactions query (under work)
  - handle 4000 chars limit
  - format output propertly
- add the following requests
  - withdraw
- add deposit
- add withdraw
- add import (include initial balance)
- add error handling
- add timeout to dialogs
- replace web server for cb_server to waitress

post MVP
- auth authentication to cb_server module
- add language support

