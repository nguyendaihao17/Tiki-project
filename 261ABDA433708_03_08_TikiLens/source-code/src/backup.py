from dataclasses import dataclass
from contextlib import closing
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import sqlite3
import zipfile
import hashlib

import streamlit as st
from bson import json_util

from src.auth import check_permission
from src.database import CLEAN_COLLECTIONS, DB_NAME, get_db_connection


BACKUP_VERSION = 1
MAX_ARCHIVE_SIZE = 250 * 1024 * 1024
MAX_UNCOMPRESSED_SIZE = 1024 * 1024 * 1024
DEFAULT_RESTORE_TEST_DB_NAME = "tikilens_vn_restore_test"
ARCHIVE_MEMBERS = {"manifest.json"} | {
    f"collections/{name}.jsonl" for name in CLEAN_COLLECTIONS
}


class BackupError(ValueError):
    pass


@dataclass
class ValidatedBackup:
    created_at: str
    collections: dict

    @property
    def counts(self):
        return {name: len(documents) for name, documents in self.collections.items()}


def _audit_path():
    configured_path = os.environ.get("TIKI_BACKUP_AUDIT_DB_PATH")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).resolve().parent.parent / "data" / "backup_restore_audit.sqlite3"


def _record_audit(action, status, details, target_db=None):
    username = st.session_state.get("username", "unknown")
    if not os.environ.get("TIKI_BACKUP_AUDIT_DB_PATH"):
        database = get_db_connection()
        if database is None:
            raise BackupError("Không thể kết nối để ghi nhật ký sao lưu.")
        database.client["tikilens_auth"]["backup_restore_audit"].insert_one({
            "timestamp_utc": datetime.now(timezone.utc),
            "username": username,
            "action": action,
            "status": status,
            "target_db": target_db,
            "details": str(details),
        })
        return

    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10)) as connection, connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS backup_restore_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp_utc TEXT NOT NULL,
            username TEXT NOT NULL, action TEXT NOT NULL, status TEXT NOT NULL,
            target_db TEXT, details TEXT NOT NULL)""")
        connection.execute("""INSERT INTO backup_restore_audit
            (timestamp_utc, username, action, status, target_db, details)
            VALUES (?, ?, ?, ?, ?, ?)""", (
                datetime.now(timezone.utc).isoformat(), username, action, status, target_db, str(details),
            ))


def get_backup_restore_audit(limit=50):
    if not check_permission("admin"):
        raise PermissionError("Chỉ quản trị viên được xem nhật ký sao lưu và phục hồi.")
    if not os.environ.get("TIKI_BACKUP_AUDIT_DB_PATH"):
        database = get_db_connection()
        if database is None:
            raise BackupError("Không thể kết nối để đọc nhật ký sao lưu.")
        rows = database.client["tikilens_auth"]["backup_restore_audit"].find(
            {}, {"_id": 0, "timestamp_utc": 1, "username": 1, "action": 1,
                "status": 1, "target_db": 1, "details": 1}
        ).sort("timestamp_utc", -1).limit(max(1, min(int(limit), 500)))
        return [{**row, "timestamp_utc": row["timestamp_utc"].isoformat()} for row in rows]

    path = _audit_path()
    if not path.exists():
        return []
    with closing(sqlite3.connect(path, timeout=10)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT timestamp_utc, username, action, status, target_db, details
            FROM backup_restore_audit
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(int(limit), 500)),),
        ).fetchall()
    return [dict(row) for row in rows]


def create_database_backup():
    if not check_permission("admin"):
        raise PermissionError("Chỉ quản trị viên được sao lưu cơ sở dữ liệu.")
    try:
        database = get_db_connection()
        if database is None:
            raise BackupError("Không thể kết nối cơ sở dữ liệu để sao lưu.")

        created_at = datetime.now(timezone.utc).isoformat()
        archive_buffer = BytesIO()
        manifest = {
            "format_version": BACKUP_VERSION,
            "source_database": DB_NAME,
            "created_at": created_at,
            "collections": {},
        }
        with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for collection_name in sorted(CLEAN_COLLECTIONS):
                documents = list(database[collection_name].find({}))
                member_name = f"collections/{collection_name}.jsonl"
                content = "\n".join(json_util.dumps(document) for document in documents)
                if content:
                    content += "\n"
                archive.writestr(member_name, content.encode("utf-8"))
                manifest["collections"][collection_name] = {
                    "file": member_name,
                    "document_count": len(documents),
                }
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            )

        backup_data = archive_buffer.getvalue()
        if len(backup_data) > MAX_ARCHIVE_SIZE:
            raise BackupError("Bản sao lưu vượt quá giới hạn tải xuống 250 MB.")
        document_counts = {
            name: metadata["document_count"]
            for name, metadata in manifest["collections"].items()
        }
        _record_audit(
            "backup",
            "success",
            json.dumps(document_counts, ensure_ascii=False),
        )
        return backup_data, created_at, document_counts
    except Exception as error:
        _record_audit("backup", "failed", str(error))
        raise


def _configured_restore_test_database_name():
    return os.environ.get(
        "TIKI_RESTORE_TEST_DB_NAME",
        DEFAULT_RESTORE_TEST_DB_NAME,
    ).strip()


def validate_backup_archive(archive_data):
    if not check_permission("admin"):
        raise PermissionError("Chỉ quản trị viên được kiểm tra bản sao lưu.")

    audit_target = _configured_restore_test_database_name()
    try:
        if not archive_data or len(archive_data) > MAX_ARCHIVE_SIZE:
            raise BackupError("File sao lưu trống hoặc vượt quá giới hạn 250 MB.")
        with zipfile.ZipFile(BytesIO(archive_data), "r") as archive:
            entries = archive.infolist()
            entry_names = [entry.filename for entry in entries]
            if len(entry_names) != len(set(entry_names)):
                raise BackupError("File sao lưu chứa tên tệp bị trùng.")
            if set(entry_names) != ARCHIVE_MEMBERS:
                raise BackupError("File sao lưu thiếu hoặc chứa collection không được hỗ trợ.")
            if sum(entry.file_size for entry in entries) > MAX_UNCOMPRESSED_SIZE:
                raise BackupError("Nội dung giải nén vượt quá giới hạn 1 GB.")

            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            if not isinstance(manifest, dict) or manifest.get("format_version") != BACKUP_VERSION:
                raise BackupError("Phiên bản định dạng bản sao lưu không được hỗ trợ.")
            if manifest.get("source_database") != DB_NAME:
                raise BackupError("Bản sao lưu không thuộc cơ sở dữ liệu dự án.")
            if set(manifest.get("collections", {})) != CLEAN_COLLECTIONS:
                raise BackupError("Danh sách collection trong bản sao lưu không hợp lệ.")

            collections = {}
            for collection_name in sorted(CLEAN_COLLECTIONS):
                metadata = manifest["collections"][collection_name]
                expected_file = f"collections/{collection_name}.jsonl"
                if metadata.get("file") != expected_file:
                    raise BackupError(f"Tệp dữ liệu của {collection_name} không hợp lệ.")
                documents = []
                document_ids = set()
                content = archive.read(expected_file).decode("utf-8")
                for line_number, line in enumerate(content.splitlines(), start=1):
                    if not line.strip():
                        continue
                    document = json_util.loads(line)
                    if not isinstance(document, dict):
                        raise BackupError(
                            f"Bản ghi {line_number} trong {collection_name} không phải đối tượng."
                        )
                    if "_id" not in document:
                        raise BackupError(
                            f"Bản ghi {line_number} trong {collection_name} thiếu khóa MongoDB _id."
                        )
                    document_id = json_util.dumps(document["_id"])
                    if document_id in document_ids:
                        raise BackupError(
                            f"Collection {collection_name} có khóa _id bị trùng."
                        )
                    document_ids.add(document_id)
                    documents.append(document)
                if metadata.get("document_count") != len(documents):
                    raise BackupError(f"Số lượng bản ghi {collection_name} không khớp manifest.")
                collections[collection_name] = documents

            validated = ValidatedBackup(
                created_at=str(manifest.get("created_at", "")),
                collections=collections,
            )
        _record_audit(
            "restore_validation",
            "success",
            json.dumps(validated.counts, ensure_ascii=False),
            audit_target,
        )
        return validated
    except zipfile.BadZipFile as error:
        backup_error = BackupError("Tệp tải lên không phải bản sao lưu ZIP hợp lệ.")
        _record_audit(
            "restore_validation",
            "failed",
            str(backup_error),
            audit_target,
        )
        raise backup_error from error
    except Exception as error:
        _record_audit(
            "restore_validation",
            "failed",
            str(error),
            audit_target,
        )
        raise


def restore_backup_to_test_database(validated_backup):
    if not check_permission("admin"):
        raise PermissionError("Chỉ quản trị viên được phục hồi bản sao lưu.")
    target_name = _configured_restore_test_database_name()
    try:
        if target_name == DB_NAME or not target_name.endswith("_restore_test"):
            raise BackupError(
                "Tên cơ sở dữ liệu phục hồi phải khác cơ sở dữ liệu nhóm và kết thúc bằng '_restore_test'."
            )
        if not isinstance(validated_backup, ValidatedBackup):
            raise BackupError("Cần kiểm tra tính hợp lệ của bản sao lưu trước khi phục hồi.")
        database = get_db_connection()
        if database is None:
            raise BackupError("Không thể kết nối MongoDB để phục hồi.")
        target_database = database.client[target_name]
        with database.client.start_session() as session:
            with session.start_transaction():
                for collection_name in sorted(CLEAN_COLLECTIONS):
                    documents = validated_backup.collections[collection_name]
                    collection = target_database[collection_name]
                    collection.delete_many({}, session=session)
                    if documents:
                        collection.insert_many(documents, ordered=True, session=session)

        _record_audit(
            "restore",
            "success",
            json.dumps(validated_backup.counts, ensure_ascii=False),
            target_name,
        )
        return target_name, validated_backup.counts
    except Exception as error:
        _record_audit("restore", "failed", str(error), target_name)
        raise


def backup_fingerprint(archive_data):
    return hashlib.sha256(archive_data).hexdigest()
