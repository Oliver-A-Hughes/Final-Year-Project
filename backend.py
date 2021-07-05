import os
import random
import pymongo
import googlemaps
import datetime
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioRestException
from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS

#Setup Flask Framework
app = Flask(__name__)
CORS(app)

#Database Config
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.eCover               # select the database
staff = db.staff                 # select the staff collection
shops = db.shops                 # select the shops collection
coverRequests = db.coverRequests # select the cover requests collection

#API Setup - Values retrieved from envrioment variables.
t_account_sid = os.environ ["TWILIO_ACCOUNT_SID"]
t_auth_token = os.environ ["TWILIO_AUTH_TOKEN"]
g_api_key = os.environ ["GOOGLE_MAPS_API_KEY"]

twilio_client = Client(t_account_sid, t_auth_token)
google_maps_client = googlemaps.Client(g_api_key)


# Creating Cover Requests and Status Management.

#Method to create a new cover request.
@app.route("/api/v1.0/sendmessage", methods=['POST'])
def new_cover_request():

    #Get request filters.
    if request.args.get('travelTime') and request.args.get('distance'):
        travelTime = str(request.args.get('travelTime'))
        distance = str(request.args.get('distance'))
    else:
        return make_response( jsonify( { "error" : "Request is missing data" } ), 400)
    
    distance = distance.lower()
    travelTime = travelTime.lower()

    #Check all required information is in form.
    filter_error = validate_Filters(travelTime, distance)
    if filter_error != None:
        return filter_error
    form_error = validate_coverRequest_form(request.form)
    if form_error != None:
        return form_error

    #Get cover request information.
    role = request.form["role"]
    store = request.form["store"]
    startTime = request.form["startTime"]
    endTime = request.form["endTime"]
    shiftDate =  request.form["date"]
    recipients = getRecipients(distance, travelTime, store)
    passcode = generatePasscode()
   
    #Collect information to be added to database.
    new_cover_request = { "_id" : ObjectId(),
                   "creationDate" : request.form["creationDate"],
                   "store" : store,
                   "role" : role,
                   "startTime" : startTime,
                   "endTime" : endTime,
                   "shiftDate" : shiftDate,
                   "status" : "Open",
                   "recipients" : recipients,
                   "passcode": passcode,
                   "distanceFilter": distance,
                   "timeFilter": travelTime
                }
    
    #Add cover request to the database.
    new_cover_request_id = coverRequests.insert_one(new_cover_request)

    #Send message to every contact in the recipients list.
    for contact in recipients:
         message = twilio_client.messages.create(
                      body=("Hi {}. We are looking for a {} to cover a shift at the {} shop. The shift begins at {} and finishes at {} on {}. \
                      if you are able to fill this role please reply with passcode {}.".format(contact["firstName"],role,store,startTime,endTime,shiftDate,passcode)),
                      from_='+447782506478',
                      to=contact["mobile"]
                     )

    #Return the new cover request URL.  
    new_cover_request_link = "http://localhost:5000/coverrequests/" + str(new_cover_request_id.inserted_id)
    return make_response( jsonify({"url": new_cover_request_link} ), 201)

#Method used to generate a passcode for a new cover request.
def generatePasscode():
    usedPasscodes = []

    #Generate passcode.
    passcode = random.randint(1000, 9999) 
    
    #Get a list of all passcodes currently in use.
    usedPasscodes = []
    for entry in coverRequests.find( {},{"passcode":1}):
            entry['_id'] = str(entry['_id'])
            usedPasscodes.append(entry)

    #If the passcode is used, regenerate the passcode until an available one is found.
    while passcodeAvailability(passcode,usedPasscodes) == False:
        passcode = random.randint(1000, 9999) 
  
    return passcode

#Method used to check passcode availability 
def passcodeAvailability(passcode, passcodeList):
    #Go through each of the used passcodes and compare it the generated passcode.
    #If the passcode is used return False, if the available return True.
        for entry in passcodeList:
            if entry['passcode'] == passcode:
                return False
        else:
            return True

