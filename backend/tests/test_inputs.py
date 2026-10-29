from io import BytesIO

from docx import Document

from tests.test_projects import create

TEXT = "The system shall let librarians add books.\nThe system shall respond within 2 seconds."


def make_docx(text: str) -> bytes:
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def make_pdf(text: str) -> bytes:
    """Minimal one-page PDF with a single line of text, offsets computed so readers accept it."""
    stream = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


def upload(client, headers, pid, name, data):
    return client.post(f"/api/projects/{pid}/inputs/file", files={"file": (name, data)}, headers=headers)


def test_typed_text_is_stored(client, analyst):  # TC-08
    pid = create(client, analyst)["id"]
    response = client.post(f"/api/projects/{pid}/inputs/text", json={"content": TEXT}, headers=analyst)
    assert response.status_code == 201
    listed = client.get(f"/api/projects/{pid}/inputs", headers=analyst).json()
    assert listed[0]["content"] == TEXT and listed[0]["kind"] == "text"


def test_blank_text_rejected(client, analyst):
    pid = create(client, analyst)["id"]
    response = client.post(f"/api/projects/{pid}/inputs/text", json={"content": "  \n "}, headers=analyst)
    assert response.status_code == 422


def test_docx_upload_parsed(client, analyst):  # TC-09
    pid = create(client, analyst)["id"]
    response = upload(client, analyst, pid, "reqs.docx", make_docx(TEXT))
    assert response.status_code == 201, response.text
    assert "librarians add books" in response.json()["content"]


def test_pdf_and_txt_upload_parsed(client, analyst):
    pid = create(client, analyst)["id"]
    pdf = upload(client, analyst, pid, "reqs.pdf", make_pdf("The system shall export reports."))
    assert pdf.status_code == 201, pdf.text
    assert "export reports" in pdf.json()["content"]
    txt = upload(client, analyst, pid, "notes.txt", TEXT.encode())
    assert txt.status_code == 201 and txt.json()["filename"] == "notes.txt"


def test_oversize_and_unsupported_files_rejected(client, analyst):  # TC-10
    pid = create(client, analyst)["id"]
    big = upload(client, analyst, pid, "big.pdf", b"%PDF" + b"0" * (11 * 1024 * 1024))
    assert big.status_code == 413 and "10 MB" in big.json()["detail"]
    exe = upload(client, analyst, pid, "tool.exe", b"MZ\x90\x00")
    assert exe.status_code == 415 and "Unsupported" in exe.json()["detail"]
    fake = upload(client, analyst, pid, "fake.pdf", b"not really a pdf")
    assert fake.status_code == 415
    assert client.get(f"/api/projects/{pid}/inputs", headers=analyst).json() == []


def test_exactly_10_mb_text_file_is_accepted(client, analyst):  # TC-10 boundary
    pid = create(client, analyst)["id"]
    data = (b"The system shall work.\n" * (10 * 1024 * 1024 // 23 + 1))[: 10 * 1024 * 1024]
    assert upload(client, analyst, pid, "edge.txt", data).status_code == 201


def test_injection_payloads_stored_as_plain_data(client, analyst):  # TC-36, SEC-04
    pid = create(client, analyst)["id"]
    payload = "<script>alert(1)</script> '; DROP TABLE users; --"
    response = client.post(f"/api/projects/{pid}/inputs/text", json={"content": payload}, headers=analyst)
    assert response.json()["content"] == payload
    assert client.get("/api/auth/me", headers=analyst).status_code == 200  # users table intact


def test_path_in_filename_is_stripped(client, analyst):
    pid = create(client, analyst)["id"]
    response = upload(client, analyst, pid, "../../etc/passwd.txt", b"The system shall log in.")
    assert response.json()["filename"] == "passwd.txt"


def test_developer_cannot_add_input(client, analyst):
    from tests.conftest import login, register

    pid = create(client, analyst)["id"]
    register(client, "dev@example.com", "Developer")
    client.post(f"/api/projects/{pid}/members", json={"email": "dev@example.com"}, headers=analyst)
    dev = login(client, "dev@example.com")
    response = client.post(f"/api/projects/{pid}/inputs/text", json={"content": TEXT}, headers=dev)
    assert response.status_code == 403


def test_delete_input(client, analyst):
    pid = create(client, analyst)["id"]
    item = client.post(f"/api/projects/{pid}/inputs/text", json={"content": TEXT}, headers=analyst).json()
    assert client.delete(f"/api/projects/{pid}/inputs/{item['id']}", headers=analyst).status_code == 204
    assert client.delete(f"/api/projects/{pid}/inputs/{item['id']}", headers=analyst).status_code == 404
