from analyze_block import save_block_info    
from time import time


while 1:
    start = time()
    save_block_info('bitcoind', True, 'unprocessed', False)
    print "Time elapsed: " + str(time() - start)
