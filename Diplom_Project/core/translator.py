from deep_translator import GoogleTranslator

class Translator:
    def __init__(self, source='ru', target='en'):
        self.translator = GoogleTranslator(source=source, target=target)

    def translate(self, text):
        """Translates text from source language to target language."""
        if not text:
            return ""
        try:
            return self.translator.translate(text)
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original text if translation fails
