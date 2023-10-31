from flask import Flask, request, render_template, redirect, url_for
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import base64
import os
import io
from PIL import Image
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create an "uploads" directory to store uploaded files
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

#CurrentAccount Initilization
CurrentAccount=""


#AdminAccountDeatils
sender_email = "*******@gmail.com"
sender_password = "***********"



# Initialize Firebase Admin SDK with your service account key
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()
def compress_image(image_path):
    with Image.open(image_path) as img:
        img.thumbnail((800, 800))  # Adjust the size as needed
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")  # You can adjust the format
        return buffer.getvalue()

# Create a route to display the form
@app.route("/",methods=["GET"])
def hom():
    return render_template("start.html")




@app.route("/addproduct", methods=["GET"])
def index():
    return render_template("form.html")

# Create a route to handle form submission
@app.route("/submit", methods=["POST"])
def submit():
    global CurrentAccount
    global sender_email
    global sender_password
    if CurrentAccount == "":
        return redirect(url_for("/log"))

    seller_id = int(request.form.get("seller_id"))
    
    product_name = request.form.get("product_name")
    price = int(request.form.get("price"))
    product_description = request.form.get("product_description")
    category_type = request.form.get("category_type")
    year = request.form.get("year")
    seller_name = request.form.get("seller_name")
    seller_email = request.form.get("seller_email")
    #Encoding the productId
    input_data = f"{seller_id}-{product_name}".encode()
    hash_object = hashlib.sha256(input_data)
    hex_digest = hash_object.hexdigest()
    product_id = int(hex_digest, 16) % 10**7
    # product_id = int(request.form.get("product_id"))

    # Handle file upload
    if 'product_image' in request.files:
        image_file = request.files['product_image']
        if image_file.filename != '':
            # Save the uploaded image to the "uploads" directory
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
            image_file.save(image_path)

            # Read the image as binary data and encode it as base64
            # with open(image_path, "rb") as image_file:
            #     image_binary = base64.b64encode(image_file.read()).decode("utf-8")
            compressed_image = compress_image(image_path)
            image_binary = base64.b64encode(compressed_image).decode("utf-8")
            # Store the data in the Firestore database
            product_ref = db.collection("login").document()
            product_ref.set({
                "seller_id": seller_id,
                "product_id": product_id,
                "product_name":product_name,
                "product_image": image_binary,
                "price": price,
                "product_description": product_description,
                "category_type": category_type,
                "year": year,
                "seller_name": seller_name,
                "seller_email": seller_email
            })
            os.remove(image_path)
            recipient_email=CurrentAccount
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            subject = "Successfull added Product Item"
            message_text="Hello "+recipient_email+""", \nYour Item added successfull to 
            CampusCart, We will inform you when buyer choose your Item.\n\n\n
            - Thanks from CampusCart.
            """
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message_text, 'plain'))
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()


    return redirect(url_for("products"))

@app.route("/products", methods=["GET"])
def products():
    products = db.collection("login").stream()
    product_data = []

    for product in products:
        product_dict = product.to_dict()
        product_data.append(product_dict)

    return render_template("products.html", product_data=product_data)

# charan
@app.route("/product_details/<product_id>")
def product_details(product_id):
    # Retrieve the product details from Firestore based on the product ID
    # print("hello",product_id)
    a=int(product_id)
    try:
        product_ref = db.collection("login").where("product_id", "==",a).get()
    # rest of your code
    except Exception as e:
        print(f"Firestore query error: {str(e)}")
    # Handle the error appropriately (e.g., logging or displaying an error message to the user).
    product_data = {}
    for doc in product_ref:
        # print(doc,"rara sir")
        product_data = doc.to_dict()
    return render_template("product_details.html", product_data=product_data)

