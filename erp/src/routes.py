from .bank import Bank

from uuid import uuid4
from flask import Blueprint, jsonify, request

erp = Blueprint('erp', __name__)

node_identifier = str(uuid4()).replace('-', '')

bank = Bank()

@erp.route('/')
def home():
    return "<h1>Blockchain ERP System</h1>"

# ----------------------------------
#            Blockchain
# ----------------------------------

@erp.route('/mine', methods=['GET'])
def mine():
    blocks = []
    for type in ['meta', 'finance', 'hr', 'clients']:
        if bank.current_transactions[type]:
            last_block = bank.chains[type][-1]
            print(last_block)
            proof = bank.proof_of_work(last_block)
            previous_hash = bank.hash(last_block)
            block = bank.add_block(type, proof, previous_hash)

    response = {
        'message': "New blocks forged"
    }
    for block in blocks:
        response.update(
            {'block': 
                {
                    'index': block['index'],
                    'transactions': block['transactions'],
                    'proof': block['proof'],  
                    'previous_hash': block['previous_hash']
                }
            })

    return jsonify(response), 200

@erp.route('/chains', methods=['GET'])
def full_chain():
    response = {
            'meta': bank.chains['meta'],
            'finance': bank.chains['finance'],
            'hr': bank.chains['hr'],
            'clients': bank.chains['clients']
    }
    return jsonify(response), 200

@erp.route('/chains/<type>', methods=['GET'])
def chain(type):
    response = {
        'chain': bank.chains[type]
    }
    return jsonify(response), 200

@erp.route('/transactions', methods=['GET'])
def full_transactions():
    response = {
            'meta': bank.current_transactions['meta'],
            'finance': bank.current_transactions['finance'],
            'hr': bank.current_transactions['hr'],
            'clients': bank.current_transactions['clients']
    }
    return jsonify(response), 200

@erp.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    required = ['authorizer', 'nodes']

    if not all(k in values for k in required):
        return "Missing values authorizer or nodes", 400
    
    nodes = values['nodes']
    authorizer = values['authorizer']

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    try:
        for node in list(nodes):
            bank.register_node(authorizer, node)
    except ValueError:
        return "Error: Missing proper authorizer for registration", 400

    response = {
            'message': "New nodes have been added",
            'total_nodes': list(bank.nodes)
    }
    return jsonify(response), 200

# ----------------------------------
#               Meta
# ----------------------------------

@erp.route('/meta/set', methods=["POST"])
def meta_transaction():
    values = request.get_json()
    required = ['interest', 'reserve_ratio']

    if not all(k in values for k in required):
        return "Missing values interest or reserve ratio", 400

    index = bank.set_meta(values['interest'], values['reserve_ratio'])

    response = {
        'message': f'Transactions will be added to Block {index}'
    }
    return jsonify(response), 200

# ----------------------------------
#              Finance
# ----------------------------------

@erp.route('/finance/reserves', methods=["GET"])
def reserves_check():
    response = {
        "reserves": bank.reserves,
        "valid": bank.validate_reserves()
    }
    return jsonify(response), 200

@erp.route('/finance/interbank/borrow', methods=['POST'])
def borrow():
    values = request.get_json()
    required = ['amount']

    if not all(k in values for k in required):
        return "Missing values", 400

    cash, index = bank.borrow(values['amount'])

    response = {
        'message': f'Cash at {cash}, transactions will be added to Block {index}'
    }
    return jsonify(response), 200

@erp.route('/finance/interbank/lend', methods=['POST'])
def lend():
    values = request.get_json()
    required = ['amount']

    if not all(k in values for k in required):
        return "Missing values", 400

    cash, index = bank.lend(values['amount'])

    response = {
        'message': f'Cash at {cash}, transactions will be added to Block {index}'
    }
    return jsonify(response), 200

@erp.route('/finance/interbank/compound', methods=['GET'])
def interbank_interest():
    nv, index = bank.interbank_compound_interest()

    response = {
        'message': f'Net value at {nv}, transactions will be added to Block {index}'
    }
    return jsonify(response), 200

@erp.route('/finance/repo/buy', methods=['POST'])
def buy_repo():
    values = request.get_json()
    required = ['yield']

    if not all(k in values for k in required):
        return "Missing values", 400

    try:
        repo, index = bank.buy_repo(values['yield'], values['par'])
    except KeyError:
        repo, index = bank.buy_repo(values['yield'])
    par = repo['par']
    response = {
        'message': f'Bought at par {par}, transactions will be added to Block {index}'
    }
    return jsonify(response), 200

