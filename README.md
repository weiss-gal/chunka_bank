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

## TODO
pre Trial

pre MVP
- handle allowance

post MVP
- add SU (set user) command for admins
- add gracefull shutdown from command 
  - new command set (admin ?)
  - warning in case of pending transfers
- add timed request for users 
- consider using the new bot ui feature (https://discordpy.readthedocs.io/en/stable/interactions/api.html#view)
- execute commands one by one (request each part separately)
- add transfer request - request 
- auth authentication to cb_server module
- add language support
- add more friendly answers
- add admin commands
- gracefull shutdown (check logs, close existing dialogs propertly)

- add export to excel to "show transactions"


