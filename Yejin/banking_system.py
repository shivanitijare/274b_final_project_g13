from abc import ABC


class BankingSystem(ABC):
    """
    `BankingSystem` interface.
    """
    
    def __init__(self, accounts_dic: dict):
      """
      Create accounts dictionary to store all accounts with their id and information
      
      Args:
          accounts_dic (dict): 
      """
      self.accounts: dict = {}      
      
      
      
    def create_account(self, timestamp: int, account_id: str) -> bool:
        """
        Should create a new account with the given identifier if it
        doesn't already exist.
        Returns `True` if the account was successfully created or
        `False` if an account with `account_id` already exists.
        """
        # default implementation
        if account_id in self.accounts:
            return False
        else:
          # create a new account information first (default set of balance = 0 and empty transaction)
            account_info = {'balance': 0,
                            'transactions': []}
            account_info['transactions'].append({'timestamp': timestamp,
                                                 'operation': 'created account',
                                                 'amount': 0}) #should specify type?
            
            # add new account information with key of account_id to accounts dictionary
            self.accounts[account_id] = account_info      #create a new account
            return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        """
        Should deposit the given `amount` of money to the specified
        account `account_id`.
        Returns the balance of the account after the operation has
        been processed.
        If the specified account doesn't exist, should return
        `None`.
        """
        # default implementation
        if account_id in self.accounts:
            account_info = self.accounts[account_id]
            
            account_info['transactions'].append({'timestamp': timestamp,
                                                 'operation': 'deposited',
                                                 'amount': amount})
            account_info['balance'] += amount
        else:
            return None
        return account_info['balance']

    def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        """
        Should transfer the given amount of money from account
        `source_account_id` to account `target_account_id`.
        Returns the balance of `source_account_id` if the transfer
        was successful or `None` otherwise.
          * Returns `None` if `source_account_id` or
          `target_account_id` doesn't exist.
          * Returns `None` if `source_account_id` and
          `target_account_id` are the same.
          * Returns `None` if account `source_account_id` has
          insufficient funds to perform the transfer.
        """
        # default implementation
        if source_account_id not in self.accounts or target_account_id not in self.accounts:
            return None
        if source_account_id == target_account_id: #elif or if ?
            return None
        if self.accounts[source_account_id]['balance'] < amount:
            return None
        else:
          # source account
          account_info_source = self.accounts[source_account_id]
          account_info_source['transactions'].append({'timestamp': timestamp,
                                                 'operation': 'transferred out',
                                                 'amount': amount})
          account_info_source['balance'] -= amount
          
          # target account
          account_info_target = self.accounts[target_account_id]
          account_info_target['transactions'].append({'timestamp': timestamp,
                                                 'operation': 'transferred in',
                                                 'amount': amount})
          account_info_target['balance'] += amount
          
        return account_info_source['balance']

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        """
        Should return the identifiers of the top `n` accounts with
        the highest outgoing transactions - the total amount of
        money either transferred out of or paid/withdrawn (the
        **pay** operation will be introduced in level 3) - sorted in
        descending order, or in case of a tie, sorted alphabetically
        by `account_id` in ascending order.
        The result should be a list of strings in the following
        format: `["<account_id_1>(<total_outgoing_1>)", "<account_id
        _2>(<total_outgoing_2>)", ..., "<account_id_n>(<total_outgoi
        ng_n>)"]`.
          * If less than `n` accounts exist in the system, then return
          all their identifiers (in the described format).
          * Cashback (an operation that will be introduced in level 3)
          should not be reflected in the calculations for total
          outgoing transactions.
        """
        # default implementation
        spender_sum = {}
        for account_id, account_info in self.accounts.items():
            for indiv_trans in account_info['transactions']: # indiv_trans = [ {}, {}, {}... ]
                if indiv_trans['operation'] == 'transferred out':
                    spender_sum[account_id] += indiv_trans['amount']
                #if indiv_trans['operation'] == 'paid':
                    #spender_sum[account_id] += indiv_trans['amount']
        
        # ascending order
        sorted_spender_sum = sorted(spender_sum.items(), key=lambda item: item[1])
        
        if len(sorted_spender_sum) < n:
          return sorted_spender_sum
        #if Cashback
        

        return sorted_spender_sum[:n]

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        """
        Should withdraw the given amount of money from the specified
        account.
        All withdraw transactions provide a 2% cashback - 2% of the
        withdrawn amount (rounded down to the nearest integer) will
        be refunded to the account 24 hours after the withdrawal.
        If the withdrawal is successful (i.e., the account holds
        sufficient funds to withdraw the given amount), returns a
        string with a unique identifier for the payment transaction
        in this format:
        `"payment[ordinal number of withdraws from all accounts]"` -
        e.g., `"payment1"`, `"payment2"`, etc.
        Additional conditions:
          * Returns `None` if `account_id` doesn't exist.
          * Returns `None` if `account_id` has insufficient funds to
          perform the payment.
          * **top_spenders** should now also account for the total
          amount of money withdrawn from accounts.
          * The waiting period for cashback is 24 hours, equal to
          `24 * 60 * 60 * 1000 = 86400000` milliseconds (the unit for
          timestamps).
          So, cashback will be processed at timestamp
          `timestamp + 86400000`.
          * When it's time to process cashback for a withdrawal, the
          amount must be refunded to the account before any other
          transactions are performed at the relevant timestamp.
        """
        # default implementation
        return None

    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        """
        Should return the status of the payment transaction for the
        given `payment`.
        Specifically:
          * Returns `None` if `account_id` doesn't exist.
          * Returns `None` if the given `payment` doesn't exist for
          the specified account.
          * Returns `None` if the payment transaction was for an
          account with a different identifier from `account_id`.
          * Returns a string representing the payment status:
          `"IN_PROGRESS"` or `"CASHBACK_RECEIVED"`.
        """
        # default implementation
        return None

    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool:
        """
        Should merge `account_id_2` into the `account_id_1`.
        Returns `True` if accounts were successfully merged, or
        `False` otherwise.
        Specifically:
          * Returns `False` if `account_id_1` is equal to
          `account_id_2`.
          * Returns `False` if `account_id_1` or `account_id_2`
          doesn't exist.
          * All pending cashback refunds for `account_id_2` should
          still be processed, but refunded to `account_id_1` instead.
          * After the merge, it must be possible to check the status
          of payment transactions for `account_id_2` with payment
          identifiers by replacing `account_id_2` with `account_id_1`.
          * The balance of `account_id_2` should be added to the
          balance for `account_id_1`.
          * `top_spenders` operations should recognize merged accounts
          - the total outgoing transactions for merged accounts should
          be the sum of all money transferred and/or withdrawn in both
          accounts.
          * `account_id_2` should be removed from the system after the
          merge.
        """
        # default implementation
        return False

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        """
        Should return the total amount of money in the account
        `account_id` at the given timestamp `time_at`.
        If the specified account did not exist at a given time
        `time_at`, returns `None`.
          * If queries have been processed at timestamp `time_at`,
          `get_balance` must reflect the account balance **after** the
          query has been processed.
          * If the account was merged into another account, the merged
          account should inherit its balance history.
        """
        # default implementation
        return None