#Method used to get the recipients of a cover request.
def getRecipients(distance, travelTime, store):
    recipientsList = []
    
    #If both filters aren't set, return all staff members.
    if distance == 'n/a' and travelTime == 'n/a':
        for staffMember in staff.find( {}, {"firstName":1, "surname":1, "mobile":1}):
            staffMember['_id'] = str(staffMember['_id'])
            recipientsList.append(staffMember)

    else:
        # Get the stored geographic coordinates for the selected shop
        for stores in shops.find( {}, {"shopName":1, "latitude":1, "longitude":1 }):
            stores['_id'] = str(stores['_id'])
            if stores['shopName'] == store:
                destinationLat = stores['latitude']
                destinationLng = stores['longitude']

        
        #For each staff member, get their stored geographic coordinates. Perform filtering methods based on which filters are set. 
        for staffMember in staff.find( {}, {"firstName":1, "surname":1, "mobile":1, "latitude":1, "longitude":1 }):
            staffMember['_id'] = str(staffMember['_id'])
            departureLat = staffMember['latitude']
            departureLng = staffMember['longitude']
            
            if distance != 'n/a' and travelTime == 'n/a':
                if get_travel_distance(departureLat, departureLng, destinationLat, destinationLng, distance) == True:
                    recipientsList.append(staffMember)
            
            elif distance == 'n/a' and travelTime != 'n/a':
                if get_travel_time(departureLat, departureLng, destinationLat, destinationLng, travelTime) == True:
                    recipientsList.append(staffMember)
            
            elif distance != 'n/a' and travelTime != 'n/a':
                if get_travel_distance(departureLat, departureLng, destinationLat, destinationLng, distance) == True & \
                   get_travel_time(departureLat, departureLng, destinationLat, destinationLng, travelTime) == True:
                    recipientsList.append(staffMember)

    return recipientsList

#Method to filter staff members based on their distance to the shop.
def get_travel_distance(departureLat,departureLng,destinationLat,destinationLng,distanceFilter):

    departure = (departureLat, departureLng)
    destination = (destinationLat, destinationLng)

    result = google_maps_client.distance_matrix(departure, destination, mode='walking', units='imperial')["rows"][0]["elements"][0]["distance"]["text"]
    #Result example: "15.6 mi". Need to remove string. 
    #If distance is less than a mile result will be returned in ft.

    if "mi" in result:
        result = result.replace('mi', '')
    else:
        result = result.replace('ft', '')
        result = float(result) / 5280  #Convert ft to mi. 
    if (float(result) <= float(distanceFilter)):
        return True
    else:
        return False

#Method to filter staff members based on their distance to the shop.
def get_travel_time(departureLat,departureLng,destinationLat,destinationLng,travelTimeFilter):
    departure = (departureLat, departureLng)
    destination = (destinationLat, destinationLng)

    result = google_maps_client.distance_matrix(departure, destination, mode='driving', units='imperial')["rows"][0]["elements"][0]["duration"]["text"]
    # Result example: "2 hours 15 minutes". Need to remove strings and convert hours to minutes.

    if "hours" in result or "hour" in result:
        splitResult = result.split()
        hours = int(splitResult[0])
        hoursIntoMinutes = hours * 60
        minutes = int(splitResult[2])
        convertedTime = hoursIntoMinutes + minutes
        if convertedTime <= int(travelTimeFilter):
            return True
        else: 
            return False
    else:
        splitResult = result.split()
        minutes = int(splitResult[0])
        if minutes <= int(travelTimeFilter):
            return True
        else: 
            return False

#Method used to return the number of recipients for a cover request  
@app.route("/api/v1.0/numberofrecipients", methods=['GET'])
def getNumberOfRecipients():
    numberOfRecipients = [] 
    distance = request.args.get('distance')
    travelTime = request.args.get('travelTime')
    store = str(request.args.get('store'))
    
    #Check that the filters are vailid values.
    validationError = validate_Filters(travelTime, distance)
    if validationError != None:
        return validationError
    
    distance = distance.lower()
    travelTime = travelTime.lower()

    recipients = getRecipients(distance, travelTime, store)
    numberOfRecipients.append(len(recipients))
    return make_response(jsonify(numberOfRecipients),200)

