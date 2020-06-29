"""
Block chain Implementation

Author @ Zhao Yea
"""

import hashlib
import json
from time import time


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.block_hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, client, domain_name, zone_file_hash):
        """
        Creates a new chunk of data to go into the our Block chain
        @param client: <str> uuid of the requesting client
        @param domain_name: <str> Domain name
        @param zone_file_hash: <hash> Hash of zone file
        @return: <int> Index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'client': client,
            'domain_name': domain_name,
            'zone_file_hash': zone_file_hash
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, previous_hash):
        """
        Simple Proof of Work Algorithm:
        :param previous_hash: <hash> Hash of the previous block
        :return: <int> Proof
        """

        proof = 0
        while not self.valid_proof(previous_hash, proof):
            proof += 1

        return proof

    @staticmethod
    def valid_proof(previous_hash, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param previous_hash: <int> Previous Hash of the block
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """
        # guess_hash = hashlib.sha256(f'{previous_hash * proof}'.encode()).hexdigest()
        # TODO This is a temp POW, faster for testing purposes
        guess_hash = hashlib.sha256(f'{previous_hash} * {proof}'.encode()).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def block_hash(block):
        """
        Create a SHA-256 hash of Block
        :param block: <dict> Block
        :return: <str> hash of block
        """

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def generate_sha256(fname):
        """
        Generate a sha256 hash of the given file
        @param fname: <dir> Directory of the given filename
        @return: <hash> SHA256 Hash of the given file
        """

        file_hash = hashlib.sha256()
        with open(fname, "rb") as in_file:
            for chunk in iter(lambda: in_file.read(4096), b""):
                file_hash.update(chunk)

        return file_hash.hexdigest()

    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]
