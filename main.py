import cv2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import threading
import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture

class DiemDanhApp(App):
    def build(self):
        self.title = "Hệ thống Điểm danh AI"

        # Layout dọc cho màn hình điện thoại
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.image = Image(size_hint_y=0.85)
        layout.add_widget(self.image)

        self.status_label = Label(
            text="Đang khởi tạo...", 
            size_hint_y=0.15, 
            font_size='16sp'
        )
        layout.add_widget(self.status_label)

        # Kết nối Google Sheets
        self.init_google_sheets()

        # Nạp bộ phát hiện khuôn mặt OpenCV
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        self.attended_set = set()

        # Trên Android: Camera trước thường là Index 0 hoặc 1
        self.capture = cv2.VideoCapture(0) 
        
        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)
        return layout

    def init_google_sheets(self):
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            # Đường dẫn file credentials lưu trên bộ nhớ điện thoại
            creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)
            self.sheet = client.open("DiemDanh_GoogleSheet").sheet1
            self.status_label.text = "Sẵn sàng điểm danh!"
        except Exception as e:
            self.status_label.text = f"Lỗi kết nối Sheets: {str(e)}"
            self.sheet = None

    def update_frame(self, dt):
        ret, frame = self.capture.read()
        if not ret:
            return

        # Chuyển xám để nhận diện
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            user_id = "ThanhVien_01"
            if user_id not in self.attended_set and self.sheet:
                self.attended_set.add(user_id)
                threading.Thread(target=self.send_to_sheet, args=(user_id,)).start()

        # Xuất khung hình ra giao diện Kivy
        buffer = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
        self.image.texture = texture

    def send_to_sheet(self, user_id):
        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")

            self.sheet.append_row([user_id, date_str, time_str, "Thành công"])
            self.status_label.text = f"✅ Đã điểm danh: {user_id} ({time_str})"
        except Exception as e:
            self.status_label.text = f"❌ Lỗi ghi dữ liệu: {str(e)}"

    def on_stop(self):
        if self.capture:
            self.capture.release()

if __name__ == '__main__':
    DiemDanhApp().run()