"""
Course    : CSE 351
Assignment: 04
Student   : <Rylan Hoogland>

Instructions:
    - review instructions in the course

In order to retrieve a weather record from the server, Use the URL:

f'{TOP_API_URL}/record/{name}/{recno}

where:

name: name of the city
recno: record number starting from 0

"""
from queue import Queue
import threading 
import time
from common import TOP_API_URL, CITIES, get_data_from_server, Log
from cse351 import *

THREADS = 20                # TODO - set for your program
WORKERS = 10
RECORDS_TO_RETRIEVE = 5000  # Don't change
REQUEST_QUEUE_DONE = None
DATA_QUEUE_DONE = None

# ---------------------------------------------------------------------------
def retrieve_weather_data(request_queue, data_queue):
# TODO - fill out this thread function (and arguments)
    while True:
        command = request_queue.get()
        if command is REQUEST_QUEUE_DONE:
            data_queue.put(DATA_QUEUE_DONE)
            request_queue.put(REQUEST_QUEUE_DONE)
            request_queue.task_done()
            print(f'{threading.current_thread().name} finished retrieving.')
            break 
        else:
            name, recno = command
    
    url = f'{TOP_API_URL}/record/{name}/{recno}'
    data = get_data_from_server(url)
        
    weather_data = (data['city'], data['date'], data['temp'])
    data_queue.put(weather_data)
        
    request_queue.task_done()
        
    


# ---------------------------------------------------------------------------
# TODO - Create Worker threaded class
class Worker(threading.Thread):
    def __init__(self, data_queue, noaa_instance):
        threading.Thread.__init__(self)
        self.data_queue = data_queue 
        self.noaa = noaa_instance

    def run(self):
        while True:
            data = self.data_queue.get()

            if data is DATA_QUEUE_DONE:
                self.data_queue.put(DATA_QUEUE_DONE)
                self.data_queue.task_done()
                break

            city, date, temp = data
            self.noaa.add_temp_record(city, temp)
            self.data_queue.task_done()

        print(f'{self.name} finished working')



# ---------------------------------------------------------------------------
# TODO - Complete this class
class NOAA:

    def __init__(self):
        self.data = {city: [] for city in CITIES}
        self.lock = threading.Lock()

    def add_temp_record(self, city, temp):
        with self.lock:
            self.data[city].append(temp)

    def get_temp_details(self, city):
        temps = self.data.get(city, [])
        if not temps:
            return 0.0
        
        return sum(temps) / len(temps)


# ---------------------------------------------------------------------------
def verify_noaa_results(noaa):

    answers = {
        'sandiego': 14.5004,
        'philadelphia': 14.865,
        'san_antonio': 14.638,
        'san_jose': 14.5756,
        'new_york': 14.6472,
        'houston': 14.591,
        'dallas': 14.835,
        'chicago': 14.6584,
        'los_angeles': 15.2346,
        'phoenix': 12.4404,
    }

    print()
    print('NOAA Results: Verifying Results')
    print('===================================')
    for name in CITIES:
        answer = answers[name]
        avg = noaa.get_temp_details(name)

        if abs(avg - answer) > 0.00001:
            msg = f'FAILED  Expected {answer}'
        else:
            msg = f'PASSED'
        print(f'{name:>15}: {avg:<10} {msg}')
    print('===================================')


# ---------------------------------------------------------------------------
def main():

    log = Log(show_terminal=True, filename_log='assignment.log')
    log.start_timer()

    noaa = NOAA()

    # Start server
    data = get_data_from_server(f'{TOP_API_URL}/start')

    # Get all cities number of records
    print('Retrieving city details')
    city_details = {}
    name = 'City'
    print(f'{name:>15}: Records')
    print('===================================')
    for name in CITIES:
        city_details[name] = get_data_from_server(f'{TOP_API_URL}/city/{name}')
        print(f'{name:>15}: Records = {city_details[name]['records']:,}')
    print('===================================')

    records = RECORDS_TO_RETRIEVE

    # TODO - Create any queues, pipes, locks, barriers you need
    #barrier = threading.Barrier(records)

    #barrier.wait()
    request_queue = Queue(maxsize=10)
    data_queue = Queue(maxsize=10)
    
    request_threads = []
    print(f'Starting {THREADS} request threads...')
    for i in range(THREADS):
        t = threading.Thread(target=retrieve_weather_data, args=(request_queue, data_queue), name=f'ReqThread-{i}')
        request_threads.append(t)
        t.start()
    
    workers = []
    print('starting {WORKERS} worker threads...')
    for i in range (WORKERS):
        w = Worker(data_queue, noaa)
        workers.append(w)
        w.start()

    print(f'Populating request que with {len(CITIES) * records:,} commands...')
    for name in CITIES:
        for recno in range(records):
            request_queue.put((name, recno))

    request_queue.join()
    print('Request que empty. sending all done sentinel')
    request_queue.put(REQUEST_QUEUE_DONE)

    for t in request_threads:
        t.join()
    print ('All requested threads finished')

    data_queue.join()
    print('data queue empty')

    for w in workers:
        w.join()
    print('all worker threads finished')

    # End server - don't change below
    data = get_data_from_server(f'{TOP_API_URL}/end')
    print(data)

    verify_noaa_results(noaa)

    log.stop_timer('Run time: ')


if __name__ == '__main__':
    main()

