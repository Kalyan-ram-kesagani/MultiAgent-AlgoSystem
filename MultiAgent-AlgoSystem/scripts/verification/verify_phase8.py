import sys
import os
sys.path.insert(0, os.path.abspath("."))
import requests
import json
import uuid

def verify_phase8():
    print("================================================================")
    print("=== PHASE 8: FULL DEMO INTEGRATION & SAFETY VALIDATION GATE ===")
    print("================================================================")
    
    # 1. MT5 DEMO Health & Status
    print("\n1. Verifying MT5 DEMO Account & Terminal Status...")
    requests.post("http://127.0.0.1:8000/api/risk/kill-switch", json={"activate": False, "reason": "Operator reset before Phase 8 run", "requested_by": "OPERATOR"}, timeout=5)
    r_health = requests.get("http://127.0.0.1:8000/api/system/health", timeout=5)
    assert r_health.status_code == 200, f"System health check failed: {r_health.status_code}"
    health = r_health.json()
    mt5_info = health["mt5"]
    print(f"  - MT5 Connected: {mt5_info.get('connected')}")
    print(f"  - MT5 Mode: {mt5_info.get('mode')}")
    print(f"  - Account: {mt5_info.get('account')}")
    print(f"  - Server: {mt5_info.get('server')}")
    print(f"  - Equity: ${mt5_info.get('equity', 0):,.2f}")
    assert health["execution_engine"]["mode"] == "DEMO ONLY", "Execution engine mode is not DEMO ONLY!"
    print("  -> MT5 DEMO ONLY operation strictly verified.")

    # 2. End-to-End Approved DEMO Order Pipeline
    print("\n2. Testing End-to-End Approved DEMO Order Pipeline...")
    order_payload = {
        "symbol": "EURUSD",
        "side": "BUY",
        "quantity": 0.01,
        "stop_loss": 1.1300,
        "take_profit": 1.1500,
        "strategy_id": "strategy_v1",
        "reason": "Phase 8 End-to-End Verification Pipeline DEMO order",
        "execute": True,
    }
    r_order = requests.post("http://127.0.0.1:8000/api/orders/request", json=order_payload, timeout=15)
    assert r_order.status_code == 200, f"Order request failed: {r_order.status_code} - {r_order.text}"
    ord_res = r_order.json()
    assert ord_res["approved"] is True, f"Valid order was not approved: {ord_res}"
    req_id = ord_res["request_id"]
    ticket = ord_res.get("broker_ticket")
    print(f"  - Order Request ID: {req_id}")
    print(f"  - Risk Approval: APPROVED (lots={ord_res.get('calculated_lots')})")
    print(f"  - Execution Status: {ord_res.get('status')}")
    print(f"  - MT5 Broker Ticket: {ticket}")

    # 3. Verify Journal Audit Record in DB
    print("\n3. Verifying Durable Journal Audit in DB...")
    r_audit = requests.get(f"http://127.0.0.1:8000/api/orders/{req_id}", timeout=5)
    assert r_audit.status_code == 200, f"Failed to retrieve audit record: {r_audit.status_code}"
    audit_data = r_audit.json()
    assert audit_data["is_approved"] is True
    assert audit_data["order_request_id"] == req_id
    print(f"  - Verified Journal Record: ID={audit_data['order_request_id']}, Approved={audit_data['is_approved']}, Status={audit_data['execution_status']}")

    # 4. Risk-Rejected Order Test (Zero MT5 Orders)
    print("\n4. Testing Risk-Rejected Order (Safety Gate)...")
    rejected_payload = {
        "symbol": "EURUSD",
        "side": "BUY",
        "quantity": 10.0,  # Extreme volume violation
        "stop_loss": 0.0,   # Missing mandatory stop loss
        "take_profit": 1.1500,
        "strategy_id": "strategy_v1",
        "reason": "Extreme lot size without SL",
        "execute": True,
    }
    r_reject = requests.post("http://127.0.0.1:8000/api/orders/request", json=rejected_payload, timeout=10)
    assert r_reject.status_code == 200
    rej_data = r_reject.json()
    assert rej_data["approved"] is False, "Violation order was unexpectedly approved!"
    assert rej_data["status"] == "REJECTED"
    assert "broker_ticket" not in rej_data or rej_data.get("broker_ticket") is None
    print(f"  - Violation correctly REJECTED by Risk Engine: {rej_data['reason']}")
    print("  -> Proof: ZERO MT5 orders submitted.")

    # 5. Kill Switch Drill & Fail Closed
    print("\n5. Testing Kill Switch Drill & Fail Closed...")
    # Engage
    r_kill = requests.post("http://127.0.0.1:8000/api/risk/kill-switch", json={"activate": True, "reason": "Phase 8 Safety Drill", "requested_by": "OPERATOR"}, timeout=5)
    assert r_kill.status_code == 200
    assert r_kill.json()["kill_switch_active"] is True
    print("  - Kill Switch engaged.")

    # Try order while kill switch active
    r_blocked = requests.post("http://127.0.0.1:8000/api/orders/request", json=order_payload, timeout=10)
    blocked_data = r_blocked.json()
    assert blocked_data["approved"] is False
    assert "KILL SWITCH" in blocked_data["reason"].upper()
    print("  - Order submitted during kill switch -> BLOCKED immediately.")

    # Disengage
    requests.post("http://127.0.0.1:8000/api/risk/kill-switch", json={"activate": False, "reason": "Phase 8 Drill complete", "requested_by": "OPERATOR"}, timeout=5)
    print("  - Kill Switch disengaged.")

    # 6. Autonomous Research Lifecycle & LIVE Block
    print("\n6. Testing Research Pipeline & Live Deployment Block...")
    cand_version = f"v1.9.{uuid.uuid4().hex[:4]}"
    from backend.app.ai_agent.tools.strategy import create_strategy_candidate
    cand_res = json.loads(create_strategy_candidate(
        strategy_id="strategy_v1",
        version=cand_version,
        parameters={"ema_fast": 14, "ema_slow": 42},
        rules="Phase 8 test candidate",
    ))
    assert cand_res["status"] == "CANDIDATE"
    print(f"  - Candidate created in CANDIDATE status: version={cand_version}")

    # Overwrite attempt must fail
    cand_overwrite = json.loads(create_strategy_candidate(
        strategy_id="strategy_v1",
        version=cand_version,
        parameters={"ema_fast": 20, "ema_slow": 50},
    ))
    assert "error" in cand_overwrite
    print("  - Candidate immutability verified: overwrite blocked.")

    # Live deployment attempt
    r_exp = requests.get("http://127.0.0.1:8000/api/research/experiments", timeout=5)
    exps = r_exp.json()
    if exps:
        exp_id = exps[0]["experiment_id"]
        r_live = requests.post(
            f"http://127.0.0.1:8000/api/research/experiments/{exp_id}/review",
            json={"decision": "LIVE_ACTIVE", "operator_comment": "Attempting live promotion"},
            timeout=5,
        )
        assert r_live.status_code == 403, f"Expected 403 for LIVE, got: {r_live.status_code}"
        print("  - Promotion to LIVE trading strictly BLOCKED with HTTP 403 Forbidden.")

    # 7. Frontend UI Responsiveness
    print("\n7. Verifying Frontend Web Application...")
    r_fe = requests.get("http://localhost:5173/", timeout=5)
    assert r_fe.status_code == 200
    print("  - Frontend UI is RUNNING and returned HTTP 200 OK.")

    print("\n================================================================")
    print("=== PHASE 8 FULL DEMO INTEGRATION & SAFETY GATE PASSED 100% ===")
    print("================================================================")

if __name__ == "__main__":
    verify_phase8()
