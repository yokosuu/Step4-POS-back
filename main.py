from fastapi import FastAPI, HTTPException, Body, Depends
from datetime import datetime, timezone, timedelta
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey, Boolean
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, datetime
from typing import List, Optional
import logging 
import config 
import traceback
from datetime import datetime

app = FastAPI()

# 通信許可するドメインリスト
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
    "http://localhost:3000/kawana",
    "http://localhost:3000/kawana_Lv3",
    "http://localhost:3000/02_MenuList",
    "http://localhost:3000/05_MenuDetail",
    "*",
]

# CORSを回避するために追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,   # ブラウザからリクエスト受けた時の認証情報サーバー送信可否指定。Trueの場合は許可
    allow_methods=["*"],      # 許可するHTTPメソッドリスト(Get,Post,Putなど) ["*"]と指定することですべてのHTTPメソッドを許可
    allow_headers=["*"]       # 許可するHTTPヘッダーリスト  ["*"]と指定することですべてのHTTPヘッダーを許可
)

# ロガーのインスタンスを作成する
logger = logging.getLogger(__name__)

# データベースへの接続を取得
def get_db_connection():
    # MySQL設定(Azure)
    MYSQL_SERVER = config.MYSQL_SERVER_ONASURE
    MYSQL_USER = config.MYSQL_USER_ONASURE
    MYSQL_PASSWORD = config.MYSQL_PASSWORD_ONASURE
    MYSQL_DB = config.MYSQL_DB_ONASURE

    # MySQL設定(Local)
    #MYSQL_SERVER = config.MYSQL_SERVER
    #MYSQL_USER = config.MYSQL_USER
    #MYSQL_PASSWORD = config.MYSQL_PASSWORD
    #MYSQL_DB = config.MYSQL_DB

    # SSLの設定
    SSL_CONFIG = config.MYSQL_SSL_CONFIG 

    # データベースに接続する
    engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_SERVER}/{MYSQL_DB}?ssl_ca={SSL_CONFIG}", echo=True)

    # SQLiteの場合
    #DB_FILE = "pop-make-up_DB.db"
    #engine =  create_engine(f"sqlite:///{DB_FILE}", echo=True)

    # Sessionオブジェクトを作成する
    session = sessionmaker(bind=engine)()

    # 接続を返す
    return session

