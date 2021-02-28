import requests
import re
from flask import Flask, render_template, request

import settings
from settings import *
from geoip.geo import Geo
from rdap.rdap import Rdap
from tor.tor import Tor

app = Flask(__name__, static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16Mb

tor = Tor(settings)
geo = Geo(tor, settings)
rdap = Rdap(tor, settings)

response = requests.get('https://check.torproject.org/exit-addresses')
tor_ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", response.text)
for ip in tor_ips:
    settings.TOR_IPS.append(ip)
print('\n[!] Update tor exit node with', len(tor_ips), 'ips')

@app.route('/')
def hello():
    public_ip = request.remote_addr
    if not public_ip == '127.0.0.1': # dev env
        result = handle(public_ip)
    else:
        result = {'ip':'', 'geolocation':'', 'rdap':''}
    
    return render_template('index2.html', port=APP_PORT, ip_info=result)


@app.route('/list', methods=['POST'])
def list_():
    if request.method == 'POST':
        ip = request.form['ipForm']
        if ip:
            result = handle(ip)
            return render_template('list2.html', ip_info=result)
        return render_template('list2.html', ip_info={})


def handle(ip):
    
    ip_dict = {'ip':ip}
    geolocation = geo.get_geolocation(ip)
    ip_dict['geolocation'] = geolocation
            
    rdap_info = rdap.get_rdap(ip) # get whois
    ip_dict['rdap'] = rdap_info

    whois_info = rdap.get_whois(ip) # get whois
    print('whois_info -->', whois_info)
    ip_dict['whois'] = whois_info
    
    ip_dict['is_tor'] = True if ip in settings.TOR_IPS else False

    if not ip_dict['geolocation'] and not ip_dict['rdap']:
        return None
    
    return ip_dict

if __name__ == '__main__':
    app.run(debug=True, port=APP_PORT)