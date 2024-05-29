import cv2
import face_recognition
import time
import gspread
import requests
import os
import base64
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from simple_facerec import SimpleFacerec
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('odroid-400614-45570d47424c.json', scope)
client = gspread.authorize(credentials)

credentials_path = 'odroid-400614-45570d47424c.json'
folder_id = '1CkkY4NnatLzhOExt074HGI9V_hKYk8md'
credentialsfordrive = service_account.Credentials.from_service_account_file(credentials_path, scopes=['https://www.googleapis.com/auth/drive'])

# Create Google Drive service
drive_service = build('drive', 'v3', credentials=credentialsfordrive)

# ของ LINE Notify Access Token
LINE_NOTIFY_ACCESS_TOKEN = 'RNMRdALZU3b2JE36nKC7qwATQAnQ2kTFNyoRZ3Ukhna'

# Open the Google Spreadsheet using its title
spreadsheet = client.open('Face Recognition')
worksheet = spreadsheet.get_worksheet(0)  # Use index 0 for the first sheet in the spreadsheet


# Encode faces from a folder
sfr = SimpleFacerec()
sfr.load_encoding_images("images/")
img_counter = 0
img_num = 0

#load camera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    
    # Detect Faces
    face_locations, face_names = sfr.detect_known_faces(frame)
    for face_loc, name in zip(face_locations, face_names):
        y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
        cv2.putText(frame, name,(x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

        # Delay การถ่ายรูป
        if time.time() - img_counter > 15:
            cv2.imwrite(f'Camera/detected_img{img_num}.jpg', frame)
            image_path = f'Camera/detected_img{img_num}.jpg'
            image_pathforsheet = f'Recog/detected_img{img_num}.jpg'
            file_metadata = {
                'name': f'detected_img{img_num}.jpg', #Name of the file
                'parents': [folder_id]  # ID of the folder in Google Drive
            }
            media = MediaFileUpload(image_path, mimetype='image/jpeg')
            uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
            # ตัวแปรที่เก็บไฟล์รูปภาพ
            now = datetime.datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%m")
            day = now.strftime("%d")
            realtime = now.strftime("%H:%M:%S")
            message = f'ตอนนี้มีคนเข้าใช้งาน ณ วันที่ {day}/{month}/{year} เวลา {realtime}'
            # ตัวแปรสำหรับสร้างไฟล์สำหรับการส่ง
            files = {'imageFile': open(image_path, 'rb')}

            # ส่งรูปไปที่ LINE Notify
            try:
                response = requests.post('https://notify-api.line.me/api/notify',
                                         headers={'Authorization': f'Bearer {LINE_NOTIFY_ACCESS_TOKEN}'},
                                         files=files, data = {'message': message})
                
                # ตรวจสอบว่าการส่งสำเร็จหรือไม่
                if response.status_code == 200:
                    print('รูปถูกส่งไปที่ LINE Notify สำเร็จแล้ว!')
                else:
                    print('เกิดข้อผิดพลาดในการส่งรูปไปที่ LINE Notify:', response.status_code, response.text)
            except Exception as e:
                print('เกิดข้อผิดพลาด:', str(e))
            img_num += 1
            img_counter = time.time()
    cv2.imshow("Frame", frame)
    
    key = cv2.waitKey(1)
    if key == 27:
        break
        
cap.release()
cv2.destroyAllWindows()