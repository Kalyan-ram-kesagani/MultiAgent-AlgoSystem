"""Live Verification Gate for Phase 5 Background Supervisor & Autonomous Runtime."""
import urllib.request
import json
import time

def verify_phase5_live():
    base = "http://127.0.0.1:8000"

    print("--- 1. Verify Supervisor Status & Heartbeat ---")
    req = urllib.request.Request(f"{base}/api/supervisor/status")
    with urllib.request.urlopen(req) as resp:
        status = json.loads(resp.read().decode())
        print("Supervisor Status:", status)
        assert status["running"] is True, "Supervisor should be running"
        assert status["last_heartbeat"] is not None, "Heartbeat timestamp must be present"
        assert status["mt5_connected"] is True, "MT5 must be connected"
        assert status["db_healthy"] is True, "Database must be healthy"
        assert status["ai_runtime_state"] in [
            "IDLE", "THINKING", "TOOL_CALL", "RESEARCHING",
            "BACKTESTING", "RISK_CHECK", "EXECUTING", "WAITING_APPROVAL", "ERROR", "STOPPED"
        ], f"Invalid AI state: {status['ai_runtime_state']}"

    print("--- 2. Reset Kill Switch & Clean Slate ---")
    reset_payload = json.dumps({'activate': False, 'reason': 'Phase 5 live verification', 'requested_by': 'OPERATOR'}).encode()
    req_reset = urllib.request.Request(f'{base}/api/kill-switch', data=reset_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_reset) as resp:
        ks = json.loads(resp.read().decode())
        assert ks['kill_switch_active'] is False

    with urllib.request.urlopen(f'{base}/api/v1/execution/positions') as pos_resp:
        existing = json.loads(pos_resp.read().decode())
        for p in existing:
            try:
                urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/execution/positions/{p['ticket']}/close", data=b'', headers={'Content-Type': 'application/json'}))
                print(f"Cleaned up pre-existing position #{p['ticket']}")
            except Exception:
                pass
    time.sleep(5)  # Let supervisor sync clean slate

    print("--- 3. Trigger Real Trade Event on MT5 DEMO ---")
    with urllib.request.urlopen(f'{base}/api/v1/execution/price/EURUSD') as p_resp:
        live_p = json.loads(p_resp.read().decode())
        ask = live_p['ask']
        valid_sl = round(ask - 0.0050, 5)
        valid_tp = round(ask + 0.0050, 5)

    order_payload = json.dumps({
        'symbol': 'EURUSD',
        'side': 'BUY',
        'quantity': 0.01,
        'stop_loss': valid_sl,
        'take_profit': valid_tp,
        'strategy_id': 'strategy_v1',
        'reason': 'Phase 5 Live Trade Detection Test',
        'execute': True
    }).encode()
    req_order = urllib.request.Request(f'{base}/api/orders/request', data=order_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_order) as resp:
        order_res = json.loads(resp.read().decode())
        print("Placed Order:", order_res)
        assert order_res["approved"] is True
        ticket = order_res.get("broker_ticket")
        assert ticket is not None

    print(f"Waiting 3 seconds for supervisor to detect trade #{ticket}...")
    time.sleep(3)

    # Check supervisor detected trade
    with urllib.request.urlopen(f"{base}/api/supervisor/status") as resp:
        st_after_trade = json.loads(resp.read().decode())
        print("Supervisor status with open position:", st_after_trade)
        assert st_after_trade["open_positions_count"] >= 1
        assert st_after_trade["events_detected_count"] >= 1

    print("--- 4. Close Position & Verify Closed Trade Detection & Reconciliation ---")
    req_close = urllib.request.Request(f'{base}/api/v1/execution/positions/{ticket}/close', data=b'', headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_close) as resp:
        close_res = json.loads(resp.read().decode())
        print("Closed Position:", close_res)
        assert close_res.get("success") is True

    print("Waiting 5 seconds for supervisor loop to detect closure and reconcile...")
    time.sleep(5)

    with urllib.request.urlopen(f"{base}/api/supervisor/status") as resp:
        st_after_close = json.loads(resp.read().decode())
        print("Supervisor status after closure & reconciliation:", st_after_close)
        assert st_after_close["open_positions_count"] == 0
        assert st_after_close["events_detected_count"] >= 2

    # Verify reconciliation endpoint confirms IN_SYNC
    with urllib.request.urlopen(f"{base}/api/v1/execution/reconcile") as resp:
        rec = json.loads(resp.read().decode())
        print("Broker positions reconciliation status:", rec)
        assert rec["status"] == "IN_SYNC"

    print("ALL PHASE 5 LIVE SUPERVISOR & AUTONOMOUS RUNTIME CHECKS PASSED!")

if __name__ == "__main__":
    verify_phase5_live()
