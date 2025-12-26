import os 

class Config:
    SECRET_KEY = "SECRET_KEY"
    SQLALCHEMY_DATABASE_URI = "postgresql://usuario:password@localhost/inventario"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #minIO Configuration
    MINIO_ENDPOINT = "localhost:9000"
    MINIO_ACCESS_KEY = "minioadmin"
    MINIO_SECRET_KEY = "minioadmin"
    MINIO_BUCKET = "archivos"
