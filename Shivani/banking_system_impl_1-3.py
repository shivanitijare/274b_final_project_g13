from banking_system import BankingSystem
from typing import Dict

#for timestamp purposes
milliseconds_to_day = 24 * 60 * 60 * 1000

class BankingSystemImpl(BankingSystem):
     """
    Level 1 implementation:
      - create_account
      - deposit
      - transfer
    Notes:
      * Timestamps are accepted but not used for Level 1 logic.
      * Balances are stored as non-negative integers.
    """
     def __init__(self) -> None:
        self._balances: Dict[str, int] = {} #current balance of the account (maps account_id)
        self._outgoing_total: Dict[str, int] = {} #total amount account has sent out (maps account_id)

        # Level 3
        self._next_payment_id: int = 0               # global counter for "paymentX"
        self._payments: Dict[str, Dict] = {}         # payment_id -> info dict
        # cashback_timestamp -> list of payment_ids whose cashback should be processed then
        self._cashback_schedule: Dict[int, list[str]] = {}
        self._last_processed_ts: int = 0             # last timestamp up to which cashback was processed
    
    #helper method
     def _process_cashbacks(self, timestamp: int) -> None:
         """
         Apply all cashbacks whose scheduled time is <= current timestamp,
         ensuring they are applied before any work done at this timestamp.
        """
         if not self._cashback_schedule:
             self._last_processed_ts = max(self._last_processed_ts, timestamp)
             return
         due_times = [ts for ts in self._cashback_schedule.keys()
                 if self._last_processed_ts < ts <= timestamp]
         if not due_times:
             self._last_processed_ts = max(self._last_processed_ts, timestamp)
             return
         for ts in sorted(due_times):
            for payment_id in self._cashback_schedule[ts]:
                info = self._payments.get(payment_id)
                if info is None or info["status"] != "IN_PROGRESS":
                    continue
                acc_id = info["account_id"]
                cashback = info["cashback"]
                    # refund cashback first
                self._balances[acc_id] += cashback
                info["status"] = "CASHBACK_RECEIVED"
            del self._cashback_schedule[ts]
         self._last_processed_ts = max(self._last_processed_ts, timestamp)
   
   # time complexity of O(1)
     def create_account(self, timestamp: int, account_id: str) -> bool:
        #level 3
        self._process_cashbacks(timestamp)
        
        if account_id in self._balances:
            return False
        self._balances[account_id] = 0
        self._outgoing_total[account_id] = 0
        return True

    # time complexity of O(1)
     def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None: 
        #level 3
        self._process_cashbacks(timestamp)
        
        balance = self._balances.get(account_id) #looks up the balance in the account
        if balance is None: #when account does not exist
            return None
        # Assuming non-negative amounts
        balance += amount
        self._balances[account_id] = balance
        return balance

    # time complexity of O(1)
     def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        #level 3
        self._process_cashbacks(timestamp)
       
       #checking if the accounts exisit, and making sure they are not the same account
        if (
            source_account_id not in self._balances
            or target_account_id not in self._balances
            or source_account_id == target_account_id
        ): 
            return None
        #sournce account does not have sufficient funds, the transfer will not happen
        if self._balances[source_account_id] < amount:
            return None

        #performing the transfer (subtract from source and add to target)
        self._balances[source_account_id] -= amount
        self._balances[target_account_id] += amount

        # added this for Level 2 to help with top_spenders function
        self._outgoing_total[source_account_id] += amount
        
        return self._balances[source_account_id]

    # Level 2
     def top_spenders(self, timestamp: int, n: int) -> list[str]:
        #level 3
        self._process_cashbacks(timestamp)
        
        #list of tuples to have acount ID and the total outgoing ammount
        top_accounts = []
        for acc_id in self._balances.keys():
            total_outgoing = self._outgoing_total.get(acc_id, 0) #get 0 if account id is not in outgoing_total
            tuple_pair = (acc_id, total_outgoing)
            top_accounts.append(tuple_pair)

        #sorts the higher outgoing total first
        top_accounts.sort(key=lambda item: (-item[1], item[0]))

        #slices to keep top n entries
        top_accounts = top_accounts[:n]

        return [f"{acc_id}({total})" for acc_id, total in top_accounts]
    
    #Level 3
     def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        self._process_cashbacks(timestamp)

        if account_id not in self._balances:
            return None
        if self._balances[account_id] < amount:
            return None

        # withdraw now
        self._balances[account_id] -= amount
        # payments also count as outgoing
        self._outgoing_total[account_id] += amount

        # create payment id
        self._next_payment_id += 1
        payment_id = f"payment{self._next_payment_id}"

        # compute cashback (2% rounded down)
        cashback = (amount * 2) // 100
        cashback_ts = timestamp + milliseconds_to_day

        # record payment info
        self._payments[payment_id] = {
            "account_id": account_id,
            "amount": amount,
            "cashback": cashback,
            "cashback_ts": cashback_ts,
            "status": "IN_PROGRESS",
        }

        # schedule cashback
        self._cashback_schedule.setdefault(cashback_ts, []).append(payment_id)

        return payment_id

     def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        self._process_cashbacks(timestamp)

        if account_id not in self._balances:
            return None

        info = self._payments.get(payment)
        if info is None:
            return None
        if info["account_id"] != account_id:
            return None

        return info["status"]