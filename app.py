from flask import Flask,redirect,render_template,url_for,request,session
from config import config
from database import mysql
from werkzeug.security import generate_password_hash,check_password_hash
from google import genai



app = Flask(__name__)
app.config.from_object(config)
client=genai.Client(api_key=app.config["GEMINI_API_KEY"])



mysql.init_app(app)

uploads_folder = "uploads"
app.secret_key="recipe_hub"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login",methods=["POST","GET"])
def login():
    if request.method == "POST":
        email=request.form["email"]
        password=request.form["password"]
        cur= mysql.connection.cursor()
        cur.execute("select * from user where email=%s",(email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[4],password):
            session["fullname"] = user[1]
            return redirect("/dashboard")
        else:
            return "Invaild Email or password"
    return render_template("login.html")

@app.route("/register",methods=["POST","GET"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        fullname = request.form["fullname"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        
        cur= mysql.connection.cursor()
        cur.execute("insert into user(email,fullname,password) values(%s,%s,%s)",(email,fullname,hashed_password))
        mysql.connection.commit()
        cur.close()
        return redirect("/login")
    return render_template("register.html")

@app.route("/add_recipe",methods=["GET","POST"])
def add_recipe():
    if "fullname" not in session:
        return redirect("/login")
    if request.method == "POST":
        title=request.form["title"]
        ingredeint=request.form["ingredient"]
        instruction=request.form["instruction"]
        cur=mysql.connection.cursor()
        cur.execute("insert into recipe(title,ingredients,instructions) values(%s,%s,%s)",(title,ingredeint,instruction))
        mysql.connection.commit()
        cur.close()
        return redirect("/dashboard")

    return render_template("add_recipe.html")


@app.route("/about")
def about():
    return render_template("about.html")



@app.route("/dashboard")
def dashboard():
    if "fullname" in session:
        return render_template("dashboard.html",fullname = session["fullname"])
    return redirect("/login")
    

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/recipes")
def recipes():
    if "fullname" not in session:
        return redirect("/login")
    search = request.args.get("search")
    cur = mysql.connection.cursor()
    if search:
        cur.execute("select * from recipe where title like %s",("%" + search + "%",))
        
    else:
        cur.execute("select * from recipe")
    recipes = cur.fetchall()
    cur.close()
    return render_template("recipes.html",recipes=recipes)


@app.route("/ai",methods=["GET","POST"])
def ai():
    recipe=""
    if request.method == "POST":
        ingredients=request.form["ingredeint"]
        prompt=f"""create a detailed recipe using these ingredient:{ingredients} Inculde:
        -Recipe Name,-ingredients,-step-by-step instructions"""
        response=client.models.generate_content(model="gemini-3.6-flash",contents=prompt)

        recipe=response.text
    return render_template("ai.html",recipe=recipe)

@app.route("/recipe_details/<int:id>")
def recipe_details(id):
    if "fullname" not in session:
        return redirect("/login")
    cur=mysql.connection.cursor()
    cur.execute("select * from recipe where id=%s",(id,))
    recipe = cur.fetchone()
    cur.close()
    return render_template("recipe_detail.html",recipe=recipe)

@app.route("/delete_recipe/<int:id>")
def delete_recipe(id):
    if "fullname" not in session:
        return  redirect("/login")
    cur=mysql.connection.cursor()
    cur.execute("delete from recipe where id = %s",(id,))
    mysql.connection.commit()
    cur.close()
    return redirect("/recipes")


    

@app.route("/result")
def result():
    return render_template("result.html")

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)