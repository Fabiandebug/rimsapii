import uvicorn
from application.factory import create_app
from application.base.models import Base
from application.utils.db_connection import engine
from application.utils import default_data

# create app instance
app = create_app()

# create database tables.
Base.metadata.create_all(bind=engine)

# create default data
default_data.run()


if __name__ == "__main__":
    # start background task handler.
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)