from sqlalchemy import Table
from sqlalchemy.orm import Session

from app.database.base import Base
from app.enum.document import DocumentType
from app.errors.database import DBOperationError
from app.models.document import Document
from app.utils.logging_config import logger


def delete_address_proofs(db: Session, link_table: Table, owner_column: str, owner_id: str | int) -> list[str]:
    """Delete the ``proof_of_address`` documents linked to one owner (a driver, a guarantor or a garage).

    Used when the owner's address changes: the proof of the old address is no longer valid. The link rows (in every
    table that references ``document.id``) and the documents go in one transaction. Returns the storage keys so the
    caller can move the files to ``deleted/`` after the commit.
    """
    try:
        documents = (
            db.query(Document)
            .join(link_table, Document.id == link_table.c.document_id)
            .filter(link_table.c[owner_column] == owner_id, Document.type == DocumentType.PROOF_OF_ADDRESS.value)
            .all()
        )
        keys = [doc.url for doc in documents]
        ids = [doc.id for doc in documents]
        if ids:
            for table in Base.metadata.sorted_tables:
                if table is Document.__table__:
                    continue
                for foreign_key in table.foreign_keys:
                    if foreign_key.column.table is Document.__table__ and foreign_key.column.name == "id":
                        db.execute(table.delete().where(foreign_key.parent.in_(ids)))
            db.query(Document).filter(Document.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
    except Exception as ex:
        db.rollback()
        logger.error("Error deleting the address proofs of %s %s: %s", owner_column, owner_id, ex, exc_info=True)
        raise DBOperationError("Error deleting the address proof") from ex
    return keys
