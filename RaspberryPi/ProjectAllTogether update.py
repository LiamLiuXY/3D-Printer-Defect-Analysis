# Python program to illustrate the concept
# of threading
# importing the threading module
#https://api.telegram.org/bot6414681005:AAF9mqEdZfI3avx3LkuvmC6Iw7FGJxy6PnA/getMe
#API key - 6414681005:AAF9mqEdZfI3avx3LkuvmC6Iw7FGJxy6PnA
    
import multiprocessing as mp
import os
from picamera2 import Picamera2
from libcamera import controls
from LITM import *
import gc
import requests
import RPi.GPIO as GPIO
import Adafruit_DHT
import telebot
import time
import datetime
from picamera2.encoders import H264Encoder
import telegram
import logging
import bcrypt
import subprocess
import os.path
import shlex
from hashlib import pbkdf2_hmac 
import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
state=False
currentstate = False #AI tool current state On is True  Off is False
defectthreshold = 5 #define how many consecutive defects needed before triggering a notification warning 
chatid=''
BOT_TOKEN = os.environ.get('BOT_TOKEN1')
USERNAME= os.environ.get('USERNAME')
PASSWORDUSERNAME= os.environ.get('PASSWORD')
SALT1= os.environ.get('SALT1')
SALT2= os.environ.get('SALT2')
AITOOLMSG="\t !!!Warning Print Error Found!!! \n Please manually review your print, AI tool will be deactivated ,To restart monitoring reactivate AI tool in Camera Menu"


retry = 4 #define the number of retires for video upload
motorPins = (4, 17, 27, 22)    # define pins connected to four phase ABCD of stepper motor
CCWStep = (0x01,0x02,0x04,0x08) # define power supply order for rotating anticlockwise 
CWStep = (0x08,0x04,0x02,0x01)  # define power supply order for rotating clockwise
prevangle = 0
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    # set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def predictor()->str:
    return "Working"


def setup(angle):    
    GPIO.setmode(GPIO.BCM)       # use PHYSICAL GPIO Numbering
    for pin in motorPins:
        GPIO.setup(pin,GPIO.OUT)
    try:

        if (angle=='30' or angle=='45' or angle=='60'):
             moveangleclever(angle)
        else :
             print('invalid angle')
        # while True:
        #     angle = input("Enter Angle\n")
        #     if (angle=='30' or angle=='45' or angle=='60'):
        #        moveangleclever(angle)
        #     else :
        #         print('invalid angle')
        
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()   
        
# as for four phase stepping motor, four steps is a cycle. the function is used to drive the stepping motor clockwise or anticlockwise to take four steps    
def moveOnePeriod(direction,ms):    
    for j in range(0,4,1):      # cycle for power supply order
        for i in range(0,4,1):  # assign to each pin
            if (direction == 1):# power supply order clockwise
                GPIO.output(motorPins[i],((CCWStep[j] == 1<<i) and GPIO.HIGH or GPIO.LOW))
            else :              # power supply order anticlockwise
                GPIO.output(motorPins[i],((CWStep[j] == 1<<i) and GPIO.HIGH or GPIO.LOW))
        if(ms<3):       # the delay can not be less than 3ms, otherwise it will exceed speed limit of the motor
            ms = 3
        time.sleep(ms*0.001)    
        
# continuous rotation function, the parameter steps specifies the rotation cycles, every four steps is a cycle
def moveSteps(direction, ms, steps):
    for i in range(steps):
        moveOnePeriod(direction, ms)
        
# function used to stop motor
def motorStop():
    for i in range(0,4,1):
        GPIO.output(motorPins[i],GPIO.LOW)
            
def turntheta(deg):
    moveSteps(1,3,round(int(deg)*1.42222222))
    
def turnbacktheta(deg):
    moveSteps(0,3,round(int(deg)*1.42222222))
   

def moveangleclever(angle):
    angle=int(angle)
    global prevangle
    if (prevangle<angle):
        turntheta(int(angle)-int(prevangle))
        prevangle=angle
    elif(prevangle>angle):
        turnbacktheta(int(prevangle)-int(angle))
        prevangle=angle
    elif(prevangle==angle):
        angle=0
        moveangleclever(angle)

def destroy():
    GPIO.cleanup()             # Release resource
    
def DHT() -> [str,str] :

    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 18																																																																																																																																																																																																																																																																																																																																																																		
 
    while True:
        humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
        if humidity is not None and temperature is not None:
            logger.info("Temp={0:0.1f}C Humidity={1:0.1f}%".format(temperature, humidity))
            return [temperature,humidity]
        #else:
        
        #print("Sensor failure. Check wiring.");
    #time.sleep(2);

