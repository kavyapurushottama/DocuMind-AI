# DocuMind AI — Version 1: The Complete Beginner's Guide
### Written for someone who has never seen code or AI before

---

# WHAT IS THIS DOCUMENT?

This document explains **every single file** inside the DocuMind AI project.
For each file, you will learn:
- What the file does (in plain English, no jargon)
- Why the file exists (what would break without it)
- What the code inside actually means, line by line
- What alternatives exist and why this approach was chosen

Think of this as a guided tour of the entire project — like a museum guide
who explains every exhibit, not just the famous ones.

---

# PART 0: THE BIG PICTURE FIRST

Before looking at any individual file, you need to understand the system as a whole.

## What is DocuMind AI?

Imagine you have a 500-page legal contract. You need to know what it says
about "termination clauses". Normally you'd read all 500 pages.

DocuMind AI lets you:
1. Upload the PDF
2. Type "What are the termination clauses?"
3. Get a clear answer — with the exact page number it came from

It works for any document: PDFs, Word files, plain text files.

## The Two Main Parts

DocuMind AI has two halves that constantly talk to each other:

PART 1: FRONTEND (what you see in your browser)
  - Built with: React (a JavaScript framework)
  - Lives at: http://localhost:5173
  - Job: Show pages, buttons, forms. Send requests to the backend.

PART 2: BACKEND (the server you never see)
  - Built with: FastAPI (a Python framework)
  - Lives at: http://localhost:8000
  - Job: Handle logic, talk to databases, call AI services.

## The Three Databases

The backend uses three separate "storage systems":

POSTGRESQL: Like a spreadsheet program.
  - Stores: Users, documents list, chat history
  - Good for: Structured data you can search with exact filters

QDRANT: A special "meaning database" (vector database).
  - Stores: The "meaning" of each paragraph of each document
  - Good for: Finding text that MEANS the same thing as your question

GROQ/GEMINI: Not a database, but an AI service.
  - Does: Reads your question + relevant paragraphs, writes an answer
  - Like: A very well-read expert you can ask questions

## The Key Concept: RAG (Retrieval-Augmented Generation)

RAG is the reason this app works at all. Here is what it means, simply:

WITHOUT RAG: You ask AI "what does my contract say?"
  → AI guesses (it never read your contract)
  → Answer is made up (called "hallucination")

WITH RAG (what DocuMind AI does):
  STEP 1 (when you upload a document):
    - The text is extracted from the PDF
    - It is cut into paragraphs (called "chunks")
    - Each chunk is converted into a list of 768 numbers
      (This list of numbers = the "meaning" of that paragraph)
    - All these numbers are stored in Qdrant

  STEP 2 (when you ask a question):
    - Your question is ALSO converted into 768 numbers
    - Qdrant finds which paragraph-numbers are closest to your question-numbers
    - The actual text of those top 5 paragraphs is retrieved
    - These paragraphs + your question are sent to the AI
    - The AI reads ONLY those paragraphs to write its answer
    - The answer + which paragraphs it used (citations) is returned to you

WHY 768 NUMBERS?
  Converting words to numbers lets us do MATH on meaning.
  "Dog" and "puppy" convert to very similar numbers (close meaning).
  "Dog" and "mortgage" convert to very different numbers (different meaning).
  The AI learned these number-to-meaning mappings from reading the entire internet.

---

# PART 1: THE ROOT LEVEL FILES

These are the files sitting at the very top of the project folder.
"Root level" means they are not inside any subfolder.


---
## FILE: .env.example
### Location: DocuMind AI/.env.example

PURPOSE:
  A template file that shows what secret settings the project needs.
  It does NOT contain real secrets — just placeholder names.

WHY IT EXISTS:
  The real secrets (API keys, passwords) live in a file called ".env"
  which is NEVER uploaded to GitHub or shared with anyone.
  But new developers joining the project need to know WHAT secrets to fill in.
  So .env.example is the "fill in these blanks" template they follow.

WHAT'S INSIDE IT:
  DATABASE_URL=postgresql://docmind:localdevpass@localhost:5432/docmind
  → This is the address of the PostgreSQL database.
    Format: postgresql://USERNAME:PASSWORD@SERVER:PORT/DATABASENAME

  REDIS_URL=redis://localhost:6379
  → Address of Redis (a fast temporary storage). Installed but not actively
    used in V1 — it's ready for future features like caching.

  QDRANT_URL=http://localhost:6333
  → Address of the Qdrant vector database.

  QDRANT_COLLECTION=docmind_chunks
  → Inside Qdrant, data is organized in "collections" (like folders).
    All document paragraphs go into a collection named "docmind_chunks".

  JWT_SECRET=change-this-to-a-long-random-string
  → A secret password used to sign login tokens (like a wax seal on a letter).
    If this is guessed, attackers can fake login credentials.

  JWT_EXPIRE_MINUTES=1440
  → 1440 minutes = 24 hours. Login tokens expire after 1 day.

  GEMINI_API_KEY=your-gemini-api-key
  → Key to access Google's Gemini AI. Get it free at aistudio.google.com

  GROQ_API_KEY=your-groq-api-key
  → Key to access Groq's fast LLaMA-3 AI. Get it free at console.groq.com

  LLM_PROVIDER=groq
  → Which AI to use for answering questions: "groq" or "gemini"
    You can switch anytime by changing just this one word.

  GROQ_MODEL=llama-3.3-70b-versatile
  → The specific AI model inside Groq to use.
    "llama-3.3-70b-versatile" = LLaMA version 3.3, 70 billion parameters.
    More parameters = smarter but slower and more expensive.

  GEMINI_MODEL=gemini-2.0-flash
  → The specific Gemini model. "flash" = faster and cheaper than "pro".

  GEMINI_EMBEDDING_MODEL=text-embedding-004
  → The model used to convert text into 768-number vectors.
    NOT used for answering questions — only for turning text into numbers.

  EMBEDDING_DIM=768
  → The number of dimensions in each embedding vector.
    Must match what the embedding model actually outputs.

  MAX_UPLOAD_MB=25
  → Maximum file size allowed. Files larger than 25MB are rejected.

  UPLOAD_DIR=./uploads
  → Where uploaded files are saved on the server's hard drive.

  CORS_ORIGINS=http://localhost:5173
  → Which websites are allowed to talk to this backend.
    (Explained fully in the main.py section below.)

  VITE_API_URL=http://localhost:8000
  → The frontend needs to know where the backend is.
    This tells the React app "the backend server is at port 8000".

---
## FILE: .gitignore
### Location: DocuMind AI/.gitignore

PURPOSE:
  Tells Git (the version control system) which files to IGNORE.
  These files are never saved to GitHub or shared with teammates.

WHY IT EXISTS:
  Some files should never be shared:
  - .env contains real API keys and passwords (sharing = security disaster)
  - __pycache__ contains compiled Python bytecode (auto-generated, bloats storage)
  - node_modules contains thousands of npm packages (too large, re-downloadable)
  - uploads/ contains user files (private user data)
  - .DS_Store is a Mac metadata file (useless to others)

ANALOGY:
  Git is like a photocopier that copies your project for teammates.
  .gitignore is the sticky note on certain pages saying "DON'T COPY THIS PAGE".

---
## FILE: docker-compose.yml
### Location: DocuMind AI/docker-compose.yml

PURPOSE:
  A single command that starts all three database services at once.
  Run "docker compose up -d" and PostgreSQL, Redis, and Qdrant all start.

WHY IT EXISTS:
  Without Docker, setting up PostgreSQL, Redis, and Qdrant requires:
  - Downloading 3 different installers
  - Configuring each one separately
  - Making sure they don't conflict with each other

  With Docker, you just run one command. Docker creates isolated
  "containers" (like mini virtual computers) for each service.

WHAT'S INSIDE IT:
  services:
    postgres:
      image: postgres:16             → Use PostgreSQL version 16
      environment:
        POSTGRES_DB: docmind         → Create a database called "docmind"
        POSTGRES_USER: docmind       → Username to connect
        POSTGRES_PASSWORD: localdevpass  → Password (local dev only!)
      ports:
        - "5432:5432"               → Make PostgreSQL accessible at port 5432

    redis:
      image: redis:7-alpine          → Lightweight Redis version 7
      ports:
        - "6379:6379"

    qdrant:
      image: qdrant/qdrant:latest    → Latest Qdrant vector database
      ports:
        - "6333:6333"               → REST API port
        - "6334:6334"               → gRPC port (faster internal communication)

ANALOGY:
  Docker is like an IKEA flatpack for software. Instead of building the
  shelf from scratch (installing databases manually), you follow one
  instruction sheet (docker-compose.yml) and everything assembles itself.

---
## FILE: README.md
### Location: DocuMind AI/README.md

PURPOSE:
  The project's "front page" — the first thing anyone reads.
  Contains: what the project does, how to set it up, how to run it.

WHY IT EXISTS:
  GitHub automatically displays README.md on the project's homepage.
  A project without a README is like a product without instructions.


---
# PART 2: THE BACKEND FILES
## Folder: backend/

The backend is the "brain" of the application. It:
- Receives requests from the browser
- Checks if you are logged in
- Reads/writes to databases
- Calls AI services (Groq, Gemini)
- Sends back answers

The backend is written in PYTHON, a programming language famous for its
AI/data science ecosystem. Python code runs on the SERVER, not in your browser.

---
## FILE: backend/requirements.txt
### Location: backend/requirements.txt

PURPOSE:
  A shopping list of all Python packages (libraries) the backend needs.
  Run "pip install -r requirements.txt" and Python downloads them all.

