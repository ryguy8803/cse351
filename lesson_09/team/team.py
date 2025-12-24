""" 
Course: CSE 351
Team  : 
File  : Week 9 team.py
Author:  Luc Comeau
"""

# Include CSE 351 common Python files. 
from cse351 import *
import time
import random
import multiprocessing as mp

# number of cleaning staff and hotel guests
CLEANING_STAFF = 2
HOTEL_GUESTS = 5

# Run program for this number of seconds
TIME = 60

STARTING_PARTY_MESSAGE =  'Turning on the lights for the party vvvvvvvvvvvvvv'
STOPPING_PARTY_MESSAGE  = 'Turning off the lights  ^^^^^^^^^^^^^^^^^^^^^^^^^^'

STARTING_CLEANING_MESSAGE =  'Starting to clean the room >>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
STOPPING_CLEANING_MESSAGE  = 'Finish cleaning the room <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'

def cleaner_waiting():
    time.sleep(random.uniform(0, 2))

def cleaner_cleaning(id):
    print(f'Cleaner: {id}')
    time.sleep(random.uniform(0, 2))

def guest_waiting():
    time.sleep(random.uniform(0, 2))

def guest_partying(id, count):
    print(f'Guest: {id}, count = {count}')
    time.sleep(random.uniform(0, 1))

def cleaner(cleanerlock, clean_count):
    """
    do the following for TIME seconds
        cleaner will wait to try to clean the room (cleaner_waiting())
        get access to the room
        display message STARTING_CLEANING_MESSAGE
        Take some time cleaning (cleaner_cleaning())
        display message STOPPING_CLEANING_MESSAGE
    """
    cleaner_waiting()
    while True:
        with cleanerlock:
            cleanercount += 1
            if cleanercount == 1:
                cleanerlock.aquire()
        
        print(f"{STARTING_CLEANING_MESSAGE}")

        with cleanerlock:
            cleanercount -= 1
            if cleanercount == 0:
                cleanerlock.release()
                clean_count += 1
        print(f"{STOPPING_CLEANING_MESSAGE}")


    pass

def guest(guestlock, party_count):
    """
    do the following for TIME seconds
        guest will wait to try to get access to the room (guest_waiting())
        get access to the room
        display message STARTING_PARTY_MESSAGE if this guest is the first one in the room
        Take some time partying (call guest_partying())
        display message STOPPING_PARTY_MESSAGE if the guest is the last one leaving in the room
    """
    guest_waiting
    while True:
        with guestlock:
            cleanercount += 1
            if cleanercount == 1:
                guestlock.aquire()
        
        print(f"{STARTING_PARTY_MESSAGE}")

        with guestlock:
            cleanercount -= 1
            if cleanercount == 0:
                guestlock.release()
                party_count += 1
        print(f"{STOPPING_PARTY_MESSAGE}")
    pass

def main():
    # Start time of the running of the program.
    start_time = time.time()
    room_lock = mp.Lock()
    rc_lock= mp.Lock()
    party_count = 0
    cleaned_count = 0

    for i in range(CLEANING_STAFF):
        t = mp.Thread(target=cleaner, args=(i+1, room_lock, clean_count_val), name=f"Cleaner-{i+1}", daemon=True)
        threads.append(t)
        t.start()


    for i in range(HOTEL_GUESTS):
        
        t = mp.Thread(target=guest, args=(i+1, rc_lock, room_lock, read_count_val, party_count_val), name=f"Guest-{i+1}", daemon=True)
        threads.append(t)
        t.start()

    # TODO - add any variables, data structures, processes you need
    # TODO - add any arguments to cleaner() and guest() that you need

    # Results
    print(f'Room was cleaned {cleaned_count} times, there were {party_count} parties')


if __name__ == '__main__':
    main()
