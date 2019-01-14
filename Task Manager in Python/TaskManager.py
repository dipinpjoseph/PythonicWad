import os
import subprocess
import threading
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import time
from functools import partial
import traceback
import multiprocessing

class TaskManager:

    def __init__(self,root):

        self.startProcessPid  = 10000
        self.processToStart  = ""

        self.root=root
        self.root.title("Enhanced Task Manager")
        self.root.geometry("850x460")
        root.configure(background='white')
        self.root.resizable(0,0)

        self.topFrame = Frame(self.root,bg="black")
        self.topFrame.pack(side=TOP,fill="both")
        self.leftFrame = Frame(self.root,bg="white")
        self.leftFrame.pack(side=LEFT,expand=1,fill="both")


        self.rightFrame = Frame(self.root)
        self.rightFrame.pack(side=RIGHT,fill="both")

        self.treeHeadings =  ["pid", "name","state","ppid","priority","vsize(kiloBytes)","Avg CPU %","%MEM"]

        self.treeView = ttk.Treeview(self.leftFrame,columns=self.treeHeadings, show="headings",height = 20)

        self.scrollBar = ttk.Scrollbar(self.leftFrame,orient="vertical",command=self.treeView.yview)
        self.treeView.configure(yscrollcommand=self.scrollBar.set)

        for col in self.treeHeadings:
            self.treeView.heading(col, text=col.title())

        self.treeView.column("pid", width=70)
        self.treeView.column("name", width=200)
        self.treeView.column("state", width=50)
        self.treeView.column("ppid", width=70)
        self.treeView.column("priority", width=50)
        self.treeView.column("vsize(kiloBytes)", width=100)
        self.treeView.column("Avg CPU %", width=70)
        self.treeView.column("%MEM", width=70)

        #self.treeView["columns"] = ["pid", "name","ppid"]

        #self.treeView.heading("pid", text="PID")

        self.treeView.grid(row =0,column =0,columnspan = 3)
        self.scrollBar.grid(column=4, row=0, sticky='ns')
        Label(self.topFrame, text="All running Process details").grid(row=0,  sticky=N, padx=10, pady=10)

        Label(self.rightFrame, text="Name of Process").grid(row=0, column=1, padx=10, pady=10)
        pidOrNameToStart = StringVar()
        Entry(self.rightFrame, textvariable=pidOrNameToStart, bd=5).grid(row=1, column=1, sticky=W)
        Button(self.rightFrame, text="START", command=partial(self.startProcess, pidOrNameToStart)).grid(row=2, column=1, sticky=E)

        Label(self.rightFrame, text="PID of Process").grid(row=3, column=1,  padx=10, pady=10)
        pidOrNameToStop = StringVar()
        Entry(self.rightFrame, textvariable=pidOrNameToStop, bd=5).grid(row=4, column=1, sticky=E)
        Button(self.rightFrame, text="KILL", command=partial(self.killProcess, pidOrNameToStop)).grid(row=5, column=1, sticky=E)

        Label(self.rightFrame, text="Name of Service").grid(row=6, column=1,  padx=10, pady=10)
        nameOfService = StringVar()
        Entry(self.rightFrame, textvariable=nameOfService, bd=5).grid(row=7, column=1, sticky=W)
        Button(self.rightFrame, text="START", command=partial(self.startService, nameOfService)).grid(row=8, column=1, sticky=W)

        Button(self.rightFrame, text="STOP", command=partial(self.stopService, nameOfService)).grid(row=8, column=1, sticky=E)

        #self.leftFrame.pack_forget()
        self.listingAllProcess()

    def child(self):
        try:
            pp = subprocess.Popen([self.processToStart], close_fds=True)
            print("Child process PID - ", pp.pid)
            self.startProcessPid = pp.pid
            #print("Inside - ",self.startProcessPid)
        except Exception as e:

            traceback.print_tb(e.__traceback__)

    def parent(self):
        try:
            cc = multiprocessing.Process(name='child', target=self.child)
            cc.daemon = False
            cc.start()
        except Exception as e:

            traceback.print_tb(e.__traceback__)


    def startProcess(self,processNameToStart):
        try :

            self.processToStart = processNameToStart.get()
            d = multiprocessing.Process(name='parent', target=self.parent)
            d.daemon = False
            d.start()
            time.sleep(1)
            d.terminate()

            print(processNameToStart.get())
            #output = subprocess.Popen([processNameToStart.get(), "&"], close_fds=True)

            pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
            print("Start process Pid - ",self.startProcessPid)
           # if str(self.startProcessPid) in pids:
            messagebox.showinfo("Title", "Process Created")

            #else:
               # messagebox.showinfo("Title", "Process Creation Failed")
        except:
            messagebox.showerror("Exception", "Process could not be found ")


    def killProcess(self,processNameorPid):
        try :
            processPid = "";
            processNameorPid = processNameorPid.get()
            if(processNameorPid.isdigit()):
                processPid = processNameorPid

            killStatus = subprocess.Popen([ "kill", "-9", str(processPid)], close_fds=True)

            time.sleep(1)
            pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

            if str(processPid) in pids:
                messagebox.showinfo("Title", "Process kill failed")

            else:
                messagebox.showinfo("Title", "Process killed")
        except:
            messagebox.showerror("Exception", "Process could not be found ")


    def startService(self,serviceName):
        try :
            subprocess.Popen(["service" , serviceName.get(), "start"], stdout=subprocess.PIPE,
                                             close_fds=True)
            serviceStatus = subprocess.Popen(["service" , serviceName.get(), "status"], stdout=subprocess.PIPE,
                                             close_fds=True)
            #print(str(serviceStatus.stdout.read()))
            time.sleep(2)
            lineList = serviceStatus.stdout.readlines()
            print(str(lineList[len(lineList)-1]))
            if (str(lineList[len(lineList)-1]).__contains__("Starting")|str(lineList[len(lineList)-1]).__contains__("Started")):
                print(str(serviceStatus.stdout.read()))
                messagebox.showinfo("Title", "Service Started")
            else:
                messagebox.showinfo("Title","Service Starting failed")
        except :
            messagebox.showerror("Exception", "Service could not be found ")


    def stopService(self,serviceName):
        try :
            subprocess.Popen(["service" , serviceName.get(), "stop"], stdout=subprocess.PIPE,
                                             close_fds=True)
            serviceStatus = subprocess.Popen(["service", serviceName.get(), "status"], stdout=subprocess.PIPE,
                                             close_fds=True)
            # print(str(serviceStatus.stdout.read()))
            time.sleep(2)
            lineList = serviceStatus.stdout.readlines()
            print(str(lineList[len(lineList) - 1]))
            if (str(lineList[len(lineList) - 1]).__contains__("Stopping") | str(lineList[len(lineList) - 1]).__contains__(
                    "Stopped")):
                print(str(serviceStatus.stdout.read()))
                messagebox.showinfo("Title","Service Stopped")
            else:
                messagebox.showinfo("Title","Service Stopping failed")
        except:
            messagebox.showerror("Exception", "Service could not be found ")


    def listingAllProcess(self):
        try:
            memDetails = (open(os.path.join('/proc', 'meminfo'), 'r').read()).splitlines()
            print(memDetails[0].split()[1])

            Label(self.topFrame, text=memDetails[0]).grid(row=0, column=0, padx=10, pady=10)
            Label(self.topFrame, text=memDetails[1]).grid(row=0, column=1, padx=10, pady=10)
            Label(self.topFrame, text=memDetails[3]).grid(row=0, column=2, padx=10, pady=10)
            Label(self.topFrame, text=memDetails[4]).grid(row=0, column=3, padx=10, pady=10)

            cpuDetailsOld = (open(os.path.join('/proc', 'stat'), 'r').readline()).split()
            prevNum = (int(cpuDetailsOld[1]) + int(cpuDetailsOld[2]) + int(cpuDetailsOld[3]))
            prevTotal = int(prevNum) + int(cpuDetailsOld[4]) + int(cpuDetailsOld[5])
            print(cpuDetailsOld)
            print(prevTotal)
            time.sleep(4)
            cpuDetailsNew = (open(os.path.join('/proc', 'stat'), 'r').readline()).split()
            curNum = (int(cpuDetailsNew[1]) + int(cpuDetailsNew[2]) + int(cpuDetailsNew[3]))
            curTotal = int(prevNum) + int(cpuDetailsNew[4]) + int(cpuDetailsNew[5])

            totald = curTotal - prevTotal

            idled = curNum - prevNum
            try :
                percentage = (float(idled) / float(totald)) * 100
                print (percentage)
                Label(self.topFrame, text="CPU Usage : " + str(round(percentage, 2)) + "%").grid(row=0, column=4,
                                                                                                 padx=10, pady=10)
            except Exception as e:

                traceback.print_tb(e.__traceback__)




            self.pidDetailsList = []
            self.pids = []

            pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

            for pid in pids:
                try:
                    self.pidDetailsList.append((open(os.path.join('/proc', pid, 'stat'), 'r').read()) + (
                        open(os.path.join('/proc', pid, 'statm'), 'r').read()))
                except:  # process has already terminated
                    continue

            self.treeView.delete(*self.treeView.get_children())


            for pidDetails in self.pidDetailsList:

                #print(pidDetails)

                singlePidList = pidDetails.split()
                pid = singlePidList[0]
                name = singlePidList[1].replace("(", "")
                name = name.replace(")", "")
                state = singlePidList[2]
                ppid = singlePidList[3]
                priority = singlePidList[17]
                utime = singlePidList[13]
                stime = singlePidList[14]
                startTime = singlePidList[21]
                vsize = singlePidList[22]
                vsize = int(int(vsize)/1000)
                resSize = singlePidList[53]
                resSizeShared = singlePidList[54]
                perMem = ((int(resSize)+int(resSizeShared))/(int(memDetails[0].split()[1])-int(memDetails[1].split()[1])))*100
                cpuPerProcess = ((float(utime)+float(stime))/float(curTotal))*100
                print(pid,singlePidList[53],singlePidList[54])
                #print(perMem)
                try :

                    self.treeView.insert("", 'end', values=(pid, name,state, ppid, priority, str(vsize), str(round(cpuPerProcess,2)),str(round(perMem,2))))
                except Exception as e:

                     traceback.print_tb(e.__traceback__)
                #Label(self.leftFrame, text=name).pack()
                #print(pid, "     ", name, "    ", state, "    ", ppid, "   ", priority, "   ", startTime)
                #self.listbox.insert(END, name+pid+ppid+state+priority+startTime+"   "+vsize+"   "+resSize)

            #

            self.root.after(9000, self.listingAllProcess)

        except Exception as e :

            traceback.print_tb(e.__traceback__)


def uiCreation():
    root = Tk()
    taskManager = TaskManager(root)
    root.mainloop()


uiCreation()

print("Check")
