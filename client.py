"""
Alice Prototype (Client)

Author @ Zhao Yea
"""

import os
import json
import pickle
import socket

from encryption.RSACipher import *
from blockchain import Blockchain

UUID = "4226355408"
HOST, PORT = "localhost", 1339
BUFSIZE = 1024
CACHE_SITES = []

# Public Key Directory
ALICE_PUBKEY_DIR = r"client/alice.pub"
BROKER_PUBKEY_DIR = r"client/dnStack.pub"

# Private Key Directory
ALICE_SECRET = r"/home/osboxes/.ssh/alice_rsa"

# Directory to store Zone File
ZONE_FILE_DIR = r"client/{}/dns_zone.json".format(UUID)

# Flags
ZONE_FILE = "zone_file".encode()


class Client(object):
    def __init__(self, host, port):
        """
        Initial Connection to the Broker Address
        @param host: <str> IP Addr of the Broker
        @param port: <int> Port number of the Broker
        @return: <sock> Client socket connection to the Broker
        """
        print(f"[*] Connecting to Broker @ ({host},{port})")

        # Start the blockchain
        self.blockchain = Blockchain()

        # Initialise socket
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connects to broker
        try:
            self.client_sock.connect((host, port))

        except socket.error:
            print("[!] Connection failed! Please check your network connectivity and try again.")
            self.client_sock.close()

        # Send client pubkey over to server on initial connection
        server_hello_msg = (UUID, self.get_pubkey(ALICE_PUBKEY_DIR))
        self.client_sock.send(pickle.dumps(server_hello_msg))

        # Run the message_handle
        self.message_handle()

    def message_handle(self):
        """ Handles the message between server and client """

        # Load the RSACipher for encryption/decryption
        rsa_cipher = RSACipher()
        privkey = rsa_cipher.load_privkey(ALICE_SECRET)

        try:
            # Prepare for incoming data
            data = b""
            while True:
                packet = self.client_sock.recv(BUFSIZE)

                if not packet:
                    break

                # ZONE FILE HANDLER
                elif ZONE_FILE in packet:
                    data += packet.rstrip(ZONE_FILE)

                    # Load the encryption data list
                    enc, chain = pickle.loads(data)
                    # Prepare to write zone file contents locally and stored in client/ folder
                    with open(ZONE_FILE_DIR, "wb") as out_file:
                        for ciphertext in enc:
                            plaintext = rsa_cipher.decrypt_with_RSA(privkey, ciphertext)
                            out_file.write(plaintext)

                    print(chain)
                    # Verify the given blockchain
                    flag, msg = self.verify_blockchain(chain)
                    print(msg)

                    if flag:
                        # Update the client Blockchain
                        self.blockchain.chain = chain

                        # Run the user_menu
                        self.user_menu()

                # Concatenate the data
                data += packet

        except KeyboardInterrupt:
            self.client_sock.close()

        except socket.error:
            self.client_sock.close()

    def verify_blockchain(self, chain):
        """
        Verifies that the blockchain is authentic. Ensures equation is True.
        Equation: Previous hash * proof = 0000......
        @return: Returns True if blockchain is verified, False otherwise
        """
        last_block = chain[1]
        current_index = 2

        while current_index < len(chain):
            block = chain[current_index]

            # Check the hash of the block is correct
            if block['previous_hash'] != self.blockchain.block_hash(last_block):
                return (False, "[!] Error in blockchain! Do not visit any domains until you can update your zone file")

            # Check that the Proof of Work is correct:
            if not self.blockchain.valid_proof(last_block['previous_hash'], last_block['proof']):
                return (False, "[!] Error in blockchain! Do not visit any domains until you can update your zone file")

            last_block = block
            current_index += 1

        return (True, "[*] Blockchain verified successfully")

    @staticmethod
    def get_pubkey(pubkey_dir):
        """
        Function to get Public Key of Alice
        @param pubkey_dir: <str> Directory of the client's Public Key
        @return:
        """
        rsa_cipher = RSACipher()
        return rsa_cipher.load_pubkey(pubkey_dir).publickey().exportKey(format='PEM', passphrase=None, pkcs=1)

    def user_menu(self):
        # Temporary menu system for Proof Of Concept (POC)
        # Client will be browser/proxy in the future
        while True:
            print(f"\n\t###### Today's Menu ######")
            # print(f"\t[1] Request for DNS record (Update)")
            print(f"\t[1] Register a new domain")
            print(f"\t[2] Resolve a domain")
            print(f"\t[3] Resolve an IP address")
            print(f"\t[4] Quit")

            try:
                user_option = input("\t >  ")
            except KeyboardInterrupt:
                user_option = "4"

            if user_option == "4":
                # User wants to quit
                print("\n[!] Bye!")
                return False
            elif user_option == "1":
                # !! Currently not working !!
                # User wants to register a new domain
                print("[!] Option to register new domain chosen")
                self.register_domain()
            elif user_option == "2":
                # User wants to resolve a domain name
                print("[!] Option to resolve domain chosen")
                domain_name = input("[*] Enter domain name to resolve > ")
                self.resolve_domain(domain_name)
            elif user_option == "3":
                # User wants to resolve an IP address
                print("[!] Option to resolve IP address chosen")
                ip_addr = input("[*] Enter IP address to resolve > ")
                self.resolve_ip(ip_addr)
            else:
                # User doesn't know what he wants
                print("[*] Please select an option.")

    def register_domain(self):
        """
        Registers a new domain, currently only POC. Does not work fully.
        @return: True
        """

        # Requesting for new domain name to register
        print("[*] Please enter your new domain name, without any prefix. (Eg. google.stack, youtube.stack)")
        new_domain_name = input(" >  ")

        # Does a check if domain already exists
        print("[*] Checking if domain is taken... Please wait")
        for i in self.blockchain.chain[1:]:
            # If the domain exists in the blockchain
            if (i["transactions"][0]["domain_name"]) == new_domain_name:
                print(
                    f"[*] Domain {new_domain_name} already exists! Please choose another domain.")
                return False

        # Requests for zone file
        print("\n[*] Please enter the path to your zone file. (Eg. C:\\Users\\bitcoinmaster\\bitcoinzone.json)")
        new_zone_file = input(" >  ")

        # TODO Check if zone_file:
        # - Is in correct json format

        # Checks if file exists
        if not os.path.isfile(new_zone_file):
            print("\n[*] File not found.")
            return False

        print("\n\t###### Registering new domain ######")
        print(f"\tClient: {UUID}")
        print(f"\tDomain Name: {new_domain_name}")
        print(f"\tZone File: {new_zone_file}")

        try:
            user_confirmation = input("\n[*] Continue? Y/N > ")
        except KeyboardInterrupt:
            return False

        if user_confirmation == "Y":
            self.blockchain.new_transaction(client=UUID, domain_name=new_domain_name,
                                            zone_file_hash=self.blockchain.generate_sha256(new_zone_file))

        # TODO Forward transaction to broker then to miner
        self.client_sock.send(pickle.dumps(self.blockchain.current_transactions))

        return True

    def resolve_domain(self, domain_name):
        """
        Resolves domains
        @param domain_name: <str> Domain name to resolve to IP address
        @return: Returns True if domain is resolved, False otherwise
        """

        # Locates domain in blockchain
        for i in self.blockchain.chain[1:]:
            # If the domain exists in the blockchain
            if (i["transactions"][0]["domain_name"]) == domain_name:

                # Loads in zone file
                with open(ZONE_FILE_DIR, "rb") as in_file:
                    data = json.loads(in_file.read())

                # Loops through to locate requested domain
                for domains in data.keys():
                    if domains == domain_name:
                        print("\n\t###### IP Addresses ######")
                        for i in data[domains]:
                            print(f"\t{i['type']}\t{i['data']}")
                        return True

        print("[*] Domain does not exist! Have you updated your zone file?")
        return False

    def resolve_ip(self, ip_address):
        """
        Resolves IP addresses
        @param ip_address: <str> IP address to resolve to domain name
        @return: Returns True if IP address is resolved, False otherwise
        """

        # Loads in zone file
        with open(ZONE_FILE_DIR, "rb") as in_file:
            data = json.loads(in_file.read())

        # Loops through to locate requested IP address
        for domain in data.keys():
            for subdomains in data[domain]:
                if subdomains["data"] == ip_address:
                    print("\n\t###### Domain Name ######")
                    print(f"\t{domain}")
                    return True

        print("[*] IP address does not exist! Have you updated your zone file?")
        return False


if __name__ == '__main__':
    # Create directory if it does not exist
    if not os.path.exists(os.path.dirname(ZONE_FILE_DIR)):
        os.mkdir(os.path.dirname(ZONE_FILE_DIR))

    # Run the client connection with the broker
    Client(HOST, PORT)
