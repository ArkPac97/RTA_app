from flask import Flask, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Globalny DataFrame na anomalia
anomalies_df = pd.DataFrame()

@app.route('/anomalies/live', methods=['POST'])
def receive_anomaly():
    global anomalies_df
    anomaly = request.json
    
    # Konwersja do DataFrame (pojedynczy rekord)
    new_entry = pd.DataFrame([anomaly])
    
    # Doklejamy do globalnego DataFrame
    anomalies_df = pd.concat([anomalies_df, new_entry], ignore_index=True)
    
    print(f"Nowa anomalia: {anomaly.get('title')} - {anomaly.get('comment')}")
    return jsonify({"status": "ok"}), 200

@app.route('/anomalies', methods=['GET'])
def get_anomalies():
    global anomalies_df
    # Zwracamy JSON z wszystkimi anomaliami
    return anomalies_df.to_json(orient='records'), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
