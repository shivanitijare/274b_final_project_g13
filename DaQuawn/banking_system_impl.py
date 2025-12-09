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
        │             ├── "amount": int     
        |             ├── "payment": str    # only in payback transactions, stores the unique payment number (num_payment) generated in pay()
        │             └── "deposited": bool     # only in payback transactions, tracks if cashback has deposited or not
        '''

        self.MILLISECONDS_IN_1_DAY = 86400000 # number of seconds in 1 day (24 hours)

        # store merged-away accounts for historical get_balance()
        # key: account_id -> value: {"account_info": ..., "merged_at": timestamp}
        self.archived_accounts: dict = {}

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
                        'transactions': [],
                        'created_at': timestamp
                        }
        
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
                # check if cashback has been deposited, if not, deposit it
                if transaction['deposited'] is True:
                    return 'CASHBACK_RECEIVED'
                else:
                    return 'IN_PROGRESS'
    
    def merge_accounts(self, 
                       timestamp, 
                       account_id_1, 
                       account_id_2) -> bool:
        
        self._process_cashbacks(timestamp)
        import copy

        # checking if the accounts are the same. 
        if account_id_1 == account_id_2:
            return False
        
        # checking if both accounts exist.
        if account_id_1 not in self.whole_accounts or account_id_2 not in self.whole_accounts:
            return False
        
        acct1 = self.whole_accounts[account_id_1]
        acct2 = self.whole_accounts[account_id_2]

        # Archive donor for historical get_balance()
        archived_info = copy.deepcopy(acct2)
        self.archived_accounts[account_id_2] = {
                                                    "account_info": archived_info,
                                                    "merged_at": timestamp,
                                                }

        # Copy acct2's transactions into acct1, tagging them
        merged_transactions = []
        for transaction in acct2["transactions"]:
            new_tx = transaction.copy()
            new_tx["merged_from"] = account_id_2
            new_tx["merged_at"] = timestamp
            merged_transactions.append(new_tx)
        
        acct1['transactions'].extend(merged_transactions)

        # adding acct2 balance to acct1 balance
        acct1['balance'] += acct2['balance']

        # dropping acct2 from whole_accts
        self.whole_accounts.pop(account_id_2)

        # sorting acct1 by timestamp
        acct1['transactions'].sort(key=lambda d: d['timestamp'])

        return True
    
    def get_balance(self, 
                    timestamp, 
                    account_id, 
                    time_at)-> int |None:
        
        self._process_cashbacks(time_at)

        # Determine whether this ID refers to an active and/or archived account
        active_info = self.whole_accounts.get(account_id)
        archived_bundle = self.archived_accounts.get(account_id)

        account_info = None
        merged_at = None
        is_archived = False
        
        # checking if account exists
        if active_info is None and archived_bundle is None:
            return None

        if active_info is not None and archived_bundle is not None:
            # ID was reused: choose which incarnation to use based on time_at
            active_created_at = active_info.get("created_at", -1)
            archived_merged_at = archived_bundle["merged_at"]

            if time_at < active_created_at:
                # Before the new account was (re)created: use old (archived) account
                account_info = archived_bundle["account_info"]
                merged_at = archived_merged_at
                is_archived = True
            else:
                # After new account exists: use active one
                account_info = active_info
        elif active_info is not None:
            account_info = active_info
        else:
            # Only archived version exists
            account_info = archived_bundle["account_info"]
            merged_at = archived_bundle["merged_at"]
            is_archived = True

        # If this is an archived (merged-away) account and time_at is at or after merge,
        # the account no longer exists
        if is_archived and time_at >= merged_at:
            return None

        # Check if account had been created by time_at
        created_at = account_info.get("created_at", None)
        if created_at is not None and created_at > time_at:
            return None

        balance_at_time = 0
        add_to_balance = ["cashback", "deposited", "transferred in"]

        for transaction in account_info["transactions"]:
            tx_time = transaction["timestamp"]
            if tx_time > time_at:
                continue

            # If this transaction came from a merge, it should *only* count
            # starting at its merged_at time for the receiving account.
            tx_merged_at = transaction.get("merged_at")
            if tx_merged_at is not None and time_at < tx_merged_at:
                # At this time, it still belonged to the original account
                continue

            operation = transaction['operation']
            amount = transaction['amount']

            if operation in add_to_balance:
                balance_at_time += amount
            elif operation == 'transferred out':
                balance_at_time -= amount
            elif operation.startswith('payment'):
                balance_at_time -= amount
        
        return balance_at_time
