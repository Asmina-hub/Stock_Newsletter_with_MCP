import random
from fastmcp import FastMCP
import sqlite3
import os


mcp_server = FastMCP('expense tracker')
db_path = os.path.join(os.path.dirname(__file__),"expense.db")
category_path = os.path.join(os.path.dirname(__file__),"categories.json")

def initialize_db():
    with sqlite3.connect(db_path) as c :
        c.execute(
            """CREATE TABLE IF NOT EXISTS expense(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount INTEGER NOT NULL,
            note TEXT DEFAULT ' ' 
              )
            """
        )
initialize_db()

@mcp_server.tool
def add_expense(date,amount,category,note= ' '):
    'Add a new expense'
    with sqlite3.connect(db_path) as c:
        cur = c.execute("INSERT INTO expense(date,amount,category,note) VALUES (?,?,?,?)",(date,amount,category,note))
        return {'id':cur.lastrowid}

@mcp_server.tool
def list_expense():
    'List the expenses'
    with sqlite3.connect(db_path) as c:
        cur = c.execute("SELECT date,amount,category,note FROM expense ORDER BY id ASC")
        cols = [i[0] for i in cur.description]
        return (dict(zip(cols,r))for r in cur.fetchall())

@mcp_server.tool
def list_expense_bydate(st_date,end_date):
     'List the expense between a start date and end date'
     with sqlite3.connect(db_path) as c:
            cur = c.execute("""SELECT date,amount,category,note FROM expense WHERE date BETWEEN ? AND ? ORDER BY id ASC""",(st_date,end_date))
            cols = [i[0] for i in cur.description]
            return (dict(zip(cols,r))for r in cur.fetchall())

@mcp_server.tool
def summarize(st_date,end_date,category= None):
    'Summarize the expense withbin some dates'
    with sqlite3.connect(db_path) as c:
                query = ("""SELECT category, SUM(amount) AS total_expense_per_categors FROM expense WHERE date BETWEEN ? AND ? """ ) 
                parameters =[st_date,end_date] 
                if category:
                     query += "AND category = ?"
                     parameters.append(category)
                
                query+= "GROUP BY category ORDER BY category ASC "
                cur = c.execute(query,parameters)
                cols = [i[0] for i in cur.description]
                return (dict(zip(cols,r))for r in cur.fetchall())

@mcp_server.resource("expense://categories.json", mime_type="application/json")
def categories():
    'categories to add from'
    with open(category_path, "r", encoding="utf-8") as c:
            return c.read()




if __name__ == "__main__":
    mcp_server.run(transport="http", host ="0.0.0.0", port=8000)