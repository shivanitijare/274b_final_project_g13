from banking_system import BankingSystem


class BankingSystemImpl(BankingSystem):
    """
    Implementation for:
        1) Level 1: create_account, deposit, transfer
        2) Level 2: top_spenders
    """
    
    def __init__(self) -> None:
        # Dictionary that stores all accounts.
        # Key    : account_id (str)
        # Value  : account_info (dict with "balanced" and "transactions")
        self.whole_accounts: dict = {} 


        self.withdraw_count = 0

        # Cashback events: timestamp -> list of (account_id, cashback_amount, payment_id)
        self.cashback_events = {}
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

    # cashback helper function for level 3
    def process_cashback(self, timestamp: int):
        # list to store all cashback times that are due
        pending_times = []

        # Check each scheduled cashback time
        for cashback_time in self.cashback_events:
            if cashback_time <= timestamp:
                pending_times.append(cashback_time)

        # Now process each pending cashback
        for t in pending_times:
            # Remove the list of cashback events for this timestamp from the dictionary
            events = self.cashback_events.pop(t)

            for (acc_id, cashback_amt, payment_id) in events:
                if acc_id in self.whole_accounts:
                    acc = self.whole_accounts[acc_id]
                    acc["balance"] += cashback_amt
                    acc["transactions"].append({
                        "timestamp": t,
                        "operation": "cashback",
                        "amount": cashback_amt,
                        "payment_id": payment_id
                    })


    # Level 1: Create account
    def create_account(self, timestamp: int, account_id: str) -> bool: 
        self.process_cashback(timestamp)

        # If the account already exists, creation fails
        if account_id in self.whole_accounts:
            return False
        
        # Initialize a new account with balance of 0 and an empty transaction list
        account_info = {'balance': 0,
                        'transactions': [],
                        'created_at': timestamp} # add for level 4
        
        # Record the "created account" tranactionn 
        account_info['transactions'].append({'timestamp': timestamp,
                                            'operation': 'created',
                                            'amount': 0}) 
        
        # Store the new account in the main dictionary
        self.whole_accounts[account_id] = account_info 
        return True


    # Level 1: Deposit
    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self.process_cashback(timestamp)

        # If the account exists
        if account_id in self.whole_accounts:
            # Get the account information
            account_info = self.whole_accounts[account_id]
            # Record the deposit transaction
            account_info['transactions'].append({'timestamp': timestamp,
                                                'operation': 'deposited',
                                                'amount': amount})
            # Increase the balance by the deposit amount
            account_info['balance'] += amount

             # Return the updated balance
            return account_info['balance']
        
        # If the account does not exist, return None
        return None
        


    # Level 1: Transfer
    def transfer(self,timestamp: int,source_account_id: str,target_account_id: str,amount: int,) -> int | None:
        self.process_cashback(timestamp)

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
    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        self.process_cashback(timestamp)

        # Put each account_id to its total outgoing amount in dictionary
        spender_sum = {} 
        
        # Iterate over all accounts
        for account_id, account_info in self.whole_accounts.items():
            # Start with 0 outgoing for account
            spender_sum[account_id] = 0
            
            # Scan all transactions of this account
            for indiv_trans in account_info['transactions']: 
                # Outgoing money is recorded when operatioin is transferred out
                if indiv_trans['operation'] == 'transferred out':
                    spender_sum[account_id] += indiv_trans['amount']
                
                # Level 3 extension 
                if indiv_trans['operation'] == 'paid':
                    spender_sum[account_id] += indiv_trans['amount']
                if indiv_trans['operation'] == 'withdrawn':
                    spender_sum[account_id] += indiv_trans['amount']
                    
        # Store the total outgoing amount for this account
        sorted_spender_sum = sorted(spender_sum.items(), key=lambda item: (-item[1], item[0]))
    
        if len(sorted_spender_sum) < n:
            n = len(sorted_spender_sum)
            
        top_n = sorted_spender_sum[:n]
        
        result = [f"{acc}({amt})" for acc, amt in top_n]
        return result
    
    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        # Process cashback first
        self.process_cashback(timestamp)

        # Account must exist
        if account_id not in self.whole_accounts:
            return None

        account_info = self.whole_accounts[account_id]

        # Must have enough funds
        if account_info["balance"] < amount:
            return None

        # Deduct the withdrawn money
        account_info["balance"] -= amount

        # Generate payment ID
        self.withdraw_count += 1
        payment_id = f"payment{self.withdraw_count}"

        # Record withdrawal transaction
        account_info["transactions"].append({
            "timestamp": timestamp,
            "operation": "withdrawn",
            "amount": amount,
            "payment_id": payment_id
        })

        # Calculate cashback (2%, rounded down)
        cashback = (amount * 2) // 100

        # Cashback occurs 24 hours later
        cashback_time = timestamp + 86400000 

        # Schedule cashback
        if cashback_time not in self.cashback_events:
            self.cashback_events[cashback_time] = []

        self.cashback_events[cashback_time].append((account_id, cashback, payment_id))

        return payment_id
    
    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        # First process any cashback due at this timestamp
        self.process_cashback(timestamp)

        # Check if account exists
        if account_id not in self.whole_accounts:
            return None

        account = self.whole_accounts[account_id]

        # Search for the withdrawal transaction that matches the payment ID
        withdraw_timestamp = None
        for trans in account["transactions"]:
            if trans["operation"] == "withdrawn" and trans.get("payment_id") == payment:
                withdraw_timestamp = trans["timestamp"]
                break

        if withdraw_timestamp is None:
            return None

        # cashback timestamp = withdrawal time + 24 hours (86400000 ms)
        cashback_time = withdraw_timestamp + 86400000

        # Determine if cashback has happened yet
        for trans in account["transactions"]:
            if (
                trans["operation"] == "cashback"
                and trans.get("payment_id") == payment
            ):
                return "CASHBACK_RECEIVED"

        if timestamp >= cashback_time:
            # If it wasn't found, we force process it now.
            self.process_cashback(timestamp)

            # Check again after forced process
            for trans in account["transactions"]:
                if (
                    trans["operation"] == "cashback"
                    and trans.get("payment_id") == payment
                ):
                    return "CASHBACK_RECEIVED"

        # else cashback is still pending
        return "IN_PROGRESS"
    
    # level 4
    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool:
        self.process_cashback(timestamp)

        # invalid merge
        if account_id_1 == account_id_2:
            return False
        if account_id_1 not in self.whole_accounts or account_id_2 not in self.whole_accounts:
            return False
        
        account1 = self.whole_accounts[account_id_1]
        account2 = self.whole_accounts[account_id_2]

        # merged account inherit earliest creation time
        created1 = account1.get('created_at', timestamp)
        created2 = account2.get('created_at', timestamp)
        account1['created_at'] = min(created1, created2)

        #transfer balance
        account1['balance'] += account2.get('balance', 0)

        #transfer transactions
        for i in account2['transactions']:
            transaction_copy = i.copy()
            transaction_copy['merged_at'] = timestamp #copy and tag
            account1['transactions'].append(transaction_copy)

        #make sure it is in chronological order
        account1['transactions'].sort(key = lambda t: t['timestamp'])

        # cashback events
        for cb_time in list(self.cashback_events.keys()):
            updated_events = []
            for (acc_id, cash_amt, payment_id) in self.cashback_events[cb_time]:
                if acc_id == account_id_2:
                    updated_events.append((account_id_1, cash_amt, payment_id))
                else:
                    updated_events.append((acc_id, cash_amt, payment_id))
            self.cashback_events[cb_time] = updated_events

        # delete merged account
        self.whole_accounts.pop(account_id_2, None)

        return True

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        self.process_cashback(timestamp)

        if account_id not in self.whole_accounts:
            return None
        
        account = self.whole_accounts[account_id]
        transactions = account['transactions']
        
        existed = False
        for i in transactions:
            if i['timestamp'] <= time_at:
                existed = True
                break
        
        #account not exist at time_at
        if not existed:
            return None

        balance = 0
        for i in transactions:
            merged_at = i.get('merged_at')
            if merged_at is not None and time_at < merged_at:
                continue
            
            if i['timestamp'] > time_at:
                continue

            op = i['operation']
            amt = i['amount']

            if op in ('deposited', 'transferred in', 'cashback'):
                balance += amt
            elif op in ('transferred out', 'withdrawn', 'paid'):
                balance -= amt
        
        return balance