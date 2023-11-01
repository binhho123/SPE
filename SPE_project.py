import numpy
import random
import simpy

num_customer = 10
service_time = 2
lamda = 1/6
mu = 1/20
c = 5
leave_rate = 0.2
department_num = 4
simulation_time = 100
maxCapacity = 100
population = 10000
randarray = numpy.arange(0+2, department_num + 2, 1)
queue_note = 3

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
                print(self.server_id,'process', self.job.id,'at',env.now)
                t = env.now
                self.waitingTime += t - self.job.arrtime
                yield self.env.timeout(self.job.duration)
                if self.service == 0:
                    self.job.service = 1
                    self.job.arrtime = self.env.now
                    self.job.duration = random.expovariate(mu)
                    simulationGen.joblist[1].append(self.job)
                    entrance_department.availableStatus[self.server_id] = 1

                elif self.service == 1:
                    self.job.service = random.choices(randarray, weights =(25, 25, 25, 25), k = 1)[0]
                    self.job.duration = random.expovariate(mu)
                    self.job.arrtime = self.env.now
                    simulationGen.joblist[2].append(self.job)
                    select_department.availableStatus[self.server_id] = 1

                else:
                    feedback = random.choices([0, 1], weights =(10, 90), k = 1)[0]
                    if feedback == 1:
                        self.job.service = 0
                        self.job.arrtime = self.env.now
                        self.job.duration = random.expovariate(mu)
                        simulationGen.joblist[0].append(self.job)
                    serviceDepartments[self.service - 2].availableStatus[self.server_id] = 1

                print(self.service, 'finish',self.job.id,'at',env.now)
                self.job = None
                self.servingTime += env.now - t
                self.jobDone += 1

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
        self.hold = None
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
        print(self.service,'add customer',customer.id)

    def push(self):
        x = sum(self.availableStatus)
        if x != 0:
            h = min(x, len(self.jobs))
            customerToServeList = numpy.argsort(self.availableStatus)
            for i in range(h):
                self.servers[customerToServeList[i]].job = self.jobs.pop(0)
                if not self.servers[customerToServeList[i]].standBy.triggered:
                    self.servers[customerToServeList[i]].standBy.interrupt('customer came')
                print('queue', self.service, 'push', self.servers[customerToServeList[i]].job.id,'at', env.now)
                self.availableStatus[customerToServeList[i]] = 0
                self.capacity -= 1
                if self.full == True:
                    self.full == False

class Generator:
    def __init__(self, env, departments, select_department, entrance_department, job_num, lamda, mu, c):
        self.env = env
        self.departments = departments
        self.select_department = select_department
        self.entrance_department = entrance_department
        self.job_num = job_num
        self.lamda = lamda
        self.mu = mu
        self.c = c
        self.joblist = list()
        for i in range(queue_note):
            self.joblist.append(list())
        self.env.process(self.generate_customer(self.env))

    def generate_customer(self, env):

        i = 1
        while True:
            job_interval = random.expovariate(self.lamda)
            yield env.timeout(job_interval)

            job_duration = random.expovariate(self.mu)

            self.joblist[0].append(Customer(i, 0, env.now, job_duration))
            print(self.joblist[0][0])

            if len(self.joblist[0]) != 0:
                if not self.entrance_department.full:
                    self.entrance_department.add_customer(self.joblist[0].pop(0))
            if len(self.joblist[1]) != 0:
                if not self.select_department.full:
                    self.select_department.add_customer(self.joblist[1].pop(0))
            if len(self.joblist[2]) != 0:
                if not self.departments[self.joblist[2][0].service - 2].full:
                    self.departments[self.joblist[2][0].service - 2].add_customer(self.joblist[2].pop(0))

            if len(self.entrance_department.jobs) != 0:
                self.entrance_department.push()
            if len(self.select_department.jobs) != 0:
                self.select_department.push()
            for k in range(department_num):
                if len(self.departments[k].jobs) != 0:
                    self.departments[k].push()

            i += 1

env = simpy.Environment()

serviceDepartments = [None] * department_num
for i in range(department_num):
    serviceDepartments[i] = Department(env, i + 2, maxCapacity, c)
select_department = Department(env, 1, maxCapacity, 3)
entrance_department = Department(env, 0, maxCapacity, 1)
simulationGen = Generator(env, serviceDepartments, select_department, entrance_department, population, lamda, mu, c)

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