@app.route("/buy_product/<product_id>", methods=["POST"])
def buy_product(product_id):
    global CurrentAccount
    global sender_email
    global sender_password
    if len(CurrentAccount)==0:
        return redirect(url_for("/log"))
    try:
        # Retrieve the product details from Firestore based on the product ID
        a = int(product_id)
        product_ref = db.collection("login").where("product_id", "==", a).get()
        product_ref2=db.collection("loginDetails").where("email","==",CurrentAccount).get()
        
        # Handle the error if the product is not found
        if len(product_ref) == 0:
            return "Product not found", 404

        # Assuming there is only one product with the given ID, get its data
        product_data = product_ref[0].to_dict()
        product_data2=product_ref2[0].to_dict()

        # Now, you can store this product data in the "buy" collection or perform other actions.
        product_data["Buyeremail"] = CurrentAccount
        # Example: Store the product data in a "buy" collection
        db.collection("buy").add(product_data)

       

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        subject = "Order placed Successfully"
        subject2="Your product is ready to Buy"
        message_text="Hello "+CurrentAccount+""", \nYour order placed successfully,\n\n\n
        your order details:- \n\n
        -  product name :- """+str(product_data["product_name"])+"""
        -  product_id :- """+str(product_data["product_id"])+"""
        -  Seller-Email :- """+str(product_data["seller_email"])+"""
        -  Seller-name :- """+str(product_data["seller_name"])+"""
        -  product price :- """+str(product_data["price"])+"""
        Please contact to the above sender email if did'nt get any response from the seller.\n\n
        Thankyou for choosing our website.\nHave a good day.
        """
        message_text2="Hello "+str(product_data["seller_email"])+", Your Product is ready to take by the customer\n Your customer details:\nCustomer Name :- "+product_data2["name"]+"\nCustomer email :- "+CurrentAccount+"\nPlease contact the above customer for further proceedings to delivery the product.\nThankYou!!!"
        
        msg = MIMEMultipart()
        msg_buyer=MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = CurrentAccount
        msg['Subject'] = subject
        msg.attach(MIMEText(message_text, 'plain'))
        server.sendmail(sender_email, CurrentAccount, msg.as_string())
        msg_buyer["From"]= sender_email
        msg_buyer["To"]= str(product_data["seller_email"])
        msg_buyer["Subject"]=subject2
        msg_buyer.attach(MIMEText(message_text2,"plain"))
        server.sendmail(sender_email,product_data["seller_email"],msg_buyer.as_string())
        server.quit()

        return redirect(url_for("popup"))
    except Exception as e:
        print(f"Firestore query error: {str(e)}")
        return "Error purchasing the product", 500

@app.route("/add_product/<product_id>", methods=["POST"])
def add_product(product_id):
    global CurrentAccount
    try:
        # Retrieve the product details from Firestore based on the product ID
        a = int(product_id)
        product_ref = db.collection("login").where("product_id", "==", a).get()

        # Handle the error if the product is not found
        if len(product_ref) == 0:
            return "Product not found", 404

        # Assuming there is only one product with the given ID, get its data
        product_data = product_ref[0].to_dict()

        # Now, you can store this product data in the "buy" collection or perform other actions.

        # Example: Store the product data in a "buy" collection
        product_data["Email"] = CurrentAccount
        db.collection("cart").add(product_data)

        # Set the success message for the popup
        popup_message = "Product  successfully."

        # You can return this message to the client
        return render_template("SuccADDCart.html")

    except Exception as e:
        print(f"Firestore query error: {str(e)}")
        return "Error purchasing the product", 500


@app.route("/addcart")
def carti():
    global CurrentAccount
    if CurrentAccount=="":
        return render_template("login.html")
    try:
        # Retrieve order details from the "buy" collection
        order_ref = db.collection("cart").where("Email", "==", CurrentAccount).stream()
        orders = []

        for doc in order_ref:
            order_data = doc.to_dict()
            orders.append(order_data)

        return render_template("addcart.html", orders=orders)
    except Exception as e:
        print(f"Firestore query error: {str(e)}")
        return "Error fetching order details", 500
    
@app.route("/order")
def order():
    global CurrentAccount
    try:
        # Retrieve order details from the "buy" collection
        order_ref = db.collection("buy").where("Buyeremail", "==", CurrentAccount).stream()
        orders = []

        for doc in order_ref:
            order_data = doc.to_dict()
            orders.append(order_data)

        return render_template("order.html", orders=orders)
    except Exception as e:
        print(f"Firestore query error: {str(e)}")
        return "Error fetching order details", 500

@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")


@app.route("/delete_order/<order_id>", methods=["POST"])
def delete_order(order_id):
    try:
        # Retrieve the order details that match the product_id
        order_ref = db.collection("buy").where("product_id", "==", int(order_id)).stream()
        print("helo")
        # Loop through the query results and delete the matching order(s)
        for doc in order_ref:
            doc.reference.delete()
            print("doc")
            
        return redirect(url_for('order'))  # Redirect back to the order page
    except Exception as e:
        print(f"Error deleting order: {str(e)}")
        return "Error deleting the order", 500
    
@app.route("/delete_cart/<order_id>", methods=["POST"])
def delete_cart(order_id):
    try:
        # Retrieve the order details that match the product_id
        order_ref = db.collection("cart").where("product_id", "==", int(order_id)).stream()
        print("helo")
        # Loop through the query results and delete the matching order(s)
        for doc in order_ref:
            doc.reference.delete()
            print("doc")
            
        return redirect(url_for('carti'))  # Redirect back to the order page
    except Exception as e:
        print(f"Error deleting order: {str(e)}")
        return "Error deleting the order", 500



#After the login to website
@app.route("/Account", methods=["GET"])
def Accdetails():
    products = db.collection("login").stream()
    product_data = []

    for product in products:
        product_dict = product.to_dict()
        product_data.append(product_dict)

    return render_template("Homedashbord.html", product_data=product_data)


