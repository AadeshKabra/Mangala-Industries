import pymongo
from flask import Flask, render_template, request, session, jsonify, send_file
import pandas as pd
import io
import os

app = Flask(__name__, static_folder='static')

# app.config["SECRET_KEY"] = "013a658d9c8323f8e0af1f8ba8b4bcf30456a4c0"
# app.config["MONGO_URI"] = "mongodb+srv://mangalaindustries:mangalaindustries@cluster0.hvbqkjb.mongodb.net/?retryWrites=true&w=majority"

app.config["SECRET_KEY"] = "013a658d9c8323f8e0af1f8ba8b4bcf30456a4c0"
app.config["MONGO_URI"] = "mongodb+srv://mangalaindustries:mangalaindustries@cluster0.hvbqkjb.mongodb.net/?retryWrites=true&w=majority"


mongo_client = pymongo.MongoClient(app.config["MONGO_URI"])

# mongo_client = PyMongo(app)
db = mongo_client.get_database("MI")

# db = pymongo.database.Database(mongo_client, 'MI')
# users = pymongo.collection.Collection(db, 'users')
# db = mongo_client.get_database('MI')

# ---->Collections
users = db.get_collection('users')
insertsI = db.get_collection('InsertsInward')
inserts = db.get_collection('Inserts')
insertsO = db.get_collection('InsertsOutward')
operators = db.get_collection("Operators")


# ---->Functions
def get_brands_list():
    brands_list = []
    brand_names = inserts.find({}, {"Brand": 1})
    for brand in brand_names:
        brands_list.append(brand["Brand"])

    return brands_list


def get_inserts_list():
    inserts_list = []
    names = inserts.find({}, {"Name": 1})
    for name in names:
        inserts_list.append(name["Name"])

    return inserts_list


def get_operators_list():
    operators_list = []
    operators_doc = operators.find({}, {"Name": 1})
    for i in operators_doc:
        operators_list.append(i["Name"])
    print(operators_list)
    return operators_list


def get_current_report():
    balance_list = []
    inserts_list2 = []
    records = inserts.find()
    for record in records:
        balance_list.append(int(record["Quantity"]))
        inserts_list2.append(record['Name'])

    df = pd.DataFrame(list(zip(inserts_list2, balance_list)), columns=['Insert', 'Current Stock'])
    df.reset_index(drop=True, inplace=True)
    df.index += 1

    return df


def get_inward_reports():
    # Report1
    dates_list = []
    inserts_list = []
    brands_list = []
    quantity_list = []

    docs = insertsI.find({})
    for doc in docs:
        dates_list.append(doc['Date'])
        inserts_list.append(doc['Name'])
        brands_list.append(doc['Brand'])
        quantity_list.append(doc['Quantity'])

    df1 = pd.DataFrame(list(zip(dates_list, brands_list, inserts_list, quantity_list)),
                       columns=['Date', 'Brand', 'Insert', 'Quantity Purchased'])
    df1.reset_index(drop=True, inplace=True)
    df1.index += 1

    # Report2
    seen = set()
    inserts_list_new = [x for x in inserts_list if not (x in seen or seen.add(x))]
    total_qty = []
    for item in inserts_list_new:
        docs = insertsI.find({'Name': item})
        sum = 0
        for doc in docs:
            sum += doc['Quantity']
        total_qty.append(sum)

    df2 = pd.DataFrame(list(zip(inserts_list_new, total_qty)), columns=['Insert', 'Total Purchase'])
    df2.reset_index(inplace=True, drop=True)
    df2.index += 1

    return df1, df2


def get_outward_reports():
    # Report1
    dates_list = []
    operators_list = []
    inserts_list = []
    brands_list = []
    quantity_list = []
    docs = insertsO.find()
    for doc in docs:
        dates_list.append(doc['Date'])
        operators_list.append(doc['Operator'])
        quantity_list.append(doc['Quantity'])
        brands_list.append(doc['Brand'])
        inserts_list.append(doc['Name'])

    df1 = pd.DataFrame(list(zip(dates_list, brands_list, inserts_list, operators_list, quantity_list)),
                       columns=['Date', 'Brand', 'Item', 'Operator', 'Quantity Given'])
    df1.reset_index(drop=True, inplace=True)
    df1.index += 1

    # Report2

    seen = set()
    inserts_list_new = [x for x in inserts_list if not (x in seen or seen.add(x))]
    total_qty = []
    for item in inserts_list_new:
        docs = insertsO.find({'Name': item})
        sum = 0
        for doc in docs:
            sum += int(doc['Quantity'])
        total_qty.append(sum)

    df2 = pd.DataFrame(list(zip(inserts_list_new, total_qty)), columns=['Insert', 'Total Outward'])
    df2.reset_index(inplace=True, drop=True)
    df2.index += 1

    return df1, df2


