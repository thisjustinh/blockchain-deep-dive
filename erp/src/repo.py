class RepoPortfolio:

    def __init__(self, portfolio=None):
        if portfolio is None:
            self.portfolio = []
        else:
            self.portfolio = portfolio
    
    @property
    def number(self):
        return len(self.portfolio)
    
    @property
    def reserves(self):
        value = 0

        for bond in self.portfolio:
            if bond.flag == "buy":
                value -= bond.par
            else:
                value += bond.par

        return value

    @property
    def present_value(self):
        pv = 0

        for bond in self.portfolio:
            if bond.flag == "buy":
                pv -= bond.present_value
            else:
                pv += bond.present_value
        
        return pv

    def buy_repo(self, ytm, par):
        self.portfolio.append(Repo(ytm, "buy", par))
        return self.portfolio[-1]
    
    def sell_repo(self, ytm, par):
        self.portfolio.append(Repo(ytm, "sell", par))
        return self.portfolio[-1]

    @property
    def mapped(self):
        return {
            'portfolio': [repo.mapped for repo in self.portfolio],
        }


class Repo:

    def __init__(self, ytm, flag, par):
        self.par = par
        self.ytm = ytm

        if not (flag == "buy" or flag == "sell"):
            raise AttributeError("Flag value can only be `buy` or `sell.`")
        self.flag = flag

    @property
    def present_value(self):
        return self.par * (1 + self.ytm)

    @property
    def mapped(self):
        return {
            'par': self.par,
            'ytm': self.ytm,
            'flag': self.flag
        }