@app.route("/search", methods=["POST"])
def search():
    search_query = request.form.get("product_name").strip().lower()  # Convert to lowercase and remove leading/trailing spaces
    # Retrieve products with a matching or substring product name or category_type from the Firestore database
    products = db.collection("login").stream()
    product_data = []

    for product in products:
        product_dict = product.to_dict()
        # Check if the entered search_query is in either product_name or category_type, and convert both to lowercase
        if search_query in product_dict["product_name"].lower() or search_query in product_dict["category_type"].lower():
            product_data.append(product_dict)

    return render_template("products.html", product_data=product_data)


@app.route("/category/<category_name>")
def category(category_name):
    # Retrieve products from Firestore that match the category
    products = db.collection("login").stream()
    product_data = []

    for product in products:
        product_dict = product.to_dict()
        # Check if the entered product name is a substring of the product name or matches exactly
        if category_name in product_dict["category_type"].lower():
            product_data.append(product_dict)

    return render_template("products.html", product_data=product_data)




# ----------------------------------------------------------------------------------------------------------------------------------
#Login And Signin route




@app.route("/log" ,methods=["GET"])
def log():
    return render_template("login.html")
@app.route("/sig",methods=["GET"])
def sig():
    return render_template("signin.html")

@app.route("/sigsub", methods=["POST"])
def signin():
    global sender_email
    global sender_password

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_ref = db.collection("loginDetails").where("email", "==", email).stream()
        if len(list(user_ref)) > 0:
            # Redirect to a page indicating that the email is already registered
            return render_template("Already.html")
        
        sha256_hash = hashlib.sha256(email.encode()).digest()
    
        # Take the first 4 bytes of the hash (32 bits)
        first_4_bytes = sha256_hash[:4]

        # Convert the 4 bytes to an integer
        code_int = int.from_bytes(first_4_bytes, byteorder='big')

        # Ensure it's a 5-digit code (between 10000 and 99999)
        code_int = code_int % 90000 + 10000

        # Store user registration data in Firestore or your database
        product_ref = db.collection("loginDetails").document()
        product_ref.set({
            "email": email,
            "password": password,
            "Id":code_int
        })

        # CurrentAccount = email

        # Send a confirmation email to the registered user
        recipient_email = email

        # Create an SMTP session
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        # Create a message with a subject
        subject = "Sign-in to Website"
        message_text = "Hello " + email + ",\nThanks for signing in to our website.\nYour User/Seller ID: " + str(code_int) +". Please don't sshare this to anyone."
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message_text, 'plain'))

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())

        # Close the SMTP session
        server.quit()
    return redirect(url_for("products"))

@app.route("/logsub", methods=["POST"])
def login():
    global CurrentAccount

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Query Firestore to check if the email and password match
        user_ref = db.collection("loginDetails").where("email", "==", email).where("password", "==", password).stream()
        
        # If a matching user is found, set the CurrentAccount variable and redirect to products
        if len(list(user_ref)) > 0:
            CurrentAccount = email
            return redirect(url_for("Accdetails"))
        else:
            # Redirect to a login error page or display an error message
            return render_template("login_error.html")

    return render_template("login.html")  # Render the login page initially





#profile
@app.route("/update_profile", methods=["POST"])
def update_profile():
    if request.method == "POST":
        global CurrentAccount  # Replace with your method of getting the current account's email
        email = CurrentAccount  # Use the current account's email as the identifier
        password = request.form.get("password")
        user_id = request.form.get("user_id")
        name=request.form.get("name")
        image = request.files["image"]

        # Query Firestore to find the document with the matching email
        users_ref = db.collection("loginDetails")
        query = users_ref.where("email", "==", email)

        user_data = {}  # Initialize user_data as an empty dictionary
        user_ref = None

        for doc in query.stream():
            user_ref = doc.reference
            user_data = doc.to_dict()
            break  # Assuming there's only one document with the provided email

        if user_ref is not None:
            # Update user information in Firestore based on the retrieved document
            user_data.update({
                "email": email,  # Ensure the email field remains the same
                "name":name,
                "password": password,
                "Id": user_id,
            })

            # Handle the image upload and conversion to Base64
            if image:
                image_data = image.read()  # Read binary image data
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                user_data["image"] = image_base64

            user_ref.update(user_data)  # Update the document

            # Redirect to the profile page or another page
            return redirect(url_for("Accdetails"))
        else:
            # Handle the case where no user with the provided email is found
            return "User not found", 404

@app.route("/profile")
def profile():
    global CurrentAccount
    print(CurrentAccount)
    # email = CurrentAccount  # Get the user's email from the session or context
    user_ref = db.collection("loginDetails").where('email','==', CurrentAccount)
    user_data = {}
    for doc in user_ref.stream():
        user_data = doc.to_dict()
        break

    # Populate the form fields with the user's data, including the image
    # print(user_data)
    return render_template("profile.html", user_data=user_data)



@app.route("/order-placed",methods=["GET"])
def popup():
    return render_template("popup.html")


if __name__ == "__main__":
    app.run(debug=True)


# p: ttif ezpl hqxh phum


