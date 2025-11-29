import os
from pathlib import Path

# OLLAMA LLM
OLLAMA_MODEL = "qwen2.5:7b-instruct-q4_K_M"
OLLAMA_URL = "http://localhost:11434/api/generate"
TIMEOUT_OLLAMA = 90

# DIRECTORIES
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
VOICE_DIR = BASE_DIR / "voice"
ACTIONS_DIR = BASE_DIR / "actions"

# Data files
SKILLS_FILE = DATA_DIR / "skills.json"
MEMORY_FILE = DATA_DIR / "memory.json"
PREFERENCES_FILE = DATA_DIR / "preferences.json"
CREDENTIALS_FILE = DATA_DIR / "credentials.json"

# VOICE
WHISPER_MODEL = "medium"
WHISPER_DEVICE = "auto"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_LANGUAGE = "fr"
WHISPER_VAD_FILTER = True

TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
TTS_DEVICE = "auto"
TTS_LANGUAGE = "fr"
TTS_SPEAKER_WAV = None

AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1024
AUDIO_SILENCE_THRESHOLD = 500
AUDIO_SILENCE_DURATION = 1.5
AUDIO_MIN_PHRASE_LENGTH = 0.5

USE_WAKE_WORD = False
WAKE_WORD = "jarvis"

# ACTIONS
TIMEOUT_GUI_ACTION = 10
TIMEOUT_WEB_ACTION = 30
TIMEOUT_FILE_ACTION = 15
TIMEOUT_EMAIL_ACTION = 20

WEB_SCREENSHOTS_DIR = DATA_DIR / "screenshots"

PYAUTOGUI_PAUSE = 0.5
PYAUTOGUI_FAILSAFE = True

REQUIRE_CONFIRMATION_EMAIL = True
REQUIRE_CONFIRMATION_PURCHASE = True
REQUIRE_CONFIRMATION_FILE_DELETE = True
REQUIRE_CONFIRMATION_SYSTEM_COMMAND = False

MAX_AUTO_PURCHASE_AMOUNT = 0

# PLAYWRIGHT SUPPORT (Étape 3)
CHROME_DEBUG_PORT = 9222
AUTO_LAUNCH_CHROME = True 
ENABLE_PLAYWRIGHT_SUPPORT = True
AUTO_CLOSE_POPUPS = True

# USER INTERVENTION (Étape 4)
ENABLE_USER_INTERVENTION_DETECTION = True
ENABLE_KEYBOARD_CONTROL = True  # Touches P/C/Q
USER_INTERVENTION_VLM_VALIDATION = False  # VLM validation (plus lent)

# Confirmations (existants + nouveau)
REQUIRE_CONFIRMATION_DOWNLOAD = True  # Nouveau pour téléchargements

# Mots-clés détection
USER_INTERVENTION_KEYWORDS_CAPTCHA = ["captcha", "recaptcha", "verify", "i'm not a robot", "i am not a robot"]
USER_INTERVENTION_KEYWORDS_PASSWORD = ["password", "mot de passe", "login", "sign in", "connexion"]

# VLM for CUA
TARS_MODEL_NAME = "qwen3-vl:4b"
FALLBACK_VLM_MODEL = "qwen2.5vl"

# =========================
# VISION PIPELINE
# =========================

# VISION - OmniParser v2.0 (Icon Detection + Semantic Caption)
import torch
OMNIPARSER_WEIGHTS_DIR = BASE_DIR / "OmniParser" / "weights"
OMNIPARSER_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
OMNIPARSER_CONFIDENCE_THRESHOLD = 0.25  # Seuil de confiance minimum pour YOLOv8

# LEGACY - PaddleOCR (deprecated, keeping for reference)
PADDLE_OCR_LANG = ["fr", "en"]
PADDLE_OCR_USE_GPU = True
PADDLE_OCR_CONFIDENCE_THRESHOLD = 0.3

# LEGACY - SAM (deprecated, keeping for reference)
# SAM_MODEL_TYPE = "vit_b"
# SAM_POINTS_PER_SIDE = 32
# SAM_PRED_IOU_THRESH = 0.86
# SAM_STABILITY_SCORE_THRESH = 0.92
# SAM_MIN_MASK_REGION_AREA = 500
# SAM_DEVICE = "cuda"

# OpenCV Preprocessing
ENABLE_PREPROCESSING = True
PREPROCESSING_DENOISE = True
PREPROCESSING_CONTRAST = True
PREPROCESSING_SHARPENING = False

# Screen Monitoring
ENABLE_SCREEN_MONITORING = True
MONITOR_DIFF_THRESHOLD = 0.05
MONITOR_HISTORY_SIZE = 3

# Vision Pipeline
VISION_TIMEOUT = 10
FUSION_NMS_THRESHOLD = 0.3  # Legacy from detection fusion (not used with OmniParser)

# =========================
# MEMORY
# =========================
MAX_MEMORY_INTERACTIONS = 1000
MAX_CONTEXT_INTERACTIONS = 10
MEMORY_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

DETECT_IMPORTANT_MOMENTS = True
IMPORTANT_MOMENT_KEYWORDS = [
    "prefere", "aime", "deteste", "important", "rappelle",
    "toujours", "jamais", "mot de passe", "identifiant"
]

# User Profile (Enhanced Memory - Étape 7)
ENABLE_USER_PROFILING = True
PROFILE_UPDATE_FREQUENCY = "each_interaction"
MAX_CONSOLIDATIONS = 30  # Historique consolidations sessions

# =========================
# SYSTEM
# =========================
MAX_RETRIES = 2
LOG_LEVEL = "INFO"
ENABLE_VISUAL_VERIFICATION = True

AGENT_NAME = "Assistant"
AGENT_PERSONALITY = "helpful"

# CREATE DIRECTORIES
for directory in [DATA_DIR, MODELS_DIR, WEB_SCREENSHOTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)