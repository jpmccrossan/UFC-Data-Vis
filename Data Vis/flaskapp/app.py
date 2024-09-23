from flask import Flask, render_template, current_app, g, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connections
DATABASE_FIGHTERS = 'var/Fighter_Data.db'
db = sqlite3.connect(DATABASE_FIGHTERS)

# Database connection function
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_FIGHTERS)
        g.db.row_factory = sqlite3.Row
    return g.db

# Close database connection at the end of each request
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weight_class', methods=['GET'])
def weight_classes():
    weights = []
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT DISTINCT Weight_Class FROM Clean_Fighter_Data')
        weights = [weight[0] for weight in cursor.fetchall()]
        
    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")
    return render_template('weight_classes.html', weights=weights)



@app.route('/weight_class_data', methods=['GET'])
def weight_class_data():
    weight = request.args.get('weight', None)
    # fighters in order of rank for weight class using get_data():
    fighters_names_in_rank_order = []
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT Name FROM Clean_Fighter_Data WHERE Weight_Class = ? ORDER BY Rank_In_Weight_Class ASC', (weight,))
        rows = cursor.fetchall()
        for row in rows:
            fighters_names_in_rank_order.append({'Name': row[0]})
    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")

    # Adapt fighters in rank order to [name:[stat1_name: stat1, stat2_name: stat2, ...], ...]
    fighters_stats = []
    for fighter in fighters_names_in_rank_order:
        fighter_stats = {}
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT * FROM Clean_Fighter_Data WHERE Name = ?', (fighter['Name'],))
            row = cursor.fetchone()
            if row:
                for i, value in enumerate(row):
                    fighter_stats[cursor.description[i][0]] = value
        except Exception as e:
            current_app.logger.error(f"An error occurred: {str(e)}")
        fighters_stats.append(fighter_stats)

    # Get average stats for weight class
    weight_class_stats_average_stats = {}
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Clean_Fighter_Data WHERE Weight_Class = ?', (weight,))
        rows = cursor.fetchall()
        for row in rows:
            for i, value in enumerate(row):
                if isinstance(value, (int, float)):
                    if cursor.description[i][0] in weight_class_stats_average_stats:
                        weight_class_stats_average_stats[cursor.description[i][0]] += value
                    else:
                        weight_class_stats_average_stats[cursor.description[i][0]] = value

        for key in weight_class_stats_average_stats:
            if not isinstance(weight_class_stats_average_stats[key], (int, float)):
                weight_class_stats_average_stats[key] = 0

        for key in weight_class_stats_average_stats:
            if isinstance(weight_class_stats_average_stats[key], (int, float)):
                weight_class_stats_average_stats[key] /= len(rows)

        # round stats in weight_class_stats_average_stats to 2 decimal places
        for key in weight_class_stats_average_stats:
            if isinstance(weight_class_stats_average_stats[key], (int, float)):
                weight_class_stats_average_stats[key] = round(weight_class_stats_average_stats[key], 2)
    
    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")
        

    return render_template('weight_class_data.html', weight=weight, fighters_stats=fighters_stats, weight_class_stats_average_stats=weight_class_stats_average_stats)