# SQLAlchemyのモデルインスタンスを辞書に変換するヘルパー関数
def to_dict(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class ProductStocks(BaseModel):
    ID: int
    PRD_ID: str
    STORE_ID: int
    DATE_ID: int
    LOT: date
    BEST_BY_DAY: date
    PIECES: int

class Products(BaseModel):
    ID: int
    PRD_CODE: str
    PRD_IMAGE: Optional[str]
    PRD_NAME: str
    DESCRIPTION: Optional[str]
    PRICE: int
    CAL: float
    SALINITY: float
    ALLERGY_ID: Optional[int]
    CATEGORY_ID: int

class ReservationData(BaseModel):
    RSV_TIME: date
    STOCK_ID: int
    USER_ID: str
    MY_COUPON_ID: str
    #購入方法
    MET: int
    DATE: str

class Coupons(BaseModel):
    ID: int
    NAME: str
    DESCRIPTION: str
    EXPIRATION: int
    PRICE: int

class MyCoupons(BaseModel):
    ID: int
    USER_ID: int
    COUPON_ID: int
    GET_DATE: date
    EXP_DATE: date
    STATUS: int

class Dates(BaseModel):
    ID: int
    DATE: date
    WEEK: str

class Categories(BaseModel):
    ID: int
    NAME: str

class TransactionRecord(BaseModel):
    ID: int
    USER_ID: int
    PRD_ID: int
    MY_COUPON_ID: int
    DATE: date



# データベースのテーブルを定義する
Base = declarative_base()

# Userモデルの定義
class User(Base):
    __tablename__ = "users"

    ID = Column(Integer, primary_key=True, index=True)
    USER_NAME = Column(String(13), index=True)
    EMAIL = Column(String, unique=True, index=True)
    PASSWORD = Column(String)
    IS_ACTIVE = Column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    ID = Column(Integer, primary_key=True, index=True)
    PRD_CODE = Column(String(13), index=True)
    PRD_NAME = Column(String(50), index=True)
    PRD_IMAGE = Column(String, index=True, nullable=True)
    DESCRIPTION = Column(String, index=True, nullable=True)
    PRICE = Column(Integer, index=True)
    CAL = Column(Float, index=True)
    SALINITY = Column(Float, index=True)
    ALLERGY_ID = Column(Integer, ForeignKey('allergies.ID'), index=True, nullable=True)
    CATEGORY_ID = Column(Integer, index=True)

# ProductStocksモデルの定義
class ProductStocks(Base):
    __tablename__ = "stocks"

    ID = Column(Integer, primary_key=True, index=True)
    PRD_ID = Column(String(13), ForeignKey('products.PRD_CODE'), index=True)
    STORE_ID = Column(Integer, index=True)
    DATE_ID = Column(Integer, index=True, nullable=True)
    LOT = Column(Date, index=True)
    BEST_BY_DAY = Column(Date, index=True)
    PIECES = Column(Integer, index=True)

# ReservationDataモデルの定義
class Reservation(Base):
    __tablename__ = "reservations"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    RSV_TIME = Column(Date, index=True)
    STOCK_ID = Column(Integer, index=True)
    USER_ID = Column(String(13), ForeignKey('users.ID'), index=True)
    MY_COUPON_ID = Column(String(13), ForeignKey('coupons.ID'), index=True)
    #購入方法
    MET = Column(Integer, index=True)
    DATE = Column(String, index=True)

# クーポンモデルの定義
class Coupon(Base):
    __tablename__ = "coupons"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    NAME = Column(String(50), index=True)
    IMAGE = Column(String, index=True, nullable=True)
    DESCRIPTION = Column(String, index=True, nullable=True)
    EXPIRATION = Column(Integer, index=True)
    PRICE = Column(Integer, index=True)

# マイクーポンの定義
class MyCoupon(Base):
    __tablename__ = "my_coupons"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    USER_ID = Column(Integer, index=True)
    COUPON_ID = Column(Integer, index=True)
    GET_DATE = Column(Date, index=True)
    EXP_DATE = Column(Date, index=True)
    STATUS = Column(Integer, index=True)

# 取引データの定義
class TransactionData(Base):
    __tablename__ = "transaction_records"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    USER_ID = Column(Integer, index=True)
    PRD_ID = Column(Integer, index=True)
    MY_COUPON_ID = Column(Integer, index=True)
    DATE = Column(Date, index=True)

# 日にちの定義
class Date(Base):
    __tablename__ = "dates"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    DATE = Column(Date, index=True)
    WEEK = Column(String, index=True)

# カテゴリーの定義
class Category(Base):
    __tablename__ = "categories"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    NAME = Column(String, index=True)



@app.get("/")
def read_root():
    return {"Hello": "World"}

# 在庫情報をとってくる
@app.post("/Stocks/")
async def stock_product(
    date: str,
    category: str,
    db: Session = Depends(get_db_connection)):

    # strで送られてきているのでdate型に変換する
    client_date = datetime.strptime(date, '%Y-%m-%d')
    formatted_date = client_date.strftime('%Y-%m-%d')
    #print(category)

    try:
        # with文を使って、データベースへの接続を自動的に閉じるようにする
        with db:
            # stocksTable内のDateが一致するレコードを取得
            date_id = db.query(Date).filter_by(DATE = formatted_date).first()
            category_id = db.query(Category).filter_by(NAME = category).first()
            categorizedProducts = db.query(Product).filter_by(CATEGORY_ID = category_id.ID).all()
            stocks = db.query(ProductStocks).filter_by(DATE_ID = date_id.ID).all()

            # PRD_ID に対応する製品レコードをデータベースから取得
            if stocks:
                combined_data = []
                for stock in stocks:
                    product_data = next((product for product in categorizedProducts if product.ID == stock.PRD_ID), None)
                    if product_data is not None:
                        stock_dict = to_dict(stock)
                        product_dict = to_dict(product_data)
                        combined_dict = {**product_dict, **stock_dict}  # 最古情報と商品情報の2つの辞書を結合
                        combined_data.append(combined_dict)
                return {"status": "success", "data": combined_data}
    # 例外が発生した場合
    except Exception as e:
        # ログにエラーを出力
        logger.error(f"A transactionData error occurred: {e}", exc_info=True)
        # tracebackモジュールをインポート
        import traceback
        # エラーのスタックトレースを文字列に変換
        error_trace = traceback.format_exc()
        # HTTPExceptionを発生させて、ステータスコードを500にし、詳細をエラーとスタックトレースにする
        raise HTTPException(status_code=500, detail=f"Error processing data: {e}\n{error_trace}")


# 商品詳細ページ（商品をタップした時）
@app.post("/Products/")
# クエリパラメータとしてproduct_idを取得する
async def product_detail(
    ID: int, 
    db: Session = Depends(get_db_connection)):
    try:
        with db:
            # プロダクトIDが一致する商品詳細情報を取得
            product = db.query(Product).filter(Product.ID == ID).first()
            return {"status": "success", "data": product}

    # 例外が発生した場合
    except Exception as e:
        # ログにエラーを出力
        logger.error(f"A transactionData error occurred: {e}", exc_info=True)
        # tracebackモジュールをインポート
        import traceback
        # エラーのスタックトレースを文字列に変換
        error_trace = traceback.format_exc()
        # HTTPExceptionを発生させて、ステータスコードを500にし、詳細をエラーとスタックトレースにする
        raise HTTPException(status_code=500, detail=f"Error processing data: {e}\n{error_trace}")
    

# 予約リストに追加（=購入ボタンを押した時）
@app.post("/Reservation/")
async def create_ReservationData(
    postReservationData: ReservationData = Body(...), 
    db: Session = Depends(get_db_connection)):

    try:
        # with文を使って、データベースへの接続を自動的に閉じるようにする
        with db:
            # 指定された型でdbへのレコード追加用の情報を作る
            RSV = Reservation(
                RSV_TIME = postReservationData.RSV_TIME, 
                STOCK_ID = postReservationData.STOCK_ID, 
                USER_ID = postReservationData.USER_ID, 
                MY_COUPON_ID = postReservationData.MY_COUPON_ID,
                MET = postReservationData.MET,
                DATE = postReservationData.DATE,
            )
            # db追加
            db.add(RSV)
            db.commit()
            # 自動採番されたRSV.IDを取得
            rsv_id = RSV.ID
            # RSV.IDをレスポンスに含める
            return {"RSV_ID": rsv_id }
        
    # 例外が発生した場合
    except Exception as e:
        # ログにエラーを出力
        logger.error(f"A transactionData error occurred: {e}", exc_info=True)
        # tracebackモジュールをインポート
        import traceback
        # エラーのスタックトレースを文字列に変換
        error_trace = traceback.format_exc()
        # HTTPExceptionを発生させて、ステータスコードを500にし、詳細をエラーとスタックトレースにする
        raise HTTPException(status_code=500, detail=f"Error processing data: {e}\n{error_trace}")
    

# 予約リストにクーポン追加（=予約ボタンを押した時）
@app.post("/CouponReservation/")
async def create_ReservationData(
    postReservationData: ReservationData = Body(...), 
    db: Session = Depends(get_db_connection)):

    try:
        # with文を使って、データベースへの接続を自動的に閉じるようにする
        with db:
            # 指定された型でdbへのレコード追加用の情報を作る
            RSV = Reservation(
                RSV_TIME = postReservationData.RSV_TIME, 
                STOCK_ID = postReservationData.STOCK_ID, 
                USER_ID = postReservationData.USER_ID, 
                MY_COUPON_ID = postReservationData.MY_COUPON_ID,
                MET = postReservationData.MET,
                DATE = postReservationData.DATE,
            )
            # db追加
            db.add(RSV)
            db.commit()
            # 自動採番されたRSV.IDを取得
            rsv_id = RSV.ID
            # MyCouponテーブルからIDがRSV_STOCK_IDと完全一致するデータを検索し、STATUSを1から2に変更する 
            my_coupon = db.query(MyCoupon).filter(MyCoupon.ID == postReservationData.MY_COUPON_ID).first()
            if my_coupon:
                my_coupon.STATUS = 2
                db.commit()
            # RSV.IDをレスポンスに含める
            return {"RSV_ID": rsv_id }
        
    # 例外が発生した場合
    except Exception as e:
        # ログにエラーを出力
        logger.error(f"A transactionData error occurred: {e}", exc_info=True)
        # tracebackモジュールをインポート
        import traceback
        # エラーのスタックトレースを文字列に変換
        error_trace = traceback.format_exc()
        # HTTPExceptionを発生させて、ステータスコードを500にし、詳細をエラーとスタックトレースにする
        raise HTTPException(status_code=500, detail=f"Error processing data: {e}\n{error_trace}")


# 予約リストを表示する
@app.get("/Reservation/")
# クエリパラメータとしてuser_id、dateを取得する
async def reservation_product(
    user_id: str, 
    date: Optional[str] = None,
    db: Session = Depends(get_db_connection)):

    # strで送られてきているのでdate型に変換する
    if date is None or date == 'undefined':
        client_date = datetime.now()
        formatted_date = client_date.strftime('%Y-%m-%d')
    else:
        client_date = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = client_date.strftime('%Y-%m-%d')

    # CouponをProductのモデルに合うようにデータ加工
    def convert_coupon_to_product(coupon):
        return {
            "ID": coupon.ID,
            "PRD_NAME": coupon.NAME,
            "PRD_IMAGE": coupon.IMAGE,
            "DESCRIPTION": coupon.DESCRIPTION,
            "PRICE": -coupon.PRICE,
            # 他のフィールドはNoneまたは適切なデフォルト値を設定
            "PRD_CODE": None,
            "CAL": None,
            "SALINITY": None,
            "ALLERGY_ID": None,
            "CATEGORY_ID": None,
        }

    try:
        # with文を使って、データベースへの接続を自動的に閉じるようにする
        with db:
            # ユーザーIDが一致する予約情報を取得
            reservations = db.query(Reservation).filter(Reservation.USER_ID == user_id).all()

            # date_idを取得
            date_id = db.query(Date).filter_by(DATE = formatted_date).first()

            # 予約リストから STOCK_ID, MY_COUPON_ID を取得
            stk_ids = [reservation.STOCK_ID for reservation in reservations]
            myc_ids = [reservation.MY_COUPON_ID for reservation in reservations]
            RSVdates = [reservation.DATE for reservation in reservations]

            # PRD_ID に対応する製品レコードをデータベースから取得
            products = []
            for stk_id, myc_id, RSVdate in zip(stk_ids, myc_ids, RSVdates):
                if stk_id != 9999:
                    # stockTableのIDとstk_id、date_idが両方一致するもののみをstockに格納
                    stock = db.query(ProductStocks).filter(ProductStocks.ID == stk_id).filter(ProductStocks.DATE_ID == date_id.ID).first()
                    if stock:
                        # stockのidとPRD_IDが一致する商品情報をproductsの配列に追加
                        product = db.query(Product).filter(Product.ID == stock.PRD_ID).first()
                        products.append(product)
                else:
                    if RSVdate == date: 
                        # stk_idが9999の場合、my_couponsTableからIDとmyc_idが一致するものを抽出
                        my_coupon = db.query(MyCoupon).filter(MyCoupon.ID == myc_id).first()
                        if my_coupon:
                            # 抽出データのCOUPON_IDと一致するクーポンをcouponsTableから取得
                            coupon = db.query(Coupon).filter(Coupon.ID == my_coupon.COUPON_ID).first()
                            product = convert_coupon_to_product(coupon)
                            products.append(product)

                #else:
                    # 製品が見つからなかった場合は次のfor文へ
                    # continue
                    # ここではエラーを発生させる例を示します
                    # raise HTTPException(status_code=404, detail=f"Product with PRD_ID {stk_id} not found")

            return {"status": "success", "data": products}
        
    # 例外が発生した場合
    except Exception as e:
        # ログにエラーを出力
        logger.error(f"A transactionData error occurred: {e}", exc_info=True)
        # tracebackモジュールをインポート
        import traceback
        # エラーのスタックトレースを文字列に変換
        error_trace = traceback.format_exc()
        # HTTPExceptionを発生させて、ステータスコードを500にし、詳細をエラーとスタックトレースにする
        raise HTTPException(status_code=500, detail=f"Error processing data: {e}\n{error_trace}")


# マイクーポン情報取得
@app.get("/MyCoupon/")
# クエリパラメータとしてuser_idを取得する
async def my_coupon(
    user_id: int, 
    db: Session = Depends(get_db_connection)):

    try:
        # with文を使って、データベースへの接続を自動的に閉じるようにする
        with db:
            # ユーザーIDが一致するクーポン情報を取得
            my_coupons = db.query(MyCoupon).filter(MyCoupon.USER_ID == user_id, MyCoupon.STATUS == 1).all()

            # USER_IDに対応するクーポンレコードをデータベースから取得
            if my_coupons:
                combined_my_coupon_data = []
                for my_coupon in my_coupons:
                    coupon_data = db.query(Coupon).filter(Coupon.ID == my_coupon.COUPON_ID).first()
                    my_coupon_dict = to_dict(my_coupon)
                    coupon_dict = to_dict(coupon_data)
                    combined_dict = {**coupon_dict, **my_coupon_dict}  # クーポン情報とまいクーポン情報の2つの辞書を結合
                    combined_my_coupon_data.append(combined_dict)
                return {"status": "success", "data": combined_my_coupon_data}
        
    # 例外が発生した場合
    except Exception as e:
        # ログにエラーを出力
        logger.error(f"A transactionData error occurred: {e}", exc_info=True)
        # tracebackモジュールをインポート
        import traceback
        # エラーのスタックトレースを文字列に変換
        error_trace = traceback.format_exc()
        # HTTPExceptionを発生させて、ステータスコードを500にし、詳細をエラーとスタックトレースにする
        raise HTTPException(status_code=500, detail=f"Error processing data: {e}\n{error_trace}")


# 商品受け取り時の処理（バーコードで読み取る場合）
@app.post("/TransactionData/")
async def transactionData(
    user_id: str,
    prd_code: str,
    db: Session = Depends(get_db_connection)):


    try:
        # with文を使って、データベースへの接続を自動的に閉じるようにする
        with db:
            # 現在の日付を取得
            today = datetime.now()
            # 日付を指定された形式の文字列に変換
            formatted_date = today.date()
            # 今日の日付のidを取得
            date_id = db.query(Date).filter_by(DATE = formatted_date).first().ID

            # prd_codeからprd_id取得
            prd_data = db.query(Product).filter(Product.PRD_CODE == prd_code).first()

            # stocksTable内のdate、productが一致するレコードを取得
            ##### "1"の部分を本来はdate_idにすること（動かすために便宜的に1を代入） 
            stocks_data = db.query(ProductStocks).filter(ProductStocks.DATE_ID == date_id).filter(ProductStocks.PRD_ID == prd_data.ID).first()

            #reservationsTableから該当するレコードを取得 -> user_id、stock_idの2点一致で照合
            reservation_data = db.query(Reservation).filter(Reservation.USER_ID == user_id).filter(Reservation.STOCK_ID == stocks_data.ID).first()
            Product_id = prd_data.ID

            # Transactionクラスのインスタンスを作成する
            trd = TransactionData(
                USER_ID = user_id, 
                PRD_ID = Product_id, 
                DATE = formatted_date,
            )

            # データベースにインスタンスを追加
            db.add(trd)
            db.commit()

            # 自動採番されたIDを取得
            trd_id = trd.ID

            # 数量を1減らす
            stocks_data.PIECES -= 1
            db.commit()

            # reservationsTableの該当するレコードを削除
            #db.delete(reservation_data)
            #db.commit()

            # IDをレスポンスに含める
            return {"TRD_ID": trd_id, "PRD": prd_data, "message": "Stock pieces decreased successfully. and Transaction data recorded." }
        
    # 例外が発生した場合
    except Exception as e:
        # ログにエラーを出力
        logger.error(f"A transactionData error occurred: {e}", exc_info=True)
        # tracebackモジュールをインポート
        import traceback
        # エラーのスタックトレースを文字列に変換
        error_trace = traceback.format_exc()
        # HTTPExceptionを発生させて、ステータスコードを500にし、詳細をエラーとスタックトレースにする
        raise HTTPException(status_code=500, detail=f"Error processing data: {e}\n{error_trace}")

        



# # /transactionStatementData/というエンドポイントにPOSTリクエストを送ると、取引明細データのリストを受け取って、データベースに保存
# @app.post("/transactionStatementData/")
# async def create_transactionStatementData(
#     postTransactionStatements: List[TransactionStatementData] = Body(...), 
#     db: Session = Depends(get_db_connection)
# ):
#     # 受け取ったデータをログに出力する
#     logger.info(f"Received transactionStatementData: {postTransactionStatements}")
#     try:
#         # with文を使って、データベースへの接続を自動的に閉じるようにする
#         with db:
#             # 受け取ったデータのリストをループで処理
#             for postTransactionStatement in postTransactionStatements:
#                 # TransactionStatementクラスのインスタンスを作成する
#                 transactionStatement =TransactionStatementData(
#                     TRD_ID = postTransactionStatement.TRD_ID,
#                     PRD_NAME = postTransactionStatement.PRD_NAME, 
#                     PRD_PRICE = postTransactionStatement.PRD_PRICE,
#                     TAC_CD = postTransactionStatement.TAC_CD,
#                 )
#                 # データベースにインスタンスを追加
#                 db.add(transactionStatement)
#             # データベースに変更をコミット
#             db.commit()
#             # 返すデータのリストを作成する
#             return_data = []
#             # 受け取ったデータのリストをループで処理
#             for postTransactionStatement in postTransactionStatements:
#                 # 返すデータの辞書を作成する
#                 data = {
#                     "TRD_ID": postTransactionStatement.TRD_ID,
#                     "PRD_NAME": postTransactionStatement.PRD_NAME,
#                     "PRD_PRICE": postTransactionStatement.PRD_PRICE,
#                     "TAC_CD": postTransactionStatement.TAC_CD,
#                     "id": postTransactionStatement.id # id属性はdb.addメソッドで付与される
#                 }
#                 # 返すデータのリストに辞書を追加
#                 return_data.append(data)
#             # 返すデータのリストをレスポンスとして返す
#             return return_data
        
#     # 例外が発生した場合
#     except Exception as e:
        # ログにエラーを出力
        logger.error(f"A transactionData error occurred: {e}", exc_info=True)
        # tracebackモジュールをインポート
        import traceback
        # エラーのスタックトレースを文字列に変換
        error_trace = traceback.format_exc()
        # HTTPExceptionを発生させて、ステータスコードを500にし、詳細をエラーとスタックトレースにする
        raise HTTPException(status_code=500, detail=f"Error processing data: {e}\n{error_trace}")