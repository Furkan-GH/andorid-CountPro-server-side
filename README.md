# 🖥️ Backend for Android-Based Industrial Object Counting App

This is the **backend server** component of the industrial object counting system. It is designed to run on a **Raspberry Pi 4 (8GB)** and supports AI-based image processing via **Roboflow**, task queuing with **RabbitMQ**, and API services through **FastAPI**.

---

## 🧰 Technologies Used

| Component       | Technology                     |
|----------------|--------------------------------|
| API Framework   | FastAPI (Python 3.10+)         |
| Queue System    | RabbitMQ (Dockerized)          |
| Object Detection| Roboflow API                   |
| Database        | PostgreSQL                     |
| Authentication  | JWT (OAuth2) + bcrypt          |
| Deployment      | Gunicorn + Uvicorn + DuckDNS   |
| Storage         | Processed image saving system  |

---

## 🌐 System Architecture

```text
[Android App]
     ⬇
[FastAPI Backend on Raspberry Pi]
     ⬇                  ⬇
[RabbitMQ Queue]    [PostgreSQL DB]
     ⬇
[Image sent to Roboflow for Detection]
     ⬇
[Processed Image + Count returned to App]

---

## ⚙️ Key Features

- ✅ **JWT-based user authentication** (`OAuth2PasswordBearer`)
- 📦 **Async image processing** via **RabbitMQ**
- 📸 **Object detection** using custom **Roboflow** models
- 🗂 **Image saving** (raw + processed)
- 🕓 **Request logging** with timestamp, object type, and result
- 🔐 **Password hashing** with `bcrypt + passlib`
- 🌍 **External access** via **DuckDNS** and port forwarding

