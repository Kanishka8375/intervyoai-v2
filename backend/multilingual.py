"""
Multilingual Support Module
Supports 42+ languages with optimized STT and TTS
"""

import os
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LanguageConfig:
    """Language configuration"""

    code: str
    name: str
    stt_model: str
    tts_voice: str
    accent: Optional[str] = None


# Complete language support - 50 languages
LANGUAGES = {
    # Major Languages
    "en": LanguageConfig("en", "English", "en_US", "cortana"),
    "es": LanguageConfig("es", "Spanish", "es_ES", "helena"),
    "fr": LanguageConfig("fr", "French", "fr_FR", "hortense"),
    "de": LanguageConfig("de", "German", "de_DE", "kate"),
    "it": LanguageConfig("it", "Italian", "it_IT", "elsa"),
    "pt": LanguageConfig("pt", "Portuguese", "pt_BR", "maria"),
    "ru": LanguageConfig("ru", "Russian", "ru_RU", "irina"),
    "zh": LanguageConfig("zh", "Chinese (Mandarin)", "zh_CN", "huihui"),
    "ja": LanguageConfig("ja", "Japanese", "ja_JP", "haruka"),
    "ko": LanguageConfig("ko", "Korean", "ko_KR", "heami"),
    # European Languages
    "nl": LanguageConfig("nl", "Dutch", "nl_NL", "colette"),
    "pl": LanguageConfig("pl", "Polish", "pl_PL", "paulina"),
    "sv": LanguageConfig("sv", "Swedish", "sv_SE", "hedvig"),
    "da": LanguageConfig("da", "Danish", "da_DK", "helle"),
    "no": LanguageConfig("no", "Norwegian", "nb_NO", "nina"),
    "fi": LanguageConfig("fi", "Finnish", "fi_FI", "satu"),
    "el": LanguageConfig("el", "Greek", "el_GR", "melina"),
    "cs": LanguageConfig("cs", "Czech", "cs_CZ", "zuzana"),
    "sk": LanguageConfig("sk", "Slovak", "sk_SK", "laura"),
    "hu": LanguageConfig("hu", "Hungarian", "hu_HU", "szabolcs"),
    "ro": LanguageConfig("ro", "Romanian", "ro_RO", "ioana"),
    "bg": LanguageConfig("bg", "Bulgarian", "bg_BG", "tarik"),
    "hr": LanguageConfig("hr", "Croatian", "hr_HR", "nika"),
    "sl": LanguageConfig("sl", "Slovenian", "sl_SI", "lado"),
    "uk": LanguageConfig("uk", "Ukrainian", "uk_UA", "lesya"),
    # Asian Languages
    "hi": LanguageConfig("hi", "Hindi", "hi_IN", "hemant"),
    "bn": LanguageConfig("bn", "Bengali", "bn_BN", "puja"),
    "ta": LanguageConfig("ta", "Tamil", "ta_IN", "valluvar"),
    "te": LanguageConfig("te", "Telugu", "te_IN", "chandra"),
    "mr": LanguageConfig("mr", "Marathi", "mr_IN", "manohar"),
    "gu": LanguageConfig("gu", "Gujarati", "gu_IN", "arjun"),
    "kn": LanguageConfig("kn", "Kannada", "kn_IN", "guru"),
    "ml": LanguageConfig("ml", "Malayalam", "ml_IN", "midhun"),
    "th": LanguageConfig("th", "Thai", "th_TH", "krit"),
    "vi": LanguageConfig("vi", "Vietnamese", "vi_VN", "linh"),
    "id": LanguageConfig("id", "Indonesian", "id_ID", "damayanti"),
    "ms": LanguageConfig("ms", "Malay", "ms_MY", "yasmin"),
    "tl": LanguageConfig("tl", "Tagalog", "tl_PH", "belle"),
    "my": LanguageConfig("my", "Burmese", "my_MM", "nilar"),
    "km": LanguageConfig("km", "Khmer", "km_KH", "sokha"),
    # Middle Eastern Languages
    "ar": LanguageConfig("ar", "Arabic", "ar-SA", "meka"),
    "he": LanguageConfig("he", "Hebrew", "he_IL", "asaf"),
    "tr": LanguageConfig("tr", "Turkish", "tr_TR", "yelda"),
    "fa": LanguageConfig("fa", "Persian", "fa_IR", "diana"),
    "ur": LanguageConfig("ur", "Urdu", "ur_PK", "uzma"),
    # African Languages
    "sw": LanguageConfig("sw", "Swahili", "sw_TZ", "waku"),
    "af": LanguageConfig("af", "Afrikaans", "af_ZA", "themba"),
    "am": LanguageConfig("am", "Amharic", "am_ET", "melaku"),
    "yo": LanguageConfig("yo", "Yoruba", "yo_NG", "akin"),
    "zu": LanguageConfig("zu", "Zulu", "zu_ZA", "thando"),
    # Latin American Spanish variants
    "es-MX": LanguageConfig("es-MX", "Spanish (Mexico)", "es_MX", "diana"),
    "es-AR": LanguageConfig("es-AR", "Spanish (Argentina)", "es_AR", "marta"),
    # Portuguese variants
    "pt-PT": LanguageConfig("pt-PT", "Portuguese (Portugal)", "pt_PT", "abigail"),
    # Chinese variants
    "zh-TW": LanguageConfig("zh-TW", "Chinese (Taiwan)", "zh_TW", "hanhan"),
    "zh-HK": LanguageConfig("zh-HK", "Chinese (Hong Kong)", "zh_HK", "hong"),
    # English variants
    "en-GB": LanguageConfig("en-GB", "English (UK)", "en_GB", "susan"),
    "en-AU": LanguageConfig("en-AU", "English (Australia)", "en_AU", "claire"),
    "en-IN": LanguageConfig("en-IN", "English (India)", "en_IN", "heera"),
}


class MultilingualManager:
    """
    Manages multilingual support for speech recognition and synthesis
    """

    def __init__(self):
        self.current_language = "en"
        self.supported_languages = LANGUAGES
        self._initialize()

    def _initialize(self):
        """Initialize multilingual support"""
        # Detect system language
        system_lang = os.environ.get("LANG", "en_US").split(".")[0]
        if system_lang in self.supported_languages:
            self.current_language = system_lang
        elif system_lang.split("_")[0] in self.supported_languages:
            self.current_language = system_lang.split("_")[0]

        logger.info(
            f"Multilingual support initialized. Current: {self.current_language}"
        )

    def get_language(self, code: str) -> Optional[LanguageConfig]:
        """Get language config by code"""
        return self.supported_languages.get(code)

    def set_language(self, code: str) -> bool:
        """Set current language"""
        if code in self.supported_languages:
            self.current_language = code
            logger.info(f"Language changed to: {code}")
            return True
        return False

    def get_language_list(self) -> List[Dict]:
        """Get list of supported languages"""
        return [
            {"code": code, "name": config.name, "native_name": config.name}
            for code, config in self.supported_languages.items()
        ]

    def get_stt_model(self) -> str:
        """Get STT model for current language"""
        config = self.supported_languages.get(self.current_language)
        return config.stt_model if config else "en_US"

    def detect_language(self, audio_data: bytes) -> str:
        """Detect language from audio (placeholder - would use actual detection)"""
        # This would integrate with language detection API
        # For now, return current language
        return self.current_language

    def get_system_language(self) -> str:
        """Get system default language"""
        return self.current_language


# Global instance
multilingual_manager = MultilingualManager()
