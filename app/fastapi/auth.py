from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import pg8000
import redis
import jwt
import bcrypt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os, json, configparser
from app.util import get_logger

logger = get_logger()

# --- CONFIG ---
config = configparser.ConfigParser()

project_root = "/var/www/html"
print(project_root)
base_directory = os.path.abspath(os.path.join(project_root,'./orderbook'))  # 2 levels up from script
print(base_directory)
config_directory = os.path.join(base_directory, 'config_folder') 
print(config_directory)

config_file_path = os.path.join(os.path.dirname(__file__), config_directory, 'credentials.ini')
# Ensure the config file exists before trying to load it
if not os.path.exists(config_file_path):
    raise FileNotFoundError(f"Config file not found at {config_file_path}")
# Initialize the config parser and read the file
config = configparser.ConfigParser()
config.read(config_file_path)

# config.read(os.path.join(os.path.dirname(__file__), 'config_folder', 'credentials.ini'))

config_source = config['dbchoice']['db']
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']
SECRET_KEY = config['jwt_secret']['secret_key']

# --- APP ---
app = FastAPI(title="AuthAPI", docs_url="/docs", redoc_url="/redoc")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REDIS ---
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# --- AUTH ---
bearer_scheme = HTTPBearer()

async def token_required(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- DB Dependency ---
def with_db_connection():
    con = pg8000.connect(user=dbusername, password=dbpassword, host="localhost", port=5432, database=dbname)
    try:
        yield con.cursor()
    finally:
        con.close()

# --- ROUTES ---
import httpx
import asyncio

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...), cursor=Depends(with_db_connection)):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    cursor.connection.commit()

    logger.info(f"User:{username} registration successful.")
    return {"message": "Registration successful!"}

async def trigger_exchange_init(username,key):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                "http://localhost:5080/okxperp/init_exchange",
                json={"username": username, "redis_key":key},
                timeout=2
            )
        except httpx.HTTPError as e:
            logger.error(f"Exchange pre-warm failed: {e}")




@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), cursor=Depends(with_db_connection)):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    userrow = cursor.fetchone()
    if not userrow:
        raise HTTPException(status_code=404, detail="User not found")

    db_username, db_hashed_pw = userrow
    if not bcrypt.checkpw(password.encode('utf-8'), bytes.fromhex(db_hashed_pw[2:])):
        raise HTTPException(status_code=401, detail="Invalid password")

    cursor.execute("""
        SELECT 
            u.username, 
            u.password, 
            COALESCE(
                JSONB_OBJECT_AGG(ac.exchange, 
                    JSONB_BUILD_OBJECT(
                        'apikey', COALESCE(ac.apikey, 'N/A'),
                        'secretkey', COALESCE(ac.secretkey, 'N/A'),
                        'passphrase', COALESCE(ac.passphrase, 'N/A')
                    )
                ),
                '{}'::jsonb
            ) AS api_credentials
        FROM 
            users u
        LEFT JOIN 
            api_credentials ac ON u.username = ac.username
        WHERE 
            u.username = %s
        GROUP BY 
            u.username, u.password;
    """, (username,))
    _, _, api_creds_dict = cursor.fetchone()

    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(json.dumps({
        'htx_secretkey': api_creds_dict['htx']['secretkey'],
        'htx_apikey': api_creds_dict['htx']['apikey'],
        'okx_secretkey': api_creds_dict['okx']['secretkey'],
        'okx_apikey': api_creds_dict['okx']['apikey'],
        'okx_passphrase': api_creds_dict['okx']['passphrase'],
        'deribit_secretkey': api_creds_dict['deribit']['secretkey'],
        'deribit_apikey': api_creds_dict['deribit']['apikey'],
        'binance_secretkey': api_creds_dict['binance']['secretkey'],
        'binance_apikey': api_creds_dict['binance']['apikey']

    }).encode())

    cache_key = f"user:{username}:api_credentials"
    r.set(cache_key, encrypted_data)

    payload = {
        'sub': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1000)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    logger.info(f"User:{username} login successful.")

    asyncio.create_task(trigger_exchange_init(username,key.decode()))



    return {
        'message': 'Login successful',
        'token': token,
        'key': key.decode(),
        'username': username
    }




@app.get("/logout")
async def logout(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            username = payload.get("sub")
            r.delete(f"user:{username}:api_credentials")
            logger.info(f"User:{username} logout successful.")
        except Exception as e:
            logger.warning(f"Invalid token during logout: {e}")
    else:
        logger.info("Logout called with no token.")

    return {"message": "Logout processed."}


@app.post("/test")
async def test_secure(user=Depends(token_required)):
    username = user.get("sub")
    logger.info(f"Secured route accessed by {username}")
    return {"message": f"Hello, {username}. Secured endpoint working."}
