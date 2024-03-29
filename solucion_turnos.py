import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value





SOUTH = 1
NORTH = 0

NCARS = 15
NPED = 5
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        
        #Contador
        self.patata = Value('i', 0)
        
        
        
        #Número de coches y peatones esperando
        self.cN_waiting     = Value('i', 0)
        self.cS_waiting     = Value('i', 0)
        self.pers_waiting   = Value('i', 0)
        
        #Número de coches y peatones dentro del puente
        self.ncoches_N         = Value('i', 0)
        self.ncoches_S         = Value('i', 0)
        self.npers             = Value('i', 0)
        
        # turno=0 => peatones; turno=1 => coche_S; turno=2 => coche_N
        self.turno             = Value('i', 0)
        
        
        #Condiciones para entrar en el puente
        self.entra_pers       = Condition(self.mutex)
        self.entra_coche_S    = Condition(self.mutex)
        self.entra_coche_N    = Condition(self.mutex)
        

    

    #Devuelve true si no hay ni personas ni coches del norte dentro del puente y 
    # si no hay ni coches del norte ni personas esperando o si es el turno de los coches del sur
    def no_pers_S(self):
        return self.npers.value + self.ncoches_N.value == 0 and \
            (self.cN_waiting.value + self.pers_waiting.value == 0 ) or \
            (self.turno.value == 1 ) 
            
    #Devuelve true si no hay ni personas ni coches del sur dentro del puente y 
    # si no hay ni coches del sur ni personas esperando o si es el turno de los coches del sur       
    def no_pers_N(self):
        return self.npers.value + self.ncoches_S.value == 0 and \
            (self.cS_waiting.value + self.pers_waiting.value == 0 ) or \
            (self.turno.value == 2 ) 
    
    
            
             

    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        if direction == 1:
            self.cS_waiting.value += 1
            self.entra_coche_S.wait_for(self.no_pers_S)
            self.cS_waiting.value -= 1
            self.ncoches_S.value  += 1
        else:
            self.cN_waiting.value += 1
            self.entra_coche_N.wait_for(self.no_pers_N)
            self.cN_waiting.value -= 1
            self.ncoches_N.value  += 1
        self.mutex.release()
    
    
                
                
    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
          
        if direction == 1:
            self.ncoches_S.value -= 1
            self.turno.value = random.choice([0,2])
            if self.ncoches_S.value == 0:
                self.entra_coche_N.notify_all()
                self.entra_pers.notify_all() 
                self.entra_coche_S.notify_all()
        else:
            self.ncoches_N.value -= 1
            self.turno.value = random.randint(0,1)
            if self.ncoches_N.value == 0:
                self.entra_pers.notify_all()    
                self.entra_coche_S.notify_all()
                self.entra_coche_N.notify_all()

        self.mutex.release()
        
        
    
    #Devuelve true si no hay coches dentro del puente y 
    # si no hay coches esperando o si es el turno de las personas        
    def no_hay_coches(self):
        return self.ncoches_S.value + self.ncoches_N.value  == 0 and \
            (self.cS_waiting.value + self.cN_waiting.value == 0 or self.turno.value == 0)

    
        
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.pers_waiting.value += 1

        self.entra_pers.wait_for(self.no_hay_coches)

        self.pers_waiting.value -= 1
        self.npers.value  += 1
        self.mutex.release()
        



    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.npers.value -= 1
        self.turno.value = random.randint(1,2)
        if self.npers.value == 0:
            self.entra_coche_S.notify_all()
            self.entra_coche_N.notify_all()
            self.entra_pers.notify_all() 
        self.mutex.release()

    def __repr__(self) -> str:
        return f"iter:{self.patata.value},coche_S:{self.ncoches_S.value}, cS_wait:{self.cS_waiting.value},coche_N:{self.ncoches_N.value}, cN_wait:{self.cN_waiting.value}, npers:{self.npers.value}, pers_wait:{self.pers_waiting.value}>"

def delay_car_north() -> None:      
    #time.sleep(random.normalvariate(1,0.5))
    time.sleep(random.random()/3)

def delay_car_south() -> None:     
    #time.sleep(random.normalvariate(1,0.5))
    time.sleep(random.random()/3)

def delay_pedestrian() -> None:   
    #time.sleep(random.normalvariate(30,10))
    time.sleep(random.random()/2)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()
