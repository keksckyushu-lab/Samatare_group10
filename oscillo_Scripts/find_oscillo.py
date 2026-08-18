import pyvisa as visa

rm = visa.ResourceManager()
print(rm)
print(rm.list_resources())