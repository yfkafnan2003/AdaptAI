from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Conversation, Message


def test_conversation_stores_messages_in_order():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        conv = Conversation(user_id="u1")
        conv.messages.append(Message(role="user", content="hi"))
        conv.messages.append(Message(role="assistant", content="hello"))
        db.add(conv)
        db.commit()

        saved = db.query(Conversation).one()
        assert saved.user_id == "u1"
        assert [m.role for m in saved.messages] == ["user", "assistant"]