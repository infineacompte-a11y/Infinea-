import React, { useState, useRef, useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Mic, MicOff } from "lucide-react";
import { toast } from "sonner";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

/** Map i18n short code → BCP 47 speech recognition locale */
const SPEECH_LANG_MAP = { fr: "fr-FR", en: "en-US" };
function getSpeechLang(i18nLang) {
  return SPEECH_LANG_MAP[i18nLang] || `${i18nLang}-${i18nLang.toUpperCase()}`;
}

/**
 * Clean up speech transcript: remove stutters, fix spacing, capitalize.
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
  return text;
}

/**
 * Universal voice input component with real-time transcript display.
 *
 * Two usage modes:
 *
 * MODE 1 — Managed (recommended): pass textValue + onTextChange
 *   The component auto-manages interim display in the linked text field.
 *   <VoiceInput textValue={notes} onTextChange={setNotes} />
 *
 * MODE 2 — Manual: pass onResult (+ optional onInterim)
 *   You handle everything yourself.
 *   <VoiceInput onResult={(text) => append(text)} />
 *
 * Props:
 * - textValue: current text field value (managed mode)
 * - onTextChange(newValue): setter for text field (managed mode)
 * - onResult(text): called with cleaned transcript when recording stops (manual mode)
 * - onInterim(text): called with interim text during recording (manual mode)
 * - onListeningChange(isListening): notifies parent when listening state changes
 * - disabled: disables the button
 * - variant: "icon" (default) | "pill"
 * - className: additional CSS classes
 */
export default function VoiceInput({
  textValue,
  onTextChange,
  onResult,
  onInterim,
  onListeningChange,
  disabled = false,
  variant = "icon",
  className = "",
}) {
  const { t, i18n } = useTranslation();
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState("");
  const recognitionRef = useRef(null);
  const fullTranscriptRef = useRef("");
  const baselineRef = useRef(""); // text value when recording started
  const isManaged = textValue !== undefined && onTextChange;
  const isSupported = !!SpeechRecognition;

  // Notify parent of listening state changes
  useEffect(() => {
    onListeningChange?.(isListening);
  }, [isListening, onListeningChange]);

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
      toast.error(t("components.voiceInput.unsupported"));
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = getSpeechLang(i18n.language);
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    fullTranscriptRef.current = "";
    setInterimText("");

    // Save baseline text for managed mode
    if (isManaged) {
      baselineRef.current = textValue || "";
    }

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      let interim = "";
      let finalText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalText += transcript;
        } else {
          interim += transcript;
        }
      }
      if (finalText) {
        fullTranscriptRef.current += finalText;
      }

      // Real-time display
      const currentDraft = fullTranscriptRef.current + interim;

      if (isManaged) {
        // Update text field in real-time with interim
        const separator = baselineRef.current && currentDraft ? " " : "";
        onTextChange(baselineRef.current + separator + currentDraft);
      }

      setInterimText(interim);

      if (onInterim) {
        onInterim(currentDraft);
      }
    };

    recognition.onerror = (event) => {
      if (event.error === "not-allowed") {
        toast.error(t("components.voiceInput.micDenied"));
      } else if (event.error !== "no-speech" && event.error !== "aborted") {
        toast.error(t("components.voiceInput.errorRecognition"));
      }
      setIsListening(false);
      setInterimText("");
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimText("");
      const cleaned = cleanTranscript(fullTranscriptRef.current);

      if (isManaged) {
        // Set final cleaned text
        const separator = baselineRef.current && cleaned ? " " : "";
        onTextChange(baselineRef.current + separator + cleaned);
      } else if (cleaned && onResult) {
        onResult(cleaned);
      }

      fullTranscriptRef.current = "";
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch {
      toast.error(t("components.voiceInput.errorStart"));
      setIsListening(false);
    }
  }, [isSupported, isManaged, textValue, onTextChange, onResult, onInterim, t]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
    }
  }, []);

  const toggle = useCallback(() => {
    if (isListening) stopListening();
    else startListening();
  }, [isListening, startListening, stopListening]);

  if (!isSupported) return null;

  // Icon variant: small circular button with enhanced listening feedback
  if (variant === "icon") {
    return (
      <button
        type="button"
        onClick={toggle}
        disabled={disabled}
        title={isListening ? t("components.voiceInput.stopDictation") : t("components.voiceInput.dictate")}
        className={`relative shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 ${
          isListening
            ? "bg-red-500 text-white shadow-lg shadow-red-500/30 scale-110"
            : "bg-muted/50 text-muted-foreground hover:bg-primary/10 hover:text-primary border border-border/50"
        } ${disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer"} ${className}`}
      >
        {isListening ? (
          <MicOff className="w-4 h-4" />
        ) : (
          <Mic className="w-4 h-4" />
        )}
        {isListening && (
          <>
            <span className="absolute inset-0 rounded-xl bg-red-500/20 animate-ping" />
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-red-400 animate-pulse" />
          </>
        )}
      </button>
    );
  }

  // Pill variant: labeled button with full listening state
  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      className={`shrink-0 flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
        isListening
          ? "bg-red-500 text-white shadow-lg shadow-red-500/30 scale-[1.02]"
          : "bg-muted/50 text-muted-foreground hover:bg-primary/10 hover:text-primary border border-border/50"
      } ${disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer"} ${className}`}
    >
      {isListening ? (
        <MicOff className="w-4 h-4" />
      ) : (
        <Mic className="w-4 h-4" />
      )}
      {isListening ? (
        <span className="flex items-center gap-1.5">
          <span className="flex items-center gap-0.5">
            <span className="w-1 h-3 bg-white/80 rounded-full animate-pulse" style={{ animationDelay: "0ms" }} />
            <span className="w-1 h-4 bg-white/90 rounded-full animate-pulse" style={{ animationDelay: "150ms" }} />
            <span className="w-1 h-2 bg-white/70 rounded-full animate-pulse" style={{ animationDelay: "300ms" }} />
            <span className="w-1 h-3.5 bg-white/85 rounded-full animate-pulse" style={{ animationDelay: "100ms" }} />
          </span>
          {t("components.voiceInput.listening")}
        </span>
      ) : (
        t("components.voiceInput.dictate")
      )}
    </button>
  );
}

