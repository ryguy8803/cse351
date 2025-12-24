"""
Course: CSE 351, week 10
File: functions.py
Author: Rylan Hoogland

Instructions:

Depth First Search
https://www.youtube.com/watch?v=9RHO6jU--GU

Breadth First Search
https://www.youtube.com/watch?v=86g8jAQug04

--------------------------------------------------------------------------------------
You will lose 10% if you don't detail your part 1 and part 2 code below

Describe how to speed up part 1

I used threading to parallelize the retrieval of family members. 
The server has a time delay delay per request, processing a family normaly will be slow. 
As soon as a Family object is retrieved, I spawn separate threads for The husband, the wife, and every child 
This lets the program to wait for the network delay of all family members together.

Describe how to speed up part 2

I used a queue to process the tree generations. 
I then made threads for every single family in the generation's queue. 
I also made more threads to fetch the husband, wife, and children in parallel. 

Extra (Optional) 10% Bonus to speed up part 3

<Add your comments here>

"""
from common import *
import threading
tree_lock = threading.Lock()

# -----------------------------------------------------------------------------
def depth_fs_pedigree(family_id, tree):

    threads = []

    if family_id is None:
        return

    fam_data = get_data_from_server(f'{TOP_API_URL}/family/{family_id}')
    if not fam_data:
        return

    family = Family(fam_data)
    
    with tree_lock:
        if not tree.does_family_exist(family.get_id()):
            tree.add_family(family)

    def process_parent_recursive(person_id):
        if person_id is None:
            return
        
        p_data = get_data_from_server(f'{TOP_API_URL}/person/{person_id}')
        if p_data:
            person = Person(p_data)
            with tree_lock:
                if not tree.does_person_exist(person.get_id()):
                    tree.add_person(person)
            
            
            parent_fam_id = person.get_parentid()
            if parent_fam_id:
                depth_fs_pedigree(parent_fam_id, tree)

    def process_child(person_id):
        if person_id is None:
            return
        p_data = get_data_from_server(f'{TOP_API_URL}/person/{person_id}')
        if p_data:
            person = Person(p_data)
            with tree_lock:
                if not tree.does_person_exist(person.get_id()):
                    tree.add_person(person)
    
    # Husband
    t_h = threading.Thread(target=process_parent_recursive, args=(family.get_husband(),))
    threads.append(t_h)
    t_h.start()

    # Wife
    t_w = threading.Thread(target=process_parent_recursive, args=(family.get_wife(),))
    threads.append(t_w)
    t_w.start()

    # Children
    for child_id in family.get_children():
        t_c = threading.Thread(target=process_child, args=(child_id,))
        threads.append(t_c)
        t_c.start()

    for t in threads:
        t.join()


# -----------------------------------------------------------------------------
def breadth_fs_pedigree(family_id, tree):
    
    if family_id is None:
        return

    fam_queue = [family_id]

    while len(fam_queue) > 0:
        
        next_fam_queue = []
        next_queue_lock = threading.Lock()
        threads = []

        def process_family(fid):
            fam_data = get_data_from_server(f'{TOP_API_URL}/family/{fid}')
            if not fam_data:
                return

            family = Family(fam_data)
            with tree_lock:
                if not tree.does_family_exist(family.get_id()):
                    tree.add_family(family)   #© Brother Edmond's suggestion

            member_threads = []

            def fetch_and_queue_parent(pid):
                if pid is None: return
                p_data = get_data_from_server(f'{TOP_API_URL}/person/{pid}')
                if p_data:
                    p = Person(p_data)
                    with tree_lock:
                        if not tree.does_person_exist(p.get_id()):
                            tree.add_person(p)
                    par_fam_id = p.get_parentid()
                    if par_fam_id:
                        with next_queue_lock:
                            next_fam_queue.append(par_fam_id)

            def fetch_child(pid):
                if pid is None: return
                p_data = get_data_from_server(f'{TOP_API_URL}/person/{pid}')
                if p_data:
                    p = Person(p_data)
                    with tree_lock:
                        if not tree.does_person_exist(p.get_id()):
                            tree.add_person(p)

            t_h = threading.Thread(target=fetch_and_queue_parent, args=(family.get_husband(),))
            t_w = threading.Thread(target=fetch_and_queue_parent, args=(family.get_wife(),))
            
            member_threads.extend([t_h, t_w])
            t_h.start()
            t_w.start()

            for cid in family.get_children():
                t_c = threading.Thread(target=fetch_child, args=(cid,))
                member_threads.append(t_c)
                t_c.start()

            for t in member_threads:
                t.join()

        for fid in fam_queue:
            t = threading.Thread(target=process_family, args=(fid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        fam_queue = next_fam_queue


# -----------------------------------------------------------------------------
def breadth_fs_pedigree_limit5(family_id, tree):
    # KEEP this function even if you don't implement it
    # TODO - implement breadth first retrieval
    #      - Limit number of concurrent connections to the FS server to 5
    # TODO - Printing out people and families that are retrieved from the server will help debugging

    pass