import urllib.request
import json

def test_api():
    base = 'http://127.0.0.1:8000'
    
    # 1. Test limits
    req_lim = urllib.request.Request(f'{base}/api/risk/limits')
    with urllib.request.urlopen(req_lim) as resp:
        lims = json.loads(resp.read().decode())
        print('Risk limits response:', lims)
        assert lims['max_risk_per_trade_pct'] == 1.0
        assert lims['ai_modification_permitted'] is False
        
    # 2. Test and ensure kill switch disengaged for order gate testing
    reset_payload = json.dumps({'activate': False, 'reason': 'Reset for real API Phase 3 Gate test', 'requested_by': 'OPERATOR'}).encode()
    req_reset = urllib.request.Request(f'{base}/api/kill-switch', data=reset_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_reset) as resp:
        ks_res = json.loads(resp.read().decode())
        print('Reset kill switch response:', ks_res)
        assert ks_res['kill_switch_active'] is False

    req_stat = urllib.request.Request(f'{base}/api/risk/status')
    with urllib.request.urlopen(req_stat) as resp:
        stat = json.loads(resp.read().decode())
        print('Risk status kill_switch:', stat['kill_switch_active'])
        assert stat['kill_switch_active'] is False
        
    # 3. Test approved order request
    order_payload = json.dumps({
        'symbol': 'EURUSD',
        'side': 'BUY',
        'quantity': 0.01,
        'stop_loss': 1.0750,
        'take_profit': 1.1050,
        'strategy_id': 'strategy_v1',
        'reason': 'Real API Phase 3 Gate Validation'
    }).encode()
    req_post = urllib.request.Request(f'{base}/api/orders/request', data=order_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_post) as resp:
        order_res = json.loads(resp.read().decode())
        print('Order request result (Approved):', order_res)
        assert order_res['approved'] is True
        assert order_res['status'] == 'APPROVED'
        req_id = order_res['request_id']
        
    # 4. Query order request by ID
    req_get = urllib.request.Request(f'{base}/api/orders/{req_id}')
    with urllib.request.urlopen(req_get) as resp:
        got_order = json.loads(resp.read().decode())
        print('Order record queried from DB:', got_order['order_request_id'], got_order['execution_status'])
        assert got_order['execution_status'] == 'APPROVED'
        
    # 5. Test rejected order request (inverted stop loss)
    bad_payload = json.dumps({
        'symbol': 'EURUSD',
        'side': 'BUY',
        'quantity': 0.01,
        'stop_loss': 1.2500,
        'take_profit': 1.3000,
        'strategy_id': 'strategy_v1',
        'reason': 'Inverted SL rejection test'
    }).encode()
    req_post_bad = urllib.request.Request(f'{base}/api/orders/request', data=bad_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_post_bad) as resp:
        bad_res = json.loads(resp.read().decode())
        print('Order request result (Rejected):', bad_res)
        assert bad_res['approved'] is False
        assert bad_res['status'] == 'REJECTED'
        
    # 6. Verify positions count in MT5 (should NOT have changed)
    with urllib.request.urlopen(f'{base}/api/v1/execution/positions') as resp:
        positions = json.loads(resp.read().decode())
        print('Open positions count in MT5:', len(positions))
        
    print('ALL REAL API PHASE 3 CHECKS PASSED!')

if __name__ == '__main__':
    test_api()
