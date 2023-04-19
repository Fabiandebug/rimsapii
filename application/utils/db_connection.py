import traceback


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pymongo

from ..config import Config


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=False)
SessionLocal = sessionmaker(autocommit=True, autoflush=True, bind=engine)


def session_hook(func: object) -> object:
    """hook opens a database session do a session_hook(read or write) and closes the connection after the run()
    func: function that communicates with the database (e.g fun(*args, db: Session))
    returns;
    data: The return from func
    error: in case of an error in hook"""

    def run(*args, **kwargs):
        global db
        # error = False
        try:
            db = SessionLocal()

            data = func(db, *args, **kwargs)
            # return error, data
            return data
        except Exception as e:
            # traceback.print_exc(e)
            # error = True
            raise Exception(e)

        finally:
            db.close()

    return run


def get_db():
    global db
    # error = False
    try:
        db = SessionLocal()
        # return error, data
        return db
    except Exception as e:
        # traceback.print_exc(e)
        # error = True
        raise Exception(e)
    finally:
        db.close()


def get_staggingdb():
    global client 

    try:
        client = pymongo.MongoClient(Config.MONGODB_STAGGING_DATABASE_URI)
        staggingdb = client[Config.STAGGING_MONGODB_NAME]
        return staggingdb
    except Exception as e: 
        raise Exception(e) 


def get_mongodb():
    global client 

    try:
        client = pymongo.MongoClient(Config.MONGODB_DATABASE_URI)
        mongodb = client[Config.MONGODB_NAME]
        return mongodb
    except Exception as e: 
        raise Exception(e)
   