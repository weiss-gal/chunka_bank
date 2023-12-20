import argparse
import os
import flask
from cb_repo import Repo, UserNotFound

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starts the Chunka bank database server")
    parser.add_argument('db_path', help='Database file path ')
    parser.add_argument('-c', '--create', action='store_true', help='Create a new database')
    return parser.parse_args()

args = parse_args()
print ("args:", args)

create = False
if args.create:
    if os.path.isfile(args.db_path):
        print(f"Database file already exists at '{args.db_path}'")
        exit(-1)
    
    create = True
else:
    if not os.path.isfile(args.db_path):
        print(f"No database file found at {args.db_path}, to create new one re-run the server with the '--create' flag")
        exit(-1)

repo = Repo(args.db_path, create)

app = flask.Flask(__name__)

@app.route('/user/<username>/balance', methods=['GET'])
def get_user_balance(username):
    try:
        balance = repo.get_user_balance(username)
        return flask.jsonify({'balance': balance})
    except UserNotFound:
        return flask.jsonify({'error': f'User {username} not found'}), 404
    
@app.route('/user/<username>', methods=['POST'])
def add_user(username):
    repo.add_user(username, 0)
    # upon success return 204
    return '', 204
    
@app.route('/user/<username>/transfer', methods=['POST'])
def transfer_money(username):
    # get the request body
    req_body = flask.request.json
    
    to = req_body['to']
    value = float(req_body['value'])
    # get the 'description' field
    description = req_body['description']
    # transfer the money
    repo.transfer_money(username, to, value, description)
    # upon success return 204
    return '', 204

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)