# ---->Routes
@app.route("/")
def index():
    # return render_template("login.html")
    return render_template("home.html")


@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        # print("POST request")
        username = request.form.get("username")
        password = request.form.get("password")
        print(username, password)

        existing_user = users.find_one({"Username": username})
        if existing_user is None:
            print("New user")
            users.insert_one({
                "Username": username,
                "Password": password
            })

            return render_template("login.html")

        else:
            return "User already present. Please try logging in"

    return render_template("register.html")


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        # users = mongo_client.db.users
        username = request.form.get("username")
        password = request.form.get("password")
        print(username, password)
        login_user = users.find_one({"Username": username})
        # print("User searched")
        if login_user:
            print("User present in database")
            if request.form["password"] == login_user["Password"]:
                session["username"] = request.form["username"]
                return render_template("home.html")
            else:
                return "Incorrect Credentials"
        else:
            return render_template("login.html")


# Inserts Section
@app.route("/inserts", methods=['POST'])
def inserts_section():
    df = get_current_report()
    report = df.to_html()
    report = report.replace('<th>', '<th style="font-weight:bold;">')
    report = report.replace('</table>', '<style>table tr td:last-child {font-weight: bold;}</style></table>')
    return render_template("Inserts/inserts.html", report=report)


@app.route("/insertsInward", methods=['POST'])
def inserts_inward():
    return render_template("Inserts/insertsInward.html")


@app.route("/insertsOutward", methods=['POST'])
def inserts_outward():
    inserts_list = get_inserts_list()
    brands_list = get_brands_list()
    operators_list = get_operators_list()
    return render_template("Inserts/insertsOutward.html", inserts=inserts_list, brands=brands_list, operators=operators_list)


@app.route("/newInsert", methods=['POST'])
def new_insert():
    date = request.form.get("date")
    name = request.form.get("name")
    quantity = int(request.form.get("quantity"))
    brand = request.form.get("brand")

    date = date.split("-")
    date = date[::-1]
    date_string = ""
    for i in date:
        date_string += i
        date_string += "-"

    document = {
        "Name": name,
        "Date": date_string,
        "Quantity": quantity,
        "Brand": brand
    }
    # Insert in Inward Collection
    insertsI.insert_one(document)

    # Update in stock Collection
    existing_doc = inserts.find_one({"Name": name, "Brand": brand})
    if existing_doc is None:
        inserts.insert_one(document)
    else:
        existing_quantity = existing_doc["Quantity"]
        update_query = {"$set": {"Quantity": int(existing_quantity) + int(quantity)}}
        result = inserts.update_one({"Name": name, "Brand": brand}, update_query)

        if result.modified_count > 0:
            print("Quantity updated successfully")
        else:
            print("Error in updating quantity")

    print("Inserted")
    df = get_current_report()
    report = df.to_html()
    report = report.replace('<th>', '<th style="font-weight:bold;">')
    report = report.replace('</table>', '<style>table tr td:last-child {font-weight: bold;}</style></table>')
    return render_template("Inserts/inserts.html", report=report)


@app.route('/get_max_quantity', methods=['POST'])
def get_max_quantity():
    selected_insert = request.form.get('item')
    existing_doc = inserts.find_one({'Name': selected_insert})
    quantity = int(existing_doc['Quantity'])

    response = {'max_value': quantity}
    return jsonify(response)


@app.route('/get_inserts', methods=['POST'])
def get_inserts():
    brand = request.form.get('brand')
    print(brand)
    docs = inserts.find({"Brand": brand}, {"Name": 1, "_id": 0})
    inserts_list = []
    for doc in docs:
        inserts_list.append(doc['Name'])
    print(inserts_list)

    response = {'inserts': inserts_list}
    return jsonify(response)


