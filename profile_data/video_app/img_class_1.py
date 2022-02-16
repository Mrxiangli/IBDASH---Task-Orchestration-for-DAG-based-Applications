import json
import os
import matplotlib.pyplot as plt
import mxnet as mx
from mxnet import gluon, nd
from mxnet.gluon.model_zoo import vision
import numpy as np
import time as timer

def predict(model, image, categories, k):
	predictions = model(transform(image)).softmax()
	top_pred = predictions.topk(k=k)[0].asnumpy()
	for index in top_pred:
		probability = predictions[0][int(index)]
		category = categories[int(index)]
		#print("{}: {:.2f}%".format(category, probability.asscalar()*100))
   # print('')

def transform(image):
	resized = mx.image.resize_short(image, 224) #minimum 224x224 images
	cropped, crop_info = mx.image.center_crop(resized, (224, 224))
	normalized = mx.image.color_normalize(cropped.astype(np.float32)/255,
									  mean=mx.nd.array([0.485, 0.456, 0.406]),
									  std=mx.nd.array([0.229, 0.224, 0.225]))
	# the network expect batches of the form (N,3,224,224)
	transposed = normalized.transpose((2,0,1))  # Transposing from (224, 224, 3) to (3, 224, 224)
	batchified = transposed.expand_dims(axis=0) # change the shape from (3, 224, 224) to (1, 3, 224, 224)
	return batchified

if __name__ =='__main__':

	start=timer.time()
	ctx = mx.cpu()

	densenet121 = vision.densenet121(pretrained=True, ctx=ctx)
	mobileNet = vision.mobilenet0_5(pretrained=True, ctx=ctx)
	resnet18 = vision.resnet18_v1(pretrained=True, ctx=ctx)

	mx.test_utils.download('https://raw.githubusercontent.com/dmlc/web-data/master/mxnet/doc/tutorials/onnx/image_net_labels.json')
	categories = np.array(json.load(open('image_net_labels.json', 'r')))


	path_parent = os.path.dirname(os.getcwd())
	file_path="video_app/img_set1/"
	dir_path=os.path.join(path_parent,file_path) 
	for each_img in os.listdir(dir_path):
		if ".jpg" in each_img:
			#print(each_img)
			image = mx.image.imread(os.path.join(dir_path,each_img))
			plt.imshow(image.asnumpy())
			predict(resnet18, image, categories, 3)
	end=timer.time()
	print("img_class_1: "+str((end-start)/100))