@app.route('/compare_fighters', methods=['POST', 'GET'])
def compare_fighters():
    if request.method == 'POST':
        selected_fighter1 = request.form.get('fighter1Checkbox')
        selected_fighter2 = request.form.get('fighter2Checkbox')

        fighter1_stats = {}
        fighter2_stats = {}
        column_names = []
        weight_class_stats_average_stats = {}

        try:
            db = get_db()
            cursor = db.cursor()
            
            # Fetch column names
            cursor.execute('PRAGMA table_info(Clean_Fighter_Data)')
            column_info = cursor.fetchall()
            column_names = [info[1] for info in column_info]

            # Fetch fighter1 stats
            cursor.execute('SELECT * FROM Clean_Fighter_Data WHERE Name = ?', (selected_fighter1,))
            row = cursor.fetchone()  # Fetch only one row

            # Map column names to values in dictionary
            if row:
                fighter1_stats = dict(zip(column_names, row))

            # Fetch fighter2 stats
            cursor.execute('SELECT * FROM Clean_Fighter_Data WHERE Name = ?', (selected_fighter2,))
            row = cursor.fetchone()  # Fetch only one row

            if row:
                fighter2_stats = dict(zip(column_names, row))
                
        except Exception as e:
            current_app.logger.error(f"An error occurred: {str(e)}")
            return "An error occurred while fetching fighter stats."
        
        # Get average stats for weight class
        try:
            weight = fighter1_stats.get('Weight_Class')
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT * FROM Clean_Fighter_Data WHERE Weight_Class = ?', (weight,))
            rows = cursor.fetchall()
            for row in rows:
                for i, value in enumerate(row):
                    if isinstance(value, (int, float)):
                        if cursor.description[i][0] in weight_class_stats_average_stats:
                            weight_class_stats_average_stats[cursor.description[i][0]] += value
                        else:
                            weight_class_stats_average_stats[cursor.description[i][0]] = value

            for key in weight_class_stats_average_stats:
                if not isinstance(weight_class_stats_average_stats[key], (int, float)):
                    weight_class_stats_average_stats[key] = 0

            for key in weight_class_stats_average_stats:
                if isinstance(weight_class_stats_average_stats[key], (int, float)):
                    weight_class_stats_average_stats[key] /= len(rows)

            # round stats in weight_class_stats_average_stats to 2 decimal places
            for key in weight_class_stats_average_stats:
                if isinstance(weight_class_stats_average_stats[key], (int, float)):
                    weight_class_stats_average_stats[key] = round(weight_class_stats_average_stats[key], 2)
        

        except Exception as e:
            current_app.logger.error(f"An error occurred: {str(e)}")
            return "An error occurred while fetching weight class stats."
        

        if selected_fighter1 and selected_fighter2:
            return render_template('compare_fighters.html', fighter1_stats=fighter1_stats, fighter2_stats=fighter2_stats, weight_class_stats_average_stats=weight_class_stats_average_stats)
        else:
            return "Please select exactly one fighter 1 and one fighter 2."



@app.route('/fighters_in_weight_class', methods=['GET'])
def fighters():
    weight = request.args.get('weight', None)
    fighters_names = []
    fighters_ranks = []
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT Name, Rank_In_Weight_Class FROM Clean_Fighter_Data WHERE Weight_Class = ? ORDER BY Rank_In_Weight_Class ASC', (weight,))
        rows = cursor.fetchall()
        for row in rows:
            fighters_names.append({'Name': row[0]})
            fighters_ranks.append({'Rank': row[1]})
    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")
    return render_template('fighters_in_weight_class.html', fighters_names=fighters_names, fighters_ranks=fighters_ranks, weight=weight)




@app.route('/get_data/<name>', methods=['GET'])
def get_data(name):
    fighter_stats = {}
    weight_class_stats_averages = {}
    column_names = []

    # Fighter stats
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Fetch column names
        cursor.execute('PRAGMA table_info(Clean_Fighter_Data)')
        column_info = cursor.fetchall()
        column_names = [info[1] for info in column_info]

        # Fetch fighter stats
        cursor.execute('SELECT * FROM Clean_Fighter_Data WHERE Name = ?', (name,))
        row = cursor.fetchone()  # Fetch only one row

        # Map column names to values in dictionary
        if row:
            fighter_stats = dict(zip(column_names, row))

    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")

    # Weight class stats averages
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Fetch column names
        cursor.execute('PRAGMA table_info(Weight_Class_Stats_Averages)')
        column_info = cursor.fetchall()
        column_names = [info[1] for info in column_info]

        # Fetch fighter stats
        cursor.execute('SELECT * FROM Clean_Fighter_Data WHERE Weight_Class = ?', (fighter_stats.get('Weight_Class'),))
        
        # Fetch all rows for the weight class
        rows = cursor.fetchall()

        # If the row contains a number: sum the numbers in the column and divide by the number of rows
        for row in rows:
            for i, value in enumerate(row):
                if isinstance(value, (int, float)):
                    # If the column name is already in the dictionary, add the value to the existing value
                    if column_names[i] in weight_class_stats_averages:
                        weight_class_stats_averages[column_names[i]] += value
                    else:
                        weight_class_stats_averages[column_names[i]] = value

        # Check each column to see if it is a number and if it is not, change it to 0
        for key in weight_class_stats_averages:
            if not isinstance(weight_class_stats_averages[key], (int, float)):
                weight_class_stats_averages[key] = 0

        # Divide the sum of the values by the number of rows to get the average
        for key in weight_class_stats_averages:
            if isinstance(weight_class_stats_averages[key], (int, float)):
                weight_class_stats_averages[key] /= len(rows)

    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")

    return render_template('fighter_data.html', fighter_stats=fighter_stats, weight_class_stats_averages=weight_class_stats_averages)




@app.route('/data_vis_analysis')
def data_vis_analysis():
    return render_template('data_vis_analysis.html')


if __name__ == '__main__':
    app.run(debug=True)

