#!/usr/bin/env python

# standard usage - grabs latest block from local bitcoind via rpc and does analysis on it
#
#     python analyze_block.py --live=true

import sys
import json
import optparse
import urllib
import numpy

import matplotlib 
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from pprint import pprint
from param import param
from operator import itemgetter

from util import *
from settings import *

debug = DEBUG 

# process_block - calculates basic statistics on each transaction in a block including number of
# inputs and outputs, number of p2sh inputs and outputs, fee, and whether it respends outputs
# created in the same block. Calculates the relative average and standard deviation of the size 
# of the largest output for two and three output transactions. Calculates the independent
# distributions of transactions by number of inputs and number of outputs.
def process_block(data):
    json_out = {}

    total_tx = 0
    has_fee = 0
    prev_out_txindex = []
    for tx in data['tx']:
        total_value = 0
        num_out = 0
        max_value = 0

        total_in_value = 0
        num_in = 0
        max_in_value = 0
        for output in tx['out']:
            total_value = total_value + output['value']
            if output['value'] > max_value:
                max_value = output['value']
            num_out = num_out + 1 

        for prev in tx['inputs']:
            if 'prev_id' in prev and 'value' in prev:
                prev_out_txindex.append(prev['prev_id'])
                in_value = prev['value']
                total_in_value = total_in_value + in_value
                if in_value > max_in_value:
                    max_in_value = in_value
                num_in = num_in + 1 

        fee = total_in_value - total_value
        if fee > 0:
            has_fee += 1

        if num_in > 0:
            fees.append(fee)
            size = tx['size']/1000.0
            if size < 1.0:
                size = 1.0
            feesperkb.append([fee/size/100000.0,tx['size']])

        total_tx += 1

        if total_value > 0:
            population_max_in_fraction_all.append( float(max_value)/total_value )
        
            if num_out == 2:
                population_max_fraction2.append( float(max_value)/total_value )
        
            if num_out == 3:
                population_max_fraction3.append( float(max_value)/total_value )

            if num_out in num_outs.keys():
                max_fraction[num_out] = max_fraction[num_out] + float(max_value)/total_value
            else:
                max_fraction[num_out] = float(max_value)/total_value

        if num_out in num_outs.keys():
            num_outs[num_out] = num_outs[num_out] + 1 
        else:
            num_outs[num_out] = 1

        if num_in in num_ins.keys():
            num_ins[num_in] = num_ins[num_in] + 1 
        else:
            num_ins[num_in] = 1

    for tx in data['tx']:
        tx['respends'] = 0
        if tx['id'] in prev_out_txindex:
            tx['respends'] += 1
     
    distribution = ''
    for i in num_outs.keys():
        distribution = distribution + (str(num_outs[i]))
        distribution = distribution + ','
    if debug:
        print "Outputs per transaction"
        print distribution
        print ""
    json_out['output_count_distribution'] = distribution

    result = get_stats( population_max_fraction2 ) 
    if debug:
        print "2 output transactions (mean fraction of max output, stdev of that fraction)"
        print result
        print ""
    json_out['mean_largest_output_for_2_output_tx'] = result[0]
    json_out['stddev_largest_output_for_2_output_tx'] = result[1]

    result = get_stats( population_max_fraction3 ) 
    if debug:
        print "3 output transactions"
        print result
        print ""
    json_out['mean_largest_output_for_3_output_tx'] = result[0]
    json_out['stddev_largest_output_for_3_output_tx'] = result[1]

    distribution = ''
    for i in num_ins.keys():
        distribution = distribution + (str(num_ins[i]))
        distribution = distribution + ','
    if debug:
        print "Inputs per transaction"
        print distribution
        print ""
    json_out['input_count_distribution'] = distribution

    if debug:
        print "General"
        print "Total transactions: " + str(total_tx) + " No fee: " + str(total_tx - has_fee)
    json_out['tx_count'] = total_tx
    json_out['no_fee_count'] = total_tx - has_fee

    result = get_stats( population_max_in_fraction_all ) 
    if debug:
        print "all inputs"
        print result
        print ""
    json_out['mean_largest_output_for_all_tx'] = result[0]
    json_out['stddev_largest_output_for_all_tx'] = result[1]

    i = 0
    while i < len(param):
        json_out.update(run_filter(data, param[i], options.provider))
        i += 1

    if debug:
        print "Leftover transactions"
    matched = 0
    for tx in data['tx']:
        if tx['leftover_count'] >= len(param) and debug:
            print "https://blockchain.info/tx/%s %d %d in %0.8f out %0.8f totin %0.8f totout %0.8f lo %d" % (tx['id'],tx['num_in'],tx['num_out'],tx['max_in_value'],tx['max_value'],tx['total_in_value'],tx['total_value'],tx['leftover_count'])
            matched += 1
    if debug:
        print "Matched: " + str(matched)

    return json_out


