
############################################################################################## GLOBALS THAT YOU NEED TO FILL IN #################################################################################
#OPTIONAL:
#If you want the code to email you, make a gmail account and enable 'less secure apps' 
#Instructions for this are at the below lins.
#https://support.google.com/mail/answer/56256?hl=en
#https://support.google.com/accounts/answer/6010255?hl=en
gmail_user = "test@gmail.com" #Enter the email address you created.
gmail_password = "testPassword213!" #Enter password to your gmail account you made above.
yourEmailAddress = "EnterYourEmail@microsoft.com" #Your real email address you want to receive notifications at.

#REQUIRED:
#Choose a strong password value, something with letters, numbers, case, and characters. 
#You will only ever have to enter this twice, so more complex the better.
authPassword = "H3r#1sAg00dP@ss!"

############################################################################################# DON'T TOUCH BELOW THIS POINT ######################################################################################

from random import randint

import logging

from flask import Flask, render_template, request, Response

import win32com.client as comctl

import time

import os

import threading #background threads

import smtplib #for sending emails

import datetime #for hash

import time

import sys, struct, socket

import hashlib #for hasing

from threading import Thread

import traceback #for traceback error logging

#create window shell object
wsh = comctl.Dispatch("WScript.Shell")

#big time error var
bigTimeError = 0
AuthKeyTime = None


################################################################################################# Worker Threads #################################################################################################


def RestartWorker():
    wsh.run('shutdown.exe /f /r /t 15 /c "ALEXA RESTART"')
    return


def ShutdownWorker():
    wsh.run('shutdown /f /s /t 15 /c "ALEXA SHUTDOWN"')
    return

################################################################################## Auth \ Intent Functions ##################################################################################################

def AuthKeys():
    while(1):
        try:
            global AuthSignature
            global AuthKeyTime
            global authPassword
            AuthSignature = []
            now = datetime.datetime.utcnow()
            AuthKeyTime = now
            #Edits for twice a day chromecast 
            normalHour = now.hour
            normalMin = now.minute
            normalYear = now.year
            normalMonth = now.month
            normalDay = now.day
            hourT = str(normalHour)
            minuteT = str(normalMin)
            #Current Min Seed
            seedValue = str(normalYear) + str(normalMonth) + str(normalDay) + str(normalHour) + str(normalMin)
            seedValueOrig = str(normalYear) + " " + str(normalMonth) + " " + str(normalDay) + " " + str(normalHour) + " " + str(normalMin)
            seedValue = authPassword + seedValue
            #Next Min Seed \ account for on the hour time issue
            if normalMin + 1 >= 60:
                #increment hour set min to 0
                nextHour = str(normalHour + 1)
                nextMin = "0"
                nextSeedvalue = str(normalYear) + str(normalMonth) + str(normalDay) + str(nextHour) + nextMin
                nextSeedvalueOrig = str(normalYear) + " " + str(normalMonth) + " " + str(normalDay) + " " + str(nextHour) + " " + nextMin
            else:
                #increment min 
                nextMin = str(normalMin + 1)
                nextSeedvalue = str(normalYear) + str(normalMonth) + str(normalDay) + str(normalHour) + nextMin
                nextSeedvalueOrig = str(normalYear) + " " + str(normalMonth) + " " + str(normalDay) + " " + str(normalHour) + " " + nextMin
            nextSeedvalue = authPassword + nextSeedvalue
            AuthSignature = [hashlib.sha256(seedValue.encode()).hexdigest(),hashlib.sha256(nextSeedvalue.encode()).hexdigest()]
            print("\n" + str(now) + "\n" + "Current ({}): {} \n".format(seedValueOrig,AuthSignature[0]) + "Next Minute ({}): {} \n".format(nextSeedvalueOrig,AuthSignature[1]))
            time.sleep(60)
        except Exception as E:
            print(traceback.print_exc())
            print("AUTH FUNCTION CRITICAL FAILURE:",E)

def RestartTime():
    try:
        t = threading.Thread(target=RestartWorker)
        t.start()
        return "EndSess-Good-Rebooting computer, goodbye for now."
    except:
        return "EndSess-Bad-Cannot reboot computer, we ran into an error."


def ShutdownTime():
    try:
        t = threading.Thread(target=ShutdownWorker)
        t.start()
        return "EndSess-Good-Shutting down computer, goodbye for now."
    except:
        return "EndSess-Bad-Issue powering down computer."


def IntentRouter(IntentName,SlotData):
    print("Validating Intent: " + IntentName + "\nSlot Data: " + SlotData)
    if IntentName == "ShutdownIntent":
        return ShutdownTime()
    elif IntentName == "RestartIntent":
        return RestartTime()    
    else:
        #if we have no matching intents we return bad
        print("No Match: " + IntentName + "\nSlot Data: " + SlotData)
        return "Bad-No matching intent."