@app.route("/outInsert", methods=['POST'])
def out_insert():
    date = request.form.get("date")
    brand = request.form.get("brand")
    item = request.form.get("insert")
    quantity = request.form.get("quantity")
    operator = request.form.get("operator")

    date = date.split("-")
    date = date[::-1]
    date_string = ""
    for i in date:
        date_string += i
        date_string += "-"

    existing_doc = inserts.find_one({"Name": item, "Brand": brand})

    if existing_doc:
        existing_quantity = int(existing_doc["Quantity"])

        if int(existing_quantity) < int(quantity):
            inserts_list = get_inserts_list()
            brands_list = get_brands_list()
            operators_list = get_operators_list()

            return render_template("Inserts/insertsOutward.html", inserts=inserts_list, brands=brands_list, operators=operators_list, message="Outward Quantity exceeded maximum quantity! Please enter correct qunatity.")

        else:
            update_query = {'$set': {"Quantity": int(existing_quantity) - int(quantity)}}
            result = inserts.update_one({"Name": item, "Brand": brand}, update_query)

            if result.modified_count > 0:
                print("Quantity updated successfully")
            else:
                print("Error in updating quantity")

    doc = {
        "Date": date_string,
        "Brand": brand,
        "Name": item,
        "Quantity": quantity,
        "Operator": operator
    }
    insertsO.insert_one(doc)

    print("Removed")

    df = get_current_report()
    report = df.to_html()
    report = report.replace('<th>', '<th style="font-weight:bold;">')
    report = report.replace('</table>', '<style>table tr td:last-child {font-weight: bold;}</style></table>')
    return render_template("Inserts/inserts.html", report=report)


@app.route("/inwardReport", methods=['POST'])
def inward_report():
    df1, df2 = get_inward_reports()

    report1 = df1.to_html()
    report1 = report1.replace('<th>', '<th style="font-weight:bold;">')
    report1 = report1.replace('</table>', '<style>table tr td:last-child {font-weight: bold;}</style></table>')

    report2 = df2.to_html()
    report2 = report2.replace('<th>', '<th style="font-weight:bold;">')
    report2 = report2.replace('</table>', '<style>table tr td:last-child {font-weight: bold;}</style></table>')

    return render_template("Inserts/inwardReport.html", report1=report1, report2=report2)


@app.route("/outwardReport", methods=['POST'])
def outward_report():
    df1, df2 = get_outward_reports()

    report1 = df1.to_html()
    report1 = report1.replace('<th>', '<th style="font-weight:bold;">')
    report1 = report1.replace('</table>', '<style>table tr td:last-child {font-weight: bold;}</style></table>')

    report2 = df2.to_html()
    report2 = report2.replace('<th>', '<th style="font-weight:bold;">')
    report2 = report2.replace('</table>', '<style>table tr td:last-child {font-weight: bold;}</style></table>')

    return render_template("Inserts/outwardReport.html", report1=report1, report2=report2)


@app.route("/download", methods=['POST'])
def download():
    inward_report1, inward_report2 = get_inward_reports()
    # print(inward_report1)
    outward_report1, outward_report2 = get_outward_reports()
    balance_report = get_current_report()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        inward_report1.to_excel(writer, sheet_name="Inward1", index=False)
        inward_report2.to_excel(writer, sheet_name="Inward2", index=False)
        outward_report1.to_excel(writer, sheet_name="Outward1", index=False)
        outward_report2.to_excel(writer, sheet_name="Outward2", index=False)
        balance_report.to_excel(writer, sheet_name="Balance", index=False)

    output.seek(0)
    file_path = os.path.join(os.path.expanduser("~"), "Downloads", "Reports.xlsx")
    response = send_file(output, as_attachment=True, download_name=file_path,mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    response.headers['Content-Disposition'] = 'attachment; filename=Reports.xlsx'
    response.headers['Cache-Control'] = 'no-cache'

    return response


@app.route("/operators", methods=['POST'])
def operator():
    return render_template("Operators/operators.html")


@app.route("/addOperator", methods=['POST'])
def add_operator():
    name = request.form.get("name")
    doc = {
        "Name": name
    }
    operators.insert_one(doc)
    df = get_current_report()
    report = df.to_html()
    report = report.replace('<th>', '<th style="font-weight:bold;">')
    report = report.replace('</table>', '<style>table tr td:last-child {font-weight: bold;}</style></table>')
    return render_template("Inserts/inserts.html", report=report)



@app.route("/get_operators", methods=['GET'])
def get_operators():
    docs = operators.find({})
    operators_list = []
    for doc in docs:
        operators_list.append(doc["Name"])

    response = {"operators": operators_list}
    return jsonify(response)


if __name__ =='__main__':
    app.run()


# mangalaindustries
