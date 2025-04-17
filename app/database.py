from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据库文件路径
DB_PATH = os.path.join(BASE_DIR, "data", "logistics.db")

# 创建数据库引擎
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite特定配置
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

class Shipment(Base):
    """运单表"""
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipping_date = Column(Date, index=True)
    raw_address = Column(String)  # 原始地址（不经过处理的）
    province = Column(String, index=True)
    city = Column(String, index=True)
    area = Column(String, index=True)
    total_price = Column(Float)
    quantity = Column(Integer)
    unit = Column(String)
    raw_goods = Column(String)
    
    # 关系
    items = relationship("ShipmentItem", back_populates="shipment")

class ShipmentItem(Base):
    """运单货物项表"""
    __tablename__ = "shipment_items"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    goods_type = Column(String, index=True)  # A/B/C/其他
    quantity = Column(Integer)
    
    # 关系
    shipment = relationship("Shipment", back_populates="items")

# 创建所有表
def init_db():
    Base.metadata.create_all(bind=engine) 