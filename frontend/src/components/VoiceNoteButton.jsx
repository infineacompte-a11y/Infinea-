import React, { useState, useRef, useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { toast } from "sonner";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

/** Map i18n short code → BCP 47 speech recognition locale */
const SPEECH_LANG_MAP = { fr: "fr-FR", en: "en-US" };
function getSpeechLang(i18nLang) {
  return SPEECH_LANG_MAP[i18nLang] || `${i18nLang}-${i18nLang.toUpperCase()}`;
}

/**
 * Clean up speech transcript: remove repeated words/stutters,
 * fix spacing, capitalize first letter.
 */
function cleanTranscript(raw) {
  if (!raw) return "";

  let text = raw.trim();

  // Remove consecutive duplicate words (stutters like "je je veux")
  text = text.replace(/\b(\w+)(\s+\1\b)+/gi, "$1");

  // Remove consecutive duplicate short phrases (2-3 words repeated)
  text = text.replace(/\b((\w+\s+){1,2}\w+)(\s+\1\b)+/gi, "$1");

  // Fix multiple spaces
  text = text.replace(/\s{2,}/g, " ").trim();

  // Capitalize first letter
  if (text.length > 0) {
    text = text.charAt(0).toUpperCase() + text.slice(1);
  }

  // Add period if no ending punctuation
  if (text.length > 0 && !/[.!?]$/.test(text)) {
    text += ".";
  }

  return text;
}

export default function VoiceNoteButton({ onTranscript, disabled = false }) {
  const { t, i18n } = useTranslation();
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState("");
  const recognitionRef = useRef(null);
  const fullTranscriptRef = useRef("");
  const isSupported = !!SpeechRecognition;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch {}
      }
    };
  }, []);

  const startListening = useCallback(() => {
    if (!isSupported) {
      toast.error(t("components.voiceNoteButton.unsupported"));
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = getSpeechLang(i18n.language);
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    fullTranscriptRef.current = "";

    recognition.onstart = () => {
      setIsListening(true);
      setInterimText("");
    };

    recognition.onresult = (event) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      if (final) {
        fullTranscriptRef.current += final;
      }

      setInterimText(interim || fullTranscriptRef.current);
    };

    recognition.onerror = (event) => {
      if (event.error === "not-allowed") {
        toast.error(t("components.voiceNoteButton.micDenied"));
      } else if (event.error === "no-speech") {
        // Silence — ignore, will auto-restart if continuous
      } else if (event.error !== "aborted") {
        toast.error(t("components.voiceNoteButton.errorRecognition"));
      }
      setIsListening(false);
      setInterimText("");
    };

    recognition.onend = () => {
      setIsListening(false);

      // Process and send the final transcript
      const cleaned = cleanTranscript(fullTranscriptRef.current);
      if (cleaned && onTranscript) {
        onTranscript(cleaned);
      }

      setInterimText("");
      fullTranscriptRef.current = "";
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (e) {
      toast.error(t("components.voiceNoteButton.errorStart"));
      setIsListening(false);
    }
  }, [isSupported, onTranscript, t]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
    }
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  if (!isSupported) {
    return null; // Hide button if browser doesn't support speech recognition
  }

  return (
    <div className="space-y-2">
      {/* Mic button */}
      <div className="flex items-center gap-3">
        <Button
          type="button"
          variant={isListening ? "default" : "outline"}
          size="sm"
          onClick={toggleListening}
          disabled={disabled}
          className={`rounded-xl gap-2 transition-all ${
            isListening
              ? "bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/25"
              : "hover:border-primary/50"
          }`}
          data-testid="voice-note-btn"
        >
          {isListening ? (
            <>
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-white" />
              </span>
              {t("components.voiceNoteButton.stop")}
            </>
          ) : (
            <>
              <Mic className="w-4 h-4" />
              {t("components.voiceNoteButton.dictate")}
            </>
          )}
        </Button>

        {isListening && (
          <span className="text-xs text-muted-foreground animate-pulse">
            {t("components.voiceNoteButton.speakPrompt")}
          </span>
        )}
      </div>

      {/* Interim transcript preview */}
      {isListening && interimText && (
        <div className="p-2.5 rounded-lg bg-primary/5 border border-primary/20 animate-fade-in">
          <p className="text-sm text-muted-foreground italic leading-relaxed">
            {interimText}
          </p>
        </div>
      )}
    </div>
  );
}
