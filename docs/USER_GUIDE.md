# ReqTrace user guide

ReqTrace turns raw requirements into an IEEE 830 Software Requirements Specification (SRS), then
generates test cases, a test plan and UML diagrams and keeps a requirement-to-test traceability matrix.
Every AI output is editable and versioned, and nothing is used downstream until a person approves it.

> AI-generated content must be reviewed by a human before use.

## 1. Accounts and roles

Open the app (https://localhost with Docker Compose, https://localhost:8443 on Kubernetes) and choose
**Create an account**. Pick your role:

| Role | Can do |
|---|---|
| Analyst | Add input, generate, edit and approve the SRS, generate tests, test plan and diagrams |
| QA Engineer | Generate and edit test cases and the test plan; cannot approve an SRS |
| Developer | Generate and edit UML diagrams; read everything else |
| Administrator | Everything an Analyst can, plus user roles and the audit log (created by the deployment, not self-registered) |

Sessions end after 60 minutes without activity, or when you log out.

## 2. Projects

1. On **Projects**, choose **New project**, enter a name and an optional description.
2. In the project's **Overview** tab the owner can add members by email, rename, archive or delete the
   project. Only members can open a project.

## 3. Input

In the **Input** tab, paste requirements as text or upload a **TXT, DOCX or PDF** file (up to 10 MB).
Files of other types, or larger files, are rejected with a message.

## 4. SRS

1. In the **SRS** tab choose **Generate SRS**. The SRS agent writes all IEEE 830 sections and lists every
   requirement with a unique ID (FR-01…, NFR-01…). This usually takes 10–30 seconds.
2. **Check quality** flags vague words (for example "fast", "user-friendly") with a suggested
   measurable rewrite, empty sections, and conflicting requirements.
3. **Edit** changes sections and requirements. **Save as new version** keeps the previous version.
4. **Compare** shows what changed between two versions.
5. **Approve** (Analyst or Administrator) records who approved the version and when. Test cases, the
   test plan and diagrams are generated from the latest **approved** version.
6. **Export DOCX** downloads the selected version as a Word document.

## 5. Test cases and traceability

1. In **Test Cases**, choose **Generate tests**: each requirement gets positive, negative and, where it
   has a limit, boundary tests with steps and an expected result. Add, edit or delete cases as needed.
2. **Traceability** shows each requirement with its test cases, the coverage percentage, and highlights
   any requirement without a test in red.
3. Both tabs have **Export CSV**.

## 6. Test plan and diagrams

- **Test Plan** → **Generate test plan** writes scope, approach, environment, schedule, risks, entry
  and exit criteria. Edit any section; **Export DOCX** downloads it.
- **Diagrams** → **Generate diagrams** creates use-case, class and sequence diagrams. **Edit source**
  lets you correct the Mermaid text and re-render; **Export PNG** downloads an image.

## 7. Administration

Administrators see **Admin** in the header:

- **Users and roles**: change a user's role or deactivate an account (their sessions end immediately).
- **Audit log**: who created, edited, generated, approved, exported or deleted what, and when.

## 8. When the AI service is unavailable

If the LLM provider is down or over quota, generation shows "The AI service could not produce a valid
result right now. Your work is saved; please try again." Saved input and versions are never lost, and
every other page keeps working.