if __name__ == '__main__':
    parser = optparse.OptionParser(usage="%prog [options]")
    parser.add_option("--live", dest="live", default=True,
            help="Get data from server")
    parser.add_option("--unconf", dest="unconf", default=False,
            help="Process only unconfirmed transactions")
    parser.add_option("--blockindex", dest="blockindex", default="last",
            help="Choose block by index")
    parser.add_option("--provider", dest="provider", default="bitcoind",
            help="Choose from 'blockchaininfo' and 'bitcoind'")
    parser.add_option("--verbose", dest="verbose", default=False,
            help="Get data from server")
    (options, args) = parser.parse_args()

    num_outs = {}
    num_ins = {}
    max_fraction = {}
    population_max_fraction2 = []
    population_max_fraction3 = []
    fees = []
    feesperkb = []
    population_max_in_fraction_all = []
    data = {}

    # obtain data to process
    if options.live or options.unconf:
        raw = ''
        if options.provider == 'blockchaininfo':
            if options.blockindex != "last":
                url = "https://blockchain.info/block-height/" + str(options.blockindex) + "?format=json"
            elif options.unconf:
                url = "https://blockchain.info/unconfirmed-transactions?format=json&offset="
            else:
                url = "https://blockchain.info/latestblock"
                
            if not options.unconf:
                response = urllib.urlopen(url);
                raw = response.read()
                parsed = json.loads(raw)
            else:
                txs = []
                response = urllib.urlopen("https://blockchain.info/q/unconfirmedcount")
                unconf_count = int(response.read())
                for i in range(unconf_count,0,-50):
                    response = urllib.urlopen(url+str(i));
                    raw = response.read()
                    parsed = json.loads(raw)
                    txs = txs + parsed['txs']
                    
            if options.blockindex != "last" or options.unconf:
                if not options.unconf:
                    height = parsed['blocks'][0]['height']
                    block_hash = parsed['blocks'][0]['hash']    
                    data = parsed['blocks'][0]
                else:
                    height = "unconf" 
                    block_hash = "unconf"
                    data = {}
                    data['tx'] = txs
                    
            else:
                height = parsed['height']
                block_hash = parsed['hash'] 
                url = "https://blockchain.info/rawblock/" + parsed['hash']

                response = urllib.urlopen(url);
                raw = response.read()
                parsed = json.loads(raw)

                data = parsed
                
            f = open("blocks/"+str(height)+"-"+options.provider+"-"+block_hash+".txt", "w")
            f.write(json.dumps(raw))
            f.close()
        else:
            from rpc import RPC
            rpc = RPC(RPCUSER, RPCPASS, SERVER, RPCPORT)
            block_hash = rpc.get('getbestblockhash')['output']['result']
            block = rpc.get('getblock',[block_hash])['output']['result']
            height = block['height']
            block_hash = block['hash']
            data['tx'] = []
            inptx_cache = {}
            for txid in block['tx']:
                rawtx = rpc.get('getrawtransaction',[txid])['output']['result']
                tx = rpc.get('decoderawtransaction',[rawtx])['output']['result']
                for inp in tx['vin']:
                    if 'txid' not in inp:
                        continue
                    if inp['txid'] not in inptx_cache:
                        rawtx = rpc.get('getrawtransaction',[inp['txid']])['output']['result']
                        inptx = rpc.get('decoderawtransaction',[rawtx])['output']['result']
                        inptx_cache[inp['txid']] = inptx
                    else:
                        inptx = inptx_cache[inp['txid']]
                    #TODO: deal with nonstandard transaction inputs whose transactions don't seem to have enough outputs
                    if inp['vout'] < len(inptx['vout']):
                        inp['value'] = inptx['vout'][inp['vout']]['value']
                data['tx'].append(tx)
    else:
        if options.provider == 'blockchaininfo':
            the_file = '000000000000000016bae92da911065f77e52e65c7c5d164ee12b57247176ab0.json'
        else:
            the_file = 'last'

        with open(the_file) as data_file:
            data = json.load(data_file)

    normalized_data = {'tx':[]}
    for tx in data['tx']:
        normalized_data['tx'].append(read_transaction(tx, options.provider))

    stats = process_block(normalized_data)
    print json.dumps(stats)