#Method to process SMS messages recieved from a staff member.
@app.route("/api/v1.0/messageresponse", methods=['GET','POST'])
def process_reply():
    requestInformation = []
    senderInformation = []
    followupRecipients = []
    senderNumberWithoutAreaCode = ''
    senderNumberWithAreaCode = ''

    messageContent = request.values.get("Body",None)
    senderNumber = request.values.get("From")
    if "+44" in senderNumber:
        senderNumberWithoutAreaCode = senderNumber.replace('+44', '0')
    else:
        senderNumberWithAreaCode = senderNumber.replace('0', '+44', 1)  
    reply = MessagingResponse()

    #Search the database for a corver request that has a passcode matching the message content.
    #If a database entry is found. Get the contact numbers of all message recipients.
    for entries in coverRequests.find( {}, {"_id":1, "status":1, "passcode":1, "recipients":1}):
            entries['_id'] = str(entries['_id'])
            if str(entries['passcode']) == messageContent:
                requestInformation.append(entries)
                for contact in entries['recipients']:
                    contact['_id'] = str(contact['_id'])
                    if senderNumberWithAreaCode == '':
                        if contact["mobile"] != senderNumber and contact["mobile"] != senderNumberWithoutAreaCode:
                            followupRecipients.append(contact)
                        elif contact["mobile"] == senderNumber or contact["mobile"] == senderNumberWithoutAreaCode:
                            senderInformation.append(contact)
                    else:
                        if contact["mobile"] != senderNumber and contact["mobile"] != senderNumberWithAreaCode:
                            followupRecipients.append(contact)
                        elif contact["mobile"] == senderNumber or contact["mobile"] == senderNumberWithAreaCode:
                            senderInformation.append(contact)
                break
    
    #If a corver request that has a passcode matching the message content is not found. Reply to inform the staff member.
    if requestInformation == []:
         reply.message("No shift was found with that passcode. Please try again")
    
    else:
        # If the request is Open. 
        # Assign the request to the staff member and inform them that they have been assign the position.
        # Inform other recipients that cover has been found and the position is no longer avaliable.
        for entry in requestInformation:
            if entry["status"] == "Open":
                closeRequest(requestInformation, senderInformation)
                reply.message("You have been assigned the shift.")
                informCoverHasBeenFound(requestInformation, followupRecipients)
            else:
                # If the request is not Open. Inform the staff member.
                reply.message("Sorry, this shift is no longer available.")
        
    return str(reply)

#Method used to close and assign a staff member to a cover request.
def closeRequest(requestInformation, senderInformation):
    for contact in senderInformation:
        assigneeName = contact['firstName'] + ' ' + contact['surname']
        assigneeMobile = contact['mobile']
    for entry in requestInformation:
        coverRequests.update_one({'_id': ObjectId(entry['_id'])},{'$set': {
                                                                'status': 'Closed',
                                                                'assigneeName': assigneeName,
                                                                'assigneeMobile': assigneeMobile}})

#Method used to inform staff members that cover has been found and the position is no longer available.
def informCoverHasBeenFound(coverDetails, followupRecipients):
    passcode = None
    for entry in coverDetails:
        passcode = entry['passcode'] 
    for contact in followupRecipients:
        message = twilio_client.messages.create(
                    body=("Hi {}. The shift associated with Passcode {} has now been filled.".format(contact["firstName"],passcode)),
                    from_='+447782506478',
                    to=contact["mobile"]
                    ) 

