from datetime import datetime

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime

from model_view_controller.controller import Controller
from model_view_controller.model import Model


def main():
    postgres_connection = sqlalchemy.create_engine(
        "postgresql://postgres:postgres@localhost:5432/postgres"
    )

    class User(Model):
        __tablename__ = "users"
        __schema__ = "public"

        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        nickname = Column(String)
        created_at = Column(DateTime, default=datetime.utcnow)

        def __repr__(self):
            return f"<User(name='{self.name}', fullname='{self.fullname}', nickname='{self.nickname}')>"

    Controller.build(
        postgres_connection,
        User,
    )  # Builds the table using the plan


if __name__ == "__main__":
    main()
