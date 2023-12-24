def log_error_in_db(func=None):
    def decorator():
        print("I got decorated")
        func()

    return decorator
