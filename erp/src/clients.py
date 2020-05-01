from uuid import uuid4

class Client:

    def __init__(self, bank_num, n_accounts=0, accounts=None):
        self.bank_num = bank_num
        self.n_accounts = n_accounts
        if accounts is None:
            self.accounts = []
        else:
            self.accounts = accounts

    def get_account(self, account_num):
        for account in self.accounts:
            if account.account_num == account_num:
                return account
        raise ValueError("Account number doesn't match existing accounts.")

    def open_account(self, principal: float, interest: float, type: str):
        if not (type == "checking" or type == "savings"):
            raise ValueError("Account type must be checking or savings")
        
        self.accounts.append(Account(principal, 0, type))
        self.n_accounts += 1
        return self.accounts[-1]

    def close_account(self, account_num):
        for i in range (len(self.accounts)):
            if self.accounts[i].account_num == account_num:
                account = self.accounts.pop(i)
                self.n_accounts -= 1
                return account
        raise ValueError("Account number doesn't match existing accounts.")

    @property
    def mapped(self):
        # mapped = []
        # for account in self.accounts:
        #     mapped.append({
        #         "account_num": account.account_num,
        #         "amount": account.amount,
        #         "type": account.type,
        #         "interest": account.interest,
        #     })
        return {
            "bank_num": self.bank_num,
            "n_accounts": self.n_accounts,
            "accounts": [account.mapped for account in self.accounts]
        }


class Account:

    def __init__(self, principal: float, interest: float, type: str, account_num=None):
        self.amount = principal
        self.type = type
        self.interest = interest if type == "savings" else 0
        
        if account_num is None:
            self.account_num = uuid4().hex
        else:
            self.account_num = account_num

    def compound_interest(self):
        self.amount *= (1 + self.interest)

    def deposit(self, amount):
        self.amount += amount
        return self.amount

    def withdraw(self, amount):
        if self.type == "checking":
            self.amount -= amount
            return amount
        else:
            self.amount -= amount * 0.9
            return amount * 0.9
        
    def transfer(self, recipient, amount):
        if self.type == "savings":
            raise AttributeError("Transfers are not allowed for savings accounts.")
        
        self.amount -= amount
        recipient.amount += amount

        return {recipient.account_num: amount}

    @property
    def mapped(self):
        return {
            "account_num": self.account_num,
            "amount": self.amount,
            "type": self.type,
            "interest": self.interest
        }
