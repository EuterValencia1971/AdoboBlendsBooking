#imports all the modules
from flask import Flask, render_template, request, redirect
import sqlite3
from flask_mail import Mail, Message
from datetime import datetime, timedelta, time as dt_time

app = Flask(__name__)

# Flask-Mail Setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com' #Sets up what mail server I will be using 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'adoboblendsbooking@gmail.com' #New created email for adoboblends
app.config['MAIL_PASSWORD'] = 'ximz bnxk ykfj zstk'
app.config['MAIL_DEFAULT_SENDER'] = 'adoboblendsbooking@gmail.com'
mail = Mail(app)

# Initialize's and creates the the database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            barber TEXT,
            date TEXT,
            time TEXT,
            service TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Establishes the date and times Adoboblends is avaialable throught the week. 
def get_available_times(barber, date):
    weekday = datetime.strptime(date, '%Y-%m-%d').weekday()
    start_time = datetime.strptime("15:30", "%H:%M") if weekday < 5 else datetime.strptime("08:00", "%H:%M") #Establishes that if its a weekday he is only available from 3:00pm 
    end_time = datetime.strptime("21:00", "%H:%M") #Establishes that he finishes at 9 

    all_times = []
    while start_time <= end_time:
        all_times.append(start_time.strftime("%H:%M"))
        start_time += timedelta(minutes=30) # Drop down menu goes by 30 minute increments. 

    conn = sqlite3.connect('database.db') #Uses the database again 
    c = conn.cursor()
    c.execute("SELECT time FROM appointments WHERE barber=? AND date=?", (barber, date)) #Gets the user to pick what date using a drop down menu. 
    booked_times = [row[0] for row in c.fetchall()]
    conn.close()

    available = [t for t in all_times if t not in booked_times]
    return available

@app.route('/')
def index():
    return render_template('index.html') #Homepage

@app.route('/gallery')
def gallery():
    return render_template('gallery.html') #Previous Work Page 

@app.route('/book', methods=['GET', 'POST'])
def book(): #The Booking Page asking for name, email, the barber, date, time and type of service. 
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        barber = request.form['barber'].strip().lower()
        date = request.form['date']
        time_str = request.form['time'][:5].strip()
        service = request.form['service']

        # Checks if time is valid 
        day_of_week = datetime.strptime(date, '%Y-%m-%d').weekday()
        appointment_time = datetime.strptime(time_str, '%H:%M').time()
        #Establishes the start times and end times on Weekdays and weekends
        weekday_start = dt_time(15, 30)
        weekday_end = dt_time(21, 0)
        weekend_start = dt_time(8, 0)
        weekend_end = dt_time(21, 0)
        #establishes weekend and week day time. 
        if (day_of_week < 5 and not (weekday_start <= appointment_time <= weekday_end)) or \
           (day_of_week >= 5 and not (weekend_start <= appointment_time <= weekend_end)):
            return render_template('invalidtime.html', date=date, time=time_str)

        # Check if time is already booked
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM appointments WHERE barber=? AND date=? AND time=?", (barber, date, time_str))
        if c.fetchone():
            conn.close()
            return render_template('bookedout.html', date=date, time=time_str, barber=barber)

        # Saves booking:
        c.execute("INSERT INTO appointments (name, email, barber, date, time, service) VALUES (?, ?, ?, ?, ?, ?)",
                  (name, email, barber, date, time_str, service))
        conn.commit()
        conn.close()

        # Send confirmation email to user with a message, and address of the barber. 
        user_msg = Message(
            subject='Booking Confirmed - AdoboBlends',
            recipients=[email],
            body=f"""Hi {name},

Your appointment with {barber.title()} on {date} at {time_str} for '{service}' has been confirmed.

📍 Address:
AdoboBlends Barbershop
123 Example Avenue
Sydney, NSW 2761

Thanks for booking in with me, I'll get you just right, trust me. 

See you soon,
AdoboBlends 
"""
        )
        mail.send(user_msg)

        # Send email to barber
        barber_msg = Message(
            subject='New Appointment Booked',
            recipients=['adoboblendsbooking@gmail.com'],
            body=f"{name} has booked an appointment on {date} at {time_str}.\nService: {service}\nClient email: {email}"
        )
        mail.send(barber_msg)

        return redirect('/confirm')

    today = datetime.now().strftime('%Y-%m-%d')
    selected_date = request.args.get('date', today)
    barber = 'adoboblends'
    available_times = get_available_times(barber, selected_date)
    return render_template('book.html', available_times=available_times, selected_date=selected_date)

@app.route('/confirm') #Calls back to the confirm page. 
def confirm():
    return render_template('confirm.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
