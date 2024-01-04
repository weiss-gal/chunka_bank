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
pre Trial
- add withdraw - request (under work)
  - add a way to cancel 
- add timeout to dialogs
- change time in transactions table to be user-friendly (there should
  already be a function for that)

pre MVP
- handle allowance
- replace web server for cb_server to waitress

post MVP
- consider using the new bot ui feature (https://discordpy.readthedocs.io/en/stable/interactions/api.html#view)
- execute commands one by one (request each part separately)
- add transfer request - request 
- auth authentication to cb_server module
- add language support
- add more friendly answers


