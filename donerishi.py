import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import hashlib, csv, os, random
from datetime import datetime, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
# -------------------- USER MANAGEMENT --------------------
USERS_FILE = "users.csv"
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["username","password"])
    with open(USERS_FILE,'r',newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0]==username:
                return False
    with open(USERS_FILE,'a',newline='') as f:
        writer = csv.writer(f)
        writer.writerow([username, hash_password(password)])
    return True

def validate_login(username,password):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE,'r',newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0]==username and row[1]==hash_password(password):
                return True
    return False

# -------------------- MEALS DATABASE --------------------
MEALS = {
    'breakfast': [
        ("Ragi idli + sambhar + fruit", 350, 10, 60, 6, {"vegetarian", "south"}),
        ("Ragi dosa + sambar + coconut chutney", 380, 8, 58, 10, {"vegetarian", "south"}),
        ("Oats upma + curd + fruit", 360, 12, 50, 8, {"vegetarian"}),
        ("Millet porridge + nuts", 320, 8, 40, 12, {"vegetarian", "south"}),
        ("Two boiled eggs + vegetable toast", 300, 18, 25, 12, {"omnivore"}),
        ("Poha + peanuts + curd", 340, 10, 55, 9, {"vegetarian", "south"}),
    ],
    'lunch': [
        ("Brown rice + dal + vegetable curry + salad", 650, 18, 95, 12, {"vegetarian", "rice"}),
        ("White rice + sambar + rasam + veg", 700, 16, 110, 10, {"vegetarian", "rice", "south"}),
        ("Quinoa bowl + chickpeas + salad", 600, 22, 70, 14, {"vegetarian"}),
        ("Grilled chicken + brown rice + veg salad", 700, 40, 80, 14, {"omnivore", "rice"}),
        ("Chapati (2) + sabzi + curd", 600, 18, 70, 18, {"vegetarian"}),
    ],
    'snack': [
        ("Fruit bowl + a handful of nuts", 200, 5, 28, 10, {"vegetarian"}),
        ("Sprout salad", 180, 12, 20, 6, {"vegetarian"}),
        ("Buttermilk + cucumber sticks", 120, 5, 12, 4, {"vegetarian"}),
        ("Greek yogurt + berries", 180, 12, 20, 6, {"vegetarian"}),
    ],
    'dinner': [
        ("Mixed vegetable soup + millet dosa", 420, 12, 50, 12, {"vegetarian", "south"}),
        ("Grilled fish + steamed veg + salad", 450, 35, 20, 18, {"omnivore"}),
        ("Vegetable stir-fry + tofu + small portion of rice", 480, 20, 55, 15, {"vegetarian", "rice"}),
        ("Ragi roti + dal + salad", 420, 15, 50, 10, {"vegetarian", "south"}),
    ]
}

# -------------------- DIET HELPERS --------------------
def bmr_mifflin_st_jeor(weight,height,age,gender):
    return 10*weight + 6.25*height - 5*age + (5 if gender=='M' else -161)

def activity_multiplier(level):
    return {'sedentary':1.2,'light':1.375,'moderate':1.55,'active':1.725}.get(level,1.375)

def target_calories(profile):
    bmr = bmr_mifflin_st_jeor(profile['weight'], profile['height'], profile['age'], profile['gender'])
    tdee = bmr * activity_multiplier(profile['activity'])
    if profile['goal']=='lose': return max(1200,int(tdee-400))
    elif profile['goal']=='gain': return int(tdee+300)
    return int(tdee)

def filter_meals(meal_list, profile, mandatory_tag=None):
    results=[]
    for name,kcal,p,c,f,tags in meal_list:
        if profile['pref']=='vegetarian' and 'omnivore' in tags: continue
        if profile['pref']=='vegan' and ('egg' in name.lower() or 'curd' in name.lower() or 'milk' in name.lower()): continue
        if profile.get('diabetic',False) and c>90: continue
        if mandatory_tag and mandatory_tag not in tags: continue
        results.append((name,kcal,p,c,f,tags))
    return results

def pick_meal(slot, profile, mandatory_tag=None):
    pool = filter_meals(MEALS[slot], profile, mandatory_tag)
    if not pool: pool = MEALS[slot]
    return random.choice(pool)

