#addr = "169.254.71.5" #find_oscilloを実行してオシロのIPを調べ、ここに記入
addr = "192.168.0.10" 
visa_addr = f"TCPIP::{addr}::hislip0,4800::INSTR"
#visa_addr = "TCPIP::169.254.245.227::INSTR"