import urllib.request
import json
import time

def test_phase4_live_execution():
    base = 'http://127.0.0.1:8000'
    
    # 1. Reset kill switch
    reset_payload = json.dumps({'activate': False, 'reason': 'Reset for Phase 4 live gate test', 'requested_by': 'OPERATOR'}).encode()
    req_reset = urllib.request.Request(f'{base}/api/kill-switch', data=reset_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_reset) as resp:
        ks = json.loads(resp.read().decode())
        print('Kill switch active:', ks['kill_switch_active'])
        assert ks['kill_switch_active'] is False

    # Close any existing open positions so test starts clean
    with urllib.request.urlopen(f'{base}/api/v1/execution/positions') as pos_resp:
        existing_pos = json.loads(pos_resp.read().decode())
        for p in existing_pos:
            t = p['ticket']
            try:
                urllib.request.urlopen(urllib.request.Request(f'{base}/api/v1/execution/positions/{t}/close', data=b'', headers={'Content-Type': 'application/json'}))
                print(f'Cleaned up pre-existing position {t}')
            except Exception as e:
                print(f'Notice closing {t}: {e}')

    # 2. Fetch live price from broker
    with urllib.request.urlopen(f'{base}/api/v1/execution/price/EURUSD') as p_resp:
        live_p = json.loads(p_resp.read().decode())
        ask = live_p['ask']
        valid_sl = round(ask - 0.0050, 5)
        valid_tp = round(ask + 0.0050, 5)
        print(f'Live EURUSD ask={ask}, SL={valid_sl}, TP={valid_tp}')

    # Test approved order request -> Real DEMO execution
    order_payload = json.dumps({
        'symbol': 'EURUSD',
        'side': 'BUY',
        'quantity': 0.01,
        'stop_loss': valid_sl,
        'take_profit': valid_tp,
        'strategy_id': 'strategy_v1',
        'reason': 'Real DEMO Phase 4 Gate Validation',
        'execute': True
    }).encode()
    req_post = urllib.request.Request(f'{base}/api/orders/request', data=order_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_post) as resp:
        order_res = json.loads(resp.read().decode())
        print('Phase 4 Approved DEMO Execution Result:', order_res)
        assert order_res['approved'] is True
        assert order_res['status'] == 'EXECUTED'
        assert 'execution_id' in order_res
        assert order_res['execution_id'].startswith('EXEC-')
        assert order_res['broker_ticket'] is not None
        req_id = order_res['request_id']
        exec_id = order_res['execution_id']
        ticket = order_res['broker_ticket']

    # 3. Query order by ID from API / Supabase DB
    req_get = urllib.request.Request(f'{base}/api/orders/{req_id}')
    with urllib.request.urlopen(req_get) as resp:
        got = json.loads(resp.read().decode())
        print('Queried Order Request Record:', got['order_request_id'], got['execution_status'], got['execution_id'], got['broker_ticket'])
        assert got['execution_status'] == 'EXECUTED'
        assert got['execution_id'] == exec_id
        assert got['broker_ticket'] == ticket

    # 4. Duplicate Order Protection test
    req_dup = urllib.request.Request(f'{base}/api/orders/request', data=order_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_dup) as resp:
        dup_res = json.loads(resp.read().decode())
        print('Duplicate order attempt result:', dup_res)
        assert dup_res['approved'] is False
        assert dup_res['status'] == 'REJECTED'
        assert 'duplicate' in dup_res['reason'].lower()

    # 5. Risk rejection test (Inverted SL) -> ZERO MT5 orders
    bad_payload = json.dumps({
        'symbol': 'EURUSD',
        'side': 'BUY',
        'quantity': 0.01,
        'stop_loss': 1.2500,
        'take_profit': 1.3000,
        'strategy_id': 'strategy_v1',
        'reason': 'Phase 4 Risk Rejection Inverted SL',
        'execute': True
    }).encode()
    req_bad = urllib.request.Request(f'{base}/api/orders/request', data=bad_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_bad) as resp:
        bad_res = json.loads(resp.read().decode())
        print('Risk rejection result:', bad_res)
        assert bad_res['approved'] is False
        assert bad_res['status'] == 'REJECTED'

    # 6. Test MT5 Reconciliation Endpoint
    req_rec = urllib.request.Request(f'{base}/api/v1/execution/reconcile')
    with urllib.request.urlopen(req_rec) as resp:
        rec_res = json.loads(resp.read().decode())
        print('MT5 Positions Reconciliation Result:', rec_res)
        assert rec_res.get('status') == 'IN_SYNC'
        assert rec_res.get('broker_positions_count') >= 1

    # 7. Close position to keep demo account clean
    req_close = urllib.request.Request(f'{base}/api/v1/execution/positions/{ticket}/close', data=b'', headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_close) as resp:
        close_res = json.loads(resp.read().decode())
        print('Closed position ticket result:', close_res)
        assert close_res.get('success') is True

    print('ALL REAL DEMO PHASE 4 EXECUTION GATE CHECKS PASSED!')

if __name__ == '__main__':
    test_phase4_live_execution()
