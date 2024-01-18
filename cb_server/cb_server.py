import argparse
from datetime import datetime, timezone
from json import JSONEncoder
import os
from typing import List
import flask
from cb_server.cb_repo import Repo, UserNotFound
from models.server_errors import ErrorCodes, ServerError
from models.transactions import UserTransactionInfo

def get_timestamp_from_req(req , key: str) -> int:
    print("the type of req is ", type(req)) # XXX - debug
    iso_time = req.args.get(key)
    if iso_time is None:
        return None
    
    try:
        return int(datetime.fromisoformat(iso_time).timestamp())
    except ValueError:
        flask.abort(400, f'Invalid {key} value: {iso_time}')

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starts the Chunka bank database server")
    parser.add_argument('db_path', nargs="?", default=os.environ.get('CB_DB_PATH', None), help='Database file path')
    parser.add_argument('-c', '--create', action='store_true', help='Create a new database')
    return parser.parse_args()

def build_error_response(error: ServerError) -> flask.Response:
    # a workaround to convert the enum to string
    error_dict = {**error._asdict(), "error_code":error.error_code.name}
    response = flask.jsonify(error_dict)
    response.status_code = 400
    return response

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
    if to == username:
        return build_error_response(ServerError(ErrorCodes.USER_ERROR, 'You cannot transfer money to yourself'))
    try:
        value = float(req_body['value'])
    except ValueError:
        value = None
    if value is None or value <= 0:
        return build_error_response(ServerError(ErrorCodes.USER_ERROR, f'Invalid amount: \'{req_body["value"]}\''))
    
    # get the 'description' field
    description = req_body['description']
    # transfer the money
    sucess, msg = repo.transfer_money(username, to, value, description)
    if not sucess:
        error = ServerError(ErrorCodes.USER_ERROR, msg)
        return build_error_response(error)
        
    # upon success return 204
    return '', 204

@app.route('/user/<username>/transactions', methods=['GET'])
def get_user_transactions(username):
    # get the request query parameters
    from_timestamp = get_timestamp_from_req(flask.request, 'from_time')
    to_timestamp = get_timestamp_from_req(flask.request, 'to_time')
    try:
        last_n = int(flask.request.args.get('last_n')) if flask.request.args.get('last_n') is not None else None
    except ValueError:
        flask.abort(400, f'Invalid last_n value: {last_n}')
    
    # get the transactions
    transactions = repo.get_user_transactions(username, last_n, from_timestamp, to_timestamp)

    transactions_list: List[UserTransactionInfo] = []
    for t in transactions:
        transactions_list.append(UserTransactionInfo(
            userid=username,
            amount=t[1],
            timestamp=datetime.fromtimestamp(t[0], timezone.utc).isoformat(),
            description=t[2],
            id=t[3]
        ))
        
    # return the transactions
    return flask.jsonify([t._asdict() for t in transactions_list])

if __name__ == '__main__':
    from waitress import serve
    from urllib.parse import urlparse
    cb_server_url = os.environ.get('CB_SERVER_URL', 'http://127.0.0.1:5000')
    
    parsed = urlparse(cb_server_url)
    if parsed.scheme != 'http':
        raise Exception("only HTTP is supported")
    if parsed.hostname not in ['localhost', '127.0.0.1']:
        raise Exception("cb server must run on localhost, since its not protected")

    serve(app, listen=parsed.netloc)
    

