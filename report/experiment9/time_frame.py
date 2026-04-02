import csv
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import datetime as dt

base_dir = os.path.dirname(os.path.dirname(__file__)) 
ALA_e9 = os.path.join(base_dir,"experiment9","ALA_e9.csv")
iNaturalist=os.path.join(base_dir,"experiment9","iNaturalist_e9.csv")
new_flora=os.path.join(base_dir,"experiment9","new_flora_e9.csv")
prototype=os.path.join(base_dir,"experiment9","prototype_e9.csv")
withoutprototype=os.path.join(base_dir,"experiment9","WithoutPrototype_e9.csv")
filelist=[ALA_e9,iNaturalist,new_flora,prototype,withoutprototype]


for i in filelist:
    with open(i, "r", encoding="utf-8") as f:
        yearlist=[]
        frequencylist=[]
        reader = csv.reader(f)
        for row in reader:
            year=row[2][:10]
            date=year[:4]+year[5:7]+year[8:10]
            
            if (date.isdigit()):
                if int(date) in yearlist:
                    frequencylist[yearlist.index(int(date))]+=1
                else:
                    yearlist.append(int(date))
                    frequencylist.append(1)
        print(frequencylist)
        dates = [dt.datetime.strptime(str(d), "%Y%m%d") for d in yearlist]
        plt.scatter(dates, frequencylist, c="orange", marker="x")
        # 格式化横坐标为年份
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.gca().xaxis.set_major_locator(mdates.YearLocator(15))  # 每 5 年一个刻度

        plt.title("Decimal Precision of GPS Coordinates Over Time")
        plt.xlabel("Event Date")
        plt.ylabel("Frequency")
        plt.show()


