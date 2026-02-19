from flask import Flask, render_template_string
import sqlite3
from config import settings  # Assumes your settings include DATABASE_NAME

app = Flask(__name__)
DATABASE = settings.DATABASE_NAME


def get_db_connection():
    """Create a new database connection with row_factory set for dictionary-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Fetch data from all tables and render them in an HTML page using Bootstrap."""
    conn = get_db_connection()

    # Get all records from each table
    players = conn.execute('SELECT * FROM player').fetchall()
    games = conn.execute('SELECT * FROM game').fetchall()
    matches = conn.execute('SELECT * FROM Matches').fetchall()
    mvp_votes = conn.execute('SELECT * FROM MVP_Votes').fetchall()

    conn.close()

    # Render a simple HTML page with Bootstrap styling for the tables.
    return render_template_string("""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Discord Tournament DB Viewer</title>
        <!-- Bootstrap CSS -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
          body {
            padding-top: 20px;
          }
          h1 {
            margin-bottom: 40px;
          }
          .table-container {
            margin-bottom: 40px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1 class="text-center">Discord Tournament Database</h1>

          <div class="table-container">
            <h2>Players</h2>
            {% if players %}
            <table class="table table-striped table-bordered">
              <thead class="thead-dark">
                <tr>
                  {% for col in players[0].keys() %}
                  <th scope="col">{{ col }}</th>
                  {% endfor %}
                </tr>
              </thead>
              <tbody>
                {% for row in players %}
                <tr>
                  {% for col in row.keys() %}
                  <td>{{ row[col] }}</td>
                  {% endfor %}
                </tr>
                {% endfor %}
              </tbody>
            </table>
            {% else %}
              <p>No players found.</p>
            {% endif %}
          </div>

          <div class="table-container">
            <h2>Games</h2>
            {% if games %}
            <table class="table table-striped table-bordered">
              <thead class="thead-dark">
                <tr>
                  {% for col in games[0].keys() %}
                  <th scope="col">{{ col }}</th>
                  {% endfor %}
                </tr>
              </thead>
              <tbody>
                {% for row in games %}
                <tr>
                  {% for col in row.keys() %}
                  <td>{{ row[col] }}</td>
                  {% endfor %}
                </tr>
                {% endfor %}
              </tbody>
            </table>
            {% else %}
              <p>No games found.</p>
            {% endif %}
          </div>

          <div class="table-container">
            <h2>Matches</h2>
            {% if matches %}
            <table class="table table-striped table-bordered">
              <thead class="thead-dark">
                <tr>
                  {% for col in matches[0].keys() %}
                  <th scope="col">{{ col }}</th>
                  {% endfor %}
                </tr>
              </thead>
              <tbody>
                {% for row in matches %}
                <tr>
                  {% for col in row.keys() %}
                  <td>{{ row[col] }}</td>
                  {% endfor %}
                </tr>
                {% endfor %}
              </tbody>
            </table>
            {% else %}
              <p>No matches found.</p>
            {% endif %}
          </div>

          <div class="table-container">
            <h2>MVP Votes</h2>
            {% if mvp_votes %}
            <table class="table table-striped table-bordered">
              <thead class="thead-dark">
                <tr>
                  {% for col in mvp_votes[0].keys() %}
                  <th scope="col">{{ col }}</th>
                  {% endfor %}
                </tr>
              </thead>
              <tbody>
                {% for row in mvp_votes %}
                <tr>
                  {% for col in row.keys() %}
                  <td>{{ row[col] }}</td>
                  {% endfor %}
                </tr>
                {% endfor %}
              </tbody>
            </table>
            {% else %}
              <p>No MVP votes found.</p>
            {% endif %}
          </div>
        </div>
        <!-- Optional JavaScript for Bootstrap -->
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
      </body>
    </html>
    """, players=players, games=games, matches=matches, mvp_votes=mvp_votes)


if __name__ == '__main__':
    app.run(debug=True)
