import React, { useState, useRef, useCallback, useEffect } from "react";
import { Mic } from "lucide-react";
import { toast } from "sonner";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

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
 * Universal voice input component — inline mic button that can be placed
 * next to any text field. Captures speech, cleans it, and returns via onResult.
 *
 * Props:
 * - onResult(text): called with cleaned transcript when recording stops
 * - onInterim(text): called with interim text during recording (optional)
 * - disabled: disables the button
 * - variant: "icon" (default, small round button) | "pill" (labeled button)
 * - className: additional CSS classes for the container
 */
export default function VoiceInput({
  onResult,
  onInterim,
  disabled = false,
  variant = "icon",
  className = "",
}) {
  const [isListening, setIsListening] = useState(false);
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
      toast.error("Votre navigateur ne supporte pas la reconnaissance vocale.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "fr-FR";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    fullTranscriptRef.current = "";

    recognition.onstart = () => {
      setIsListening(true);
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
      if (onInterim) {
        onInterim(interim || fullTranscriptRef.current);
      }
    };

    recognition.onerror = (event) => {
      if (event.error === "not-allowed") {
        toast.error("Accès au micro refusé. Autorisez le micro dans les paramètres.");
      } else if (event.error !== "no-speech" && event.error !== "aborted") {
        toast.error("Erreur de reconnaissance vocale.");
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      const cleaned = cleanTranscript(fullTranscriptRef.current);
      if (cleaned && onResult) {
        onResult(cleaned);
      }
      fullTranscriptRef.current = "";
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch {
      toast.error("Impossible de démarrer le micro.");
      setIsListening(false);
    }
  }, [isSupported, onResult, onInterim]);

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

  // Icon variant: small circular button, perfect for inline placement
  if (variant === "icon") {
    return (
      <button
        type="button"
        onClick={toggle}
        disabled={disabled}
        title={isListening ? "Arrêter la dictée" : "Dicter"}
        className={`relative shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
          isListening
            ? "bg-red-500 text-white shadow-lg shadow-red-500/25"
            : "bg-muted/50 text-muted-foreground hover:bg-primary/10 hover:text-primary border border-border/50"
        } ${disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer"} ${className}`}
      >
        <Mic className="w-4 h-4" />
        {isListening && (
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
        )}
      </button>
    );
  }

  // Pill variant: labeled button, similar to original VoiceNoteButton
  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      className={`shrink-0 flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
        isListening
          ? "bg-red-500 text-white shadow-lg shadow-red-500/25"
          : "bg-muted/50 text-muted-foreground hover:bg-primary/10 hover:text-primary border border-border/50"
      } ${disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer"} ${className}`}
    >
      <Mic className="w-4 h-4" />
      {isListening ? (
        <span className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
          </span>
          Écoute...
        </span>
      ) : (
        "Dicter"
      )}
    </button>
  );
}
