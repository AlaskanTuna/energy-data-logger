import time, pprint

from logger_service import service

service.start()
print("Logger started … Ctrl-C to quit demo")

try:
    for _ in range(5):
        time.sleep(3)
        pprint.pprint(service.latest())
finally:
    service.stop()