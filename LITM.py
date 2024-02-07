#LiveInferenceTrainedModel
from picamera2 import Picamera2
import gc
from keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator


model = load_model('training4.h5')
test_dir ='/home/pi/Desktop/Project/test'
print(test_dir)
threshold = 0.5

def predict()->str:
		picam2 = Picamera2()
		picam2.start(show_preview=True)
	    #picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous, "AfSpeed": controls.AfSpeedEnum.Fast})
		picam2.start_and_capture_files("test/test/fastfocus-test{:d}.jpg", num_files=1, delay=0.5)
		picam2.stop_preview()
		picam2.stop()
		picam2.close()
		test_datagen = ImageDataGenerator(rescale=1./255)

    #model.summary()
		
		test_generator = test_datagen.flow_from_directory(
        test_dir,
        target_size=(150, 150),
        batch_size=1,
        class_mode='binary')
        
# Predict using the trained model
		predictions = model.predict(test_generator,verbose=1)
# Apply threshold for binary classification
		binary_predictions = (predictions > threshold).astype(int) #if pred>thres val =1
		if binary_predictions[0]==1:
			print("Defect")
		else:
			print("Non Defect")
		gc.collect()
		return str(binary_predictions[0])

if __name__ =="__main__":
	while True:
		print(predict())
