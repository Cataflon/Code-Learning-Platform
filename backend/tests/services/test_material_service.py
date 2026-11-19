def test_a_material_deleted_while_indexing_is_not_an_error(db_session, monkeypatch, file_store):
    from sqlalchemy.orm.exc import StaleDataError

    from app.services import material_service

    def deleted_meanwhile(*_args, **_kwargs):
        raise StaleDataError("UPDATE expected to update 1 row(s); 0 were matched.")

    monkeypatch.setattr(material_service, "extract_pages", deleted_meanwhile)
    monkeypatch.setattr(db_session, "close", lambda: None)
    monkeypatch.setattr(db_session, "get", lambda *_args: object())

    material_service.extract_pages_in_background(1, lambda: db_session, file_store)  # no raise
