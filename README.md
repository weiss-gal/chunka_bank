# chunka_bank
a family pseudo banking application. 

It has started as a simple project and by now have a few thousands lines of code and over 80 commits (And I didn't even officially deploy it yet). 

My idea was to manage my kids weekly allowance in an easier way than an excel file. Nevertheless, I didn't want to write an application or worry about a web server. 
so I thought that just using a chatbot would be great. we are now testing it, it looks quite good, although I should probabaly ditch the complicated text commands in favor of using the discord "view"s (which I just recently learned about their existence). 

If you are trying to use it and fail for lack of instructions, just drop me a line or open an issue in Github. I'll do my best to help if I have the time. 

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

post MVP
- jobs lock fails on abnormal temrination
  - its probably enough if we pick it just when updating
- add goals
- no cleanup of users from UserInfoProvider
  - remove undetected users 
- add version command (and version)
- handle allowance
  - (optional for pre MVP) add command for jobs
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


