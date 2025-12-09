from banking_system import BankingSystem

class BankingSystemImpl(BankingSystem):
    def __init__(self) -> None:
        # Key: account_id
        # Value: dict { 
        #    "balance": int, 
        #    "transactions": list, 
        #    "creation_time": int,
        #    "merged_at": int (optional, if present, account is merged)
        # }
        self.accounts = {}
        self.payment_counter = 1
        self.MILLISECONDS_IN_1_DAY = 86400000

    def _process_cashbacks(self, timestamp: int) -> None:
        for acc in self.accounts.values():
            # Even if merged, the prompt implies cashback refunds for merged accounts 
            # should be processed but refunded to the survivor.
            # However, my merge logic moves transactions to the survivor, 
            # so the survivor handles the cashback processing naturally.
            # We only need to process active accounts here for unmerged scenarios.
            if "merged_at" in acc:
                continue
                
            for tr in acc["transactions"]:
                if (tr["operation"] == "cashback" 
                    and tr["timestamp"] <= timestamp 
                    and not tr["deposited"]):
                    
                    acc["balance"] += tr["amount"]
                    tr["deposited"] = True

    def create_account(self, timestamp: int, account_id: str) -> bool:
        if account_id in self.accounts:
            # If account exists and is ACTIVE, fail.
            if "merged_at" not in self.accounts[account_id]:
                return False
            # If account exists but was MERGED (soft deleted), 
            # we overwrite it (effectively creating a new account with the same ID).
        
        self.accounts[account_id] = {
            "balance": 0,
            "transactions": [],
            "creation_time": timestamp
        }
        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)
        
        if account_id not in self.accounts:
            return None
        
        acc = self.accounts[account_id]
        if "merged_at" in acc:
            return None
            
        acc["balance"] += amount
        acc["transactions"].append({
            "timestamp": timestamp,
            "operation": "deposit",
            "amount": amount
        })
        return acc["balance"]

    def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)
        
        if (source_account_id not in self.accounts or 
            target_account_id not in self.accounts or 
            source_account_id == target_account_id):
            return None
            
        src = self.accounts[source_account_id]
        tgt = self.accounts[target_account_id]
        
        # Check if either is merged
        if "merged_at" in src or "merged_at" in tgt:
            return None
        
        if src["balance"] < amount:
            return None
        
        src["balance"] -= amount
        tgt["balance"] += amount
        
        src["transactions"].append({
            "timestamp": timestamp,
            "operation": "transfer_out",
            "amount": amount,
            "target": target_account_id
        })
        tgt["transactions"].append({
            "timestamp": timestamp,
            "operation": "transfer_in",
            "amount": amount,
            "source": source_account_id
        })
        
        return src["balance"]

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        self._process_cashbacks(timestamp)
        
        spenders = []
        for acc_id, info in self.accounts.items():
            # Skip merged accounts
            if "merged_at" in info:
                continue
                
            total_outgoing = 0
            for tr in info["transactions"]:
                op = tr["operation"]
                if op == "transfer_out" or op.startswith("payment"):
                    total_outgoing += tr["amount"]
            
            spenders.append((-total_outgoing, acc_id))
            
        spenders.sort()
        
        result = []
        for i in range(min(n, len(spenders))):
            amt = -spenders[i][0]
            acc = spenders[i][1]
            result.append(f"{acc}({amt})")
            
        return result

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        self._process_cashbacks(timestamp)
        
        if account_id not in self.accounts:
            return None
            
        acc = self.accounts[account_id]
        if "merged_at" in acc:
            return None
            
        if acc["balance"] < amount:
            return None
        
        payment_id = f"payment{self.payment_counter}"
        self.payment_counter += 1
        
        acc["balance"] -= amount
        
        acc["transactions"].append({
            "timestamp": timestamp,
            "operation": payment_id,
            "amount": amount
        })
        
        cashback_amt = int(amount * 0.02)
        acc["transactions"].append({
            "timestamp": timestamp + self.MILLISECONDS_IN_1_DAY,
            "operation": "cashback",
            "amount": cashback_amt,
            "related_payment": payment_id,
            "deposited": False
        })
        
        return payment_id

    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        self._process_cashbacks(timestamp)
        
        if account_id not in self.accounts:
            return None
            
        acc = self.accounts[account_id]
        if "merged_at" in acc:
            return None
        
        # Check transaction history
        payment_found = False
        cashback_deposited = False
        
        for tr in acc["transactions"]:
            if tr["operation"] == payment:
                payment_found = True
            if (tr["operation"] == "cashback" and 
                tr.get("related_payment") == payment and 
                tr["deposited"]):
                cashback_deposited = True
                
        if not payment_found:
            return None
            
        return "CASHBACK_RECEIVED" if cashback_deposited else "IN_PROGRESS"

    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool:
        self._process_cashbacks(timestamp)
        
        if account_id_1 == account_id_2:
            return False
        
        if account_id_1 not in self.accounts or account_id_2 not in self.accounts:
            return False
            
        acc1 = self.accounts[account_id_1]
        acc2 = self.accounts[account_id_2]
        
        # Cannot merge if either is already merged
        if "merged_at" in acc1 or "merged_at" in acc2:
            return False
        
        # 1. Transfer Balance
        acc1["balance"] += acc2["balance"]
        
        # 2. Transfer Transactions (Copy and Tag)
        # We COPY them so acc2 retains its original history for historical queries,
        # but acc1 gets the data for future queries.
        for tr in acc2["transactions"]:
            # Shallow copy is enough as dicts inside are simple
            new_tr = tr.copy()
            new_tr["merged_from"] = account_id_2
            new_tr["merged_at"] = timestamp
            acc1["transactions"].append(new_tr)
            
        # 3. Soft Delete Account 2
        acc2["merged_at"] = timestamp
        
        return True

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        self._process_cashbacks(timestamp)
        
        if account_id not in self.accounts:
            return None
            
        acc = self.accounts[account_id]
        
        # 1. Check if account existed at time_at
        if acc["creation_time"] > time_at:
            return None
            
        # 2. Check merge status relative to time_at
        # If the account is merged, AND the query is for a time AFTER the merge,
        # then the account "doesn't exist" (it's gone).
        if "merged_at" in acc:
            if time_at >= acc["merged_at"]:
                return None
        
        # 3. Calculate Balance
        balance = 0
        for tr in acc["transactions"]:
            # Skip future transactions
            if tr["timestamp"] > time_at:
                continue
                
            # Filter Merged Transactions
            # If this transaction came from a merge, we only count it 
            # if the merge happened BEFORE (or at) the query time.
            if "merged_at" in tr:
                if tr["merged_at"] > time_at:
                    continue
            
            op = tr["operation"]
            amt = tr["amount"]
            
            if op == "deposit":
                balance += amt
            elif op == "transfer_in":
                balance += amt
            elif op == "transfer_out":
                balance -= amt
            elif op.startswith("payment"):
                balance -= amt
            elif op == "cashback":
                balance += amt
                
        return balance