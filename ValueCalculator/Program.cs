using System;
using Microsoft.Data.SqlClient;
using System.Collections.Generic;
using System.Reflection.PortableExecutable;
using System.Diagnostics;
using System.IO;
using System.Diagnostics;
using Newtonsoft.Json;
using Azure;
using Newtonsoft.Json.Linq;

namespace Lainalaskuri
{
    public class Product
    {
        public int id;
        public double value;
        public int age;
        public string name;
        public float depreciation;

        public Product(int i, double v, int a, string n, float d)
        {
            id = i;
            value = v;
            age = a;
            name = n;
            depreciation = d;
        }

        public void print() {
            Console.WriteLine("Age(months):" + age + ", Name:" + name+ ", Value:" + value + ", Depreciation:" + depreciation);
        }

        public void FutureValueChange(int x) {
            double percent = (double)depreciation / 100;
            for (int i = 0; i < x; i++) {
                value -= (value * percent);
            }
            age += x;
            print();

        }

        public void PastValueChange(int x)
        {
            double percent = (double)depreciation / 100;
            while (age < x)
            {
                value += value * percent;
                age++;
            }
            age = 0 - age;
            print();
        }

        public void PurchasePrice() {
            double percent = (double)depreciation / 100;
            double notpercent = (100 - (depreciation / 100) * 100)/100;
            double x = percent / notpercent; 
            double roundedValue = Math.Round(x, 3);
            double temp = percent / (1 + percent);


            if (age < 0) {
                //Console.WriteLine(temp);
                while (age < 0)
                {
                    value -= value * (temp);
                    age++;
                }
                print();
            }

            if (age > 0) {
                //Console.WriteLine(roundedValue);
                while (age > 0)
                {
                    value += value * roundedValue;
                    age--;
                }
                print();
            }
            Console.WriteLine(" ");
        }
    }

    public class Loan
    {
        public int LoanID { get; set; }
        public string Owner { get; set; }
        public decimal Amount { get; set; }
        public decimal OriginalAmount { get; set; }
        public decimal Interest { get; set; }
        public decimal MinimumPayment { get; set; }
        public decimal Cost { get; set; }
        public decimal Fine { get; set; }
        public int PaymentTime { get; set; }

        public void print()
        {
            Console.WriteLine("LoanID:" + LoanID + ", Owner:" + Owner + ", Amount:" + Amount + ", Interest:" + Interest + ", MinimumPayment:" + MinimumPayment + ", Cost:" + Cost + ", Fine:" + Fine + ", PaymentTime:" + PaymentTime);
        }
    }

    public static class Search
    {
        public static List<Product> products = new List<Product>();

        public static void Main()
        {
            //id, value age name,deprecation% 
            //add_product();
            List<Loan> loans = new List<Loan>();
            List<Product> products = new List<Product>();
            products = get_products();
            loans = get_loans();
            Console.WriteLine("Tuotteen arvo lainanmaksun jälkeen:");
            for (int i = 0; i < products.Count; i++)
            {
                for (int j = 0; j < loans.Count; j++)
                {
                    if (products[i].id == loans[j].LoanID) {
                        //Tässä on tuote ja tuotteen lainan tiedot
                        products[i].FutureValueChange(loans[j].PaymentTime);

                    }
                    
                }

            }
        }


        public static List<Loan> get_loans()
        {
            string pythonScriptPath = @"C:\Users\n1k0m\AppData\Local\Programs\Python\Python311\python.exe";
            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = @"C:\Users\n1k0m\AppData\Local\Programs\Python\Python311\python.exe";
            start.Arguments = @"C:\Users\n1k0m\Documents\Loans_python\Loans.py";
            start.UseShellExecute = false;
            start.RedirectStandardOutput = true;

            using (Process process = Process.Start(start))
            {
                var output = process.StandardOutput.ReadToEnd();
                var lines = output.Split('\n');

                List<Loan> loans = new List<Loan>();

                for (int i = 0; i < lines.Length; i++)
                {
                    string line = lines[i].Trim();

                    if (int.TryParse(line, out int months))
                    {
                        // If it's a number, it's the payment time
                        var loan = JsonConvert.DeserializeObject<Loan>(lines[i + 1].Trim());
                        loan.PaymentTime = months;
                        loans.Add(loan);
                        i++; // Increment i to skip the next line since we've just processed it
                    }
                }
                return loans;
            }


        }
        public static List<Product> get_products()
        {
            List<Product> products = new List<Product>();
            string connectionString = GetConnection();

            using (SqlConnection connection = new SqlConnection(connectionString))
            {
                connection.Open();

                // SQL Command
                using (SqlCommand cmd = new SqlCommand("SELECT * FROM Products", connection))
                {
                    using (SqlDataReader reader = cmd.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            int i = Convert.ToInt32(reader["ProductID"]);
                            int v = Convert.ToInt32(reader["value"]);
                            int a = Convert.ToInt32(reader["age"]);
                            string n = reader["name"].ToString();
                            float d = Convert.ToInt32(reader["depreciation"]);

                            Product product = new Product(i, v, a, n, d);
                            products.Add(product);
                            //UpdateProducts(products);
                        }
                        return products;
                    }
                }
            }
        }
        public static void add_product(int i, int v, int a, string n, float d)
        {
            Product product = new Product(i, v, a, n, d);

            string connectionString = GetConnection();  // Assuming you have this method as shown in previous code

            using (SqlConnection connection = new SqlConnection(connectionString))
            {
                connection.Open();

                // SQL Command
                string query = "INSERT INTO Products (Value, Age, Name, LoanID, depreciation) VALUES (@Value, @Age, @Name, @LoanID, @depreciation)";
                using (SqlCommand cmd = new SqlCommand(query, connection))
                {
                    cmd.Parameters.AddWithValue("@Value", product.value);
                    cmd.Parameters.AddWithValue("@Age", product.age);
                    cmd.Parameters.AddWithValue("@Name", product.name);
                    cmd.Parameters.AddWithValue("@LoanID", product.id);
                    cmd.Parameters.AddWithValue("@depreciation", product.depreciation);

                    cmd.ExecuteNonQuery();  // Executes the SQL command
                }
            }

        }
        public static void UpdateProducts(List<Product> products)
        {
            string connectionString = GetConnection();

            using (SqlConnection connection = new SqlConnection(connectionString))
            {
                connection.Open();

                foreach (var product in products)
                {
                    using (SqlCommand updateCmd = new SqlCommand("UPDATE Products SET value = @value, age = @age, name = @name, depreciation = @depreciation WHERE ProductID = @id", connection))
                    {
                        updateCmd.Parameters.AddWithValue("@id", product.id);
                        updateCmd.Parameters.AddWithValue("@value", product.value);
                        updateCmd.Parameters.AddWithValue("@age", product.age);
                        updateCmd.Parameters.AddWithValue("@name", product.name);
                        updateCmd.Parameters.AddWithValue("@depreciation", product.depreciation);

                        updateCmd.ExecuteNonQuery();
                    }
                }
            }
        }
        public static string GetConnection()
        {
            return "Server=localhost;Database=Finances;Trusted_Connection=True;Encrypt=False;TrustServerCertificate=True;";
        }
    }
}