def generate_plan(profile):
    plan=[]
    target_kcal = target_calories(profile)
    for d in range(profile['days']):
        day_date = (datetime.now()+timedelta(days=d)).date()
        lunch_tag = 'rice' if profile['one_rice_per_day'] else None
        breakfast = pick_meal('breakfast', profile)
        lunch = pick_meal('lunch', profile, lunch_tag)
        snack = pick_meal('snack', profile)
        dinner = pick_meal('dinner', profile)
        total = breakfast[1]+lunch[1]+snack[1]+dinner[1]
        note=""
        if total>target_kcal+200: note="Calories exceed target!"
        elif total<target_kcal-300: note="Calories below target!"
        plan.append({'date':str(day_date),'breakfast':breakfast[0],'lunch':lunch[0],'snack':snack[0],'dinner':dinner[0],'total_kcal':total,'note':note,'macros':(breakfast[2]+lunch[2]+snack[2]+dinner[2],breakfast[3]+lunch[3]+snack[3]+dinner[3],breakfast[4]+lunch[4]+snack[4]+dinner[4])})
    return plan

# -------------------- AUTH WINDOW --------------------
class AuthWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Health Tech And Well-Being Login/Register")
        self.geometry("400x300")
        self.configure(bg="#f5f5f5")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Welcome to Ayurvedic Diet", font=("Helvetica",16,"bold"), bg="#f5f5f5").pack(pady=10)
        frame = tk.Frame(self, bg="#f5f5f5")
        frame.pack(pady=10)

        tk.Label(frame, text="Username:", bg="#f5f5f5").grid(row=0, column=0, sticky='w', pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.username_var).grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Password:", bg="#f5f5f5").grid(row=1, column=0, sticky='w', pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.password_var, show="*").grid(row=1, column=1, pady=5)

        ttk.Button(self, text="Login", command=self.login_user).pack(pady=5)
        ttk.Button(self, text="Register", command=self.register_user).pack(pady=5)

    def login_user(self):
        u = self.username_var.get().strip()
        p = self.password_var.get().strip()
        if validate_login(u,p):
            messagebox.showinfo("Login", "Login Successful!")
            self.destroy()
            app = DietMateApp(u)
            app.mainloop()
        else:
            messagebox.showerror("Error", "Invalid credentials!")

    def register_user(self):
        u = self.username_var.get().strip()
        p = self.password_var.get().strip()
        if not u or not p:
            messagebox.showwarning("Input", "Enter both username and password!")
            return
        if register_user(u,p):
            messagebox.showinfo("Success","User registered! You can login now.")
        else:
            messagebox.showerror("Error","Username already exists!")