def picam()->str:
	
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration()
    picam2.configure(video_config)

    encoder = H264Encoder(10000000)
    filename = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    filename1 = "Video/"+filename+'_10s.mp4'
    filename = "Video/"+filename+'_10s.h264'
    picam2.start_recording(encoder, str(filename))
    time.sleep(10)
    picam2.stop_recording()
    picam2.close()

    command = "MP4Box -add {} {}.mp4".format(filename, os.path.splitext(filename1)[0])
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        return filename1
    except subprocess.CalledProcessError as e:
        print('FAIL:\ncmd:{}\noutput:{}'.format(e.cmd, e.output))
    
    return filename1


def telegrambot(q,id):
	
    LOGIN,PASSWORD,FEATURE,CAMERA,AITOOL,ROTATION,CANCEL = range(7)

    # Enable logging
    

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    #reply_keyboard = [["30", "45", "60"]]
    
        await update.message.reply_text(
        "Hi! This is the 3D Printer tracker Bot. Please Login with ID and Password.\n\n"
        "What is your login ID?",
        reply_markup=ReplyKeyboardRemove()
         )
    

        return LOGIN
    
    async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
        user = update.message.from_user
        chatid = user.id
        id.put(user.id)
        rndmsalt1_login=SALT1.encode()
        dk_login = pbkdf2_hmac('sha256', bytes(update.message.text,'utf-8'), rndmsalt1_login * 2, 500000)
        logger.info("User {0} Login entered :- {1}".format(chatid,str(dk_login.hex())))
        Login_Credential = USERNAME
        if dk_login.hex() == Login_Credential:
            await update.message.reply_text(
            "Please enter your password",
            reply_markup=ReplyKeyboardRemove(),
            )
            return PASSWORD
        else:
            await update.message.reply_text("Wrong Login Credential")
            return LOGIN

    async def authentication(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
        user = update.message.from_user
        rndmsalt1=SALT2.encode()
        dk = pbkdf2_hmac('sha256', bytes(update.message.text,'utf-8'), rndmsalt1 * 2, 500000)
        logger.info("User Password Entered :-{0}".format(str(dk.hex())))
        Password = PASSWORDUSERNAME
        if  dk.hex() == Password:
            reply_keyboard = [["Temperature & Humidity", "Camera", "Camera Rotation","Exit"]]
        
            await update.message.reply_text(
            "Login successful, please select the access feature",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Which feature?"
             ))
            return FEATURE
        
        else:
            await update.message.reply_text("Wrong Password")
            return PASSWORD


    async def feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
        logger.info("Feature Selected")
        i=0
        reply_keyboard = [["Temperature & Humidity", "Camera", "Camera Rotation","Exit"]]
        if update.message.text == "Temperature & Humidity":
            while i<retry:
                try:
                    await update.message.reply_text(
                    "Current Temperature is {0:0.1f}C and current humidity is {1:0.1f}% ".format(DHT()[0],DHT()[1]),read_timeout=50,write_timeout=50,connect_timeout=50,
                     reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True, input_field_placeholder="Which feature?"))
                    break
                except:
                    await update.message.reply_text("Send Failed Retrying...")
                    logger.info("Network error retrying :- {0}".format(i))

                i+=1
           
            
            return FEATURE
    
        elif update.message.text == "Camera":
            
            reply_keyboard = [["Manual Check","AI Monitoring Tool","Back","Exit"]]
            await update.message.reply_text(
            "Please select the corresponding camera option",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select camera feature?"
            ))
            
            return CAMERA
        
        elif update.message.text == "Camera Rotation":
        
            reply_keyboard = [["30","45","60"]]
            await update.message.reply_text(
            "What Degree would you like to rotate? Three options are provided on the button below, please note the camera will rotate, and restore upon the next selection of rotation degrees",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="What degrees would you like to rotate?"
            ))
            
            return ROTATION
    
        elif update.message.text == "Exit":
            reply_keyboard = [["Yes","No"]]
            await update.message.reply_text(
            "Are you sure you want to exit?",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Are you sure?"
            ))        
            return CANCEL
    
    async def camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
       
        logger.info("Waiting :- {0}".format(update.message.text))
        i=0
        if update.message.text == "Manual Check":
            video = picam()
            reply_keyboard = [["Manual Check","AI Monitoring Tool","Back","Exit"]]
            await update.message.reply_text(
            "Camera activated,please wait",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Recording in progress"
            )
            )
            await update.message.reply_text("Recording...")
            while i<retry:
                try:
                    await update.message.reply_video(video, read_timeout=50,write_timeout=50,connect_timeout=50)
                    break
                except:
                    await update.message.reply_text("Send Failed Retrying...")
                    logger.info("Network error retrying :- {0}".format(i))

                i+=1
            
            return CAMERA
        elif update.message.text == "AI Monitoring Tool":
            reply_keyboard = [["Activate","Deactivate","Back","Exit"]]
            await update.message.reply_text(
            "Select AI Tool status",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select status of AI Monitoring Tool?"
            )) 
            return AITOOL
        
        elif update.message.text == "Back":
            reply_keyboard = [["Temperature & Humidity", "Camera", "Camera Rotation","Exit"]]
            await update.message.reply_text(
            "Please select the required feature",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select Feature"
            ))        
            return FEATURE
        elif update.message.text == "Exit":
            reply_keyboard = [["Yes","No"]]
            await update.message.reply_text(
            "Are you sure you want to exit?",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Are you sure?"
            ))        
            return CANCEL


    
    async def aitool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancels and ends the conversation."""
        user = update.message.from_user
        reply_keyboard = [["Activate","Deactivate","Back","Exit"]]
        
        if update.message.text == "Activate": 
            await update.message.reply_text(
            "Activating AI Tool",  reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select status of AI Monitoring Tool?"
            ))
            logger.info("AiTool Selection status :- {0}".format(update.message.text))
            q.put(True)
            return AITOOL
        elif update.message.text == "Deactivate": 
            await update.message.reply_text(
            "Deactivating AI Tool", reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select status of AI Monitoring Tool?"
            ))
            logger.info("AiTool Selection status :- {0}".format(update.message.text))
            q.put(False)
            return AITOOL
        elif update.message.text == "Back": 
            reply_keyboard = [["Manual Check","AI Monitoring Tool","Back","Exit"]]
            await update.message.reply_text(
            "Please select the access feature",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Which feature?"
            ))
            return CAMERA
        elif update.message.text == "Exit":
            reply_keyboard = [["Yes","No"]]
            await update.message.reply_text(
            "Are you sure you want to exit?",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Are you sure?"
            ))        
            return CANCEL
        
    async def rotation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
        setup(update.message.text)
        logger.info("Rotation Degrees Applied :- {0}".format(update.message.text))
        reply_keyboard = [["Temperature & Humidity", "Camera", "Camera Rotation","Exit"]]
        if update.message.text != 'Exit':
            await update.message.reply_text(
            "The rotation degrees are applied to the camera",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Which feature?"
            ))
            return FEATURE
        else:
            reply_keyboard = [["Yes","No"]]
            await update.message.reply_text(
            "Are you sure you want to exit?",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Are you sure?"
            ))        
            return CANCEL

    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancels and ends the conversation."""
        user = update.message.from_user
        logger.info("Exiting the conversation with {0} :- {1}".format(user.first_name,user.id))
        if update.message.text == "Yes": 
            await update.message.reply_text(
            "Thank you and have a great day!", reply_markup=ReplyKeyboardRemove()
             )
            return ConversationHandler.END
        else:
            reply_keyboard = [["Temperature & Humidity", "Camera", "Camera Rotation","Exit"]]
            await update.message.reply_text(
            "Please select the required feature",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Which feature?"
            ))
            return FEATURE
    
    

    application = Application.builder().token(BOT_TOKEN).read_timeout(10).write_timeout(10).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LOGIN: [MessageHandler(filters.TEXT, password)],
            PASSWORD: [MessageHandler(filters.TEXT, authentication)],
            FEATURE: [
                MessageHandler(filters.TEXT, feature),
            ],
            CAMERA:[MessageHandler(filters.TEXT, camera)],
            AITOOL:[MessageHandler(filters.TEXT, aitool)],
            ROTATION:[MessageHandler(filters.TEXT, rotation)],
            CANCEL: [MessageHandler(filters.TEXT, cancel)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    gc.collect()
    application.run_polling(allowed_updates=Update.ALL_TYPES)




if __name__ =="__main__":
	
    # creating thread
    
    pool = mp.Pool()
    q = mp.Queue()
    id = mp.Queue()
    chid=''
    predictionresults=[]
    p1 = mp.Process(target=telegrambot, args=(q,id,)) 
    # p2 = mp.Process(target=AICameraTool,args=(q,currentstate,state))
    # p3 = mp.Process(target=setup,args=(30))
    try:	   
        p1.start()
        ##Intresting Note :- Preditions work only from main thread
        while True:
            if not q.empty():
                state = q.get()
                print ("Running "+str(state))
                currentstate = state
            elif currentstate==state and q.empty():
                if state == False:
                    logger.info("AI tool Off ,Prediction List :- {0}".format(predictionresults))
                    time.sleep(10)
                else:
                    if len(predictionresults)<defectthreshold:
                        predictionresults.append(predict())
                    elif len(predictionresults)==defectthreshold:
                        predictionresults.pop(0)
                        predictionresults.append(predict())
                        print(predictionresults.count("[1]"))
                        if not id.empty():
                            chid=id.get()
                        if predictionresults.count("[1]") == defectthreshold:
                            url = 'https://api.telegram.org/bot'+BOT_TOKEN+'/sendMessage?chat_id='+str(chid)+'&text='+AITOOLMSG
                            print(url)
                            r = requests.post(url)
                            state=False
                            break

        # while True:
        #     time.sleep(1)
    except KeyboardInterrupt:
        p1.terminate()
        #p2.terminate()
    # p3.start()
    finally:
        print('Done')
    

	# both threads completely executed
 
