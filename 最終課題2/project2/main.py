from database import Database

def main():
    print("main.py start")

    db = Database()
    db.create_tables()
    print("database OK")

    print("DB ready. Run main_old.py to populate data.")

if __name__ == "__main__":
    main()