################################################################################################# Start\Kill Flask App #################################################################################################


print("Creating Flask App")
#Create flask app from class
app = Flask(__name__)

#Start auth thread
if authPassword == "" or authPassword == "H3r#1sAg00dP@ss!":
    #User did not elect a password
    print("\nNo authPassword is set. Check the section in the script (located at the top) for global variables and enter a proper password value.")
    sys.exit()
else:
    print("\nStarting Auth Thread")
    StartAuthThread = Thread(name="AuthKeys",target=AuthKeys)
    StartAuthThread.start()

print("\n\nActive Threads:",threading.enumerate())

def kill_switch():
    time.sleep(2)
    os._exit(1)

############################################################################## Potential Blocking\IO Funcs #################################################################################################


def EmailSomeone(Subject,Body,ToAdd):
    global gmail_user
    global gmail_password
    if gmail_user != "test@gmail.com" and gmail_password != "testPassword213!" and ToAdd != "EnterYourEmail@microsoft.com":
        print("Sending Email To:",ToAdd)
        Body = str(Body)
        sent_from = gmail_user
        to = ToAdd
        body = str("\n\n") + Body

        email_text = "Subject: %s %s" % (Subject, body)
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(sent_from, to, email_text.encode("utf-8"))
            server.close()
            return 'Email sent!'
        except Exception as E:
            return 'Email function error:', E
    else:
        print("Not sending email. If you want an email when the server status changes, use the global variables located at the top of the script.")


################################################################################### Main Flask Func ########################################################################################################


@app.route("/AuthMe", methods=['GET','POST'])
def AuthPage():
    now = str(datetime.datetime.utcnow())
    try:
        global AuthSignature
        global bigTimeError
        global yourEmailAddress
        AuthKeyTime
        #Email Vars
        headinfo = request.headers
        keys = headinfo.get('AuthKeys')
        #headinfo = str(request.headers).encode()
        headinfoE = str(request.headers)
        #remoteaddr = str(request.remote_addr).encode()
        remoteaddre = str(request.remote_addr)
        emailbody = "Someone tried to incorrectly auth:\n\n" + headinfoE + "\nRemote IP: " + remoteaddre
        ioEmail = Thread(target=EmailSomeone, args=("ALEXA ERROR: SOMEONE TRIED TO INCORRECTLY AUTH",emailbody,yourEmailAddress))
        #Main Body
        headinfo = request.headers
        BodyData = request.data
        BodyData = BodyData.decode()
        print("BODY DATA IS:",BodyData)

        if keys == None:
            #Someone sent an authrequest without the proper keys
            print("\nALERT - Bad Auth: No Keys In Header - " + now)
            bigTimeError += 1
            ioEmail.start()
            replytext ="""<!DOCTYPE html>
                        <title>You Have Been Logged</title>
                        <style>
                        div.container {
                        background-color: #ffffff;
                        }
                        div.container p {
                        text-align: Center;
                        font-family: Arial;
                        font-size: 14px;
                        font-style: normal;
                        font-weight: bold;
                        text-decoration: none;
                        text-transform: capitalize;
                        color: #ff0000;
                        background-color: #000000;
                        }
                        </style>

                        <div class="container">
                        <p>You are not authorized to be here. Your browser and IP info has been recorded. </p>
                        </div>"""
            #replytext = "<b>You are not authorized to be here. This request has been logged.</b>"
            if bigTimeError >= 2:
                KillSwitchEngage = Thread(target=kill_switch)
                print("\nEngaging Kill Switch")
                KillSwitchEngage.start()
            return Response(str(replytext),mimetype='text/html')

        #Check the body of the data stream
        if not "Intent" in BodyData:
            #Someone sent an authrequest without the proper keys
            print("\nALERT - Bad Auth: No Intent Keyword In Body - " + now)
            bigTimeError += 1
            ioEmail.start()
            replytext ="""<!DOCTYPE html>
                        <title>You Have Been Logged</title>
                        <style>
                        div.container {
                        background-color: #ffffff;
                        }
                        div.container p {
                        text-align: Center;
                        font-family: Arial;
                        font-size: 14px;
                        font-style: normal;
                        font-weight: bold;
                        text-decoration: none;
                        text-transform: capitalize;
                        color: #ff0000;
                        background-color: #000000;
                        }
                        </style>

                        <div class="container">
                        <p>You are not authorized to be here. Your browser and IP info has been recorded. </p>
                        </div>"""
            #replytext = "<b>You are not authorized to be here. This request has been logged.</b>"
            if bigTimeError >= 2:
                KillSwitchEngage = Thread(target=kill_switch)
                print("\nEngaging Kill Switch")
                KillSwitchEngage.start()
            return Response(str(replytext),mimetype='text/html')      
        #If keys past the null check we split into an array and iterate
        keys = keys.split(",")
        print("\nTime Of Auth Request: {}".format(str(now)))
        for ele in keys:
            print("Comparing",ele," with",AuthSignature)
            if ele in AuthSignature:
                print("\nGood Auth - " + now) 
                #Extract actual intent name payload
                SlotData = BodyData.split(",")[1].split(":")[1]
                IntentName = BodyData.split(",")[0].split(":")[1]
                #IntentRouterThread = Thread(target=IntentRouter, args=(IntentName,))
                #IntentRouterThread.start()
                #SlotData = SlotData.decode()
                #IntentName = IntentName.decode()
                return Response(str(IntentRouter(IntentName,SlotData)),mimetype='text/html')
            else:
                print("\nALERT - Bad Auth: Passed Keys Do Not Match Global - " + now)
                bigTimeError += 1
                ioEmail.start()
                replytext ="""<!DOCTYPE html>
                            <title>You Have Been Logged</title>
                            <style>
                            div.container {
                            background-color: #ffffff;
                            }
                            div.container p {
                            text-align: Center;
                            font-family: Arial;
                            font-size: 14px;
                            font-style: normal;
                            font-weight: bold;
                            text-decoration: none;
                            text-transform: capitalize;
                            color: #ff0000;
                            background-color: #000000;
                            }
                            </style>

                            <div class="container">
                            <p>You are not authorized to be here. Your browser and IP info has been recorded. </p>
                            </div>"""
                #replytext = "<b>You are not authorized to be here. This request has been logged.</b>"
                if bigTimeError >= 2:
                    KillSwitchEngage = Thread(target=kill_switch)
                    print("\nEngaging Kill Switch")
                    KillSwitchEngage.start()
                return Response(str(replytext),mimetype='text/html')
    except Exception as E:
        print("\nALERT - Big error: AuthMe Page - " + now + ": " + str(E))
        print(traceback.print_exc())
        bigTimeError += 1
        #If there is an error here extra
        ioEmail = Thread(target=EmailSomeone, args=("ALEXA ERROR: SOMEONE TRIED TO INCORRECTLY AUTH",emailbody,yourEmailAddress))
        ioEmail.start()
        replytext ="""<!DOCTYPE html>
                    <title>You Have Been Logged</title>
                    <style>
                    div.container {
                    background-color: #ffffff;
                    }
                    div.container p {
                    text-align: Center;
                    font-family: Arial;
                    font-size: 14px;
                    font-style: normal;
                    font-weight: bold;
                    text-decoration: none;
                    text-transform: capitalize;
                    color: #ff0000;
                    background-color: #000000;
                    }
                    </style>

                    <div class="container">
                    <p>You are not authorized to be here. Your browser and IP info has been recorded. </p>
                    </div>"""
        #replytext = "<b>You are not authorized to be here. This request has been logged.</b>"
        #return Response(str("Bad Auth. You have been logged."),mimetype='text/html') 
        if bigTimeError >= 2:
            KillSwitchEngage = Thread(target=kill_switch)
            print("\nEngaging Kill Switch")
            KillSwitchEngage.start()
        return Response(str(replytext),mimetype='text/html')