#Method used to cancel a request.
@app.route("/api/v1.0/coverhistory/<string:cover_id>/cancel", methods=['PUT'])
def cancelCoverRequest(cover_id):
    #Check the ID supplied is valid.
    id_error = validate_ID(cover_id)
    if id_error != None:
        return id_error
    id_existence_error = valid_coverRequest(cover_id)
    if id_existence_error != None:
        return id_existence_error

    contactList = []
    requestInformation = []

    #Get the recipients of the request.
    for entries in coverRequests.find( {}, {"_id":1, "status":1, "passcode":1, "recipients":1}):
        entries['_id'] = str(entries['_id'])
        if str(entries['_id']) == cover_id:
                requestInformation.append(entries)
                for contact in entries['recipients']:
                    contact['_id'] = str(contact['_id'])
                    contactList.append(contact)
                break
    
    #Check Request is still open
    for entry in requestInformation:
        if entry['status'] != "Open":
            return (make_response(jsonify( {"error" : "Unable to cancel. Request status is no longer 'Open'"}), 400))

    #Cancel the request.
    coverRequests.update_one({'_id': ObjectId(cover_id)},{'$set': {'status': 'Canceled'}})
    
    #Inform recipients that the position is no longer available.
    for entry in requestInformation:
        passcode = entry['passcode']
    for contact in contactList:
        message = twilio_client.messages.create(
                    body=("Hi {}. The shift associated with Passcode {} is no longer available.".format(contact["firstName"],passcode)),
                    from_='+447782506478',
                    to=contact["mobile"]
                    ) 

    return get_single_cover_request(cover_id) 


# Staff Member Functionality

#Method to add a staff member to the database.
@app.route("/api/v1.0/staffmembers", methods=['POST'])
def add_staff_member():
    #Check all required information is in form.
    form_error = validate_staff_form(request.form)
    if form_error != None:
        return form_error

    #Geocode provided address
    address = request.form["address"]
    city = request.form["city"]                              
    region = request.form["region"]
    

    try:
        latitude,longitude = get_address_coordinates(address,city,region)
    except IndexError:
        return(make_response(jsonify( {"error" : "Unable to locate address"}), 404))
    
    #Validate provided phone number
    mobile = request.form["mobile"]
    mobile_error = validate_mobile_number(mobile)
    if mobile_error != None:
        return mobile_error

    #Prepare staff member information for database.
    newStaffMember = { "_id" : ObjectId(),
                   "firstName" : request.form["firstName"],
                   "surname" : request.form["surname"],
                   "address" : address,
                   "city" : city,
                   "region" : region,
                   "latitude": latitude,
                   "longitude": longitude,
                   "mobile" : mobile
                 }
    
    #Add staff member to the database and return the staff member URL.
    new_staff_id = staff.insert_one(newStaffMember)
    new_staff_link = "http://localhost:5000/addstaff/" + str(new_staff_id.inserted_id)
    return make_response( jsonify({"url": new_staff_link} ), 201)

#Method to get all staff members from the database.
@app.route("/api/v1.0/staffmembers", methods=['GET'])
def get_staff_members():
    data_to_return = []
    for employees in staff.find( {},{"_id":1, "firstName":1, "surname":1, "address":1, "city":1, "region":1, "mobile":1}) \
    .sort("surname", pymongo.ASCENDING):
        employees['_id'] = str(employees['_id'])
        data_to_return.append(employees)
    return make_response(jsonify(data_to_return),200)

#Method to get a single staff member from the database.
@app.route("/api/v1.0/staffmembers/<string:staff_id>", methods=['GET'])
def get_single_staff_member(staff_id):
    #Check the ID supplied is valid.
    id_error = validate_ID(staff_id)
    if id_error != None:
        return id_error
    id_existence_error = valid_StaffMember(staff_id)
    if id_existence_error != None:
        return id_existence_error
    
    data_to_return = []
    employee = staff.find_one({'_id':ObjectId(staff_id)}, {"_id":1,"firstName":1, "surname":1, "address":1, "city":1, 
                                                                "region":1, "mobile":1})
    employee['_id'] = str(employee['_id'])
    data_to_return.append(employee) 
    return make_response( jsonify( data_to_return ), 200 )

