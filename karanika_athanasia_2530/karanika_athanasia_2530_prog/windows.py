import csv
import math
import os
import tkinter
import tkinter as tk
from tkinter import *
from PIL import ImageTk, Image
from tkinter import messagebox

from geopy import Nominatim
from neo4j import GraphDatabase

try:
    # python 3
    from tkinter import font as tkfont  # python 3


except ImportError:

    import tkFont as tkfont  # python 2

login = 0#eksetazoume an exei mpei kapoios xristis
current_frame = "StartPage"
username = ""
password = ""

class graph:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Fivos99!"))

    def close(self):
        self.driver.close()

    def findmindistance(self, product, loc_latitude, loc_longitude):
        with self.driver.session() as session:
            findmin = session.read_transaction(self.findmin, product, loc_latitude, loc_longitude)
            global login
            if login:
                print("loginnnn")
                global username
                find_user_products = session.write_transaction(self.find_user_products, username,product)


            print(findmin)
            return (findmin)

    @staticmethod
    def findmin(tx, product, loc_latitude, loc_longitude):
        all_results = []

        all = tx.run(
            "MATCH (n:shop) -[r]->(product{name:$product}) "  # psaxnoume gia to shop pou diatheti to product poy epithimi o user 
            "RETURN n.name ",
            product=product)
        for record in all:
            all_results.append(record.values()[0])

        print("all results for shops", all_results)

        min = math.inf

        for name in all_results:

            print("name", name)
            current = tx.run("MATCH (n:shop{name:$name}) "
                             "RETURN n.longitude, n.latitude, n.address ",
                             name=name)
            # print(current.values())

            lat_log = current.values()
            cur_latitude = [i[0] for i in lat_log][0]
            cur_longitude = [i[1] for i in lat_log][0]
            address = [i[2] for i in lat_log][0]

            print(cur_longitude, cur_latitude, address)

            distance = tx.run(
                "WITH point({x: $loc_latitude, y: $loc_longitude, crs: 'cartesian'}) AS p1, point({x: $shop_latitude, y: $shop_longitude, crs: 'cartesian'}) AS p2 "
                "RETURN distance(p1,p2) AS dist",
                shop_latitude=cur_latitude, shop_longitude=cur_longitude, loc_longitude=loc_longitude,
                loc_latitude=loc_latitude)

            cur_distance = distance.value()[0]  # vriskw tin apostasi apo to shop pou eksetazw
            print(cur_distance)
            if (cur_distance < min):
                min = cur_distance
                min_name = name
                min_address = [i[2] for i in lat_log][0]

        print(min, min_name, min_address)
        return_str = min_name + ',\n' + min_address
        return return_str


    @staticmethod
    def find_user_products(tx, username,product):

        all = tx.run("RETURN EXISTS((:user {name: $name})-[:selected]-(:product {name:$product})) ", name = username, product = product)
        out = all.values()[0];

        print(out[0])
        if not out[0]:
            relationship = tx.run("MATCH (a:user {name: $name}),(b:product {name:$product}) " 
                                "WHERE a.name = $name AND b.name = $product "
                                "CREATE(a) - [r: selected {rank : $rank}]->(b) "
                                  "RETURN r.rank", name = username, product = product,rank = 1)
            print(relationship.values())
        else:

            relationship = tx.run("MATCH ((u:user {name: $name})-[r:selected]-(p:product {name:$product})) "
                                  "SET r.rank = r.rank+1"
                                  "RETURN r.rank"
                                  , name=username, product=product)

            print(relationship.values())


    #diadikasia gia tin eggrafi
    def username_exists(self, username):  # pairnoume to username pou vazei o xristis
        # query gia na vroume an to username uparxei idi
        # query gia na vroume an to username uparxei idi
        with self.driver.session() as session:
            out = session.read_transaction(self.exists, username)
            return out

    @staticmethod
    def exists(tx, username):
        all_results = []

        all = tx.run(
            "MATCH (n:user{name : $name}) "   #psaxnoume aniparxei o user
            "RETURN n.name ", name=username)

        for record in all:
            all_results.append(record.values()[0])

        print("all results", all_results)
        if len(all_results) == 0:
            return 0
        else:
            return 1

    def add_user(self, username, password):
        print("prin add user", username)
        with self.driver.session() as session:
            new_user = session.write_transaction(self.user, username, password)



    @staticmethod
    def user(tx, username, password):
        result_add_shop = tx.run("CREATE (node:user) "
                                 "SET node.name = $name , node.password = $password"
                                 , name=username,
                                 password=password)

    # diadikasia gia tin sindesi

    def ckeck_user(self, username, password):  # pairnoume to username pou vazei o xristis
        # query gia na vroume an to username uparxei idi
        with self.driver.session() as session:
            out = session.read_transaction(self.ckeck_user_exists, username,password)

            return out

    @staticmethod
    def ckeck_user_exists(tx, username, password):
        user = []
        all = tx.run("MATCH (n:user{name : $name, password : $password}) "  # psaxnoume gia ton user
                        "RETURN n.name ", name = username, password = password)
        print("elegxoi: password", username, "username ",username, "password", password)
        for record in all:
            user.append(record.values()[0])

        print("user", user)
        if len(user) == 0:
            return 0
        else:
            return 1

    # diadikasia gia na vroume to agapimeno proion enos xristi pou ekane login

    def findfavorite(self, username):
        with self.driver.session() as session:
            out = session.read_transaction(self.favorite, username)

            return out

    @staticmethod
    def favorite(tx, username):
        out = tx.run("MATCH ((u:user {name: $name})-[r:selected]-(p:product)) "
               "RETURN p"
               , name=username)
        print(out.values())



