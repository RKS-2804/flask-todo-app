# app.py
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
# Use PyMySQL with configuration loaded from environment variables.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)

class Todo(db.Model):
    '''Class to access todo db column.'''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"

@app.route('/', methods=['GET', 'POST'])
def home():
    '''Function responsible to display and manage task at home page.'''
    if request.method == 'POST':
        title = request.form['title'].strip()
        desc = request.form['desc'].strip()

        if not title or not desc:
            flash("Please fill in both the title and description.", "danger")
        else:
            # Check if a Todo with the same title already exists.
            existing_todo = Todo.query.filter_by(title=title).first()
            if existing_todo:
                flash("A Todo with that title already exists. Please choose a different title.", "danger")
            else:
                todo = Todo(title=title, desc=desc)
                db.session.add(todo)
                db.session.commit()
                flash("Todo added successfully!", "success")
                return redirect(url_for('home'))

    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of todos per page
    allTodo = Todo.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('index.html', allTodo=allTodo)

@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    '''Function to update todo.'''
    todo = Todo.query.get_or_404(sno)
    if request.method == 'POST':
        title = request.form['title'].strip()
        desc = request.form['desc'].strip()

        if not title or not desc:
            flash("Please fill in both the title and description.", "danger")
        else:
            # Check for duplicate title in update scenario.
            if title != todo.title:
                existing_todo = Todo.query.filter_by(title=title).first()
                if existing_todo:
                    flash("A Todo with that title already exists. Please choose a different title.", "danger")
                    return redirect(url_for('update', sno=sno))
            
            todo.title = title
            todo.desc = desc
            db.session.commit()
            flash("Todo updated successfully!", "success")
            return redirect(url_for('home'))
    
    return render_template('update.html', todo=todo)

@app.route('/delete/<int:sno>')
def delete(sno):
    '''Function to delete todo.'''
    todo = Todo.query.get_or_404(sno)
    db.session.delete(todo)
    db.session.commit()
    flash("Todo deleted successfully!", "success")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, port=8000)
