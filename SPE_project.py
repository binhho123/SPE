import numpy
import random
import simpy

'''Pre-set parameters'''
num_customer = 10
service_time = 2
lamda = 1/6
mu = 1/20
c = 3
leave_rate = 0.2
department_num = 4
simulation_time = 100
maxCapacity = 100
population = 10000
randarray = numpy.arange(0+2, department_num + 2, 1)
feedBack_rate = 0.2
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
                '''If there is no customer to serve, server goes idle'''
                self.standBy = env.process(self.waiting(self.env))
                t = env.now
                yield self.standBy
                self.idleTime += env.now - t

            else:
                '''Serving customer'''
                print(self.server_id,'of',self.service,'process', self.job.id,'at',env.now)
                t = env.now
                self.waitingTime += t - self.job.arrtime
                yield self.env.timeout(self.job.duration)

                '''Dialling customer to next queue node'''
                if self.service == 0:
                    self.job.service = 1
                    self.job.arrtime = self.env.now
                    self.job.duration = random.expovariate(mu)
                    simulationGen.joblist[1].append(self.job)
                    entrance_department.availableStatus[self.server_id] = 1
                    if not simulationGen.select_department.no_add.triggered:
                        simulationGen.select_department.no_add.interrupt('customer came')

                elif self.service == 1:
                    self.job.service = random.choices(randarray, weights =(25, 25, 25, 25), k = 1)[0]
                    self.job.duration = random.expovariate(mu)
                    self.job.arrtime = self.env.now
                    simulationGen.joblist[2].append(self.job)
                    select_department.availableStatus[self.server_id] = 1
                    if not simulationGen.departments[self.job.service - 2].no_add.triggered:
                        simulationGen.departments[self.job.service - 2].no_add.interrupt('customer came')

                else:
                    feedback = random.choices([0, 1], weights =(1-feedBack_rate , feedBack_rate), k = 1)[0]
                    if feedback == 1:
                        self.job.service = 0
                        self.job.arrtime = self.env.now
                        self.job.duration = random.expovariate(mu)
                        simulationGen.joblist[1].append(self.job)
                        if not simulationGen.entrance_department.no_add.triggered:
                            simulationGen.entrance_department.no_add.interrupt('customer came')
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
    def __init__(self, env, service, maxCapacity, servernum, queue_no):
        self.queue_no = queue_no
        self.service = service
        self.servers = [None]*servernum
        self.servernum = servernum
        self.env = env
        for i in range(servernum):
            self.servers[i] = Server(self.env, None, i, self.service)
        self.maxCapacity = maxCapacity
        self.capacity = 0
        #self.leaveNum = 0
        self.full = False
        self.no_add = None
        self.no_push = None
        self.jobs = list()
        self.availableStatus = [None]*servernum
        for i in range(servernum):
            self.availableStatus[i] = 1
        self.env.process(self.push())
        self.env.process(self.add_customer())

    def add_customer(self):
        while True:
            '''Add customer to queue'''
            if not self.full and len(simulationGen.joblist[self.queue_no]) != 0:
                self.jobs.append(simulationGen.joblist[self.queue_no].pop(0))
                self.capacity += 1
                if self.capacity == self.maxCapacity:
                    self.full = True
                print(self.service,'add customer',self.jobs[0].id,'at',env.now)
                if not self.no_push.triggered:
                    self.no_push.interrupt('customer came')
            else:
                self.no_add = env.process(self.dont_add(self.env))
                yield self.no_add
    def push(self):

        '''Push customer to available servers to be served'''
        while True:
            if self.capacity != 0 and 1 in self.availableStatus:
                x = sum(self.availableStatus)
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
                    if not self.no_add.triggered:
                        self.no_add.interrupt('customer came')
            else:
                self.no_push = env.process(self.dont_push(self.env))
                yield self.no_push

    def dont_push(self, env):
        try:
            yield env.timeout(simulation_time)
        except simpy.Interrupt as i:
            pass

    def dont_add(self, env):
        try:
            yield env.timeout(simulation_time)
        except simpy.Interrupt as i:
            pass

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

            '''Add customer from waited lists to corresponding queue nodes'''
            if len(self.joblist[0]) != 0:
                if not self.entrance_department.no_add.triggered:
                        self.entrance_department.no_add.interrupt('customer came')

            '''increase customer count'''
            i += 1

env = simpy.Environment()

'''3rd queue node with 4 service departments, each has 3 servers'''
serviceDepartments = [None] * department_num
for i in range(department_num):
    serviceDepartments[i] = Department(env, i + 2, maxCapacity, c, 2)
'''2nd queue node with 1 department, 3 servers for service department selection'''
select_department = Department(env, 1, maxCapacity, 3, 1)
'''1st queue node with 1 department, 1 servers'''
entrance_department = Department(env, 0, maxCapacity, 1, 0)

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