#########################################################################################  Create APP And Trap Page ########################################################################################
#Establish default trap. Browsing the root or any other page will trap, email me, kill server.
@app.route('/', defaults={'path': ''},methods=['GET','POST'])
@app.route('/<path:path>')
def catch_all(path):
    headinfo = str(request.headers)
    remoteaddr = str(request.remote_addr)
    print("\nALERT - Someone Tried To Access The Root: " + remoteaddr)
    emailbody = "Someone tried to browse the root (Killswitch Engaged):\n\n" + headinfo + "\nRemote IP: " + remoteaddr
    ioEmail = Thread(target=EmailSomeone, args=("ALEXA ERROR: SOMEONE TRIED TO BROWSE THE ROOT",emailbody,yourEmailAddress))
    ioEmail.start()
    replytext ="""<!DOCTYPE html>
                <title>You Have Been Logged</title>
                <style>
                div.container {
                background-color: #ffffff;
                }
                div.container p {
                text-align: Center;
                font-family: Arial;
                font-size: 14px;
                font-style: normal;
                font-weight: bold;
                text-decoration: none;
                text-transform: capitalize;
                color: #ff0000;
                background-color: #000000;
                }
                </style>

                <div class="container">
                <p>You are not authorized to be here. Your browser and IP info has been recorded. </p>
                </div>"""
    #replytext = "<b>You are not authorized to be here. This request has been logged.</b>"
    KillSwitchEngage = Thread(target=kill_switch)
    print("\nEngaging Kill Switch")
    KillSwitchEngage.start()
    return Response(str(replytext),mimetype='text/html')


#Start Web Server
if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, port=50010, host='0.0.0.0', ssl_context='adhoc') #