# -------------------- DIET APP --------------------
class DietMateApp(tk.Tk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title(f"DietMate: {username}")
        self.geometry("1000x650")
        self.configure(bg="#f5f5f5")
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#4CAF50", foreground="white")
        style.configure("Treeview", font=("Helvetica", 10), rowheight=25)

        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Profile Tab
        profile_frame = tk.Frame(notebook, bg="#e6f2ff")
        notebook.add(profile_frame,text="Profile")
        self.entries={}
        labels = ["Name","Age","Gender","Weight(kg)","Height(cm)","Activity","Goal","Plan Days"]
        defaults = [self.username,25,"M",60,165,"light","maintain",7]
        for i,(label,default) in enumerate(zip(labels,defaults)):
            tk.Label(profile_frame,text=label+":",bg="#e6f2ff").grid(row=i,column=0,sticky='w',padx=10,pady=5)
            if label=="Gender": var=tk.StringVar(value=default);self.entries[label]=var;ttk.Combobox(profile_frame,values=["M","F"],textvariable=var,state='readonly').grid(row=i,column=1)
            elif label=="Activity": var=tk.StringVar(value=default);self.entries[label]=var;ttk.Combobox(profile_frame,values=["sedentary","light","moderate","active"],textvariable=var,state='readonly').grid(row=i,column=1)
            elif label=="Goal": var=tk.StringVar(value=default);self.entries[label]=var;ttk.Combobox(profile_frame,values=["lose","maintain","gain"],textvariable=var,state='readonly').grid(row=i,column=1)
            else: var=tk.StringVar(value=str(default));self.entries[label]=var;ttk.Entry(profile_frame,textvariable=var).grid(row=i,column=1)

        self.diabetic_var=tk.BooleanVar(); tk.Checkbutton(profile_frame,text="Diabetic",variable=self.diabetic_var,bg="#e6f2ff").grid(row=8,column=0,sticky='w')
        self.hypertensive_var=tk.BooleanVar(); tk.Checkbutton(profile_frame,text="Hypertensive",variable=self.hypertensive_var,bg="#e6f2ff").grid(row=8,column=1,sticky='w')
        self.pref_var=tk.StringVar(value="omnivore"); tk.Label(profile_frame,text="Diet Preference:",bg="#e6f2ff").grid(row=9,column=0,sticky='w'); ttk.Combobox(profile_frame,values=["omnivore","vegetarian","vegan"],textvariable=self.pref_var,state='readonly').grid(row=9,column=1)
        self.south_var=tk.BooleanVar(value=True); tk.Checkbutton(profile_frame,text="Prefer South-Indian breakfast",variable=self.south_var,bg="#e6f2ff").grid(row=10,column=0,sticky='w')
        self.rice_var=tk.BooleanVar(); tk.Checkbutton(profile_frame,text="Require 1 rice meal/day",variable=self.rice_var,bg="#e6f2ff").grid(row=10,column=1,sticky='w')
        ttk.Button(profile_frame,text="Generate Plan",command=self.generate_plan).grid(row=11,column=0,columnspan=2,pady=10)

        # Plan Tab
        plan_frame = tk.Frame(notebook, bg="#fff")
        notebook.add(plan_frame,text="Meal Plan")
        columns = ("Date","Breakfast","Lunch","Snack","Dinner","Total kcal","Note")
        self.tree = ttk.Treeview(plan_frame,columns=columns,show='headings')
        for col in columns:
            self.tree.heading(col,text=col)
            self.tree.column(col,width=130,anchor='center')
        self.tree.pack(fill='both',expand=True,padx=10,pady=10)
        self.tree.tag_configure('over', background='#ffcccc')
        self.tree.tag_configure('under', background='#ffe6cc')
        self.tree.tag_configure('normal', background='#ccffcc')
        ttk.Button(plan_frame,text="Export CSV",command=self.export_csv).pack(pady=5)
        ttk.Label(plan_frame,text="Select a row to see macro chart").pack()
        self.fig,self.ax=plt.subplots(figsize=(4,3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plan_frame)
        self.canvas.get_tk_widget().pack(pady=10)
        self.tree.bind("<ButtonRelease-1>", self.show_macro_chart)

    def generate_plan(self):
        try:
            profile = {
                'name':self.entries["Name"].get(),
                'age':int(self.entries["Age"].get()),
                'gender':self.entries["Gender"].get(),
                'weight':float(self.entries["Weight(kg)"].get()),
                'height':float(self.entries["Height(cm)"].get()),
                'activity':self.entries["Activity"].get(),
                'goal':self.entries["Goal"].get(),
                'days':int(self.entries["Plan Days"].get()),
                'diabetic':self.diabetic_var.get(),
                'hypertensive':self.hypertensive_var.get(),
                'pref':self.pref_var.get(),
                'south_indian_prefer':self.south_var.get(),
                'one_rice_per_day':self.rice_var.get()
            }
        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            return
        self.profile=profile
        self.plan=generate_plan(profile)
        for row in self.tree.get_children(): self.tree.delete(row)
        target=target_calories(profile)
        for day in self.plan:
            tag='normal'
            if day['total_kcal']>target+200: tag='over'
            elif day['total_kcal']<target-300: tag='under'
            self.tree.insert("",tk.END,values=(day['date'],day['breakfast'],day['lunch'],day['snack'],day['dinner'],day['total_kcal'],day['note']),tags=(tag,))
        self.ax.clear()
        self.canvas.draw()

    def export_csv(self):
        if not hasattr(self,'plan') or not self.plan:
            messagebox.showwarning("No Data","Generate a plan first!")
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV files","*.csv")],initialfile=f"{self.username}_plan.csv")
        if file:
            with open(file,'w',newline='') as f:
                writer=csv.writer(f)
                writer.writerow(["Date","Breakfast","Lunch","Snack","Dinner","Total kcal","Note"])
                for day in self.plan:
                    writer.writerow([day['date'],day['breakfast'],day['lunch'],day['snack'],day['dinner'],day['total_kcal'],day['note']])
            messagebox.showinfo("Exported",f"Plan saved to {file}")

    def show_macro_chart(self,event):
        selected=self.tree.focus()
        if not selected: return
        index=self.tree.index(selected)
        day=self.plan[index]
        macros=day['macros']
        self.ax.clear()
        self.ax.pie(macros, labels=["Protein","Carbs","Fat"], autopct='%1.1f%%', colors=['#4CAF50','#FF9800','#2196F3'])
        self.ax.set_title(f"Macros for {day['date']}")
        self.canvas.draw()

# -------------------- RUN APP --------------------
if __name__=="__main__":
    auth = AuthWindow()
    auth.mainloop()