class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        self.title_font = tkfont.Font(size=18, weight="bold")
        self.menuBar = Menu()
        self.menuBar_login = Menu()                                      #otan kanoume login theloume na exoume alles epiloges sto menu
        self.config(menu=self.menuBar)
        # File Menu
        self.connectMenu = tk.Menu(self.menuBar, tearoff=0)
        self.connectMenu_login = tk.Menu(self.menuBar_login, tearoff=0)
        self.connectMenu_login.add_separator()
        self.menuBar_login.add_cascade(label="Λογαριασμός", menu=self.connectMenu_login)

        self.connectMenu.add_separator()
        self.menuBar.add_cascade(label="Λογαριασμός", menu=self.connectMenu)

        window = tk.Frame(self)
        window.pack(side="top", fill="both", expand=True)
        self.title("BIO products")
        self.geometry("500x200")

        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, registration_form, login):
            page_name = F.__name__
            frame = F(parent=window, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")
        self.connectMenu.add_command(label="Κεντρικό μενού", command=lambda: self.show_frame("StartPage"))
        self.connectMenu.add_command(label="Δημιουργία", command=lambda: self.show_frame("registration_form"))
        self.connectMenu.add_command(label="Σύνδεση", command=lambda: self.show_frame("login"))

        self.connectMenu_login.add_command(label="Κεντρικό μενού", command=lambda: self.show_frame("StartPage"))
        self.connectMenu_login.add_command(label="Αποσύνδεση", command=lambda: self.logout())

    def show_frame(self, page_name):
        global current_frame
        if current_frame == "login" or current_frame == "registration_form" :
            self.frames[current_frame].entry_username.delete(0,END)
            self.frames[current_frame].entry_password.delete(0, END)
        '''Show a frame for the given page name'''
        current_frame = page_name
        frame = self.frames[page_name]
        frame.tkraise()
        global login
        if login == 1:
            self.config(menu=self.menuBar_login)
        else :
            self.config(menu=self.menuBar)

    def logout(self):
        global login
        login = 0
        self.config(menu=self.menuBar)



class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.dbms = graph("bolt://localhost:7687", "neo4j", "Fivos99!")
        self.controller = controller
        print("pressed")

        #########code for entry ###########
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.frame1 = tk.Frame(master=self, height=50)
        self.frame1.grid(row=0, column=0, sticky="nsew", columnspan=2)

        Grid.rowconfigure(self.frame1, 1, weight=1)

        Grid.columnconfigure(self.frame1, 0, weight=1)
        Grid.columnconfigure(self.frame1, 1, weight=1)
        Grid.columnconfigure(self.frame1, 2, weight=1)
        Grid.columnconfigure(self.frame1, 3, weight=1)
        Grid.columnconfigure(self.frame1, 4, weight=1)

        label = tkinter.Label(self.frame1, text="Προιόν ")
        label.grid(row=0, column=0, sticky="nsew", padx=10)
        self.entry = tk.Entry(self.frame1)
        self.entry.grid(row=0, column=1, sticky="nsew")
        label1 = tkinter.Label(self.frame1, text="διέυθυνση ")
        label1.grid(row=0, column=2, sticky="nsew", padx=10)
        self.entry_address = tk.Entry(self.frame1)
        self.entry_address.grid(row=0, column=3, sticky="nsew")

        sub_btn = tk.Button(self.frame1, text='Submit', command=self.submit)
        sub_btn.grid(row=0, column=4, sticky="nsew", padx=10)

        self.return_string = tk.StringVar()
        frame_result = tk.Frame(master=self.frame1, height=40, bg='#6b88fe')
        frame_result.grid(row=1, column=3, sticky="new")
        result = tk.Label(frame_result, textvariable=self.return_string)
        result.pack(side=TOP)

        tvar = tk.StringVar(value="Hi")


        #ama o xristis exei kanei login prepei na tou proteinoum proionta pou exei epileksi sto parelthon edw tha mpei to label
        global frame_rank
        frame_rank = tk.Frame(master=self.frame1, height=40)
        frame_rank.grid(row=1, column=2, sticky="new", pady = 20)
        frame_rank.pack_forget()
        global rank_label
        rank_label = tkinter.Label(frame_rank, text="Προτείνεται για εσάς ")
        rank_label.pack(side=BOTTOM)
        rank_label.pack_forget()
        #kai edw tha mpei to apotelesma sto frame_result dhladh katw apo to apotelesma
        global rankvar
        rankvar = tk.StringVar(value="Hi")
        global rank_button
        rank_button = tk.Button(frame_result, textvariable=rankvar)
        rank_button.pack(side=BOTTOM)
        rank_button.pack_forget()

        #####list for autocomplete
        self.list = []

        for root, dirs, files in os.walk("shops"):
            for file in files:
                if file.endswith(".csv"):
                    file = os.path.join("shops\\", file)
                    f = open(file, 'r', encoding='utf-8')
                    available_products = csv.reader(f, delimiter=',')
                    for product in available_products:
                        if len(product) > 0:
                            product[0] = product[0].strip()

                            if product[0] not in self.list:
                                self.list.append(product[0])

                    f.close()

        print("list", list)

        ################code for import image

        image = Image.open("./plant.gif")
        resize_image = image.resize((50, 50))

        img = ImageTk.PhotoImage(resize_image, master=parent)

        # create label and add resize image
        labelimg = Label(self.frame1, image=img, bg="blue")
        labelimg.image = img
        labelimg.grid(row=2, column=0, sticky="nsew", padx=10)

        self.image = Image.open("./background.jpg")
        self.resize_image = self.image.resize((500, 50), Image.ANTIALIAS)
        self.resize_image.master = parent
        self.resize_image.master.bind('<Configure>', self._resize_image)
        self.img = ImageTk.PhotoImage(self.resize_image, master=parent)

        # create label and add resize image
        self.labelimg = Label(self.frame1, bg="blue")
        self.labelimg.config(image=self.img)
        self.labelimg.image = self.img
        self.labelimg.grid(row=2, column=1, columnspan=4)
        #########################

        ###handlers

        self.listbox = tk.Listbox(self.frame1, width=self.entry.winfo_width(), bg='#6b88fe')
        parent.update()
        print(label.winfo_width())
        self.listbox.grid(row=1, column=1, sticky="nsew")

        self.update(self.list)
        # create bindind on the listbox onclick
        self.listbox.bind("<<ListboxSelect>>", self.fillout)
        # binding on entry box
        self.entry.bind("<KeyRelease>", self.check)

    def _resize_image(self,event):
        print("resize", self.master.winfo_width())
        new_width = self.master.winfo_width()
        new_height = self.master.winfo_height()
        self.resize_image = self.image.resize((new_width, 50))

        self.img = ImageTk.PhotoImage(self.resize_image, master=self.frame1)
        # create label and add resize image
        self.labelimg = Label(self.frame1, bg="blue")
        self.labelimg.config(image=self.img)
        #self.labelimg.image = self.img
        self.labelimg.grid(row=2, column=1, columnspan=4)



    def update(self, data):
        self.listbox.delete(0, END)
        for item in data:
            self.listbox.insert(END, item)  # add at the end of the listbox new item

    def fillout(self, event):
        # delete all in the etnry box
        self.entry.delete(0, END)
        self.entry.insert(0, self.listbox.get(ACTIVE))

        # handler for entry

    def check(self, e):
        typed = self.self.entry.get()

        # initialize data for listbox update
        if typed == "":
            data = self.list
        else:
            data = []
            for item in self.list:
                if typed.lower() in item.lower():
                    data.append(item)
        self.update(data)

    def submit(self):
        typed = self.entry.get()
        address = self.entry_address.get()
        geolocator = Nominatim(user_agent="main.py", timeout=50)
        location = geolocator.geocode(address)

        if typed not in self.list:
            messagebox.showerror("Error", "το προιόν δεν είναι διαθέσιμο")
            return
        if type(location) is type(None):
            messagebox.showerror("Error", "Η διεύθυνση δεν υπάρχει")
            return
        self.dbms = graph("bolt://localhost:7687", "neo4j", "Fivos99!")

        user_latitude = location.latitude
        user_longitude = location.longitude
        self.return_string.set(self.dbms.findmindistance(typed, user_latitude, user_longitude))

    def _quit(self):
        self.parent.quit()
        self.parent.destroy()
        exit()


class registration_form(tk.Frame):

    def __init__(self, parent, controller):

        self.dbms = graph("bolt://localhost:7687", "neo4j", "Fivos99!")
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Username", font=controller.title_font)
        label.grid(row=1, column=1, padx=20, pady=20)
        label = tk.Label(self, text="Password", font=controller.title_font)
        label.grid(row=2, column=1, padx=20, pady=20)

        self.label_already_exists = tk.Label(self, text="Το όνομα υπάρχει ήδη!", font=(5))
        self.label_already_exists.configure(foreground="red")

        self.entry_username = tk.Entry(self)
        self.entry_username.grid(row=1, column=2);
        self.entry_username.bind("<Key>", self.recover);

        self.entry_username.bind('<Return>', self.get_username)
        self.entry_password = tk.Entry(self)
        self.entry_password.grid(row=2, column=2)

        sub_btn = tk.Button(self, text='Submit', command=self.submit)
        sub_btn.grid(row=3, column=2, sticky="nsew", padx=10)

    def get_username_for_submit(self):
        if self.dbms.username_exists(self.entry_username.get()) == 0:
            print("ok")
            return 0;

    def get_username(self, event):
        if self.dbms.username_exists(self.entry_username.get()) == 0:
            print("ok")
        else:
            self.label_already_exists.grid(row=1, column=3);

    def submit(self):
        if self.get_username_for_submit() == 0:
            if len(self.entry_password.get()) != 0:
                self.dbms.add_user(self.entry_username.get(), self.entry_password.get())
                global login
                login = 1
                global username
                username = self.entry_username.get()

                print("LOGIN")
                self.controller.show_frame("StartPage")

            else:
                self.label_already_exists.grid(row=1, column=3);

    def recover(self, event):
        self.label_already_exists.grid_forget()

class login(tk.Frame):
    def __init__(self, parent, controller):
        self.dbms = graph("bolt://localhost:7687", "neo4j", "Fivos99!")
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Username", font=controller.title_font)
        label.grid(row=1, column=1, padx=20, pady=20)
        label = tk.Label(self, text="Password", font=controller.title_font)
        label.grid(row=2, column=1, padx=20, pady=20)

        self.label_exists = tk.Label(self, text="Το όνομα δεν υπάρχει!", font=(5))
        self.label_exists.configure(foreground="red")

        self.label_false_password = tk.Label(self, text="ο κωδικός είναι λανθασμένος!", font=(5))
        self.label_false_password.configure(foreground="red")

        self.entry_username = tk.Entry(self)
        self.entry_username.grid(row=1, column=2);
        self.entry_username.bind("<Key>", self.recover);

        self.entry_username.bind('<Return>', self
                                 .get_username)
        self.entry_password = tk.Entry(self)
        self.entry_password.grid(row=2, column=2)

        sub_btn = tk.Button(self, text='Submit', command=self.submit)
        sub_btn.grid(row=3, column=2, sticky="nsew", padx=10)

    def get_username_for_submit(self):
        if self.dbms.username_exists(self.entry_username.get()) == 0:
            print("den iparxei")
            return 0
        else:
            return 1

    def get_username(self, event):
        if self.dbms.username_exists(self.entry_username.get()) != 0:  # ama to onoma iparxei stin vasi
            print("ok")
        else:
            self.label_exists.grid(row=1, column=3);

    def submit(self):

        if self.get_username_for_submit() != 0:
            if len(self.entry_password.get()) != 0:  # ama to onoma iparxei stin vasi
                if self.dbms.ckeck_user(self.entry_username.get(), self.entry_password.get()) == 0:
                    self.label_false_password.grid(row=2, column=3)

                else:
                    global login
                    login = 1
                    global username
                    username = self.entry_username.get()
                    self.dbms.findfavorite(username)
                    frame_rank.grid(row=1, column=2, sticky="new", pady=20)
                    rank_label.pack(side=BOTTOM)
                    rank_button.pack(side=BOTTOM)

                    print("LOGIN")
                    self.controller.show_frame("StartPage")

        else:
            self.label_exists.grid(row=1, column=3)

    def recover(self, event):
        self.label_false_password.grid_forget()
        self.label_exists.grid_forget()

if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()
