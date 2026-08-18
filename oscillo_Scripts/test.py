import pyvisa
import env

rm = pyvisa.ResourceManager()

print("VISA library:", rm.visalib)
print("Detected:", rm.list_resources())

visa_addr = env.visa_addr

try:
    osc = rm.open_resource(visa_addr)
    osc.timeout = 5000
    osc.read_termination = "\n"
    osc.write_termination = "\n"

    print("Connected:", osc.query("*IDN?"))

finally:
    if "osc" in locals():
        osc.close()
    rm.close()
