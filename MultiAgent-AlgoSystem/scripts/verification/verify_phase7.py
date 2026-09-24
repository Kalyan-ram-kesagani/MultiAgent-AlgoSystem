import sys
import os
sys.path.insert(0, os.path.abspath("."))
import requests
import json
import uuid

def verify_phase7():
    print("=== PHASE 7 AUTONOMOUS RESEARCH LOOP VERIFICATION ===")
    
    # 1. Trigger research task via API
    print("1. Triggering research task via API...")
    req_payload = {
        "symbol": "EURUSD",
        "strategy_id": "strategy_v1",
        "issue": "volatility_expansion_drift",
        "force_run": True,
    }
    r = requests.post("http://127.0.0.1:8000/api/orchestrator/investigate", json=req_payload, timeout=30)
    assert r.status_code == 200, f"Investigation failed: {r.status_code} - {r.text}"
    inv_data = r.json()
    print(f"  - Orchestrator investigation completed: task_id={inv_data.get('task_id')}")

    # 2. Verify Hypotheses in Supabase / Database
    print("2. Verifying Hypotheses in DB...")
    r_hyp = requests.get("http://127.0.0.1:8000/api/research/hypotheses", timeout=5)
    assert r_hyp.status_code == 200, f"Hypotheses listing failed: {r_hyp.status_code}"
    hyps = r_hyp.json()
    assert len(hyps) > 0, "No hypotheses found in database"
    top_hyp = hyps[0]
    print(f"  - Hypothesis persisted: ID={top_hyp['hypothesis_id']}, Title={top_hyp['title']}, Status={top_hyp['status']}")

    # 3. Verify Experiments in Supabase / Database
    print("3. Verifying Experiments in DB...")
    r_exp = requests.get("http://127.0.0.1:8000/api/research/experiments", timeout=5)
    assert r_exp.status_code == 200, f"Experiments listing failed: {r_exp.status_code}"
    experiments = r_exp.json()
    assert len(experiments) > 0, "No experiments found in database"
    exp = experiments[0]
    exp_id = exp["experiment_id"]
    print(f"  - Experiment persisted: ID={exp_id}, Status={exp['status']}, Action={exp['action']}")

    # 4. Verify Candidate Immutability
    print("4. Verifying Candidate Strategy Immutability...")
    from backend.app.ai_agent.tools.strategy import create_strategy_candidate
    cand_v = f"v1.9.{uuid.uuid4().hex[:4]}"
    first_res = json.loads(create_strategy_candidate(
        strategy_id="strategy_v1",
        version=cand_v,
        parameters={"ema_fast": 16, "ema_slow": 48},
        rules="Test rules",
        experiment_id=exp_id,
    ))
    assert first_res["status"] == "CANDIDATE"
    print(f"  - Candidate created in CANDIDATE status: version={cand_v}")

    # Overwrite attempt must fail
    second_res = json.loads(create_strategy_candidate(
        strategy_id="strategy_v1",
        version=cand_v,
        parameters={"ema_fast": 20, "ema_slow": 50},
    ))
    assert "error" in second_res, "Overwrite did not fail!"
    print(f"  - Candidate immutability verified: overwrite blocked with: {second_res['error']}")

    # 5. Human Approval Gate & Live Deployment Block
    print("5. Verifying Human Approval Gate & Live Deployment Block...")
    r_live = requests.post(
        f"http://127.0.0.1:8000/api/research/experiments/{exp_id}/review",
        json={"decision": "LIVE_ACTIVE", "operator_comment": "Attempting live activation"},
        timeout=5,
    )
    assert r_live.status_code == 403, f"Expected 403 for LIVE deployment, got: {r_live.status_code}"
    print("  - Live deployment strictly BLOCKED with HTTP 403 Forbidden.")

    r_approve = requests.post(
        f"http://127.0.0.1:8000/api/research/experiments/{exp_id}/review",
        json={"decision": "DEMO_VALIDATION", "operator_comment": "Approved for MT5 DEMO Forward Testing"},
        timeout=5,
    )
    assert r_approve.status_code == 200, f"Approval failed: {r_approve.status_code} - {r_approve.text}"
    app_data = r_approve.json()
    assert app_data["human_approved"] is True
    assert app_data["trading_mode"] == "DEMO"
    print(f"  - Human Approval Gate passed: status={app_data['decision']}, mode={app_data['trading_mode']}")

    # 6. Verify Frontend UI loads cleanly
    print("6. Verifying Frontend UI loading...")
    r_fe = requests.get("http://localhost:5173/", timeout=5)
    assert r_fe.status_code == 200
    print("  - Frontend UI is RUNNING and returned HTTP 200 OK.")

    print("\n=== ALL PHASE 7 VERIFICATION CHECKS PASSED ===")

if __name__ == "__main__":
    verify_phase7()
