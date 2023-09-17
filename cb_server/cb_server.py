import flask
import sys
from cb_repo import Repo, UserNotFound

if len(sys.argv) != 2:
    print('Usage: cb_server.py <db_path>')
    sys.exit(1)

db_path = sys.argv[1]

repo = Repo(db_path)

app = flask.Flask(__name__)

@app.route('/user/<username>/balance', methods=['GET'])
def get_user_balance(username):
    try:
        balance = repo.get_user_balance(username)
        return flask.jsonify({'balance': balance})
    except UserNotFound:
        return flask.jsonify({'error': f'User {username} not found'}), 404
    
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)

