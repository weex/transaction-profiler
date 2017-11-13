import numpy

debug = False

def get_stats( data ):
    if len(data) > 0:
        arr = numpy.array( data )
        return ( numpy.mean(arr), numpy.std(arr) )
    return "No data"

def get_fee_stats( data ):
    if len(data) > 0:
        arr = numpy.array( data )
        print "Number of non-cb transactions: " + str(len(data))
        print "Minimum fee: " + str(numpy.min(arr)/100000000.0)
        print "Average fee for payers: " + str(numpy.mean(arr)/100000000.0)
        print "Median fee for payers: " + str(numpy.median(arr)/100000000.0)
        print "Stdev of fee for payers: " + str(numpy.std(arr)/100000000.0)
    return "No data"

def read_transaction(native_tx,source):
    our_tx = {}

    if source == 'blockchaininfo':
        our_tx['inputs'] = native_tx['inputs']
        our_tx['out'] = native_tx['out']
        our_tx['id'] = native_tx['tx_index']
        for out in our_tx['inputs']:
            if 'prev_out' in out:
                out['prev_id'] = out['prev_out']['tx_index']
                out['value'] = out['prev_out']['value']
    else: # bitcoind
        our_tx['inputs'] = native_tx['vin']
        our_tx['out'] = native_tx['vout']
        our_tx['id'] = native_tx['txid']
        for inp in our_tx['inputs']:
            if 'txid' in inp:
                inp['prev_id'] = inp['txid']

    our_tx['size'] = native_tx['size']

    return our_tx

