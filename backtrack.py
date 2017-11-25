from analyze_block import save_block_info
from time import time

while 1:
    start = time()
    height, block_hash = save_block_info('bitcoind', True, 'unprocessed', False)
    print "Block %s Hash %s Time elapsed %s" % (height, block_hash, str(time() - start))
