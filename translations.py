"""Bilingual (EN/TR) text strings for the trigger tracker app."""

TEXT = {
    "en": {
        "app_title": "Trigger tracker",
        "source_label": "Source",
        "source_hint": "Unreasonable situation",
        "raw_description": "What happened, in your own words?",

        "extract_title": "Extract: turn the event into fact",
        "extract_fact": "What exactly happened, as an observable fact (no interpretation)?",
        "extract_third_party_version": "How would you describe this to a court or a third party?",
        "extract_is_evidence_based": "Is this supported by evidence, or is it your interpretation?",
        "extract_is_recurring_pattern": "Has this happened before, or is it new?",

        "transform_title": "Transform: separate the emotional load",
        "transform_intensity_score": "Intensity right now (1-10)?",
        "transform_is_proportional": "Is this intensity proportional to the fact?",
        "transform_signal_type": "Does this feeling say 'action needed' or 'needs processing'?",
        "transform_signal_action": "Action needed",
        "transform_signal_processing": "Needs processing",
        "transform_serves_purpose": "Would expressing it now resolve the fact, or just relieve you?",

        "filter_title": "Filter: separate from old emotion",
        "filter_feels_familiar": "Does this feeling feel familiar from way before?",
        "filter_reaction_vs_event_size": "Is your reaction equal to the event, or bigger?",
        "filter_reaction_equal": "Equal",
        "filter_reaction_bigger": "Bigger",
        "filter_would_react_same_stranger": "Would you react the same way if a stranger did this?",
        "filter_echoes_childhood": "Does this echo something from childhood or family?",

        "destination_title": "Load: destination",
        "destination_tag": "Where does this go?",
        "destination_note": "Note (e.g. sent to lawyer, logged for court)",

        "submit": "Save event",
        "yes": "Yes",
        "no": "No",
        "unsure": "Not sure / doesn't fit yes-no",
        "counts_title": "How many times triggered",
        "total": "Total",

        "login_title": "Log in",
        "register_title": "Create account",
        "email": "Email",
        "password": "Password",
        "login_submit": "Log in",
        "register_submit": "Create account",
        "logout": "Log out",
        "no_account": "No account yet?",
        "have_account": "Already have an account?",
        "email_required": "Email is required",
        "password_too_short": "Password must be at least 8 characters",
        "email_taken": "An account with this email already exists",
        "invalid_credentials": "Invalid email or password",
    },
    "tr": {
        "app_title": "Tetikleyici takip",
        "source_label": "Kaynak",
        "source_hint": "Unreasonable situation",
        "raw_description": "Ne oldu, kendi cümlelerinle?",

        "extract_title": "Extract: olayı olguya çevir",
        "extract_fact": "Tam olarak ne oldu, gözlemlenebilir olgu olarak (yorum yok)?",
        "extract_third_party_version": "Bunu bir mahkemeye/üçüncü kişiye nasıl anlatırdın?",
        "extract_is_evidence_based": "Bu kanıtla mı destekleniyor, yoksa senin yorumun mu?",
        "extract_is_recurring_pattern": "Bu daha önce oldu mu, yoksa yeni mi?",

        "transform_title": "Transform: duygusal yükü ayır",
        "transform_intensity_score": "Şu anki yoğunluk (1-10)?",
        "transform_is_proportional": "Bu yoğunluk olgunun büyüklüğüyle orantılı mı?",
        "transform_signal_type": "Bu duygu 'aksiyon gerekli' mi diyor, yoksa 'işlenmeli' mi diyor?",
        "transform_signal_action": "Aksiyon gerekli",
        "transform_signal_processing": "İşlenmeli",
        "transform_serves_purpose": "Bunu şimdi ifade etmek olguyu çözer mi, yoksa sadece rahatlatır mı?",

        "filter_title": "Filter: eski duygudan ayır",
        "filter_feels_familiar": "Bu his çok öncesinden tanıdık geliyor mu?",
        "filter_reaction_vs_event_size": "Tepkin olayla eşit mi, yoksa daha mı büyük?",
        "filter_reaction_equal": "Eşit",
        "filter_reaction_bigger": "Daha büyük",
        "filter_would_react_same_stranger": "Aynı şeyi tanımadığın biri yapsaydı aynı tepkiyi verir miydin?",
        "filter_echoes_childhood": "Bu, çocukluktan veya aileden bir şey hatırlatıyor mu?",

        "destination_title": "Load: hedef",
        "destination_tag": "Bu nereye gidiyor?",
        "destination_note": "Not (örn. avukata gönderildi, mahkeme için kaydedildi)",

        "submit": "Kaydı kaydet",
        "yes": "Evet",
        "no": "Hayır",
        "unsure": "Emin değilim / evet-hayıra sığmıyor",
        "counts_title": "Kaç kez tetiklendi",
        "total": "Toplam",

        "login_title": "Giriş yap",
        "register_title": "Hesap oluştur",
        "email": "E-posta",
        "password": "Şifre",
        "login_submit": "Giriş yap",
        "register_submit": "Hesap oluştur",
        "logout": "Çıkış yap",
        "no_account": "Hesabın yok mu?",
        "have_account": "Zaten bir hesabın var mı?",
        "email_required": "E-posta gerekli",
        "password_too_short": "Şifre en az 8 karakter olmalı",
        "email_taken": "Bu e-posta ile zaten bir hesap var",
        "invalid_credentials": "E-posta veya şifre hatalı",
    },
}


def t(lang: str, key: str) -> str:
    """Get a translated string, falling back to English then the key itself."""
    lang = lang if lang in TEXT else "en"
    return TEXT[lang].get(key, TEXT["en"].get(key, key))