def txfilter(data, param, source):
    out = []
    leftovers = []
    has_fee = 0
    for tx in data:
        # do calculations
        total_value = 0
        num_out = 0
        p2sh_out = 0
        max_value = 0
        min_value = 10000000.0
        out_value_bins = {}
        out_pole_count = 0

        total_in_value = 0
        num_in = 0
        p2sh_in = 0
        min_in_value = 10000000.0
        max_in_value = 0
        in_value_bins = {}
        in_pole_count = 0

        keep = 0 
        tests_applied = 0

        # find min and max output values, count p2sh outputs
        for output in tx['out']:
            total_value = total_value + output['value']
            if output['value'] > max_value:
                max_value = output['value']
            if output['value'] < min_value:
                min_value = output['value']
            if output['value'] in out_value_bins:
                out_value_bins[output['value']] += 1
            else:
                out_value_bins[output['value']] = 1
            if 'addr' in output and output['addr'][0] == '3':
                p2sh_out += 1
            num_out = num_out + 1 
    
        tx['num_out'] = num_out
        tx['p2sh_out'] = p2sh_out
        tx['max_value'] = max_value / 100000000.0 
        tx['min_value'] = min_value / 100000000.0 
        tx['total_value'] = total_value / 100000000.0

        # find min and max input values, count p2sh inputs
        for prev in tx['inputs']:
            if 'value' in prev:
                in_value = prev['value']
                total_in_value = total_in_value + in_value
                if in_value > max_in_value:
                    max_in_value = in_value
                if in_value < min_in_value:
                    min_in_value = in_value
                if in_value in in_value_bins:
                    in_value_bins[in_value] += 1
                else:
                    in_value_bins[in_value] = 1
                if 'addr' in prev and prev['addr'][0] == '3':
                    p2sh_in += 1
                num_in = num_in + 1 

        tx['num_in'] = num_in
        tx['p2sh_in'] = p2sh_in
        tx['max_in_value'] = max_in_value / 100000000.0
        tx['min_in_value'] = min_in_value / 100000000.0
        tx['total_in_value'] = total_in_value / 100000000.0

        tx['fee'] = total_in_value - total_value
        if tx['fee'] > 0:
            has_fee += 1
    
        # has_carry - fee seems to be taken entirely from one input the rest of which is passed through
        tx['has_carry'] = False
        tx['carry_left'] = 0
        for output in tx['out']:
            for prev in tx['inputs']:
                if 'value' in prev:
                    if abs(prev['value'] - output['value'] - tx['fee']) < 0.00001:
                        tx['carry_left'] = output['value']
                        tx['has_carry'] = True
                            
        out_range_keep = 0
        for output in tx['out']:
            if "out_range" in param:
                (min_or, max_or) = param['out_range']
                if output['value'] >= min_or*100000000.0 and output['value'] <= max_or*100000000.0 and tx['carry_left'] != output['value']:
                    out_range_keep += 1     

        if out_range_keep > 0:
            keep += 1

        if "out_range" in param:
            tests_applied += 1
        
        # find out the most frequent of the identical valued outputs, aka pole, if there are multiple duplicates it'll list the first identical group
        max_bin_count = 0
        max_bin_key = 0
        for key in out_value_bins.keys():
            if out_value_bins[key] > max_bin_count:
                max_bin_key = key
        out_pole = max_bin_key
        if max_bin_key != 0:
            out_pole_count = out_value_bins[max_bin_key]

        Gmax_bin_count = 0
        max_bin_key = 0
        for key in in_value_bins.keys():
            if in_value_bins[key] > max_bin_count:
                max_bin_key = key
        in_pole = max_bin_key
        if max_bin_key != 0:
            in_pole_count = in_value_bins[max_bin_key]

        # apply filters
        if "num_in" in param:
            tests_applied += 1
            (pmin, pmax) = param['num_in']
            if tx['num_in'] >= pmin and tx['num_in'] <= pmax:
                keep += 1       

        if "num_out" in param:
            tests_applied += 1
            (pmin, pmax) = param['num_out']
            if tx['num_out'] >= pmin and tx['num_out'] <= pmax:
                keep += 1       

        if "p2sh_in" in param:
            tests_applied += 1
            (pmin, pmax) = param['p2sh_in']
            if tx['p2sh_in'] >= pmin and tx['p2sh_in'] <= pmax:
                keep += 1       

        if "p2sh_out" in param:
            tests_applied += 1
            (pmin, pmax) = param['p2sh_out']
            if tx['p2sh_out'] >= pmin and tx['p2sh_out'] <= pmax:
                keep += 1       

        if "abs_smallest" in param:
            tests_applied += 1
            (min_as, max_as) = param['abs_smallest']
            if tx['min_value'] >= min_as and tx['min_value'] <= max_as:
                keep += 1       

        if "abs_largest" in param:
            tests_applied += 1
            (min_al, max_al) = param['abs_largest']
            if tx['max_value'] >= min_al and tx['max_value'] <= max_al:
                keep += 1       

        if "max_in_eq_out" in param:
            tests_applied += 1
            if tx['max_value'] == tx['max_in_value']:
                keep += 1       

        if "respends" in param:
            tests_applied += 1
            if tx['respends'] > 0:
                keep += 1       

        if "ident_in" in param:
            tests_applied += 1
            (pmin, pmax) = param['ident_in']
            if in_pole_count >= pmin and in_pole_count <= pmax:
                keep += 1       

        if "ident_out" in param:
            tests_applied += 1
            (pmin, pmax) = param['ident_out']
            if out_pole_count >= pmin and out_pole_count <= pmax:
                keep += 1       

        if "carry_fee" in param:
            tests_applied += 1
            if param['carry_fee'] and tx['has_carry']:
                keep += 1       
        
        if tests_applied <= keep:
            out.append(tx)
        else:
            leftovers.append(tx)            
    
    return (out, leftovers) 

def run_filter(data, param, source):
    json_out = {}
    (filtered,leftovers) = txfilter(data['tx'], param, source)
    description = param['label']
    matched = 0
    if debug:
        print "\nFiltering for "+description

    for tx in filtered:
        if debug:
            print "https://blockchain.info/tx/%s %d %d in %0.8f out %0.8f totin %0.8f totout %0.8f" % (tx['hash'],tx['num_in'],tx['num_out'],tx['max_in_value'],tx['max_value'],tx['total_in_value'],tx['total_value'])
        matched += 1

    if debug:
        print (param)
        print "Matched: " + str(matched)

    json_out[description] = {'count': matched}

    for tx in leftovers:
        for otx in data['tx']:
            if tx['id'] == otx['id']:
                if 'leftover_count' in otx:
                    otx['leftover_count'] += 1
                else:
                    otx['leftover_count'] = 1
      
    return json_out
