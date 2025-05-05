from flask import Flask,request,jsonify
from supabase import create_client, Client
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

SUPABASE_URL = "https://oehxlcvgdmoedhljgfpl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9laHhsY3ZnZG1vZWRobGpnZnBsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTIzODE0NSwiZXhwIjoyMDU2ODE0MTQ1fQ.5Fy6wU9-aZGLu59A0dPLqaKcJ_MIgsKO-GKxP6bahpU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route('/get-dropdown-options', methods=['GET'])
def get_dropdown_options():
    try:
        response = supabase.table("bakar").select("height").execute()
        data = response.data  # Make sure response.data is a list of dictionaries
        print("Raw API Response:", data)  # Debugging line
        
        if isinstance(data, list):
            options = [str(item["height"]) for item in data]  # Ensure conversion to strings
        else:
            options = []  # Handle unexpected format

        return jsonify({"options": options})  # Proper JSON format
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@app.route('/get-customers', methods=['GET'])
def get_new_dropdown_options():
    try:
        zbon_or_not = request.args.get('zbon_or_not', default='0')  # Get from query string, default to 0
        print("Received zbon_or_not:", zbon_or_not)  # Debug log

        response = supabase.table("customers") \
            .select("customer_id, customer_name") \
            .eq("zbon_or_not", int(zbon_or_not)) \
            .execute()
        
        data = response.data
        print("Raw API Response:", data)
        
        return jsonify({"options": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/save-inputs', methods=['POST'])
def save_inputs():
    data = request.json  # Receive JSON data
    print("Received Data:", data)  # Debugging
    items = data.get("items", [])  # List of items
    store_bakar(data)
    store_customer_data(data)
    store_moshtarayat_Masarif(data)
    return jsonify({"message": "Data processed successfully", "total_items": len(items)})

def store_bakar(data):
    items = data.get("items", [])  # List of items
    price = data.get("price", "")
    for item in items:
            height = item["dropdown_value"]
            new_weight = float(item["text_input"])  # Convert to float for addition
            print(height,new_weight)
            # Check if the height already exists in the table
            response = supabase.table("storage_bakar").select("weight").eq("hight", int(height)).execute()

            existing_data = response.data
            
            if existing_data:
                # If height exists, update weight (add new weight to existing one)
                existing_weight = float(existing_data[0]["weight"])
                updated_weight = existing_weight + new_weight
                
                supabase.table("storage_bakar").update({"weight": updated_weight}).eq("hight", height).execute()
            
            else:
                # If height doesn't exist, insert a new row
                supabase.table("storage_bakar").insert({
                    "hight": height,
                    "weight": new_weight,
                    "price": price
                }).execute()



def store_moshtarayat_Masarif(data):
    items = data.get("items", [])  # List of items
    price = data.get("price", "")
    date = datetime.datetime.today().strftime("%Y-%m-%d")
    dofaa = data.get("madfoa","")
    factory = data.get("factory", "")
    customer_id = supabase.table("customers").select("customer_id").eq("customer_id", factory).execute()
    customer_id = customer_id.data[0]["customer_id"]

    res=supabase.table("Msarif").insert({
                    "mission_code": 1,
                    "price": dofaa,           
                    "date": date,
                    "notes":" "
                }).execute()
    mission_seq=res.data[0]["mission_seq"]

    for item in items:
            height = item["dropdown_value"]
            new_weight = float(item["text_input"])  # Convert to float for addition
            #  insert a new row
            res=supabase.table("moshtarayat").insert({
                "mission_seq":mission_seq,
                "hight": height,
                "weight": new_weight,
                "price": price,
                "customer_id":customer_id,
                "date":date
            }).execute()



def store_customer_data(data):
        items = data.get("items", [])
        price = float(data.get("price", 0))
        factory = data.get("factory", "")
        madfoa=data.get("madfoa")

        total_weight = sum(float(item["text_input"]) for item in items)  # Sum of all weights

        total_price = total_weight * price  # Calculate total price

        # Fetch the current "ager" value
        customer_data = supabase.table("customers").select("ager").eq("customer_id", factory).execute()
        current_ager = float(customer_data.data[0]["ager"]) if customer_data.data and customer_data.data[0]["ager"] else 0
        current_ager = current_ager - float(madfoa)

        # Add the new total price to the existing "ager"
        new_ager_value = current_ager + total_price

        # Update the "ager" column
        supabase.table("customers").update({"ager": new_ager_value}).eq("customer_id", factory).execute()


@app.route('/get-storage', methods=['GET'])
def get_storage():
    try:
        response = supabase.table("storage_bakar").select("hight, weight").gt("weight", 0).order("hight").execute()
        return jsonify({"data": response.data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-mstsanaa-storage', methods=['GET'])
def get_mstsanaa_storage():
    try:
        response = supabase.table("storage_mtsanaa").select("height_after_tasniaa, width, weight, price,shrit,hanger").gt("weight", 0).order("height_after_tasniaa,width").execute()

        return jsonify({"data": response.data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Route to get `hieght_after_tasniaa` based on `height`
@app.route('/get-tasnia-value', methods=['GET'])
def get_tasnia_value():
    height = request.args.get('height')

    if not height:
        return jsonify({"error": "Height parameter is missing"}), 400

    try:
        print(float(height))
        response = supabase.table("bakar").select("height_after_tasnia").eq("height", int(float(height))).execute()
        print(response.data)

        if response.data:
            return jsonify({"height_after_tasnia": response.data[0]["height_after_tasnia"]})
        else:
            return jsonify({"error": "No matching height found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to save tasnia data
@app.route('/save-tasnia', methods=['POST'])
def save_tasnia():
    #try:
        data = request.json
        height = data.get("height")
        width = data.get("input_value")
        tasnia_value = data.get("tasnia_value")
        price = data.get("price")
        weight=data.get("weight")
        weight_bakr=data.get("weight_bakr")
        ishager=data.get("hanger")
        shrit=data.get("shrit")
        
        print(height,width,tasnia_value,price,weight,weight_bakr)

        if height is None or width is None or tasnia_value is None or price is None  or weight is None or weight_bakr is None:
            return jsonify({"error": "Missing required fields"}), 400

        new_weight=weight_bakr-weight

        # Perform the calculation
        total_value = width * tasnia_value
        print(new_weight)

        response = supabase.table("storage_mtsanaa").select("weight").eq("height_after_tasniaa", float(tasnia_value)).eq("width", float(width)).eq("hanger", ishager).eq("shrit",shrit).execute()

        existing_data = response.data
            
        if existing_data:
                # If height exists, update weight (add new weight to existing one)
                existing_weight = float(existing_data[0]["weight"])
                updated_weight = existing_weight + weight
                
                supabase.table("storage_mtsanaa").update({"weight": updated_weight}).eq("height_after_tasniaa", float(tasnia_value)).eq("width", float(width)).eq("hanger", ishager).eq("shrit",shrit).execute()
            
        else:
        # Insert into `tasnia` table
                response = supabase.table("storage_mtsanaa").insert({
                    "height_after_tasniaa": tasnia_value,
                    "width":width,
                    "weight":weight,
                    "price": price,
                    "hanger": ishager,
                    "shrit": shrit,
                }).execute()

        print("saved1")
        supabase.table("storage_bakar").update({"weight": new_weight}).eq("hight", int(height)).execute()
        print("saved2")
        return jsonify({"message": "Data saved successfully", "total_value": total_value})

@app.route('/storage_mtsanaa')
def get_storage_mtsanaa():
    storage_response = supabase.table('storage_mtsanaa') \
        .select('width, height_after_tasniaa, weight,hanger,shrit,price').execute()
    return jsonify(storage_response.data)


@app.route('/orders')
def get_orders():
    # Step 1: Get all orders
    orders_response = supabase.table("orders").select("mission_seq,Customer_id,date").eq("finished",0).execute()

    orders = orders_response.data

    results = []
    for order in orders:
        mission_seq = order.get('mission_seq')
        customer_id = order.get('Customer_id')
        date=order.get('date')
        # Step 2: Get customer name for the customer_id
        if customer_id is not None:
            customer_response = supabase.table("customers").select("customer_name").eq("customer_id", customer_id).single().execute()
            customer_data = customer_response.data
            customer_name = customer_data['customer_name'] if customer_data else "غير معروف"
        else:
            customer_name = "غير معروف"
        # Step 3: Get order details
        details_response = supabase.table("order_details").select("*").eq("mission_seq", mission_seq).gt("wight", 0).order("hight_after_tasniaa,width").execute()
        details = details_response.data

        results.append({
            "mission_seq": mission_seq,
            "customer_name": customer_name,
            "date":date,
            "details": details
        })

    return jsonify(results)


@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    customer_id = data.get("Customer_id")
    date = data.get("date")  # Expected as 'YYYY-MM-DD'
    details = data.get("details", [])  # List of dicts

    if not customer_id or not date or not details:
        return jsonify({"error": "Missing required fields"}), 400

    # Insert into orders table
    order_response = supabase.table("orders").insert({
        "Customer_id": customer_id,
        "date": date
    }).execute()

    if not order_response.data:
        return jsonify({"error": "Failed to create order"}), 500

    mission_seq = order_response.data[0]['mission_seq']

    # Insert into order_details table
    for item in details:
        item["mission_seq"] = mission_seq

    supabase.table("order_details").insert(details).execute()

    return jsonify({"message": "Order created successfully", "mission_seq": mission_seq})



@app.route('/finish_order', methods=['POST'])
def delete_order():
    data = request.json
    mission_seq = data.get('mission_seq')
    total_price = data.get('total_price')  # Assuming you pass the total price in the request
    print(total_price)

    try:
         # Retrieve the current dofaa value for the given mission_seq
        order = supabase.table('orders').select('dofaa').match({"mission_seq": mission_seq}).execute()

        if order.data:  # If the order exists
            dofaa_value = order.data[0].get('dofaa', None)

            if dofaa_value is None:  # If dofaa is NULL, update it with the total_price
                supabase.table('orders').update({"dofaa": total_price}).match({
                    "mission_seq": mission_seq,
                }).execute()
            else:  # If dofaa is not NULL, add the total_price to the existing value
                updated_dofaa = dofaa_value + total_price
                supabase.table('orders').update({"dofaa": updated_dofaa}).match({
                    "mission_seq": mission_seq,
                }).execute()

            # Mark the order as finished
            supabase.table('orders').update({"finished": True}).match({
                "mission_seq": mission_seq,
            }).execute()

            return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

@app.route('/update_order_weights', methods=['POST'])
def update_order_weights():
    data = request.json
    order_id = data.get('order_id')
    mission_seq = data.get('mission_seq')
    updated_details = data.get('updated_details', [])
    total_price = data.get('total_price')  # Assuming you pass the total price in the request
    print(total_price)
    try:
        order = supabase.table('orders').select('dofaa').match({"mission_seq": mission_seq}).execute()

        if order.data:  # If the order exists
            dofaa_value = order.data[0].get('dofaa', None)

            if dofaa_value is None:  # If dofaa is NULL, update it with the total_price
                supabase.table('orders').update({"dofaa": total_price}).match({
                    "mission_seq": mission_seq,
                }).execute()
            else:  # If dofaa is not NULL, add the total_price to the existing value
                updated_dofaa = dofaa_value + total_price
                supabase.table('orders').update({"dofaa": updated_dofaa}).match({
                    "mission_seq": mission_seq,
                }).execute()

        for detail in updated_details:
            # You need to know how to uniquely identify each detail
            width = detail['width']
            hight = detail['hight_after_tasniaa']
            hanger = detail.get('hanger', False)
            shrit = detail.get('shrit', False)
            weight = detail['wight']
            order_id = detail['order_id']

            # Update matching detail
            supabase.table('order_details').update({"wight": weight}).match({
                "order_id": order_id,
                "width": width,
                "hight_after_tasniaa": hight,
                "hanger": hanger,
                "shrit": shrit
            }).execute()

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route("/subtract_storage_weight", methods=["POST"])
def subtract_from_storage():
    data = request.get_json()
    
    if not isinstance(data, list):
        return jsonify({"error": "Input must be a list of shipment entries"}), 400

    errors = []
    updated = []
    try:
        for item in data:
            print(item.get("shipped_weight"))
            result = supabase.rpc("subtract_storage_weight", {
                "width_param": item.get("width"),
                "height_param": item.get("hight_after_tasniaa"),
                "shipped_weight": item.get("shipped_weight"),
                "hanger_param": item.get("hanger"),
                "shrit_param": item.get("shrit")
            }).execute()

        if getattr(result, 'error', None):
            errors.append({"item": item, "error": str(result.error)})
        else:
            updated.append(item)

        return jsonify({
            "updated": updated,
            "errors": errors
        }), 200
    except Exception as e:
            errors.append({"item": item, "error": str(e)})

    if errors:
        return jsonify({"status": "partial_success", "updated": updated, "errors": errors}), 207

    return jsonify({"status": "success", "updated": updated}), 200



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)


