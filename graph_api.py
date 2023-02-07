import json
import os
from csv import DictReader

import requests
from bottle import default_app, hook, request, response, route, run, template

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

def get_markets(filter_results):
    if not DATA:
        load_data()
    # Now we assume DATA is populated...
    all_markets = sorted(set(r['cbsa_title'] for r in DATA))
    if filter_results:
        filtered_markets = []
        for market in [m for m in all_markets if m]:
            market_data = [r for r in DATA if r['cbsa_title'] == market]
            if sum([int(r['active_listing_count']) for r in market_data if r['active_listing_count']]) / len(market_data) > 100:
                filtered_markets.append(market)
        return filtered_markets
    return all_markets
    

# @hook('after_request') 
# def enable_cors():
#     """Add headers to enable CORS"""
#     response.headers['Access-Control-Allow-Origin'] = '*'
#     response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
#     # response.headers['Access-Control-Allow-Headers'] = ''

@route('/<:re:.*>', method='OPTIONS')
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

@route('/', method=('GET',))
def index():
    market = request.query.get('market', '')
    return template('chart.html', BASE_URL='http://localhost:9876', market=market)

@route('/markets')
def hello():
    filter_results = request.params.get('filter', 'false') == 'true'
    markets = get_markets(filter_results)
    return json.dumps(markets)

@route('/markets/data', method=('POST',))
def get_market_data():
    if not DATA:
        load_data()
    # Now we assume DATA is populated...
    market = request.json.get('market')
    market_data = [{'month': r['month_date_yyyymm'], 'count': r['active_listing_count']} for r in DATA if r['cbsa_title'] == market]
    return json.dumps(market_data)


# run(host='localhost', port=9876, debug=True)
application = default_app()
