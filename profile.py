from analyze_block import save_block_info    
from time import time
import cProfile

cProfile.run("save_block_info('bitcoind', True, 'unprocessed', False)")
