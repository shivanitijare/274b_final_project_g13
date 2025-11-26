from banking_system import BankingSystem

class BankingSystemImpl(BankingSystem):
    """
    Implementation for:
        1) Level 1: create_account, deposit, transfer
        2) Level 2: top_spenders
        3) Level 3: pay, get_payment_status
    """

    def __init__(self) -> None:
        # Dictionary that stores all accounts.
        # Key    : account_id (str)
        # Value  : account_info (dict with "balanced" and "transactions")
        self.whole_accounts: dict = {}  
        
        '''
        # Example structure
        whole_accounts: dict[account_id:str, account_info: dict]

        account_info: dict {
            "balance": int,
            "transactions": list[transaction]
        }

        transaction: dict {
            "timestamp": int,
            "operation": str,
            "amount": int
        }
        
        # Example structure in tree
        whole_accounts: dict
        │
        ├── key: account_id (str)
        │      value: account_info (dict)
        │
        │ account_info
        │ ├── "balance": int
        │ └── "transactions": list
        │        └── transaction dict:
        │             ├── "timestamp": int
        │             ├── "operation": str
        │             └── "amount": int
        '''

        self.MILLISECONDS_IN_1_DAY = 86400000 # number of seconds in 1 day (24 hours)

    def _process_cashbacks(self, timestamp: int) -> None:
        """
        Go through all scheduled cashback transactions stored inside whole_accounts,
        and deposit any cashback whose due timestamp <= current timestamp,
        and which has not yet been deposited.
        """
        for account_info in self.whole_accounts.values():
            for transaction in account_info["transactions"]:
                if (
                    transaction["operation"] == "cashback"
                    and transaction["timestamp"] <= timestamp
                    and transaction["deposited"] is False
                ):
                    # deposit cashback
                    account_info["balance"] += transaction["amount"]
                    transaction["deposited"] = True

    # Level 1: Create account
    def create_account(self, 
                       timestamp: int,
                       account_id: str) -> bool: 
        # If the account already exists, creation fails
        if account_id in self.whole_accounts:
            return False
        
        # Initialize a new account with balance of 0 and an empty transaction list
        account_info = {'balance': 0,
                        'transactions': []}
        
        # Record the "created account" tranactionn 
        account_info['transactions'].append({'timestamp': timestamp,
                                            'operation': 'created account',
                                            'amount': 0}) 
        
        # Store the new account in the main dictionary
        self.whole_accounts[account_id] = account_info 
        return True

    # Level 1: Deposit
    def deposit(self, 
                timestamp: int, 
                account_id: str, 
                amount: int) -> int | None:
        
        self._process_cashbacks(timestamp)
        
        # If the account does not exists
        if account_id not in self.whole_accounts:
            return None
        
        # Get the account information
        account_info = self.whole_accounts[account_id]
        # Record the deposit transaction
        account_info['transactions'].append({   'timestamp': timestamp,
                                                'operation': 'deposited',
                                                'amount': amount
                                                })

        # Increase the balance by the deposit amount
        account_info['balance'] += amount
        
        # Return the updated balance
        return account_info['balance']


    # Level 1: Transfer
    def transfer(self,
                 timestamp: int,
                 source_account_id: str,
                 target_account_id: str,
                 amount: int,) -> int | None:
        
        self._process_cashbacks(timestamp)

        # If either account does not exist, or they are the same, transfer fails
        if (
            source_account_id not in self.whole_accounts
            or target_account_id not in self.whole_accounts
            or source_account_id == target_account_id
        ):
            return None
        
        # If the source account does not have enough balance, transfer fails
        if self.whole_accounts[source_account_id]['balance'] < amount:
            return None

        # Source account: recored outgoing transfer and decrease balance
        account_info_source = self.whole_accounts[source_account_id]
        account_info_source['transactions'].append({'timestamp': timestamp,
                                                'operation': 'transferred out',
                                                'amount': amount})
        account_info_source['balance'] -= amount
        
        # Target account: record incoming transfer transfer and increase balance
        account_info_target = self.whole_accounts[target_account_id]
        account_info_target['transactions'].append({'timestamp': timestamp,
                                                'operation': 'transferred in',
                                                'amount': amount})
        account_info_target['balance'] += amount
        
        # Return the updated balance of the source account
        return account_info_source['balance']


    # Level 2: Top spenders
    def top_spenders(self, 
                     timestamp: int, 
                     n: int) -> list[str]:
        
        self._process_cashbacks(timestamp)

        # Put each account_id to its total outgoing amount in dictionary
        spender_sum = {} 
        
        # Iterate over all accounts
        for account_id, account_info in self.whole_accounts.items():
            # Start with 0 outgoing for account
            spender_sum[account_id] = 0
            
            # Scan all transactions of this account
            for indiv_trans in account_info['transactions']: 
                # Outgoing money is recorded when operatioin is transferred out (or starts with payment)
                if indiv_trans['operation'] == 'transferred out'or indiv_trans['operation'].startswith('payment'):
                    spender_sum[account_id] += indiv_trans['amount']
                
        # Store the total outgoing amount for this account
        sorted_spender_sum = sorted(spender_sum.items(), key=lambda item: (-item[1], item[0]))
    
        if len(sorted_spender_sum) < n:
            n = len(sorted_spender_sum)
            
        top_n = sorted_spender_sum[:n]
        
        result = [f"{acc}({amt})" for acc, amt in top_n]
        return result
    
    # Level 3: Pay()
    def pay(self, 
            timestamp, 
            account_id, 
            amount) -> str | None:
        
        self._process_cashbacks(timestamp)
        
        # if either account does not exist or if account has insuffiecent funds, payment fails, return None
        if (    
                account_id not in self.whole_accounts
                or self.whole_accounts[account_id]['balance'] < amount
            ):
            return None
        
        account_info = self.whole_accounts[account_id]

        # deduct funds from account
        account_info['balance'] -= amount

        # count the number of prior payment in respecive account
        payment_count = 1

        for account in self.whole_accounts: # loop through all accounts
            # loop through all transaction oeprations of each account
            for transaction in self.whole_accounts[account]['transactions']: 
                if transaction['operation'].startswith('payment'):
                    payment_count += 1

        num_payment = f'payment{payment_count}'

        # add payment to transactions
        account_info['transactions'].append({  
                                                'timestamp' : timestamp,
                                                'operation' : num_payment,
                                                'amount' : amount
                                            })
        
        # add cashback to transactions
        cashback_mult = 0.02 # 2% cashback multiplier
        account_info['transactions'].append({ 
                                                'timestamp' : timestamp + self.MILLISECONDS_IN_1_DAY,
                                                'operation' : 'cashback',
                                                'amount'    : int(amount * cashback_mult),
                                                'payment'   : num_payment,
                                                'deposited' : False
                                            })
        
        '''# add cashback instance to cashback_tracking
        self.cashback_tracking[account_id][num_payment].append({
                                                                    'timestamp' : timestamp + self.MILLISECONDS_IN_1_DAY,
                                                                    'payment'   : num_payment,
                                                                    'amount'    : amount * cashback_mult,
                                                                    'deposited' : False
                                                                })
'''
        return num_payment
    
    def get_payment_status(self, 
                           timestamp, 
                           account_id, 
                           payment) -> str | None:
        
        self._process_cashbacks(timestamp)
        #check if the account exists
        if account_id not in self.whole_accounts:
            return None
        
        account_info = self.whole_accounts[account_id]['transactions']

        payment_found = False
        # check if the payment is in the referenced account
        for transaction in account_info:
            if transaction['operation'] == payment:
                payment_found = True
                break

        if not payment_found:
            return None
        
        # check if caskback has been deposited
        for transaction in account_info:
            if (
                transaction['operation'] == 'cashback'
                and transaction['payment'] == payment
            ):
                # 'deposited' flag tells us if cashback has been applied
                if transaction['deposited'] is True:
                    return 'CASHBACK_RECEIVED'
                else:
                    return 'IN_PROGRESS'
    

