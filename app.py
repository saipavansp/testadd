from flask import Flask, session, request, jsonify, render_template, redirect, url_for, flash
from flask_pymongo import PyMongo
from pymongo import MongoClient
from flask_cors import CORS
from bson import ObjectId


app = Flask(__name__)
CORS(app)


app.config["MONGO_URI"] = "mongodb+srv://vasudha:vasudha@cluster0.0vkno.mongodb.net/usersDB?authSource=admin&retryWrites=true&w=majority&readPreference=primary"
mongo = PyMongo(app)

try:
    client = MongoClient('mongodb+srv://vasudha:vasudha@cluster0.0vkno.mongodb.net/usersDB?authSource=admin&retryWrites=true&w=majority&readPreference=primary')
    db = client.get_database("usersDB")
    print("Databases:", client.list_database_names())
    print("Connection successful!")
except Exception as e:
    print("Connection failed:", e)

@app.route('/')
def home():
    # Query the 'admin' collection for all scenarios
    scenarios = mongo.db.admin.find()  
    # Render 'index.html' and pass 'scenarios' to it
    return render_template('index.html', scenarios=scenarios)

@app.route('/admindashboard')
def admin_dashboard():
    return render_template('admindashboard.html')

@app.route('/get_prompt', methods=['POST'])
def get_prompt():
    try:
        # Get the selected scenario ID
        request_data = request.json
        print("Received Request Data:", request_data)

        # Get the selected scenario ID
        scenario_id = request.json.get('scenario_id', '')
        print(f"Extracted Scenario ID: {scenario_id}")

        if not scenario_id:
            return jsonify({"error": "No scenario ID provided"}), 400
        
        try:
            object_id = ObjectId(scenario_id)
        except Exception as e:
            print(f"Invalid ObjectId: {e}")
            return jsonify({"error": "Invalid scenario ID format"}), 400
        
        # Query MongoDB for the corresponding prompt
        scenario_data = mongo.db.admin.find_one({"_id": object_id})

        if scenario_data and "prompt" in scenario_data:
            updated_prompt = scenario_data["prompt"]
            return jsonify({"prompt": updated_prompt})
        else:
            return jsonify({"error": "Scenario not found"}), 404
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch prompt"}), 500

@app.route('/index')
def question():
    scenarios = mongo.db.admin.find()
    return render_template('index.html', scenarios=scenarios)

# Route to create a new roleplay scenario
@app.route('/create', methods=['POST'])
def create_scenario():
    try:
        data = request.json
        result = mongo.db.admin.insert_one({
            "scenario": data['scenario'],
            "prompt": data['prompt'],
            "question": data['question']
        })
        return jsonify({"message": "Roleplay created successfully", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error creating scenario: {e}")
        return jsonify({"error": "Failed to create scenario"}), 500

@app.route('/history', methods=['GET'])
def get_history():
    try:
        history = mongo.db.admin.find()
        return jsonify([
            {
                "_id": str(doc['_id']),
                "scenario": doc.get('scenario', ''),
                "prompt": doc.get('prompt', ''),
                "question": doc.get('question', '')
            }
            for doc in history
        ]), 200
    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify({"error": "Failed to fetch history"}), 500

# New route for deleting a single scenario
@app.route('/delete/<scenario_id>', methods=['DELETE'])
def delete_scenario(scenario_id):
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(scenario_id)
        
        # Delete the scenario from MongoDB
        result = mongo.db.admin.delete_one({'_id': object_id})
        
        if result.deleted_count > 0:
            return jsonify({"message": "Scenario deleted successfully"}), 200
        else:
            return jsonify({"error": "Scenario not found"}), 404
            
    except Exception as e:
        print(f"Error deleting scenario: {e}")
        return jsonify({"error": "Failed to delete scenario"}), 500

# New route for batch deletion
@app.route('/delete-batch', methods=['POST'])
def delete_batch():
    try:
        scenario_ids = request.json.get('ids', [])
        if not scenario_ids:
            return jsonify({"error": "No scenarios specified"}), 400

        # Convert string IDs to ObjectIds
        object_ids = [ObjectId(id) for id in scenario_ids]
        
        # Delete multiple scenarios
        result = mongo.db.admin.delete_many({'_id': {'$in': object_ids}})
        
        if result.deleted_count > 0:
            return jsonify({
                "message": f"Successfully deleted {result.deleted_count} scenarios",
                "deleted_count": result.deleted_count
            }), 200
        else:
            return jsonify({"error": "No scenarios found to delete"}), 404
            
    except Exception as e:
        print(f"Error in batch delete: {e}")
        return jsonify({"error": "Failed to delete scenarios"}), 500

if __name__ == '__main__':
    app.run(debug=True)
