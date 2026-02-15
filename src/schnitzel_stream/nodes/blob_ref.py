from __future__ import annotations

"""
Portable payload reference nodes (P7.2 draft).

Intent:
- Provide a minimal, domain-neutral "blob/handle" strategy for large payloads.
- Current durable lane is JSON-only (see `SqliteQueue*` nodes); this node converts in-proc bytes
  into a portable file reference (`kind=bytes_ref`).

Lifecycle (v1, file scheme):
- Producer writes blobs under a configured directory.
- Consumers treat referenced blobs as read-only.
- Cleanup is out-of-band for now (explicit operator action or future GC/TTL policy).
"""

from dataclasses import replace
import hashlib
from pathlib import Path
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.project import resolve_project_root


def _as_path(raw: Any) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("path must be a non-empty string")
    p = Path(raw.strip())
    if not p.is_absolute():
        p = resolve_project_root() / p
    return p


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


class BytesToFileRefNode:
    """Write in-proc `bytes` payloads to disk and emit a JSON file reference.

    Input packet:
    - kind: bytes
    - payload: bytes

    Output packet:
    - kind: bytes_ref
    - payload: {"ref": {...}}

    Config:
    - dir: str (required) : output directory for blobs
    - filename: str (optional) : file name template
      - Supports: {source_id}, {packet_id}
      - Default: "{source_id}/{packet_id}.bin"
    - compute_sha256: bool (default: true)
    - content_type: str (optional) : informational only (example: "image/jpeg")
    """

    INPUT_KINDS = {"bytes"}
    OUTPUT_KINDS = {"bytes_ref"}

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self._node_id = str(node_id or "bytes_to_file_ref")

        out_dir_raw = cfg.get("dir")
        self._dir = _as_path(out_dir_raw)
        self._dir.mkdir(parents=True, exist_ok=True)

        self._filename = str(cfg.get("filename") or "{source_id}/{packet_id}.bin")
        self._compute_sha256 = bool(cfg.get("compute_sha256", True))
        content_type = cfg.get("content_type")
        self._content_type = str(content_type).strip() if isinstance(content_type, str) and content_type.strip() else None

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        data = packet.payload
        if isinstance(data, bytearray):
            data = bytes(data)
        if isinstance(data, memoryview):
            data = data.tobytes()
        if not isinstance(data, (bytes,)):
            raise TypeError(f"{self._node_id}: expected bytes payload")

        rel = self._filename.format(source_id=str(packet.source_id), packet_id=str(packet.packet_id))
        # Prevent absolute path injection via template.
        rel_path = Path(rel.lstrip("/\\"))
        base_dir = self._dir.resolve()
        out_path = (base_dir / rel_path).resolve()
        try:
            out_path.relative_to(base_dir)
        except ValueError as exc:
            raise ValueError(f"{self._node_id}: output path escapes dir") from exc
        out_path.parent.mkdir(parents=True, exist_ok=True)

        out_path.write_bytes(data)

        ref = {
            "scheme": "file",
            "path": str(out_path),
            "content_type": self._content_type,
            "size_bytes": int(len(data)),
        }
        if self._compute_sha256:
            ref["sha256"] = _sha256_bytes(data)

        out_payload = {"ref": ref}
        yield replace(packet, kind="bytes_ref", payload=out_payload)

    def close(self) -> None:
        return


class FileRefToBytesNode:
    """Read a file reference payload and emit in-proc bytes payloads.

    Input packet:
    - kind: bytes_ref
    - payload: {"ref": {"scheme":"file","path":"..."}}

    Output packet:
    - kind: bytes
    - payload: bytes

    Config:
    - output_kind: str (default: "bytes")
    """

    INPUT_KINDS = {"bytes_ref"}
    OUTPUT_KINDS = {"bytes"}

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self._node_id = str(node_id or "file_ref_to_bytes")
        self._output_kind = str(cfg.get("output_kind", "bytes"))

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        payload = packet.payload
        if not isinstance(payload, dict):
            raise TypeError(f"{self._node_id}: expected payload as a mapping")
        ref = payload.get("ref")
        if not isinstance(ref, dict):
            raise TypeError(f"{self._node_id}: expected payload.ref as a mapping")
        if ref.get("scheme") != "file":
            raise ValueError(f"{self._node_id}: unsupported ref scheme: {ref.get('scheme')!r}")
        path = ref.get("path")
        if not isinstance(path, str) or not path.strip():
            raise TypeError(f"{self._node_id}: expected payload.ref.path as a string")

        data = Path(path).read_bytes()
        yield replace(packet, kind=self._output_kind, payload=data)

    def close(self) -> None:
        return
