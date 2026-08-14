import sys
sys.path.insert(0, '.')
from agents.forensic_cfo import _has_individual_alert

r = {
    'metric': 'staff_courtesy_ratio',
    'status': 'ok',
    'context': 'by_responsable: {"M-03": {"rate_pct": "9.63"}}'
}
print(_has_individual_alert(r))