from fastmcp import FastMCP
import psycopg
import os


mcp_server = FastMCP('expense tracker')
category_path = os.path.join(os.path.dirname(__file__),"categories.json")

# Postgres connection string, e.g. from Supabase or Neon. Set it as an
# environment variable in FastMCP Cloud so the data survives restarts.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

def connect():
    # prepare_threshold=None keeps it working behind connection poolers (Supabase/Neon)
    return psycopg.connect(DATABASE_URL, prepare_threshold=None)

def rows_as_dicts(cur):
    cols = [i[0] for i in cur.description]
    return [dict(zip(cols,r)) for r in cur.fetchall()]

def initialize_db():
    with connect() as c :
        c.execute(
            """CREATE TABLE IF NOT EXISTS expense(
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount DOUBLE PRECISION NOT NULL,
            note TEXT DEFAULT ' '
              )
            """
        )
initialize_db()

@mcp_server.tool
def add_expense(date,amount,category,note= ' '):
    'Add a new expense'
    with connect() as c:
        cur = c.execute("INSERT INTO expense(date,amount,category,note) VALUES (%s,%s,%s,%s) RETURNING id",(date,amount,category,note))
        return {'id':cur.fetchone()[0]}

@mcp_server.tool
def list_expense():
    'List the expenses'
    with connect() as c:
        cur = c.execute("SELECT date,amount,category,note FROM expense ORDER BY id ASC")
        return rows_as_dicts(cur)

@mcp_server.tool
def list_expense_bydate(st_date,end_date):
     'List the expense between a start date and end date'
     with connect() as c:
            cur = c.execute("""SELECT date,amount,category,note FROM expense WHERE date BETWEEN %s AND %s ORDER BY id ASC""",(st_date,end_date))
            return rows_as_dicts(cur)

@mcp_server.tool
def summarize(st_date,end_date,category= None):
    'Summarize the expense withbin some dates'
    with connect() as c:
                query = ("""SELECT category, SUM(amount) AS total_expense_per_categors FROM expense WHERE date BETWEEN %s AND %s """ )
                parameters =[st_date,end_date]
                if category:
                     query += "AND category = %s "
                     parameters.append(category)

                query+= "GROUP BY category ORDER BY category ASC "
                cur = c.execute(query,parameters)
                return rows_as_dicts(cur)

@mcp_server.resource("expense://categories.json", mime_type="application/json")
def categories():
    'categories to add from'
    with open(category_path, "r", encoding="utf-8") as c:
            return c.read()




if __name__ == "__main__":
    mcp_server.run(transport="http", host ="0.0.0.0", port=8000)
