import cv2
import numpy as np
import pika
import json
import uuid
import os
from inference_sdk import InferenceHTTPClient
import base64
from PIL import Image,ImageDraw
from io import BytesIO

MODEL_CONFIGS = {
    "Palet": {
        "api_url": "https://detect.roboflow.com",
        "api_key": "6d2jqta9IqzqfXxLkFbX",
        "model_id": "pallets-5zqoh-wy9w4-fyqen-clyye/2"
    },
    "Odun": {
        "api_url": "https://detect.roboflow.com",
        "api_key": "6d2jqta9IqzqfXxLkFbX",
        "model_id": "timber-log-v1/44"
    }
}

def process_image(input_path,output_path,json_path,item_type):
    try:
        config = MODEL_CONFIGS.get(item_type)
        if not config:
            raise ValueError(f"Unsupported type: {item_type}")
            
        api_url = config["api_url"]
        api_key = config["api_key"]
        model_id = config["model_id"]
            
            
        image = Image.open(input_path)
        image_bytes = BytesIO()
        image.save(image_bytes, format="JPEG")
        image_bytes = image_bytes.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        client = InferenceHTTPClient(api_url=api_url, api_key=api_key)
        result = client.infer(image_base64, model_id=model_id)

        print("Tahmin Sonuclari:")
        #print(json.dumps(result, indent=4))

        num_predictions = len(result.get('predictions', []))
        print(f"Toplam Tahmin Sayisi: {num_predictions}")
        """
        with open(json_path,"w") as json_file:
            json.dump(num_predictions,json_file)
        """
        data = {
            "count": num_predictions,
            "type": item_type  # "Odun" veya "Palet"
        }
        with open(json_path, "w") as json_file:
            json.dump(data, json_file)
            
            
        if num_predictions > 0:
            """
            for prediction in result['predictions']:
                print(f"Label: {prediction['class']}, Confidence: {prediction['confidence']}")
                print(f"Bounding Box: {prediction['x']}, {prediction['y']}, {prediction['width']}, {prediction['height']}")
            """
        # Gorseli tekrar ac islem icin
        image = Image.open(input_path)
        draw = ImageDraw.Draw(image)

        for prediction in result['predictions']:
            x, y = prediction['x'], prediction['y']
            w, h = prediction['width'], prediction['height']
            confidence = prediction['confidence']

            if item_type == "Palet":
                # Dikd
                left = x - w / 2
                top = y - h / 2
                right = x + w / 2
                bottom = y + h / 2
                draw.rectangle([left, top, right, bottom], outline="red", width=3)
            elif item_type == "Odun":
                # Daire n)
                radius = (w + h) / 4
                draw.ellipse(
                    [int(x - radius), int(y - radius), int(x + radius), int(y + radius)],
                    outline="lime", width=2
                )
            else:
                print("Belirtilmeyen tip.Tekrar dene!")

        image.save(output_path)
        image.save(f"images/{output_path}")
        print(f"Processed image saved: {output_path}")
    
    except Exception as e:
        print(f"Error processing image {input_path}: {str(e)}")




#rabbitmq time
def callback(ch,method,properties,body):
    print("Received message:", body)
    message = json.loads(body)
    file_id = message['file_id']
    item_type = message['type']
    input_path = f"{file_id}.jpg"
    output_path = f"processed_{file_id}.jpg"
    json_path = f"{file_id}.json"
    try:
        process_image(input_path,output_path,json_path,item_type)
        print(f"Processed image: {output_path}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag)


#rabbitconnect
def start_consuming():
    connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.0.70',port=5673))
    channel = connection.channel()

    channel.queue_declare(queue='image_queue')

    channel.basic_consume(queue='image_queue', on_message_callback=callback, auto_ack=False)

    print("Waiting for messages.To exit press CTRL+C.")
    while True:
        try:
            channel.start_consuming()  
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ server connection lost, trying to reconnect...")
            time.sleep(5)  
            continue

if __name__ == '__main__':
    start_consuming()
    




