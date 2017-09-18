import oauth2
import urllib
import json
import requests
import gen_outline
import json2csv
import socket
import os

import common

def oauth_req(url, consumer_key, consumer_secret, key, secret, http_method="GET", post_body="", http_headers=None):
    consumer = oauth2.Consumer(key=consumer_key, secret=consumer_secret)
    token = oauth2.Token(key=key, secret=secret)
    client = oauth2.Client(consumer, token)
    resp, content = client.request(url, method=http_method, body=post_body, headers=http_headers)
    return content


def get_json_data(url, parameters, consumer_key, consumer_secret, key, secret):
    json_element = {"nodes": []}
    page = 1
    max_id = None
    while True:
        parameter_encode = urllib.urlencode(parameters)
        try:
            search_result = oauth_req(url + parameter_encode, consumer_key, consumer_secret, key, secret)
        except socket.error:
            print('Connection timed-out. Try again later.')
            break
        search_result = json.loads(search_result)
        if common.CONF['data_to_fetch'] == '1':
            try:
                statuses = search_result['statuses']
                assert len(statuses) > 1
            except (KeyError, AssertionError):
                if not max_id:
                    print('Empty response received.')
                break
            json_element['nodes'].extend(statuses)
            max_id = statuses[-1]['id']
            parameters['max_id'] = max_id
        else:
            try:
                assert len(search_result) > 1
            except (KeyError, AssertionError):
                if page != 1:
                    print('Empty response received.')
                break
            json_element['nodes'].extend(search_result)
            page += 1
            parameters['page'] = page
    return json_element


def main():
    common.start()
    common.CONF['data_to_fetch'] = common.ask('Fetch Tweet Data or User Data? 1/Tweet 2/User',
                                answer=list, default='2', options=[1, 2])
    request_params = {}
    if common.CONF['data_to_fetch'] == '2':
        print("You requested User Data")
        common.CONF['query'] = common.ask('Search terms? ' +
                            'Found here: https://dev.twitter.com/rest/public/search',
                            answer=common.str_compat)
        request_params['q'] = common.CONF['query']
        url = 'https://api.twitter.com/1.1/users/search.json?'
    else:
        print("You requested Tweet Data")
        common.CONF['query'] = common.ask('Search terms? ' +
                            'Found here: https://dev.twitter.com/rest/public/search',
                            answer=common.str_compat)
        request_params['q'] = common.CONF['query']
        result_data_type = common.ask('Type of search results? 1/Popular 2/Recent 3/Mixed',
                               answer=list, default='1', options=[1, 2, 3])
        request_params['result_type'] = common.RESULT_MAP[result_data_type]
        location = common.ask('Location? Eg. 1600 Amphitheatre Parkway, Mountain View, CA',
                       answer=common.str_compat, default=" ")
        if location.strip():
            encode_location = urllib.urlencode({'address': location})
            response_location = requests.get('https://maps.googleapis.com/maps/api/geocode/json?' +
                                             encode_location)
            try:
                location_json = response_location.json()
                location_data = location_json['results'][0]['geometry']['location']
                location_array = [str(value) for value in location_data.itervalues()]
                if location_array:
                    radius_mi = common.ask('Distance to search within in miles',
                                    answer=common.str_compat)

                    location_array.append(radius_mi + u'mi')
                    common.CONF['geocode'] = ",".join(location_array)
                    request_params['geocode'] = common.CONF['geocode']
            except:
                print('Unable to fetch lat and long for location')

        # date = common.ask('Include tweets before? eg. 2015-07-19', answer=dateObject, default=" ")
        # if date.strip():
        #     request_params['until'] = date
        url = 'https://api.twitter.com/1.1/search/tweets.json?'
    output_file_name = common.ask('Output file name',
                           answer=common.str_compat, default="output")
    print('Sending request to API...')
    json_search_data = get_json_data(url, request_params, common.CONF['consumer_key'],
                                     common.CONF['consumer_secret'],
                                     common.CONF['api_key'], common.CONF['api_secret'])
    if json_search_data['nodes']:
        print('API response received.')
        with open('json_dump.json', 'w') as outfile:
            json.dump(json_search_data, outfile)
        outline = gen_outline.make_outline('json_dump.json', False, 'nodes')
        print('Generating outline file..')
        outfile = 'outline.json'
        with open(outfile, 'w') as f:
            json.dump(outline, f, indent=2, sort_keys=True)
        print('Outline file generation done.')
        with open(outfile) as f:
            key_map = json.load(f)
        loader = json2csv.Json2Csv(key_map)
        outfile = output_file_name + '.csv'
        if os.path.isfile(outfile):
            os.remove(outfile)
        print('Writing to %s' % outfile)
        with open('json_dump.json') as f:
            loader.load(f)
        loader.write_csv(filename=outfile, make_strings=True)
        print('Output file generated.')
    else:
        print('Search yield no results')

if __name__ == "__main__":
    main()