EACH PACKAGE EXPLAINED:

  fastapi==0.115.6
  → The web framework. Handles incoming HTTP requests (like "GET /api/documents")
    and routes them to the right Python function.
    WHY FASTAPI: Automatically generates interactive API documentation.
    Supports async (handling many requests at the same time). Very fast.
    ALTERNATIVE: Django — older, heavier. Flask — simpler but less features.

  uvicorn[standard]==0.34.0
  → The "server" that actually runs FastAPI.
    FastAPI is just code — uvicorn is what makes it listen for web requests.
    ANALOGY: FastAPI is a recipe. Uvicorn is the oven that cooks it.

  pydantic==2.10.4
  → A data validation library. Checks that data has the right shape.
    Example: If the signup form sends "email: 'notanemail'", Pydantic rejects it
    before it even reaches the database.

  pydantic-settings==2.7.1
  → An extension of Pydantic that reads settings from the .env file.
    Makes environment variables available as Python objects.

  sqlalchemy==2.0.36
  → ORM (Object-Relational Mapper). Lets you work with databases using
    Python objects instead of raw SQL queries.
    Instead of: "SELECT * FROM users WHERE email = 'x@y.com'"
    You write:  "db.query(User).filter(User.email == 'x@y.com').first()"
    ALTERNATIVE: Raw SQL — more control but much more error-prone.

  psycopg2-binary==2.9.10
  → The actual driver that connects Python to PostgreSQL.
    SQLAlchemy needs psycopg2 to "speak PostgreSQL".
    Without this, SQLAlchemy wouldn't know HOW to talk to Postgres.

  alembic==1.14.0
  → A database migration tool. When you change a database table
    (add a column, rename one), Alembic tracks the change history.
    IN V1: Installed but not actively used. Schema changes are done
    manually with ALTER TABLE commands in main.py instead.

  python-jose[cryptography]==3.3.0
  → Creates and verifies JWT (JSON Web Tokens) — the "login badges"
    that prove who you are without checking the database every request.

  passlib[bcrypt]==1.7.4
  → Handles password hashing using bcrypt.
    Bcrypt is the gold standard for storing passwords safely.
    WHY NOT SHA256: SHA256 is fast — makes brute-force attacks easy.
    Bcrypt is deliberately slow — brute-forcing takes decades.

  python-multipart==0.0.20
  → Handles file uploads. When you drag a PDF onto the page,
    it is sent as "multipart/form-data". This library reads that format.
    Without it: file uploads would fail with a 422 error.

  qdrant-client==1.12.1
  → The official Python SDK for Qdrant.
    Lets the code store and search vectors without writing raw HTTP calls.

  google-genai==0.3.0
  → Google's official Python library for Gemini.
    Used for BOTH: text-to-vector conversion AND question answering.

  groq==0.13.1
  → Groq's official Python library.
    Used for: fast LLaMA-3 question answering.
    WHY GROQ: Their specialized hardware (LPU chips) makes LLaMA-3
    run at 200+ tokens per second — much faster than standard GPU servers.

  pymupdf==1.25.1
  → A Python binding for MuPDF, a C library for reading PDFs.
    Extracts text from PDF files page by page.
    WHY PYMUPDF: Extremely fast (C library), handles complex PDFs well.
    ALTERNATIVE: pdfplumber (slower), pypdf (less accurate).

  python-docx==1.1.2
  → Reads Microsoft Word (.docx) files.
    Extracts paragraphs from the Word document.

  redis==5.2.1
  → Python client for Redis. Installed but minimally used in V1.
    Prepared for future features: rate limiting, background job queues.

  httpx==0.28.1
  → An HTTP client library (like Python's requests, but async).
    Used to make HTTP requests to Ollama (the local AI option).

  python-dotenv==1.0.1
  → Reads the .env file and loads its values into the program's environment.
    Works alongside pydantic-settings.

---
## FILE: backend/app/main.py
### Location: backend/app/main.py

PURPOSE:
  The entry point of the backend server.
  This is the FIRST file that runs when you start the backend.
  It assembles all the pieces of the application together.

WHAT HAPPENS WHEN THE SERVER STARTS:
  1. Creates the FastAPI app object
  2. Creates database tables if they don't exist
  3. Adds safety middleware (CORS)
  4. Registers all API endpoints (routes)

CODE WALKTHROUGH:

  from fastapi import FastAPI
  → Import the FastAPI framework. "import" = "load this tool".

  app = FastAPI(title="DocuMind AI API", version="1.0.0")
  → Create the actual application. All requests will go through "app".

  Base.metadata.create_all(bind=engine)
  → On first startup, this looks at all the Model classes (User, Document,
    Conversation, Message) and creates the matching tables in PostgreSQL.
    ANALOGY: Like creating the tabs in a binder if they don't exist yet.
    IF THE TABLE ALREADY EXISTS: Nothing happens. It is safe to re-run.

  with engine.connect() as connection:
      connection.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_pinned ..."))
  → This manually adds a new column to an existing table.
    WHY NEEDED: The "is_pinned" feature was added AFTER the initial release.
    The proper way would be an Alembic migration, but V1 keeps it simple.
    "IF NOT EXISTS" makes it safe — if the column is already there, skip it.

  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.cors_origins_list,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  → CORS = Cross-Origin Resource Sharing.
    PROBLEM: Browsers have a security rule: if website A tries to send
    a request to website B, the browser BLOCKS it by default.
    Our frontend (port 5173) and backend (port 8000) are different "origins".
    Without this: the browser would block ALL our API calls.
    WITH this: the backend tells browsers "port 5173 is allowed to call me".

  app.include_router(routes_auth.router)
  app.include_router(routes_documents.router)
  app.include_router(routes_chat.router)
  → Register the three "departments" of the API:
    - Auth department: handles signup, login, get profile
    - Documents department: handles upload, list, delete files
    - Chat department: handles asking questions, conversations
    ANALOGY: Like telling the receptionist "these three managers handle requests".

  @app.get("/health")
  async def health():
      return {"status": "ok"}
  → A simple test endpoint. Going to /health always returns {"status": "ok"}.
    Used by monitoring tools to check "is the server running?"


---
## FILE: backend/app/config.py
### Location: backend/app/config.py

PURPOSE:
  Reads all environment variables from the .env file and makes them
  available throughout the entire backend as a single Python object.

WHY IT EXISTS:
  Instead of reading os.environ["GEMINI_API_KEY"] in 10 different files,
  you import "settings" once and use settings.GEMINI_API_KEY anywhere.
  This also validates types — if DATABASE_URL is missing, the app refuses
  to start with a clear error instead of crashing mysteriously later.

CODE WALKTHROUGH:

  class Settings(BaseSettings):
  → "class" = a blueprint. "BaseSettings" = reads from .env automatically.
    Think of Settings as a form with pre-filled values from .env.

    DATABASE_URL: str = "postgresql://..."
    → The database address. "str" = must be a text string.
      If missing from .env, use this default value.

    JWT_SECRET: str = "change-this-to-a-long-random-string"
    → The signing key for login tokens.
      NOTE: This default is NOT secure — always change it in production!

    LLM_PROVIDER: str = "groq"
    → "groq" or "gemini". Determines which AI answers questions.
      Changing this one value switches the entire AI provider instantly.

    MAX_UPLOAD_MB: int = 25
    → "int" = must be a whole number. Maximum upload size.

  @property
  def cors_origins_list(self) -> list[str]:
      return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
  → "@property" means this can be accessed like a variable, not called like a function.
    The .env stores CORS_ORIGINS as a comma-separated string:
    "http://localhost:5173,https://myapp.com"
    This converts it to a Python list:
    ["http://localhost:5173", "https://myapp.com"]
    WHY: FastAPI's CORS middleware expects a list, not a string.

  settings = Settings()
  → Create ONE instance of Settings. This is imported by all other files.
    The single instance ensures the .env is only read once.

---
## FILE: backend/app/database.py
### Location: backend/app/database.py

PURPOSE:
  Creates the connection to PostgreSQL and provides a database "session"
  to any code that needs to read or write data.

ANALOGY:
  PostgreSQL is a filing cabinet. "database.py" is the person who:
  - Has the keys to the cabinet (connection)
  - Opens a drawer for each visitor (session)
  - Makes sure the drawer is closed after they leave (cleanup)

CODE WALKTHROUGH:

  engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
  → "engine" = the permanent connection manager.
    It keeps a "pool" of pre-opened connections ready.
    pool_pre_ping=True: Before handing out a connection, it sends a tiny
    test query ("SELECT 1") to make sure the connection is still alive.
    WHY: If PostgreSQL restarts, old connections break silently.
    pool_pre_ping detects this and gets a fresh connection instead.

  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  → "sessionmaker" creates a factory for database sessions.
    autocommit=False: Changes are NOT saved until you explicitly say db.commit().
    autoflush=False: Data is not sent to the DB until you commit.
    WHY autocommit=False: You might make 5 changes that all need to succeed together
    (e.g., delete a document AND its vectors AND its file). If step 3 fails,
    you want to undo steps 1 and 2. This is called a "transaction".

  class Base(DeclarativeBase):
      pass
  → The base class that all database table models inherit from.
    SQLAlchemy uses this to know which classes = database tables.

  def get_db():
      db = SessionLocal()     <- Open a new session (drawer)
      try:
          yield db            <- Give it to whoever asked for it
      finally:
          db.close()          <- ALWAYS close it, even if an error occurs
  → This is a FastAPI "dependency" — a function that provides something.
    "yield" is special: it pauses here and resumes in "finally" after the
    route function finishes, guaranteeing cleanup no matter what happens.
    WHY NOT just open db every time: Sessions hold database locks.
    Forgetting to close them causes performance problems and crashes.

---
## FILE: backend/app/models/user.py
### Location: backend/app/models/user.py

PURPOSE:
  Defines the "users" table in PostgreSQL.
  Every column of the table is defined here as a Python attribute.

ANALOGY:
  This is like the column headers of a spreadsheet:
  | id | email | hashed_password | full_name | created_at |

CODE WALKTHROUGH:

  class User(Base):
      __tablename__ = "users"
  → "class User" = the blueprint. "__tablename__" = the actual table name in PostgreSQL.

      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  → UUID = Universally Unique IDentifier. Looks like: "550e8400-e29b-41d4-a716-446655440000"
    WHY UUID instead of 1, 2, 3:
    Sequential IDs are predictable. An attacker knowing user ID=5 exists
    would try ID=6, 7, 8... and enumerate all users.
    UUID is a random 128-bit number — impossible to guess.
    default=uuid.uuid4: Generate a new random UUID for each new user.

      email = Column(String, unique=True, nullable=False, index=True)
  → String = text. unique=True = database rejects duplicate emails (not just code).
    nullable=False = email is REQUIRED (not optional).
    index=True = creates a B-tree index on email.
    WHY INDEX: "Find user where email = X" scans every row without index.
    With index: jumps directly to the right row. 1000x faster for large tables.

      hashed_password = Column(String, nullable=False)
  → We NEVER store the actual password. Only the bcrypt hash.
    Even if someone reads the database, they cannot recover passwords.

      full_name = Column(String, nullable=True)
  → nullable=True = optional. Users don't have to provide their name.

      created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
  → Automatically records when the account was created.
    "lambda: datetime.now(timezone.utc)" = a tiny function called at insert time.
    WHY lambda: If you wrote "default=datetime.now()" (without lambda),
    Python evaluates it ONCE when the class is defined, not when a row is created.
    All users would get the same creation timestamp. lambda fixes this.
    timezone.utc = always store in UTC, convert to local time in the UI.

---
## FILE: backend/app/models/document.py
### Location: backend/app/models/document.py

PURPOSE:
  Defines the "documents" table. Every uploaded file gets one row here.

CODE WALKTHROUGH:

  class DocumentStatus(str, enum.Enum):
      PENDING = "pending"
      PROCESSING = "processing"
      READY = "ready"
      FAILED = "failed"
  → An "enum" is a list of allowed values. The status can ONLY be one of these 4.
    WHY: Without enum, code could accidentally set status = "reedy" (typo)
    and it would silently save. With enum: Python raises an error immediately.
    This models a "state machine":
    PENDING → PROCESSING → READY (success path)
    PENDING → PROCESSING → FAILED (error path)

  class Document(Base):
      __tablename__ = "documents"

      filename = Column(String, nullable=False)
      → The original filename as uploaded ("report.pdf")

      file_path = Column(String, nullable=False)
      → The path on the server's hard disk where the file is saved.
        Example: "./uploads/a1b2c3_report.pdf"

      file_type = Column(String, nullable=False)
      → The extension: "pdf", "docx", "txt", "md"

      file_size_bytes = Column(BigInteger, nullable=False)
      → File size in bytes. BigInteger because PDFs can be tens of MB.
        1 MB = 1,048,576 bytes.

      status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
      → Starts as PENDING. The background task updates it as processing proceeds.

      status_detail = Column(String, nullable=True)
      → A human-readable message shown during processing.
        Examples: "Extracting text contents...", "Vectorizing 47 chunks..."
        The frontend polls this every 2 seconds to show live progress.

      chunk_count = Column(Integer, default=0)
      → How many text chunks were created from this document.
        Updated after embedding is complete.

      page_count = Column(Integer, nullable=True)
      → Number of pages (for PDFs). null for TXT files (no pages).

      error_message = Column(String, nullable=True)
      → If processing fails, the error message is saved here.
        The frontend shows it in the document card as red text.

      user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
      → EVERY document belongs to exactly one user.
        ForeignKey = "this UUID must exist in the users.id column".
        If the user is deleted, their documents can be cascade-deleted.

      user = relationship("User")
      → This lets you write "document.user.email" in Python.
        SQLAlchemy will automatically join the users table.
        Without relationship: you'd need a separate query every time.


---
## FILE: backend/app/models/chat.py
### Location: backend/app/models/chat.py

PURPOSE:
  Defines TWO tables: "conversations" and "messages".
  A conversation is a thread of messages (like a WhatsApp chat thread).
  A message is one individual message in that thread.

WHY TWO TABLES:
  One conversation has MANY messages.
  This is the "one-to-many" database relationship:
    Conversation (1) ←→ Messages (many)
  Storing them in separate tables is cleaner than putting all messages
  in one giant blob of text.

CODE WALKTHROUGH:

  class MessageRole(str, enum.Enum):
      USER = "user"
      ASSISTANT = "assistant"
  → Only two allowed roles: the human (user) or the AI (assistant).
    This mirrors the chat bubble display: user bubbles go right, AI goes left.

  class Conversation(Base):
      __tablename__ = "conversations"

      user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
      → Every conversation belongs to one user.

      document_id = Column(UUID, ForeignKey("documents.id"), nullable=True)
      → nullable=True is important: if null, the conversation is CROSS-DOCUMENT
        (asks across ALL the user's documents).
        If set, the conversation is scoped to ONE specific document.

      title = Column(String, nullable=True)
      → Auto-generated from the first 60 characters of the first question.
        Example: "What are the payment terms in the contr..."

      is_pinned = Column(Boolean, default=False, nullable=False)
      → Users can pin important conversations to keep them at the top.
        Added after initial release via ALTER TABLE in main.py.

      messages = relationship("Message", back_populates="conversation",
                              cascade="all, delete-orphan")
      → "relationship" = SQLAlchemy will load messages automatically.
        cascade="all, delete-orphan": If a conversation is deleted,
        ALL its messages are automatically deleted too.
        WHY: Prevents "orphan" messages with no parent conversation.

  class Message(Base):
      __tablename__ = "messages"

      conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False)
      → Which conversation this message belongs to.

      role = Column(Enum(MessageRole), nullable=False)
      → "user" or "assistant".

      content = Column(Text, nullable=False)
      → The actual message text. "Text" type = unlimited length (unlike String).
        AI responses can be hundreds of words, so we need Text not String.

      citations = Column(JSON, nullable=True)
      → Stores the list of source references as JSON directly in this column.
        Example stored value:
        [{"filename": "contract.pdf", "page": 12, "snippet": "The notice period...", "score": 0.92}]
        WHY JSON column: Avoids creating a separate "citations" table.
        Simple for V1. A production V2 might normalize this into its own table
        for better querying and analytics.

---
## FILE: backend/app/schemas/auth.py
### Location: backend/app/schemas/auth.py

PURPOSE:
  Defines the exact shape of data coming IN (requests) and going OUT (responses)
  for authentication-related API endpoints.

WHY SEPARATE FROM MODELS:
  Models = what's in the DATABASE (includes hashed_password, internal IDs)
  Schemas = what the API EXPOSES (never exposes hashed_password!)

  CRITICAL SECURITY RULE: You NEVER send hashed_password back to the browser.
  Schemas enforce this separation at the code level.

CODE WALKTHROUGH:

  class SignupRequest(BaseModel):
      email: EmailStr
      password: str
      full_name: str | None = None
  → This is what the frontend sends when signing up.
    EmailStr: Pydantic's special email validator. "notvalid" fails.
    "abc@gmail.com" passes. No code needed — validation is automatic.
    str | None = None: full_name is optional (can be None or a string).

  class LoginRequest(BaseModel):
      email: EmailStr
      password: str
  → What the frontend sends when logging in.

  class TokenResponse(BaseModel):
      access_token: str
      token_type: str = "bearer"
  → What the backend sends back after successful login.
    "bearer" is the standard type for JWT tokens.

  class UserResponse(BaseModel):
      id: str
      email: str
      full_name: str | None
      created_at: datetime
      model_config = ConfigDict(from_attributes=True)
  → Returned by GET /api/auth/me ("who am I?").
    Notice: NO hashed_password field.
    "from_attributes=True" allows creating this from a SQLAlchemy User object.

---
## FILE: backend/app/schemas/document.py
### Location: backend/app/schemas/document.py

PURPOSE:
  Defines data shapes for document-related API endpoints.

CODE WALKTHROUGH:

  class DocumentResponse(BaseModel):
      id: str
      filename: str
      file_type: str
      file_size_bytes: int
      status: str
      status_detail: str | None
      chunk_count: int
      page_count: int | None
      error_message: str | None
      created_at: datetime
      model_config = ConfigDict(from_attributes=True)
  → Everything the frontend needs to display a document card.
    Notice: NO file_path. The frontend never needs to know where
    files are stored on the server's disk (security and abstraction).

  class DashboardStats(BaseModel):
      total_documents: int
      total_chats: int
      storage_used_bytes: int
      recent_documents: list[DocumentResponse]
  → The summary data shown at the top of the dashboard.
    Calculated in a single API call instead of 4 separate calls.

---
## FILE: backend/app/schemas/chat.py
### Location: backend/app/schemas/chat.py

PURPOSE:
  Defines data shapes for chat-related API endpoints.

CODE WALKTHROUGH:

  class Citation(BaseModel):
      filename: str
      page: int | None
      chunk_id: str
      snippet: str      <- First 220 characters of the matched text
      score: float      <- Similarity score 0.0 to 1.0
  → One citation = one source paragraph that was used to answer the question.
    "score" = cosine similarity. 1.0 = perfect match, 0.0 = unrelated.
    The CitationBadge in the frontend shows this as a colored confidence bar.

  class AskRequest(BaseModel):
      question: str
      document_id: str | None = None
      conversation_id: str | None = None
  → What the frontend sends when you type a question.
    document_id=None: search ALL user's documents.
    document_id set: search ONLY that one document.
    conversation_id=None: start a new conversation thread.
    conversation_id set: continue an existing thread.

  class MessageResponse(BaseModel):
      id: str
      role: str
      content: str
      citations: list[Citation] | None
      created_at: datetime
  → One message, returned to the frontend with citations attached.

  class AskResponse(BaseModel):
      conversation_id: str
      message: MessageResponse
  → The full response when you ask a question.
    Includes: which conversation it belongs to + the AI message.

---
## FILE: backend/app/core/security.py
### Location: backend/app/core/security.py

PURPOSE:
  Two jobs: (1) hash and verify passwords, (2) create and verify JWT tokens.

ANALOGY:
  (1) Password hashing = putting a document through a shredder.
      You can check "did this paper come from THIS shredder?" but
      you cannot reconstruct the original paper.

  (2) JWT tokens = a hotel key card.
      The hotel (server) issues it, your room number (user ID) is encoded inside,
      and any door reader (API endpoint) can verify it without calling the front desk.

CODE WALKTHROUGH - Passwords:

  def hash_password(password: str) -> str:
      return bcrypt.hashpw(
          password.encode("utf-8"),
          bcrypt.gensalt()
      ).decode("utf-8")
  → password.encode("utf-8"): Convert text string to bytes (bcrypt needs bytes).
    bcrypt.gensalt(): Generate a random "salt" (random noise added before hashing).
    WHY SALT: Without salt, two users with "password123" would have the SAME hash.
    An attacker with a precomputed table of hashes ("rainbow table") would crack both.
    With different salts, same password → different hashes every time.
    .decode("utf-8"): Convert bytes back to a string for storage.

  def verify_password(plain: str, hashed: str) -> bool:
      return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
  → At login: compare what the user typed against the stored hash.
    bcrypt.checkpw handles the salt extraction automatically.
    Returns True (match) or False (wrong password).

CODE WALKTHROUGH - JWT Tokens:

  def create_access_token(subject: str) -> str:
      expire = datetime.now(timezone.utc) + timedelta(minutes=1440)
      payload = {"sub": subject, "exp": expire}
      return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
  → "sub" (subject) = the user's ID string.
    "exp" (expiry) = timestamp 24 hours from now.
    jwt.encode: Creates the 3-part JWT string: header.payload.signature
    "HS256" = HMAC-SHA256. The signature is HMAC(header+payload, JWT_SECRET).
    Anyone can READ the payload (it's just base64). But without JWT_SECRET,
    they cannot forge a valid signature.

  def decode_access_token(token: str) -> str | None:
      try:
          payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
          return payload.get("sub")    <- Return the user ID
      except JWTError:
          return None                  <- Invalid or expired token
  → Verifies the signature and checks expiry automatically.
    Returns the user ID (or None if token is invalid/expired).

---
## FILE: backend/app/core/deps.py
### Location: backend/app/core/deps.py

PURPOSE:
  A "dependency" — a piece of code that FastAPI automatically runs
  BEFORE a route handler, then passes the result to that handler.

  Specifically: "get_current_user" reads the JWT token from the request
  header, verifies it, loads the User from the database, and returns it.
  Any route that uses this dependency is automatically protected.

CODE WALKTHROUGH:

  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
  → Tells FastAPI "the bearer token is in the Authorization header".
    FastAPI automatically extracts "Bearer eyJ..." from the header.

  def get_current_user(
      token: str = Depends(oauth2_scheme),
      db: Session = Depends(get_db)
  ) -> User:
  → "Depends()" = "run this other function and give me its result".
    So: token = the extracted JWT string. db = an open database session.

      user_id = decode_access_token(token)
      if user_id is None:
          raise HTTPException(status_code=401, detail="Could not validate credentials")
  → Decode the token. If invalid/expired, immediately return HTTP 401.
    The browser receives 401, the axios interceptor logs the user out.

      user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
      if user is None:
          raise HTTPException(status_code=401, ...)
  → Even if the token is valid, the user might have been deleted.
    This catches that edge case.

  HOW IT IS USED IN ROUTE FILES:
    @router.get("/documents")
    def list_documents(current_user: User = Depends(get_current_user)):
        # current_user is guaranteed to be a valid, logged-in User object
        # FastAPI ran get_current_user() automatically before this function


---
## FILE: backend/app/api/routes_auth.py
### Location: backend/app/api/routes_auth.py

PURPOSE:
  The HTTP endpoints (URLs) for everything related to user accounts:
  - POST /api/auth/signup    <- Create a new account
  - POST /api/auth/login     <- Log in and get a token
  - GET  /api/auth/me        <- Get your own profile

ANALOGY:
  This file = a customer service counter with three windows:
  Window 1 (signup): "I want to create an account"
  Window 2 (login): "I have an account, give me my key card"
  Window 3 (me): "What is my account information?"

CODE WALKTHROUGH:

  router = APIRouter(prefix="/api/auth", tags=["auth"])
  → Create a "router" — a sub-group of endpoints.
    prefix="/api/auth": All endpoints here start with /api/auth.
    tags=["auth"]: Groups them together in the auto-generated API docs.

  @router.post("/signup", response_model=TokenResponse)
  async def signup(data: SignupRequest, db: Session = Depends(get_db)):
  → "@router.post" = this function handles POST requests to /api/auth/signup.
    "data: SignupRequest" = Pydantic automatically reads + validates the JSON body.
    "db: Session = Depends(get_db)" = FastAPI provides a database session.
    "response_model=TokenResponse" = only the fields in TokenResponse are returned.

      try:
          user = create_user(db, data)
      except ValueError as e:
          raise HTTPException(status_code=400, detail=str(e))
  → "create_user" checks for duplicate emails, hashes password, saves to DB.
    If email exists: ValueError is raised, converted to HTTP 400 Bad Request.
    The browser receives {"detail": "An account with this email already exists"}.

      return issue_token(db, user)
  → Returns {"access_token": "eyJ...", "token_type": "bearer"}.

  @router.post("/login", response_model=TokenResponse)
  async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
  → "OAuth2PasswordRequestForm" = a special FastAPI form reader.
    The frontend sends "username=email@x.com&password=secret" (form-encoded).
    WHY FORM ENCODED (not JSON): This is the OAuth2 standard for login.
    The "username" field is actually the email (OAuth2 quirk).

      user = authenticate_user(db, form.username, form.password)
      if not user:
          raise HTTPException(status_code=401, detail="Invalid credentials")
  → "authenticate_user" finds the user by email, then calls bcrypt.checkpw.
    If either the email doesn't exist OR the password is wrong:
    Return HTTP 401. (We deliberately don't say WHICH one failed —
    this prevents "email enumeration" attacks where attackers test emails.)

  @router.get("/me", response_model=UserResponse)
  async def get_me(current_user: User = Depends(get_current_user)):
      return current_user
  → The simplest endpoint. Just return the current user's info.
    "Depends(get_current_user)" handles the JWT verification automatically.
    If token is invalid: 401 returned before this function even runs.
    If token is valid: current_user is the full User object.

---
## FILE: backend/app/api/routes_documents.py
### Location: backend/app/api/routes_documents.py

PURPOSE:
  The HTTP endpoints for document management:
  - POST /api/documents/upload           <- Upload a new file
  - GET  /api/documents                  <- List all your documents
  - DELETE /api/documents/{id}           <- Delete a document
  - GET  /api/documents/{id}/download    <- Download the original file
  - GET  /api/documents/dashboard/stats  <- Dashboard statistics

THIS FILE CONTAINS THE MOST COMPLEX LOGIC: the document processing pipeline.

CODE WALKTHROUGH - Upload Endpoint:

  @router.post("/upload", response_model=DocumentResponse)
  async def upload_document(
      file: UploadFile = File(...),
      background_tasks: BackgroundTasks,
      db: Session = Depends(get_db),
      current_user: User = Depends(get_current_user),
  ):
  → "UploadFile" = FastAPI's file upload handler.
    "BackgroundTasks" = FastAPI's way of running code AFTER the response is sent.
    The function is ASYNC = can handle other requests while processing.

      ext = file.filename.rsplit(".", 1)[-1].lower()
      if ext not in {"pdf", "docx", "txt", "md"}:
          raise HTTPException(status_code=400, detail="Unsupported file type")
  → Only allow 4 file extensions. "rsplit(".", 1)" splits "report.pdf" into
    ["report", "pdf"] and takes the last part "pdf".

      content = await file.read()
      if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
          raise HTTPException(status_code=413, detail="File too large")
  → Read the entire file into memory. Check size BEFORE saving to disk.
    25 * 1024 * 1024 = 26,214,400 bytes = 25 MB.
    HTTP 413 = "Payload Too Large" (the standard status code for this).

      filename = f"{uuid.uuid4()}_{file.filename}"
      file_path = os.path.join(settings.UPLOAD_DIR, filename)
      with open(file_path, "wb") as f:
          f.write(content)
  → Prepend a UUID to the filename to avoid collisions.
    If two users upload "report.pdf", they get different filenames.
    "wb" = write binary. PDFs are binary files, not text.

      doc = Document(
          user_id=current_user.id,
          filename=file.filename,
          file_path=file_path,
          file_type=ext,
          file_size_bytes=len(content),
          status=DocumentStatus.PENDING,
      )
      db.add(doc)
      db.commit()
      db.refresh(doc)
  → Create the database record immediately with status=PENDING.
    The frontend gets this record back and starts showing the document card.

      background_tasks.add_task(process_document, doc.id, db)
      return doc
  → Schedule the heavy processing to run AFTER we return the response.
    WHY: Processing a large PDF (embedding 500 chunks) takes 30-60 seconds.
    If we waited: the browser would show a spinning loader for 60 seconds.
    With BackgroundTasks: we return immediately (status=pending) and
    the frontend polls every 2 seconds to see status updates.

  async def process_document(document_id, db):
  → The background function. Runs independently, in sequence:

      Step 1: Update status to PROCESSING
        doc.status = DocumentStatus.PROCESSING
        doc.status_detail = "Extracting text contents..."
        db.commit()

      Step 2: Extract text (choose extractor based on file type)
        if doc.file_type == "pdf":
            extractor = PdfExtractor()
        elif doc.file_type == "docx":
            extractor = DocxExtractor()
        else:
            extractor = TxtExtractor()
        pages = extractor.extract(doc.file_path)

      Step 3: Chunk the text
        chunks = chunk_pages(pages)
        doc.page_count = len({c.page_number for c in chunks if c.page_number})
        db.commit()

      Step 4: Embed all chunks
        doc.status_detail = f"Vectorizing {len(chunks)} chunks..."
        db.commit()
        texts = [c.text for c in chunks]
        vectors = embed_texts(texts)

      Step 5: Store in Qdrant
        upsert_chunks(doc.id, current_user.id, doc.filename, chunks, vectors)
        doc.chunk_count = len(chunks)

      Step 6: Mark as READY
        doc.status = DocumentStatus.READY
        doc.status_detail = None
        db.commit()

      If ANYTHING fails:
        doc.status = DocumentStatus.FAILED
        doc.error_message = str(error)
        db.commit()

---
## FILE: backend/app/api/routes_chat.py
### Location: backend/app/api/routes_chat.py

PURPOSE:
  The HTTP endpoints for the chat system:
  - POST /api/chat/ask                           <- Ask a question
  - GET  /api/chat/conversations                 <- List all conversations
  - GET  /api/chat/conversations/{id}/messages   <- Load a specific conversation
  - DELETE /api/chat/conversations/{id}          <- Delete a conversation
  - PATCH /api/chat/conversations/{id}/pin       <- Pin/unpin a conversation

CODE WALKTHROUGH - Ask Endpoint:

  @router.post("/ask", response_model=AskResponse)
  async def ask(
      body: AskRequest,
      db: Session = Depends(get_db),
      current_user: User = Depends(get_current_user),
  ):
  → The main endpoint. Takes a question, returns an answer with citations.

      # Create or find conversation
      if body.conversation_id:
          conv = db.query(Conversation).filter(Conversation.id == ...).first()
      else:
          conv = Conversation(
              user_id=current_user.id,
              document_id=body.document_id,
              title=body.question[:60],   <- First 60 characters as title
          )
          db.add(conv)
          db.commit()
  → First message in a new thread: create the Conversation row.
    Following messages: find the existing Conversation.
    The title is the first question (truncated to 60 chars).

      # Save the user's message
      user_msg = Message(
          conversation_id=conv.id,
          role=MessageRole.USER,
          content=body.question,
      )
      db.add(user_msg)
      db.commit()
  → Save what the user typed BEFORE calling the AI.
    Why: If the AI call fails, the user's question is still in history.

      # Check if user has any documents
      has_documents = db.query(Document).filter(
          Document.user_id == current_user.id,
          Document.status == DocumentStatus.READY
      ).count() > 0

      # Call RAG pipeline
      answer, citations = answer_question(
          question=body.question,
          user_id=str(current_user.id),
          document_id=str(body.document_id) if body.document_id else None,
          has_documents=has_documents,
      )
  → The RAG service does the heavy lifting. Returns the answer text
    and a list of citations (which paragraphs were used).

      # Save AI's message
      ai_msg = Message(
          conversation_id=conv.id,
          role=MessageRole.ASSISTANT,
          content=answer,
          citations=[c.model_dump() for c in citations],
      )
      db.add(ai_msg)
      db.commit()
      return AskResponse(conversation_id=str(conv.id), message=ai_msg)


---
## FILE: backend/app/services/auth_service.py
### Location: backend/app/services/auth_service.py

PURPOSE:
  The business logic for user accounts.
  Routes call these functions — they don't need to know HOW users are created.

CODE WALKTHROUGH:

  def create_user(db, data: SignupRequest) -> User:
      existing = db.query(User).filter(User.email == data.email).first()
      if existing:
          raise ValueError("An account with this email already exists.")
  → Query PostgreSQL for a user with this email.
    .first() returns ONE result or None (not a list).
    If found: raise ValueError (routes_auth.py converts this to HTTP 400).

      user = User(
          email=data.email,
          hashed_password=hash_password(data.password),
          full_name=data.full_name,
      )
      db.add(user)
      db.commit()
      db.refresh(user)
      return user
  → db.refresh(user): After commit, PostgreSQL has generated the id and created_at.
    refresh() re-reads these generated values into the Python object.
    Without refresh: user.id would still be None (not yet filled in).

  def authenticate_user(db, email: str, password: str) -> User | None:
      user = db.query(User).filter(User.email == email).first()
      if not user:
          return None
      if not verify_password(password, user.hashed_password):
          return None
      return user
  → Returns the User if credentials are valid. Returns None otherwise.
    Note: Both "email not found" and "wrong password" return None.
    This prevents revealing which emails are registered (security best practice).

  def issue_token(db, user: User) -> TokenResponse:
      token = create_access_token(str(user.id))
      return TokenResponse(access_token=token, token_type="bearer")
  → Wraps create_access_token in a convenient function.
    Returns the schema object (which auto-converts to JSON in the response).

---
## FILE: backend/app/services/extraction/base_extractor.py
### Location: backend/app/services/extraction/base_extractor.py

PURPOSE:
  An "abstract base class" that defines what ALL extractors must do.
  It is a CONTRACT that every file-type extractor must follow.

WHY IT EXISTS (Design Pattern: Template/Interface):
  The document processing pipeline needs to extract text from any file type.
  Without BaseExtractor, the pipeline code would look like:

    if ext == "pdf":
        text = extract_pdf(path)
    elif ext == "docx":
        text = extract_docx(path)
    elif ext == "txt":
        text = extract_txt(path)

  With BaseExtractor, the pipeline just calls:
    extractor = get_extractor(ext)
    pages = extractor.extract(path)

  Adding a new format (e.g., .xlsx, .pptx) = write one new class.
  The pipeline code never changes.

CODE WALKTHROUGH:

  @dataclass
  class ExtractedPage:
      text: str
      page_number: int | None
  → A simple data container. "text" = the extracted text.
    "page_number" = which page (None for files with no pages like .txt).
    @dataclass automatically generates __init__, __repr__ etc.

  class BaseExtractor(ABC):
  → ABC = Abstract Base Class. Python's way of defining an interface.
    You CANNOT create a BaseExtractor() directly. It is just a blueprint.

      @abstractmethod
      def extract(self, file_path: str) -> list[ExtractedPage]:
          raise NotImplementedError
  → Any class that inherits BaseExtractor MUST implement extract().
    If it doesn't: Python raises a TypeError when you try to create it.
    This is enforced at runtime.

      @staticmethod
      def clean_text(text: str) -> str:
          lines = [line.strip() for line in text.splitlines()]
          lines = [line for line in lines if line]
          return "\n".join(lines)
  → Shared utility method available to ALL extractors.
    "line.strip()" = removes whitespace from both ends of each line.
    "[line for line if line]" = removes completely empty lines.
    Keeps the text clean and avoids embedding empty strings.

---
## FILE: backend/app/services/extraction/pdf_extractor.py
### Location: backend/app/services/extraction/pdf_extractor.py

PURPOSE:
  Extracts text from PDF files, page by page.

CODE WALKTHROUGH:

  class PdfExtractor(BaseExtractor):
      def extract(self, file_path: str) -> list[ExtractedPage]:
          pages = []
          with fitz.open(file_path) as doc:
              for i, page in enumerate(doc):
                  raw_text = page.get_text("text")
                  text = self.clean_text(raw_text)
                  if not text:
                      continue   <- Skip blank pages
                  pages.append(ExtractedPage(text=text, page_number=i + 1))
          return pages
  → "fitz" = PyMuPDF library. "fitz.open()" opens the PDF file.
    "page.get_text("text")" = extract plain text (not images, not layout info).
    "with ... as doc" = Python's "context manager". When the "with" block ends,
    the file is automatically closed (no memory leaks).
    enumerate(doc) = loop with index: i=0,1,2... so page_number=1,2,3...

  WHY PYMUPDF:
  - Written in C (very fast)
  - Handles corrupted PDFs, encrypted PDFs
  - The "text" mode extracts natural reading order
  ALTERNATIVE: pdfplumber (more Python-friendly but slower),
               pypdf (pure Python, but less accurate for complex layouts)

---
## FILE: backend/app/services/extraction/docx_extractor.py
### Location: backend/app/services/extraction/docx_extractor.py

PURPOSE:
  Extracts text from Microsoft Word (.docx) files.

CODE WALKTHROUGH:

  class DocxExtractor(BaseExtractor):
      def extract(self, file_path: str) -> list[ExtractedPage]:
          doc = DocxDocument(file_path)
          paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

          page_size = 25
          pages = []
          for i in range(0, len(paragraphs), page_size):
              chunk = paragraphs[i:i + page_size]
              text = "\n".join(chunk)
              pages.append(ExtractedPage(text=text, page_number=(i // page_size) + 1))
          return pages
  → Word documents have no true "pages" (pages depend on font size, margins, etc.)
    We group every 25 paragraphs into a "pseudo-page".
    So "page 2" means "the 2nd group of 25 paragraphs".

  WHY 25 PARAGRAPHS:
  A typical Word document paragraph averages 100-150 words.
  25 paragraphs ≈ 2500-3750 words ≈ 1-2 actual printed pages.
  This is a reasonable approximation. In V2, we could parse Word's
  page layout XML to get real page numbers.

---
## FILE: backend/app/services/extraction/txt_extractor.py
### Location: backend/app/services/extraction/txt_extractor.py

PURPOSE:
  Extracts text from plain text (.txt) and Markdown (.md) files.

CODE WALKTHROUGH:

  class TxtExtractor(BaseExtractor):
      def extract(self, file_path: str) -> list[ExtractedPage]:
          with open(file_path, "r", encoding="utf-8") as f:
              raw_text = f.read()
          text = self.clean_text(raw_text)
          if not text:
              return []
          return [ExtractedPage(text=text, page_number=None)]
  → "encoding="utf-8"" = UTF-8 handles all languages and special characters.
    Returns exactly ONE page with page_number=None.
    WHY None: Text files have no concept of pages.
    The frontend shows "Ref Doc" instead of "Ref Page X" for citations.

---
## FILE: backend/app/services/chunking.py
### Location: backend/app/services/chunking.py

PURPOSE:
  Splits large text into smaller overlapping pieces called "chunks".
  Each chunk becomes one vector in Qdrant.

WHY CHUNKING:
  You cannot embed an entire 500-page document as one vector.
  Problems with one huge vector:
  1. Embedding models have token limits (usually 8192 tokens)
  2. If the question is about page 347, a whole-document vector is too vague
  3. Citations would just say "see this document" (not helpful)

  With chunks: "See contract.pdf, page 347, paragraph 3"

CODE WALKTHROUGH:

  CHUNK_SIZE_CHARS = 1200
  CHUNK_OVERLAP_CHARS = 200
  → 1200 characters ≈ 200-250 words ≈ 1-2 paragraphs. A good granularity:
    Small enough to point to specific information.
    Large enough to have surrounding context.

    200 character overlap ≈ 1-2 sentences.
    WHY OVERLAP: If a sentence spans the boundary between two chunks,
    without overlap it gets split and neither chunk has the full sentence.
    With 200-char overlap, that sentence appears in BOTH adjacent chunks.

  @dataclass
  class Chunk:
      text: str
      page_number: int | None
      chunk_index: int
  → chunk_index = sequential number within a document (0, 1, 2, ...)
    Used in Qdrant as part of the chunk ID.

  def chunk_pages(pages: list[ExtractedPage]) -> list[Chunk]:
      chunks = []
      idx = 0
      for page in pages:
          text = page.text
          n = len(text)
          start = 0
          while start < n:
              end = min(start + CHUNK_SIZE_CHARS, n)
              piece = text[start:end].strip()
              if piece:
                  chunks.append(Chunk(text=piece, page_number=page.page_number, chunk_index=idx))
                  idx += 1
              if end == n:
                  break
              start = end - CHUNK_OVERLAP_CHARS
      return chunks
  → The sliding window algorithm:
    Position 0: Take chars 0-1200 (chunk 1)
    Position 1000: Take chars 1000-2200 (chunk 2, shares chars 1000-1200 with chunk 1)
    Position 2000: Take chars 2000-3200 (chunk 3)
    And so on until end of text.
    "if end == n: break" prevents an infinite loop at the last chunk.

---
## FILE: backend/app/services/embedding_service.py
### Location: backend/app/services/embedding_service.py

PURPOSE:
  Converts text strings into vectors (lists of 768 numbers).
  Supports two providers: Gemini (cloud) and Ollama (local).

CODE WALKTHROUGH:

  EMBEDDING_PROVIDER = settings.embedding_provider  <- "gemini" or "ollama"

  def embed_texts(texts: list[str]) -> list[list[float]]:
  → Takes a LIST of texts, returns a LIST of vectors.
    Batching is more efficient than one API call per text.

      if EMBEDDING_PROVIDER == "gemini":
          client = genai.Client(api_key=settings.GEMINI_API_KEY)
          result = client.models.embed_content(
              model="text-embedding-004",
              contents=texts,
              config=types.EmbedContentConfig(
                  task_type="RETRIEVAL_DOCUMENT",
                  output_dimensionality=768
              ),
          )
          return [e.values for e in result.embeddings]
  → "task_type=RETRIEVAL_DOCUMENT" = optimizes the embedding for storage.
    (There is also RETRIEVAL_QUERY for the question side.)
    Using the right task type improves search accuracy by ~5%.
    output_dimensionality=768 = we could use up to 768. This is the full size.

      elif EMBEDDING_PROVIDER == "ollama":
          ...
          response = httpx.post(
              "http://localhost:11434/api/embeddings",
              json={"model": OLLAMA_MODEL, "prompt": text}
          )
  → Ollama runs models locally on your machine (no internet required).
    It provides an HTTP API at localhost:11434.
    WHY OLLAMA: For developers who don't want to share data with Google.
    Downside: Requires 4-8GB RAM to run the embedding model locally.

  def embed_query(text: str) -> list[float]:
  → Single text version (for embedding a question at query time).
    Returns just one vector (not a list of lists).
    Uses task_type=RETRIEVAL_QUERY (slightly different optimization than DOCUMENT).


---
## FILE: backend/app/services/vector_store.py
### Location: backend/app/services/vector_store.py

PURPOSE:
  All communication with the Qdrant vector database.
  Three operations: store vectors, search vectors, delete vectors.

WHY A SEPARATE FILE:
  If Qdrant is ever replaced with a different vector database (Weaviate, Pinecone),
  ONLY this one file needs to change. Nothing else in the codebase touches Qdrant directly.
  This is called the "Repository Pattern" in software design.

CODE WALKTHROUGH:

  _client: QdrantClient | None = None

  def _get_client() -> QdrantClient:
      global _client
      if _client is None:
          _client = QdrantClient(url=settings.QDRANT_URL)
      return _client
  → "Singleton pattern" — only ONE client instance is ever created.
    "_client = None" at start. First call: create it. Subsequent calls: reuse it.
    WHY: Creating a client opens a network connection. Creating one per request
    would be wasteful (like hanging up and re-dialing a phone every sentence).

  def ensure_collection():
      client = _get_client()
      existing = [c.name for c in client.get_collections().collections]
      if COLLECTION_NAME not in existing:
          client.create_collection(
              collection_name=COLLECTION_NAME,
              vectors_config=VectorParams(size=768, distance=Distance.COSINE),
          )
  → "ensure_collection" = create the collection if it doesn't exist.
    "vectors_config": each vector has 768 numbers, compared by COSINE distance.
    COSINE DISTANCE: Measures the angle between two vectors (0° = identical meaning).
    WHY COSINE and not Euclidean: Cosine ignores vector magnitude.
    A short sentence and a long sentence about the same topic will be close.
    Euclidean would penalize length differences.

  def upsert_chunks(document_id, user_id, filename, chunks, vectors):
      ensure_collection()
      points = []
      for chunk, vector in zip(chunks, vectors):
          point_id = str(uuid.uuid4())
          points.append(models.PointStruct(
              id=point_id,
              vector=vector,
              payload={
                  "document_id": str(document_id),
                  "user_id": str(user_id),
                  "filename": filename,
                  "text": chunk.text,
                  "page": chunk.page_number,
                  "chunk_index": chunk.chunk_index,
              },
          ))
      client.upsert(collection_name=COLLECTION_NAME, points=points)
  → "upsert" = insert OR update. If the ID already exists, replace it.
    Each "point" = one paragraph, stored with both its vector AND its metadata.
    The metadata (payload) is returned alongside search results — so we know
    WHICH document and page the matched text came from.

  def search(query_vector, user_id, document_id=None, top_k=5):
      must_filters = [
          FieldCondition(key="user_id", match=MatchValue(value=user_id))
      ]
      if document_id:
          must_filters.append(
              FieldCondition(key="document_id", match=MatchValue(value=document_id))
          )
      results = client.query_points(
          collection_name=COLLECTION_NAME,
          query=query_vector,
          query_filter=Filter(must=must_filters),
          limit=top_k,
          with_payload=True,
      ).points
  → CRITICAL SECURITY: "user_id" filter is ALWAYS applied.
    Every search is scoped to one user's data.
    Even though ALL users' chunks are in the same Qdrant collection,
    each user only ever finds THEIR OWN paragraphs.
    Without this filter: User A's question could match User B's documents!

      return [
          {
              "text": r.payload["text"],
              "filename": r.payload["filename"],
              "page": r.payload.get("page"),
              "score": r.score,
              "chunk_id": str(r.id),
          }
          for r in results
      ]
  → Convert Qdrant result objects into simple Python dictionaries.
    "r.score" = the cosine similarity (0.0 to 1.0). Higher = more relevant.

  def delete_document_chunks(document_id):
      client.delete(
          collection_name=COLLECTION_NAME,
          points_selector=FilterSelector(
              filter=Filter(must=[
                  FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))
              ])
          ),
      )
  → Delete ALL vectors that belong to this document.
    Called when a document is deleted in routes_documents.py.
    WHY NECESSARY: If not cleaned up, orphaned vectors take up space
    AND would appear in future search results (polluting answers).

---
## FILE: backend/app/services/rag_service.py
### Location: backend/app/services/rag_service.py

PURPOSE:
  The BRAIN of the entire system.
  Orchestrates the complete question-answering pipeline:
  Question → Embed → Search Qdrant → Build Context → Call LLM → Return Answer + Citations

THIS IS THE MOST IMPORTANT FILE IN THE BACKEND.

CODE WALKTHROUGH:

  TOP_K = 5
  → Retrieve the 5 most relevant chunks. Why 5:
    Too few (1-2): might miss crucial context.
    Too many (10-20): overwhelms the LLM with irrelevant text, increases cost.
    5 is the industry-standard starting point for RAG systems.

  SYSTEM_PROMPT = """
  You are DocuMind AI, a document knowledge assistant.
  Answer the user's question using ONLY the context below.
  Do not use outside knowledge.
  If the answer is not found in the context, say:
  "I couldn't find that information in your documents."
  Be concise, accurate, and cite source numbers when relevant.
  """
  → The "system prompt" = instructions given to the AI before the conversation starts.
    "ONLY the context below" = prevents the AI from using its own training data.
    WHY: Without this, the AI would mix its knowledge with your document's content.
    You'd get answers that sound right but aren't from your document.
    "temperature=0.2" (set in the API call, not here): scale 0.0 to 1.0.
    0.0 = deterministic, robotic. 1.0 = creative, unpredictable.
    0.2 = mostly factual with slight variation (reads naturally).

  NO_DOCS_SYSTEM_PROMPT = """
  You are DocuMind AI. The user has no documents uploaded yet.
  Answer from your general knowledge and encourage them to upload documents.
  """
  → A different prompt used when the user has no documents.
    Allows general conversation and guides them to upload files.

  def _build_context_block(chunks: list[dict]) -> str:
      parts = []
      for i, chunk in enumerate(chunks, start=1):
          page_info = f", page {chunk['page']}" if chunk.get("page") else ""
          source = f"[Source {i}: {chunk['filename']}{page_info}]"
          parts.append(f"{source}\n{chunk['text']}")
      return "\n\n".join(parts)
  → Formats retrieved chunks into a structured context block.
    Example output:
    [Source 1: contract.pdf, page 12]
    The termination clause states that either party may terminate with 30 days notice...

    [Source 2: contract.pdf, page 15]
    In case of material breach, the notice period shall be extended to 60 days...
    
    WHY THIS FORMAT: The LLM can reference "Source 1" and "Source 2" in its answer.
    The structured format helps the LLM understand which text belongs to which source.

  def _call_groq(user_prompt, system_prompt) -> str:
      client = Groq(api_key=settings.GROQ_API_KEY)
      response = client.chat.completions.create(
          model=settings.GROQ_MODEL,
          messages=[
              {"role": "system", "content": system_prompt},
              {"role": "user", "content": user_prompt},
          ],
          temperature=0.2,
          max_tokens=1024,
      )
      return response.choices[0].message.content
  → "messages" is a list of turns in the conversation.
    "system" role = instructions (invisible to user).
    "user" role = the actual question + context.
    max_tokens=1024: Cap the response at ~750 words. Prevents runaway responses.
    response.choices[0] = the first (and usually only) generated response.

  def _call_gemini(user_prompt, system_prompt) -> str:
      client = genai.Client(api_key=settings.GEMINI_API_KEY)
      response = client.models.generate_content(
          model=settings.GEMINI_MODEL,
          contents=user_prompt,
          config=types.GenerateContentConfig(
              system_instruction=system_prompt,
              temperature=0.2,
              max_output_tokens=1024,
          ),
      )
      return response.text
  → Same logic as Groq but using Google's API structure.

  def generate_answer(question, context, system_prompt=None) -> str:
      prompt = f"Context:\n{context}\n\nQuestion: {question}"
      sp = system_prompt or SYSTEM_PROMPT
      if settings.LLM_PROVIDER == "groq":
          return _call_groq(prompt, sp)
      else:
          return _call_gemini(prompt, sp)
  → Chooses Groq or Gemini based on config. Single switch point.
    The question and context are combined into one "user" message.

  def answer_question(question, user_id, document_id=None, has_documents=True):
      if not has_documents:
          answer = generate_answer(question, "", NO_DOCS_SYSTEM_PROMPT)
          return answer, []

      query_vector = embed_query(question)
      chunks = search(query_vector, user_id, document_id, TOP_K)

      if not chunks:
          return "I couldn't find relevant information in your documents.", []

      context = _build_context_block(chunks)
      answer = generate_answer(question, context)

      citations = [
          Citation(
              filename=c["filename"],
              page=c.get("page"),
              chunk_id=c["chunk_id"],
              snippet=c["text"][:220],   <- First 220 chars for the tooltip
              score=c["score"],
          )
          for c in chunks
      ]
      return answer, citations
  → The full pipeline in one function:
    1. Embed the question
    2. Search Qdrant for top 5 matching chunks
    3. Build context block
    4. Generate answer with LLM
    5. Build Citation objects (shown as hoverable badges in the UI)
    6. Return both answer text and citations


---
# PART 3: THE FRONTEND FILES
## Folder: frontend/

The frontend is everything you SEE and CLICK in your browser.
It is written in TYPESCRIPT (JavaScript with type checking) using REACT.

React is a "component-based" UI library. Instead of one giant HTML page,
the UI is broken into reusable components (like LEGO bricks).
Each component is responsible for one part of the screen.

---
## FILE: frontend/package.json
### Location: frontend/package.json

PURPOSE:
  Like requirements.txt for Python, but for JavaScript.
  Lists all npm (Node Package Manager) packages the frontend needs.

EACH DEPENDENCY EXPLAINED:

  "@tanstack/react-query": "^5.62.7"
  → The data-fetching library. Handles: API calls, caching, polling,
    loading states, error states, and optimistic updates.
    WHY NOT FETCH DIRECTLY: Without React Query, you'd need to write
    useEffect + useState + loading/error handling for EVERY data call.
    React Query eliminates 80% of that boilerplate.
    ALTERNATIVE: SWR (similar but fewer features), Redux Toolkit Query (overkill).

  "axios": "^1.7.9"
  → HTTP client for making API requests (GET, POST, DELETE etc.)
    WHY AXIOS over native "fetch":
    - Axios has "interceptors" (middleware for requests/responses)
    - Automatically parses JSON responses
    - Better error handling (fetch doesn't throw on 4xx/5xx errors)
    The interceptors are critical for auto-attaching the JWT token.

  "docx-preview": "^0.4.0"
  → Renders .docx (Word) files in the browser as HTML.
    Word files are binary XML — the browser can't display them natively.
    This library converts them to styled HTML on the fly.
    Used in ChatPage's document preview modal.

  "react": "^18.3.1" and "react-dom": "^18.3.1"
  → React itself. React = the component model. react-dom = renders to the browser.
    Together they power the entire UI.

  "react-router-dom": "^7.1.1"
  → URL-based navigation for React apps.
    Maps URLs to components: /dashboard → DashboardPage, /chat → ChatPage.
    Manages browser history so the Back button works correctly.

  DEV DEPENDENCIES (only used during development, not in production):

  "tailwindcss": "^3.4.17"
  → A CSS framework where you style with utility classes in HTML/JSX.
    Instead of writing a CSS file, you use class names like:
    "flex items-center gap-3 rounded-2xl bg-white p-4 shadow-lg"
    WHY TAILWIND: Much faster to build UI. The generated CSS bundle is
    tiny (only includes classes you actually use).
    ALTERNATIVE: Plain CSS (more verbose), styled-components, CSS Modules.

  "typescript": "^5.7.2"
  → TypeScript = JavaScript + static types.
    Catches errors BEFORE running the code:
    "documentId is a string, you passed a number" → error at compile time.
    Without TypeScript: that error appears only at runtime (maybe in production).

  "vite": "^6.0.7"
  → The build tool and development server.
    WHY VITE over Webpack (old standard):
    - Dev server starts in under 300ms (Webpack: 10-30 seconds)
    - Hot Module Replacement (HMR): component changes appear in browser instantly
    - Much simpler configuration

---
## FILE: frontend/index.html
### Location: frontend/index.html

PURPOSE:
  The single HTML page for the entire application.
  React renders ALL content into the one div: <div id="root">

CODE WALKTHROUGH:

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter...">
  → Load the "Inter" font from Google Fonts.
    Inter is specifically designed for screens (not for print like Times New Roman).
    Used by Notion, Linear, Vercel — modern tech companies.
    WHY "preconnect": Opens the connection to fonts.googleapis.com early,
    reducing font loading time by ~50ms.

  <title>DocuMind AI — Your Intelligent Document Assistant</title>
  → The browser tab title. Also what appears in Google search results.

  <div id="root"></div>
  → The empty container. React's createRoot() targets this div and fills it.
    Without JavaScript, this page would be completely blank.

  <script type="module" src="/src/main.tsx"></script>
  → The entry point. Vite loads this file, which loads React, which loads
    App.tsx, which loads all the pages and components.

---
## FILE: frontend/tailwind.config.js
### Location: frontend/tailwind.config.js

PURPOSE:
  Customizes the Tailwind CSS framework with DocuMind's specific design system.
  Defines colors, fonts, animations, and shadows used throughout the app.

CODE WALKTHROUGH:

  theme: {
    extend: {
      colors: {
        accent: "#5B6FFF",     <- The main purple-blue color
        accentSoft: "#EEF0FF", <- Light accent for backgrounds
        success: "#22C55E",    <- Green (for "Ready" status)
        warning: "#F59E0B",    <- Yellow (for "Processing" status)
        danger: "#EF4444",     <- Red (for "Failed" status, delete buttons)
        ink: "#0F1117",        <- Near-black text color
        paper: "#F8F9FC",      <- Off-white background color
        muted: "#F1F2F6",      <- Very light gray for backgrounds
      },
  → These named colors are used throughout the codebase:
    "text-accent" = purple-blue text. "bg-success" = green background.
    WHY CUSTOM COLORS: Tailwind's default blues/reds are generic.
    Custom colors create a cohesive, branded look.

      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Inter", "system-ui", "sans-serif"],
      },
  → Sets Inter as the default font. "display" = for headings.
    "system-ui" = fallback (uses the OS's native UI font).

      animation: {
        "fade-up": "fade-up 0.3s ease-out",
        "fade-in": "fade-in 0.2s ease-out",
        "spin-slow": "spin 2s linear infinite",
        "pulse-soft": "pulse-soft 2s ease-in-out infinite",
        "ping-soft": "ping 1s cubic-bezier(0,0,0.2,1) infinite",
      },
  → Custom animations used throughout the UI:
    fade-up: New chat messages slide up smoothly.
    spin-slow: The loading spinner during file upload.
    pulse-soft: The pulsing dot on "Processing" status.

      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        float: "0 8px 24px rgba(0,0,0,0.10), ...",
        glow: "0 0 0 3px rgba(91,111,255,0.20)",
      },
  → Shadows: "card" = subtle shadow for document cards.
    "float" = deeper shadow for hover state.
    "glow" = accent-colored outline (shown on focused inputs).

---
## FILE: frontend/src/main.tsx
### Location: frontend/src/main.tsx

PURPOSE:
  The entry point of the React application.
  Creates the React app and wraps it in three "providers".

CODE WALKTHROUGH:

  const queryClient = new QueryClient({
      defaultOptions: {
          queries: {
              retry: 1,
              refetchOnWindowFocus: false,
          },
      },
  });
  → Creates the TanStack Query "client" — the central store for all API data.
    retry: 1 = if an API call fails, try once more before showing an error.
    refetchOnWindowFocus: false = don't re-fetch data when you Alt+Tab back to the browser.
    (Default is true — annoying for this use case, causes confusing UI jumps.)

  ReactDOM.createRoot(document.getElementById("root")!).render(
      <React.StrictMode>
          <QueryClientProvider client={queryClient}>
              <BrowserRouter>
                  <App />
              </BrowserRouter>
          </QueryClientProvider>
      </React.StrictMode>
  );
  → "createRoot" = React 18's modern way to start the app.
    "!" = TypeScript's "non-null assertion". Tells TypeScript "I know this exists".

    THREE PROVIDERS wrap the app like layers of an onion:
    1. StrictMode: In development, runs each render twice to find bugs.
       Double-renders help catch side effects and deprecated API usage.
    2. QueryClientProvider: Makes React Query available to ALL components below.
       Any component can use useQuery/useMutation without prop drilling.
    3. BrowserRouter: Makes URL routing available. Any component can read
       the current URL or navigate to a different page.

---
## FILE: frontend/src/App.tsx
### Location: frontend/src/App.tsx

PURPOSE:
  The root component. Defines ALL URL routes and the navigation bar.
  Also defines "ProtectedLayout" — the guard that requires login.

CODE WALKTHROUGH:

  function ProtectedLayout({ children }: { children: React.ReactNode }) {
      const { isAuthenticated, loading } = useAuth();
      if (loading) return <LoadingDots />;
      if (!isAuthenticated) return <Navigate to="/login" replace />;
      return (
          <div className="min-h-screen bg-paper">
              <NavBar />
              {children}
          </div>
      );
  }
  → "children" = whatever components are nested inside ProtectedLayout.
    THREE STATES:
    - loading=true: Show spinner (auth check not done yet)
    - not authenticated: Redirect to /login
    - authenticated: Show NavBar + the page content

    WHY "loading" STATE: Without it, for ~100ms the app sees "not authenticated"
    (before the token is verified) and redirects to /login — even for logged-in users.
    The "flash to login" bug. The loading check prevents this.

    "replace" in Navigate: Replaces history entry instead of adding one.
    Without replace: pressing Back would go back to the protected route → redirect loop.

  export default function App() {
      return (
          <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />
              <Route path="/dashboard" element={
                  <ProtectedLayout><DashboardPage /></ProtectedLayout>
              } />
              <Route path="/chat" element={
                  <ProtectedLayout><ChatPage /></ProtectedLayout>
              } />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
      );
  }
  → <Routes> = the router container. Only ONE route renders at a time.
    path="*" = wildcard. Catches any URL not defined above.
    Goes to /dashboard (which redirects to /login if not authenticated).

  NAVBAR COMPONENT (defined in App.tsx):
  → Shows the DocuMind AI logo (brain emoji + gradient text).
  → Navigation links: Dashboard, Chat.
  → User greeting + Logout button.
  → Uses useAuth() to show the user's first name.


---
## FILE: frontend/src/hooks/useAuth.ts
### Location: frontend/src/hooks/useAuth.ts

PURPOSE:
  A React "hook" that manages authentication state for the entire application.
  Any component can call useAuth() to: know if logged in, login, logout, signup.

WHAT IS A HOOK:
  A hook is a reusable function that manages "state" (data that changes over time).
  State in React causes the UI to re-render when it changes.
  Example: user=null → "not logged in" UI. user={name: "Alice"} → "Hello Alice" UI.

CODE WALKTHROUGH:

  const TOKEN_KEY = "docmind_token";
  → The key used to store the JWT in localStorage.
    Centralizing it means changing the name needs only one edit.

  export function useAuth() {
      const [user, setUser] = useState<User | null>(null);
      const [loading, setLoading] = useState(true);
      const navigate = useNavigate();
  → useState: React's state system. When setUser() is called, the component re-renders.
    loading starts as true (we don't know yet if logged in or not).
    useNavigate: React Router's function to programmatically go to a URL.

      const loadUser = useCallback(async () => {
          const token = localStorage.getItem(TOKEN_KEY);
          if (!token) {
              setLoading(false);
              return;
          }
          try {
              const me = await authApi.getMe();
              setUser(me);
          } catch {
              localStorage.removeItem(TOKEN_KEY);
          } finally {
              setLoading(false);
          }
      }, []);
  → WHAT IS localStorage:
    A built-in browser storage (like a tiny dictionary).
    Survives page refreshes (unlike React state which resets).
    Limited to ~5MB per domain. Only stores strings.

    FLOW: Check localStorage → token exists? → Call /api/auth/me →
    Got a valid user? → setUser(me). Token invalid? → Remove it from localStorage.
    "finally" block ALWAYS runs (whether success or error) → setLoading(false).

      useEffect(() => {
          loadUser();
      }, [loadUser]);
  → "useEffect" runs ONCE when the component mounts (appears on screen).
    This checks login status on every page load.

      const doLogin = async (email, password) => {
          const { access_token } = await authApi.login(email, password);
          localStorage.setItem(TOKEN_KEY, access_token);
          await loadUser();
          navigate("/dashboard");
      };
  → Login flow:
    1. Call backend → get JWT token
    2. Save token in localStorage (survives refresh)
    3. Load user profile (sets user state)
    4. Navigate to dashboard

      const doLogout = () => {
          localStorage.removeItem(TOKEN_KEY);
          setUser(null);
          navigate("/login");
      };
  → Logout: delete token, clear user state, go to login page.
    Server-side: JWT tokens can't be "invalidated" in basic JWT systems.
    The token still works until its 24-hour expiry, but:
    - It's no longer in localStorage → the browser won't send it
    - For production apps, you'd maintain a "token blacklist" in Redis

      return {
          user,
          isAuthenticated: !!user,  <- true if user is not null
          loading,
          doLogin,
          doLogout,
          doSignup,
          loadUser,
      };
  → "!!" converts null/undefined to false, any object to true.

---
## FILE: frontend/src/api/client.ts
### Location: frontend/src/api/client.ts

PURPOSE:
  Creates and configures the axios HTTP client that ALL API calls use.
  The two interceptors are the most critical code in this file.

CODE WALKTHROUGH:

  export const apiClient = axios.create({
      baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  });
  → "axios.create" = create a pre-configured HTTP client.
    baseURL: All requests use this prefix.
    "http://localhost:8000/api/documents" becomes just "/api/documents" in code.
    import.meta.env.VITE_API_URL reads from frontend/.env:
    VITE_API_URL=http://localhost:8000

  REQUEST INTERCEPTOR:
  apiClient.interceptors.request.use((config) => {
      const token = localStorage.getItem("docmind_token");
      if (token) {
          config.headers.Authorization = Bearer ;
      }
      return config;
  });
  → RUNS BEFORE every single API request.
    Reads the JWT from localStorage and adds it to the Authorization header.
    WITHOUT THIS: Every API function would need to manually add the header:
      axios.post(url, data, { headers: { Authorization: Bearer  } })
    That's 20+ places. The interceptor does it in ONE place.

  RESPONSE INTERCEPTOR:
  apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
          if (error.response?.status === 401) {
              localStorage.removeItem("docmind_token");
              window.location.href = "/login";
          }
          return Promise.reject(error);
      }
  );
  → RUNS AFTER every single API response.
    First function: success path — just pass through.
    Second function: error path — check if it's "401 Unauthorized".
    If 401: the JWT has expired or been tampered with.
    Action: clear the stored token, force-redirect to login.
    "window.location.href" = hard redirect (resets all React state too).
    WHY NOT navigate(): At this point we're outside React, navigate() doesn't work.

---
## FILE: frontend/src/api/auth.ts
### Location: frontend/src/api/auth.ts

PURPOSE:
  Functions for calling authentication endpoints.
  Acts as a clean interface between useAuth.ts and the HTTP calls.

CODE WALKTHROUGH:

  export async function login(email: string, password: string) {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const { data } = await apiClient.post("/api/auth/login", form, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      return data as TokenResponse;
  }
  → WHY URLSearchParams (form-encoded) instead of JSON:
    The backend uses FastAPI's OAuth2PasswordRequestForm.
    This is the OAuth2 standard — it expects form data, not JSON.
    Form-encoded data looks like a URL: "username=x@y.com&password=abc"
    The field is called "username" even though we put an email there.
    This is an OAuth2 quirk — the standard uses "username" as the identifier.

  export async function signup(email: string, password: string, fullName?: string) {
      const { data } = await apiClient.post("/api/auth/signup", {
          email,
          password,
          full_name: fullName,
      });
      return data as TokenResponse;
  }
  → Signup uses JSON (not form-encoded), because it's a custom endpoint.
    Note the name conversion: fullName (JavaScript camelCase) → full_name (Python snake_case).

  export async function getMe() {
      const { data } = await apiClient.get("/api/auth/me");
      return data as User;
  }
  → The simplest API call. Just GET the current user's profile.
    The JWT token is attached automatically by the request interceptor.

---
## FILE: frontend/src/api/documents.ts
### Location: frontend/src/api/documents.ts

PURPOSE:
  Functions for all document-related API calls.

CODE WALKTHROUGH:

  export async function uploadDocument(file: File) {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post("/api/documents/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
      });
      return data as DocumentItem;
  }
  → "FormData" is JavaScript's way to send files over HTTP.
    "multipart/form-data" = the HTTP encoding for file uploads.
    The backend's "file: UploadFile = File(...)" reads this format.

  export async function deleteDocument(id: string) {
      await apiClient.delete(/api/documents/);
  }
  → Template literals: /api/documents/ becomes "/api/documents/abc-123-..."
    Calls DELETE on the backend, which cleans up Qdrant + disk + PostgreSQL.

  export async function downloadDocument(id: string, filename: string) {
      const response = await apiClient.get(/api/documents//download, {
          responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
  }
  → "responseType: blob" = get raw binary data (for the file), not JSON.
    "createObjectURL" = creates a temporary URL in memory for the file blob.
    A hidden <a> tag is created, pointed at this URL, and "clicked" programmatically.
    This triggers the browser's download dialog.
    "revokeObjectURL" frees the memory after the download starts.

---
## FILE: frontend/src/api/chat.ts
### Location: frontend/src/api/chat.ts

PURPOSE:
  Functions for all chat-related API calls.

CODE WALKTHROUGH:

  export async function askQuestion(params: {
      question: string;
      documentId?: string | null;
      conversationId?: string | null;
  }): Promise<{ conversation_id: string; message: ChatMessage }> {
      const { data } = await apiClient.post("/api/chat/ask", {
          question: params.question,
          document_id: params.documentId || null,
          conversation_id: params.conversationId || null,
      });
      return data;
  }
  → Notice: JavaScript uses camelCase (documentId) but Python uses snake_case (document_id).
    This function bridges that gap by renaming the properties.
    "Promise<...>" = TypeScript's type for an async function's return value.

  export async function pinConversation(id: string, pin: boolean) {
      const { data } = await apiClient.patch(/api/chat/conversations//pin, {
          is_pinned: pin,
      });
      return data;
  }
  → PATCH = partial update (update ONE field). Vs PUT = replace everything.
    Pinning only updates the "is_pinned" column, nothing else.

---
## FILE: frontend/src/types/index.ts
### Location: frontend/src/types/index.ts

PURPOSE:
  TypeScript type definitions for all data structures used in the frontend.
  These mirror the backend's Pydantic schemas EXACTLY.

WHY THIS FILE EXISTS:
  TypeScript catches errors at COMPILE TIME (before running code).
  Without types: JavaScript is completely blind.
    result.user.emial  <- typo in "email", no error, just undefined at runtime
  With types:
    result.user.emial  <- TypeScript: "Property 'emial' does not exist on type User. Did you mean 'email'?"

CODE WALKTHROUGH:

  export type DocumentStatus = "pending" | "processing" | "ready" | "failed";
  → A "union type" — the value can ONLY be one of these four strings.
    Mirrors backend's DocumentStatus enum exactly.

  export interface DocumentItem {
      id: string;
      filename: string;
      file_type: string;
      file_size_bytes: number;
      status: DocumentStatus;
      status_detail: string | null;
      chunk_count: number;
      page_count: number | null;
      error_message: string | null;
      created_at: string;
  }
  → An "interface" = the shape of a JavaScript object.
    "string | null" = either a string or null (mirrors Python's "str | None").
    DocumentCard.tsx uses this: function DocumentCard({ doc }: { doc: DocumentItem })
    If the backend ever removes "chunk_count", TypeScript immediately warns all usages.

  export interface Citation {
      filename: string;
      page: number | null;
      chunk_id: string;
      snippet: string;
      score: number;
  }
  → Mirrors backend's Citation Pydantic schema.
    CitationBadge.tsx uses this type.

  export interface ChatMessage {
      id: string;
      role: "user" | "assistant";
      content: string;
      citations: Citation[] | null;
      created_at: string;
  }
  → "Citation[]" = an array of Citation objects.
    ChatBubble.tsx uses this type.


---
## FILE: frontend/src/pages/LoginPage.tsx
### Location: frontend/src/pages/LoginPage.tsx

PURPOSE:
  The login screen. A form with email + password fields.
  On submit: calls doLogin(), which calls the backend, gets a token, saves it.

CODE WALKTHROUGH:

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  → FOUR pieces of state:
    email/password: controlled form values (React tracks every keystroke)
    error: if login fails, show the error message
    loading: while waiting for backend, show a spinner and disable the button

  const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
  → "e.preventDefault()" stops the default browser behavior.
    Without it: the form would submit as a traditional HTML form (page refresh).
    We want to handle it in JavaScript instead.

      setLoading(true);
      setError(null);
      try {
          await doLogin(email, password);
      } catch (err: any) {
          setError(err.response?.data?.detail || "Login failed. Please try again.");
      } finally {
          setLoading(false);
      }
  → "err.response?.data?.detail" = tries to read the backend's error message.
    "?." = optional chaining. If any part is null/undefined, returns undefined.
    Example backend error: {"detail": "Invalid credentials"}
    Shown as: "Invalid credentials" in the red error box.
    Fallback: "Login failed. Please try again." if the error has no detail.

  VISUAL DESIGN:
  → Gradient background with glassmorphism card.
  → Brain emoji logo + "DocuMind AI" gradient text.
  → Email and password inputs with focus glow effect.
  → "Sign in" button that shows a spinner when loading (button disabled too).
  → "Don't have an account? Sign up" link.

---
## FILE: frontend/src/pages/SignupPage.tsx
### Location: frontend/src/pages/SignupPage.tsx

PURPOSE:
  The registration screen. Same structure as LoginPage but with name + confirm password.

ADDITIONAL VALIDATION vs LoginPage:

  if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
  }
  → Client-side check BEFORE sending to the backend.
    Saves a network round trip for a very common mistake.
    The backend also validates, but this gives instant feedback.

  if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
  }
  → Another client-side check. Backend doesn't enforce this,
    but good UX to tell users the rule before they submit.

---
## FILE: frontend/src/pages/DashboardPage.tsx
### Location: frontend/src/pages/DashboardPage.tsx

PURPOSE:
  The home page after login. Shows:
  - Three stat cards (documents, conversations, storage used)
  - File upload zone
  - All document cards with live status
  - Recent conversations list

THIS IS THE LARGEST PAGE COMPONENT.

CODE WALKTHROUGH:

  const { data: stats } = useQuery({
      queryKey: ["dashboard"],
      queryFn: () => getDashboardStats(),
  });
  → useQuery: React Query's main hook.
    "queryKey: ["dashboard"]" = a unique identifier for this data.
    React Query caches by key. If another component also calls useQuery(["dashboard"]),
    they share the SAME cached data (no duplicate API calls).
    "queryFn" = the async function that fetches the data.

  const { data: docs, refetch: refetchDocs } = useQuery({
      queryKey: ["documents"],
      queryFn: () => listDocuments(),
      refetchInterval: (query) => {
          const docs = query.state.data;
          const stillProcessing = docs?.some(
              d => d.status === "pending" || d.status === "processing"
          );
          return stillProcessing ? 2000 : false;
      },
  });
  → "refetchInterval" = how often to re-fetch (in milliseconds).
    It's a FUNCTION (not a fixed number), so it can be dynamic.
    Logic: if ANY document is pending/processing, re-fetch every 2 seconds.
    Otherwise: stop polling (false = no automatic re-fetching).
    WHY NOT ALWAYS POLL: Polling every 2s when nothing is happening
    wastes bandwidth and battery. Smart polling is better UX.

  const uploadMutation = useMutation({
      mutationFn: (file: File) => uploadDocument(file),
      onSuccess: () => {
          refetchDocs();
          queryClient.invalidateQueries({ queryKey: ["dashboard"] });
          setUploadError(null);
      },
      onError: (error: any) => {
          setUploadError(error.response?.data?.detail || "Upload failed.");
      },
  });
  → useMutation: React Query's hook for operations that CHANGE data (POST, PUT, DELETE).
    onSuccess: When upload succeeds:
    - Refetch the documents list (see the new document appear)
    - Invalidate dashboard stats (document count increased)
    "invalidateQueries" marks cached data as stale → triggers a fresh fetch.

  STAT CARDS:
  → "Your Documents" count: stats.total_documents
  → "Conversations" count: stats.total_chats
  → "Storage Used": formatBytes(stats.storage_used_bytes)
    Example: 2.4 MB instead of 2,516,582 bytes.

  GREETING:
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  → Shows "Good morning, Alice!" based on time of day.
    new Date().getHours() = 0-23.

  CONVERSATIONS SECTION:
  → Shows up to 10 recent conversations.
  → Pinned conversations appear first (sorted server-side).
  → Each item has: title, time-ago label, pin button, delete button.
  → Clicking a conversation goes to /chat?conversationId=X.

---
## FILE: frontend/src/pages/ChatPage.tsx
### Location: frontend/src/pages/ChatPage.tsx

PURPOSE:
  The full chat interface. Left sidebar (conversation list) + right chat area.
  The most complex component in the frontend (~537 lines).

KEY FEATURES EXPLAINED:

  URL Parameters for shareable links:
  const [searchParams, setSearchParams] = useSearchParams();
  const documentId = searchParams.get("documentId");
  const convIdParam = searchParams.get("conversationId");
  → The URL /chat?documentId=abc&conversationId=xyz encodes full state.
    You can BOOKMARK or SHARE a conversation URL.
    Opening it restores the exact conversation and document context.

  Optimistic UI update (makes the app feel instant):
  const askMutation = useMutation({
      mutationFn: ({ question }) => askQuestion({ question, documentId, conversationId }),
      onMutate: ({ question }) => {
          // Show user message BEFORE backend responds
          const optimisticMsg = {
              id: 	emp-,
              role: "user",
              content: question,
              created_at: new Date().toISOString(),
          };
          setMessages(prev => [...prev, optimisticMsg]);
          setInput("");
      },
      onSuccess: (data) => {
          // Replace optimistic message with real message, add AI response
          setMessages(prev => [
              ...prev.filter(m => !m.id.startsWith("temp-")),
              data.message,
          ]);
          setConversationId(data.conversation_id);
      },
  });
  → Without onMutate: User types, presses Enter → blank for 2-3 seconds → answer appears.
    With onMutate: User types, presses Enter → INSTANT message appears → then AI response.
    The "thinking dots" animation plays while the AI is generating.

  Thinking Indicator:
  {askMutation.isPending && (
      <div>
          <span>🧠</span>
          <div className="dot-1"></div>
          <div className="dot-2"></div>
          <div className="dot-3"></div>
      </div>
  )}
  → "isPending" = the API call is in flight (not yet returned).
    Three bouncing dots with staggered animation delays (0s, 0.2s, 0.4s).
    Defined in index.css as .dot-1, .dot-2, .dot-3 animations.

  Document Viewer Modal:
  → Clicking a document name opens a full-screen modal showing the file.
  → PDF/TXT: Rendered in an <iframe> (browser handles natively).
  → DOCX: Rendered using the docx-preview library (converts to HTML).
  → The user can read the source document AND chat about it simultaneously.

  Keyboard Shortcut:
  const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleSend();
      }
  };
  → Enter submits the question.
  → Shift+Enter adds a new line (for multi-line questions).
  → Standard chat app convention (like Slack, WhatsApp).

---
## FILE: frontend/src/pages/UploadPage.tsx
### Location: frontend/src/pages/UploadPage.tsx

PURPOSE:
  A legacy page kept for backward compatibility.
  Redirects immediately to /dashboard (where uploads now happen).

  import { Navigate } from "react-router-dom";
  export default function UploadPage() {
      return <Navigate to="/dashboard" replace />;
  }
  → In V1's initial design, there was a separate upload page.
    It was later merged into the dashboard for better UX.
    This file prevents broken links if anyone navigates to /upload.


---
## FILE: frontend/src/components/FileUploader.tsx
### Location: frontend/src/components/FileUploader.tsx

PURPOSE:
  The drag-and-drop upload zone shown on the dashboard.
  Handles three input methods: drag-and-drop, click-to-browse, file selection.
  Shows upload progress animation while uploading.

CODE WALKTHROUGH:

  const ACCEPTED = ".pdf,.docx,.txt,.md";
  → The list of accepted file types. Passed to the hidden <input> element.
    The browser will only allow these extensions in the file picker dialog.
    Server-side validation is ALSO done (this is a user-experience layer only).

  const [dragOver, setDragOver] = useState(false);
  → When the user is dragging a file over the zone, dragOver=true.
    This changes the visual style (blue border, "Drop to upload" text, scale up).

  const inputRef = useRef<HTMLInputElement>(null);
  → "useRef" creates a reference to a DOM element.
    We need this to programmatically "click" the hidden file input.
    When user clicks the zone → inputRef.current.click() → opens file picker.

  DRAG AND DROP EVENTS:
  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
  → "e.preventDefault()" is CRITICAL here.
    Default browser behavior for dragover = open the file (navigate away!).
    preventDefault stops that. Without it, drag-and-drop wouldn't work.

  onDrop={(e) => {
      e.preventDefault();
      setDragOver(false);
      handleFiles(e.dataTransfer.files);
  }}
  → "e.dataTransfer.files" = the files being dragged.
    Same handleFiles function used for both drag-drop and browse.

  const handleFiles = useCallback((files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];  <- Only take the first file
      const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
      setPreview({ name: file.name, ext, size: formatBytes(file.size) });
      onUpload(file);  <- Call the parent component's upload handler
  }, [onUpload]);
  → "useCallback" = memoizes the function. Prevents recreating it on every render.
    Only take files[0] = process one file at a time (V1 limitation).
    "?." = optional chaining. If pop() returns undefined, ?? provides "".

  UPLOAD STATE vs IDLE STATE:
  → Idle: Show upload icon + "Drop your document here" text + file type badges.
  → Uploading: Show spinning animation + filename being uploaded + "Uploading & processing..."
  → dragOver: Animated pulsing border + "Drop to upload" text.

---
## FILE: frontend/src/components/DocumentCard.tsx
### Location: frontend/src/components/DocumentCard.tsx

PURPOSE:
  One card in the document list. Shows all information about one document
  and provides Chat and Delete actions.

CODE WALKTHROUGH:

  const STATUS_CONFIG = {
      ready:      { dot: "bg-success",  pill: "bg-green-50  text-success",   label: "Ready" },
      processing: { dot: "bg-warning",  pill: "bg-amber-50  text-warning",   label: "Processing" },
      pending:    { dot: "bg-t4",       pill: "bg-muted     text-t3",        label: "Pending" },
      failed:     { dot: "bg-danger",   pill: "bg-red-50    text-danger",    label: "Failed" },
  };
  → An object that maps status → visual styles.
    Why this pattern: Avoids long if/else chains.
    Instead of:
      if (status === "ready") { color = "green"; label = "Ready"; }
      else if (status === "processing") { color = "yellow"; ... }
    Just do: STATUS_CONFIG[doc.status].label
    Adding a new status = add one line to the config object.

  function FileIcon({ type }) {
      const { bg, color } = FILE_CONFIG[type] ?? FILE_CONFIG.txt;
      return (
          <div className={ounded-xl }>
              <span className={	ext-[10px] font-extrabold }>
                  {type.toUpperCase().slice(0, 4)}
              </span>
          </div>
      );
  }
  → Shows "PDF" in red, "DOCX" in blue, "TXT" in gray, "MD" in violet.
    "?? FILE_CONFIG.txt" = fallback if type not in config.
    ".slice(0, 4)" = truncate to 4 chars (some extensions could be longer).

  LIVE STATUS DETAIL (during processing):
  {doc.status === "processing" && doc.status_detail ? (
      <span className="animate-pulse-soft text-accent">
          <span className="animate-ping bg-accent" />
          {doc.status_detail}
      </span>
  ) : (
      <>{formatBytes(doc.file_size_bytes)} · {doc.page_count} pages · {doc.chunk_count} chunks</>
  )}
  → While processing: show "Vectorizing 47 chunks..." with a pulsing dot.
  → When ready: show file size, page count, chunk count.
  → The status_detail comes from the backend and updates every 2 seconds.

  ACTIONS (Chat button, Delete button):
  → Chat button: only shown for "ready" status documents.
    Links to /chat?documentId={doc.id}
    Opens a chat scoped to just this one document.

  → Delete button: hidden normally, visible on hover (group-hover CSS).
    Calls onDelete(doc.id) → triggers delete mutation in DashboardPage.

---
## FILE: frontend/src/components/ChatBubble.tsx
### Location: frontend/src/components/ChatBubble.tsx

PURPOSE:
  Renders one message in the chat. User messages and AI messages look different.
  AI messages also show citation badges below.

CODE WALKTHROUGH:

  function timeAgo(iso: string) {
      const diff = Date.now() - new Date(iso).getTime();
      const m = Math.floor(diff / 60_000);
      if (m < 1) return "just now";
      if (m < 60) return ${m}m ago;
      const h = Math.floor(m / 60);
      if (h < 24) return ${h}h ago;
      return ${Math.floor(h / 24)}d ago;
  }
  → Converts ISO timestamp to human-readable relative time.
    "2 minutes ago" is more readable than "2026-07-31T08:23:41Z".
    "60_000" = 60,000. The underscore is a JavaScript readability feature.

  const isUser = message.role === "user";
  → Determines which style to apply.
    User messages: right-aligned, accent-colored (blue/purple), rounded corner bottom-right.
    AI messages: left-aligned, white card with border, rounded corner bottom-left.

  DEDUPLICATION of citations:
  const uniqueCitations = message.citations.reduce((acc, current) => {
      const isDuplicate = acc.some(
          item => item.filename === current.filename && item.page === current.page
      );
      if (!isDuplicate) acc.push(current);
      return acc;
  }, []);
  → The backend returns 5 chunks, but multiple chunks can come from the same page.
    Example: chunks 1, 3, 5 are all from page 12 of contract.pdf.
    Without deduplication: three identical "Ref Page 12" badges appear.
    With deduplication: only one "Ref Page 12" badge appears.

---
## FILE: frontend/src/components/CitationBadge.tsx
### Location: frontend/src/components/CitationBadge.tsx

PURPOSE:
  An interactive badge shown below AI messages.
  Hover over it to see a tooltip with source details.

CODE WALKTHROUGH:

  const [open, setOpen] = useState(false);
  → Controls whether the tooltip is visible.
    onMouseEnter: setOpen(true) → show tooltip.
    onMouseLeave: setOpen(false) → hide tooltip.

  const label = citation.page ? Ref Page  : "Ref Doc";
  → PDF/DOCX: "Ref Page 12" (has a page number).
  → TXT/MD: "Ref Doc" (no page concept, page=null).

  TOOLTIP CONTENT when open=true:
  → File icon + filename + page number
  → The exact text snippet that matched the question
  → ConfidenceBar showing the similarity score

  function ConfidenceBar({ score }) {
      const pct = Math.round(score * 100);
      const color = pct >= 80 ? "bg-success" : pct >= 50 ? "bg-warning" : "bg-danger";
      return (
          <div>
              <span>Relevance</span>
              <span>{pct}%</span>
              <div className={color} style={{ width: ${pct}% }} />
          </div>
      );
  }
  → WHAT IS THE SCORE:
    "Cosine similarity" between the question vector and the chunk vector.
    1.0 (100%) = the chunk is about the EXACT same topic as the question.
    0.5 (50%) = somewhat related.
    0.0 (0%) = completely unrelated.
    COLOR CODING:
    80%+ → Green (highly relevant, good citation)
    50-79% → Yellow (possibly relevant)
    Below 50% → Red (loosely related, use with caution)

---
## FILE: frontend/src/index.css
### Location: frontend/src/index.css

PURPOSE:
  Global CSS styles that apply to the ENTIRE application.
  Custom utilities that can't be easily done with Tailwind alone.

CODE WALKTHROUGH:

  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  → Imports Tailwind's three layers:
    base: CSS resets (normalize browser defaults)
    components: Tailwind component classes
    utilities: The utility classes (flex, text-sm, bg-white, etc.)

  body {
      -webkit-font-smoothing: antialiased;
      font-family: 'Inter', sans-serif;
      background-color: #F8F9FC;
      color: #0F1117;
  }
  → antialiased: makes text rendering smoother on Mac displays (less pixelated).
    F8F9FC: a very slightly blue-tinted white (the "paper" color).
      Pure white (#FFFFFF) is harsh on eyes. This subtle tint reduces eye strain.
    0F1117: near-black (not pure black). Pure black text on white has too much contrast.
      This subtler ratio is easier to read for extended periods.

  .glass {
      background: rgba(255, 255, 255, 0.72);
      backdrop-filter: blur(16px) saturate(180%);
  }
  → "Glassmorphism" — the frosted glass design trend.
    rgba(255,255,255,0.72) = 72% opaque white (partially transparent).
    backdrop-filter: blur: blurs whatever is behind the element.
    saturate(180%): makes background colors more vivid through the glass.
    Used for: the navigation bar, some cards.

  .skeleton {
      background: linear-gradient(90deg, #E5E7EB 0%, #F3F4F6 50%, #E5E7EB 100%);
      background-size: 200% 100%;
      animation: shimmer 1.8s linear infinite;
  }
  → The loading placeholder. Gray blocks that animate a moving light.
    The gradient sweeps left-to-right continuously (shimmer effect).
    Used for: document card skeletons while loading.
    WHY: Shows "something is here, just loading" vs blank white space.
    Called a "skeleton screen" — popularized by Facebook/LinkedIn.

  .dot-1, .dot-2, .dot-3 {
      animation: dot-bounce ... 0s, 0.2s, 0.4s;
  }
  → Three bouncing dots for the AI "thinking" animation.
    Each dot bounces with a 0.2s delay after the previous.
    Creates a wave-like effect: ● ● ● (like typing indicator in iMessage).

---
# PART 4: COMPLETE SYSTEM FLOW DIAGRAMS

## Diagram 1: What happens when you LOG IN

  You type email + password → click "Sign In"
           |
           v
  SignupPage/LoginPage → handleSubmit() → e.preventDefault()
           |
           v  POST /api/auth/login (form-encoded)
  Backend: routes_auth.py → login()
           |
           v  authenticate_user(email, password)
  auth_service.py:
    - Query PostgreSQL for user by email
    - bcrypt.checkpw(typed_password, stored_hash)
    - If wrong: return None → HTTP 401
    - If correct: return User object
           |
           v  create_access_token(user.id)
  security.py:
    - Create JWT: {sub: user_id, exp: now+24h}
    - Sign with JWT_SECRET using HS256
    - Return: "eyJhbGci..." (base64 encoded)
           |
           v  Response: {access_token: "eyJ...", token_type: "bearer"}
  useAuth.ts → doLogin():
    - localStorage.setItem("docmind_token", token)
    - await loadUser() → GET /api/auth/me → setUser(me)
    - navigate("/dashboard")
           |
           v
  Dashboard renders! User is logged in.

---
## Diagram 2: What happens when you UPLOAD a PDF

  Drag PDF onto drop zone
           |
           v
  FileUploader → handleFiles() → onUpload(file)
           |
           v  FormData with the file
  DashboardPage → uploadMutation.mutate(file)
           |
           v  POST /api/documents/upload (multipart/form-data)
  Backend: routes_documents.py → upload_document()

  IMMEDIATE (< 100ms):
    - Check extension (pdf/docx/txt/md)
    - Check size (< 25MB)
    - Save file to ./uploads/uuid_filename.pdf
    - Insert Document row: status=PENDING
    - Schedule background task
    - Return DocumentResponse
           |
           v  Frontend receives doc with status="pending"
  DashboardPage → doc appears in list with "Pending" badge
  React Query polls every 2 seconds

  BACKGROUND (runs concurrently):
  process_document():
    Step 1: status="processing", detail="Extracting text contents..."
    Step 2: PdfExtractor.extract() → list of ExtractedPage objects
    Step 3: chunk_pages() → list of Chunk objects (1200 chars, 200 overlap)
    Step 4: status detail = "Vectorizing N chunks..."
    Step 5: embed_texts(chunk_texts) → Gemini API → 768-float vectors
    Step 6: upsert_chunks() → Qdrant stores vectors + metadata
    Step 7: status="ready", chunk_count=N
           |
           v  Next poll (2 seconds later)
  Frontend sees status="ready" → "Ready" green badge appears
  Polling stops automatically

---
## Diagram 3: What happens when you ASK A QUESTION

  Type "What is the notice period?" → press Enter
           |
           v
  ChatPage → handleSend() → OPTIMISTIC UPDATE:
    - Immediately add user message to UI (feels instant)
    - Set input to ""
           |
           v  POST /api/chat/ask {question, document_id, conversation_id}
  Backend: routes_chat.py → ask()
    - If no conversation_id: create new Conversation row
    - Save user Message row
    - Check if user has any READY documents
           |
           v  answer_question(question, user_id, document_id)
  rag_service.py:

    A. embed_query(question)
       → Gemini API → 768-float vector for the question

    B. vector_store.search(query_vector, user_id, doc_id, top_k=5)
       → Qdrant: filter by user_id (security!)
       → cosine similarity search
       → Return top 5 chunks: [{text, filename, page, score}]

    C. _build_context_block(chunks)
       → Format: "[Source 1: contract.pdf, page 12]\nThe notice period..."

    D. generate_answer(question, context)
       → _call_groq() or _call_gemini()
       → SYSTEM: "Answer ONLY from context. No outside knowledge."
       → USER: "Context: [5 paragraphs]\nQuestion: What is the notice period?"
       → LLM returns: "The notice period is 30 days per Section 8.3."

    E. Build Citation objects from the 5 chunks
           |
           v
  routes_chat.py:
    - Save AI Message row with citations as JSON
    - Return {conversation_id, message: {content, citations}}
           |
           v  Frontend receives answer
  ChatPage → onSuccess():
    - Remove optimistic user message
    - Add real user message + AI message
    - Show CitationBadges below AI message
    - Thinking indicator disappears
           |
           v
  User sees the answer with hoverable page references!

---
# PART 5: V1 LIMITATIONS AND WHAT V2 WOULD IMPROVE

  LIMITATION 1: No streaming responses
  → The answer appears all at once after 2-3 seconds.
  → V2 IMPROVEMENT: Server-Sent Events (SSE) or WebSockets.
    The answer would stream word-by-word like ChatGPT.

  LIMITATION 2: No conversation memory
  → Each question is answered independently.
    The AI doesn't remember what it said in the previous message.
  → V2 IMPROVEMENT: Include recent conversation history in the prompt.
    "[User: What is the notice period?] [AI: 30 days.] [User: And for breach?]"

  LIMITATION 3: Alembic not used
  → Schema changes require manual ALTER TABLE in main.py.
  → V2 IMPROVEMENT: Use Alembic migrations from the start.
    "alembic revision --autogenerate" detects model changes automatically.

  LIMITATION 4: No rate limiting
  → Any logged-in user can make unlimited API calls.
  → V2 IMPROVEMENT: Rate limiting middleware using Redis.
    Example: 60 questions per hour per user.

  LIMITATION 5: Single file at a time
  → FileUploader only takes files[0] (the first file if multiple selected).
  → V2 IMPROVEMENT: Queue multiple files, process them in parallel.

  LIMITATION 6: Basic auth (no OAuth)
  → Sign up/login with email+password only.
  → V2 IMPROVEMENT: "Sign in with Google/GitHub" via OAuth2.

---
# QUICK REFERENCE: WHAT DOES EACH FILE DO?

  BACKEND FILES:
  main.py               → Start the server, register all routes
  config.py             → Read .env settings into Python objects
  database.py           → Connect to PostgreSQL, provide DB sessions
  models/user.py        → Define "users" table columns
  models/document.py    → Define "documents" table columns
  models/chat.py        → Define "conversations" and "messages" tables
  schemas/auth.py       → Shape of login/signup request and response data
  schemas/document.py   → Shape of document data for the API
  schemas/chat.py       → Shape of chat/citation data for the API
  core/security.py      → Hash passwords, create/verify JWT tokens
  core/deps.py          → "Who is making this request?" auth dependency
  api/routes_auth.py    → /api/auth/* endpoints (signup, login, me)
  api/routes_documents.py → /api/documents/* endpoints (upload, list, delete)
  api/routes_chat.py    → /api/chat/* endpoints (ask, conversations)
  services/auth_service.py        → User creation and authentication logic
  services/chunking.py            → Split text into overlapping chunks
  services/embedding_service.py   → Convert text to 768-number vectors
  services/vector_store.py        → Store/search/delete vectors in Qdrant
  services/rag_service.py         → The full Q&A pipeline orchestrator
  services/extraction/base_extractor.py  → Abstract interface for extractors
  services/extraction/pdf_extractor.py   → Extract text from PDFs
  services/extraction/docx_extractor.py  → Extract text from Word files
  services/extraction/txt_extractor.py   → Extract text from TXT/MD files

  FRONTEND FILES:
  index.html            → The single HTML page (React renders inside it)
  package.json          → JavaScript dependencies list
  tailwind.config.js    → Custom colors, animations, shadows
  src/main.tsx          → Bootstrap React app with providers
  src/App.tsx           → URL routes + ProtectedLayout + NavBar
  src/index.css         → Global styles, glassmorphism, skeleton, animations
  src/hooks/useAuth.ts  → Login state management for the whole app
  src/api/client.ts     → Axios HTTP client with JWT interceptors
  src/api/auth.ts       → Login/signup/getMe API calls
  src/api/documents.ts  → Upload/list/delete/download API calls
  src/api/chat.ts       → Ask/conversations/pin API calls
  src/types/index.ts    → TypeScript type definitions
  src/pages/LoginPage.tsx     → Login form UI
  src/pages/SignupPage.tsx    → Registration form UI
  src/pages/DashboardPage.tsx → Main home page with all documents and stats
  src/pages/ChatPage.tsx      → Full chat interface with document viewer
  src/pages/UploadPage.tsx    → Redirect to dashboard (legacy)
  src/components/FileUploader.tsx   → Drag-and-drop upload zone
  src/components/DocumentCard.tsx   → One document row card
  src/components/ChatBubble.tsx     → One chat message bubble
  src/components/CitationBadge.tsx  → Hoverable source reference badge

  ROOT FILES:
  .env                  → Real secrets (never share this!)
  .env.example          → Template showing what secrets are needed
  .gitignore            → Files/folders Git should never track
  docker-compose.yml    → One-command startup for PostgreSQL, Redis, Qdrant
  README.md             → Project overview and setup instructions

---
END OF DOCUMENT

DocuMind AI V1 - Complete Guide
Generated: 2026-07-31
Total files explained: 36
