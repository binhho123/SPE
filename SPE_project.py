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
randarray = np.arange(1, department_num + 1, 1)

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
        self.env.process(self.serve())

    def serve(self):

        while True:
            if self.job is None:
                self.standBy = env.process(self.waiting(self.env))
                t = env.now
                yield self.standBy
                self.idleTime += env.now - t
            else:
                t = env.now
                self.waitingTime += t - self.job.arrtime
                yield self.env.timeout(self.job.duration)
                if self.service == 0:
                    self.job.service = random.choice(randarray)
                    self.job.duration = random.exponential(lamda)
                    serviceDepartments[self.job.service].add_customer(self.job)
                else:
                    feedback = random.choice([0, 1], [0.8, 0.2])
                    if feedback:
                        self.job.service = random.choice(randarray)
                        self.job.service = 0
                        entrance_department.add_customer(self.job)
                self.job = None
                self.servingTime += env.now - t
                self.jobDone += 1
                serviceDepartments[self.service].availableStatus[self.server_id] = 1

    def waiting(self, env):
            try:
                yield env.timeout(simulation_time)
            except simpy.Interrupt as i:
                pass

class Department:
    def __init__(self, env, service, maxCapacity, servernum):
        self.service = service
        self.servers = [None]*servernum
        self.servernum = servernum
        self.env = env
        for i in range(servernum):
            self.servers[i] = Server(self.env, None, i, self.service)
        self.maxCapacity = maxCapacity
        self.capacity = 0
        self.leaveNum = 0
        self.full = False
        self.jobs = list()
        self.availableStatus = [None]*servernum
        for i in range(servernum):
            self.availableStatus[i] = 1

    def add_customer(self, customer):

        customer.arrtime = self.env.now
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
    def __init__(self, env, departments, entrance_department, job_num, lamda, mu, c):
        self.departments = departments
        self.entrance_department = entrance_department
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

            self.jobs.append(Customer(i, 0, env.now, job_duration))
            print(self.jobs[0])

            if len(self.jobs) != 0:
                if not self.entrance_department.full:
                    self.entrance_department.add_customer(self.jobs.pop(0))
                else:
                    self.jobs.pop(0)
                    self.entrance_department.leaveNum += 1

            if len(self.entrance_department.jobs) != 0:
                self.entrance_department.push()

            for k in range(department_num):
                if len(self.departments[k].jobs) != 0:
                    self.departments[k].push()

            for k in range(department_num):
                for h in range(c):
                    if not self.departments[k].servers[h].standBy.triggered:
                        self.departments[k].servers[h].standBy.interrupt('customer came')

            i += 1


env = simpy.Environment()

serviceDepartments = [None] * department_num

for i in range(department_num):
    serviceDepartments[i] = Department(env, i + 1, maxCapacity, c)

entrance_department = Department(env, 0, maxCapacity, 2)

simulationGen = Generator(env, serviceDepartments, entrance_department, population, lamda, mu, c)

env.run(until = simulation_time)

served_customers = [0] * department_num
for i in range(department_num):
    for k in range(c):
        served_customers[i] += serviceDepartments[i].servers[k].jobDone

average_serving_time = [0] * department_num
for i in range(department_num):
    for k in range(c):
        average_serving_time[i] += serviceDepartments[i].servers[k].servingTime
    average_serving_time[i] /= c

average_waiting_time = [0] * department_num
for i in range(department_num):
    for k in range(c):
        average_waiting_time[i] += serviceDepartments[i].servers[k].waitingTime
    average_waiting_time[i] /= c

print(served_customers)
print(average_serving_time)
print(average_waiting_time)
