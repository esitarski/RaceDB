import argparse
from LLRPClientServer import runServer

if __name__ == '__main__':
	parser = argparse.ArgumentParser( formatter_class=argparse.ArgumentDefaultsHelpFormatter )
	parser.add_argument('--host', type=str, help='LLRPServer Host', nargs='?', default='localhost')
	parser.add_argument('--rfid_transmit_power', type=int, help='RFID Transmit Power: max_power = 0', nargs='?', default=0)
	parser.add_argument('--rfid_reader_host', type=str, help='RFID Reader (Impinj) Host', nargs='?', default='autodetect')
	args = parser.parse_args()
	
	runServer( host=args.host, llrp_host=args.rfid_reader_host, transmitPower=args.rfid_transmit_power )
