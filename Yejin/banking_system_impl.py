from banking_system import BankingSystem

class BankingSystemImpl(BankingSystem):
    """
    Implementation for:
        1) Level 1: create_account, deposit, transfer
        2) Level 2: top_spenders
        3) Level 3: pay, get_payment_status
        4) Level 4: merge_accounts, get_balanced
    """
    
    def __init__(self) -> None:
        # Dictionary that stores all accounts.
        # Key    : account_id (str)
        # Value  : account_info (dict with "balanced" and "transactions")
        
        self.whole_accounts: dict = {}  
        self.MILLISECONDS_IN_1_DAY = 86400000 # number of seconds in 1 day (24 hours)
        
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
        │             ├── "operation": str (e.g., 'created account', 'deposited', 'transferred out', 'transferred in', 'cashback')
        │             ├── "amount": int
        │             ├── "payment_id": str (e.g., 'payment1')
        │             └── "deposited": bool
        '''
        
#-----Helper function-----#
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

#-----Main functions-----#
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
        
        # Process any pending cashback up to this timestamp
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
        
        # Process any pending cashback up to this timestamp
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
        
        # Process any pending cashback up to this timestamp
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


    # Level 3: Pay
    def pay(self, 
            timestamp : int, 
            account_id: str, 
            amount: int) -> str | None:
        
        # Process any pending cashback up to this timestamp
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
                                                'payment_id': num_payment,
                                                'deposited' : False
                                            })

        return num_payment


    # Level 3: Get payment status
    def get_payment_status(self, 
                           timestamp, 
                           account_id, 
                           payment) -> str | None:
        
        # Process any pending cashback up to this timestamp
        self._process_cashbacks(timestamp)
        
        # check if the account exists
        if account_id not in self.whole_accounts:
            return None
        
        payment_found = False
        # check if the payment is in the referenced account
        transaction_dict = self.whole_accounts[account_id]['transactions']
        for transaction in transaction_dict:
            if transaction['operation'] == payment:
                payment_found = True
                break

        if not payment_found:
            return None
        
        # check if caskback has been deposited
        for transaction in transaction_dict:
            if (
                transaction['operation'] == 'cashback'
                and transaction['payment_id'] == payment
            ):
                # check if cashback has been deposited, if not, deposit it
                if transaction['deposited'] is True:
                    return 'CASHBACK_RECEIVED'
                else:
                    return 'IN_PROGRESS'


    # Level 4: Merge
    def merge_accounts(self, 
                       timestamp: int, 
                       account_id_1: str, 
                       account_id_2: str)-> bool:
        
        # Process any pending cashback up to this timestamp
        self._process_cashbacks(timestamp)
        
        #check if the accounts are same
        if account_id_1 == account_id_2:
            return False
        # Both accounts must exist
        if account_id_1 not in self.whole_accounts or account_id_2 not in self.whole_accounts:
            return False
        
        acc1_info = self.whole_accounts[account_id_1]
        acc2_info = self.whole_accounts[account_id_2]
        
        # Add account2's balance into account1
        acc1_info['balance'] += acc2_info['balance']
        
        # Move all transactions of account2 into account1
        acc1_info['transactions'].extend(acc2_info['transactions'])
        
        # Remove account2 entirely from the system
        del self.whole_accounts[account_id_2]
        
        return True
    
    
    # Level 4: Get balance
    def get_balance(self, 
                    timestamp: int, 
                    account_id: str, 
                    time_at: int)-> int | None:
        
        # Process any pending cashback up to this timestamp
        #self._process_cashbacks(timestamp)
        
        if account_id not in self.whole_accounts:
            return None
        
        transactions = self.whole_accounts[account_id]['transactions']
        if not transactions:
            return None
        
        created_timestamp = [t['timestamp'] 
                             for t in transactions 
                             if t['operation'] == "created account"]
        if not created_timestamp:
            return None
        
        if time_at < min(created_timestamp):
            return None
        
        
        transactions_before_time = []
        for t in transactions:
            if t['timestamp'] <= time_at:
                transactions_before_time.append(t)
        transactions_before_time.sort(key=lambda t: t['timestamp'])
        
        balance =  0
        
        for tx in transactions_before_time:
            op = tx['operation']
            amt = tx['amount']
            
            if op in ('deposited', 'transferred in', 'cashback'):
                balance += amt
            elif op == 'transferred out' or op.startswith('payment'):
                balance -= amt
                
        return balance


if __name__ == "__main__":
    DAY = BankingSystemImpl().MILLISECONDS_IN_1_DAY

    # =========================
    # Example 1 
    # =========================
    print("=== Example 1 ===")
    bank = BankingSystemImpl()

    r = bank.create_account(1, "account1")
    print("create_account(1, 'account1') ->", r)
    assert r is True

    r = bank.create_account(2, "account2")
    print("create_account(2, 'account2') ->", r)
    assert r is True

    r = bank.deposit(3, "account1", 2000)
    print("deposit(3, 'account1', 2000) ->", r)
    assert r == 2000

    r = bank.deposit(4, "account2", 2000)
    print("deposit(4, 'account2', 2000) ->", r)
    assert r == 2000

    r = bank.pay(5, "account2", 2000)
    print("pay(5, 'account2', 2000) ->", r)
    assert r == "payment1"

    r = bank.transfer(6, "account1", "account2", 500)
    print("transfer(6, 'account1', 'account2', 500) ->", r)
    assert r == 1500

    r = bank.merge_accounts(7, "account1", "non-existing")
    print("merge_accounts(7, 'account1', 'non-existing') ->", r)
    assert r is False

    r = bank.merge_accounts(8, "account1", "account1")
    print("merge_accounts(8, 'account1', 'account1') ->", r)
    assert r is False

    r = bank.merge_accounts(9, "account1", "account2")
    print("merge_accounts(9, 'account1', 'account2') ->", r)
    assert r is True

    r = bank.deposit(10, "account1", 100)
    print("deposit(10, 'account1', 100) ->", r)
    assert r == 2100 

    r = bank.deposit(11, "account2", 100)
    print("deposit(11, 'account2', 100) ->", r)
    assert r is None

    r = bank.get_payment_status(12, "account2", "payment1")
    print("get_payment_status(12, 'account2', 'payment1') ->", r)
    assert r is None

    r = bank.get_payment_status(13, "account1", "payment1")
    print("get_payment_status(13, 'account1', 'payment1') ->", r)
    assert r == "IN_PROGRESS"

    r = bank.get_balance(14, "account2", 1)
    print("get_balance(14, 'account2', 1) ->", r)
    assert r is None  # account2는 time_at=1 시점에 아직 생성 전

    r = bank.get_balance(15, "account2", 9)
    print("get_balance(15, 'account2', 9) ->", r)
    assert r is None  # account2는 이미 merge되어 삭제됨

    r = bank.get_balance(16, "account1", 11)
    print("get_balance(16, 'account1', 11) ->", r)
    assert r == 2100 #3800

    t = 5 + DAY
    r = bank.deposit(t, "account1", 100)
    print(f"deposit(5 + DAY, 'account1', 100) [t={t}] ->", r)
    assert r == 2240 #3906

    print("Example 1 passed.\n")

    # =========================
    # Example 2 (Another example)
    # =========================
    print("=== Example 2 (Another example) ===")
    bank2 = BankingSystemImpl()

    r = bank2.create_account(1, "account1")
    print("create_account(1, 'account1') ->", r)
    assert r is True

    r = bank2.deposit(2, "account1", 1000)
    print("deposit(2, 'account1', 1000) ->", r)
    assert r == 1000

    r = bank2.pay(3, "account1", 300)
    print("pay(3, 'account1', 300) ->", r)
    assert r == "payment1"

    # time_at = 3 시점 잔액
    r = bank2.get_balance(4, "account1", 3)
    print("get_balance(4, 'account1', 3) ->", r)
    assert r == 700

    # time_at = 2 + DAY : 아직 cashback 시점(3 + DAY) 이전이므로 여전히 700
    r = bank2.get_balance(5 + DAY, "account1", 2 + DAY)
    print(f"get_balance(5 + DAY, 'account1', 2 + DAY) -> {r}")
    assert r == 700

    # time_at = 3 + DAY : cashback(2%) 6이 반영되어 706
    r = bank2.get_balance(6 + DAY, "account1", 3 + DAY)
    print(f"get_balance(6 + DAY, 'account1', 3 + DAY) -> {r}")
    assert r == 706

    print("Example 2 passed.\n")

    print("✅ All example tests passed.")
