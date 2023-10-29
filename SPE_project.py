import numpy as np
from numpy import random
import simpy

num_customer = 10
service_time = 2
lamda = 1/6
mu = 1/20
c = 5
department_num = 3
simulation_time = 60000
maxCapacity = 100
population = 10000
randarray = np.arange(0, department_num, 1)

class Customer:
    def __init__(self, id, service, arrtime, duration):
        self.id = id
        self.service = service
        self.arrtime = arrtime
        self.duration = duration
    def __str__(self):
        return 'customer %d arrive at %d, request %d length %d' % (self.id, self.arrtime, self.service, self.duration)

class Server:
    def __init__(self, env, job, server_id, service):
        self.env = env
        self.job = job
        self.waitingTime = 0
        self.servingTime = 0
        self.server_id = server_id
        self.service = service
        self.standBy = None
        self.idleTime = 0
        self.jobDone = 0
        env.process(self.serve())

    def serve(self):

        while True:
            if self.job is None:
                self.standBy = env.process(self.waiting(self.env))
                t = env.now
                yield self.standBy
                self.idleTime += env.now - t
            else:
                self.waitingTime += env.now - self.job.arrtime
                t = env.now
                yield self.env.timeout(self.job.duration)
                print('done')
                self.servingTime += env.now - t
                self.jobDone += 1
                self.job = None
                department[self.service].availableStatus[self.server_id] = 1

    def waiting(self, env):
            try:
                yield env.timeout(simulation_time)

            except simpy.Interrupt as i:
                print('ready to serve')

class Department:
    def __init__(self, env, service, maxCapacity, servernum):
        self.service = service
        self.servers = [None]*servernum
        for i in range(servernum):
            self.servers[i] = Server(env, None, i, self.service)
        self.maxCapacity = maxCapacity
        self.capacity = 0
        self.full = False
        self.jobs = list()
        self.availableStatus = [None]*servernum
        for i in range(servernum):
            self.availableStatus[i] = 1

    def add_customer(self, customer):

        self.jobs.append(customer)
        self.capacity += 1
        if self.capacity == self.maxCapacity:
            self.full = True

    def push(self):
        x = sum(self.availableStatus)
        if x != 0:
            h = min(x, len(self.jobs))
            customerToServeList = np.argsort(self.availableStatus)
            for i in range(h):
                self.servers[customerToServeList[i]].job = self.jobs.pop(0)
                self.availableStatus[customerToServeList[i]] = 0
                self.capacity -= 1
                if self.full == True:
                    self.full = False

class Generator:
    def __init__(self, env, departments, job_num, lamda, mu, c):
        self.departments = departments
        self.job_num = job_num
        self.lamda = lamda
        self.mu = mu
        self.c = c
        self.jobs = list()

        env.process(self.generate_customer(env))

    def generate_customer(self, env):

        i = 1
        while True:
            job_interval = random.exponential(self.lamda)
            yield env.timeout(job_interval)

            job_duration = random.exponential(self.mu)
            job_service = random.choice(randarray)

            self.jobs.append(Customer(i, job_service, env.now, job_duration))
            print(self.jobs[0])

            if len(self.jobs) != 0:
                print(len(self.jobs), ' ', self.jobs[0].service)
                if not self.departments[self.jobs[0].service].full:
                    self.departments[self.jobs[0].service].add_customer(self.jobs.pop(0))

            for k in range(len(self.departments)):
                if len(self.departments[k].jobs) != 0:
                    self.departments[k].push()

            i += 1


env = simpy.Environment()

serviceDepartments = [None] * department_num
for i in range(department_num):
    serviceDepartments[i] = Department(env, i, maxCapacity, c)

simulationGen = Generator(env, serviceDepartments, population, lamda, mu, c)

env.run( until = simulation_time)