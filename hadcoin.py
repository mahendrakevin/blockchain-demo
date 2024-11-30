# Module 2 - create cryptocurrency

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# Part 1 - Building a Blockchain
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        # Create the genesis block
        self.create_block(proof=1, previous_hash='0' * 64)
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }

        self.transactions = []

        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    @staticmethod
    def proof_of_work(previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = (hashlib
                              .sha256(str(new_proof ** 2 - previous_proof ** 2).encode())
                              .hexdigest())

            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    @staticmethod
    def hash(block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = (hashlib
                              .sha256(str(proof ** 2 - previous_proof ** 2).encode())
                              .hexdigest())
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transactions(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True


# Part 2 - Mining Blockchain
app = Flask(__name__)

# Creating an address for the node on Port
node_address = str(uuid4()).replace('-', '')

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
blockchain = Blockchain()


@app.get('/mine_block')
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(sender=node_address, receiver='Kevin', amount=1)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Congratulations, you just mined a block!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200


@app.post('/add_transaction')
def add_transaction():
    data = request.get_json()
    transactions_key = ['sender', 'receiver', 'amount']
    if not all(key in data for key in transactions_key):
        return 'Some lements of the transaction are missing', 400

    index = blockchain.add_transactions(data['sender'], data['receiver'], data['amount'])
    response = {'message': f'This transactions will be added to Block {index}'}
    return jsonify(response), 201


@app.get('/is_valid')
def is_valid():
    block = blockchain.chain
    response = {
        'is_valid': blockchain.is_chain_valid(block)
    }

    return jsonify(response), 200


@app.get('/get_chain')
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }

    return jsonify(response), 200


# Part 3 Decentralizing blockchain
app.run(host='0.0.0.0', port=5001, debug=True)
