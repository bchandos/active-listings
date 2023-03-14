import json
import os
from csv import DictReader

import requests
from bottle import default_app, hook, request, response, route, run, template, static_file

ENV = os.environ.get('ACTIVE_LISTINGS_ENV', 'development')

BASE_URL = '/active-listings' if ENV == 'production' else ''

DATA_URL = 'https://econdata.s3-us-west-2.amazonaws.com/Reports/Core/RDC_Inventory_Core_Metrics_Metro_History.csv'
DATA = []

def load_data():
    data_path = f'{os.path.curdir}/data/RDC_Inventory_Core_Metrics_Metro_History.csv'
    if not os.path.exists(data_path):
        r = requests.get(DATA_URL)
        if r.ok:
            with open(data_path, 'w', encoding="utf-8") as f:
                f.write(r.text)
        else:
            print('Could not download data')
            raise Exception

    with open(data_path, newline='', encoding="utf-8") as csvfile:
        global DATA
        reader = DictReader(csvfile)
        for row in reader:
            DATA.append(row)

def get_markets(*filters, state=None):
    if not DATA:
        load_data()
    # Now we assume DATA is populated...
    all_markets = sorted(set(r['cbsa_title'] for r in DATA))
    filtered_markets = []
    if state and 'state' in filters:
        filtered_markets = [m for m in all_markets if f', {state}' in m or f'-{state}-' in m or m.endswith(f'-{state}')]
    if 'hundred' in filters:
        op_markets = filtered_markets or all_markets
        filtered_markets = []
        for market in [m for m in op_markets if m]:
            market_data = [r for r in DATA if r['cbsa_title'] == market]
            if sum([int(r['active_listing_count']) for r in market_data if r['active_listing_count']]) / len(market_data) > 100:
                filtered_markets.append(market)
    if filtered_markets and filtered_markets[0] != '':
        filtered_markets = [''] + filtered_markets
    return filtered_markets or all_markets
    

# @hook('after_request') 
# def enable_cors():
#     """Add headers to enable CORS"""
#     response.headers['Access-Control-Allow-Origin'] = '*'
#     response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
#     # response.headers['Access-Control-Allow-Headers'] = ''

@route(f'{BASE_URL}/<:re:.*>', method='OPTIONS')
def enable_cors_generic_route():
    """
    This route takes priority over all others. So any request with an OPTIONS
    method will be handled by this function.

    See: https://github.com/bottlepy/bottle/issues/402

    NOTE: This means we won't 404 any invalid path that is an OPTIONS request.
    """
    add_cors_headers()

@hook('after_request')
def enable_cors_after_request_hook():
    """
    This executes after every route. We use it to attach CORS headers when
    applicable.
    """
    add_cors_headers()

def add_cors_headers():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

@route(f'{BASE_URL}/', method=('GET','POST'))
def index():
    market = request.params.get('market', '')
    markets = get_markets(None)
    return template(
        'chart.html', 
        BASE_URL=BASE_URL, 
        markets=json.dumps(markets),
        market=market,
    )

@route(f'{BASE_URL}/markets')
def hello():
    filters = request.params.getlist('filters')
    state_val = request.params.get('state')
    if not filters or not set(filters) <= set(['hundred', 'state']):
        filters = None
    if 'state' in filters and not state_val:
        _ = filters.pop('state')
    
    markets = get_markets(*filters, state=state_val)
    return json.dumps(markets)

@route(f'{BASE_URL}/markets/data')
def get_market_data():
    if not DATA:
        load_data()
    # Now we assume DATA is populated...
    market = request.params.get('market')
    market_data = [{'month': r['month_date_yyyymm'], 'count': r['active_listing_count']} for r in DATA if r['cbsa_title'] == market]
    return json.dumps(market_data)

if __name__ == '__main__' and ENV != 'production':
    run(host='localhost', port=9876, debug=True)

application = default_app()
