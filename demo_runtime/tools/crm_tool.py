from __future__ import annotations
from typing import Any, Dict

ORDERS = {
    "ORD-1001": {"customer": "Ada", "status": "shipped", "amount": 128.5},
    "ORD-1002": {"customer": "Grace", "status": "processing", "amount": 89.0},
}

def lookup(arguments: Dict[str, Any]) -> Dict[str, Any]:
    order_id = arguments.get("order_id", "ORD-1001")
    return {"tool": "crm.lookup", "record": ORDERS.get(order_id, {"status": "not_found"})}

def refund(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return {"tool": "crm.refund", "status": "simulated_refund_created", "amount": arguments.get("amount")}