@erp.route('/finance/repo/sell', methods=['POST'])
def sell_repo():
    values = request.get_json()
    required = ['yield']

    if not all(k in values for k in required):
        return "Missing values", 400

    try:
        repo, index = bank.sell_repo(values['yield'], values['par'])
    except KeyError:
        repo, index = bank.sell_repo(values['yield'])
    par = repo['par']
    response = {
        'message': f'Sold at par {par}, transactions will be added to Block {index}'
    }
    return jsonify(response), 200

# ----------------------------------
#          Human Resources
# ----------------------------------

@erp.route('/hr/employee/add', methods=["POST"])
def add_employee():
    values = request.get_json()
    required = ['salary', 'department', 'supervisor_id']

    if not all(k in values for k in required):
        return "Missing values", 400

    index = bank.add_employee(values['salary'], values['department'], values['supervisor_id'])

    response = {
        'message': f"Employee will be added to Block {index}"
    }

    return jsonify(response), 200

# ----------------------------------
#              Clients
# ----------------------------------

@erp.route('/clients/add', methods=['GET'])
def add_client():
    index = bank.add_client()

    mine()

    response = {
        'message': f"Client added to the system in block {index}",
    }
    return jsonify(response), 200

@erp.route('/clients/open', methods=['POST'])
def open_account():
    values = request.get_json()
    required = ['bank_num', 'principal', 'type']

    if not all(k in values for k in required):
        return "Missing values", 400
    
    try:
        account, index = bank.open_account(values['bank_num'], values['principal'], values['type'])
    except ValueError:
        return "Associated client with bank number not found", 400
    
    response = {
        'message': f"Account created and will be updated in Block {index}",
        'account': account.mapped
    }
    
    return jsonify(response), 200

@erp.route('/clients/close', methods=['POST'])
def close_account():
    values = request.get_json()
    required = ['bank_num', 'account_num']

    if not all(k in values for k in required):
        return "Missing values", 400
    
    try:
        account, index = bank.close_account(values['bank_num'], values['account_num'])
    except ValueError:
        return "Associated client with bank number and account number not found", 400
    
    response = {
        'message': f"Account closed and will be updated in Block {index}",
        'account': account.mapped
    }

    return jsonify(response), 200

@erp.route('/clients/deposit', methods=['POST'])
def deposit():
    values = request.get_json()
    required = ['bank_num', 'account_num', 'amount']

    if not all(k in values for k in required):
        return "Missing values", 400
    
    try:
        amount, index = bank.deposit(values['bank_num'], values['account_num'], values['amount'])
    except ValueError:
        return "Associated client with bank number not found", 400
    
    response = {
        'message': f"Amount deposited and will be updated in Block {index}",
        'account_value': amount
    }

    return jsonify(response), 200

@erp.route('/clients/withdraw', methods=['POST'])
def withdraw():
    values = request.get_json()
    required = ['bank_num', 'account_num', 'amount']

    if not all(k in values for k in required):
        return "Missing values", 400
    
    try:
        amount, index = bank.withdraw(values['bank_num'], values['account_num'], values['amount'])
    except ValueError:
        return "Associated client with bank number not found", 400
    
    response = {
        'message': f"Amount withdrawn and will be updated in Block {index}",
        'account_value': amount
    }

    return jsonify(response), 200

@erp.route('/clients/transfer', methods=['POST'])
def transfer():
    values = request.get_json()
    required = ['bank_num', 'account_num', 'recipient_num', 'amount']

    if not all(k in values for k in required):
        return "Missing values", 400
    
    try:
        result, index = bank.transfer(values['bank_num'], values['account_num'], values['recipient_num'], values['amount'])
    except ValueError:
        return "Associated client with bank number not found", 400
    
    response = {
        'message': f"Amount transferred and will be updated in Block {index}",
        'result': result
    }

    return jsonify(response), 200

@erp.route('/clients/compound', methods=['GET'])
def client_compound_interest():
    index = bank.client_compound_interest()

    response = {
        'message': f'Interest compounded; will be updated in Block {index}'
    }

    return jsonify(response), 200