/**
 * Wrapper component: voice-enabled textarea area with listening indicator bar.
 * Use this for a complete voice + text experience.
 *
 * <VoiceTextArea value={text} onChange={setText} placeholder="..." rows={3} />
 */
export function VoiceTextArea({
  value,
  onChange,
  placeholder = "",
  rows = 2,
  maxLength,
  className = "",
  disabled = false,
  voiceDisabled = false,
  textareaClassName = "",
}) {
  const { t } = useTranslation();
  const [listening, setListening] = useState(false);

  return (
    <div className={`relative ${className}`}>
      {/* Listening indicator bar */}
      {listening && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/5 border border-red-500/15 border-b-0 rounded-t-lg">
          <div className="flex items-center gap-0.5">
            <span className="w-0.5 h-2 bg-red-500/60 rounded-full animate-pulse" style={{ animationDelay: "0ms" }} />
            <span className="w-0.5 h-3 bg-red-500/80 rounded-full animate-pulse" style={{ animationDelay: "150ms" }} />
            <span className="w-0.5 h-1.5 bg-red-500/50 rounded-full animate-pulse" style={{ animationDelay: "300ms" }} />
            <span className="w-0.5 h-2.5 bg-red-500/70 rounded-full animate-pulse" style={{ animationDelay: "100ms" }} />
          </div>
          <span className="text-[11px] text-red-500/80 font-medium">{t("components.voiceInput.listeningIndicator")}</span>
        </div>
      )}

      {/* Textarea */}
      <textarea
        className={`w-full rounded-lg border bg-muted/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none transition-all duration-200 ${
          listening
            ? "border-red-500/30 ring-1 ring-red-500/10 rounded-t-none rounded-b-none"
            : "border-border rounded-b-none"
        } ${textareaClassName}`}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        maxLength={maxLength}
        disabled={disabled}
      />

      {/* Toolbar below textarea with mic button */}
      <div className={`flex items-center justify-between px-2 py-1.5 border border-t-0 rounded-b-lg transition-colors ${
        listening ? "border-red-500/30 bg-red-500/3" : "border-border bg-muted/20"
      }`}>
        <div className="flex items-center gap-1.5">
          {maxLength && (
            <span className={`text-[10px] ${
              value.length > maxLength * 0.8 ? "text-amber-500" : "text-muted-foreground/40"
            }`}>
              {value.length}/{maxLength}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {listening && (
            <span className="text-[10px] text-red-500/60 font-medium mr-1">{t("components.voiceInput.dictatePrompt")}</span>
          )}
          <VoiceInput
            variant="icon"
            textValue={value}
            onTextChange={onChange}
            onListeningChange={setListening}
            disabled={disabled || voiceDisabled}
          />
        </div>
      </div>
    </div>
  );
}
