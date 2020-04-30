'''
  In this file, I have added all the basic requirements that you need to complete the code, and the defenitions to build out the functions in succession. All you need to do is fill in the documentation, and submit the filled in file on GitHub, I will go over some of the components in class.
'''
from time import time
#Make sure that you do not change the imports and depandacies, I would also recomend exploring https://pypi.org/ for packages that you may not understand
import hashlib
import json

from urllib.parse import urlparse
from uuid import uuid4
# We Will be building a flask server that emulates a blockchain network, and allows users to create, mine and edit a blockchain network
import requests
from flask import Flask, jsonify, request


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block Sometime in the future using self.new_block({parms}) / Not in Quiz 1
        self.new_block(previous_hash='1', proof=100)
    def register_node(self, address):
        """
        :param address: Address of node

        Implement in Quiz 1:
          1) Using urlparse() parse the address param
          2) Add the Address to the nodes. with scheme
          3) Verify the URl, and give an error message if It is invalid
        """
        print(address)
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            #Add Node
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'. Check parseurl documentation
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')


    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print('\n ------------------------------ \n')
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False
            
            last_block = block
            current_index += 1
        
        return True

    def resolve_conflicts(self):
        neighbors = self.nodes
        new_chain = False

        max_length = len(self.chain)

        for node in neighbors:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        
        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block

        Implement in Quiz 1:
          1) Complete the framework for the new Block array below
            1.1) the new block's index is 1 greater than the len(self.chain)
            1.2) The timestamp of the new block is the current time which can be found using the time() library.
            1.3) Transactions can be found at the currently being processed transactions self.current_transactions.
            1.4) The proof is a param if the new block.
            1.5) Previous hash lockation can be found using the previous_hash or previous_hash algorithem: self.hash(self.chain[-1])
          2) Reset Transactions, and append the block with the new block.
          3) Verify the URl, and give an error message if It is invalid
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions in line 72. Remember transactions are stored in self.current_transactions
        self.current_transactions = []
        # In line 74, using self.chain.append() method, add the new object {block} to the blockchain.
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction

        Implement in Quiz 1:
          1) Complete the framework for the new transaction bellow
            1.1) the new transaction to be posted, needs the objects from the params {sender, redipient, amount}
          2) Reset 
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        #return the index of the new transaction. Old index can be found self.last_block['index']
        return self.last_block['index'] + 1

    @property
    def last_block(self):
      """
      Returns the last block.
      """
      return self.chain[-1]

    @staticmethod
    def hash(block):
        block_str = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Check if proof meets the target
        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"


app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)
    
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],  
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {
        'message': f'Transactions will be added to Block {index}'
    }
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    print(values)
    nodes = values['nodes']

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in list(nodes):
        blockchain.register_node(node)

    response = {
            'message': "New nodes have been added",
            'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': "Chain was replaced",
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': "Chain not replaced",
            'new_chain': blockchain.chain
        }
    return jsonify(response), 200

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
 
