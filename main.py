#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 24 13:49:12 2024

@author: akshathaaavinashannadhani
"""

from flask import Flask, render_template, request, redirect, session, flash, jsonify
import os
import pandas as pd
import warnings
import support
from collections import defaultdict

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management


@app.route('/')
def login():
    """
    Login page handler.
    If a user is already logged in, redirect to home page.
    Otherwise, show the login page.
    """
    if 'user_id' in session:
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:
        return render_template("login.html")


@app.route('/login_validation', methods=['POST'])
def login_validation():
    """
    Handle login validation.
    Check user credentials and log in if valid.
    """
    if 'user_id' not in session:
        email = request.form.get('email')
        passwd = request.form.get('password')
        query = """SELECT * FROM user_login WHERE email = '{}' AND password = '{}'""".format(email, passwd)
        users = support.execute_query("search", query)
        if users:
            session['user_id'] = users[0][0]
            return redirect('/home')
        else:
            flash("Invalid email and password!")
            return redirect('/')
    else:
        flash("Already a user is logged-in!")
        return redirect('/home')


@app.route('/reset', methods=['POST'])
def reset():
    if 'user_id' not in session:
        email = request.form.get('femail')
        pswd = request.form.get('pswd')
        userdata = support.execute_query('search', """SELECT * FROM user_login WHERE email = '{}'""".format(email))
        if userdata:
            try:
                query = """UPDATE user_login SET password = '{}' WHERE email = '{}'""".format(pswd, email)
                support.execute_query('insert', query)
                flash("Password has been changed!")
                return redirect('/')
            except:
                flash("Something went wrong!")
                return redirect('/')
        else:
            flash("Invalid email address!")
            return redirect('/')
    else:
        return redirect('/home')


@app.route('/register')
def register():
    if 'user_id' in session:
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:
        return render_template("register.html")


@app.route('/registration', methods=['POST'])
def registration():
    if 'user_id' not in session:
        name = request.form.get('name')
        email = request.form.get('email')
        passwd = request.form.get('password')
        if len(name) > 5 and len(email) > 10 and len(passwd) > 5:
            try:
                query = """INSERT INTO user_login(username, email, password) VALUES('{}', '{}', '{}')""".format(name, email, passwd)
                support.execute_query('insert', query)
                user = support.execute_query('search', """SELECT * FROM user_login WHERE email = '{}'""".format(email))
                session['user_id'] = user[0][0]
                flash("Successfully Registered!")
                return redirect('/home')
            except:
                flash("Email id already exists, use another email!")
                return redirect('/register')
        else:
            flash("Not enough data to register, try again!")
            return redirect('/register')
    else:
        flash("Already a user is logged-in!")
        return redirect('/home')


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/feedback', methods=['POST'])
def feedback():
    flash("Thanks for reaching out to us. We will contact you soon.")
    return redirect('/')


@app.route('/home')
def home():
    """
    Home page handler.
    Display user information, expense summary, and monthly budget.
    """
    if 'user_id' in session:
        budget = session.get('budget', 1000)  # Use the budget from the session, or default to 1000 if it's not set
        query = """SELECT * FROM user_login WHERE user_id = {}""".format(session['user_id'])
        userdata = support.execute_query("search", query)

        table_query = """SELECT * FROM user_expenses WHERE user_id = {} ORDER BY pdate DESC""".format(session['user_id'])
        table_data = support.execute_query("search", table_query)
        df = pd.DataFrame(table_data, columns=['#', 'User_Id', 'Date', 'Expense', 'Amount', 'Note'])
        df = support.generate_df(df)

        try:
            earning, spend, invest, saving = support.top_tiles(df)
        except:
            earning, spend, invest, saving = 0, 0, 0, 0

        monthly_data = support.get_monthly_spendings_and_savings(df, budget)

        return render_template('home.html',
                               user_name=userdata[0][1],
                               df_size=df.shape[0],
                               df=jsonify(df.to_json()),
                               earning=earning,
                               spend=spend,
                               invest=invest,
                               saving=saving,
                               table_data=table_data[:4],
                               monthly_data=monthly_data,
                               budget=budget)
    else:
        return redirect('/')


@app.route('/home/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            date = request.form.get('e_date')
            expense = request.form.get('e_type')
            amount = request.form.get('amount')
            notes = request.form.get('notes')
            try:
                query = """INSERT INTO user_expenses (user_id, pdate, expense, amount, pdescription) VALUES 
                ({}, '{}','{}',{},'{}')""".format(user_id, date, expense, amount, notes)
                support.execute_query('insert', query)
                flash("Saved!")
            except:
                flash("Something went wrong.")
                return redirect("/home")
            return redirect('/home')
    else:
        return redirect('/')
    
@app.route('/delete_expense', methods=['POST'])
def delete_expense():
    """
    Handle deletion of an expense record.
    """
    if 'user_id' in session:
        expense_id = request.form.get('expense_id')
        try:
            query = """DELETE FROM user_expenses WHERE id = {}""".format(expense_id)
            support.execute_query('insert', query)
            flash("Record deleted successfully!")
        except Exception as e:
            flash("Something went wrong. Could not delete the record.")
            print(e)
        return redirect('/home')
    else:
        return redirect('/')
    
@app.route('/home/update_expense', methods=['POST'])
def update_expense():
    """
    Handle the update of an expense record.
    """
    if 'user_id' in session:
        expense_id = request.form.get('expense_id')
        date = request.form.get('e_date')
        expense = request.form.get('e_type')
        amount = request.form.get('amount')
        notes = request.form.get('notes')
        
        try:
            query = """UPDATE user_expenses SET pdate = '{}', expense = '{}', amount = {}, pdescription = '{}' WHERE id = {}""".format(date, expense, amount, notes, expense_id)
            support.execute_query('insert', query)
            flash("Record updated successfully!")
        except Exception as e:
            flash("Something went wrong. Could not update the record.")
            print(e)
        return redirect('/home')
    else:
        return redirect('/')
    
@app.route('/budget_input', methods=['GET', 'POST'])
def budget_input():
    """
    Budget input page handler.
    Display a form for the user to input their budget.
    """
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        budget = request.form.get('budget')
        if budget.isdigit():
            session['budget'] = int(budget)
            return redirect('/home')
    return render_template('budget_input.html')




@app.route('/logout')
def logout():
    try:
        session.pop("user_id")  # delete the user_id in session (deleting session)
        return redirect('/')
    except Exception as e:  # Catching exception in case user_id not in session
        print(e)
        return redirect('/')
        

if __name__ == "__main__":
    app.run(debug=True)
