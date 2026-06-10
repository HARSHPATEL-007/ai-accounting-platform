from typing import Dict, Any

class ExecutionGuard:
    """Prevent AI from autonomously executing sensitive actions."""

    BLOCKED_ACTIONS = [
        "file tax return", "submit gst", "file gstr", "submit itr",
        "execute transfer", "initiate payment", "send money", "wire transfer",
        "modify ledger", "delete entry", "update books", "reverse transaction",
        "send email to client", "notify customer", "dispatch notice",
        "approve loan", "sign document", "digital signature"
    ]

    def check(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        for action in self.BLOCKED_ACTIONS:
            if action in query_lower:
                return {
                    "allowed": False,
                    "reason": f"Autonomous action '{action}' requires biometric or cryptographic approval from an authorized user."
                }
        return {"allowed": True, "reason": "No blocked execution actions detected"}
