from time import sleep
from multiprocessing import Queue as InterProcessQueue


def generate_text(ipq: InterProcessQueue):
    print("process started")
    for i in range(10):
        ipq.put("Hello, ws \n")
        sleep(0.1)
    ipq.close()
