from .hr import Employee
from .repo import RepoPortfolio, Repo
from .interbank import InterbankLoanPortfolio
from .clients import Client, Account

import json
import requests
import hashlib

from urllib.parse import urlparse
from uuid import uuid4
from time import time

class Bank:

    def __init__(self):
        self.nodes = set()
        self.chains = {
            'meta': [],
            'finance': [],
            'hr': [],
            'clients': []
        }

        self.current_transactions = {
            'meta': [],
            'finance': [],
            'hr': [],
            'clients': []
        }

        self.employees = []
        self.clients = []

        self.genesis()

    # ----------------------------------
    #            Blockchain
    # ----------------------------------

    def genesis(self):
        for type in ['meta', 'finance', 'hr', 'clients']:
            if type == 'meta':
                self.add_transaction(type, {'interest': 0.05, 'reserve_ratio': 0.2})
            elif type == 'finance':
                # Initialize chain with new RepoPortfolio and InterbankLoanPortfolio
                repo = RepoPortfolio()
                interbank = InterbankLoanPortfolio(0.02)
                self.add_transaction(type, repo.mapped)
                self.add_transaction(type, interbank.mapped)
            self.add_block(type, 100, 1)

    def register_node(self, authorizer, address):
        if self.nodes:
            print(self.nodes)
            if authorizer not in self.nodes:
                raise ValueError("Not authorized.")
        
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            #Add Node
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'. Check parseurl documentation
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')
        
    def validate_chains(self, chains):
        for type in ['meta', 'finance', 'hr', 'clients']:
            last_block = chains[type][0]
            current_index = 1

            while current_index < len(chains[type]):
                block = chains[type][current_index]
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
        pass

    def add_block(self, type, proof, previous_hash):
        block = {
            'index': len(self.chains[type]) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions[type],
            'proof': proof,
            'previous_hash': previous_hash,
        }

        self.current_transactions[type] = []
        self.chains[type].append(block)
        
        return block

    def add_transaction(self, type, data):
        if type not in ['meta', 'finance', 'hr', 'clients']:
            raise ValueError("Transaction type not recognized.")

        self.current_transactions[type].append(data)

        if len(self.chains[type]) == 0:
            return 1
        return self.chains[type][-1]['index'] + 1

    @staticmethod
    def hash(block):
        print(block)
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

    # ----------------------------------
    #               Meta
    # ----------------------------------
    
    def set_meta(self, rate, ratio):
        data = {
            'interest': rate,
            'reserve_ratio': ratio
        }
        new_index = self.add_transaction('meta', data)
        return new_index

    def get_meta(self):
        meta = self.chains['meta'][-1]['transactions'][-1]
        return meta

    # ----------------------------------
    #              Finance
    # ----------------------------------

    @property
    def reserves(self) -> float:
        # Calculate total reserves first
        interbank = self.get_interbank().cash
        repo = self.get_repo().reserves

        client_reserves = 0
        for bank_num in self.clients:
            client = self.get_client(bank_num)
            for account in client.accounts:
                client_reserves += account.amount

        # Calculate liabilities from employee salaries
        payroll = 0
        for employee_num in self.employees:
            employee = self.get_employee(employee_num)
            payroll += employee.salary
        
        return interbank + repo + client_reserves - payroll

    def validate_reserves(self) -> bool:
        liabilities = self.get_interbank().liabilities
        repo = self.get_repo().reserves
        reserve_ratio = self.get_meta()['reserve_ratio']

        client_reserves = 0
        for bank_num in self.clients:
            client = self.get_client(bank_num)
            for account in client.accounts:
                client_reserves += account.amount

        if (client_reserves + repo - liabilities) / (client_reserves + repo) >= reserve_ratio:
            return True
        return False

    def get_interbank(self) -> InterbankLoanPortfolio:
        i = len(self.chains['finance']) - 1
        while i >= 0:
            block = self.chains['finance'][i]
            j = len(block['transactions']) - 1
            while j >= 0:
                try:
                    inter = block['transactions'][j]
                    return InterbankLoanPortfolio(inter['interest'], inter['assets'], inter['liabilities'], inter['cash'])
                except KeyError:  # Caught if the current transaction isn't for an InterbankLoanPortfolio
                    continue

    def borrow(self, amount):
        interbank = self.get_interbank()
        new_cash = interbank.borrow(amount)
        index = self.add_transaction('finance', interbank.mapped)

        return new_cash, index

    def lend(self, amount):
        interbank = self.get_interbank()
        new_cash = interbank.lend(amount)
        index = self.add_transaction('finance', interbank.mapped)

        return new_cash, index

    def interbank_compound_interest(self):
        interbank = self.get_interbank()
        net_value = interbank.compound_interest()
        index = self.add_transaction('finance', interbank.mapped)

        return net_value, index

    def get_repo(self) -> RepoPortfolio:
        i = len(self.chains['finance']) - 1
        while i >= 0:
            block = self.chains['finance'][i]
            j = len(block['transactions']) - 1
            while j >= 0:
                try:
                    repo = block['transactions'][j]
                    return RepoPortfolio(repo['portfolio'])
                except KeyError:  # Caught if the current transaction isn't for a RepoPortfolio
                    continue

    def buy_repo(self, ytm, par=1000):
        portfolio = self.get_repo()
        repo = portfolio.buy_repo(ytm, par)

        index = self.add_transaction('finance', portfolio.mapped)

        return repo.mapped, index

    def sell_repo(self, ytm, par=1000):
        portfolio = self.get_repo()
        repo = portfolio.sell_repo(ytm, par)

        index = self.add_transaction('finance', portfolio.mapped)

        return repo.mapped, index

    # ----------------------------------
    #          Human Resources
    # ----------------------------------

    def add_employee(self, salary, department, supervisor_id):
        employee = Employee(uuid4().hex, salary, department, supervisor_id)
        self.employees.append(employee.employee_num)
        index = self.add_transaction('hr', employee.mapped)
        
        return index

    def get_employee(self, employee_num) -> Employee:
        i = len(self.chains['hr']) - 1
        while i >= 0:
            block = self.chains['hr'][i]
            j = len(block['transactions']) - 1
            while j >= 0:
                current_emp = block['transactions'][j]
                if current_emp['employee_num'] == employee_num:
                    return Employee(current_emp['employee_num'], current_emp['salary'], current_emp['department'], current_emp['supervisor_id'])
                j -= 1
            i -= 1
        raise ValueError("Invalid employee number.")

    # ----------------------------------
    #              Clients
    # ----------------------------------

    def add_client(self):
        client = Client(uuid4().hex)
        self.clients.append(client.bank_num)

        index = self.add_transaction('clients', client.mapped)

        return index

    def get_client(self, bank_num):
        i = len(self.chains['clients']) - 1
        while i >= 0:
            block = self.chains['clients'][i]
            j = len(block['transactions']) - 1
            while j >= 0:
                current_client = block['transactions'][j]
                if current_client['bank_num'] == bank_num:
                    accounts = []
                    for account in current_client['accounts']:
                        accounts.append(Account(account['amount'], account['interest'], account['type'], account['account_num']))
                    return Client(current_client['bank_num'], current_client['n_accounts'], current_client['accounts'])
                j -= 1
            i -= 1
        raise ValueError("Client not found")

    def open_account(self, bank_num, principal, type):
        client = self.get_client(bank_num)
        interest = self.get_meta()['interest']
        account = client.open_account(principal, interest, type)

        index = self.add_transaction('clients', client.mapped)
        return account, index

    def close_account(self, bank_num, account_num):
        client = self.get_client(bank_num)
        closed_account = client.close_account(account_num)

        index = self.add_transaction('clients', client.mapped)

        return closed_account, index

    def deposit(self, bank_num, account_num, amount):
        client = self.get_client(bank_num)
        account = client.get_account(account_num)

        new_amount = account.deposit(amount)
        index = self.add_transaction('clients', client.mapped)

        return new_amount, index
        
    def withdraw(self, bank_num, account_num, amount):
        client = self.get_client(bank_num)
        account = client.get_account(account_num)

        withdrawn = account.withdraw(amount)
        index = self.add_transaction('clients', client.mapped)

        return withdrawn, index

    def transfer(self, bank_num, account_num, recipient_num, amount):
        client = self.get_client(bank_num)
        sender = client.get_account(account_num)
        receiver = client.get_account(recipient_num)

        result = sender.transfer(receiver, amount)
        index = self.add_transaction('clients', client.mapped)

        return result, index

    def client_compound_interest(self):
        for bank_num in self.clients:
            client = self.get_client(bank_num)
            for i in range(len(client.accounts)):
                client.accounts[i].compound_interest()
                index = self.add_transaction('clients', client.mapped)
        return index
    