#Method to edit an exiting staff member stored in the database.
@app.route("/api/v1.0/staffmembers/<string:staff_id>", methods=['PUT'])
def edit_staff_member(staff_id):

    #Check the ID supplied is valid.
    id_error = validate_ID(staff_id)
    if id_error != None:
        return id_error
    id_existence_error = valid_StaffMember(staff_id)
    if id_existence_error != None:
        return id_existence_error
    
    #Check all required information is in form.
    form_error = validate_staff_form(request.form)
    if form_error != None:
        return form_error

    #Validate provided phone number
    mobile = request.form["mobile"]
    mobile_error = validate_mobile_number(mobile)
    if mobile_error != None:
        return mobile_error

    #Geocode provided address
    address = request.form["address"]
    city = request.form["city"]                              
    region = request.form["region"]
    
    try:
        latitude,longitude = get_address_coordinates(address,city,region)
    except IndexError:
        return(make_response(jsonify( {"error" : "Unable to locate address"}), 404))

    #Prepare staff member information for database.
    staff.update_one({ "_id" : ObjectId(staff_id)},{
        "$set": {  "firstName" : request.form["firstName"],
                   "surname" : request.form["surname"],
                   "address" : address,
                   "city" : city,
                   "region" : region,
                   "latitude": latitude,
                   "longitude": longitude,
                   "mobile" : mobile
                 }
    })

    #Return URL of updated staff member
    edited_employee_link = "http://localhost:5000/api/v1.0/staffmembers/" + staff_id 
    return make_response (jsonify ( {"url":edited_employee_link} ),200)

#Method to delete an exiting staff member from the database.
@app.route("/api/v1.0/staffmembers/<string:staff_id>", methods=['DELETE'])
def delete_staff_member(staff_id):
    #Check the ID supplied is valid.
    id_error = validate_ID(staff_id)
    if id_error != None:
        return id_error
    id_existence_error = valid_StaffMember(staff_id)
    if id_existence_error != None:
        return id_existence_error

    staff.delete_one( { "_id" : ObjectId(staff_id) } )
    return make_response( jsonify( {} ),204)
    
# Cover Request History Functionality

#Method to get all cover requests stored in the database.
@app.route("/api/v1.0/coverhistory", methods=['GET'])
def get_cover_requests():
    data_to_return = []
    for entries in coverRequests.find( {},{"_id":1, "creationDate":1, "store":1, "role":1, "startTime":1, "endTime":1, \
                                            "shiftDate":1, "status":1, "recipients":1}) \
                                            .sort("creationDate", pymongo.DESCENDING):
        entries['_id'] = str(entries['_id'])
        for recipients in entries['recipients']:
            recipients['_id'] = str(recipients['_id'])
        data_to_return.append(entries)
    return make_response(jsonify(data_to_return),200)

#Method to get a single cover request stored in the database.
@app.route("/api/v1.0/coverhistory/<string:cover_id>", methods=['GET'])
def get_single_cover_request(cover_id):
    #Check the ID supplied is valid.
    id_error = validate_ID(cover_id)
    if id_error != None:
        return id_error
    id_existence_error = valid_coverRequest(cover_id)
    if id_existence_error != None:
        return id_existence_error

    data_to_return = []
    entry = coverRequests.find_one({'_id':ObjectId(cover_id)}, {"_id":1, "creationDate":1, "store":1, "role":1, "startTime":1, 
                                                                "endTime":1, "shiftDate":1, "timeFilter":1, "distanceFilter":1, "status":1, "recipients":1, 
                                                                'assigneeName':1, "assigneeMobile":1})

    entry['_id'] = str(entry['_id'])
    data_to_return.append(entry) 
    return make_response( jsonify( data_to_return ), 200 )


# Shop Functionality

