import matplotlib.pyplot as plt 
import mysql.connector
import pyodbc
import json
from decimal import Decimal

final_loan_costs = {}
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # or float(obj) if you want to convert to float instead of string
        return super(DecimalEncoder, self).default(obj)
    
def connect_databse():
    connection_string = r'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=Finances;Trusted_Connection=yes;'

    # Connect to the database
    cnx = pyodbc.connect(connection_string)
    cursor = cnx.cursor()
    return cursor, cnx

def done(i):
    for x in loans.copy():
        if x['amount'] == 0:
            print(i)
            final_loan_costs[x["owner"]] = x["cost"]
            loans.remove(x)
            print(json.dumps(x, cls=DecimalEncoder))

def minumum_payments(payment, loans, i):
     penalty = 0
     reduction = payment
     cost = 0
     for x in loans:   
        cost += x['minimum_payment']
     #print("Lainojen maksuun tarvittava minimisumma on:", cost)
     if payment >= cost:
         #print("lainojen maksun pitäisi onnistua!")
         for x in loans:
            if x['amount'] < x['minimum_payment']:
                 payment -= x['amount']
                 #print("Maksetaan lainasta", x['owner'], x['amount'], )
                 x['amount'] = 0
                 done(i)
            else:
                x['amount'] -= x['minimum_payment']
                #print("Maksetaan lainasta", x['owner'], x['minimum_payment'])
                payment -= x['minimum_payment']
     else:
         #print("rahat eivät riitä lainojen maksuun!")
         for x in loans:
            #tässä katsotaan pystyykö maskamaan jotain pois
            #print((payment >=  x['amount'] and x['amount'] != 0))
            if payment >=  x['amount'] and x['amount'] != 0:
                 #payment -= x['amount']
                 #print("Maksetaan laina", x['owner'],"kokonaan pois, jonka jälkeen rahaa on jäljellä:", payment)
                 x['amount'] = 0
                 done(i)

         loans = sorted(loans, key=lambda x: x['minimum_payment'], reverse=False)
         for x in loans:
            #tässä katotaan pystyykö maksamaan pakollisia maksuja
                if payment >= x['minimum_payment'] and x['amount'] != 0:
                        payment -= x['minimum_payment']
                        x['amount'] -= x['minimum_payment']
                        #print("Pystytään maksamaan lainasta", x['owner'], "vain minimiosa: ",x['minimum_payment'],", jonka jälkeen rahaa on jäljellä:", payment)

                else:
                    sakko = 5
                    x['amount'] += x['minimum_payment'] + sakko
                    x['fine']  += 1
                    x['cost'] += sakko
                    penalty += x['minimum_payment'] + sakko

     if penalty > reduction:
         print("Lainoja ei saa tällä budjetilla koskaan maksettua")

     done(i)
     loans = sorted(loans, key=lambda x: x['interest'], reverse=True)
     if payment > 0:
        additional_payments(payment, i)

def additional_payments(payment, i):
    #print("--------------------------")
    #print("Minimi maksujen jälkeen rahaa jäi:",payment)
    for x in loans:
         if x['amount'] > payment:
            #print("Maksetaan lainasta", x['owner'],"summa", payment)
            x['amount'] -= payment
            payment = 0
         else:
             temp = x['amount']
             x['amount'] = 0
             payment -= temp

         if payment == 0:
            break
    done(i)
    """if payment != 0:
        print("Rahaa jäi: ", payment)"""

def add_intrest():
    for x in loans:
        if x['interest'] != 0:
            interest = x['amount'] * ((x['interest']/12)/100)
            x['amount'] += interest
            x['cost'] += interest

def get_visuals(ax1, ax2):

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))  # 1 row, 2 columns

    # First plot: Loan Amount
    for loan_name, amounts in history.items():
        ax1.plot(amounts, label=loan_name)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax1.set_xlabel('Kuukaudet')
    ax1.set_ylabel('Lainan määrä')
    ax1.legend()


    loan_names = list(final_loan_costs.keys())
    costs = list(final_loan_costs.values())
    ax2.bar(loan_names, costs)
    ax2.set_xlabel('Lainat')
    ax2.set_ylabel('Kustannukset')
    ax2.set_title('Lainojen kustannukset')

    plt.show()

def fetch_loans():
    
    cursor, cnx = connect_databse()
    cursor.execute("SELECT * FROM loans")
    
    rows = cursor.fetchall()
    
    loans = []
    for row in rows:
        loan = {
            "LoanID":row.LoanID,
            "owner": row.Owner,
            "amount": row.Amount,
            "interest": row.Interest,
            "minimum_payment": row.MinimumPayment,
            "cost": row.Cost,
            "fine": row.Fine
        }
        loans.append(loan)

    cursor.close()
    cnx.close()

    return loans

def insert_into_loans(Owner, Amount, Interest, MinimumPayment, Fine, Cost):
    conn_str = (
        r'Driver={ODBC Driver 17 for SQL Server};'
        r'Server=localhost;'  # Replace with your server name
        r'Database=Finances;'    # Replace with your database name
        r'Trusted_Connection=yes;'
    )
    
    # SQL query to insert data
    insert_query = '''
    INSERT INTO Loans (Owner, Amount, Interest, MinimumPayment, Fine, Cost)
    VALUES (?, ?, ?, ?, ?, ?);
    '''

    try:
        # Establishing a connection
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(insert_query, Owner, Amount, Interest, MinimumPayment, Fine, Cost)
            conn.commit()
        print("Data inserted successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

def monthly_update():
    
    cursor, cnx = connect_databse()
    cursor.execute("SELECT * FROM loans")
    
    rows = cursor.fetchall()
    
    loans = []
    for row in rows:
        loan = {
            "LoanID":row.LoanID,
            "owner": row.Owner,
            "amount": row.Amount,
            "interest": row.Interest,
            "minimum_payment": row.MinimumPayment,
            "cost": row.Cost,
            "fine": row.Fine,
            "payments": row.Payments
        }
        loans.append(loan)

        for x in loans:
            x["amount"] -= x["minimum_payment"]
            x["payments"] += 1

        update_query = """
                UPDATE loans
                SET Amount = ?, Payments = ?
                WHERE LoanID = ?
            """
        cursor.execute(update_query, (x["amount"], x["payments"], x["LoanID"]))

        cnx.commit()


    cursor.close()
    cnx.close()

#monthly_update()
loans = fetch_loans()
print(json.dumps(loans, cls=DecimalEncoder))
loans = sorted(loans, key=lambda x: x['interest'], reverse=True)
payment = float(input("Enter the amount you can pay monthly: "))
history = {loan["owner"]: [] for loan in loans}
loan_cost = {loan["owner"]: [] for loan in loans}
i = 0
while len(loans) != 0:
    for loan in loans:
        history[loan["owner"]].append(loan["amount"])
    minumum_payments(payment, loans, i)
    add_intrest()
    i += 1
    if i > 120:
        break
#get_visuals(history, final_loan_costs)
 