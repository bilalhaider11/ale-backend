from rococo.repositories.postgresql import PostgreSQLRepository
from rococo.data.postgresql import PostgreSQLAdapter
from rococo.messaging.base import MessageAdapter
from typing import Optional


class BaseRepository(PostgreSQLRepository):
    MODEL = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.MODEL is None:
            raise TypeError(f"Subclasses of {cls.__name__} must define the MODEL attribute.")

    def __init__(
            self, db_adapter: PostgreSQLAdapter, message_adapter: Optional[MessageAdapter], 
            queue_name: str, user_id: str = None
    ):
        if user_id is None:
            try:
                from flask import has_app_context, has_request_context, g
                if has_app_context() and has_request_context() and hasattr(g, "person") and hasattr(g.person, "entity_id"):
                    user_id = g.person.entity_id
            except ImportError:
                # Flask not installed — do nothing or log
                pass

        # Pass MODEL as the model to the BaseRepository
        super().__init__(db_adapter, self.MODEL, message_adapter, queue_name, user_id=user_id)

    def save(self, entity):
        if self.user_id:
            entity.changed_by_id = self.user_id
        return super().save(entity)
