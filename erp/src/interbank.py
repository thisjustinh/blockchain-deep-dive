class InterbankLoanPortfolio:

    def __init__(self, interest, assets=0, liabilities=0, cash=0):
        self.assets = assets
        self.liabilities = liabilities
        self.cash = cash
        self.interest = interest

    @property
    def net_value(self):
        return self.assets - self.liabilities

    def borrow(self, amount):
        self.liabilities += amount
        self.cash += amount
        return self.cash

    def lend(self, amount):
        self.assets += amount
        self.cash -= amount
        return self.cash

    def compound_interest(self):
        self.assets *= (1 + self.interest)
        self.liabilities *= (1 + self.interest)
        return self.net_value

    @property
    def mapped(self):
        return {
            'assets': self.assets,
            'liabilities': self.liabilities,
            'cash': self.cash,
            'interest': self.interest 
        }