#Method to add a shop to the database.
@app.route("/api/v1.0/shops", methods=['POST'])
def add_shop():

    #Check all required information is in form.
    form_error = validate_shop_form(request.form)
    if form_error != None:
        return form_error

    #Geocode provided address
    address = request.form["address"]
    city = request.form["city"]                              
    region = request.form["region"]

    try:
        latitude,longitude = get_address_coordinates(address,city,region)
    except IndexError:
        return(make_response(jsonify( {"error" : "Unable to locate address"}), 404))


    #Prepare shop information for database.
    newShop = { "_id" : ObjectId(),
                   "shopName" : request.form["shopName"],
                   "address" : address,
                   "city" : city,
                   "region" : region,
                   "latitude": latitude,
                   "longitude": longitude
                 }
    
    #Add shop to the database and return the shop URL.
    new_shop_id = shops.insert_one(newShop)
    new_shop_link = "http://localhost:5000/shops/" + str(new_shop_id.inserted_id)
    return make_response( jsonify({"url": new_shop_link} ), 201)

#Method to get all shops stored in the database.
@app.route("/api/v1.0/shops", methods=['GET'])
def get_shops():
    data_to_return = []
    for entries in shops.find( {},{"_id":1, "shopName":1, "address":1, "city":1, "region":1, "latitude":1, "longitude":1}) \
    .sort("shopName", pymongo.ASCENDING):
        entries['_id'] = str(entries['_id'])
        data_to_return.append(entries)
    return make_response(jsonify(data_to_return),200)

#Method to get a single shop stored in the database.
@app.route("/api/v1.0/shops/<string:shop_id>", methods=['GET'])
def get_single_shop(shop_id):

    #Check the ID supplied is valid.
    id_error = validate_ID(shop_id)
    if id_error != None:
        return id_error
    id_existence_error = valid_shop(shop_id)
    if id_existence_error != None:
        return id_existence_error

    data_to_return = []
    entry = shops.find_one({'_id':ObjectId(shop_id)}, {"_id":1, "shopName":1, "address":1, "city":1, "region":1, 
                                                        "latitude":1, "longitude":1})

    entry['_id'] = str(entry['_id'])
    data_to_return.append(entry) 
    return make_response( jsonify( data_to_return ), 200 )

#Method to get the names of all shops stored in the database.
@app.route("/api/v1.0/shops/names", methods=['GET'])
def get_shop_names():
    data_to_return = []
    for store in shops.find( {}, \
            {"shopName":1}) \
                .sort("shopName", pymongo.ASCENDING):
            store['_id'] = str(store['_id'])
            data_to_return.append(store)
    
    return make_response(jsonify(data_to_return),200)

#Method to edit a shop that is stored in the database. 
@app.route("/api/v1.0/shops/<string:shop_id>", methods=['PUT'])
def edit_shop(shop_id):
    #Check the ID supplied is valid.
    id_error = validate_ID(shop_id)
    if id_error != None:
        return id_error
    id_existence_error = valid_shop(shop_id)
    if id_existence_error != None:
        return id_existence_error

    #Check all required information is in form.
    form_error = validate_shop_form(request.form)
    if form_error != None:
        return form_error

    #Geocode provided address
    address = request.form["address"]
    city = request.form["city"]                              
    region = request.form["region"]

    try:
        latitude,longitude = get_address_coordinates(address,city,region)
    except IndexError:
        return(make_response(jsonify( {"error" : "Unable to locate address"}), 404))

    #Prepare shop information for database.
    shops.update_one({ "_id" : ObjectId(shop_id)},{
        "$set": {  "shopName" : request.form["shopName"],
                   "address" : address,
                   "city" : city,
                   "region" : region,
                   "latitude": latitude,
                   "longitude": longitude
                 }
    })

    #Return URL of updated shop
    edited_shop_link = "http://localhost:5000/api/v1.0/shops/" + shop_id 
    return make_response (jsonify ( {"url":edited_shop_link} ),200)

#Method to delete a shop from the database. 
@app.route("/api/v1.0/shops/<string:shop_id>", methods=['DELETE'])
def delete_shop(shop_id):
     #Check the ID supplied is valid.
    id_error = validate_ID(shop_id)
    if id_error != None:
        return id_error
    id_existence_error = valid_shop(shop_id)
    if id_existence_error != None:
        return id_existence_error

    shops.delete_one( { "_id" : ObjectId(shop_id) } )
    return make_response( jsonify( {} ),204)


