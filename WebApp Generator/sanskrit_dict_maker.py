import mysql.connector

sdb = mysql.connector.connect(
          host="localhost",
            user="dipin",
              password="1712",
                database="sanskrit"
                )

cursor = sdb.cursor()

cursor.execute("SELECT * from tbl_all_synset")

#dat = cursor.fetchall()
dat = cursor.fetchone()
print(dat[2].decode("utf-8"))
print(dat[3].decode("utf-8"))

#for x in cursor:
#      print(x)

with open('sanskrit_static.html', 'r') as file :
    filedata = file.read()
    print(filedata)

#    for eachdat in dat:
 #       print(eachdat.head)

with open(str(dat[1])+".html","w") as wf:
    filedata = filedata.replace("##title@@",str(dat[2]))
    wf.write(filedata)
