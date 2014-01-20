from Tkinter import *
import ConfigParser

class Application(Frame):
    def say_hi(self):
        print "hi there, everyone!"

    def write_config(self):
        with open("config.ini", 'wb') as configfile:
            self.config.write(configfile)

    def set_accExp(self, val):
        self.config.set('sec1', 'accExp', val)

    def set_accCoe(self, val):
        self.config.set('sec1', 'accCoe', val)

    def createWidgets(self):
        #quit button
        self.QUIT = Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"]   = "red"
        self.QUIT["command"] =  self.quit
        self.QUIT.pack({"side": "top"})

        #apply settings button
        self.apply_settings = Button(self)
        self.apply_settings["text"] = "Apply Setings"
        self.apply_settings["command"] = self.write_config
        self.apply_settings.pack({"side": "bottom"})

        #Accelerator exponent
        self.acceleration_exponent = Scale(self, from_=1, to=2, orient=HORIZONTAL, resolution=.01, command=self.set_accExp)
        self.acceleration_exponent.pack({"side": "top"})

        #Accelerator coefficient 
        self.acceleration_coefficient = Scale(self, from_=-10, to=10, orient=HORIZONTAL, resolution=.1, command=self.set_accCoe)
        self.acceleration_coefficient.pack({"side": "top"})

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()
        self.config = ConfigParser.RawConfigParser()
        self.config.add_section('sec1')
        self.config.set('sec1', 'foo', 'bar')


root = Tk()
app = Application(master=root)
app.mainloop()
root.destroy()