# Shared Functionality

#Method used to get the geographic coordinates of a provided address. 
def get_address_coordinates(address, city, region):
    fullAddress = address + "," + city + "," + region
    geocode_result = google_maps_client.geocode(fullAddress)
    result = geocode_result[0]

    latitude = result['geometry']['location']['lat']
    longitude = result['geometry']['location']['lng']

    return latitude, longitude


# Validation / Error Handling

#Check the time and distance filters to ensure they are valid values.
def validate_Filters(travelTime, distance):
    if travelTime.lower() != 'n/a':
        try:
            travelTime = int(travelTime)
        except ValueError:
            return(make_response(jsonify( {"error" : "Time filter must equal a numerical value or N/A"}), 400))

    if distance.lower() != 'n/a':
        try:
            distance = float(distance)
        except ValueError:
            return(make_response(jsonify( {"error" : "Distance filter must equal a numerical value or N/A"}), 400))
    
    
#Check a supplied ID is the correct format.
def validate_ID(_id):
    # Check ID is correct length
    if len(_id) != 24:
        return make_response(jsonify( {"error" : "Invalid ID format"}), 400)
    
    #Check ID is valid hexadecimal
    valid_hex = ['0','1','2','3','4','5','6','7','8','9',
                    'A','B','C','D','E','F',
                    'a','b','c','d','e','f']
    for value in _id:
            if value not in valid_hex:
                return make_response(jsonify( {"error" : "Invalid ID format"}), 400)
    
    #If no errors are found return None
    return None

def valid_StaffMember(_id):
    #Check staff ID exists in database.
    employee = staff.find_one({'_id':ObjectId(_id)})
    if employee is None:
        return make_response(jsonify( {"error" : "Invalid staff ID"}),404)
    
    #If no errors are found return None
    return None

def validate_staff_form(form):
    #Check required data is present in submitted form.
    if "firstName" not in form or "surname" not in form or "address" not in form or "city" not in form or "region" not in form \
    or "mobile" not in form:
        return make_response( jsonify( { "error" : "Missing form data" } ), 400)
    else:
        return None

def validate_mobile_number(mobile):
    #Check that a supplied mobile phone number is valid
    if "+44" not in mobile:
        mobile = mobile.replace('0', '+44', 1)  
    try:
        response = twilio_client.lookups.phone_numbers(mobile).fetch(type="carrier")
        return None
    except TwilioRestException as exception:
        # Exception code 20404 = HTTP 404
        if exception.code == 20404:
            return make_response( jsonify( { "error" : "Invalid mobile phone number provided." } ), 404)

def valid_coverRequest(_id):
    #Check cover request ID exists in database.
    entry = coverRequests.find_one({'_id':ObjectId(_id)})
    if entry is None:
        return make_response(jsonify( {"error" : "Invalid cover request ID"}),404)
    
    #If no errors are found return None
    return None

def validate_coverRequest_form(form):
    #Check required data is present in submitted form.
    if "creationDate" not in form or "store" not in form or "role" not in form or "startTime" not in form or "endTime" not in form \
    or "date" not in form:
        return make_response( jsonify( { "error" : "Missing form data" } ), 400)
    else:
        return None

def valid_shop(_id):
    #Check shop ID exists in database.
    store = shops.find_one({'_id':ObjectId(_id)})
    if store is None:
        return make_response(jsonify( {"error" : "Invalid shop ID"}),404)
    
    #If no errors are found return None
    return None

def validate_shop_form(form):
    #Check required data is present in submitted form.
    if "shopName" not in form or "address" not in form or "city" not in form or "region" not in form:
        return make_response( jsonify( { "error" : "Missing form data" } ), 400)
    else:
        return None

#Run application in debug mode
if __name__ == "__main__":
    app.run(debug=True)



