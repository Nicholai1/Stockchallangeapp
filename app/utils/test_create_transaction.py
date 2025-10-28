from app.database import SessionLocal, engine
from app.models import Base, User, Transaction
from app.utils.auth import get_password_hash
import yfinance as yf

# --- DROP og genopret alle tabeller (kun under udvikling!) ---
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# --- Start database session ---
db = SessionLocal()

# --- Funktion til at oprette testbruger ---
def create_test_user(username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user:
        print(f"Brugernavn '{username}' findes allerede!")
        return user
    hashed_pw = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"Bruger oprettet: ID={new_user.id}, Username={new_user.username}, Created_at={new_user.created_at}")
    return new_user

# --- Funktion til at oprette testtransaktion ---
def create_test_transaction(user_id: int, symbol: str, type_: str, quantity: float, price: float):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    company_name = info.get("longName") or symbol
    currency = info.get("currency") or "USD"

    new_transaction = Transaction(
        user_id=user_id,
        symbol=symbol,
        name=company_name,
        type=type_,
        quantity=quantity,
        price=price,
        currency=currency
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    print(f"Transaktion oprettet: ID={new_transaction.id}, Symbol={new_transaction.symbol}, "
          f"Company={new_transaction.name}, Type={new_transaction.type}, Qty={new_transaction.quantity}, "
          f"Price={new_transaction.price}, Currency={new_transaction.currency}")

    return new_transaction

# --- Funktion til at hente alle transaktioner for en bruger ---
def get_transactions_for_user(user_id: int):
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    if not transactions:
        print(f"Ingen transaktioner fundet for bruger {user_id}")
    for t in transactions:
        print(f"ID={t.id}, Symbol={t.symbol}, Company={t.name}, Type={t.type}, Qty={t.quantity}, "
              f"Price={t.price}, Currency={t.currency}, Created_at={t.created_at}")
    return transactions

# --- Kør testsekvens ---
if __name__ == "__main__":
    # --- Opret flere testbrugere ---
    users = [
        create_test_user("alice", "Password123"),
        create_test_user("bob", "Secret456"),
        create_test_user("charlie", "Hemmelig789")
    ]

    # --- Opret transaktioner for hver bruger ---
    transactions_data = {
        "alice": [
            ("AAPL", "BUY", 10, 175.0),
            ("TSLA", "BUY", 3, 290.0)
        ],
        "bob": [
            ("MSFT", "BUY", 5, 330.2),
            ("GOOGL", "SELL", 1, 136.8)
        ],
        "charlie": [
            ("AMZN", "BUY", 2, 98.5),
            ("NFLX", "BUY", 4, 450.0),
            ("AAPL", "SELL", 2, 175.0)
        ]
    }

    for user in users:
        for symbol, type_, qty, price in transactions_data[user.username]:
            create_test_transaction(user.id, symbol, type_, qty, price)

    # --- Hent og vis alle transaktioner for alle brugere ---
    for user in users:
        print(f"\nTransaktioner for bruger {user.username}:")
        get_transactions_for_user(user.id)

# --- Luk session til sidst ---
db.close()