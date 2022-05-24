import sounddevice as sd
import numpy as np
import pandas as pd
from tkinter import *
from pandastable import Table, TableModel

deviceList = sd.query_devices()

names = [deviceList[x]['name'] for x in np.arange(0,len(deviceList))]
chans_in =  [deviceList[x]['max_input_channels'] for x in np.arange(0,len(deviceList))]
ids = np.arange(0,len(deviceList))
df = pd.DataFrame({"device_id": ids, "name": names,"chans_in": chans_in})

class TestApp(Frame):
        """Basic test frame for the table"""
        def __init__(self, parent=None):
            self.parent = parent
            Frame.__init__(self)
            self.main = self.master
            self.main.geometry('600x400+200+100')
            self.main.title('Audio Device List')
            f = Frame(self.main)
            f.pack(fill=BOTH,expand=1)
            #df = TableModel.getSampleData()
            self.table = pt = Table(f, dataframe=df,
                                    showtoolbar=True, showstatusbar=True)
            pt.show()
            return

app = TestApp()
#launch the app
app.mainloop()
