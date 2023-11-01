import numpy
import random
import simpy

'''Pre-set parameters'''
num_customer = 10
service_time = 2
lamda = 1/6
mu = [1/5, 1/5, 1/5, 1/5, 1/5]
c = 3
leave_rate = 0.2
department_num = 3
simulation_time = 4000
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
                    self.job.duration = random.expovariate(1 / mu[1])
                    simulationGen.joblist[1].append(self.job)
                    entrance_department.availableStatus[self.server_id] = 1
                    '''Trigger add process of next queue node's department, if haven't done'''
                    if not simulationGen.select_department.no_add.triggered:
                        simulationGen.select_department.no_add.interrupt('customer came')
                    '''Trigger push process of current queue node's department, if haven't done'''
                    if not simulationGen.entrance_department.no_push.triggered:
                        simulationGen.entrance_department.no_push.interrupt('customer came')

                elif self.service == 1:
                    self.job.service = random.choices(randarray, weights =(1/3, 1/3, 1/3), k = 1)[0]
                    self.job.duration = random.expovariate(1 / mu[self.job.service - 2])
                    self.job.arrtime = self.env.now
                    simulationGen.joblist[2].append(self.job)
                    select_department.availableStatus[self.server_id] = 1
                    '''Trigger add process of next queue node's department, if haven't done'''
                    if not simulationGen.departments[self.job.service - 2].no_add.triggered:
                        simulationGen.departments[self.job.service - 2].no_add.interrupt('customer came')
                    '''Trigger push process of current queue node's department, if haven't done'''
                    if not simulationGen.select_department.no_push.triggered:
                        simulationGen.select_department.no_push.interrupt('customer came')

                else:
                    feedback = random.choices([0, 1], weights =(1-feedBack_rate , feedBack_rate), k = 1)[0]
                    if feedback == 1:
                        s = self.job.service
                        self.job.service = 0
                        self.job.arrtime = self.env.now
                        '''random task duration base on mu 1'''
                        self.job.duration = random.expovariate(1 / mu[1])
                        simulationGen.joblist[1].append(self.job)
                        '''Trigger add process of next queue node's department, if haven't done'''
                        if not simulationGen.select_department.no_push.triggered:
                            simulationGen.select_department.no_push.interrupt('customer came')
                        '''Trigger push process of current queue node's department, if haven't done'''
                        if not simulationGen.departments[s - 2].no_add.triggered:
                            simulationGen.departments[s - 2].no_add.interrupt('customer came')
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
        self.leaveNum = 0
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
            '''if department queue not full and there is a waiting customer, add customer to queue'''
            if len(simulationGen.joblist[self.queue_no]) != 0:
                if not self.full:
                    self.jobs.append(simulationGen.joblist[self.queue_no].pop(0))
                    self.capacity += 1
                    if self.capacity == self.maxCapacity:
                        self.full = True
                    print(self.service,'add customer',self.jobs[self.capacity-1].id,'need',self.jobs[self.capacity-1].service,'at',env.now)
                    if not self.no_push.triggered:
                        self.no_push.interrupt('customer came')
                else:
                    print('customer', simulationGen.joblist[self.queue_no][0], 'left', self.queue_no)
                    simulationGen.joblist[self.queue_no].pop(0)
                    self.leaveNum += 1
                    if not self.no_push.triggered:
                        self.no_push.interrupt('customer came')
            else:
                self.no_add = env.process(self.dont_add(self.env))
                yield self.no_add

    def push(self):

        while True:
            '''if department queue not full and there is a waiting customer, add customer to queue'''
            if self.capacity != 0 and 1 in self.availableStatus:
                x = sum(self.availableStatus)
                h = min(x, len(self.jobs))
                customerToServeList = numpy.argsort(self.availableStatus)[::-1]
                for i in range(h):
                    self.servers[customerToServeList[i]].job = self.jobs.pop(0)
                    if not self.servers[customerToServeList[i]].standBy.triggered:
                        self.servers[customerToServeList[i]].standBy.interrupt('customer came')
                    print(self.service, 'push', self.servers[customerToServeList[i]].job.id,'to',customerToServeList[i] ,'at', env.now)
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
            job_interval = numpy.random.poisson(1 / self.lamda, size = None)
            yield env.timeout(job_interval)

            job_duration = random.expovariate(1 / self.mu [0])

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
select_department = Department(env, 1, maxCapacity, c, 1)
'''1st queue node with 1 department, 1 servers'''
entrance_department = Department(env, 0, maxCapacity, c, 0)

simulationGen = Generator(env, serviceDepartments, select_department, entrance_department, population, lamda, mu, c)

env.run(until = simulation_time)

served_customers_node1 = [0]
served_customers_node2 = [0]
served_customers_node3 = [0] * department_num
served_customers = [served_customers_node1, served_customers_node2, served_customers_node3]

for i in range(3):
    served_customers_node1[0] += entrance_department.servers[i].jobDone

for i in range(3):
    served_customers_node2[0] += select_department.servers[i].jobDone

for i in range(department_num):
    for k in range(c):
        served_customers_node3[i] += serviceDepartments[i].servers[k].jobDone

average_serving_time_node1 = [0]
average_serving_time_node2 = [0]
average_serving_time_node3 = [0] * department_num
average_serving_time = [average_serving_time_node1, average_serving_time_node2, average_serving_time_node3]

for k in range(3):
    average_serving_time_node1[0] += entrance_department.servers[k].servingTime
average_serving_time_node1[0] /= 3
average_serving_time_node1[0] /= served_customers_node2[0] + 1e-9

for k in range(3):
    average_serving_time_node2[0] += select_department.servers[k].servingTime
average_serving_time_node2[0] /= 3
average_serving_time_node2[0] /= served_customers_node2[0] + 1e-9

for i in range(department_num):
    for k in range(c):
        average_serving_time_node3[i] += serviceDepartments[i].servers[k].servingTime
    average_serving_time_node3[i] /= c
    average_serving_time_node3[i] /= served_customers_node3[i] + 1e-9

average_waiting_time_node1 = [0]
average_waiting_time_node2 = [0]
average_waiting_time_node3 = [0] * department_num
average_waiting_time = [average_waiting_time_node1, average_waiting_time_node2, average_waiting_time_node3]

for k in range(c):
    average_waiting_time_node1[0] += entrance_department.servers[k].waitingTime
average_waiting_time_node1[0] /= c
average_waiting_time_node1[0] /= served_customers_node2[0] + 1e-9

for k in range(c):
    average_waiting_time_node2[0] += select_department.servers[k].waitingTime
average_waiting_time_node2[0] /= c
average_waiting_time_node2[0] /= served_customers_node2[0] + 1e-9

for i in range(department_num):
    for k in range(c):
        average_waiting_time_node3[i] += serviceDepartments[i].servers[k].waitingTime
    average_waiting_time_node3[i] /= c
    average_waiting_time_node3[i] /= served_customers_node3[i] + 1e-9

print(served_customers)
print(average_serving_time)
print(average_waiting_time)
