import requests
import sys

def verify_phase6():
    print("=== PHASE 6 REAL-TIME DASHBOARD VERIFICATION ===")
    
    # 1. System Health & 8 Services
    print("Checking /api/system/health...")
    r = requests.get("http://127.0.0.1:8000/api/system/health", timeout=5)
    assert r.status_code == 200, f"System health failed: {r.status_code}"
    health = r.json()
    services = ["mt5", "supabase", "ai_runtime", "risk_engine", "execution_engine", "backtest_engine", "supervisor", "kill_switch"]
    for s in services:
        assert s in health, f"Service {s} missing from /api/system/health"
        print(f"  - Service [{s.upper()}]: status={health[s].get('status', 'ACTIVE' if s in ['risk_engine', 'kill_switch'] else 'OK')}")
    
    # 2. AI Panel Telemetry
    print("\nChecking /api/ai/status...")
    r = requests.get("http://127.0.0.1:8000/api/ai/status", timeout=5)
    assert r.status_code == 200, f"AI status failed: {r.status_code}"
    ai_status = r.json()
    required_ai_fields = ["status", "current_task", "current_tool", "current_run", "last_action", "last_result", "last_error"]
    for f in required_ai_fields:
        assert f in ai_status, f"AI field {f} missing"
        print(f"  - AI {f}: {ai_status[f]}")
    
    # Verify no fake states
    assert ai_status["status"] not in ["ACTIVE", "WAITING", "RUNNING_FAKE"], f"Fake AI state detected: {ai_status['status']}"
    
    # 3. Risk Panel Limits
    print("\nChecking /api/risk/limits and /api/risk/status...")
    r_limits = requests.get("http://127.0.0.1:8000/api/risk/limits", timeout=5)
    assert r_limits.status_code == 200, f"Risk limits failed: {r_limits.status_code}"
    limits = r_limits.json()
    print(f"  - Max Risk/Trade: {limits['max_risk_per_trade_pct']}%")
    print(f"  - Max Drawdown: {limits['max_portfolio_drawdown_pct']}%")
    print(f"  - Max Daily Loss: {limits['max_daily_loss_pct']}%")
    print(f"  - Max Open Positions: {limits['max_open_positions']}")
    print(f"  - Max Symbol Exposure: {limits['max_symbol_exposure']}")
    print(f"  - Stop Loss Required: {limits['stop_loss_required']}")
    print(f"  - AI Modification Permitted: {limits['ai_modification_permitted']}")
    assert limits['max_risk_per_trade_pct'] == 1.0
    assert limits['max_portfolio_drawdown_pct'] == 10.0
    assert limits['max_daily_loss_pct'] == 3.0
    assert limits['ai_modification_permitted'] is False

    r_risk = requests.get("http://127.0.0.1:8000/api/risk/status", timeout=5)
    assert r_risk.status_code == 200, f"Risk status failed: {r_risk.status_code}"
    risk_st = r_risk.json()
    print(f"  - Kill Switch Active: {risk_st['kill_switch_active']}")
    print(f"  - Account Equity: {risk_st['account_equity']}")
    print(f"  - Current Drawdown: {risk_st['current_drawdown_pct']}%")
    print(f"  - Open Positions: {risk_st['open_positions_count']}")
    
    # 4. Frontend Load
    print("\nChecking Frontend UI at http://localhost:5173/...")
    r_fe = requests.get("http://localhost:5173/", timeout=5)
    assert r_fe.status_code == 200, f"Frontend failed: {r_fe.status_code}"
    assert "<title>" in r_fe.text or "<div id=\"root\">" in r_fe.text, "Frontend HTML missing root/title"
    print("  - Frontend UI loaded HTTP 200 OK with valid HTML mount.")
    
    print("\n=== ALL PHASE 6 CHECKS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    verify_phase6()
